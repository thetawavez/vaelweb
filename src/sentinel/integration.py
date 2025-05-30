"""
VAEL Core - Sentinel Integration Module
---------------------------------------
Connects the WebSocket server with VAEL Core entities,
handles entity registration, discovery, and response aggregation.

This module serves as the bridge between the Flask WebSocket interface
and the modular VAEL Core entity system.
"""

import os
import sys
import json
import time
import logging
import importlib
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'sentinel_integration.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('sentinel.integration')

# Symbolic indicators for token efficiency
SYMBOLS = {
    'success': '✅',
    'warning': '⚠️',
    'error': '❌',
    'info': 'ℹ️',
    'processing': '⚙️',
    'security': '🔒',
    'alert': '🚨',
    'health': '💓',
    'memory': '🧠',
    'network': '🌐',
    'time': '⏱️',
    'config': '⚙️',
    'database': '💾',
    'api': '🔌',
    'voice': '🎤',
    'user': '👤',
    'system': '🖥️',
    'analysis': '🔍',
    'decision': '🧩',
}

# Entity registry
_entities = {}
_entity_status = {}
_last_pulse = {}
_decision_log = []

# Maximum size for circular buffers to maintain token efficiency
MAX_LOG_SIZE = 10
MAX_DECISION_LOG_SIZE = 20

class EntityNotFoundError(Exception):
    """Raised when an entity is not found in the registry."""
    pass

class EntityNotReadyError(Exception):
    """Raised when an entity is not ready to process requests."""
    pass

def register_entity(name: str, module_path: str) -> bool:
    """
    Register an entity with the integration system.
    
    Args:
        name: The name of the entity (e.g., 'nexus', 'sentinel')
        module_path: The import path to the entity module
        
    Returns:
        bool: True if registration was successful, False otherwise
    """
    global _entities, _entity_status, _last_pulse
    
    try:
        # Lazy import to save tokens
        module = importlib.import_module(module_path)
        _entities[name] = module
        _entity_status[name] = 'registered'
        _last_pulse[name] = time.time()
        
        # Log registration with symbolic indicator for token efficiency
        logger.info(f"{SYMBOLS['success']} Entity '{name}' registered from {module_path}")
        
        # Run initial pulse check if available
        if hasattr(module, 'pulse') and callable(module.pulse):
            pulse_result = module.pulse()
            _last_pulse[name] = time.time()
            _entity_status[name] = 'active' if pulse_result.get('status') == 'healthy' else 'warning'
            logger.info(f"{SYMBOLS['health']} Initial pulse for '{name}': {_entity_status[name]}")
        
        return True
    except ImportError as e:
        logger.error(f"{SYMBOLS['error']} Failed to register entity '{name}': {str(e)}")
        _entity_status[name] = 'error'
        return False
    except Exception as e:
        logger.error(f"{SYMBOLS['error']} Unexpected error registering '{name}': {str(e)}")
        _entity_status[name] = 'error'
        return False

def discover_entities() -> Dict[str, str]:
    """
    Automatically discover and register available entities.
    
    Returns:
        Dict[str, str]: A dictionary of entity names and their status
    """
    # Base path for entity discovery
    base_path = 'vael_core'
    
    # Potential entities to discover
    potential_entities = [
        'sentinel', 'nexus', 'watchdog', 'twin_flame', 
        'local_vael', 'manus_interface'
    ]
    
    for entity in potential_entities:
        module_path = f"{base_path}.{entity}"
        try:
            # Check if the module exists before attempting to import
            spec = importlib.util.find_spec(module_path)
            if spec is not None:
                register_entity(entity, module_path)
        except Exception as e:
            logger.warning(f"{SYMBOLS['warning']} Error discovering entity '{entity}': {str(e)}")
    
    return get_entity_status()

def get_entity_status() -> Dict[str, str]:
    """
    Get the current status of all registered entities.
    
    Returns:
        Dict[str, str]: A dictionary of entity names and their status
    """
    return _entity_status.copy()

