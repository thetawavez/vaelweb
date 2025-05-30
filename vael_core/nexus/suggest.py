"""
NEXUS Suggest Module - Threat Recommendation System

This module provides threat likelihood assessment and countermeasure recommendations
for the NEXUS entity. It analyzes anomaly data, prioritizes recommendations by impact,
and integrates with the antibody_interface for self-healing capabilities.

Token-efficient implementation with symbolic compression.
"""

import time
import json
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from collections import deque

# Import symbols from parent module
from vael_core.nexus import SYMBOLS, THREAT_LEVELS

# Configure logging
logger = logging.getLogger("vael.nexus.suggest")

class Suggest:
    """NEXUS Suggest recommendation engine"""
    
    def __init__(self):
        """Initialize the Suggest system"""
        self.recommendations = deque(maxlen=10)  # Last 10 recommendations for token efficiency
        self.last_suggest_time = 0
        self.suggest_interval = 5.0  # Default: suggest every 5 seconds
        self.confidence_threshold = 0.6  # Minimum confidence to include in recommendations
        self.learning_rate = 0.1  # Rate at which to learn from feedback
        self.feedback_history = deque(maxlen=20)  # Feedback history for learning
    
    def analyze(self, context: Dict = None) -> Dict:
        """Generate threat recommendations based on context
        
        Args:
            context: Current system context (optional)
            
        Returns:
            Recommendation results with countermeasures
        """
        current_time = time.time()
        
        # Rate limiting
        if current_time - self.last_suggest_time < self.suggest_interval:
            return {
                "status": "RATE_LIMITED",
                "symbol": SYMBOLS["BLOCK"],
                "message": "Suggestion rate limited"
            }
        
        self.last_suggest_time = current_time
        
        # Get anomaly data from pulse if not provided in context
        anomalies = self._get_anomaly_data(context)
        
        # Get rule data from sync
        rules = self._get_rule_data()
        
        # Assess threat likelihood
        threats = self._assess_threats(anomalies, rules)
        
        # Generate countermeasures
        countermeasures = self._generate_countermeasures(threats, rules)
        
        # Prioritize recommendations
        recommendations = self._prioritize_recommendations(countermeasures)
        
        # Prepare result with symbolic compression
        result = {
            "timestamp": current_time,
            "threat_count": len(threats),
            "recommendation_count": len(recommendations),
            "highest_priority": recommendations[0]["priority"] if recommendations else 0,
            "recommendations": recommendations,
            "symbol": self._get_recommendation_symbol(recommendations),
            "symbolic": f"{self._get_recommendation_symbol(recommendations)} NEXUS/SUGGEST/{current_time:.0f}"
        }
        
        # Store recommendation
        self.recommendations.append({
            "timestamp": current_time,
            "recommendations": recommendations
        })
        
        # Trigger self-healing for high-priority recommendations
        self._trigger_self_healing(recommendations)
        
        return result
    
    def _get_anomaly_data(self, context: Dict = None) -> List[Dict]:
        """Get anomaly data from pulse or context
        
        Args:
            context: Current system context (optional)
            
        Returns:
            List of anomalies
        """
        if context and "anomalies" in context:
            return context["anomalies"]
        
        try:
            # Import here to avoid circular imports
            from vael_core.nexus.pulse import get_anomaly_history
            return get_anomaly_history()
        except ImportError:
            logger.warning(f"{SYMBOLS['SUSPICIOUS']} Failed to import pulse module")
            return []
    
    def _get_rule_data(self) -> Dict:
        """Get rule data from sync
        
        Returns:
            Dictionary of rules
        """
        rules = {}
        
        try:
            # Import here to avoid circular imports
            from vael_core.nexus.sync import get_rules
            
            # Get different rule types
            rules["intrusion"] = get_rules("intrusion")
            rules["anomaly"] = get_rules("anomaly")
            rules["behavior"] = get_rules("behavior")
            rules["risk"] = get_rules("risk")
        except ImportError:
            logger.warning(f"{SYMBOLS['SUSPICIOUS']} Failed to import sync module")
        
        return rules
    
    def _assess_threats(self, anomalies: List[Dict], rules: Dict) -> List[Dict]:
        """Assess threat likelihood based on anomalies and rules
        
        Args:
            anomalies: List of detected anomalies
            rules: Dictionary of rules
            
        Returns:
            List of threat assessments
        """
        threats = []
        
        # Group anomalies by type
        anomaly_groups = {}
        for anomaly in anomalies:
            if isinstance(anomaly, dict) and "metric" in anomaly:
                metric = anomaly["metric"]
                if metric not in anomaly_groups:
                    anomaly_groups[metric] = []
                anomaly_groups[metric].append(anomaly)
        
        # Assess threats for each anomaly group
        for metric, group in anomaly_groups.items():
            # Find matching rules
            matching_rules = []
            for rule_type, rule_list in rules.items():
                for rule in rule_list:
                    if self._rule_matches_anomaly(rule, metric):
                        matching_rules.append(rule)
            
            # Calculate threat likelihood
            if matching_rules:
                # Use highest severity from matching rules
                severity = self._get_highest_severity(matching_rules)
                
                # Calculate confidence based on number and consistency of anomalies
                confidence = self._calculate_confidence(group, matching_rules)
                
                if confidence >= self.confidence_threshold:
                    threats.append({
                        "metric": metric,
                        "anomaly_count": len(group),
                        "severity": severity,
                        "confidence": confidence,
                        "matching_rules": [r.get("id", "unknown") for r in matching_rules],
                        "description": self._get_threat_description(matching_rules, group)
                    })
        
        return threats
    
    def _rule_matches_anomaly(self, rule: Dict, metric: str) -> bool:
        """Check if a rule matches an anomaly metric
        
        Args:
            rule: Rule definition
            metric: Anomaly metric
            
        Returns:
            True if rule matches, False otherwise
        """
        # Different rule types have different matching criteria
        if "metric" in rule and rule["metric"] == metric:
            return True
        
        if "metrics" in rule and metric in rule["metrics"]:
            return True
        
        if "pattern" in rule and metric in rule["pattern"]:
            return True
        
        return False
    
    def _get_highest_severity(self, rules: List[Dict]) -> str:
        """Get highest severity from a list of rules
        
        Args:
            rules: List of rules
            
        Returns:
            Highest severity
        """
        severity_order = {
            "CRITICAL": 4,
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1,
            "INFO": 0
        }
        
        highest = "INFO"
        highest_value = 0
        
        for rule in rules:
            severity = rule.get("severity", "INFO")
            value = severity_order.get(severity, 0)
            
            if value > highest_value:
                highest = severity
                highest_value = value
        
        return highest
    
    def _calculate_confidence(self, anomalies: List[Dict], rules: List[Dict]) -> float:
        """Calculate confidence score for threat assessment
        
        Args:
            anomalies: List of anomalies
            rules: List of matching rules
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not anomalies:
            return 0.0
        
        # Base confidence on number of anomalies
        base_confidence = min(0.5 + (len(anomalies) * 0.1), 0.8)
        
        # Adjust based on consistency of anomalies
        consistency = self._calculate_anomaly_consistency(anomalies)
        
        # Adjust based on rule specificity
        rule_specificity = self._calculate_rule_specificity(rules)
        
        # Combine factors
        confidence = (base_confidence * 0.5) + (consistency * 0.3) + (rule_specificity * 0.2)
        
        # Ensure within range
        return max(0.0, min(confidence, 1.0))
    
    def _calculate_anomaly_consistency(self, anomalies: List[Dict]) -> float:
        """Calculate consistency of anomalies
        
        Args:
            anomalies: List of anomalies
            
        Returns:
            Consistency score (0.0 to 1.0)
        """
        if len(anomalies) <= 1:
            return 0.5  # Neutral for single anomaly
        
        # Check if all anomalies have similar severity
        severities = [a.get("severity", "LOW") for a in anomalies if "severity" in a]
        if not severities:
            return 0.5
        
        # Count occurrences of each severity
        severity_counts = {}
        for severity in severities:
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Calculate consistency as ratio of most common severity
        most_common = max(severity_counts.values())
        consistency = most_common / len(severities)
        
        return consistency
    
    def _calculate_rule_specificity(self, rules: List[Dict]) -> float:
        """Calculate specificity of rules
        
        Args:
            rules: List of rules
            
        Returns:
            Specificity score (0.0 to 1.0)
        """
        if not rules:
            return 0.0
        
        # More specific rules have more fields
        avg_field_count = sum(len(r) for r in rules) / len(rules)
        
        # Normalize to 0.0-1.0 range (assuming most rules have 5-15 fields)
        specificity = min((avg_field_count - 5) / 10.0, 1.0)
        
        return max(0.0, specificity)
    
    def _get_threat_description(self, rules: List[Dict], anomalies: List[Dict]) -> str:
        """Generate threat description from rules and anomalies
        
        Args:
            rules: List of matching rules
            anomalies: List of anomalies
            
        Returns:
            Threat description
        """
        # Use description from highest severity rule
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            for rule in rules:
                if rule.get("severity") == severity and "description" in rule:
                    return rule["description"]
        
        # Fallback to generic description
        metric = anomalies[0].get("metric", "unknown") if anomalies else "unknown"
        return f"Potential threat detected in {metric}"
    
    def _generate_countermeasures(self, threats: List[Dict], rules: Dict) -> List[Dict]:
        """Generate countermeasures for threats
        
        Args:
            threats: List of threat assessments
            rules: Dictionary of rules
            
        Returns:
            List of countermeasures
        """
        countermeasures = []
        
        for threat in threats:
            # Find matching rules
            matching_rules = []
            for rule_id in threat.get("matching_rules", []):
                for rule_list in rules.values():
                    for rule in rule_list:
                        if rule.get("id") == rule_id:
                            matching_rules.append(rule)
            
            # Generate countermeasures from rules
            measures = self._get_countermeasures_from_rules(matching_rules, threat)
            
            # Add generic countermeasures if none found
            if not measures:
                measures = self._get_generic_countermeasures(threat)
            
            # Add to list with metadata
            for measure in measures:
                countermeasures.append({
                    "threat_metric": threat.get("metric"),
                    "threat_severity": threat.get("severity"),
                    "threat_confidence": threat.get("confidence"),
                    "action": measure.get("action"),
                    "description": measure.get("description"),
                    "impact": measure.get("impact", "MEDIUM"),
                    "automation": measure.get("automation", "MANUAL"),
                    "confidence": measure.get("confidence", threat.get("confidence", 0.5))
                })
        
        return countermeasures
    
    def _get_countermeasures_from_rules(self, rules: List[Dict], threat: Dict) -> List[Dict]:
        """Extract countermeasures from matching rules
        
        Args:
            rules: List of matching rules
            threat: Threat assessment
            
        Returns:
            List of countermeasures
        """
        countermeasures = []
        
        for rule in rules:
            # Extract mitigation from rule
            if "mitigation" in rule:
                countermeasures.append({
                    "action": "MITIGATE",
                    "description": rule["mitigation"],
                    "impact": rule.get("severity", "MEDIUM"),
                    "automation": "MANUAL",
                    "confidence": threat.get("confidence", 0.5)
                })
            
            # Extract remediation from rule
            if "remediation" in rule:
                countermeasures.append({
                    "action": "REMEDIATE",
                    "description": rule["remediation"],
                    "impact": rule.get("severity", "MEDIUM"),
                    "automation": rule.get("automation", "MANUAL"),
                    "confidence": threat.get("confidence", 0.5)
                })
            
            # Extract prevention from rule
            if "prevention" in rule:
                countermeasures.append({
                    "action": "PREVENT",
                    "description": rule["prevention"],
                    "impact": rule.get("severity", "MEDIUM"),
                    "automation": "MANUAL",
                    "confidence": threat.get("confidence", 0.5)
                })
        
        return countermeasures
    
    def _get_generic_countermeasures(self, threat: Dict) -> List[Dict]:
        """Generate generic countermeasures for a threat
        
        Args:
            threat: Threat assessment
            
        Returns:
            List of generic countermeasures
        """
        metric = threat.get("metric", "unknown")
        severity = threat.get("severity", "LOW")
        confidence = threat.get("confidence", 0.5)
        
        # Generic countermeasures based on metric type
        if "cpu" in metric.lower():
            return [{
                "action": "MONITOR",
                "description": "Monitor CPU usage and identify resource-intensive processes",
                "impact": severity,
                "automation": "ASSISTED",
                "confidence": confidence
            }, {
                "action": "OPTIMIZE",
                "description": "Optimize application code or scale resources",
                "impact": severity,
                "automation": "MANUAL",
                "confidence": confidence * 0.8  # Lower confidence for generic measure
            }]
        
        elif "memory" in metric.lower():
            return [{
                "action": "MONITOR",
                "description": "Monitor memory usage and check for memory leaks",
                "impact": severity,
                "automation": "ASSISTED",
                "confidence": confidence
            }, {
                "action": "OPTIMIZE",
                "description": "Increase memory allocation or optimize memory usage",
                "impact": severity,
                "automation": "MANUAL",
                "confidence": confidence * 0.8
            }]
        
        elif "error" in metric.lower() or "log" in metric.lower():
            return [{
                "action": "ANALYZE",
                "description": "Analyze error logs to identify root cause",
                "impact": severity,
                "automation": "ASSISTED",
                "confidence": confidence
            }, {
                "action": "REPAIR",
                "description": "Fix identified issues in application code or configuration",
                "impact": severity,
                "automation": "MANUAL",
                "confidence": confidence * 0.7
            }]
        
        elif "network" in metric.lower() or "traffic" in metric.lower():
            return [{
                "action": "MONITOR",
                "description": "Monitor network traffic for unusual patterns",
                "impact": severity,
                "automation": "ASSISTED",
                "confidence": confidence
            }, {
                "action": "RESTRICT",
                "description": "Implement rate limiting or access controls",
                "impact": severity,
                "automation": "ASSISTED",
                "confidence": confidence * 0.8
            }]
        
        # Default generic countermeasures
        return [{
            "action": "MONITOR",
            "description": f"Monitor {metric} for continued anomalies",
            "impact": severity,
            "automation": "ASSISTED",
            "confidence": confidence
        }, {
            "action": "INVESTIGATE",
            "description": f"Investigate root cause of {metric} anomalies",
            "impact": severity,
            "automation": "MANUAL",
            "confidence": confidence * 0.7
        }]
    
    def _prioritize_recommendations(self, countermeasures: List[Dict]) -> List[Dict]:
        """Prioritize recommendations by impact and confidence
        
        Args:
            countermeasures: List of countermeasures
            
        Returns:
            Prioritized list of recommendations
        """
        # Calculate priority score for each countermeasure
        for measure in countermeasures:
            # Convert impact to numeric value
            impact_value = {
                "CRITICAL": 1.0,
                "HIGH": 0.8,
                "MEDIUM": 0.5,
                "LOW": 0.3,
                "INFO": 0.1
            }.get(measure.get("impact", "MEDIUM"), 0.5)
            
            # Convert automation to numeric value (automated measures get higher priority)
            automation_value = {
                "AUTOMATIC": 1.0,
                "ASSISTED": 0.8,
                "MANUAL": 0.5
            }.get(measure.get("automation", "MANUAL"), 0.5)
            
            # Calculate priority score
            confidence = measure.get("confidence", 0.5)
            priority = (impact_value * 0.6) + (confidence * 0.3) + (automation_value * 0.1)
            
            # Add to measure
            measure["priority"] = priority
        
        # Sort by priority (descending)
        prioritized = sorted(countermeasures, key=lambda m: m.get("priority", 0), reverse=True)
        
        # Add symbolic indicators for token efficiency
        for i, measure in enumerate(prioritized):
            if i < 3:  # Top 3 recommendations
                symbol = {
                    "CRITICAL": SYMBOLS["BREACH"],
                    "HIGH": SYMBOLS["BREACH"],
                    "MEDIUM": SYMBOLS["SUSPICIOUS"],
                    "LOW": SYMBOLS["SUSPICIOUS"],
                    "INFO": SYMBOLS["CLEAR"]
                }.get(measure.get("impact", "MEDIUM"), SYMBOLS["SUSPICIOUS"])
                
                measure["symbol"] = symbol
                measure["rank"] = i + 1
                
                # Add symbolic representation
                action = measure.get("action", "ACT")
                measure["symbolic"] = f"{symbol} {action}/{measure.get('threat_metric', 'unknown')}"
        
        return prioritized
    
    def _get_recommendation_symbol(self, recommendations: List[Dict]) -> str:
        """Get symbolic representation for recommendations
        
        Args:
            recommendations: List of recommendations
            
        Returns:
            Symbol representing recommendations
        """
        if not recommendations:
            return SYMBOLS["CLEAR"]
        
        # Use symbol of highest priority recommendation
        return recommendations[0].get("symbol", SYMBOLS["SUSPICIOUS"])
    
    def _trigger_self_healing(self, recommendations: List[Dict]):
        """Trigger self-healing for high-priority recommendations
        
        Args:
            recommendations: List of prioritized recommendations
        """
        # Only trigger for automatic recommendations with high confidence
        for recommendation in recommendations:
            if (recommendation.get("automation") == "AUTOMATIC" and
                    recommendation.get("confidence", 0) >= 0.8 and
                    recommendation.get("priority", 0) >= 0.7):
                try:
                    # Import here to avoid circular imports
                    from vael_core.antibody_interface import heal
                    
                    logger.info(f"{SYMBOLS['HEAL']} Triggering self-healing for {recommendation.get('symbolic')}")
                    heal('nexus', recommendation)
                except ImportError:
                    logger.warning(f"{SYMBOLS['SUSPICIOUS']} Failed to import antibody_interface")
    
    def provide_feedback(self, recommendation_id: str, helpful: bool, comments: str = None):
        """Provide feedback on a recommendation to improve future suggestions
        
        Args:
            recommendation_id: ID of the recommendation
            helpful: Whether the recommendation was helpful
            comments: Additional comments (optional)
        """
        feedback = {
            "timestamp": time.time(),
            "recommendation_id": recommendation_id,
            "helpful": helpful,
            "comments": comments
        }
        
        # Add to feedback history
        self.feedback_history.append(feedback)
        
        # Learn from feedback (adjust confidence threshold)
        if len(self.feedback_history) >= 5:
            helpful_count = sum(1 for f in self.feedback_history if f.get("helpful", False))
            helpful_ratio = helpful_count / len(self.feedback_history)
            
            # Adjust confidence threshold based on feedback
            if helpful_ratio < 0.3:
                # Too many unhelpful recommendations, increase threshold
                self.confidence_threshold = min(self.confidence_threshold + self.learning_rate, 0.9)
            elif helpful_ratio > 0.7:
                # Mostly helpful recommendations, can lower threshold slightly
                self.confidence_threshold = max(self.confidence_threshold - self.learning_rate, 0.5)
            
            logger.info(f"{SYMBOLS['LEARN']} Adjusted confidence threshold to {self.confidence_threshold:.2f}")
    
    def get_recommendation_history(self) -> List[Dict]:
        """Get history of recommendations
        
        Returns:
            List of historical recommendations
        """
        return list(self.recommendations)

# Create singleton instance
suggest_system = Suggest()

# Public interface
def analyze(context: Dict = None) -> Dict:
    """Generate threat recommendations based on context
    
    Args:
        context: Current system context (optional)
        
    Returns:
        Recommendation results with countermeasures
    """
    return suggest_system.analyze(context)

def provide_feedback(recommendation_id: str, helpful: bool, comments: str = None):
    """Provide feedback on a recommendation to improve future suggestions
    
    Args:
        recommendation_id: ID of the recommendation
        helpful: Whether the recommendation was helpful
        comments: Additional comments (optional)
    """
    suggest_system.provide_feedback(recommendation_id, helpful, comments)

def get_recommendation_history() -> List[Dict]:
    """Get history of recommendations
    
    Returns:
        List of historical recommendations
    """
    return suggest_system.get_recommendation_history()
