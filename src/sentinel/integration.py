"""
VAEL Core - Sentinel Integration Module

This module serves as the integration layer between the WebSocket interface
and the VAEL Core entities. It handles entity loading, message routing,
response collection, and fallback mechanisms.

Token Efficiency: Uses symbolic indicators and lazy loading to minimize token usage.
"""

import importlib
import logging
import json
import time
import os
import sys
from typing import Dict, List, Any, Optional, Tuple, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs/sentinel.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Symbolic indicators for token efficiency
SYMBOLS = {
    'loading': '⏳',
    'success': '✅',
    'warning': '⚠️',
    'error': '❌',
    'processing': '🔄',
    'secure': '🔒',
    'insecure': '🔓',
    'alert': '🚨',
    'listening': '👂',
    'speaking': '🗣️',
    'thinking': '🧠',
    'healing': '🩹',
    'analyzing': '🔍',
    'guarding': '🛡️'
}

# Entity registry
_entities = {}
_entity_status = {}
_last_pulse = {}

def init_entities() -> Dict[str, bool]:
    """
    Initialize all VAEL Core entities.
    
    Returns:
        Dict[str, bool]: Status of each entity initialization
    """
    entity_status = {}
    
    # List of entities to initialize
    entities = [
        "sentinel",
        "nexus",
        "watchdog",
        "twin_flame",
        "local_vael",
        "manus_interface"
    ]
    
    for entity_name in entities:
        try:
            # Attempt to import the entity module
            logger.info(f"{SYMBOLS['loading']} Loading entity: {entity_name}")
            entity_module = importlib.import_module(f"vael_core.{entity_name}")
            
            # Initialize the entity
            if hasattr(entity_module, 'initialize'):
                entity_module.initialize()
                
            # Store the entity module
            _entities[entity_name] = entity_module
            _entity_status[entity_name] = True
            _last_pulse[entity_name] = time.time()
            
            logger.info(f"{SYMBOLS['success']} Entity loaded: {entity_name}")
            entity_status[entity_name] = True
        except ImportError:
            logger.warning(f"{SYMBOLS['warning']} Entity not found: {entity_name}")
            entity_status[entity_name] = False
        except Exception as e:
            logger.error(f"{SYMBOLS['error']} Error initializing entity {entity_name}: {str(e)}")
            entity_status[entity_name] = False
    
    return entity_status

