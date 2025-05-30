"""
VAEL Core - Sentinel Security Module
====================================

The Sentinel module provides security monitoring, threat detection,
and message filtering capabilities for the VAEL system.

Key features:
- Message content scanning and filtering
- WebSocket traffic monitoring
- Threat detection and alerting
- Integration with NEXUS IDS
- Self-diagnostic capabilities

Usage:
    from sentinel import Sentinel
    
    # Create a Sentinel instance
    sentinel = Sentinel()
    
    # Scan a message
    is_safe, reason = sentinel.scan("User message here")
    
    # Get security suggestions
    suggestions = sentinel.suggest()
"""

__version__ = '0.1.0'

import logging
import re
import time
from typing import Dict, List, Tuple, Optional, Set, Any
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

class Sentinel:
    """
    Sentinel security monitoring and threat detection system.
    
    The Sentinel acts as a guardian for the VAEL ecosystem, scanning
    messages for security threats, monitoring WebSocket traffic,
    and providing self-diagnostic capabilities.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the Sentinel security system.
        
        Args:
            config: Optional configuration dictionary with settings
        """
        self.config = config or {}
        self.enabled = self.config.get('SENTINEL_ENABLED', True)
        self.last_pulse = time.time()
        self.threat_patterns = self._load_threat_patterns()
        self.blocked_terms = self._load_blocked_terms()
        self.scan_count = 0
        self.blocked_count = 0
        self.start_time = datetime.now()
        
        logger.info(f"Sentinel v{__version__} initialized and {'' if self.enabled else 'not '}enabled")
    
    def _load_threat_patterns(self) -> List[re.Pattern]:
        """Load regex patterns for threat detection."""
        patterns = [
            # SQL injection patterns
            re.compile(r"(?i)(select|insert|update|delete|drop|alter|create)\s+(from|into|table|database)", re.IGNORECASE),
            # Command injection patterns
            re.compile(r"(?i)(;|\||\|\||&&|\$\(|\`)(ls|cat|rm|chmod|wget|curl)", re.IGNORECASE),
            # Path traversal patterns
            re.compile(r"(?i)(\.\./|\.\./\./|/\.\./|/\.\./\.\.)", re.IGNORECASE),
        ]
        
        # Add custom patterns from config
        custom_patterns = self.config.get('SENTINEL_CUSTOM_PATTERNS', [])
        for pattern in custom_patterns:
            try:
                patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error:
                logger.error(f"Invalid regex pattern: {pattern}")
        
        return patterns
    
    def _load_blocked_terms(self) -> Set[str]:
        """Load blocked terms and phrases."""
        default_terms = {
            "drop table", "rm -rf", "shutdown", "reboot", 
            "format disk", "delete all", "sudo rm"
        }
        
        # Add custom terms from config
        custom_terms = set(self.config.get('SENTINEL_BLOCKED_TERMS', []))
        return default_terms.union(custom_terms)
    
    def scan(self, message: str) -> Tuple[bool, str]:
        """
        Scan a message for security threats.
        
        Args:
            message: The message to scan
            
        Returns:
            Tuple of (is_safe, reason)
        """
        if not self.enabled:
            return True, "Sentinel disabled"
        
        self.scan_count += 1
        self.last_pulse = time.time()
        
        # Check for blocked terms
        for term in self.blocked_terms:
            if term.lower() in message.lower():
                self.blocked_count += 1
                reason = f"Blocked term detected: {term}"
                logger.warning(f"Sentinel blocked message: {reason}")
                return False, reason
        
        # Check for threat patterns
        for pattern in self.threat_patterns:
            if pattern.search(message):
                self.blocked_count += 1
                reason = f"Potential security threat detected"
                logger.warning(f"Sentinel blocked message: {reason}")
                return False, reason
        
        return True, "ok"
    
    def pulse(self) -> Dict[str, Any]:
        """
        Emit a heartbeat pulse with status information.
        
        Returns:
            Dictionary with status information
        """
        self.last_pulse = time.time()
        
        return {
            "entity": "Sentinel",
            "version": __version__,
            "enabled": self.enabled,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "scan_count": self.scan_count,
            "blocked_count": self.blocked_count,
            "timestamp": time.time()
        }
    
    def suggest(self) -> List[Dict[str, Any]]:
        """
        Provide self-diagnostic suggestions.
        
        Returns:
            List of suggestion dictionaries
        """
        suggestions = []
        
        # Check if any patterns are loaded
        if not self.threat_patterns:
            suggestions.append({
                "severity": "warning",
                "message": "No threat patterns loaded",
                "action": "Configure SENTINEL_CUSTOM_PATTERNS in .env"
            })
        
        # Check if any terms are blocked
        if not self.blocked_terms:
            suggestions.append({
                "severity": "warning",
                "message": "No blocked terms configured",
                "action": "Configure SENTINEL_BLOCKED_TERMS in .env"
            })
        
        # Suggest NEXUS integration if not present
        try:
            import nexus
        except ImportError:
            suggestions.append({
                "severity": "info",
                "message": "NEXUS IDS integration not detected",
                "action": "Implement NEXUS for advanced threat detection"
            })
        
        return suggestions

# Convenience function to create a Sentinel instance
def create_sentinel(config: Dict = None) -> Sentinel:
    """Create and return a configured Sentinel instance."""
    return Sentinel(config)
