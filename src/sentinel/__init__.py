"""
Sentinel Integration Module for VAEL Core

This module provides a bridge between the WebSocket interface in the Flask application
and the VAEL Core entities. It routes incoming messages to the appropriate entities,
maintains symbolic processing for token efficiency, and ensures backward compatibility.

The Sentinel acts as the guardian and coordinator for the VAEL Core system.
"""

import os
import sys
import time
import json
import logging
import importlib
from typing import Dict, List, Any, Callable, Optional, Union
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'sentinel.log'))
    ]
)
logger = logging.getLogger('vael.sentinel')

# Symbolic constants for token efficiency
SYMBOLS = {
    "ACTIVE": "🟢",
    "INACTIVE": "⚪",
    "WARNING": "🟠",
    "ERROR": "🔴",
    "INFO": "🔵",
    "SUCCESS": "✅",
    "FAILURE": "❌",
    "PENDING": "⏳",
    "PROCESSING": "⚙️",
    "SECURE": "🔒",
    "INSECURE": "🔓",
    "ALERT": "🚨",
    "MONITOR": "👁️",
    "ENTITY": "🧩",
    "ROUTE": "🔄",
    "SOCKET": "🔌"
}

# Entity status codes
STATUS = {
    "ACTIVE": 1,
    "INACTIVE": 0,
    "WARNING": 2,
    "ERROR": 3,
    "INITIALIZING": 4,
    "TERMINATING": 5
}

