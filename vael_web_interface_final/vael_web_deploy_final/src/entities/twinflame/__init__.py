"""
VAEL Twin Flame Entity - Bi-Hemisphere Parallel Processing
----------------------------------------------------------
The Twin Flame entity implements a dual-processing architecture inspired by
the human brain's hemispheric specialization. It distributes tasks between
logical (left) and intuitive (right) processing pathways, then merges the
results for a more comprehensive solution.

This module provides:
- Parallel processing of tasks across two specialized hemispheres
- Left hemisphere: Analytical, logical, sequential processing
- Right hemisphere: Intuitive, holistic, pattern-based processing
- Result merging with configurable weighting
- Self-diagnostic capabilities
"""

import time
import logging
import threading
import json
import random
import re
import os # Added os import for commonprefix
from enum import Enum, auto
from typing import Dict, List, Any, Optional, Callable, Union, Tuple

from .. import Entity, registry

# Configure logger
logger = logging.getLogger(__name__)


class HemisphereType(Enum):
    """Types of hemispheres in the Twin Flame entity."""
    LEFT = auto()    # Logical, analytical, sequential
    RIGHT = auto()   # Intuitive, creative, holistic


class TaskPriority(Enum):
    """Priority levels for Twin Flame tasks."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


class TaskStatus(Enum):
    """Status of a Twin Flame task."""
    PENDING = auto()
    PROCESSING_LEFT = auto()
    PROCESSING_RIGHT = auto()
    COMPLETED_LEFT = auto() # Not used in current flow, but kept for potential future use
    COMPLETED_RIGHT = auto()
    MERGED = auto()
    FAILED = auto()


class ProcessingMode(Enum):
    """Processing modes for the Twin Flame entity."""
    SEQUENTIAL = auto()   # Process tasks sequentially
    PARALLEL = auto()     # Process tasks in parallel
    ADAPTIVE = auto()     # Adapt based on workload


class Task:
    """Represents a task to be processed by the Twin Flame entity."""
    
    def __init__(self, 
                 task_id: str,
                 data: Any,
                 priority: TaskPriority = TaskPriority.MEDIUM,
                 metadata: Dict[str, Any] = None):
        """Initialize a new task.
        
        Args:
            task_id: Unique identifier for this task
            data: The data to process
            priority: Priority level for this task
            metadata: Additional task metadata
        """
        self.task_id = task_id
        self.data = data
        self.priority = priority
        self.metadata = metadata or {}
        self.status = TaskStatus.PENDING
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None
        self.left_result = None
        self.right_result = None
        self.merged_result = None
        self.error = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert this task to a dictionary for serialization."""
        return {
            'task_id': self.task_id,
            'priority': self.priority.name,
            'status': self.status.name,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'metadata': self.metadata,
            'has_left_result': self.left_result is not None,
            'has_right_result': self.right_result is not None,
            'has_merged_result': self.merged_result is not None,
            'error': self.error
        }