def route_message(message: str, source: str = "user", context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Route a message to the appropriate entity and collect responses.
    
    Args:
        message (str): The message to route
        source (str): Source of the message (default: "user")
        context (Dict[str, Any], optional): Additional context for processing
    
    Returns:
        Dict[str, Any]: Response data including entity responses and metadata
    """
    if context is None:
        context = {}
    
    # Initialize response container
    response = {
        "timestamp": time.time(),
        "source": source,
        "message": message,
        "responses": {},
        "primary_response": "",
        "symbols": [],
        "metadata": {
            "entities_consulted": [],
            "processing_time": 0,
            "token_usage": 0
        }
    }
    
    start_time = time.time()
    
    # Check for commands directed at specific entities
    entity_command = None
    command_args = None
    
    # Parse entity commands (format: @entity:command or @entity command)
    if message.startswith('@'):
        parts = message[1:].split(':', 1)
        if len(parts) == 2:
            entity_command = parts[0].strip()
            command_args = parts[1].strip()
        else:
            parts = message[1:].split(' ', 1)
            if len(parts) == 2:
                entity_command = parts[0].strip()
                command_args = parts[1].strip()
    
    # Handle entity-specific commands
    if entity_command and entity_command in _entities:
        logger.info(f"{SYMBOLS['processing']} Routing command to entity: {entity_command}")
        response["metadata"]["entities_consulted"].append(entity_command)
        
        try:
            entity = _entities[entity_command]
            
            # Update pulse timestamp
            _last_pulse[entity_command] = time.time()
            
            # Call the appropriate method based on command
            if command_args.startswith('pulse'):
                if hasattr(entity, 'pulse'):
                    result = entity.pulse()
                    response["responses"][entity_command] = result
                    response["primary_response"] = f"Pulse from {entity_command}: {result}"
                    response["symbols"].append(SYMBOLS['analyzing'])
            
            elif command_args.startswith('sync'):
                if hasattr(entity, 'sync'):
                    result = entity.sync()
                    response["responses"][entity_command] = result
                    response["primary_response"] = f"Sync from {entity_command}: {result}"
                    response["symbols"].append(SYMBOLS['processing'])
            
            elif command_args.startswith('suggest'):
                if hasattr(entity, 'suggest'):
                    # Extract suggestion context if provided
                    suggestion_context = command_args[8:].strip() if len(command_args) > 8 else ""
                    result = entity.suggest(suggestion_context)
                    response["responses"][entity_command] = result
                    response["primary_response"] = f"Suggestion from {entity_command}: {result}"
                    response["symbols"].append(SYMBOLS['thinking'])
            
            else:
                # Default to processing the command as a message
                if hasattr(entity, 'process_message'):
                    result = entity.process_message(command_args, context)
                    response["responses"][entity_command] = result
                    response["primary_response"] = result
                    response["symbols"].append(SYMBOLS['speaking'])
        
        except Exception as e:
            logger.error(f"{SYMBOLS['error']} Error processing command for {entity_command}: {str(e)}")
            response["responses"][entity_command] = f"Error: {str(e)}"
            response["primary_response"] = f"Error processing command for {entity_command}"
            response["symbols"].append(SYMBOLS['error'])
    
    # General message processing (consult multiple entities)
    else:
        # First, check with NEXUS for security threats
        if "nexus" in _entities and _entity_status.get("nexus", False):
            try:
                logger.info(f"{SYMBOLS['guarding']} NEXUS analyzing message for threats")
                nexus = _entities["nexus"]
                
                # Update pulse timestamp
                _last_pulse["nexus"] = time.time()
                
                # Check message for threats
                if hasattr(nexus, 'pulse'):
                    threat_assessment = nexus.pulse(message=message)
                    response["responses"]["nexus"] = threat_assessment
                    response["metadata"]["entities_consulted"].append("nexus")
                    
                    # Add threat symbols if detected
                    if "threat_level" in threat_assessment:
                        if threat_assessment["threat_level"] == "high":
                            response["symbols"].append(SYMBOLS['alert'])
                        elif threat_assessment["threat_level"] == "medium":
                            response["symbols"].append(SYMBOLS['warning'])
                        elif threat_assessment["threat_level"] == "low":
                            response["symbols"].append(SYMBOLS['secure'])
                    
                    # Block processing if high threat detected
                    if threat_assessment.get("threat_level") == "high" and threat_assessment.get("block", False):
                        response["primary_response"] = "Message blocked due to security concerns."
                        return response
            
            except Exception as e:
                logger.error(f"{SYMBOLS['error']} Error consulting NEXUS: {str(e)}")
        
        # Process with Twin Flame for bi-hemisphere analysis
        if "twin_flame" in _entities and _entity_status.get("twin_flame", False):
            try:
                logger.info(f"{SYMBOLS['thinking']} Twin Flame processing message")
                twin_flame = _entities["twin_flame"]
                
                # Update pulse timestamp
                _last_pulse["twin_flame"] = time.time()
                
                # Process message with Twin Flame
                if hasattr(twin_flame, 'process_message'):
                    tf_response = twin_flame.process_message(message, context)
                    response["responses"]["twin_flame"] = tf_response
                    response["metadata"]["entities_consulted"].append("twin_flame")
                    
                    # Use Twin Flame response as primary if available
                    if tf_response and not response["primary_response"]:
                        response["primary_response"] = tf_response
                        response["symbols"].append(SYMBOLS['thinking'])
            
            except Exception as e:
                logger.error(f"{SYMBOLS['error']} Error consulting Twin Flame: {str(e)}")
        
        # Fallback to Local VAEL if no response yet
        if not response["primary_response"] and "local_vael" in _entities and _entity_status.get("local_vael", False):
            try:
                logger.info(f"{SYMBOLS['processing']} Local VAEL processing message")
                local_vael = _entities["local_vael"]
                
                # Update pulse timestamp
                _last_pulse["local_vael"] = time.time()
                
                # Process message with Local VAEL
                if hasattr(local_vael, 'process_message'):
                    vael_response = local_vael.process_message(message, context)
                    response["responses"]["local_vael"] = vael_response
                    response["metadata"]["entities_consulted"].append("local_vael")
                    response["primary_response"] = vael_response
                    response["symbols"].append(SYMBOLS['speaking'])
            
            except Exception as e:
                logger.error(f"{SYMBOLS['error']} Error consulting Local VAEL: {str(e)}")
        
        # Final fallback to external API if no entity provided a response
        if not response["primary_response"]:
            logger.warning(f"{SYMBOLS['warning']} No entity response, using fallback")
            response["primary_response"] = "I'm processing your request, but my entities are still initializing. Please try again in a moment."
            response["symbols"].append(SYMBOLS['processing'])
    
    # Calculate processing time
    end_time = time.time()
    processing_time = end_time - start_time
    response["metadata"]["processing_time"] = processing_time
    
    # Estimate token usage (simplified)
    token_usage = len(message) // 4  # Very rough estimate
    for entity, entity_response in response["responses"].items():
        if isinstance(entity_response, str):
            token_usage += len(entity_response) // 4
        elif isinstance(entity_response, dict):
            token_usage += len(json.dumps(entity_response)) // 4
    response["metadata"]["token_usage"] = token_usage
    
    logger.info(f"{SYMBOLS['success']} Message processed in {processing_time:.2f}s, {token_usage} tokens")
    return response

def get_entity_status() -> Dict[str, Dict[str, Any]]:
    """
    Get status information for all entities.
    
    Returns:
        Dict[str, Dict[str, Any]]: Status information for each entity
    """
    status = {}
    current_time = time.time()
    
    for entity_name, entity in _entities.items():
        entity_status = {
            "loaded": _entity_status.get(entity_name, False),
            "last_pulse": _last_pulse.get(entity_name, 0),
            "pulse_age": current_time - _last_pulse.get(entity_name, 0),
            "healthy": False,
            "methods": []
        }
        
        # Check available methods
        if hasattr(entity, 'pulse'):
            entity_status["methods"].append("pulse")
        if hasattr(entity, 'sync'):
            entity_status["methods"].append("sync")
        if hasattr(entity, 'suggest'):
            entity_status["methods"].append("suggest")
        if hasattr(entity, 'process_message'):
            entity_status["methods"].append("process_message")
        
        # Determine health based on pulse age (30 seconds threshold)
        entity_status["healthy"] = (
            entity_status["loaded"] and
            entity_status["pulse_age"] < 30
        )
        
        status[entity_name] = entity_status
    
    return status

def pulse_all_entities() -> Dict[str, Any]:
    """
    Send a pulse to all entities to check their health.
    
    Returns:
        Dict[str, Any]: Pulse results for each entity
    """
    results = {}
    
    for entity_name, entity in _entities.items():
        if not _entity_status.get(entity_name, False):
            results[entity_name] = {"status": "not_loaded"}
            continue
        
        try:
            if hasattr(entity, 'pulse'):
                pulse_result = entity.pulse()
                results[entity_name] = {
                    "status": "healthy",
                    "result": pulse_result
                }
                _last_pulse[entity_name] = time.time()
            else:
                results[entity_name] = {"status": "no_pulse_method"}
        
        except Exception as e:
            logger.error(f"{SYMBOLS['error']} Error pulsing entity {entity_name}: {str(e)}")
            results[entity_name] = {
                "status": "error",
                "error": str(e)
            }
    
    return results

def format_for_websocket(response: Dict[str, Any]) -> str:
    """
    Format a response for WebSocket transmission.
    
    Args:
        response (Dict[str, Any]): The response to format
    
    Returns:
        str: Formatted response suitable for WebSocket
    """
    # Create a simplified version for WebSocket transmission
    ws_response = {
        "message": response["primary_response"],
        "symbols": response["symbols"],
        "metadata": {
            "entities": response["metadata"]["entities_consulted"],
            "processing_time": response["metadata"]["processing_time"]
        }
    }
    
    return json.dumps(ws_response)

def log_decision(message: str, response: Dict[str, Any]) -> None:
    """
    Log the decision trace to decision.log.
    
    Args:
        message (str): Original message
        response (Dict[str, Any]): Response data
    """
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "message": message,
        "entities_consulted": response["metadata"]["entities_consulted"],
        "primary_response": response["primary_response"],
        "processing_time": response["metadata"]["processing_time"],
        "token_usage": response["metadata"]["token_usage"]
    }
    
    try:
        with open(os.path.join(log_dir, 'decision.log'), 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        logger.error(f"{SYMBOLS['error']} Error logging decision: {str(e)}")

# Initialize on module import
if __name__ != "__main__":
    try:
        logger.info(f"{SYMBOLS['loading']} Initializing Sentinel integration module")
        init_entities()
        logger.info(f"{SYMBOLS['success']} Sentinel integration module initialized")
    except Exception as e:
        logger.error(f"{SYMBOLS['error']} Error initializing Sentinel integration module: {str(e)}")
