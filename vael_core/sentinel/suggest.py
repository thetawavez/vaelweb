"""
VAEL Core - Sentinel Suggest Module
Version: 0.1.0 (2025-05-30)

This module implements the recommendation engine for the Sentinel entity.
It analyzes context information to provide security and health recommendations,
using token-efficient symbolic indicators and patterns.

The suggest module serves as the Sentinel's advisory capability, offering
proactive guidance based on system state and detected anomalies.
"""

import os
import time
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging with minimal footprint
logger = logging.getLogger('vael.sentinel.suggest')

# Import shared symbolic indicators if available
try:
    from . import ALERT_LEVELS
except ImportError:
    # Fallback if not available
    ALERT_LEVELS = {
        'INFO': '🔵',
        'WARNING': '🟡',
        'ERROR': '🔴',
        'CRITICAL': '⛔',
        'SECURE': '🟢',
    }

# Recommendation types with symbolic indicators
RECOMMENDATION_TYPES = {
    'SECURITY': '🛡️',
    'HEALTH': '💓',
    'PERFORMANCE': '⚡',
    'CONFIGURATION': '⚙️',
    'GENERAL': 'ℹ️',
}

# Priority levels with symbolic indicators
PRIORITY_LEVELS = {
    'LOW': '⬇️',
    'MEDIUM': '➡️',
    'HIGH': '⬆️',
    'CRITICAL': '‼️',
}

# Module state
_recommendation_history = []
_max_history = 50
_suggestion_count = 0
_last_suggestion_time = 0

def _get_recommendation_store():
    """Get path to recommendation store file."""
    store_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(store_dir, exist_ok=True)
    return os.path.join(store_dir, 'recommendations.json')