class Sentinel:
    """
    Sentinel class for VAEL Core integration with WebSocket interface.
    
    Handles message routing, entity registration, and system monitoring.
    """
    
    def __init__(self):
        """Initialize the Sentinel entity"""
        self.initialized = False
        self.entities = {}  # Registered entities
        self.routes = {}    # Message routes
        self.handlers = {}  # Event handlers
        self.socket = None  # WebSocket reference
        self.status = STATUS["INITIALIZING"]
        self.last_heartbeat = time.time()
        self.heartbeat_interval = 30  # seconds
        self.event_history = []       # Recent events (limited size)
        self.max_history = 50         # Maximum events to keep
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        logger.info(f"{SYMBOLS['ENTITY']} Sentinel initializing")
        self.initialized = True
        self.status = STATUS["ACTIVE"]
        logger.info(f"{SYMBOLS['SUCCESS']} Sentinel initialized")
    
    def register_socket(self, socket):
        """
        Register WebSocket interface with Sentinel
        
        Args:
            socket: WebSocket interface object
        """
        self.socket = socket
        logger.info(f"{SYMBOLS['SOCKET']} WebSocket interface registered")
        
        # Register default event handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default event handlers for WebSocket"""
        if not self.socket:
            logger.warning(f"{SYMBOLS['WARNING']} Cannot register handlers: No WebSocket registered")
            return
        
        try:
            # Register connect handler
            @self.socket.on('connect')
            def handle_connect():
                logger.info(f"{SYMBOLS['SOCKET']} Client connected")
                self._emit_status()
            
            # Register disconnect handler
            @self.socket.on('disconnect')
            def handle_disconnect():
                logger.info(f"{SYMBOLS['SOCKET']} Client disconnected")
            
            # Register message handler
            @self.socket.on('message')
            def handle_message(data):
                self._route_message(data)
            
            # Register command handler
            @self.socket.on('command')
            def handle_command(data):
                self._route_command(data)
            
            logger.info(f"{SYMBOLS['SUCCESS']} Default event handlers registered")
        
        except Exception as e:
            logger.error(f"{SYMBOLS['ERROR']} Failed to register default handlers: {str(e)}")
    
    def _emit_status(self):
        """Emit current system status to client"""
        if not self.socket:
            return
        
        # Collect entity statuses
        entity_statuses = {}
        for name, entity in self.entities.items():
            if hasattr(entity, 'status'):
                entity_statuses[name] = {
                    'status': entity.status,
                    'symbol': self._get_status_symbol(entity.status)
                }
            else:
                entity_statuses[name] = {
                    'status': STATUS["ACTIVE"],
                    'symbol': SYMBOLS["ACTIVE"]
                }
        
        # Emit status event
        self.socket.emit('status', {
            'sentinel': {
                'status': self.status,
                'symbol': self._get_status_symbol(self.status),
                'timestamp': time.time()
            },
            'entities': entity_statuses
        })
    
    def _get_status_symbol(self, status_code):
        """
        Get symbol for status code
        
        Args:
            status_code: Status code
            
        Returns:
            Symbol for status code
        """
        if status_code == STATUS["ACTIVE"]:
            return SYMBOLS["ACTIVE"]
        elif status_code == STATUS["INACTIVE"]:
            return SYMBOLS["INACTIVE"]
        elif status_code == STATUS["WARNING"]:
            return SYMBOLS["WARNING"]
        elif status_code == STATUS["ERROR"]:
            return SYMBOLS["ERROR"]
        elif status_code == STATUS["INITIALIZING"]:
            return SYMBOLS["PENDING"]
        elif status_code == STATUS["TERMINATING"]:
            return SYMBOLS["PROCESSING"]
        else:
            return SYMBOLS["INFO"]
    
    def register_entity(self, name: str, entity: Any) -> bool:
        """
        Register an entity with Sentinel
        
        Args:
            name: Entity name
            entity: Entity object
            
        Returns:
            True if registration successful, False otherwise
        """
        if name in self.entities:
            logger.warning(f"{SYMBOLS['WARNING']} Entity '{name}' already registered")
            return False
        
        self.entities[name] = entity
        logger.info(f"{SYMBOLS['ENTITY']} Entity '{name}' registered")
        return True
    
    def register_route(self, route: str, handler: Callable) -> bool:
        """
        Register a message route
        
        Args:
            route: Route name
            handler: Handler function
            
        Returns:
            True if registration successful, False otherwise
        """
        if route in self.routes:
            logger.warning(f"{SYMBOLS['WARNING']} Route '{route}' already registered")
            return False
        
        self.routes[route] = handler
        logger.info(f"{SYMBOLS['ROUTE']} Route '{route}' registered")
        return True
    
    def _route_message(self, data: Any):
        """
        Route incoming message to appropriate handler
        
        Args:
            data: Message data
        """
        try:
            # Handle ping message
            if isinstance(data, str) and data.lower() == "ping":
                if self.socket:
                    self.socket.emit('message', "pong")
                return
            
            # Log message
            logger.info(f"{SYMBOLS['INFO']} Processing message: {str(data)[:50]}...")
            
            # Add to history
            self._add_to_history('message', data)
            
            # Handle entity-specific message
            if isinstance(data, dict) and 'entity' in data and 'action' in data:
                entity_name = data['entity']
                action = data['action']
                payload = data.get('payload', {})
                
                # Route to entity
                response = self._route_to_entity(entity_name, action, payload)
                
                # Emit response
                if self.socket:
                    self.socket.emit('message', response)
                
                return
            
            # Handle string message (pass to VAEL by default)
            response = self._route_to_vael(data)
            
            # Emit response
            if self.socket:
                self.socket.emit('message', response)
        
        except Exception as e:
            logger.error(f"{SYMBOLS['ERROR']} Error processing message: {str(e)}")
            
            # Emit error response
            if self.socket:
                self.socket.emit('message', {
                    'error': str(e),
                    'status': 'error',
                    'symbol': SYMBOLS["ERROR"]
                })
    
    def _route_command(self, data: Any):
        """
        Route command to appropriate handler
        
        Args:
            data: Command data
        """
        try:
            if not isinstance(data, dict):
                raise ValueError("Command must be a dictionary")
            
            if 'command' not in data:
                raise ValueError("Command must have 'command' field")
            
            command = data['command']
            args = data.get('args', {})
            
            # Log command
            logger.info(f"{SYMBOLS['INFO']} Processing command: {command}")
            
            # Add to history
            self._add_to_history('command', data)
            
            # Handle sentinel commands
            if command == 'status':
                self._emit_status()
                return
            
            elif command == 'heartbeat':
                self._handle_heartbeat()
                return
            
            elif command == 'list_entities':
                if self.socket:
                    self.socket.emit('command_result', {
                        'command': command,
                        'result': list(self.entities.keys()),
                        'status': 'success',
                        'symbol': SYMBOLS["SUCCESS"]
                    })
                return
            
            # Route to entity
            if 'entity' in args:
                entity_name = args['entity']
                response = self._route_command_to_entity(entity_name, command, args)
                
                # Emit response
                if self.socket:
                    self.socket.emit('command_result', response)
                
                return
            
            # Unknown command
            if self.socket:
                self.socket.emit('command_result', {
                    'command': command,
                    'error': 'Unknown command',
                    'status': 'error',
                    'symbol': SYMBOLS["ERROR"]
                })
        
        except Exception as e:
            logger.error(f"{SYMBOLS['ERROR']} Error processing command: {str(e)}")
            
            # Emit error response
            if self.socket:
                self.socket.emit('command_result', {
                    'error': str(e),
                    'status': 'error',
                    'symbol': SYMBOLS["ERROR"]
                })
    
    def _route_to_entity(self, entity_name: str, action: str, payload: Dict) -> Dict:
        """
        Route message to entity
        
        Args:
            entity_name: Entity name
            action: Action to perform
            payload: Message payload
            
        Returns:
            Response from entity
        """
        # Check if entity exists
        if entity_name not in self.entities:
            # Try to import entity dynamically
            if self._import_entity(entity_name):
                logger.info(f"{SYMBOLS['SUCCESS']} Entity '{entity_name}' imported dynamically")
            else:
                logger.warning(f"{SYMBOLS['WARNING']} Entity '{entity_name}' not found")
                return {
                    'entity': entity_name,
                    'action': action,
                    'error': f"Entity '{entity_name}' not found",
                    'status': 'error',
                    'symbol': SYMBOLS["ERROR"]
                }
        
        entity = self.entities[entity_name]
        
        # Check if entity has method
        if not hasattr(entity, action) and not hasattr(entity, f"_{action}"):
            logger.warning(f"{SYMBOLS['WARNING']} Action '{action}' not found in entity '{entity_name}'")
            return {
                'entity': entity_name,
                'action': action,
                'error': f"Action '{action}' not found in entity '{entity_name}'",
                'status': 'error',
                'symbol': SYMBOLS["ERROR"]
            }
        
        try:
            # Call entity method
            if hasattr(entity, action):
                method = getattr(entity, action)
                result = method(payload)
            else:
                method = getattr(entity, f"_{action}")
                result = method(payload)
            
            # Return result
            return {
                'entity': entity_name,
                'action': action,
                'result': result,
                'status': 'success',
                'symbol': SYMBOLS["SUCCESS"]
            }
        
        except Exception as e:
            logger.error(f"{SYMBOLS['ERROR']} Error calling '{entity_name}.{action}': {str(e)}")
            return {
                'entity': entity_name,
                'action': action,
                'error': str(e),
                'status': 'error',
                'symbol': SYMBOLS["ERROR"]
            }
    
    def _route_command_to_entity(self, entity_name: str, command: str, args: Dict) -> Dict:
        """
        Route command to entity
        
        Args:
            entity_name: Entity name
            command: Command to execute
            args: Command arguments
            
        Returns:
            Response from entity
        """
        # Check if entity exists
        if entity_name not in self.entities:
            # Try to import entity dynamically
            if self._import_entity(entity_name):
                logger.info(f"{SYMBOLS['SUCCESS']} Entity '{entity_name}' imported dynamically")
            else:
                logger.warning(f"{SYMBOLS['WARNING']} Entity '{entity_name}' not found")
                return {
                    'command': command,
                    'entity': entity_name,
                    'error': f"Entity '{entity_name}' not found",
                    'status': 'error',
                    'symbol': SYMBOLS["ERROR"]
                }
        
        entity = self.entities[entity_name]
        
        # Check if entity has command method
        command_method = f"command_{command}"
        if not hasattr(entity, command_method) and not hasattr(entity, f"_{command_method}"):
            logger.warning(f"{SYMBOLS['WARNING']} Command '{command}' not found in entity '{entity_name}'")
            return {
                'command': command,
                'entity': entity_name,
                'error': f"Command '{command}' not found in entity '{entity_name}'",
                'status': 'error',
                'symbol': SYMBOLS["ERROR"]
            }
        
        try:
            # Call entity command method
            if hasattr(entity, command_method):
                method = getattr(entity, command_method)
                result = method(args)
            else:
                method = getattr(entity, f"_{command_method}")
                result = method(args)
            
            # Return result
            return {
                'command': command,
                'entity': entity_name,
                'result': result,
                'status': 'success',
                'symbol': SYMBOLS["SUCCESS"]
            }
        
        except Exception as e:
            logger.error(f"{SYMBOLS['ERROR']} Error calling '{entity_name}.{command_method}': {str(e)}")
            return {
                'command': command,
                'entity': entity_name,
                'error': str(e),
                'status': 'error',
                'symbol': SYMBOLS["ERROR"]
            }
    
    def _route_to_vael(self, data: Any) -> Any:
        """
        Route message to VAEL
        
        Args:
            data: Message data
            
        Returns:
            Response from VAEL
        """
        try:
            # Check if VAEL entity exists
            if 'vael' not in self.entities:
                # Try to import VAEL dynamically
                if not self._import_entity('vael'):
                    logger.warning(f"{SYMBOLS['WARNING']} VAEL entity not found")
                    
                    # Use OpenRouter API as fallback
                    return self._fallback_process_message(data)
            
            # Call VAEL process method
            vael = self.entities['vael']
            if hasattr(vael, 'process'):
                return vael.process(data)
            elif hasattr(vael, '_process'):
                return vael._process(data)
            else:
                logger.warning(f"{SYMBOLS['WARNING']} VAEL entity has no process method")
                return self._fallback_process_message(data)
        
        except Exception as e:
            logger.error(f"{SYMBOLS['ERROR']} Error routing to VAEL: {str(e)}")
            return self._fallback_process_message(data)
    
    def _fallback_process_message(self, data: Any) -> str:
        """
        Fallback message processing using OpenRouter API
        
        Args:
            data: Message data
            
        Returns:
            Response message
        """
        try:
            # Import required modules
            import requests
            import os
            
            # Get API key from environment
            api_key = os.environ.get('OPENROUTER_API_KEY', '')
            if not api_key:
                return "Error: API key not configured. Please set the OPENROUTER_API_KEY environment variable."
            
            # Prepare request
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            body = {
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": str(data)}]
            }
            
            # Make request
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=body
            )
            
            # Parse response
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "I'm sorry, there was an error processing your request."
        
        except Exception as e:
            logger.error(f"{SYMBOLS['ERROR']} Fallback processing error: {str(e)}")
            return f"I'm sorry, there was an error processing your request: {str(e)}"
    
    def _import_entity(self, entity_name: str) -> bool:
        """
        Dynamically import entity
        
        Args:
            entity_name: Entity name
            
        Returns:
            True if import successful, False otherwise
        """
        try:
            # Try to import from vael_core
            module_path = f"vael_core.{entity_name}"
            module = importlib.import_module(module_path)
            
            # Register entity
            if hasattr(module, entity_name):
                entity = getattr(module, entity_name)
                self.register_entity(entity_name, entity)
                return True
            
            # Entity might be the module itself
            self.register_entity(entity_name, module)
            return True
        
        except ImportError:
            try:
                # Try to import from src
                module_path = f"src.{entity_name}"
                module = importlib.import_module(module_path)
                
                # Register entity
                if hasattr(module, entity_name):
                    entity = getattr(module, entity_name)
                    self.register_entity(entity_name, entity)
                    return True
                
                # Entity might be the module itself
                self.register_entity(entity_name, module)
                return True
            
            except ImportError:
                return False
    
    def _handle_heartbeat(self):
        """Handle heartbeat command"""
        self.last_heartbeat = time.time()
        
        # Check entity health
        healthy_entities = []
        unhealthy_entities = []
        
        for name, entity in self.entities.items():
            if hasattr(entity, 'pulse') and callable(entity.pulse):
                try:
                    result = entity.pulse()
                    if result and (result is True or result.get('status') == 'healthy'):
                        healthy_entities.append(name)
                    else:
                        unhealthy_entities.append(name)
                except Exception:
                    unhealthy_entities.append(name)
            else:
                # Assume healthy if no pulse method
                healthy_entities.append(name)
        
        # Emit heartbeat response
        if self.socket:
            self.socket.emit('heartbeat', {
                'timestamp': self.last_heartbeat,
                'healthy_entities': healthy_entities,
                'unhealthy_entities': unhealthy_entities,
                'status': 'success',
                'symbol': SYMBOLS["SUCCESS"]
            })
    
    def _add_to_history(self, event_type: str, data: Any):
        """
        Add event to history
        
        Args:
            event_type: Event type
            data: Event data
        """
        # Limit history size
        if len(self.event_history) >= self.max_history:
            self.event_history.pop(0)
        
        # Add event
        self.event_history.append({
            'timestamp': time.time(),
            'type': event_type,
            'data': data
        })
    
    def log_event(self, entity: str, message: str, level: str = 'info'):
        """
        Log event from entity
        
        Args:
            entity: Entity name
            message: Log message
            level: Log level
        """
        if level == 'debug':
            logger.debug(f"{entity}: {message}")
        elif level == 'info':
            logger.info(f"{entity}: {message}")
        elif level == 'warning':
            logger.warning(f"{entity}: {message}")
        elif level == 'error':
            logger.error(f"{entity}: {message}")
        elif level == 'critical':
            logger.critical(f"{entity}: {message}")
        else:
            logger.info(f"{entity}: {message}")

