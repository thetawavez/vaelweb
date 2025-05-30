"""
VAEL Core - Sentinel Integration Module
=======================================

This module provides utilities for integrating the Sentinel security
system with other VAEL components such as the WebSocket server,
NEXUS IDS, and Antibody self-healing system.

Usage:
    from sentinel.integration import (
        register_with_socketio, register_with_nexus,
        register_with_antibody, broadcast_security_alert
    )
"""

import logging
import json
import time
import threading
from typing import Dict, List, Tuple, Optional, Any, Callable
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

# Type aliases for clarity
AlertHandler = Callable[[Dict[str, Any]], None]
MessageFilter = Callable[[str], Tuple[bool, str]]
SecurityEvent = Dict[str, Any]

# Global registry of alert handlers
_alert_handlers: List[AlertHandler] = []

# Global registry of message filters
_message_filters: List[MessageFilter] = []

# Last security event
_last_security_event: Optional[SecurityEvent] = None

# Sentinel instance reference (set by register_sentinel)
_sentinel_instance = None

def register_sentinel(sentinel_instance) -> None:
    """
    Register the Sentinel instance for integration functions.
    
    Args:
        sentinel_instance: The Sentinel instance to register
    """
    global _sentinel_instance
    _sentinel_instance = sentinel_instance
    logger.info("Sentinel instance registered for integration")

def register_with_socketio(socketio) -> None:
    """
    Register Sentinel with Flask-SocketIO for WebSocket monitoring.
    
    This function integrates Sentinel with the WebSocket server by:
    1. Adding event handlers for incoming messages
    2. Setting up a heartbeat emitter
    3. Registering security event broadcasts
    
    Args:
        socketio: The Flask-SocketIO instance
    """
    if _sentinel_instance is None:
        logger.error("Cannot register with SocketIO: No Sentinel instance registered")
        return
    
    logger.info("Registering Sentinel with SocketIO")
    
    # Create a message interceptor for 'message' events
    @socketio.on('message')
    def _intercept_message(data):
        # Skip if it's a system message
        if isinstance(data, str) and data.lower() == "ping":
            return
        
        # Extract the message content
        message = data
        if isinstance(data, dict) and 'text' in data:
            message = data['text']
        elif isinstance(data, dict) and 'message' in data:
            message = data['message']
        
        # Apply all registered message filters
        for filter_func in _message_filters:
            is_safe, reason = filter_func(message)
            if not is_safe:
                # Block the message and notify the client
                socketio.emit('security_alert', {
                    'level': 'warning',
                    'message': f"Message blocked: {reason}",
                    'timestamp': datetime.now().isoformat()
                })
                return False  # Prevent further processing
    
    # Register a pulse emitter
    def _emit_sentinel_pulse():
        while True:
            try:
                pulse_data = _sentinel_instance.pulse()
                socketio.emit('pulse', pulse_data)
                time.sleep(5)  # Emit pulse every 5 seconds
            except Exception as e:
                logger.error(f"Error in Sentinel pulse emitter: {e}")
                time.sleep(10)  # Longer interval on error
    
    # Start the pulse emitter in a background thread
    pulse_thread = threading.Thread(
        target=_emit_sentinel_pulse,
        daemon=True,
        name="sentinel-pulse"
    )
    pulse_thread.start()
    
    # Register a function to broadcast security alerts
    def _broadcast_alert(alert_data):
        socketio.emit('security_alert', alert_data)
    
    register_alert_handler(_broadcast_alert)
    
    logger.info("Sentinel successfully registered with SocketIO")