class Hemisphere:
    """Base class for hemisphere-specific processing."""
    
    def __init__(self, hemisphere_type: HemisphereType, name: str = None):
        """Initialize a new hemisphere.
        
        Args:
            hemisphere_type: Type of this hemisphere (LEFT or RIGHT)
            name: Optional name for this hemisphere
        """
        self.type = hemisphere_type
        self.name = name or f"{hemisphere_type.name.lower()}_hemisphere"
        self._active = False
        self._tasks_processed = 0
        self._processing_time = 0.0 # Ensure float
        self._errors = 0
        self._lock = threading.RLock()
    
    def activate(self) -> bool:
        """Activate this hemisphere."""
        self._active = True
        logger.info(f"Hemisphere {self.name} activated")
        return True
    
    def deactivate(self) -> bool:
        """Deactivate this hemisphere."""
        self._active = False
        logger.info(f"Hemisphere {self.name} deactivated")
        return True
    
    def is_active(self) -> bool:
        """Check if this hemisphere is active."""
        return self._active
    
    def process(self, task: Task) -> Any:
        """Process a task using this hemisphere.
        
        Args:
            task: The task to process
            
        Returns:
            Processing result
        """
        raise NotImplementedError("Hemisphere subclasses must implement process()")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics for this hemisphere."""
        with self._lock:
            return {
                'type': self.type.name,
                'name': self.name,
                'active': self._active,
                'tasks_processed': self._tasks_processed,
                'processing_time': self._processing_time,
                'avg_processing_time': (
                    self._processing_time / self._tasks_processed 
                    if self._tasks_processed > 0 else 0.0 # Ensure float
                ),
                'errors': self._errors
            }


class LeftHemisphere(Hemisphere):
    """Left hemisphere implementation focusing on logical, analytical processing."""
    
    def __init__(self, name: str = "left_hemisphere"):
        """Initialize a new left hemisphere.
        
        Args:
            name: Name for this hemisphere
        """
        super().__init__(HemisphereType.LEFT, name)
        
        # Define logical processing patterns
        self._patterns = {
            # Symbolic patterns for token efficiency
            "[[ANALYZE]]": self._analyze_data,
            "[[CATEGORIZE]]": self._categorize_data,
            "[[SEQUENCE]]": self._sequence_data,
            "[[VALIDATE]]": self._validate_data,
            "[[OPTIMIZE]]": self._optimize_data
        }
    
    def process(self, task: Task) -> Any:
        """Process a task using logical, analytical methods.
        
        Args:
            task: The task to process
            
        Returns:
            Logical processing result
        """
        if not self._active:
            logger.warning(f"Attempted to process task on inactive hemisphere {self.name}")
            return None
        
        # Track processing metrics
        start_time = time.time()
        
        try:
            # Determine the processing approach based on task data
            data = task.data
            result = None
            
            # Check if this is a symbolic task
            if isinstance(data, str):
                # Look for symbolic patterns
                for pattern, handler in self._patterns.items():
                    if pattern in data:
                        # Extract the actual data to process
                        actual_data = data.replace(pattern, "").strip()
                        result = handler(actual_data)
                        break
            
            # If no symbolic pattern matched or data isn't a string,
            # use default analytical processing
            if result is None:
                result = self._default_process(data)
            
            # Update task processing metrics
            with self._lock:
                self._tasks_processed += 1
                self._processing_time += (time.time() - start_time)
            
            return result
            
        except Exception as e:
            # Handle processing errors
            with self._lock:
                self._errors += 1
            
            logger.error(f"Error in {self.name} processing: {e}")
            return {"error": str(e), "partial_result": None}
    
    def _default_process(self, data: Any) -> Any:
        """Default processing method for the left hemisphere.
        
        Args:
            data: Data to process
            
        Returns:
            Processed result
        """
        # For string data, perform analytical text processing
        if isinstance(data, str):
            return {
                "word_count": len(data.split()),
                "character_count": len(data),
                "structure": self._analyze_structure(data),
                "keywords": self._extract_keywords(data)
            }
        
        # For dictionary data, analyze structure and validate
        elif isinstance(data, dict):
            return {
                "keys": list(data.keys()),
                "types": {k: type(v).__name__ for k, v in data.items()},
                "validation": self._validate_dict(data)
            }
        
        # For list data, categorize and sequence
        elif isinstance(data, list):
            return {
                "length": len(data),
                "types": self._categorize_list_items(data),
                "sequence": self._analyze_sequence(data)
            }
        
        # For other data types, return basic type information
        return {
            "type": type(data).__name__,
            "analytical_value": str(data)
        }
    
    def _analyze_data(self, data: Any) -> Dict[str, Any]:
        """Analyze data structure and content.
        
        Args:
            data: Data to analyze
            
        Returns:
            Analysis results
        """
        # This is a simplified implementation for demonstration
        return {
            "type": type(data).__name__,
            "complexity": self._calculate_complexity(data),
            "structure": self._analyze_structure(data)
        }
    
    def _categorize_data(self, data: Any) -> Dict[str, Any]:
        """Categorize data into logical groups.
        
        Args:
            data: Data to categorize
            
        Returns:
            Categorization results
        """
        # This is a simplified implementation for demonstration
        if isinstance(data, str):
            # Categorize text
            categories = {
                "questions": len(re.findall(r'\?', data)),
                "statements": len(re.findall(r'\.', data)),
                "commands": len(re.findall(r'!', data)),
                "numeric": len(re.findall(r'\d+', data))
            }
            return categories
        
        elif isinstance(data, list):
            # Categorize list items
            return self._categorize_list_items(data)
        
        return {"category": "unknown", "data": str(data)}
    
    def _sequence_data(self, data: Any) -> Dict[str, Any]:
        """Arrange data in logical sequences.
        
        Args:
            data: Data to sequence
            
        Returns:
            Sequencing results
        """
        # This is a simplified implementation for demonstration
        if isinstance(data, list):
            return self._analyze_sequence(data)
        
        return {"sequence": "non-sequential", "data": str(data)}
    
    def _validate_data(self, data: Any) -> Dict[str, Any]:
        """Validate data against logical rules.
        
        Args:
            data: Data to validate
            
        Returns:
            Validation results
        """
        # This is a simplified implementation for demonstration
        if isinstance(data, dict):
            return self._validate_dict(data)
        
        return {"valid": True, "reason": "No validation rules for this data type"}
    
    def _optimize_data(self, data: Any) -> Any:
        """Optimize data for efficiency.
        
        Args:
            data: Data to optimize
            
        Returns:
            Optimized data
        """
        # This is a simplified implementation for demonstration
        # In a real system, this would implement actual optimization
        return data
    
    def _calculate_complexity(self, data: Any) -> float:
        """Calculate the complexity of data.
        
        Args:
            data: Data to analyze
            
        Returns:
            Complexity score (0.0-1.0)
        """
        # This is a simplified implementation for demonstration
        if isinstance(data, str):
            # Text complexity based on length and unique words
            words = data.split()
            if not words: return 0.0
            unique_words = set(words)
            return min(1.0, (len(words) / 100.0) * (len(unique_words) / float(len(words))))
        
        elif isinstance(data, dict):
            # Dictionary complexity based on keys and nesting
            return min(1.0, (len(data) / 20.0) * self._calculate_nesting(data))
        
        elif isinstance(data, list):
            # List complexity based on length and item types
            if not data: return 0.0
            return min(1.0, (len(data) / 50.0) * len(set(type(x).__name__ for x in data)) / 5.0)
        
        return 0.1
    
    def _calculate_nesting(self, data: Dict[str, Any], depth: int = 0) -> float:
        """Calculate the nesting level of a dictionary.
        
        Args:
            data: Dictionary to analyze
            depth: Current depth level
            
        Returns:
            Nesting score (0.0-1.0)
        """
        if not isinstance(data, dict) or depth > 5:
            return 0.0
        
        nesting = 0.0
        for key, value in data.items():
            if isinstance(value, dict):
                nesting += 0.2 + 0.8 * self._calculate_nesting(value, depth + 1)
            elif isinstance(value, list) and any(isinstance(x, dict) for x in value):
                nesting += 0.1 + 0.1 * sum(
                    self._calculate_nesting(x, depth + 1) 
                    for x in value if isinstance(x, dict)
                )
        
        return min(1.0, nesting)
    
    def _analyze_structure(self, data: Any) -> Dict[str, Any]:
        """Analyze the structure of data.
        
        Args:
            data: Data to analyze
            
        Returns:
            Structure analysis
        """
        # This is a simplified implementation for demonstration
        if isinstance(data, str):
            # Analyze text structure
            sentences = len(re.findall(r'[.!?]+', data))
            paragraphs = len(re.findall(r'\n\s*\n', data)) + 1
            
            return {
                "sentences": sentences,
                "paragraphs": paragraphs,
                "avg_sentence_length": len(data) / float(max(1, sentences))
            }
        
        elif isinstance(data, dict):
            # Analyze dictionary structure
            return {
                "keys": len(data),
                "max_depth": self._calculate_dict_depth(data),
                "key_pattern": self._detect_key_pattern(data)
            }
        
        elif isinstance(data, list):
            # Analyze list structure
            return {
                "length": len(data),
                "homogeneous": len(set(type(x).__name__ for x in data)) == 1 if data else True,
                "sorted": self._is_sorted(data)
            }
        
        return {"structure": "atomic"}
    
    def _calculate_dict_depth(self, data: Dict[str, Any], current_depth: int = 1) -> int:
        """Calculate the maximum depth of a nested dictionary.
        
        Args:
            data: Dictionary to analyze
            current_depth: Current depth level
            
        Returns:
            Maximum nesting depth
        """
        if not isinstance(data, dict) or not data:
            return current_depth
        
        max_depth = current_depth
        for value in data.values():
            if isinstance(value, dict):
                depth = self._calculate_dict_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _detect_key_pattern(self, data: Dict[str, Any]) -> str:
        """Detect patterns in dictionary keys.
        
        Args:
            data: Dictionary to analyze
            
        Returns:
            Detected pattern description
        """
        if not data:
            return "empty"
        
        keys = list(data.keys())
        
        # Check if all keys are numeric
        if all(isinstance(k, (int, float)) or (isinstance(k, str) and k.isdigit()) for k in keys):
            return "numeric"
        
        # Check if all keys are strings
        if all(isinstance(k, str) for k in keys):
            # Check if all keys follow camelCase
            if all(re.match(r'^[a-z]+([A-Z][a-z0-9]*)*$', k) for k in keys): # Adjusted regex
                return "camelCase"
            
            # Check if all keys follow snake_case
            if all(re.match(r'^[a-z0-9]+(_[a-z0-9]+)*$', k) for k in keys): # Adjusted regex
                return "snake_case"
            
            # Check if all keys follow kebab-case
            if all(re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', k) for k in keys): # Adjusted regex
                return "kebab-case"
        
        return "mixed"
    
    def _is_sorted(self, data: List[Any]) -> bool:
        """Check if a list is sorted.
        
        Args:
            data: List to check
            
        Returns:
            True if the list is sorted, False otherwise
        """
        if not data or len(data) < 2:
            return True
        
        # Check if all items are comparable
        try:
            # Check for ascending order
            is_ascending = all(data[i] <= data[i+1] for i in range(len(data)-1))
            if is_ascending:
                return True
            
            # Check for descending order
            is_descending = all(data[i] >= data[i+1] for i in range(len(data)-1))
            return is_descending
        except TypeError:
            # Items are not comparable
            return False
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of keywords
        """
        # This is a simplified implementation for demonstration
        # In a real system, this would use NLP techniques
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        if not words: return []
        word_counts = {}
        
        for word in words:
            if word not in word_counts:
                word_counts[word] = 0
            word_counts[word] += 1
        
        # Get top keywords by frequency
        return sorted(word_counts.keys(), key=lambda w: word_counts[w], reverse=True)[:10]
    
    def _categorize_list_items(self, items: List[Any]) -> Dict[str, int]:
        """Categorize items in a list by type.
        
        Args:
            items: List to categorize
            
        Returns:
            Dictionary mapping types to counts
        """
        categories = {}
        
        for item in items:
            item_type = type(item).__name__
            if item_type not in categories:
                categories[item_type] = 0
            categories[item_type] += 1
        
        return categories
    
    def _analyze_sequence(self, items: List[Any]) -> Dict[str, Any]:
        """Analyze a sequence of items.
        
        Args:
            items: Sequence to analyze
            
        Returns:
            Sequence analysis
        """
        if not items:
            return {"type": "empty"}
        
        # Check if all items are of the same type
        item_types = set(type(x).__name__ for x in items)
        
        if len(item_types) == 1:
            # Homogeneous sequence
            item_type = next(iter(item_types))
            
            if item_type == "int" or item_type == "float":
                # Numeric sequence
                if len(items) < 2:
                    return {"type": "numeric_short", "min": items[0], "max": items[0], "mean": items[0], "is_sorted": True}

                diffs = [items[i+1] - items[i] for i in range(len(items)-1)]
                
                if all(abs(d - diffs[0]) < 1e-9 for d in diffs): # Check for floating point precision
                    # Arithmetic sequence
                    return {
                        "type": "arithmetic",
                        "common_difference": diffs[0],
                        "first_term": items[0],
                        "formula": f"a_n = {items[0]} + (n-1) * {diffs[0]}"
                    }
                
                # Check for geometric sequence
                if all(items[i] != 0 for i in range(len(items))): # Avoid division by zero
                    ratios = [items[i+1] / float(items[i]) for i in range(len(items)-1)] # Ensure float division
                    if all(abs(r - ratios[0]) < 1e-9 for r in ratios): # Check for floating point precision
                        # Geometric sequence
                        return {
                            "type": "geometric",
                            "common_ratio": ratios[0],
                            "first_term": items[0],
                            "formula": f"a_n = {items[0]} * {ratios[0]}^(n-1)"
                        }
                
                # Other numeric sequence
                return {
                    "type": "numeric",
                    "min": min(items),
                    "max": max(items),
                    "mean": sum(items) / float(len(items)),
                    "is_sorted": self._is_sorted(items)
                }
            
            elif item_type == "str":
                # String sequence
                return {
                    "type": "string",
                    "min_length": min(len(s) for s in items) if items else 0,
                    "max_length": max(len(s) for s in items) if items else 0,
                    "avg_length": sum(len(s) for s in items) / float(len(items)) if items else 0,
                    "alphabetical": self._is_sorted(items)
                }
        
        # Heterogeneous sequence
        return {
            "type": "mixed",
            "type_distribution": {t: sum(1 for item in items if type(item).__name__ == t) for t in item_types}
        }
    
    def _validate_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a dictionary against common patterns.
        
        Args:
            data: Dictionary to validate
            
        Returns:
            Validation results
        """
        validation = {
            "has_required_keys": True,
            "type_consistency": True,
            "issues": []
        }
        
        # This is a simplified implementation for demonstration
        # In a real system, this would check against a schema
        
        # Check for empty dictionary
        if not data:
            validation["issues"].append("Empty dictionary")
            return validation
        
        # Check for common patterns based on keys
        keys = set(data.keys())
        
        # Check if this looks like a user object
        if keys.issuperset({"id", "name"}) or keys.issuperset({"user_id", "username"}):
            # Validate as user object
            if "id" in keys and not isinstance(data["id"], (int, str)):
                validation["type_consistency"] = False
                validation["issues"].append("User ID should be integer or string")
            
            if "name" in keys and not isinstance(data["name"], str):
                validation["type_consistency"] = False
                validation["issues"].append("User name should be string")
        
        # Check if this looks like a configuration object
        elif "config" in keys or "settings" in keys or keys.issuperset({"enabled", "version"}):
            # Validate as configuration object
            if "version" in keys and not isinstance(data["version"], (int, str, float)):
                validation["type_consistency"] = False
                validation["issues"].append("Version should be number or string")
            
            if "enabled" in keys and not isinstance(data["enabled"], bool):
                validation["type_consistency"] = False
                validation["issues"].append("Enabled flag should be boolean")
        
        return validation


class RightHemisphere(Hemisphere):
    """Right hemisphere implementation focusing on intuitive, creative processing."""
    
    def __init__(self, name: str = "right_hemisphere"):
        """Initialize a new right hemisphere.
        
        Args:
            name: Name for this hemisphere
        """
        super().__init__(HemisphereType.RIGHT, name)
        
        # Define intuitive processing patterns
        self._patterns = {
            # Symbolic patterns for token efficiency
            "[[ASSOCIATE]]": self._associate_concepts,
            "[[VISUALIZE]]": self._visualize_data,
            "[[SYNTHESIZE]]": self._synthesize_ideas,
            "[[INTUIT]]": self._intuit_patterns,
            "[[CREATE]]": self._creative_transform
        }
    
    def process(self, task: Task) -> Any:
        """Process a task using intuitive, creative methods.
        
        Args:
            task: The task to process
            
        Returns:
            Intuitive processing result
        """
        if not self._active:
            logger.warning(f"Attempted to process task on inactive hemisphere {self.name}")
            return None
        
        # Track processing metrics
        start_time = time.time()
        
        try:
            # Determine the processing approach based on task data
            data = task.data
            result = None
            
            # Check if this is a symbolic task
            if isinstance(data, str):
                # Look for symbolic patterns
                for pattern, handler in self._patterns.items():
                    if pattern in data:
                        # Extract the actual data to process
                        actual_data = data.replace(pattern, "").strip()
                        result = handler(actual_data)
                        break
            
            # If no symbolic pattern matched or data isn't a string,
            # use default intuitive processing
            if result is None:
                result = self._default_process(data)
            
            # Update task processing metrics
            with self._lock:
                self._tasks_processed += 1
                self._processing_time += (time.time() - start_time)
            
            return result
            
        except Exception as e:
            # Handle processing errors
            with self._lock:
                self._errors += 1
            
            logger.error(f"Error in {self.name} processing: {e}")
            return {"error": str(e), "partial_result": None}
    
    def _default_process(self, data: Any) -> Any:
        """Default processing method for the right hemisphere.
        
        Args:
            data: Data to process
            
        Returns:
            Processed result
        """
        # For string data, perform intuitive text processing
        if isinstance(data, str):
            return {
                "sentiment": self._analyze_sentiment(data),
                "themes": self._extract_themes(data),
                "associations": self._generate_associations(data),
                "imagery": self._extract_imagery(data)
            }
        
        # For dictionary data, find patterns and connections
        elif isinstance(data, dict):
            return {
                "patterns": self._find_patterns(data),
                "connections": self._find_connections(data),
                "creative_view": self._reframe_data(data)
            }
        
        # For list data, find groupings and relationships
        elif isinstance(data, list):
            return {
                "groupings": self._find_natural_groupings(data),
                "relationships": self._find_relationships(data),
                "creative_arrangement": self._arrange_creatively(data)
            }
        
        # For other data types, return intuitive impression
        return {
            "impression": self._generate_impression(data),
            "intuitive_value": str(data)
        }
    
    def _associate_concepts(self, data: Any) -> Dict[str, Any]:
        """Generate conceptual associations.
        
        Args:
            data: Data to process
            
        Returns:
            Associated concepts
        """
        # This is a simplified implementation for demonstration
        if isinstance(data, str):
            return {
                "associations": self._generate_associations(data),
                "related_concepts": self._find_related_concepts(data)
            }
        
        return {"associations": self._generate_impression(data)}
    
    def _visualize_data(self, data: Any) -> Dict[str, Any]:
        """Create visual representations of data.
        
        Args:
            data: Data to visualize
            
        Returns:
            Visual representation description
        """
        # This is a simplified implementation for demonstration
        # In a real system, this might generate actual visualizations
        if isinstance(data, str):
            return {
                "imagery": self._extract_imagery(data),
                "visual_metaphors": self._generate_metaphors(data)
            }
        
        elif isinstance(data, dict):
            return {
                "structure": "network",
                "nodes": len(data),
                "visual_mapping": self._map_to_visual_space(data)
            }
        
        elif isinstance(data, list):
            return {
                "structure": "sequence",
                "length": len(data),
                "visual_mapping": self._arrange_visually(data)
            }
        
        return {"visual_impression": self._generate_impression(data)}
    
    def _synthesize_ideas(self, data: Any) -> Dict[str, Any]:
        """Synthesize new ideas from existing data.
        
        Args:
            data: Data to synthesize from
            
        Returns:
            Synthesized ideas
        """
        # This is a simplified implementation for demonstration
        if isinstance(data, str):
            return {
                "synthesis": self._generate_synthesis(data),
                "new_perspectives": self._generate_perspectives(data)
            }
        
        return {"synthesis": self._generate_impression(data)}
    
    def _intuit_patterns(self, data: Any) -> Dict[str, Any]:
        """Intuit patterns and relationships in data.
        
        Args:
            data: Data to analyze
            
        Returns:
            Intuited patterns
        """
        # This is a simplified implementation for demonstration
        if isinstance(data, dict):
            return self._find_patterns(data)
        
        elif isinstance(data, list):
            return self._find_relationships(data)
        
        elif isinstance(data, str):
            return {
                "patterns": self._find_text_patterns(data),
                "intuitive_meaning": self._intuit_meaning(data)
            }
        
        return {"intuition": self._generate_impression(data)}
    
    def _creative_transform(self, data: Any) -> Any:
        """Transform data creatively.
        
        Args:
            data: Data to transform
            
        Returns:
            Transformed data
        """
        # This is a simplified implementation for demonstration
        if isinstance(data, str):
            return {
                "transformation": self._transform_text(data),
                "creative_variations": self._generate_variations(data)
            }
        
        elif isinstance(data, dict):
            return self._reframe_data(data)
        
        elif isinstance(data, list):
            return self._arrange_creatively(data)
        
        return {"creative_view": self._generate_impression(data)}
    
    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze the sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment analysis
        """
        # This is a simplified implementation for demonstration
        # In a real system, this would use NLP techniques
        
        # Simple keyword-based sentiment analysis
        positive_words = {"good", "great", "excellent", "wonderful", "amazing", "love", "like", "happy", "joy", "positive"}
        negative_words = {"bad", "terrible", "awful", "horrible", "hate", "dislike", "sad", "angry", "negative", "worst"}
        
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        total_words = len(words)
        
        if total_words == 0:
            return {"positive": 0.0, "negative": 0.0, "neutral": 1.0, "overall": 0.0}
        
        positive_score = positive_count / float(total_words)
        negative_score = negative_count / float(total_words)
        neutral_score = 1.0 - positive_score - negative_score
        
        return {
            "positive": positive_score,
            "negative": negative_score,
            "neutral": neutral_score,
            "overall": positive_score - negative_score
        }
    
    def _extract_themes(self, text: str) -> List[str]:
        """Extract thematic elements from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of themes
        """
        # This is a simplified implementation for demonstration
        # In a real system, this would use NLP techniques
        
        # Theme categories with associated keywords
        theme_keywords = {
            "nature": {"nature", "tree", "forest", "river", "mountain", "ocean", "animal", "plant", "earth", "sky"},
            "technology": {"technology", "computer", "digital", "software", "hardware", "internet", "code", "program", "device", "tech"},
            "emotion": {"emotion", "feel", "feeling", "love", "hate", "joy", "sadness", "anger", "fear", "happiness"},
            "society": {"society", "community", "people", "social", "culture", "politics", "government", "law", "policy", "nation"},
            "knowledge": {"knowledge", "learn", "education", "school", "study", "research", "science", "understand", "wisdom", "information"}
        }
        
        words = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
        
        # Find themes based on keyword matches
        themes = []
        for theme, keywords in theme_keywords.items():
            if keywords.intersection(words):
                themes.append(theme)
        
        return themes
    
    def _generate_associations(self, text: str) -> List[str]:
        """Generate word associations from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of associated words
        """
        # This is a simplified implementation for demonstration
        # In a real system, this would use word embeddings or a knowledge graph
        
        # Simple word association dictionary
        associations = {
            "water": ["ocean", "river", "lake", "flow", "drink", "blue", "clear"],
            "fire": ["hot", "burn", "flame", "heat", "red", "orange", "passion"],
            "earth": ["ground", "soil", "planet", "nature", "green", "life", "solid"],
            "air": ["wind", "breath", "sky", "invisible", "light", "free", "flow"],
            "love": ["heart", "emotion", "care", "affection", "relationship", "passion", "warm"],
            "time": ["clock", "hour", "minute", "second", "past", "future", "present"],
            "mind": ["brain", "thought", "idea", "intelligence", "consciousness", "thinking", "memory"],
            "body": ["physical", "health", "strength", "movement", "flesh", "form", "vessel"]
        }
        
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        result = []
        
        for word in words:
            if word in associations:
                # Add some of the associations
                result.extend(associations[word][:3])
        
        # Remove duplicates and limit result size
        return list(set(result))[:10]
    
    def _extract_imagery(self, text: str) -> List[Dict[str, Any]]:
        """Extract visual imagery from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of imagery descriptions
        """
        # This is a simplified implementation for demonstration
        # In a real system, this would use more sophisticated NLP
        
        # Look for color words
        colors = ["red", "blue", "green", "yellow", "orange", "purple", "black", "white", "gray", "brown"]
        color_matches = [color for color in colors if re.search(r'\b' + color + r'\b', text.lower())]
        
        # Look for shape words
        shapes = ["circle", "square", "triangle", "rectangle", "oval", "sphere", "cube", "pyramid", "line", "curve"]
        shape_matches = [shape for shape in shapes if re.search(r'\b' + shape + r'\b', text.lower())]
        
        # Look for nature imagery
        nature = ["mountain", "river", "ocean", "forest", "tree", "flower", "sky", "cloud", "sun", "moon", "star"]
        nature_matches = [n for n in nature if re.search(r'\b' + n + r'\b', text.lower())]
        
        # Compile imagery
        imagery = []
        
        if color_matches:
            imagery.append({"type": "color", "elements": color_matches})
        
        if shape_matches:
            imagery.append({"type": "shape", "elements": shape_matches})
        
        if nature_matches:
            imagery.append({"type": "nature", "elements": nature_matches})
        
        return imagery
    
    def _find_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Find patterns in dictionary data.
        
        Args:
            data: Dictionary to analyze
            
        Returns:
            Detected patterns
        """
        patterns = {}
        
        # Look for naming patterns
        key_pattern = self._detect_naming_pattern(data.keys())
        if key_pattern:
            patterns["naming"] = key_pattern
        
        # Look for value patterns
        value_types = [type(v).__name__ for v in data.values()]
        if value_types and len(set(value_types)) < len(value_types) / 2.0: # Ensure float division
            # There's a dominant type
            dominant_type = max(set(value_types), key=value_types.count)
            patterns["values"] = f"Primarily {dominant_type} values"
        
        # Look for structural patterns
        nested_keys = [k for k, v in data.items() if isinstance(v, (dict, list))]
        if nested_keys:
            patterns["structure"] = f"Nested data under keys: {', '.join(nested_keys[:3])}"
        
        return patterns
    
    def _detect_naming_pattern(self, keys) -> Optional[str]: # Added Optional return type
        """Detect naming patterns in keys.
        
        Args:
            keys: Keys to analyze
            
        Returns:
            Detected pattern description or None
        """
        keys = list(keys)
        if not keys: return None # Handle empty keys
        
        # Check for numeric sequence
        if all(isinstance(k, (int, float)) or (isinstance(k, str) and k.isdigit()) for k in keys):
            return "Numeric sequence"
        
        # Check for prefixes
        if all(isinstance(k, str) for k in keys):
            # Find common prefixes
            prefixes = {}
            for key in keys:
                for i in range(1, len(key) // 2 + 1):
                    prefix = key[:i]
                    if prefix not in prefixes:
                        prefixes[prefix] = 0
                    prefixes[prefix] += 1
            
            # Find most common prefix with significant usage
            common_prefixes = [p for p, count in prefixes.items() if count > len(keys) / 2.0] # Ensure float division
            if common_prefixes:
                return f"Common prefix: {max(common_prefixes, key=len)}"
        
        return None
    
    def _find_connections(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find connections between elements in a dictionary.
        
        Args:
            data: Dictionary to analyze
            
        Returns:
            List of connections
        """
        connections = []
        
        # This is a simplified implementation for demonstration
        # In a real system, this would use more sophisticated analysis
        
        # Look for keys with similar values
        value_groups = {}
        for k, v in data.items():
            try:
                value_str = str(v) # Ensure value is string for grouping
            except:
                continue # Skip unstringable values
            if value_str not in value_groups:
                value_groups[value_str] = []
            value_groups[value_str].append(k)
        
        # Report groups with multiple keys
        for value, keys in value_groups.items():
            if len(keys) > 1:
                connections.append({
                    "type": "shared_value",
                    "keys": keys,
                    "value": value[:50] + "..." if len(value) > 50 else value
                })
        
        # Look for complementary keys
        complementary_pairs = [
            ("start", "end"), ("begin", "end"), ("first", "last"),
            ("min", "max"), ("low", "high"), ("input", "output"),
            ("source", "target"), ("from", "to"), ("before", "after")
        ]
        
        for pair in complementary_pairs:
            if pair[0] in data and pair[1] in data:
                connections.append({
                    "type": "complementary_pair",
                    "keys": list(pair),
                    "values": [str(data[pair[0]]), str(data[pair[1]])]
                })
        
        return connections
    
    def _reframe_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Reframe dictionary data from a creative perspective.
        
        Args:
            data: Dictionary to reframe
            
        Returns:
            Reframed view of the data
        """
        # This is a simplified implementation for demonstration
        # In a real system, this would use more sophisticated techniques
        
        reframed = {}
        
        # Group by value type
        by_type = {}
        for k, v in data.items():
            v_type = type(v).__name__
            if v_type not in by_type:
                by_type[v_type] = {}
            by_type[v_type][k] = v
        
        reframed["by_type"] = {t: list(keys.keys()) for t, keys in by_type.items()}
        
        # Group by "concept" (simplified)
        concepts = {}
        for k, v in data.items():
            # Assign a concept based on key name
            concept = "unknown"
            
            if "name" in k.lower() or "title" in k.lower() or "label" in k.lower():
                concept = "identity"
            elif "time" in k.lower() or "date" in k.lower() or "when" in k.lower():
                concept = "temporal"
            elif "location" in k.lower() or "place" in k.lower() or "where" in k.lower():
                concept = "spatial"
            elif "count" in k.lower() or "number" in k.lower() or "quantity" in k.lower():
                concept = "quantitative"
            elif "status" in k.lower() or "state" in k.lower() or "condition" in k.lower():
                concept = "state"
            
            if concept not in concepts:
                concepts[concept] = {}
            concepts[concept][k] = v
        
        reframed["by_concept"] = {c: list(keys.keys()) for c, keys in concepts.items() if c != "unknown"}
        
        return reframed
    
    def _find_natural_groupings(self, items: List[Any]) -> List[Dict[str, Any]]:
        """Find natural groupings in a list of items.
        
        Args:
            items: List to analyze
            
        Returns:
            List of groupings
        """
        if not items:
            return []
        
        groupings = []
        
        # Group by type
        type_groups = {}
        for item in items:
            item_type = type(item).__name__
            if item_type not in type_groups:
                type_groups[item_type] = []
            type_groups[item_type].append(item)
        
        if len(type_groups) > 1:
            groupings.append({
                "criterion": "type",
                "groups": {t: len(group_items) for t, group_items in type_groups.items()} # Fixed variable name
            })
        
        # For string items, group by first letter
        if "str" in type_groups and len(type_groups["str"]) > 3:
            first_letter_groups = {}
            for item in type_groups["str"]:
                if not item:
                    continue
                first_letter = item[0].lower()
                if first_letter not in first_letter_groups:
                    first_letter_groups[first_letter] = []
                first_letter_groups[first_letter].append(item)
            
            if len(first_letter_groups) > 1:
                groupings.append({
                    "criterion": "first_letter",
                    "groups": {letter: len(group_items) for letter, group_items in first_letter_groups.items()} # Fixed variable name
                })
        
        # For numeric items, group by range
        numeric_types = {"int", "float"}
        numeric_items = []
        for t in numeric_types:
            if t in type_groups:
                numeric_items.extend(type_groups[t])
        
        if numeric_items:
            # Determine range groups
            min_val = min(numeric_items)
            max_val = max(numeric_items)
            if max_val == min_val: # Handle case where all numbers are the same
                range_groups = {f"{min_val:.1f}": numeric_items}
            else:
                range_size = (max_val - min_val) / 3.0  # 3 groups, ensure float division
                
                range_groups = {
                    f"{min_val:.1f}-{min_val+range_size:.1f}": [],
                    f"{min_val+range_size:.1f}-{min_val+2*range_size:.1f}": [],
                    f"{min_val+2*range_size:.1f}-{max_val:.1f}": []
                }
                
                for item in numeric_items:
                    if item < min_val + range_size:
                        range_groups[f"{min_val:.1f}-{min_val+range_size:.1f}"].append(item)
                    elif item < min_val + 2 * range_size:
                        range_groups[f"{min_val+range_size:.1f}-{min_val+2*range_size:.1f}"].append(item)
                    else:
                        range_groups[f"{min_val+2*range_size:.1f}-{max_val:.1f}"].append(item)
            
            groupings.append({
                "criterion": "value_range",
                "groups": {r: len(group_items) for r, group_items in range_groups.items()} # Fixed variable name
            })
        
        return groupings
    
    def _find_relationships(self, items: List[Any]) -> List[Dict[str, Any]]:
        """Find relationships between items in a list.
        
        Args:
            items: List to analyze
            
        Returns:
            List of relationships
        """
        if not items or len(items) < 2:
            return []
        
        relationships = []
        
        # Check for sequence relationships
        if all(isinstance(item, (int, float)) for item in items):
            # Check for arithmetic sequence
            diffs = [items[i+1] - items[i] for i in range(len(items)-1)]
            if all(abs(d - diffs[0]) < 1e-9 for d in diffs): # Check for floating point precision
                relationships.append({
                    "type": "arithmetic_sequence",
                    "difference": diffs[0]
                })
            
            # Check for geometric sequence
            if all(items[i] != 0 for i in range(len(items))): # Avoid division by zero
                ratios = [items[i+1] / float(items[i]) for i in range(len(items)-1)] # Ensure float division
                if all(abs(r - ratios[0]) < 1e-9 for r in ratios): # Check for floating point precision
                    relationships.append({
                        "type": "geometric_sequence",
                        "ratio": ratios[0]
                    })
        
        # Check for pattern relationships in strings
        if all(isinstance(item, str) for item in items):
            # Check for common prefix
            if len(items) > 1:
                prefix = os.path.commonprefix(items)
                if prefix and len(prefix) > 1:
                    relationships.append({
                        "type": "common_prefix",
                        "prefix": prefix
                    })
            
            # Check for common suffix
            if len(items) > 1:
                # Reverse strings to find common suffix
                reversed_items = [item[::-1] for item in items]
                suffix = os.path.commonprefix(reversed_items)
                if suffix and len(suffix) > 1:
                    relationships.append({
                        "type": "common_suffix",
                        "suffix": suffix[::-1]  # Reverse back
                    })
        
        return relationships
    
    def _arrange_creatively(self, items: List[Any]) -> Dict[str, Any]:
        """Arrange items in a creative way.
        
        Args:
            items: Items to arrange
            
        Returns:
            Creative arrangement
        """
        if not items:
            return {"arrangement": "empty"}
        
        # This is a simplified implementation for demonstration
        # In a real system, this would use more sophisticated techniques
        
        # Create a "constellation" arrangement
        if len(items) > 2:
            # Select a random subset as "key stars"
            key_indices = random.sample(range(len(items)), min(5, len(items)))
            key_items = [items[i] for i in key_indices]
            
            return {
                "arrangement": "constellation",
                "key_points": key_items,
                "connections": [
                    {"from": i % len(key_items), "to": (i + 1) % len(key_items)}
                    for i in range(len(key_items))
                ]
            }
        
        # For two items, create a "duality" arrangement
        elif len(items) == 2:
            return {
                "arrangement": "duality",
                "poles": items,
                "tension": "balanced"
            }
        
        # For one item, create a "singularity" arrangement
        else:
            return {
                "arrangement": "singularity",
                "focus": items[0],
                "intensity": "high"
            }
    
    def _arrange_visually(self, items: List[Any]) -> Dict[str, Any]:
        """Arrange items in a visual space.
        
        Args:
            items: Items to arrange
            
        Returns:
            Visual arrangement description
        """
        # This is a simplified implementation for demonstration
        # In a real system, this might generate actual visual coordinates
        
        if not items:
            return {"visual": "empty"}
        
        # Choose a visual arrangement based on the number of items
        if len(items) <= 3:
            return {
                "visual": "triangle",
                "points": len(items),
                "balance": "symmetric"
            }
        elif len(items) <= 5:
            return {
                "visual": "star",
                "points": len(items),
                "balance": "radial"
            }
        elif len(items) <= 8:
            return {
                "visual": "circle",
                "points": len(items),
                "balance": "distributed"
            }
        else:
            return {
                "visual": "cluster",
                "points": len(items),
                "balance": "organic"
            }
    
    def _map_to_visual_space(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map dictionary data to a visual space.
        
        Args:
            data: Dictionary to map
            
        Returns:
            Visual mapping description
        """
        # This is a simplified implementation for demonstration
        # In a real system, this might generate actual visual coordinates
        
        if not data:
            return {"visual": "empty"}
        
        # Choose a visual mapping based on the structure
        if any(isinstance(v, dict) for v in data.values()):
            return {
                "visual": "nested_clusters",
                "primary_nodes": len(data),
                "has_nesting": True
            }
        elif any(isinstance(v, list) for v in data.values()):
            return {
                "visual": "hub_and_spokes",
                "hubs": len(data),
                "has_lists": True
            }
        else:
            return {
                "visual": "network",
                "nodes": len(data),
                "has_complex_structure": False
            }
    
    def _find_related_concepts(self, text: str) -> List[str]:
        """Find concepts related to the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of related concepts
        """
        # This is a simplified implementation for demonstration
        # In a real system, this would use a knowledge graph or word embeddings
        
        # Extract key words
        words = set(re.findall(r'\b[a-zA-Z]{4,}\b', text.lower()))
        
        # Simple concept mapping
        concept_map = {
            "technology": {"computer", "software", "digital", "electronic", "internet", "online", "virtual", "cyber", "data", "information"},
            "nature": {"tree", "forest", "river", "mountain", "ocean", "animal", "plant", "earth", "natural", "environment"},
            "art": {"creative", "painting", "music", "sculpture", "design", "artistic", "expression", "aesthetic", "beauty", "imagination"},
            "science": {"research", "experiment", "theory", "hypothesis", "laboratory", "scientific", "discovery", "observation", "analysis", "evidence"},
            "philosophy": {"thinking", "thought", "concept", "idea", "meaning", "existence", "reality", "knowledge", "wisdom", "truth"},
            "emotion": {"feeling", "emotion", "happiness", "sadness", "anger", "fear", "love", "hate", "passion", "desire"}
        }
        
        # Find matching concepts
        related_concepts = []
        for concept, concept_words in concept_map.items():
            if words.intersection(concept_words):
                related_concepts.append(concept)
        
        return related_concepts
    
    def _generate_metaphors(self, text: str) -> List[str]:
        """Generate metaphors related to the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of metaphors
        """
        # This is a simplified implementation for demonstration
        # In a real system, this would use more sophisticated NLP
        
        # Extract themes
        themes = self._extract_themes(text)
        
        # Simple metaphor templates
        metaphor_templates = {
            "nature": [
                "A forest of {concepts}",
                "An ocean of {concepts}",
                "Mountains of {concepts}",
                "Seeds of {concepts}"
            ],
            "technology": [
                "A network of {concepts}",
                "Digital {concepts}",
                "The code behind {concepts}",
                "A virtual landscape of {concepts}"
            ],
            "emotion": [
                "A storm of {concepts}",
                "The heart of {concepts}",
                "A flame of {concepts}",
                "The pulse of {concepts}"
            ],
            "society": [
                "A tapestry of {concepts}",
                "The marketplace of {concepts}",
                "A community of {concepts}",
                "The architecture of {concepts}"
            ],
            "knowledge": [
                "A library of {concepts}",
                "The map of {concepts}",
                "A journey through {concepts}",
                "The light of {concepts}"
            ]
        }
        
        # Extract key words for concepts
        words = re.findall(r'\b[a-zA-Z]{5,}\b', text.lower())
        key_words = list(set(words))[:3]  # Limit to 3 unique words
        
        # Generate metaphors based on themes
        metaphors = []
        for theme in themes:
            if theme in metaphor_templates and key_words:
                template = random.choice(metaphor_templates[theme])
                concepts = " and ".join(key_words)
                metaphors.append(template.format(concepts=concepts))
        
        # If no themes matched, use a generic metaphor
        if not metaphors and key_words:
            generic_templates = [
                "A journey through {concepts}",
                "The landscape of {concepts}",
                "A constellation of {concepts}",
                "The rhythm of {concepts}"
            ]
            template = random.choice(generic_templates)
            concepts = " and ".join(key_words)
            metaphors.append(template.format(concepts=concepts))
        
        return metaphors
    
    def _generate_synthesis(self, text: str) -> Dict[str, Any]:
        """Generate a synthesis of ideas from text.
        
        Args:
            text: Text to synthesize from
            
        Returns:
            Synthesis results
        """
        # This is a simplified implementation for demonstration
        # In a real system, this would use more sophisticated NLP
        
        # Extract key elements
        themes = self._extract_themes(text)
        sentiment = self._analyze_sentiment(text)
        
        # Create a synthesis
        synthesis = {
            "core_themes": themes,
            "emotional_tone": "positive" if sentiment["overall"] > 0 else "negative" if sentiment["overall"] < 0 else "neutral",
            "synthesis": self._generate_synthetic_statement(text, themes, sentiment)
        }
        
        return synthesis
    
    def _generate_synthetic_statement(self, text: str, themes: List[str], sentiment: Dict[str, float]) -> str:
        """Generate a synthetic statement from text analysis.
        
        Args:
            text: Original text
            themes: Extracted themes
            sentiment: Sentiment analysis
            
        Returns:
            Synthetic statement
        """
        # This is a simplified implementation for demonstration
        # In a real system, this would use more sophisticated NLP
        
        # Extract a few key words
        words = re.findall(r'\b[a-zA-Z]{5,}\b', text.lower())
        key_words = list(set(words))[:5]  # Limit to 5 unique words
        
        # Determine tone
        tone = "positive" if sentiment["overall"] > 0.1 else "negative" if sentiment["overall"] < -0.1 else "neutral"
        
        # Generate a statement based on themes and tone
        if themes and key_words:
            theme_str = " and ".join(themes[:2])  # Limit to 2 themes
            words_str = ", ".join(key_words)
            
            if tone == "positive":
                return f"A harmonious integration of {theme_str} through the lens of {words_str}"
            elif tone == "negative":
                return f"A challenging interplay of {theme_str} revealing tensions in {words_str}"
            else:
                return f"A balanced perspective on {theme_str} exploring the nuances of {words_str}"
        
        # Fallback if no themes or key words
        return "A synthesis of multiple perspectives and ideas"
    
    def _generate_perspectives(self, text: str) -> List[str]:
        """Generate alternative perspectives on the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of alternative perspectives
        """
        # This is a simplified implementation for demonstration
        # In a real system, this would use more sophisticated NLP
        
        perspectives = []
        
        # Generate a few different perspectives
        perspectives.append("From a holistic viewpoint: " + self._reframe_holistically(text))
        perspectives.append("From a contrasting angle: " + self._reframe_contrastingly(text))
        perspectives.append("From a metaphorical lens: " + self._reframe_metaphorically(text))
        
        return perspectives
    
    def _reframe_holistically(self, text: str) -> str:
        """Reframe text from a holistic perspective.
        
        Args:
            text: Text to reframe
            
        Returns:
            Reframed text
        """
        # This is a simplified implementation for demonstration
        return "Considering the interconnected nature of all elements involved"
    
    def _reframe_contrastingly(self, text: str) -> str:
        """Reframe text from a contrasting perspective.
        
        Args:
            text: Text to reframe
            
        Returns:
            Reframed text
        """
        # This is a simplified implementation for demonstration
        return "Examining the opposite viewpoint reveals alternative possibilities"
    
    def _reframe_metaphorically(self, text: str) -> str:
        """Reframe text using metaphor.
        
        Args:
            text: Text to reframe
            
        Returns:
            Reframed text
        """
        # This is a simplified implementation for demonstration
        metaphors = self._generate_metaphors(text)
        if metaphors:
            return metaphors[0]
        return "Viewing this as a journey with multiple paths"
    
    def _find_text_patterns(self, text: str) -> Dict[str, Any]:
        """Find patterns in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected patterns
        """
        patterns = {}
        
        # Look for repetition
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        if not words: return patterns # Handle empty text
        word_counts = {}
        
        for word in words:
            if word not in word_counts:
                word_counts[word] = 0
            word_counts[word] += 1
        
        repeated_words = [word for word, count in word_counts.items() if count > 1]
        if repeated_words:
            patterns["repetition"] = repeated_words[:5]  # Limit to 5
        
        # Look for rhythm patterns
        sentences = re.split(r'[.!?]+', text)
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        
        if sentence_lengths:
            avg_length = sum(sentence_lengths) / float(len(sentence_lengths))
            variation = sum(abs(length - avg_length) for length in sentence_lengths) / float(len(sentence_lengths))
            
            if variation < 2:
                patterns["rhythm"] = "consistent"
            elif any(abs(sentence_lengths[i] - sentence_lengths[i-1]) < 2 for i in range(1, len(sentence_lengths))):
                patterns["rhythm"] = "alternating"
            else:
                patterns["rhythm"] = "varied"
        
        return patterns
    
    def _intuit_meaning(self, text: str) -> str:
        """Intuit the underlying meaning of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Intuited meaning
        """
        # This is a simplified implementation for demonstration
        # In a real system, this would use more sophisticated NLP
        
        # Combine themes and sentiment
        themes = self._extract_themes(text)
        sentiment = self._analyze_sentiment(text)
        
        # Generate an intuited meaning
        if themes:
            theme_str = " and ".join(themes[:2])  # Limit to 2 themes
            
            if sentiment["overall"] > 0.1:
                return f"An optimistic exploration of {theme_str}"
            elif sentiment["overall"] < -0.1:
                return f"A critical examination of challenges in {theme_str}"
            else:
                return f"A balanced consideration of {theme_str}"
        
        return "A nuanced perspective with multiple layers of meaning"
    
    def _transform_text(self, text: str) -> str:
        """Transform text creatively.
        
        Args:
            text: Text to transform
            
        Returns:
            Transformed text
        """
        # This is a simplified implementation for demonstration
        # In a real system, this would use more sophisticated NLP
        
        # Extract key words
        words = re.findall(r'\b[a-zA-Z]{5,}\b', text.lower())
        key_words = list(set(words))[:7]  # Limit to 7 unique words
        
        if not key_words:
            return "A creative transformation of the original"
        
        # Create a poetic transformation
        return "The essence distilled: " + " / ".join(key_words)
    
    def _generate_variations(self, text: str) -> List[str]:
        """Generate creative variations of text.
        
        Args:
            text: Text to vary
            
        Returns:
            List of variations
        """
        # This is a simplified implementation for demonstration
        # In a real system, this would use more sophisticated NLP
        
        variations = []
        
        # Generate a few variations
        variations.append("Poetic: " + self._transform_text(text))
        variations.append("Visual: " + self._describe_visually(text))
        variations.append("Emotional: " + self._emphasize_emotion(text))
        
        return variations
    
    def _describe_visually(self, text: str) -> str:
        """Describe text in visual terms.
        
        Args:
            text: Text to describe
            
        Returns:
            Visual description
        """
        # This is a simplified implementation for demonstration
        imagery = self._extract_imagery(text)
        
        if imagery:
            elements = []
            for img in imagery:
                if "elements" in img:
                    elements.extend(img["elements"])
            
            if elements:
                return "A canvas of " + ", ".join(elements[:5])
        
        return "A visual tapestry of interconnected elements"
    
    def _emphasize_emotion(self, text: str) -> str:
        """Emphasize emotional aspects of text.
        
        Args:
            text: Text to emphasize
            
        Returns:
            Emotionally emphasized text
        """
        # This is a simplified implementation for demonstration
        sentiment = self._analyze_sentiment(text)
        
        if sentiment["overall"] > 0.2:
            return "A heartfelt expression of joy and positivity"
        elif sentiment["overall"] > 0: # Check if overall exists
            return "A gentle warmth of positive feeling"
        elif sentiment["overall"] < -0.2:
            return "A profound depth of challenging emotion"
        elif sentiment["overall"] < 0: # Check if overall exists
            return "A subtle undercurrent of concern"
        else:
            return "A balanced emotional landscape, neither light nor dark"
    
    def _generate_impression(self, data: Any) -> str:
        """Generate an intuitive impression of data.
        
        Args:
            data: Data to analyze
            
        Returns:
            Intuitive impression
        """
        # This is a simplified implementation for demonstration
        # In a real system, this would use more sophisticated techniques
        
        # Generate different impressions based on data type
        if isinstance(data, str):
            return "A narrative with layers of meaning"
        elif isinstance(data, dict):
            return "A complex network of interconnected elements"
        elif isinstance(data, list):
            return "A sequence with an underlying pattern"
        elif isinstance(data, (int, float)):
            return "A singular point in a broader context"
        else:
            return "An entity with unique properties and potential"


