"""
NEXUS Sync Module - Rule Management System

This module manages rule synchronization, baseline profiles, and risk models
for the NEXUS entity. It provides token-efficient rule loading, validation,
and update mechanisms with integrity checks.

Token-efficient implementation with symbolic compression.
"""

import os
import json
import time
import hashlib
import logging
import shutil
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Import symbols from parent module
from vael_core.nexus import SYMBOLS

# Configure logging
logger = logging.getLogger("vael.nexus.sync")

class Sync:
    """NEXUS Sync rule management system"""
    
    def __init__(self):
        """Initialize the Sync system"""
        self.rules = {}
        self.rule_versions = {}
        self.rule_hashes = {}
        self.last_sync_time = 0
        self.sync_interval = 3600  # Default: sync once per hour
        self.rule_paths = self._get_rule_paths()
        self.modified_rules = set()
        
        # Load initial rules
        self._load_all_rules()
    
    def _get_rule_paths(self) -> Dict[str, str]:
        """Get paths for different rule types
        
        Returns:
            Dictionary mapping rule types to file paths
        """
        base_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data',
            'nexus_rules'
        )
        
        # Create directory if it doesn't exist
        os.makedirs(base_path, exist_ok=True)
        
        return {
            "intrusion": os.path.join(base_path, "intrusion_rules.json"),
            "anomaly": os.path.join(base_path, "anomaly_rules.json"),
            "behavior": os.path.join(base_path, "behavior_rules.json"),
            "baseline": os.path.join(base_path, "baseline_profiles.json"),
            "risk": os.path.join(base_path, "risk_models.json")
        }
    
    def _load_all_rules(self):
        """Load all rule sets"""
        for rule_type, path in self.rule_paths.items():
            self._load_rules(rule_type, path)
    
    def _load_rules(self, rule_type: str, path: str):
        """Load rules from file
        
        Args:
            rule_type: Type of rules to load
            path: Path to rule file
        """
        # Create default rules if file doesn't exist
        if not os.path.exists(path):
            self._create_default_rules(rule_type, path)
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                
                # Validate structure
                if not isinstance(data, dict) or 'version' not in data or 'rules' not in data:
                    logger.warning(f"{SYMBOLS['SUSPICIOUS']} Invalid rule format in {path}")
                    self._create_default_rules(rule_type, path)
                    with open(path, 'r') as f:
                        data = json.load(f)
                
                # Store rules and version
                self.rules[rule_type] = data['rules']
                self.rule_versions[rule_type] = data['version']
                
                # Compute and store hash for integrity checking
                rule_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
                self.rule_hashes[rule_type] = rule_hash
                
                logger.info(f"{SYMBOLS['RULE']} Loaded {len(data['rules'])} {rule_type} rules (v{data['version']})")
        
        except Exception as e:
            logger.error(f"{SYMBOLS['SUSPICIOUS']} Failed to load {rule_type} rules: {str(e)}")
            # Create default rules on error
            self._create_default_rules(rule_type, path)
            # Try loading again
            with open(path, 'r') as f:
                data = json.load(f)
                self.rules[rule_type] = data['rules']
                self.rule_versions[rule_type] = data['version']
    
    def _create_default_rules(self, rule_type: str, path: str):
        """Create default rules for a rule type
        
        Args:
            rule_type: Type of rules to create
            path: Path to save rules
        """
        default_rules = {
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "rules": []
        }
        
        # Add default rules based on type
        if rule_type == "intrusion":
            default_rules["rules"] = [
                {
                    "id": "INT001",
                    "name": "SQL Injection Attempt",
                    "pattern": "SELECT.*FROM.*WHERE",
                    "severity": "HIGH",
                    "description": "Possible SQL injection attempt detected",
                    "mitigation": "Validate and sanitize all input"
                },
                {
                    "id": "INT002",
                    "name": "Cross-Site Scripting",
                    "pattern": "<script>.*</script>",
                    "severity": "MEDIUM",
                    "description": "Possible XSS attempt detected",
                    "mitigation": "Encode output and validate input"
                }
            ]
        elif rule_type == "anomaly":
            default_rules["rules"] = [
                {
                    "id": "ANM001",
                    "name": "Unusual CPU Usage",
                    "metric": "cpu_usage",
                    "threshold": 3.0,  # 3 standard deviations
                    "duration": 60,    # sustained for 60 seconds
                    "severity": "MEDIUM",
                    "description": "CPU usage significantly above baseline"
                },
                {
                    "id": "ANM002",
                    "name": "High Error Rate",
                    "metric": "error_rate",
                    "threshold": 0.1,  # 10% errors
                    "duration": 300,   # sustained for 5 minutes
                    "severity": "HIGH",
                    "description": "Error rate significantly above baseline"
                }
            ]
        elif rule_type == "behavior":
            default_rules["rules"] = [
                {
                    "id": "BHV001",
                    "name": "Unusual Access Pattern",
                    "pattern": "rapid_sequential_access",
                    "threshold": 10,   # 10 accesses per second
                    "severity": "LOW",
                    "description": "Unusual pattern of resource access detected"
                },
                {
                    "id": "BHV002",
                    "name": "Off-hours Activity",
                    "pattern": "time_based_anomaly",
                    "parameters": {
                        "start_hour": 22,  # 10 PM
                        "end_hour": 6      # 6 AM
                    },
                    "severity": "LOW",
                    "description": "Activity detected outside normal operating hours"
                }
            ]
        elif rule_type == "baseline":
            default_rules["rules"] = [
                {
                    "id": "BAS001",
                    "name": "System Resource Baseline",
                    "metrics": {
                        "cpu_usage": {"mean": 30.0, "std": 15.0},
                        "memory_usage": {"mean": 40.0, "std": 20.0},
                        "disk_io": {"mean": 5.0, "std": 3.0}
                    },
                    "updated": datetime.now().isoformat()
                },
                {
                    "id": "BAS002",
                    "name": "Network Traffic Baseline",
                    "metrics": {
                        "request_rate": {"mean": 10.0, "std": 5.0},
                        "bandwidth_usage": {"mean": 1024.0, "std": 512.0},
                        "connection_count": {"mean": 20.0, "std": 10.0}
                    },
                    "updated": datetime.now().isoformat()
                }
            ]
        elif rule_type == "risk":
            default_rules["rules"] = [
                {
                    "id": "RSK001",
                    "name": "Basic Risk Model",
                    "factors": [
                        {"factor": "intrusion_severity", "weight": 0.4},
                        {"factor": "anomaly_count", "weight": 0.3},
                        {"factor": "behavior_deviation", "weight": 0.2},
                        {"factor": "system_health", "weight": 0.1}
                    ],
                    "thresholds": {
                        "low": 0.3,
                        "medium": 0.6,
                        "high": 0.8
                    },
                    "description": "Basic risk assessment model"
                }
            ]
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Write default rules to file
        with open(path, 'w') as f:
            json.dump(default_rules, f, indent=2)
        
        logger.info(f"{SYMBOLS['RULE']} Created default {rule_type} rules")
    
    def sync(self, force: bool = False) -> Dict:
        """Synchronize rules with latest versions
        
        Args:
            force: Force synchronization regardless of interval
            
        Returns:
            Synchronization results
        """
        current_time = time.time()
        
        # Check if sync is needed based on interval
        if not force and current_time - self.last_sync_time < self.sync_interval:
            return {
                "status": "SKIPPED",
                "symbol": SYMBOLS["BLOCK"],
                "message": "Sync skipped (within interval)",
                "next_sync": self.last_sync_time + self.sync_interval
            }
        
        self.last_sync_time = current_time
        
        # Check for external updates to rule files
        updated_rules = self._check_rule_updates()
        
        # Apply any pending rule modifications
        self._apply_rule_modifications()
        
        # Sync with remote sources if configured
        remote_updates = self._sync_with_remote()
        
        # Update baselines if needed
        baseline_updates = self._update_baselines()
        
        # Prepare result with symbolic compression
        result = {
            "timestamp": current_time,
            "status": "SUCCESS",
            "symbol": SYMBOLS["RULE"],
            "file_updates": updated_rules,
            "remote_updates": remote_updates,
            "baseline_updates": baseline_updates,
            "modified_rules": list(self.modified_rules),
            "symbolic": f"{SYMBOLS['RULE']} NEXUS/SYNC/{current_time:.0f}"
        }
        
        # Clear modified rules after sync
        self.modified_rules.clear()
        
        return result
    
    def _check_rule_updates(self) -> List[str]:
        """Check for external updates to rule files
        
        Returns:
            List of updated rule types
        """
        updated_rules = []
        
        for rule_type, path in self.rule_paths.items():
            if os.path.exists(path):
                try:
                    # Read current file
                    with open(path, 'r') as f:
                        data = json.load(f)
                    
                    # Compute hash
                    current_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
                    
                    # Compare with stored hash
                    if rule_type in self.rule_hashes and current_hash != self.rule_hashes[rule_type]:
                        logger.info(f"{SYMBOLS['RULE']} External update detected for {rule_type} rules")
                        
                        # Reload rules
                        self.rules[rule_type] = data['rules']
                        self.rule_versions[rule_type] = data['version']
                        self.rule_hashes[rule_type] = current_hash
                        
                        updated_rules.append(rule_type)
                
                except Exception as e:
                    logger.error(f"{SYMBOLS['SUSPICIOUS']} Error checking updates for {rule_type}: {str(e)}")
        
        return updated_rules
    
    def _apply_rule_modifications(self):
        """Apply pending rule modifications"""
        for rule_type in self.modified_rules:
            if rule_type in self.rules and rule_type in self.rule_paths:
                try:
                    # Increment version
                    if rule_type in self.rule_versions:
                        version_parts = self.rule_versions[rule_type].split('.')
                        version_parts[-1] = str(int(version_parts[-1]) + 1)
                        self.rule_versions[rule_type] = '.'.join(version_parts)
                    else:
                        self.rule_versions[rule_type] = "1.0.0"
                    
                    # Prepare data for saving
                    data = {
                        "version": self.rule_versions[rule_type],
                        "updated": datetime.now().isoformat(),
                        "rules": self.rules[rule_type]
                    }
                    
                    # Create backup
                    path = self.rule_paths[rule_type]
                    if os.path.exists(path):
                        backup_path = f"{path}.bak"
                        shutil.copy2(path, backup_path)
                    
                    # Save updated rules
                    with open(path, 'w') as f:
                        json.dump(data, f, indent=2)
                    
                    # Update hash
                    self.rule_hashes[rule_type] = hashlib.sha256(
                        json.dumps(data, sort_keys=True).encode()
                    ).hexdigest()
                    
                    logger.info(f"{SYMBOLS['RULE']} Updated {rule_type} rules (v{self.rule_versions[rule_type]})")
                
                except Exception as e:
                    logger.error(f"{SYMBOLS['SUSPICIOUS']} Failed to save {rule_type} rules: {str(e)}")
    
    def _sync_with_remote(self) -> Dict:
        """Synchronize rules with remote sources
        
        Returns:
            Remote synchronization results
        """
        # Placeholder for remote synchronization
        # In a real implementation, this would connect to a central rule repository
        
        return {
            "status": "SUCCESS",
            "updated": [],
            "message": "Remote sync not configured"
        }
    
    def _update_baselines(self) -> Dict:
        """Update baseline profiles based on recent data
        
        Returns:
            Baseline update results
        """
        # Placeholder for baseline updates
        # In a real implementation, this would analyze recent metrics and update baselines
        
        return {
            "status": "SUCCESS",
            "updated": [],
            "message": "No baseline updates needed"
        }
    
    def get_rules(self, rule_type: str) -> List[Dict]:
        """Get rules of a specific type
        
        Args:
            rule_type: Type of rules to retrieve
            
        Returns:
            List of rules
        """
        return self.rules.get(rule_type, [])
    
    def get_rule_version(self, rule_type: str) -> str:
        """Get version of a rule set
        
        Args:
            rule_type: Type of rules
            
        Returns:
            Version string
        """
        return self.rule_versions.get(rule_type, "0.0.0")
    
    def add_rule(self, rule_type: str, rule: Dict) -> bool:
        """Add a new rule
        
        Args:
            rule_type: Type of rule to add
            rule: Rule definition
            
        Returns:
            True if successful, False otherwise
        """
        if rule_type not in self.rules:
            self.rules[rule_type] = []
        
        # Check if rule with same ID already exists
        for existing_rule in self.rules[rule_type]:
            if existing_rule.get('id') == rule.get('id'):
                logger.warning(f"{SYMBOLS['SUSPICIOUS']} Rule {rule.get('id')} already exists")
                return False
        
        # Add rule
        self.rules[rule_type].append(rule)
        self.modified_rules.add(rule_type)
        
        logger.info(f"{SYMBOLS['RULE']} Added rule {rule.get('id')} to {rule_type}")
        return True
    
    def update_rule(self, rule_type: str, rule_id: str, updates: Dict) -> bool:
        """Update an existing rule
        
        Args:
            rule_type: Type of rule to update
            rule_id: ID of rule to update
            updates: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        if rule_type not in self.rules:
            logger.warning(f"{SYMBOLS['SUSPICIOUS']} Rule type {rule_type} does not exist")
            return False
        
        # Find rule with matching ID
        for i, rule in enumerate(self.rules[rule_type]):
            if rule.get('id') == rule_id:
                # Update fields
                for key, value in updates.items():
                    rule[key] = value
                
                # Update rule in list
                self.rules[rule_type][i] = rule
                self.modified_rules.add(rule_type)
                
                logger.info(f"{SYMBOLS['RULE']} Updated rule {rule_id} in {rule_type}")
                return True
        
        logger.warning(f"{SYMBOLS['SUSPICIOUS']} Rule {rule_id} not found in {rule_type}")
        return False
    
    def delete_rule(self, rule_type: str, rule_id: str) -> bool:
        """Delete a rule
        
        Args:
            rule_type: Type of rule to delete
            rule_id: ID of rule to delete
            
        Returns:
            True if successful, False otherwise
        """
        if rule_type not in self.rules:
            logger.warning(f"{SYMBOLS['SUSPICIOUS']} Rule type {rule_type} does not exist")
            return False
        
        # Find rule with matching ID
        for i, rule in enumerate(self.rules[rule_type]):
            if rule.get('id') == rule_id:
                # Remove rule
                self.rules[rule_type].pop(i)
                self.modified_rules.add(rule_type)
                
                logger.info(f"{SYMBOLS['RULE']} Deleted rule {rule_id} from {rule_type}")
                return True
        
        logger.warning(f"{SYMBOLS['SUSPICIOUS']} Rule {rule_id} not found in {rule_type}")
        return False
    
    def update_baseline(self, baseline_id: str, metrics: Dict) -> bool:
        """Update a baseline profile
        
        Args:
            baseline_id: ID of baseline to update
            metrics: Updated metric values
            
        Returns:
            True if successful, False otherwise
        """
        return self.update_rule("baseline", baseline_id, {
            "metrics": metrics,
            "updated": datetime.now().isoformat()
        })
    
    def verify_integrity(self) -> Dict:
        """Verify integrity of all rule files
        
        Returns:
            Integrity verification results
        """
        results = {
            "status": "SUCCESS",
            "verified": [],
            "failed": []
        }
        
        for rule_type, path in self.rule_paths.items():
            if os.path.exists(path):
                try:
                    # Read current file
                    with open(path, 'r') as f:
                        data = json.load(f)
                    
                    # Compute hash
                    current_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
                    
                    # Compare with stored hash
                    if rule_type in self.rule_hashes:
                        if current_hash == self.rule_hashes[rule_type]:
                            results["verified"].append(rule_type)
                        else:
                            results["failed"].append({
                                "type": rule_type,
                                "reason": "Hash mismatch"
                            })
                            logger.warning(f"{SYMBOLS['SUSPICIOUS']} Integrity check failed for {rule_type}")
                    else:
                        # No stored hash, store the current one
                        self.rule_hashes[rule_type] = current_hash
                        results["verified"].append(rule_type)
                
                except Exception as e:
                    results["failed"].append({
                        "type": rule_type,
                        "reason": str(e)
                    })
                    logger.error(f"{SYMBOLS['SUSPICIOUS']} Error verifying {rule_type}: {str(e)}")
        
        if results["failed"]:
            results["status"] = "FAILED"
        
        return results

# Create singleton instance
sync_system = Sync()

# Public interface
def sync(force: bool = False) -> Dict:
    """Synchronize rules with latest versions
    
    Args:
        force: Force synchronization regardless of interval
        
    Returns:
        Synchronization results
    """
    return sync_system.sync(force)

def get_rules(rule_type: str) -> List[Dict]:
    """Get rules of a specific type
    
    Args:
        rule_type: Type of rules to retrieve
        
    Returns:
        List of rules
    """
    return sync_system.get_rules(rule_type)

def get_rule_version(rule_type: str) -> str:
    """Get version of a rule set
    
    Args:
        rule_type: Type of rules
        
    Returns:
        Version string
    """
    return sync_system.get_rule_version(rule_type)

def add_rule(rule_type: str, rule: Dict) -> bool:
    """Add a new rule
    
    Args:
        rule_type: Type of rule to add
        rule: Rule definition
        
    Returns:
        True if successful, False otherwise
    """
    return sync_system.add_rule(rule_type, rule)

def update_rule(rule_type: str, rule_id: str, updates: Dict) -> bool:
    """Update an existing rule
    
    Args:
        rule_type: Type of rule to update
        rule_id: ID of rule to update
        updates: Fields to update
        
    Returns:
        True if successful, False otherwise
    """
    return sync_system.update_rule(rule_type, rule_id, updates)

def delete_rule(rule_type: str, rule_id: str) -> bool:
    """Delete a rule
    
    Args:
        rule_type: Type of rule to delete
        rule_id: ID of rule to delete
        
    Returns:
        True if successful, False otherwise
    """
    return sync_system.delete_rule(rule_type, rule_id)

def update_baseline(baseline_id: str, metrics: Dict) -> bool:
    """Update a baseline profile
    
    Args:
        baseline_id: ID of baseline to update
        metrics: Updated metric values
        
    Returns:
        True if successful, False otherwise
    """
    return sync_system.update_baseline(baseline_id, metrics)

def verify_integrity() -> Dict:
    """Verify integrity of all rule files
    
    Returns:
        Integrity verification results
    """
    return sync_system.verify_integrity()