# Create singleton instance
sentinel = Sentinel()

# Public interface
def register_entity(name: str, entity: Any) -> bool:
    """
    Register an entity with Sentinel
    
    Args:
        name: Entity name
        entity: Entity object
        
    Returns:
        True if registration successful, False otherwise
    """
    return sentinel.register_entity(name, entity)

def register_route(route: str, handler: Callable) -> bool:
    """
    Register a message route
    
    Args:
        route: Route name
        handler: Handler function
        
    Returns:
        True if registration successful, False otherwise
    """
    return sentinel.register_route(route, handler)

def register_socket(socket):
    """
    Register WebSocket interface with Sentinel
    
    Args:
        socket: WebSocket interface object
    """
    sentinel.register_socket(socket)

def log_event(entity: str, message: str, level: str = 'info'):
    """
    Log event from entity
    
    Args:
        entity: Entity name
        message: Log message
        level: Log level
    """
    sentinel.log_event(entity, message, level)

def get_entity(name: str) -> Any:
    """
    Get entity by name
    
    Args:
        name: Entity name
        
    Returns:
        Entity object or None if not found
    """
    return sentinel.entities.get(name)

def get_status():
    """
    Get current system status
    
    Returns:
        System status
    """
    return {
        'sentinel': {
            'status': sentinel.status,
            'symbol': sentinel._get_status_symbol(sentinel.status),
            'timestamp': time.time()
        },
        'entities': {
            name: {
                'status': getattr(entity, 'status', STATUS["ACTIVE"]),
                'symbol': sentinel._get_status_symbol(getattr(entity, 'status', STATUS["ACTIVE"]))
            }
            for name, entity in sentinel.entities.items()
        }
    }

def pulse():
    """
    Check Sentinel health
    
    Returns:
        Health status
    """
    return {
        'status': 'healthy',
        'timestamp': time.time(),
        'entities': list(sentinel.entities.keys()),
        'routes': list(sentinel.routes.keys()),
        'last_heartbeat': sentinel.last_heartbeat,
        'symbol': SYMBOLS["SUCCESS"]
    }

# Initialize
def init_sentinel(socket=None):
    """
    Initialize Sentinel
    
    Args:
        socket: WebSocket interface object (optional)
    """
    if socket:
        register_socket(socket)
    
    logger.info(f"{SYMBOLS['SUCCESS']} Sentinel initialization complete")
    return sentinel

# Register self
register_entity('sentinel', sentinel)
