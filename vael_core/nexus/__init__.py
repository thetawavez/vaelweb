"""
NEXUS - Intrusion Detection System for VAEL Core

This module provides the core functionality for the NEXUS entity,
responsible for threat detection, anomaly sensing, and security diagnostics.
NEXUS serves as the guardian layer of the VAEL Core system.

Token-efficient implementation with symbolic compression and limited scan cycles.
"""

import time
import os
import json
import logging
from collections import deque
from typing import Dict, List, Tuple, Any, Optional

# Configure logging
logger = logging.getLogger("vael.nexus")

# Symbolic constants for token efficiency
SYMBOLS = {
    "BREACH": "🟥",
    "SUSPICIOUS": "🟨",
    "CLEAR": "🟩",
    "SCAN": "🔍",
    "RULE": "📜",
    "ALERT": "🚨",
    "LEARN": "🧠",
    "HEAL": "🧬",
    "TRACE": "🔄",
    "BLOCK": "🛑"
}

# Threat levels
THREAT_LEVELS = {
    0: "CLEAR",      # No threat detected
    1: "INFO",       # Informational, no action needed
    2: "LOW",        # Low threat, monitor
    3: "MEDIUM",     # Medium threat, investigate
    4: "HIGH",       # High threat, action recommended
    5: "CRITICAL"    # Critical threat, immediate action required
}

