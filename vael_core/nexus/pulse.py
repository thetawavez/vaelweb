"""
NEXUS Pulse Module - Anomaly Detection System

This module provides anomaly detection capabilities for the NEXUS entity.
It scans socket payloads, logs, traffic patterns, and behavior profiles
to identify potential security threats and system anomalies.

Token-efficient implementation with symbolic compression.
"""

import os
import time
import json
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from collections import deque

# Import symbols from parent module
from vael_core.nexus import SYMBOLS, THREAT_LEVELS

# Configure logging
logger = logging.getLogger("vael.nexus.pulse")

class Pulse:
    """NEXUS Pulse anomaly detection system"""
    
    def __init__(self):
        """Initialize the Pulse system"""
        self.last_pulse_time = 0
        self.baseline = {}
        self.anomalies = deque(maxlen=10)  # Last 10 anomalies for token efficiency
        self.scan_count = 0
        self.signature_cache = {}
        self._load_baseline()
    
    def _load_baseline(self):
        """Load baseline behavior profiles"""
        baseline_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data',
            'nexus_baseline.json'
        )
        
        # Use default baseline if file doesn't exist
        if not os.path.exists(baseline_path):
            self.baseline = {
                "cpu_usage": {"mean": 30.0, "std": 15.0},
                "memory_usage": {"mean": 40.0, "std": 20.0},
                "request_rate": {"mean": 5.0, "std": 3.0},
                "error_rate": {"mean": 0.5, "std": 0.5},
                "session_duration": {"mean": 300.0, "std": 150.0}
            }
            return
        
        try:
            with open(baseline_path, 'r') as f:
                self.baseline = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load baseline: {str(e)}")
            # Use default baseline on error
            self.baseline = {
                "cpu_usage": {"mean": 30.0, "std": 15.0},
                "memory_usage": {"mean": 40.0, "std": 20.0},
                "request_rate": {"mean": 5.0, "std": 3.0},
                "error_rate": {"mean": 0.5, "std": 0.5},
                "session_duration": {"mean": 300.0, "std": 150.0}
            }
    
    def check(self, context: Dict = None, high_alert: bool = False) -> Dict:
        """Perform a pulse check for anomalies
        
        Args:
            context: Current system context (optional)
            high_alert: Whether system is in high alert mode
            
        Returns:
            Pulse check results with anomaly assessment
        """
        current_time = time.time()
        min_interval = 0.2 if high_alert else 1.0
        
        # Rate limiting
        if current_time - self.last_pulse_time < min_interval:
            return {
                "status": "RATE_LIMITED",
                "symbol": SYMBOLS["BLOCK"],
                "message": "Pulse check rate limited"
            }
        
        self.last_pulse_time = current_time
        self.scan_count += 1
        
        # Gather system metrics if context not provided
        metrics = context or self._gather_metrics()
        
        # Scan for anomalies
        anomalies = self._detect_anomalies(metrics)
        
        # Determine overall threat level
        threat_level = self._calculate_threat_level(anomalies)
        
        # Prepare result with symbolic compression
        result = {
            "timestamp": current_time,
            "scan_id": f"PULSE-{self.scan_count}",
            "threat_level": threat_level,
            "threat_name": THREAT_LEVELS[threat_level],
            "anomalies": anomalies,
            "symbol": self._get_threat_symbol(threat_level),
            "symbolic": f"{self._get_threat_symbol(threat_level)} NEXUS/PULSE/{current_time:.0f}"
        }
        
        # Store anomalies if any found
        if anomalies and threat_level > 0:
            self.anomalies.append({
                "timestamp": current_time,
                "threat_level": threat_level,
                "anomalies": anomalies
            })
        
        return result
    
    def _gather_metrics(self) -> Dict:
        """Gather current system metrics
        
        Returns:
            Dictionary of system metrics
        """
        # In a real implementation, this would gather actual system metrics
        # For now, return simulated metrics
        import random
        
        # Simulate normal metrics with occasional anomalies
        anomaly_chance = 0.05  # 5% chance of anomaly
        
        metrics = {
            "cpu_usage": random.normalvariate(
                self.baseline["cpu_usage"]["mean"],
                self.baseline["cpu_usage"]["std"]
            ),
            "memory_usage": random.normalvariate(
                self.baseline["memory_usage"]["mean"],
                self.baseline["memory_usage"]["std"]
            ),
            "request_rate": random.normalvariate(
                self.baseline["request_rate"]["mean"],
                self.baseline["request_rate"]["std"]
            ),
            "error_rate": random.normalvariate(
                self.baseline["error_rate"]["mean"],
                self.baseline["error_rate"]["std"]
            ),
            "session_duration": random.normalvariate(
                self.baseline["session_duration"]["mean"],
                self.baseline["session_duration"]["std"]
            ),
            "socket_payloads": self._check_socket_payloads(),
            "log_entries": self._check_log_entries(),
            "network_traffic": self._check_network_traffic()
        }
        
        # Introduce anomaly if random chance hits
        if random.random() < anomaly_chance:
            # Pick a random metric to make anomalous
            metric = random.choice(list(self.baseline.keys()))
            # Make it significantly deviate from baseline
            metrics[metric] = self.baseline[metric]["mean"] + (
                self.baseline[metric]["std"] * random.choice([-3, 3])
            )
        
        return metrics
    
    def _check_socket_payloads(self) -> Dict:
        """Check socket payloads for anomalies
        
        Returns:
            Socket payload check results
        """
        # Placeholder for actual socket payload checking
        return {
            "total": 10,
            "anomalous": 0,
            "patterns": ["normal", "normal", "normal"]
        }
    
    def _check_log_entries(self) -> Dict:
        """Check log entries for anomalies
        
        Returns:
            Log entry check results
        """
        # Placeholder for actual log checking
        return {
            "total": 50,
            "error_count": 1,
            "warning_count": 3,
            "patterns": ["normal", "normal", "normal"]
        }
    
    def _check_network_traffic(self) -> Dict:
        """Check network traffic for anomalies
        
        Returns:
            Network traffic check results
        """
        # Placeholder for actual network traffic checking
        return {
            "bytes_in": 1024,
            "bytes_out": 2048,
            "connections": 5,
            "patterns": ["normal", "normal", "normal"]
        }
    
    def _detect_anomalies(self, metrics: Dict) -> List[Dict]:
        """Detect anomalies in system metrics
        
        Args:
            metrics: Current system metrics
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Check each baseline metric
        for metric, baseline in self.baseline.items():
            if metric in metrics:
                # Calculate z-score (how many standard deviations from mean)
                if baseline["std"] > 0:  # Avoid division by zero
                    z_score = abs(metrics[metric] - baseline["mean"]) / baseline["std"]
                    
                    # Z-score > 2 is potentially anomalous (95% confidence)
                    if z_score > 2:
                        severity = "LOW"
                        if z_score > 3:  # 99.7% confidence
                            severity = "MEDIUM"
                        if z_score > 4:  # 99.99% confidence
                            severity = "HIGH"
                        
                        anomalies.append({
                            "metric": metric,
                            "value": metrics[metric],
                            "baseline": baseline["mean"],
                            "z_score": z_score,
                            "severity": severity
                        })
        
        # Check socket payloads
        if metrics.get("socket_payloads", {}).get("anomalous", 0) > 0:
            anomalies.append({
                "metric": "socket_payloads",
                "anomalous": metrics["socket_payloads"]["anomalous"],
                "total": metrics["socket_payloads"]["total"],
                "patterns": metrics["socket_payloads"]["patterns"],
                "severity": "MEDIUM"
            })
        
        # Check log entries
        log_entries = metrics.get("log_entries", {})
        error_ratio = log_entries.get("error_count", 0) / max(log_entries.get("total", 1), 1)
        if error_ratio > 0.05:  # More than 5% errors
            anomalies.append({
                "metric": "log_errors",
                "error_count": log_entries.get("error_count", 0),
                "total": log_entries.get("total", 0),
                "ratio": error_ratio,
                "severity": "MEDIUM" if error_ratio < 0.1 else "HIGH"
            })
        
        return anomalies
    
    def _calculate_threat_level(self, anomalies: List[Dict]) -> int:
        """Calculate overall threat level from anomalies
        
        Args:
            anomalies: List of detected anomalies
            
        Returns:
            Threat level (0-5)
        """
        if not anomalies:
            return 0  # No threat
        
        # Count anomalies by severity
        severity_counts = {
            "LOW": 0,
            "MEDIUM": 0,
            "HIGH": 0,
            "CRITICAL": 0
        }
        
        for anomaly in anomalies:
            severity = anomaly.get("severity", "LOW")
            severity_counts[severity] += 1
        
        # Determine threat level
        if severity_counts["CRITICAL"] > 0:
            return 5  # Critical threat
        if severity_counts["HIGH"] > 2:
            return 4  # High threat
        if severity_counts["HIGH"] > 0 or severity_counts["MEDIUM"] > 2:
            return 3  # Medium threat
        if severity_counts["MEDIUM"] > 0 or severity_counts["LOW"] > 3:
            return 2  # Low threat
        if severity_counts["LOW"] > 0:
            return 1  # Info level threat
        
        return 0  # No threat
    
    def _get_threat_symbol(self, threat_level: int) -> str:
        """Get symbolic representation for threat level
        
        Args:
            threat_level: Numeric threat level (0-5)
            
        Returns:
            Symbol representing threat level
        """
        if threat_level >= 4:  # High or Critical
            return SYMBOLS["BREACH"]
        if threat_level >= 2:  # Medium or Low
            return SYMBOLS["SUSPICIOUS"]
        return SYMBOLS["CLEAR"]
    
    def get_anomaly_history(self) -> List[Dict]:
        """Get history of detected anomalies
        
        Returns:
            List of historical anomalies
        """
        return list(self.anomalies)

# Create singleton instance
pulse_system = Pulse()

# Public interface
def check(context: Dict = None, high_alert: bool = False) -> Dict:
    """Perform a pulse check for anomalies
    
    Args:
        context: Current system context (optional)
        high_alert: Whether system is in high alert mode
        
    Returns:
        Pulse check results with anomaly assessment
    """
    return pulse_system.check(context, high_alert)

def get_anomaly_history() -> List[Dict]:
    """Get history of detected anomalies
    
    Returns:
        List of historical anomalies
    """
    return pulse_system.get_anomaly_history()