def check_entity_health(name: str = None) -> Dict[str, Any]:
    """
    Check the health of an entity or all entities.
    
    Args:
        name: The name of the entity to check, or None for all entities
        
    Returns:
        Dict[str, Any]: Health status information
    """
    if name is not None:
        if name not in _entities:
            raise EntityNotFoundError(f"Entity '{name}' not found")
        
        entity = _entities[name]
        if hasattr(entity, 'pulse') and callable(entity.pulse):
            try:
                result = entity.pulse()
                _last_pulse[name] = time.time()
                _entity_status[name] = 'active' if result.get('status') == 'healthy' else 'warning'
                return {name: result}
            except Exception as e:
                logger.error(f"{SYMBOLS['error']} Error checking health of '{name}': {str(e)}")
                _entity_status[name] = 'error'
                return {name: {'status': 'error', 'message': str(e)}}
        else:
            return {name: {'status': 'unknown', 'message': 'No pulse method available'}}
    else:
        # Check all entities
        results = {}
        for entity_name in _entities:
            results.update(check_entity_health(entity_name))
        return results

def execute_entity_method(entity_name: str, method_name: str, *args, **kwargs) -> Any:
    """
    Execute a method on a specific entity.
    
    Args:
        entity_name: The name of the entity
        method_name: The name of the method to execute
        *args, **kwargs: Arguments to pass to the method
        
    Returns:
        Any: The result of the method execution
    """
    if entity_name not in _entities:
        raise EntityNotFoundError(f"Entity '{entity_name}' not found")
    
    entity = _entities[entity_name]
    
    # Check if entity has the requested method
    if not hasattr(entity, method_name) or not callable(getattr(entity, method_name)):
        logger.error(f"{SYMBOLS['error']} Method '{method_name}' not found on entity '{entity_name}'")
        return {'status': 'error', 'message': f"Method '{method_name}' not found"}
    
    # Execute the method
    try:
        method = getattr(entity, method_name)
        result = method(*args, **kwargs)
        return result
    except Exception as e:
        logger.error(f"{SYMBOLS['error']} Error executing '{method_name}' on '{entity_name}': {str(e)}")
        return {'status': 'error', 'message': str(e)}

def process_message(message: str, source: str = 'user') -> Dict[str, Any]:
    """
    Process an incoming message and route it to the appropriate entity.
    
    Args:
        message: The message content
        source: The source of the message (e.g., 'user', 'system')
        
    Returns:
        Dict[str, Any]: The processed response
    """
    # Log the incoming message with token-efficient format
    logger.info(f"{SYMBOLS['info']} Processing message from {source}: {message[:50]}...")
    
    # Check if this is a command directed at a specific entity
    if message.startswith('/'):
        return process_command(message, source)
    
    # Determine which entity should handle this message
    # For token efficiency, we'll use a simple routing strategy
    # In a full implementation, this would use NLP or pattern matching
    
    # First, check if Twin Flame should process this (complex reasoning)
    if 'twin_flame' in _entities and _entity_status.get('twin_flame') == 'active':
        # Ask Twin Flame if it can handle this message
        can_handle = execute_entity_method('twin_flame', 'can_process', message)
        if can_handle.get('result', False):
            result = execute_entity_method('twin_flame', 'process', message)
            log_decision('twin_flame', message, result)
            return result
    
    # Next, check if this is a security-related message for NEXUS
    security_keywords = ['security', 'threat', 'attack', 'vulnerability', 'breach', 'hack']
    if 'nexus' in _entities and _entity_status.get('nexus') == 'active' and any(kw in message.lower() for kw in security_keywords):
        result = execute_entity_method('nexus', 'process', message)
        log_decision('nexus', message, result)
        return result
    
    # Default to local_vael for general processing
    if 'local_vael' in _entities and _entity_status.get('local_vael') == 'active':
        result = execute_entity_method('local_vael', 'process', message)
        log_decision('local_vael', message, result)
        return result
    
    # Fallback to a simple response if no entity can handle it
    logger.warning(f"{SYMBOLS['warning']} No suitable entity found to process message")
    return {
        'status': 'fallback',
        'message': "I'm processing your request. Please wait while I connect to the appropriate system.",
        'source': 'sentinel_integration'
    }