def register_with_nexus(nexus_instance) -> None:
    """
    Register Sentinel with NEXUS for advanced threat detection.
    
    This function integrates Sentinel with the NEXUS IDS by:
    1. Sharing security rules and patterns
    2. Setting up a communication channel for alerts
    3. Registering Sentinel as a security provider
    
    Args:
        nexus_instance: The NEXUS instance
    """
    if _sentinel_instance is None:
        logger.error("Cannot register with NEXUS: No Sentinel instance registered")
        return
    
    logger.info("Registering Sentinel with NEXUS IDS")
    
    try:
        # Register Sentinel as a security provider
        nexus_instance.register_security_provider("sentinel", {
            "name": "Sentinel",
            "version": getattr(_sentinel_instance, "__version__", "0.1.0"),
            "capabilities": ["message_scanning", "threat_detection", "pulse_monitoring"]
        })
        
        # Share Sentinel rules with NEXUS
        if hasattr(_sentinel_instance, "threat_patterns"):
            patterns = [
                pattern.pattern if hasattr(pattern, "pattern") else str(pattern)
                for pattern in _sentinel_instance.threat_patterns
            ]
            nexus_instance.update_patterns("sentinel", patterns)
        
        if hasattr(_sentinel_instance, "blocked_terms"):
            nexus_instance.update_blocked_terms("sentinel", list(_sentinel_instance.blocked_terms))
        
        # Register NEXUS alert handler
        def _handle_nexus_alert(alert_data):
            if alert_data.get("source") != "sentinel":  # Avoid loops
                broadcast_security_alert({
                    "level": alert_data.get("severity", "warning"),
                    "message": alert_data.get("message", "NEXUS security alert"),
                    "source": "nexus",
                    "timestamp": datetime.now().isoformat(),
                    "details": alert_data
                })
        
        nexus_instance.register_alert_handler(_handle_nexus_alert)
        
        # Register Sentinel as a message filter in NEXUS
        def _sentinel_filter(message):
            return _sentinel_instance.scan(message)
        
        nexus_instance.register_message_filter("sentinel", _sentinel_filter)
        
        logger.info("Sentinel successfully registered with NEXUS IDS")
    
    except Exception as e:
        logger.error(f"Error registering Sentinel with NEXUS: {e}")

def register_with_antibody(antibody_instance) -> None:
    """
    Register Sentinel with Antibody for self-healing capabilities.
    
    This function integrates Sentinel with the Antibody system by:
    1. Providing security event hooks
    2. Registering for healing notifications
    3. Setting up a communication channel for remediation
    
    Args:
        antibody_instance: The Antibody instance
    """
    if _sentinel_instance is None:
        logger.error("Cannot register with Antibody: No Sentinel instance registered")
        return
    
    logger.info("Registering Sentinel with Antibody self-healing system")
    
    try:
        # Register Sentinel as a security event source
        antibody_instance.register_event_source("sentinel", {
            "name": "Sentinel",
            "version": getattr(_sentinel_instance, "__version__", "0.1.0"),
            "event_types": ["message_blocked", "threat_detected", "anomaly_detected"]
        })
        
        # Register event handler for Antibody remediation notifications
        def _handle_remediation(remediation_data):
            logger.info(f"Antibody remediation applied: {remediation_data.get('action')}")
            
            # Update Sentinel rules if provided
            if 'new_patterns' in remediation_data:
                try:
                    for pattern in remediation_data['new_patterns']:
                        _sentinel_instance.threat_patterns.append(pattern)
                    logger.info(f"Added {len(remediation_data['new_patterns'])} new patterns from Antibody")
                except Exception as e:
                    logger.error(f"Error updating patterns from Antibody: {e}")
            
            # Update blocked terms if provided
            if 'new_blocked_terms' in remediation_data:
                try:
                    _sentinel_instance.blocked_terms.update(remediation_data['new_blocked_terms'])
                    logger.info(f"Added {len(remediation_data['new_blocked_terms'])} new blocked terms from Antibody")
                except Exception as e:
                    logger.error(f"Error updating blocked terms from Antibody: {e}")
        
        antibody_instance.register_remediation_handler("sentinel", _handle_remediation)
        
        # Register a security event handler that forwards to Antibody
        def _forward_to_antibody(event_data):
            antibody_instance.process_security_event({
                "source": "sentinel",
                "type": event_data.get("type", "security_alert"),
                "severity": event_data.get("level", "warning"),
                "message": event_data.get("message", ""),
                "timestamp": event_data.get("timestamp", datetime.now().isoformat()),
                "details": event_data
            })
        
        register_alert_handler(_forward_to_antibody)
        
        logger.info("Sentinel successfully registered with Antibody")
    
    except Exception as e:
        logger.error(f"Error registering Sentinel with Antibody: {e}")

def register_message_filter(filter_func: MessageFilter) -> None:
    """
    Register a message filter function.
    
    Args:
        filter_func: Function that takes a message string and returns (is_safe, reason)
    """
    _message_filters.append(filter_func)
    logger.debug(f"Message filter registered (total: {len(_message_filters)})")

