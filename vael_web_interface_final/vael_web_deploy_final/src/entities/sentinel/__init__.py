"""
VAEL Sentinel Entity - Security Monitoring System
-------------------------------------------------
The Sentinel entity inspects inbound and outbound messages for security threats,
enforces access controls, and maintains the integrity of the VAEL system.

This module provides:
- Rule-based security scanning
- Message sanitization
- Threat detection and response
- Self-diagnostic capabilities
"""

import re
import time
import logging
import json
from typing import Dict, List, Any, Optional, Pattern, Callable, Union
from enum import Enum, auto

from .. import Entity, registry

# Configure logger
logger = logging.getLogger(__name__)

class RuleAction(Enum):
    """Actions that can be taken when a rule matches."""
    ALLOW = auto()      # Allow the message to pass
    BLOCK = auto()      # Block the message
    SANITIZE = auto()   # Sanitize the message
    LOG = auto()        # Log the message but take no action
    ALERT = auto()      # Alert operators but allow the message


class Rule:
    """Security rule for message inspection."""
    
    def __init__(self, 
                 name: str, 
                 pattern: Union[str, Pattern], 
                 action: RuleAction = RuleAction.LOG,
                 description: str = "",
                 enabled: bool = True):
        """Initialize a new security rule.
        
        Args:
            name: Unique identifier for this rule
            pattern: Regex pattern to match
            action: Action to take when pattern matches
            description: Human-readable description of the rule
            enabled: Whether this rule is active
        """
        self.name = name
        self.description = description
        self.action = action
        self.enabled = enabled
        self._created_at = time.time()
        self._match_count = 0
        
        # Compile pattern if it's a string
        if isinstance(pattern, str):
            self.pattern = re.compile(pattern, re.IGNORECASE)
        else:
            self.pattern = pattern
    
    def matches(self, text: str) -> bool:
        """Check if this rule matches the given text.
        
        Args:
            text: The text to check
            
        Returns:
            True if the pattern matches, False otherwise
        """
        if not self.enabled:
            return False
        
        match = bool(self.pattern.search(text))
        if match:
            self._match_count += 1
        return match
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert this rule to a dictionary for serialization."""
        return {
            'name': self.name,
            'pattern': self.pattern.pattern,
            'action': self.action.name,
            'description': self.description,
            'enabled': self.enabled,
            'match_count': self._match_count,
            'created_at': self._created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rule':
        """Create a rule from a dictionary.
        
        Args:
            data: Dictionary representation of a rule
            
        Returns:
            A new Rule instance
        """
        action = RuleAction[data['action']] if isinstance(data['action'], str) else data['action']
        rule = cls(
            name=data['name'],
            pattern=data['pattern'],
            action=action,
            description=data.get('description', ''),
            enabled=data.get('enabled', True)
        )
        rule._match_count = data.get('match_count', 0)
        rule._created_at = data.get('created_at', time.time())
        return rule


class Sentinel(Entity):
    """Security entity that inspects messages for threats.
    
    The Sentinel:
    - Scans inbound and outbound messages
    - Applies security rules to detect threats
    - Takes appropriate actions based on rule matches
    - Provides self-diagnostics and suggestions
    """
    
    def __init__(self, name: str = "Sentinel", socketio=None):
        """Initialize a new Sentinel entity.
        
        Args:
            name: Name of this Sentinel instance
            socketio: Flask-SocketIO instance for emitting events
        """
        super().__init__(name, socketio)
        self.rules: Dict[str, Rule] = {}
        self._load_default_rules()
        self._threats_detected = 0
        self._messages_processed = 0
        self._last_threat_at = 0
        logger.info(f"Sentinel {name} initialized with {len(self.rules)} default rules")
    
    def _load_default_rules(self) -> None:
        """Load default security rules."""
        default_rules = [
            Rule(
                name="sql_injection",
                pattern=r"(?i)(select|update|delete|insert|drop|alter)\s+(from|into|table)",
                action=RuleAction.BLOCK,
                description="Blocks SQL injection attempts"
            ),
            Rule(
                name="xss_script",
                pattern=r"(?i)<script.*?>",
                action=RuleAction.SANITIZE,
                description="Sanitizes XSS script tags"
            ),
            Rule(
                name="command_injection",
                pattern=r"(?i)(;|\||\$\(|\`).*(sh|bash|cmd|powershell)",
                action=RuleAction.BLOCK,
                description="Blocks command injection attempts"
            ),
            Rule(
                name="path_traversal",
                pattern=r"(?i)\.\.(/|\\)",
                action=RuleAction.BLOCK,
                description="Blocks directory traversal attempts"
            ),
            Rule(
                name="sensitive_data",
                pattern=r"(?i)(password|api[-_]?key|secret|token)[\s:=]+\w+",
                action=RuleAction.LOG,
                description="Logs potential sensitive data exposure"
            ),
            # Symbolic trigger pattern - token efficient
            Rule(
                name="symbolic_access",
                pattern=r"\[\[VAEL::(ACCESS|CONTROL|ADMIN)\]\]",
                action=RuleAction.ALERT,
                description="Detects symbolic access control triggers"
            )
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
    
    def add_rule(self, rule: Rule) -> bool:
        """Add a security rule.
        
        Args:
            rule: The rule to add
            
        Returns:
            True if the rule was added, False otherwise
        """
        if rule.name in self.rules:
            logger.warning(f"Rule {rule.name} already exists, replacing")
        
        self.rules[rule.name] = rule
        logger.info(f"Added rule: {rule.name}")
        return True
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a security rule.
        
        Args:
            rule_name: Name of the rule to remove
            
        Returns:
            True if the rule was removed, False if it didn't exist
        """
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"Removed rule: {rule_name}")
            return True
        
        logger.warning(f"Rule {rule_name} not found")
        return False
    
    def get_rule(self, rule_name: str) -> Optional[Rule]:
        """Get a rule by name.
        
        Args:
            rule_name: Name of the rule to retrieve
            
        Returns:
            The rule if found, None otherwise
        """
        return self.rules.get(rule_name)
    
    def list_rules(self) -> List[Dict[str, Any]]:
        """List all security rules.
        
        Returns:
            List of rule dictionaries
        """
        return [rule.to_dict() for rule in self.rules.values()]
    
    def enable_rule(self, rule_name: str) -> bool:
        """Enable a security rule.
        
        Args:
            rule_name: Name of the rule to enable
            
        Returns:
            True if the rule was enabled, False if it doesn't exist
        """
        rule = self.get_rule(rule_name)
        if rule:
            rule.enabled = True
            logger.info(f"Enabled rule: {rule_name}")
            return True
        return False
    
    def disable_rule(self, rule_name: str) -> bool:
        """Disable a security rule.
        
        Args:
            rule_name: Name of the rule to disable
            
        Returns:
            True if the rule was disabled, False if it doesn't exist
        """
        rule = self.get_rule(rule_name)
        if rule:
            rule.enabled = False
            logger.info(f"Disabled rule: {rule_name}")
            return True
        return False
    
    def scan_text(self, text: str) -> Dict[str, Any]:
        """Scan text for security threats.
        
        Args:
            text: The text to scan
            
        Returns:
            Dictionary with scan results
        """
        results = {
            'text': text,
            'original_length': len(text),
            'threats_detected': 0,
            'actions_taken': [],
            'sanitized_text': text,
            'allowed': True
        }
        
        sanitized_text = text
        
        for rule_name, rule in self.rules.items():
            if rule.matches(text):
                results['threats_detected'] += 1
                self._threats_detected += 1
                self._last_threat_at = time.time()
                
                action_result = {
                    'rule': rule_name,
                    'action': rule.action.name
                }
                
                if rule.action == RuleAction.BLOCK:
                    results['allowed'] = False
                    action_result['result'] = 'blocked'
                    logger.warning(f"Blocked message due to rule {rule_name}")
                
                elif rule.action == RuleAction.SANITIZE:
                    sanitized_text = re.sub(rule.pattern, '[REDACTED]', sanitized_text)
                    action_result['result'] = 'sanitized'
                    logger.info(f"Sanitized message due to rule {rule_name}")
                
                elif rule.action == RuleAction.ALERT:
                    if self.socketio:
                        self.socketio.emit('sentinel_alert', {
                            'rule': rule_name,
                            'description': rule.description,
                            'timestamp': time.time()
                        })
                    action_result['result'] = 'alert_sent'
                    logger.warning(f"Sent alert due to rule {rule_name}")
                
                elif rule.action == RuleAction.LOG:
                    action_result['result'] = 'logged'
                    logger.info(f"Logged match for rule {rule_name}")
                
                results['actions_taken'].append(action_result)
        
        results['sanitized_text'] = sanitized_text
        results['final_length'] = len(sanitized_text)
        
        return results
    
    def process(self, data: Any) -> Any:
        """Process a message through the Sentinel.
        
        Args:
            data: The message to process
            
        Returns:
            Processed message (may be blocked or sanitized)
        """
        self._messages_processed += 1
        
        # If data is a string, scan it directly
        if isinstance(data, str):
            results = self.scan_text(data)
            return results['sanitized_text'] if results['allowed'] else None
        
        # If data is a dictionary with a 'message' field, scan that
        elif isinstance(data, dict) and 'message' in data:
            message = data['message']
            if isinstance(message, str):
                results = self.scan_text(message)
                if results['allowed']:
                    data['message'] = results['sanitized_text']
                    data['sentinel_processed'] = True
                    data['sentinel_actions'] = results['actions_taken']
                    return data
                else:
                    logger.warning(f"Message blocked by Sentinel: {message[:50]}...")
                    return None
        
        # If we can't process this data, return it unchanged
        logger.debug(f"Sentinel could not process data of type {type(data)}")
        return data
    
    def suggest(self) -> List[str]:
        """Provide self-diagnostic suggestions.
        
        Returns:
            List of suggestions for improvement
        """
        suggestions = super().suggest()
        
        # Add Sentinel-specific suggestions
        suggestions.extend([
            f"Total messages processed: {self._messages_processed}",
            f"Threats detected: {self._threats_detected}",
            f"Active rules: {sum(1 for rule in self.rules.values() if rule.enabled)}/{len(self.rules)}"
        ])
        
        # Suggest adding more rules if few exist
        if len(self.rules) < 5:
            suggestions.append("Consider adding more security rules for better protection")
        
        # Suggest reviewing rules if none are triggering
        if self._messages_processed > 100 and self._threats_detected == 0:
            suggestions.append("No threats detected after 100+ messages - review rule sensitivity")
        
        # Suggest enabling logging if many threats detected
        if self._threats_detected > 10:
            suggestions.append("Multiple threats detected - consider enabling detailed logging")
        
        return suggestions
    
    def sync(self) -> bool:
        """Sync Sentinel state with Codex memory.
        
        Returns:
            True if sync successful, False otherwise
        """
        try:
            # Symbolic trigger for memory sync
            if self.socketio:
                self.socketio.emit('sentinel_sync', {
                    'rules_count': len(self.rules),
                    'threats_detected': self._threats_detected,
                    'messages_processed': self._messages_processed,
                    'last_threat_at': self._last_threat_at
                })
            logger.debug(f"Sentinel {self.name} synced state")
            return True
        except Exception as e:
            logger.error(f"Sentinel sync failed: {e}")
            return False
    
    def export_rules(self, file_path: str) -> bool:
        """Export rules to a JSON file.
        
        Args:
            file_path: Path to save the rules
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            rules_data = [rule.to_dict() for rule in self.rules.values()]
            with open(file_path, 'w') as f:
                json.dump(rules_data, f, indent=2)
            logger.info(f"Exported {len(rules_data)} rules to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export rules: {e}")
            return False
    
    def import_rules(self, file_path: str, replace: bool = False) -> int:
        """Import rules from a JSON file.
        
        Args:
            file_path: Path to the rules file
            replace: Whether to replace existing rules
            
        Returns:
            Number of rules imported
        """
        try:
            with open(file_path, 'r') as f:
                rules_data = json.load(f)
            
            if replace:
                self.rules.clear()
                logger.info("Cleared existing rules")
            
            imported = 0
            for rule_data in rules_data:
                rule = Rule.from_dict(rule_data)
                self.add_rule(rule)
                imported += 1
            
            logger.info(f"Imported {imported} rules from {file_path}")
            return imported
        except Exception as e:
            logger.error(f"Failed to import rules: {e}")
            return 0


def create_sentinel(socketio=None) -> Sentinel:
    """Create and register a Sentinel entity.
    
    Args:
        socketio: Flask-SocketIO instance
        
    Returns:
        The created Sentinel instance
    """
    sentinel = Sentinel(socketio=socketio)
    registry.register(sentinel)
    return sentinel