def _load_recommendation_history():
    """Load recommendation history from disk."""
    global _recommendation_history
    
    store_path = _get_recommendation_store()
    if os.path.exists(store_path):
        try:
            with open(store_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    _recommendation_history = data[-_max_history:]
        except Exception as e:
            logger.error(f"Failed to load recommendation history: {e}")

def _save_recommendation_history():
    """Save recommendation history to disk."""
    store_path = _get_recommendation_store()
    try:
        with open(store_path, 'w') as f:
            json.dump(_recommendation_history[-_max_history:], f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save recommendation history: {e}")

def _analyze_security_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze context for security concerns."""
    security_score = 0
    findings = []
    
    # Check for explicit security indicators
    if 'security' in context:
        security_data = context['security']
        
        # Check for failed login attempts
        if 'failed_logins' in security_data:
            failed_count = security_data['failed_logins']
            if failed_count > 10:
                security_score += 8
                findings.append(f"High number of failed logins: {failed_count}")
            elif failed_count > 5:
                security_score += 4
                findings.append(f"Elevated failed login attempts: {failed_count}")
        
        # Check for unauthorized access attempts
        if 'unauthorized_access' in security_data:
            security_score += 9
            findings.append("Unauthorized access attempts detected")
        
        # Check for suspicious activity
        if 'suspicious_activity' in security_data:
            security_score += 6
            findings.append(f"Suspicious activity: {security_data['suspicious_activity']}")
    
    # Check for network anomalies
    if 'network' in context:
        network_data = context['network']
        
        # Check for unusual connections
        if 'unusual_connections' in network_data:
            security_score += 7
            findings.append("Unusual network connections detected")
        
        # Check for port scans
        if 'port_scans' in network_data:
            security_score += 8
            findings.append("Port scanning activity detected")
    
    # Check for file system changes
    if 'file_system' in context:
        fs_data = context['file_system']
        
        # Check for unexpected changes to system files
        if 'unexpected_changes' in fs_data:
            security_score += 9
            findings.append("Unexpected changes to system files")
        
        # Check for permission changes
        if 'permission_changes' in fs_data:
            security_score += 7
            findings.append("File permission changes detected")
    
    # Determine priority based on security score
    if security_score >= 15:
        priority = 'CRITICAL'
    elif security_score >= 10:
        priority = 'HIGH'
    elif security_score >= 5:
        priority = 'MEDIUM'
    else:
        priority = 'LOW'
    
    return {
        'type': 'SECURITY',
        'score': security_score,
        'priority': priority,
        'findings': findings
    }

def _analyze_health_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze context for system health concerns."""
    health_score = 0
    findings = []
    
    # Check for explicit health indicators
    if 'health' in context:
        health_data = context['health']
        
        # Check for high CPU usage
        if 'cpu_usage' in health_data:
            cpu_usage = health_data['cpu_usage']
            if cpu_usage > 90:
                health_score += 8
                findings.append(f"Critical CPU usage: {cpu_usage}%")
            elif cpu_usage > 75:
                health_score += 5
                findings.append(f"High CPU usage: {cpu_usage}%")
            elif cpu_usage > 50:
                health_score += 2
                findings.append(f"Elevated CPU usage: {cpu_usage}%")
        
        # Check for high memory usage
        if 'memory_usage' in health_data:
            memory_usage = health_data['memory_usage']
            if memory_usage > 90:
                health_score += 8
                findings.append(f"Critical memory usage: {memory_usage}%")
            elif memory_usage > 80:
                health_score += 5
                findings.append(f"High memory usage: {memory_usage}%")
            elif memory_usage > 70:
                health_score += 2
                findings.append(f"Elevated memory usage: {memory_usage}%")
        
        # Check for disk space
        if 'disk_usage' in health_data:
            disk_usage = health_data['disk_usage']
            if disk_usage > 95:
                health_score += 9
                findings.append(f"Critical disk usage: {disk_usage}%")
            elif disk_usage > 85:
                health_score += 6
                findings.append(f"High disk usage: {disk_usage}%")
            elif disk_usage > 75:
                health_score += 3
                findings.append(f"Elevated disk usage: {disk_usage}%")
    
    # Check for process crashes
    if 'processes' in context:
        process_data = context['processes']
        
        # Check for crashed processes
        if 'crashed' in process_data:
            crashed_count = len(process_data['crashed'])
            if crashed_count > 0:
                health_score += min(crashed_count * 3, 10)
                findings.append(f"{crashed_count} crashed processes detected")
        
        # Check for high-CPU processes
        if 'high_cpu' in process_data:
            high_cpu_count = len(process_data['high_cpu'])
            if high_cpu_count > 0:
                health_score += min(high_cpu_count * 2, 8)
                findings.append(f"{high_cpu_count} processes with high CPU usage")
    
    # Check for log errors
    if 'logs' in context:
        log_data = context['logs']
        
        # Check for error counts
        if 'error_count' in log_data:
            error_count = log_data['error_count']
            if error_count > 100:
                health_score += 7
                findings.append(f"High number of log errors: {error_count}")
            elif error_count > 50:
                health_score += 4
                findings.append(f"Elevated log errors: {error_count}")
            elif error_count > 20:
                health_score += 2
                findings.append(f"Increased log errors: {error_count}")
    
    # Determine priority based on health score
    if health_score >= 15:
        priority = 'CRITICAL'
    elif health_score >= 10:
        priority = 'HIGH'
    elif health_score >= 5:
        priority = 'MEDIUM'
    else:
        priority = 'LOW'
    
    return {
        'type': 'HEALTH',
        'score': health_score,
        'priority': priority,
        'findings': findings
    }

def _analyze_performance_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze context for performance concerns."""
    performance_score = 0
    findings = []
    
    # Check for explicit performance indicators
    if 'performance' in context:
        perf_data = context['performance']
        
        # Check for response time
        if 'response_time' in perf_data:
            response_time = perf_data['response_time']
            if response_time > 5000:  # milliseconds
                performance_score += 8
                findings.append(f"Critical response time: {response_time}ms")
            elif response_time > 2000:
                performance_score += 5
                findings.append(f"Slow response time: {response_time}ms")
            elif response_time > 1000:
                performance_score += 2
                findings.append(f"Elevated response time: {response_time}ms")
        
        # Check for throughput
        if 'throughput' in perf_data:
            throughput = perf_data['throughput']
            expected = perf_data.get('expected_throughput', throughput * 2)
            if throughput < expected * 0.5:
                performance_score += 7
                findings.append(f"Severely degraded throughput: {throughput}")
            elif throughput < expected * 0.7:
                performance_score += 4
                findings.append(f"Degraded throughput: {throughput}")
        
        # Check for latency
        if 'latency' in perf_data:
            latency = perf_data['latency']
            if latency > 1000:  # milliseconds
                performance_score += 8
                findings.append(f"High latency: {latency}ms")
            elif latency > 500:
                performance_score += 4
                findings.append(f"Elevated latency: {latency}ms")
    
    # Check for database performance
    if 'database' in context:
        db_data = context['database']
        
        # Check for slow queries
        if 'slow_queries' in db_data:
            slow_count = len(db_data['slow_queries'])
            if slow_count > 10:
                performance_score += 7
                findings.append(f"High number of slow queries: {slow_count}")
            elif slow_count > 5:
                performance_score += 4
                findings.append(f"Several slow queries detected: {slow_count}")
            elif slow_count > 0:
                performance_score += 2
                findings.append(f"Slow queries detected: {slow_count}")
        
        # Check for connection pool
        if 'connection_usage' in db_data:
            conn_usage = db_data['connection_usage']
            if conn_usage > 90:
                performance_score += 6
                findings.append(f"Database connection pool near capacity: {conn_usage}%")
            elif conn_usage > 75:
                performance_score += 3
                findings.append(f"Elevated database connection usage: {conn_usage}%")
    
    # Determine priority based on performance score
    if performance_score >= 15:
        priority = 'CRITICAL'
    elif performance_score >= 10:
        priority = 'HIGH'
    elif performance_score >= 5:
        priority = 'MEDIUM'
    else:
        priority = 'LOW'
    
    return {
        'type': 'PERFORMANCE',
        'score': performance_score,
        'priority': priority,
        'findings': findings
    }

def _generate_recommendations(analysis_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate recommendations based on analysis results."""
    recommendations = []
    
    for result in analysis_results:
        rec_type = result['type']
        priority = result['priority']
        findings = result['findings']
        
        if not findings:
            continue
        
        # Generate type-specific recommendations
        if rec_type == 'SECURITY':
            for finding in findings:
                if 'failed login' in finding.lower():
                    recommendations.append({
                        'type': rec_type,
                        'priority': priority,
                        'finding': finding,
                        'action': "Implement account lockout policy and review authentication logs",
                        'symbol': f"{RECOMMENDATION_TYPES[rec_type]} {PRIORITY_LEVELS[priority]}"
                    })
                elif 'unauthorized access' in finding.lower():
                    recommendations.append({
                        'type': rec_type,
                        'priority': priority,
                        'finding': finding,
                        'action': "Isolate affected systems and initiate security incident response",
                        'symbol': f"{RECOMMENDATION_TYPES[rec_type]} {PRIORITY_LEVELS[priority]}"
                    })
                elif 'suspicious activity' in finding.lower():
                    recommendations.append({
                        'type': rec_type,
                        'priority': priority,
                        'finding': finding,
                        'action': "Increase monitoring and review recent system changes",
                        'symbol': f"{RECOMMENDATION_TYPES[rec_type]} {PRIORITY_LEVELS[priority]}"
                    })
                elif 'network' in finding.lower() or 'port scan' in finding.lower():
                    recommendations.append({
                        'type': rec_type,
                        'priority': priority,
                        'finding': finding,
                        'action': "Review firewall rules and network traffic patterns",
                        'symbol': f"{RECOMMENDATION_TYPES[rec_type]} {PRIORITY_LEVELS[priority]}"
                    })
                elif 'file' in finding.lower() or 'permission' in finding.lower():
                    recommendations.append({
                        'type': rec_type,
                        'priority': priority,
                        'finding': finding,
                        'action': "Verify file integrity and review recent changes",
                        'symbol': f"{RECOMMENDATION_TYPES[rec_type]} {PRIORITY_LEVELS[priority]}"
                    })
                else:
                    recommendations.append({
                        'type': rec_type,
                        'priority': priority,
                        'finding': finding,
                        'action': "Investigate security concern and review logs",
                        'symbol': f"{RECOMMENDATION_TYPES[rec_type]} {PRIORITY_LEVELS[priority]}"
                    })
        
        elif rec_type == 'HEALTH':
            for finding in findings:
                if 'cpu usage' in finding.lower():
                    recommendations.append({
                        'type': rec_type,
                        'priority': priority,
                        'finding': finding,
                        'action': "Identify CPU-intensive processes and optimize or restart if necessary",
                        'symbol': f"{RECOMMENDATION_TYPES[rec_type]} {PRIORITY_LEVELS[priority]}"
                    })
                elif 'memory usage' in finding.lower():
                    recommendations.append({
                        'type': rec_type,
                        'priority': priority,
                        'finding': finding,
                        'action': "Check for memory leaks and consider increasing available memory",
                        'symbol': f"{RECOMMENDATION_TYPES[rec_type]} {PRIORITY_LEVELS[priority]}"
                    })
                elif 'disk usage' in finding.lower():
                    recommendations.append({
                        'type': rec_type,
                        'priority': priority,
                        'finding': finding,
                        'action': "Clean up temporary files and logs, consider adding storage",
                        'symbol': f"{RECOMMENDATION_TYPES[rec_type]} {PRIORITY_LEVELS[priority]}"
                    })
                elif 'crashed' in finding.lower():
                    recommendations.append({
                        'type': rec_type,
                        'priority': priority,
                        'finding': finding,
                        'action': "Restart crashed processes and investigate root cause",
                        'symbol': f"{RECOMMENDATION_TYPES[rec_type]} {PRIORITY_LEVELS[priority]}"
                    })
                elif 'log error' in finding.lower():
                    recommendations.append({
                        'type': rec_type,
                        'priority': priority,
                        'finding': finding,
                        'action': "Review error logs and address recurring issues",
                        'symbol': f"{RECOMMENDATION_TYPES[rec_type]} {PRIORITY_LEVELS[priority]}"
                    })
                else:
                    recommendations.append({
                        'type': rec_type,
                        'priority': priority,
                        'finding': finding,
                        'action': "Monitor system health and investigate anomalies",
                        'symbol': f"{RECOMMENDATION_TYPES[rec_type]} {PRIORITY_LEVELS[priority]}"
                    })
        
        elif rec_type == 'PERFORMANCE':
            for finding in findings:
                if 'response time' in finding.lower() or 'latency' in finding.lower():
                    recommendations.append({
                        'type': rec_type,
                        'priority': priority,
                        'finding': finding,
                        'action': "Optimize request handling and consider scaling resources",
                        'symbol': f"{RECOMMENDATION_TYPES[rec_type]} {PRIORITY_LEVELS[priority]}"
                    })
                elif 'throughput' in finding.lower():
                    recommendations.append({
                        'type': rec_type,
                        'priority': priority,
                        'finding': finding,
                        'action': "Investigate bottlenecks and optimize data processing",
                        'symbol': f"{RECOMMENDATION_TYPES[rec_type]} {PRIORITY_LEVELS[priority]}"
                    })
                elif 'query' in finding.lower() or 'database' in finding.lower():
                    recommendations.append({
                        'type': rec_type,
                        'priority': priority,
                        'finding': finding,
                        'action': "Optimize database queries and review indexing strategy",
                        'symbol': f"{RECOMMENDATION_TYPES[rec_type]} {PRIORITY_LEVELS[priority]}"
                    })
                else:
                    recommendations.append({
                        'type': rec_type,
                        'priority': priority,
                        'finding': finding,
                        'action': "Review performance metrics and optimize resource usage",
                        'symbol': f"{RECOMMENDATION_TYPES[rec_type]} {PRIORITY_LEVELS[priority]}"
                    })
    
    return recommendations

def _log_recommendation(recommendation: Dict[str, Any]):
    """Log a recommendation for auditing."""
    global _recommendation_history, _suggestion_count
    
    # Add timestamp and ID
    timestamp = datetime.now().isoformat()
    rec_id = f"REC-{int(time.time())}-{_suggestion_count}"
    _suggestion_count += 1
    
    # Create recommendation record
    record = {
        'id': rec_id,
        'timestamp': timestamp,
        'type': recommendation['type'],
        'priority': recommendation['priority'],
        'finding': recommendation['finding'],
        'action': recommendation['action'],
        'symbol': recommendation['symbol']
    }
    
    # Add to history
    _recommendation_history.append(record)
    if len(_recommendation_history) > _max_history:
        _recommendation_history.pop(0)
    
    # Log to file
    logger.info(f"{record['symbol']} [{rec_id}] {record['finding']} - {record['action']}")
    
    # Periodically save history
    if len(_recommendation_history) % 5 == 0:
        _save_recommendation_history()
    
    return record

def suggest(context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate recommendations based on context.
    
    Args:
        context (dict): Context information including system state and potential issues.
        
    Returns:
        dict: Recommendations and suggestions.
    """
    global _last_suggestion_time
    
    # Initialize if needed
    if not _recommendation_history:
        _load_recommendation_history()
    
    # Update last suggestion time
    _last_suggestion_time = time.time()
    
    # Analyze context
    analysis_results = []
    
    # Check for security concerns
    security_analysis = _analyze_security_context(context)
    if security_analysis['findings']:
        analysis_results.append(security_analysis)
    
    # Check for health concerns
    health_analysis = _analyze_health_context(context)
    if health_analysis['findings']:
        analysis_results.append(health_analysis)
    
    # Check for performance concerns
    performance_analysis = _analyze_performance_context(context)
    if performance_analysis['findings']:
        analysis_results.append(performance_analysis)
    
    # Generate recommendations
    recommendations = _generate_recommendations(analysis_results)
    
    # Log recommendations for auditing
    logged_recommendations = []
    for rec in recommendations:
        logged_rec = _log_recommendation(rec)
        logged_recommendations.append(logged_rec)
    
    # Create response
    response = {
        'timestamp': datetime.now().isoformat(),
        'recommendation_count': len(logged_recommendations),
        'recommendations': logged_recommendations,
        'analysis': {
            'security': security_analysis['score'] if 'score' in security_analysis else 0,
            'health': health_analysis['score'] if 'score' in health_analysis else 0,
            'performance': performance_analysis['score'] if 'score' in performance_analysis else 0,
        }
    }
    
    # Add highest priority
    if logged_recommendations:
        priorities = [rec['priority'] for rec in logged_recommendations]
        highest_priority = max(priorities, key=lambda p: list(PRIORITY_LEVELS.keys()).index(p))
        response['highest_priority'] = highest_priority
    else:
        response['highest_priority'] = 'LOW'
    
    return response

def get_recent_recommendations(count: int = 10) -> List[Dict[str, Any]]:
    """Get recent recommendations.
    
    Args:
        count (int): Number of recent recommendations to retrieve.
        
    Returns:
        list: Recent recommendations.
    """
    # Initialize if needed
    if not _recommendation_history:
        _load_recommendation_history()
    
    return _recommendation_history[-count:] if _recommendation_history else []

def clear_recommendations() -> Dict[str, Any]:
    """Clear recommendation history.
    
    Returns:
        dict: Status message.
    """
    global _recommendation_history
    
    # Clear history
    _recommendation_history = []
    
    # Save empty history
    _save_recommendation_history()
    
    return {
        'status': ALERT_LEVELS['INFO'],
        'message': "Recommendation history cleared",
        'timestamp': datetime.now().isoformat()
    }

# Initialize on module load
_load_recommendation_history()