def process_command(command: str, source: str = 'user') -> Dict[str, Any]:
    """
    Process a command directed at a specific entity.
    
    Args:
        command: The command string (e.g., '/nexus status')
        source: The source of the command
        
    Returns:
        Dict[str, Any]: The command response
    """
    parts = command[1:].split(' ', 1)
    entity_name = parts[0].lower()
    cmd = parts[1] if len(parts) > 1 else 'help'
    
    logger.info(f"{SYMBOLS['command']} Processing command for {entity_name}: {cmd}")
    
    # Check if the entity exists
    if entity_name not in _entities:
        return {
            'status': 'error',
            'message': f"Entity '{entity_name}' not found. Available entities: {', '.join(_entities.keys())}",
            'source': 'sentinel_integration'
        }
    
    # Special commands that don't require the entity to handle them
    if cmd == 'status':
        status = _entity_status.get(entity_name, 'unknown')
        last_pulse_time = _last_pulse.get(entity_name, 0)
        time_since_pulse = time.time() - last_pulse_time
        
        return {
            'status': 'success',
            'message': f"Entity '{entity_name}' status: {status}. Last pulse: {time_since_pulse:.1f}s ago.",
            'source': 'sentinel_integration'
        }
    
    # Forward the command to the entity
    try:
        result = execute_entity_method(entity_name, 'handle_command', cmd)
        log_decision(entity_name, command, result)
        return result
    except Exception as e:
        logger.error(f"{SYMBOLS['error']} Error processing command '{cmd}' for '{entity_name}': {str(e)}")
        return {
            'status': 'error',
            'message': f"Error processing command: {str(e)}",
            'source': 'sentinel_integration'
        }

def log_decision(entity: str, input_data: str, output_data: Any) -> None:
    """
    Log a decision made by an entity for auditing and analysis.
    
    Args:
        entity: The name of the entity making the decision
        input_data: The input that led to the decision
        output_data: The output/decision made
    """
    global _decision_log
    
    # Create a token-efficient log entry
    entry = {
        'timestamp': datetime.now().isoformat(),
        'entity': entity,
        'input_hash': hash(input_data),  # Use hash for token efficiency
        'output_type': type(output_data).__name__,
        'status': output_data.get('status', 'unknown') if isinstance(output_data, dict) else 'unknown'
    }
    
    # Add to circular buffer for token efficiency
    _decision_log.append(entry)
    if len(_decision_log) > MAX_DECISION_LOG_SIZE:
        _decision_log.pop(0)
    
    # Write to log file
    log_dir = os.path.join('logs', 'decisions')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"decision_{int(time.time())}.json")
    try:
        with open(log_file, 'w') as f:
            json.dump({
                'timestamp': entry['timestamp'],
                'entity': entity,
                'input': input_data[:100] + '...' if len(input_data) > 100 else input_data,
                'output': str(output_data)[:100] + '...' if len(str(output_data)) > 100 else str(output_data),
                'status': entry['status']
            }, f)
    except Exception as e:
        logger.error(f"{SYMBOLS['error']} Error writing decision log: {str(e)}")

def format_response(entity_response: Dict[str, Any]) -> str:
    """
    Format an entity response for the WebSocket interface.
    
    Args:
        entity_response: The raw response from an entity
        
    Returns:
        str: The formatted response suitable for the WebSocket interface
    """
    # Extract the message from the response
    if isinstance(entity_response, dict):
        if 'message' in entity_response:
            return entity_response['message']
        elif 'response' in entity_response:
            return entity_response['response']
        elif 'result' in entity_response:
            result = entity_response['result']
            if isinstance(result, (str, int, float, bool)):
                return str(result)
            else:
                return json.dumps(result)
    
    # Fallback to string representation
    return str(entity_response)

def initialize() -> bool:
    """
    Initialize the integration system and discover entities.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        logger.info(f"{SYMBOLS['info']} Initializing Sentinel integration module")
        discover_entities()
        
        # Log the discovered entities
        status = get_entity_status()
        logger.info(f"{SYMBOLS['success']} Discovered entities: {json.dumps(status)}")
        
        # Check health of all entities
        health = check_entity_health()
        logger.info(f"{SYMBOLS['health']} Entity health check complete")
        
        return True
    except Exception as e:
        logger.error(f"{SYMBOLS['error']} Error initializing integration module: {str(e)}")
        return False

# Initialize on import
initialize()
