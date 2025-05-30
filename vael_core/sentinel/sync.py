"""
VAEL Core - Sentinel Sync Module
Version: 0.1.0 (2025-05-30)

This module handles configuration synchronization for the Sentinel entity.
It provides mechanisms for reloading configuration settings, resetting caches,
and ensuring configuration consistency across the system.

The sync process is designed to be token-efficient, using symbolic indicators
and preserving essential data while refreshing configuration.
"""

import os
import json
import time
import logging
import shutil
from datetime import datetime
from pathlib import Path

# Configure logging with minimal footprint
logger = logging.getLogger('vael.sentinel.sync')

# Symbolic status indicators for token efficiency
SYNC_STATUS = {
    'SUCCESS': '🟢',
    'PARTIAL': '🟡',
    'FAILED': '🔴',
    'UNCHANGED': '⚪',
}

# Default configuration with fallback values
DEFAULT_CONFIG = {
    'alert_history_size': 100,
    'check_interval': 60,
    'log_level': 'INFO',
    'alert_levels': {
        'INFO': '🔵',
        'WARNING': '🟡',
        'ERROR': '🔴',
        'CRITICAL': '⛔',
        'SECURE': '🟢',
    },
    'components': {
        'memory': True,
        'cpu': True,
        'disk': True,
        'logs': True,
        'alerts': True,
    },
    'thresholds': {
        'memory': {
            'warning': 75,
            'critical': 90,
        },
        'cpu': {
            'warning': 70,
            'critical': 90,
        },
        'disk': {
            'warning': 85,
            'critical': 95,
        },
    },
    'sync_interval': 3600,  # seconds
}

# Module state
_config = {}
_config_path = None
_last_sync = 0
_sync_count = 0

def _get_config_path():
    """Get the path to the configuration file."""
    global _config_path
    if not _config_path:
        # Try several possible locations
        locations = [
            os.path.join(os.path.dirname(__file__), 'config.json'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'sentinel.json'),
            os.path.join(os.path.expanduser('~'), '.vael', 'sentinel.json'),
        ]
        
        for loc in locations:
            if os.path.exists(loc):
                _config_path = loc
                break
        
        # If no config file found, use the first location
        if not _config_path:
            _config_path = locations[0]
            
    return _config_path