def register_alert_handler(handler_func: AlertHandler) -> None:
    """
    Register a security alert handler function.
    
    Args:
        handler_func: Function that takes an alert data dictionary
    """
    _alert_handlers.append(handler_func)
    logger.debug(f"Alert handler registered (total: {len(_alert_handlers)})")

def broadcast_security_alert(alert_data: Dict[str, Any]) -> None:
    """
    Broadcast a security alert to all registered handlers.
    
    Args:
        alert_data: Dictionary with alert information
    """
    global _last_security_event
    
    # Add timestamp if not present
    if 'timestamp' not in alert_data:
        alert_data['timestamp'] = datetime.now().isoformat()
    
    # Store as last security event
    _last_security_event = alert_data
    
    # Log the alert
    level = alert_data.get('level', 'warning').lower()
    message = alert_data.get('message', 'Security alert')
    
    if level == 'critical':
        logger.critical(f"SECURITY ALERT: {message}")
    elif level == 'high':
        logger.error(f"SECURITY ALERT: {message}")
    elif level == 'warning':
        logger.warning(f"SECURITY ALERT: {message}")
    else:
        logger.info(f"SECURITY ALERT: {message}")
    
    # Notify all handlers
    for handler in _alert_handlers:
        try:
            handler(alert_data)
        except Exception as e:
            logger.error(f"Error in security alert handler: {e}")

def get_last_security_event() -> Optional[SecurityEvent]:
    """
    Get the last security event.
    
    Returns:
        The last security event or None if no events have occurred
    """
    return _last_security_event

def create_sentinel_message_filter(sentinel_instance) -> MessageFilter:
    """
    Create a message filter function using a Sentinel instance.
    
    Args:
        sentinel_instance: The Sentinel instance to use for filtering
        
    Returns:
        A message filter function
    """
    def _filter(message: str) -> Tuple[bool, str]:
        return sentinel_instance.scan(message)
    
    return _filter

def setup_entity_communication(entity_name: str, entity_instance: Any) -> None:
    """
    Set up communication between Sentinel and another entity.
    
    This is a generic function for establishing bidirectional
    communication with other VAEL entities.
    
    Args:
        entity_name: Name of the entity
        entity_instance: The entity instance
    """
    if _sentinel_instance is None:
        logger.error(f"Cannot setup communication with {entity_name}: No Sentinel instance registered")
        return
    
    logger.info(f"Setting up communication with {entity_name}")
    
    # Register entity's suggest method if available
    if hasattr(entity_instance, 'suggest'):
        def _handle_suggestions():
            try:
                suggestions = entity_instance.suggest()
                if suggestions:
                    logger.info(f"Received {len(suggestions)} suggestions from {entity_name}")
                    for suggestion in suggestions:
                        if suggestion.get('severity', '').lower() == 'critical':
                            broadcast_security_alert({
                                'level': 'critical',
                                'message': suggestion.get('message', f"Critical suggestion from {entity_name}"),
                                'source': entity_name,
                                'action': suggestion.get('action', '')
                            })
            except Exception as e:
                logger.error(f"Error processing suggestions from {entity_name}: {e}")
        
        # Schedule periodic suggestion checks
        suggestion_thread = threading.Thread(
            target=lambda: (
                _handle_suggestions(),
                time.sleep(60),  # Check suggestions every minute
                suggestion_thread.run()
            ),
            daemon=True,
            name=f"sentinel-{entity_name}-suggestions"
        )
        suggestion_thread.start()
    
    # Register entity's pulse method if available
    if hasattr(entity_instance, 'pulse'):
        def _handle_pulse():
            try:
                pulse_data = entity_instance.pulse()
                logger.debug(f"Received pulse from {entity_name}: {pulse_data}")
                # Check for critical status in pulse
                if pulse_data.get('status') == 'critical':
                    broadcast_security_alert({
                        'level': 'critical',
                        'message': f"Critical status in {entity_name} pulse",
                        'source': entity_name,
                        'details': pulse_data
                    })
            except Exception as e:
                logger.error(f"Error processing pulse from {entity_name}: {e}")
        
        # Register a handler for entity pulses
        if hasattr(entity_instance, 'register_pulse_handler'):
            entity_instance.register_pulse_handler('sentinel', _handle_pulse)
    
    logger.info(f"Communication with {entity_name} established")
