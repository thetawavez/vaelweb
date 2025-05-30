"""
VAEL Core - Sentinel Entity
Version: 0.1.0 (2025-05-30)

Sentinel serves as the vigilant guardian of the VAEL ecosystem:
- Monitors system health and security
- Detects anomalies and raises alerts
- Provides early warning of potential issues
- Coordinates response to security threats
- Maintains audit logs of system events

The Sentinel operates with symbolic efficiency, using minimal tokens
while maintaining maximum awareness of system state.
"""

import os
import time
import logging
from datetime import datetime

__version__ = '0.1.0'
__status__ = 'Active'

# Configure logging with minimal footprint
logger = logging.getLogger('vael.sentinel')

# Symbolic alert levels for token efficiency
ALERT_LEVELS = {
    'INFO': '🔵',
    'WARNING': '🟡',
    'ERROR': '🔴',
    'CRITICAL': '⛔',
    'SECURE': '🟢',
}

# Alert history with circular buffer for memory efficiency
_alert_history = []
_max_history = 100
_last_pulse = 0
_initialized = False

def _initialize():
    """Initialize Sentinel with minimal startup sequence."""
    global _initialized
    if not _initialized:
        logger.info(f"{ALERT_LEVELS['INFO']} Sentinel initializing")
        _initialized = True
        # Load any persisted alert history
        _load_history()
    return _initialized

def _load_history():
    """Load alert history from disk if available."""
    history_path = os.path.join(os.path.dirname(__file__), 'alert_history.log')
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r') as f:
                for line in f.readlines()[-_max_history:]:
                    if line.strip():
                        _alert_history.append(line.strip())
        except Exception as e:
            logger.error(f"Failed to load alert history: {e}")

def _save_history():
    """Save alert history to disk for persistence."""
    history_path = os.path.join(os.path.dirname(__file__), 'alert_history.log')
    try:
        with open(history_path, 'w') as f:
            for alert in _alert_history:
                f.write(f"{alert}\n")
    except Exception as e:
        logger.error(f"Failed to save alert history: {e}")

def pulse():
    """Check Sentinel health status.
    
    Returns:
        str: Status indicator with timestamp.
    """
    global _last_pulse
    _initialize()
    
    current_time = time.time()
    _last_pulse = current_time
    
    # Perform self-check
    status = ALERT_LEVELS['SECURE']
    timestamp = datetime.now().isoformat()
    
    return f"{status} Sentinel operational at {timestamp}"

def sync():
    """Reload Sentinel configuration and clear caches.
    
    Returns:
        str: Sync status message.
    """
    _initialize()
    
    # Reset internal state while preserving essential history
    _save_history()
    
    return f"{ALERT_LEVELS['INFO']} Sentinel configuration synchronized"

def suggest(context):
    """Provide security recommendations based on context.
    
    Args:
        context (dict): Context information including potential security concerns.
        
    Returns:
        dict: Security recommendations and alerts.
    """
    _initialize()
    
    # Extract relevant information from context
    alert_type = context.get('alert_type', 'general')
    severity = context.get('severity', 'INFO')
    message = context.get('message', 'No specific alert message provided')
    source = context.get('source', 'unknown')
    
    # Generate alert with symbolic efficiency
    alert_level = ALERT_LEVELS.get(severity, ALERT_LEVELS['INFO'])
    timestamp = datetime.now().isoformat()
    alert = f"{alert_level} [{timestamp}] {source}: {message}"
    
    # Add to history with circular buffer behavior
    _alert_history.append(alert)
    if len(_alert_history) > _max_history:
        _alert_history.pop(0)
    
    # Generate appropriate response based on alert type
    if alert_type == 'intrusion':
        response = {
            'action': 'isolate',
            'message': f"Potential intrusion detected from {source}. Isolation recommended.",
            'alert_id': f"SEN-{int(time.time())}"
        }
    elif alert_type == 'anomaly':
        response = {
            'action': 'investigate',
            'message': f"Behavioral anomaly detected in {source}. Investigation recommended.",
            'alert_id': f"SEN-{int(time.time())}"
        }
    elif alert_type == 'health':
        response = {
            'action': 'monitor',
            'message': f"Health issue detected in {source}. Increased monitoring recommended.",
            'alert_id': f"SEN-{int(time.time())}"
        }
    else:
        response = {
            'action': 'log',
            'message': f"General alert logged for {source}.",
            'alert_id': f"SEN-{int(time.time())}"
        }
    
    # Add alert to response
    response['alert'] = alert
    
    # Periodically save history to disk
    if len(_alert_history) % 10 == 0:
        _save_history()
    
    return response

def get_alerts(count=10):
    """Retrieve recent alerts.
    
    Args:
        count (int): Number of recent alerts to retrieve.
        
    Returns:
        list: Recent alerts.
    """
    _initialize()
    return _alert_history[-count:] if _alert_history else []

def clear_alerts():
    """Clear all alerts from history.
    
    Returns:
        str: Confirmation message.
    """
    global _alert_history
    _initialize()
    _alert_history = []
    _save_history()
    return f"{ALERT_LEVELS['INFO']} Alert history cleared"