class TwinFlame(Entity):
    """Bi-hemisphere parallel processing entity.
    
    The TwinFlame entity implements a dual-processing architecture inspired by
    the human brain's hemispheric specialization. It distributes tasks between
    logical (left) and intuitive (right) processing pathways, then merges the
    results for a more comprehensive solution.
    """
    
    def __init__(self, name: str = "TwinFlame", socketio=None):
        """Initialize a new TwinFlame entity.
        
        Args:
            name: Name of this TwinFlame instance
            socketio: Flask-SocketIO instance for emitting events
        """
        super().__init__(name, socketio)
        self.left_hemisphere = LeftHemisphere()
        self.right_hemisphere = RightHemisphere()
        self._processing_mode = ProcessingMode.PARALLEL
        self._task_queue: Dict[str, Task] = {} # Added type hint
        self._completed_tasks: Dict[str, Task] = {} # Added type hint
        self._lock = threading.RLock()
        self._worker_thread: Optional[threading.Thread] = None # Added type hint
        self._stop_worker = False
        logger.info(f"TwinFlame {name} initialized with both hemispheres")
    
    def activate(self) -> bool:
        """Activate the TwinFlame entity and both hemispheres.
        
        Returns:
            True if activation succeeded, False otherwise
        """
        result = super().activate()
        if result:
            self.left_hemisphere.activate()
            self.right_hemisphere.activate()
            self._start_worker()
            logger.info(f"TwinFlame {self.name} activated with both hemispheres")
        return result
    
    def deactivate(self) -> bool:
        """Deactivate the TwinFlame entity and both hemispheres.
        
        Returns:
            True if deactivation succeeded, False otherwise
        """
        self._stop_worker = True
        if self._worker_thread and self._worker_thread.is_alive(): # Check if thread is alive
            self._worker_thread.join(timeout=2.0)
        
        self.left_hemisphere.deactivate()
        self.right_hemisphere.deactivate()
        result = super().deactivate()
        logger.info(f"TwinFlame {self.name} deactivated")
        return result
    
    def _start_worker(self) -> None:
        """Start the background worker thread for task processing."""
        if self._worker_thread and self._worker_thread.is_alive():
            logger.warning(f"TwinFlame {self.name} worker thread already running.")
            return

        self._stop_worker = False
        self._worker_thread = threading.Thread(target=self._process_task_queue, daemon=True)
        self._worker_thread.start()
        logger.debug(f"TwinFlame {self.name} worker thread started")
    
    def _process_task_queue(self) -> None:
        """Process tasks in the queue in the background."""
        while not self._stop_worker and self.is_active():
            # Get the next task to process
            task_id: Optional[str] = None # Added type hint
            task: Optional[Task] = None # Added type hint
            
            with self._lock:
                # Find the highest priority task
                pending_tasks = [
                    (tid, t) for tid, t in self._task_queue.items()
                    if t.status == TaskStatus.PENDING
                ]
                
                if pending_tasks:
                    # Sort by priority (higher enum value = higher priority)
                    pending_tasks.sort(key=lambda x: x[1].priority.value, reverse=True)
                    task_id, task = pending_tasks[0]
                    task.status = TaskStatus.PROCESSING_LEFT # Initial status
                    task.started_at = time.time()
            
            if task and task_id: # Ensure task and task_id are not None
                try:
                    # Process with both hemispheres
                    self._process_task(task_id, task)
                except Exception as e:
                    logger.error(f"Error processing task {task_id}: {e}")
                    with self._lock:
                        task.status = TaskStatus.FAILED
                        task.error = str(e)
            
            # Sleep briefly to avoid consuming too much CPU
            time.sleep(0.1)
    
    def _process_task(self, task_id: str, task: Task) -> None:
        """Process a task with both hemispheres.
        
        Args:
            task_id: ID of the task to process
            task: Task to process
        """
        # Process with left hemisphere
        logger.debug(f"Processing task {task_id} with left hemisphere")
        left_result = self.left_hemisphere.process(task)
        
        with self._lock:
            task.left_result = left_result
            task.status = TaskStatus.PROCESSING_RIGHT # Update status
        
        # Process with right hemisphere
        logger.debug(f"Processing task {task_id} with right hemisphere")
        right_result = self.right_hemisphere.process(task)
        
        with self._lock:
            task.right_result = right_result
            # Status will be updated after merging
        
        # Merge results
        logger.debug(f"Merging results for task {task_id}")
        merged_result = self._merge_results(task, left_result, right_result)
        
        with self._lock:
            task.merged_result = merged_result
            task.status = TaskStatus.MERGED # Final status
            task.completed_at = time.time()
            
            # Move to completed tasks
            if task_id in self._task_queue: # Ensure task is still in queue before deleting
                self._completed_tasks[task_id] = task
                del self._task_queue[task_id]
        
        # Emit event if socketio is available
        if self.socketio:
            self.socketio.emit('twinflame_task_completed', {
                'task_id': task_id,
                'processing_time': (task.completed_at - task.started_at) if task.completed_at and task.started_at else None,
                'status': task.status.name
            })
        
        logger.info(f"Task {task_id} completed and merged")
    
    def _merge_results(self, task: Task, left_result: Any, right_result: Any) -> Any:
        """Merge results from both hemispheres.
        
        Args:
            task: The original task
            left_result: Result from left hemisphere
            right_result: Result from right hemisphere
            
        Returns:
            Merged result
        """
        # Check for errors in either result
        left_error = isinstance(left_result, dict) and "error" in left_result
        right_error = isinstance(right_result, dict) and "error" in right_result
        
        if left_error and right_error:
            # Both hemispheres had errors
            return {
                "status": "error",
                "left_error": left_result.get("error"),
                "right_error": right_result.get("error"),
                "message": "Both hemispheres encountered errors"
            }
        
        elif left_error:
            # Left hemisphere had an error, use right result
            return {
                "status": "partial",
                "result": right_result,
                "hemisphere": "right",
                "message": f"Using right hemisphere result due to left error: {left_result.get('error')}"
            }
        
        elif right_error:
            # Right hemisphere had an error, use left result
            return {
                "status": "partial",
                "result": left_result,
                "hemisphere": "left",
                "message": f"Using left hemisphere result due to right error: {right_result.get('error')}"
            }
        
        # No errors, merge the results
        
        # For dictionaries, combine keys
        if isinstance(left_result, dict) and isinstance(right_result, dict):
            merged = {}
            
            # Add all keys from left result
            for key, value in left_result.items():
                merged[key] = value
            
            # Add keys from right result, avoiding duplicates
            for key, value in right_result.items():
                if key not in merged:
                    merged[key] = value
                else:
                    # For duplicate keys, create a combined value
                    merged[f"{key}_combined"] = {
                        "left": merged.get(key), # Use .get() for safety
                        "right": value
                    }
            
            merged["status"] = "merged"
            merged["message"] = "Combined results from both hemispheres"
            return merged
        
        # For lists, combine items
        elif isinstance(left_result, list) and isinstance(right_result, list):
            # Combine lists, removing duplicates
            combined = list(left_result)
            for item in right_result:
                if item not in combined:
                    combined.append(item)
            
            return {
                "status": "merged",
                "result": combined,
                "message": "Combined results from both hemispheres"
            }
        
        # For strings, concatenate
        elif isinstance(left_result, str) and isinstance(right_result, str):
            return {
                "status": "merged",
                "result": f"{left_result}\n\n{right_result}",
                "message": "Combined results from both hemispheres"
            }
        
        # For other types, return both results
        return {
            "status": "parallel",
            "left": left_result,
            "right": right_result,
            "message": "Parallel results from both hemispheres"
        }
    
    def submit_task(self, data: Any, task_id: Optional[str] = None, # task_id can be None
                   priority: TaskPriority = TaskPriority.MEDIUM,
                   metadata: Optional[Dict[str, Any]] = None) -> str: # metadata can be None
        """Submit a task for processing.
        
        Args:
            data: Data to process
            task_id: Optional task ID (generated if not provided)
            priority: Task priority
            metadata: Additional task metadata
            
        Returns:
            Task ID
        """
        if not self.is_active():
            logger.warning(f"Attempted to submit task to inactive TwinFlame {self.name}")
            raise ValueError(f"TwinFlame {self.name} is not active")
        
        # Generate task ID if not provided
        if task_id is None:
            task_id = f"task_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Create the task
        task = Task(task_id, data, priority, metadata)
        
        # Add to queue
        with self._lock:
            self._task_queue[task_id] = task
        
        logger.info(f"Task {task_id} submitted to TwinFlame {self.name}")
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]: # Return type can be None
        """Get the status of a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task status information or None if not found
        """
        with self._lock:
            # Check if task is in the queue
            if task_id in self._task_queue:
                return self._task_queue[task_id].to_dict()
            
            # Check if task is completed
            if task_id in self._completed_tasks:
                return self._completed_tasks[task_id].to_dict()
        return None # Task not found

    def get_task_result(self, task_id: str) -> Optional[Any]:
        """Get the result of a completed task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task result or None if not found or not completed
        """
        with self._lock:
            if task_id in self._completed_tasks:
                task = self._completed_tasks[task_id]
                if task.status == TaskStatus.MERGED:
                    return task.merged_result
                elif task.status == TaskStatus.FAILED:
                    return {"error": task.error, "message": "Task processing failed"}
        return None

    def process(self, data: Any) -> str:
        """Process data by submitting it as a new task.
        
        This is the main entry point for the TwinFlame entity.
        
        Args:
            data: Data to process
            
        Returns:
            Task ID of the submitted task
        """
        logger.info(f"TwinFlame {self.name} received data for processing: {str(data)[:100]}...")
        task_id = self.submit_task(data)
        return task_id

    def sync(self) -> bool:
        """Sync TwinFlame state with Codex memory or log status.
        
        Returns:
            True if sync successful, False otherwise
        """
        try:
            left_stats = self.left_hemisphere.get_stats()
            right_stats = self.right_hemisphere.get_stats()
            
            sync_data = {
                'entity_name': self.name,
                'active': self.is_active(),
                'processing_mode': self._processing_mode.name,
                'queued_tasks': len(self._task_queue),
                'completed_tasks': len(self._completed_tasks),
                'left_hemisphere_stats': left_stats,
                'right_hemisphere_stats': right_stats,
                'timestamp': time.time()
            }
            
            if self.socketio:
                self.socketio.emit('twinflame_sync', sync_data)
            
            logger.debug(f"TwinFlame {self.name} synced state: {json.dumps(sync_data, indent=2)}")
            return True
        except Exception as e:
            logger.error(f"TwinFlame sync failed: {e}")
            return False

    def suggest(self) -> List[str]:
        """Provide self-diagnostic suggestions.
        
        Returns:
            List of suggestions for improvement
        """
        suggestions = super().suggest()
        
        left_stats = self.left_hemisphere.get_stats()
        right_stats = self.right_hemisphere.get_stats()
        
        suggestions.extend([
            f"Processing Mode: {self._processing_mode.name}",
            f"Tasks in Queue: {len(self._task_queue)}",
            f"Tasks Completed: {len(self._completed_tasks)}",
            f"Left Hemisphere - Tasks: {left_stats['tasks_processed']}, Avg Time: {left_stats['avg_processing_time']:.2f}s, Errors: {left_stats['errors']}",
            f"Right Hemisphere - Tasks: {right_stats['tasks_processed']}, Avg Time: {right_stats['avg_processing_time']:.2f}s, Errors: {right_stats['errors']}"
        ])
        
        if len(self._task_queue) > 10:
            suggestions.append("Task queue is growing, consider optimizing processing or adding resources.")
        
        if left_stats['errors'] > left_stats['tasks_processed'] * 0.1 and left_stats['tasks_processed'] > 10:
            suggestions.append(f"High error rate in Left Hemisphere ({left_stats['errors']}/{left_stats['tasks_processed']}). Review error logs.")
        
        if right_stats['errors'] > right_stats['tasks_processed'] * 0.1 and right_stats['tasks_processed'] > 10:
            suggestions.append(f"High error rate in Right Hemisphere ({right_stats['errors']}/{right_stats['tasks_processed']}). Review error logs.")
            
        if abs(left_stats['avg_processing_time'] - right_stats['avg_processing_time']) > 0.5 and left_stats['tasks_processed'] > 10 and right_stats['tasks_processed'] > 10:
             suggestions.append("Significant difference in average processing time between hemispheres. Investigate potential bottlenecks.")

        return suggestions

def create_twin_flame(socketio=None) -> TwinFlame:
    """Create and register a TwinFlame entity.
    
    Args:
        socketio: Flask-SocketIO instance
        
    Returns:
        The created TwinFlame instance
    """
    twin_flame = TwinFlame(socketio=socketio)
    registry.register(twin_flame)
    return twin_flame
