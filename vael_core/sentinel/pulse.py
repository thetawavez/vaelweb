"""
VAEL Core - Sentinel Pulse Module
Version: 0.1.0 (2025-05-30)

This module implements the health monitoring functionality for the Sentinel entity.
It provides a lightweight, token-efficient mechanism for checking system health
and reporting status using symbolic indicators.
"""

import os
import time
import psutil
import logging
from datetime import datetime, timedelta

# Configure logging with minimal footprint
logger = logging.getLogger('vael.sentinel.pulse')

# Symbolic status indicators for token efficiency
STATUS = {
    'OPTIMAL': '🟢',
    'DEGRADED': '🟡',
    'CRITICAL': '🔴',
    'UNKNOWN': '⚪',
    'INACTIVE': '⚫',
}

# Component check history with circular buffer
_component_status = {}
_last_full_check = 0
_check_interval = 60  # seconds

def _check_memory():
    """Check memory usage and status."""
    try:
        memory = psutil.virtual_memory()
        usage_percent = memory.percent
        
        if usage_percent > 90:
            status = STATUS['CRITICAL']
            message = f"Memory usage critical: {usage_percent}%"
        elif usage_percent > 75:
            status = STATUS['DEGRADED']
            message = f"Memory usage elevated: {usage_percent}%"
        else:
            status = STATUS['OPTIMAL']
            message = f"Memory usage normal: {usage_percent}%"
            
        return {
            'status': status,
            'message': message,
            'usage': usage_percent,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Memory check failed: {e}")
        return {
            'status': STATUS['UNKNOWN'],
            'message': f"Memory check error: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }

def _check_cpu():
    """Check CPU usage and status."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        
        if cpu_percent > 90:
            status = STATUS['CRITICAL']
            message = f"CPU usage critical: {cpu_percent}%"
        elif cpu_percent > 70:
            status = STATUS['DEGRADED']
            message = f"CPU usage elevated: {cpu_percent}%"
        else:
            status = STATUS['OPTIMAL']
            message = f"CPU usage normal: {cpu_percent}%"
            
        return {
            'status': status,
            'message': message,
            'usage': cpu_percent,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"CPU check failed: {e}")
        return {
            'status': STATUS['UNKNOWN'],
            'message': f"CPU check error: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }

def _check_disk():
    """Check disk usage and status."""
    try:
        disk = psutil.disk_usage('/')
        usage_percent = disk.percent
        
        if usage_percent > 95:
            status = STATUS['CRITICAL']
            message = f"Disk usage critical: {usage_percent}%"
        elif usage_percent > 85:
            status = STATUS['DEGRADED']
            message = f"Disk usage elevated: {usage_percent}%"
        else:
            status = STATUS['OPTIMAL']
            message = f"Disk usage normal: {usage_percent}%"
            
        return {
            'status': status,
            'message': message,
            'usage': usage_percent,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Disk check failed: {e}")
        return {
            'status': STATUS['UNKNOWN'],
            'message': f"Disk check error: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }

def _check_log_health():
    """Check log file health and status."""
    try:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        sentinel_log = os.path.join(log_dir, 'sentinel.log')
        
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        if not os.path.exists(sentinel_log):
            with open(sentinel_log, 'w') as f:
                f.write(f"[{datetime.now().isoformat()}] Sentinel log initialized\n")
            
            status = STATUS['OPTIMAL']
            message = "Log file initialized"
        else:
            # Check if log was modified in last 24 hours
            mod_time = os.path.getmtime(sentinel_log)
            if datetime.fromtimestamp(mod_time) < datetime.now() - timedelta(hours=24):
                status = STATUS['DEGRADED']
                message = "Log file not updated in 24+ hours"
            else:
                status = STATUS['OPTIMAL']
                message = "Log file healthy"
                
        return {
            'status': status,
            'message': message,
            'log_path': sentinel_log,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Log health check failed: {e}")
        return {
            'status': STATUS['UNKNOWN'],
            'message': f"Log check error: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }

def _check_alert_system():
    """Check alert system functionality."""
    try:
        # Check if alert history file exists and is writable
        history_path = os.path.join(os.path.dirname(__file__), 'alert_history.log')
        
        if not os.path.exists(history_path):
            with open(history_path, 'w') as f:
                f.write(f"[{datetime.now().isoformat()}] Alert system initialized\n")
            
            status = STATUS['OPTIMAL']
            message = "Alert system initialized"
        else:
            # Verify we can write to the file
            try:
                with open(history_path, 'a') as f:
                    f.write("")
                status = STATUS['OPTIMAL']
                message = "Alert system operational"
            except Exception as e:
                status = STATUS['CRITICAL']
                message = f"Alert system write error: {str(e)}"
                
        return {
            'status': status,
            'message': message,
            'history_path': history_path,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Alert system check failed: {e}")
        return {
            'status': STATUS['UNKNOWN'],
            'message': f"Alert system check error: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }

def pulse(force_check=False):
    """Check Sentinel health status.
    
    Args:
        force_check (bool): Force a full check regardless of interval.
        
    Returns:
        dict: Health status report with component statuses.
    """
    global _last_full_check, _component_status
    
    current_time = time.time()
    
    # Determine if we need a full check
    need_full_check = force_check or (current_time - _last_full_check > _check_interval)
    
    if need_full_check:
        # Perform full component checks
        _component_status = {
            'memory': _check_memory(),
            'cpu': _check_cpu(),
            'disk': _check_disk(),
            'logs': _check_log_health(),
            'alerts': _check_alert_system()
        }
        _last_full_check = current_time
    
    # Determine overall status
    critical_count = sum(1 for component in _component_status.values() 
                        if component['status'] == STATUS['CRITICAL'])
    degraded_count = sum(1 for component in _component_status.values() 
                        if component['status'] == STATUS['DEGRADED'])
    
    if critical_count > 0:
        overall_status = STATUS['CRITICAL']
        overall_message = f"Critical issues detected in {critical_count} components"
    elif degraded_count > 0:
        overall_status = STATUS['DEGRADED']
        overall_message = f"Performance degraded in {degraded_count} components"
    else:
        overall_status = STATUS['OPTIMAL']
        overall_message = "All systems operational"
    
    # Build the health report
    health_report = {
        'status': overall_status,
        'message': overall_message,
        'timestamp': datetime.now().isoformat(),
        'components': _component_status,
        'last_full_check': datetime.fromtimestamp(_last_full_check).isoformat() if _last_full_check else None
    }
    
    # Log the health status
    logger.info(f"Health check: {overall_status} {overall_message}")
    
    return health_report

if __name__ == "__main__":
    # If run directly, print the health report
    import json
    print(json.dumps(pulse(force_check=True), indent=2))