def _load_config():
    """Load configuration from file."""
    config_path = _get_config_path()
    config = DEFAULT_CONFIG.copy()
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                
            # Update default config with loaded values
            _deep_update(config, loaded_config)
            logger.info(f"{SYNC_STATUS['SUCCESS']} Loaded configuration from {config_path}")
        else:
            logger.warning(f"{SYNC_STATUS['UNCHANGED']} Configuration file not found at {config_path}, using defaults")
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Save default config
            with open(config_path, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
            
            logger.info(f"{SYNC_STATUS['SUCCESS']} Created default configuration at {config_path}")
    except Exception as e:
        logger.error(f"{SYNC_STATUS['FAILED']} Failed to load configuration: {e}")
        
    return config

def _deep_update(target, source):
    """Deep update target dict with source without overwriting entire nested dicts."""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_update(target[key], value)
        else:
            target[key] = value

def _save_config(config):
    """Save configuration to file."""
    config_path = _get_config_path()
    
    try:
        # Create backup of existing config
        if os.path.exists(config_path):
            backup_path = f"{config_path}.bak"
            shutil.copy2(config_path, backup_path)
            
        # Save new config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        logger.info(f"{SYNC_STATUS['SUCCESS']} Saved configuration to {config_path}")
        return True
    except Exception as e:
        logger.error(f"{SYNC_STATUS['FAILED']} Failed to save configuration: {e}")
        return False

def _validate_config(config):
    """Validate configuration and fix any issues."""
    issues = []
    
    # Check required sections
    for section in ['alert_levels', 'components', 'thresholds']:
        if section not in config:
            config[section] = DEFAULT_CONFIG[section]
            issues.append(f"Missing section '{section}', using defaults")
    
    # Check alert history size
    if 'alert_history_size' not in config or not isinstance(config['alert_history_size'], int):
        config['alert_history_size'] = DEFAULT_CONFIG['alert_history_size']
        issues.append("Invalid alert_history_size, using default")
    
    # Check thresholds
    for component in ['memory', 'cpu', 'disk']:
        if component not in config['thresholds']:
            config['thresholds'][component] = DEFAULT_CONFIG['thresholds'][component]
            issues.append(f"Missing thresholds for {component}, using defaults")
        else:
            for level in ['warning', 'critical']:
                if level not in config['thresholds'][component]:
                    config['thresholds'][component][level] = DEFAULT_CONFIG['thresholds'][component][level]
                    issues.append(f"Missing {level} threshold for {component}, using default")
    
    # Log validation results
    if issues:
        logger.warning(f"{SYNC_STATUS['PARTIAL']} Configuration validation issues: {', '.join(issues)}")
    else:
        logger.info(f"{SYNC_STATUS['SUCCESS']} Configuration validation passed")
    
    return config, issues

def sync(force=False):
    """Synchronize Sentinel configuration.
    
    Args:
        force (bool): Force synchronization regardless of interval.
        
    Returns:
        dict: Synchronization status report.
    """
    global _config, _last_sync, _sync_count
    
    # Check if sync is needed
    current_time = time.time()
    sync_interval = _config.get('sync_interval', DEFAULT_CONFIG['sync_interval']) if _config else DEFAULT_CONFIG['sync_interval']
    
    if not force and _last_sync > 0 and (current_time - _last_sync < sync_interval):
        return {
            'status': SYNC_STATUS['UNCHANGED'],
            'message': f"Sync not needed, last sync was {int(current_time - _last_sync)} seconds ago",
            'timestamp': datetime.now().isoformat(),
            'last_sync': datetime.fromtimestamp(_last_sync).isoformat() if _last_sync else None,
        }
    
    # Load configuration
    try:
        # Remember essential data
        alert_history = None
        if hasattr(__import__('sentinel', fromlist=['_alert_history']), '_alert_history'):
            alert_history = __import__('sentinel', fromlist=['_alert_history'])._alert_history
        
        # Load and validate configuration
        new_config = _load_config()
        validated_config, issues = _validate_config(new_config)
        
        # Update module configuration
        _config = validated_config
        _last_sync = current_time
        _sync_count += 1
        
        # Update sentinel module configuration
        sentinel = __import__('sentinel', fromlist=['_alert_history', '_max_history'])
        if hasattr(sentinel, '_max_history'):
            sentinel._max_history = _config.get('alert_history_size', DEFAULT_CONFIG['alert_history_size'])
        
        # Restore essential data
        if alert_history and hasattr(sentinel, '_alert_history'):
            sentinel._alert_history = alert_history
        
        # Update logging level if needed
        log_level = _config.get('log_level', DEFAULT_CONFIG['log_level'])
        logger.setLevel(getattr(logging, log_level))
        
        # Save validated configuration if there were issues
        if issues:
            _save_config(_config)
        
        # Build status report
        status = SYNC_STATUS['PARTIAL'] if issues else SYNC_STATUS['SUCCESS']
        message = f"Configuration synchronized with {len(issues)} issues" if issues else "Configuration synchronized successfully"
        
        sync_report = {
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'config_path': _get_config_path(),
            'issues': issues,
            'sync_count': _sync_count,
        }
        
        logger.info(f"{status} {message}")
        return sync_report
        
    except Exception as e:
        logger.error(f"{SYNC_STATUS['FAILED']} Sync failed: {e}")
        return {
            'status': SYNC_STATUS['FAILED'],
            'message': f"Sync failed: {str(e)}",
            'timestamp': datetime.now().isoformat(),
            'last_sync': datetime.fromtimestamp(_last_sync).isoformat() if _last_sync else None,
        }

def get_config():
    """Get current configuration.
    
    Returns:
        dict: Current configuration.
    """
    global _config
    
    if not _config:
        _config = _load_config()
        _config, _ = _validate_config(_config)
    
    return _config

def reset():
    """Reset configuration to defaults.
    
    Returns:
        dict: Reset status report.
    """
    global _config, _last_sync
    
    try:
        # Load default configuration
        _config = DEFAULT_CONFIG.copy()
        
        # Save to file
        success = _save_config(_config)
        
        # Update last sync time
        _last_sync = time.time()
        
        if success:
            return {
                'status': SYNC_STATUS['SUCCESS'],
                'message': "Configuration reset to defaults",
                'timestamp': datetime.now().isoformat(),
            }
        else:
            return {
                'status': SYNC_STATUS['PARTIAL'],
                'message': "Configuration reset in memory but failed to save to file",
                'timestamp': datetime.now().isoformat(),
            }
    except Exception as e:
        logger.error(f"{SYNC_STATUS['FAILED']} Reset failed: {e}")
        return {
            'status': SYNC_STATUS['FAILED'],
            'message': f"Reset failed: {str(e)}",
            'timestamp': datetime.now().isoformat(),
        }

# Initialize configuration on module load
_config = _load_config()
_config, _ = _validate_config(_config)