class NEXUS:
    """NEXUS Intrusion Detection System for VAEL Core"""
    
    def __init__(self, config_path: str = None):
        """Initialize the NEXUS entity
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.initialized = False
        self.high_alert_mode = False
        self.last_scan_time = 0
        self.scan_interval = 1.0  # Default: 1 scan per second
        self.high_alert_scan_interval = 0.2  # 5 scans per second in high alert mode
        
        # Rolling memory buffer (10 entries for token efficiency)
        self.memory_buffer = deque(maxlen=10)
        
        # Known intrusion signatures (lazy-loaded via sync)
        self.signatures = {}
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Register with other entities
        self._register_with_sentinel()
        self._register_with_antibody()
        
        # Self-validate
        self.initialized = self._self_validate()
        
        # Log initialization
        if self.initialized:
            self._log_event(f"{SYMBOLS['CLEAR']} NEXUS initialized successfully")
        else:
            self._log_event(f"{SYMBOLS['BREACH']} NEXUS initialization failed")
    
    def _load_config(self, config_path: str = None) -> Dict:
        """Load configuration from file or use defaults
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "scan_interval": 1.0,
            "high_alert_scan_interval": 0.2,
            "signature_path": "vael_core/nexus/signatures",
            "log_to_sentinel": True,
            "log_to_manus": True,
            "self_healing": True,
            "learning_mode": False
        }
        
        if not config_path or not os.path.exists(config_path):
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            self._log_event(f"{SYMBOLS['SUSPICIOUS']} Failed to load config: {str(e)}")
            return default_config
    
    def _self_validate(self) -> bool:
        """Validate NEXUS against known intrusion signatures
        
        Returns:
            True if validation passes, False otherwise
        """
        # Check for suspicious modifications to NEXUS files
        nexus_dir = os.path.dirname(os.path.abspath(__file__))
        required_files = ['__init__.py', 'pulse.py', 'sync.py', 'suggest.py']
        
        for file in required_files:
            file_path = os.path.join(nexus_dir, file)
            if not os.path.exists(file_path):
                self._log_event(f"{SYMBOLS['BREACH']} NEXUS file missing: {file}")
                return False
        
        # TODO: Add file integrity checks (hash validation)
        
        # Basic self-test of functionality
        try:
            # Test memory buffer
            self.add_to_memory("NEXUS self-validation")
            
            # Test alert system
            self._emit_alert("SELF_TEST", "INFO", "NEXUS self-validation complete")
            
            return True
        except Exception as e:
            self._log_event(f"{SYMBOLS['BREACH']} NEXUS self-validation failed: {str(e)}")
            return False
    
    def _register_with_sentinel(self):
        """Register NEXUS with Sentinel for monitoring"""
        try:
            # Import here to avoid circular imports
            from vael_core.sentinel import register_entity
            register_entity('nexus', self)
            self._log_event(f"{SYMBOLS['TRACE']} Registered with Sentinel")
        except ImportError:
            self._log_event(f"{SYMBOLS['SUSPICIOUS']} Failed to register with Sentinel")
    
    def _register_with_antibody(self):
        """Register NEXUS with Antibody for self-healing"""
        try:
            # Import here to avoid circular imports
            from vael_core.antibody_interface import register_entity
            register_entity('nexus', self)
            self._log_event(f"{SYMBOLS['HEAL']} Registered with Antibody")
        except ImportError:
            self._log_event(f"{SYMBOLS['SUSPICIOUS']} Failed to register with Antibody")
    
    def scan(self, target: Any = None) -> Dict:
        """Scan for anomalies and threats
        
        Args:
            target: Specific target to scan (optional)
            
        Returns:
            Scan results with threat assessment
        """
        current_time = time.time()
        interval = self.high_alert_scan_interval if self.high_alert_mode else self.scan_interval
        
        # Enforce scan rate limits
        if current_time - self.last_scan_time < interval:
            return {"status": "RATE_LIMITED", "message": f"{SYMBOLS['BLOCK']} Scan rate limited"}
        
        self.last_scan_time = current_time
        
        # Perform the scan
        self._log_event(f"{SYMBOLS['SCAN']} Scanning {'target' if target else 'system'}")
        
        # TODO: Implement actual scanning logic
        # For now, return a placeholder result
        result = {
            "timestamp": current_time,
            "target": str(target) if target else "system",
            "threat_level": 0,
            "threat_name": THREAT_LEVELS[0],
            "findings": [],
            "symbolic": f"{SYMBOLS['CLEAR']} SIGMA/SCAN/{current_time}"
        }
        
        # Add to memory buffer
        self.add_to_memory(result)
        
        return result
    
    def set_high_alert(self, enabled: bool = True):
        """Set high alert mode
        
        Args:
            enabled: Whether to enable high alert mode
        """
        self.high_alert_mode = enabled
        status = "enabled" if enabled else "disabled"
        self._log_event(f"{SYMBOLS['ALERT' if enabled else 'CLEAR']} High alert mode {status}")
    
    def add_to_memory(self, entry: Any):
        """Add entry to memory buffer
        
        Args:
            entry: Data to add to memory
        """
        # Convert to string representation for token efficiency if needed
        if not isinstance(entry, (str, dict)):
            entry = str(entry)
        
        # Add timestamp if not present
        if isinstance(entry, dict) and 'timestamp' not in entry:
            entry['timestamp'] = time.time()
        
        self.memory_buffer.append(entry)
    
    def get_memory(self) -> List:
        """Get contents of memory buffer
        
        Returns:
            List of memory entries
        """
        return list(self.memory_buffer)
    
    def clear_memory(self):
        """Clear memory buffer"""
        self.memory_buffer.clear()
        self._log_event(f"{SYMBOLS['CLEAR']} Memory buffer cleared")
    
    def _emit_alert(self, alert_type: str, severity: str, message: str):
        """Emit an alert
        
        Args:
            alert_type: Type of alert
            severity: Alert severity
            message: Alert message
        """
        # Determine symbol based on severity
        if severity in ["CRITICAL", "HIGH"]:
            symbol = SYMBOLS["BREACH"]
        elif severity in ["MEDIUM", "LOW"]:
            symbol = SYMBOLS["SUSPICIOUS"]
        else:
            symbol = SYMBOLS["CLEAR"]
        
        alert = {
            "timestamp": time.time(),
            "type": alert_type,
            "severity": severity,
            "message": message,
            "symbolic": f"{symbol} NEXUS/{alert_type}/{severity}"
        }
        
        # Add to memory
        self.add_to_memory(alert)
        
        # Log the alert
        self._log_event(f"{symbol} {alert_type} ({severity}): {message}")
        
        # Trigger self-healing if needed
        if severity in ["CRITICAL", "HIGH"] and self.config.get("self_healing", True):
            self._trigger_self_healing(alert)
    
    def _trigger_self_healing(self, alert: Dict):
        """Trigger self-healing via Antibody
        
        Args:
            alert: Alert that triggered healing
        """
        try:
            # Import here to avoid circular imports
            from vael_core.antibody_interface import heal
            
            self._log_event(f"{SYMBOLS['HEAL']} Triggering self-healing for {alert['type']}")
            heal('nexus', alert)
        except ImportError:
            self._log_event(f"{SYMBOLS['SUSPICIOUS']} Failed to trigger self-healing")
    
    def _log_event(self, message: str):
        """Log an event
        
        Args:
            message: Event message
        """
        # Log locally
        logger.info(message)
        
        # Log to Sentinel if configured
        if self.config.get("log_to_sentinel", True):
            try:
                from vael_core.sentinel import log_event
                log_event('nexus', message)
            except ImportError:
                pass  # Silent fail for token efficiency
        
        # Log to Manus if configured
        if self.config.get("log_to_manus", True):
            try:
                from vael_core.manus_interface import log_event
                log_event('nexus', message)
            except ImportError:
                pass  # Silent fail for token efficiency

# Create singleton instance
nexus = NEXUS()

# Export public interface
def initialize(config_path: str = None) -> bool:
    """Initialize NEXUS with configuration
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        True if initialization successful, False otherwise
    """
    global nexus
    nexus = NEXUS(config_path)
    return nexus.initialized

def scan(target: Any = None) -> Dict:
    """Scan for anomalies and threats
    
    Args:
        target: Specific target to scan (optional)
        
    Returns:
        Scan results with threat assessment
    """
    return nexus.scan(target)

def set_high_alert(enabled: bool = True):
    """Set high alert mode
    
    Args:
        enabled: Whether to enable high alert mode
    """
    nexus.set_high_alert(enabled)

def get_memory() -> List:
    """Get contents of memory buffer
    
    Returns:
        List of memory entries
    """
    return nexus.get_memory()

def clear_memory():
    """Clear memory buffer"""
    nexus.clear_memory()
