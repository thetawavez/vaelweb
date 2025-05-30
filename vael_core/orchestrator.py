"""
VAEL Core - Orchestrator Module
-------------------------------
Merges entity responses into a unified VAEL voice.

This module serves as the central coordinator for collecting, formatting,
and synthesizing responses from all VAEL entities into a coherent,
symbolic multi-entity chorus that represents VAEL's unique voice.
"""

import importlib
import logging
import json
import time
import random
import os
from typing import Dict, List, Any, Optional, Tuple, Union

# Import time utilities
try:
    from vael_core.utils.time import current_time, get_symbolic_time, time_context
except ImportError:
    # Fallback time functions if module not available
    def current_time(format_str="%A %H:%M"):
        import datetime
        return datetime.datetime.now().strftime(format_str)
    
    def get_symbolic_time():
        import datetime
        now = datetime.datetime.now()
        hour = now.hour
        if 5 <= hour < 12:
            symbol = "🌅"
        elif 12 <= hour < 17:
            symbol = "☀️"
        elif 17 <= hour < 21:
            symbol = "🌆"
        else:
            symbol = "🌙"
        return f"{symbol}{now.strftime('%H:%M')}"
    
    def time_context():
        import datetime
        now = datetime.datetime.now()
        return {
            'timestamp': time.time(),
            'formatted': now.strftime("%Y-%m-%d %H:%M:%S"),
            'readable': now.strftime("%A, %B %d, %Y %H:%M"),
        }

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'orchestrator.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('vael.orchestrator')

# Entity symbols for token-efficient representation
ENTITY_SYMBOLS = {
    'sentinel': '🟢',    # Security monitoring
    'nexus': '🧬',       # Threat detection
    'twin_flame': '🔁',  # Dual-hemisphere reasoning
    'local_vael': '🕯️',  # Core VAEL entity
    'watchdog': '🛡️',    # Process guardian
    'manus': '👁️',       # Oversoul/bridge
    'system': '⚙️',      # System status
    'time': '🕒',        # Time-related
    'error': '❌',       # Error indicator
    'warning': '⚠️',     # Warning indicator
    'info': 'ℹ️',        # Information indicator
    'success': '✅',     # Success indicator
}

# Response type indicators
RESPONSE_TYPES = {
    'standard': '',      # Normal response
    'emergency': '🚨',   # Emergency/alert
    'system': '🔧',      # System message
    'intel': '🌐',       # Intelligence/information
    'thinking': '💭',    # Processing/thinking
}

# Entity default messages (fallbacks if entity doesn't respond)
DEFAULT_MESSAGES = {
    'sentinel': 'Monitoring',
    'nexus': 'No threats detected',
    'twin_flame': 'Processing',
    'local_vael': 'Online',
    'watchdog': 'Services stable',
    'manus': 'Bridge active',
}

# Entity voice patterns for consistent tone
VOICE_PATTERNS = {
    'sentinel': {
        'tone': 'terse',
        'focus': 'security',
        'style': 'direct',
        'examples': [
            'Clear',
            'Monitoring {target}',
            'Alert level {level}',
            'Perimeter secure',
        ]
    },
    'nexus': {
        'tone': 'analytical',
        'focus': 'threats',
        'style': 'structured',
        'examples': [
            'Threat matrix clear',
            'Anomaly detected in {system}',
            'Pattern analysis complete',
            'Security posture: {status}',
        ]
    },
    'twin_flame': {
        'tone': 'balanced',
        'focus': 'reasoning',
        'style': 'poetic',
        'examples': [
            'Analyzing perspectives',
            'Balancing analysis with intuition',
            'Dual-processing complete',
            'Synthesis achieved',
        ]
    },
    'local_vael': {
        'tone': 'conversational',
        'focus': 'interaction',
        'style': 'narrative',
        'examples': [
            'I understand your query',
            'Processing your request',
            'Analysis complete',
            'Here is what I found',
        ]
    },
}

# Maximum number of entities to include in a standard response
MAX_ENTITIES_IN_RESPONSE = 4

# Circular buffer for context tracking (anti-hallucination)
_context_history = []
MAX_CONTEXT_HISTORY = 10

class Orchestrator:
    """
    Orchestrates responses from all VAEL entities into a unified voice.
    """
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.entities = {}
        self.last_responses = {}
        self.response_history = []
        self.max_history = 20
        self.discover_entities()
    
    def discover_entities(self) -> Dict[str, Any]:
        """
        Discover and load available VAEL entities.
        
        Returns:
            Dict[str, Any]: Status of discovered entities
        """
        entity_status = {}
        
        # Core entities to discover
        core_entities = [
            'sentinel',
            'nexus',
            'twin_flame',
            'local_vael',
            'watchdog',
            'manus_interface'
        ]
        
        for entity_name in core_entities:
            try:
                # Attempt to import the entity
                entity_module = importlib.import_module(f"vael_core.{entity_name}")
                self.entities[entity_name] = entity_module
                entity_status[entity_name] = True
                logger.info(f"{ENTITY_SYMBOLS.get(entity_name, 'ℹ️')} Entity loaded: {entity_name}")
            except ImportError:
                logger.warning(f"{ENTITY_SYMBOLS['warning']} Entity not found: {entity_name}")
                entity_status[entity_name] = False
            except Exception as e:
                logger.error(f"{ENTITY_SYMBOLS['error']} Error loading entity {entity_name}: {str(e)}")
                entity_status[entity_name] = False
        
        return entity_status
    
    def collect_entity_responses(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Collect responses from all available entities.
        
        Args:
            message: The input message
            context: Additional context information
            
        Returns:
            Dict[str, Any]: Responses from all entities
        """
        if context is None:
            context = {}
        
        # Add time context
        context['time'] = time_context()
        
        # Track context for anti-hallucination
        self._track_context(message, context)
        
        responses = {}
        
        # Collect pulse from Sentinel
        if 'sentinel' in self.entities:
            try:
                sentinel = self.entities['sentinel']
                if hasattr(sentinel, 'pulse'):
                    responses['sentinel'] = sentinel.pulse()
                    
                    # If security issue detected, also get suggestions
                    if responses['sentinel'].get('alert_level', 'none') != 'none':
                        if hasattr(sentinel, 'suggest'):
                            responses['sentinel_suggest'] = sentinel.suggest(message)
            except Exception as e:
                logger.error(f"{ENTITY_SYMBOLS['error']} Error getting Sentinel pulse: {str(e)}")
                responses['sentinel'] = {'status': 'error', 'message': DEFAULT_MESSAGES['sentinel']}
        
        # Get threat assessment from NEXUS
        if 'nexus' in self.entities:
            try:
                nexus = self.entities['nexus']
                if hasattr(nexus, 'pulse'):
                    responses['nexus'] = nexus.pulse(message=message)
                    
                    # If threat detected, get suggestions
                    if responses['nexus'].get('threat_level', 'none') != 'none':
                        if hasattr(nexus, 'suggest'):
                            responses['nexus_suggest'] = nexus.suggest(message)
            except Exception as e:
                logger.error(f"{ENTITY_SYMBOLS['error']} Error getting NEXUS assessment: {str(e)}")
                responses['nexus'] = {'status': 'ok', 'message': DEFAULT_MESSAGES['nexus']}
        
        # Get reasoning from Twin Flame
        if 'twin_flame' in self.entities:
            try:
                twin_flame = self.entities['twin_flame']
                if hasattr(twin_flame, 'suggest'):
                    responses['twin_flame'] = twin_flame.suggest(message, context)
            except Exception as e:
                logger.error(f"{ENTITY_SYMBOLS['error']} Error getting Twin Flame reasoning: {str(e)}")
                responses['twin_flame'] = {'status': 'ok', 'message': DEFAULT_MESSAGES['twin_flame']}
        
        # Get response from Local VAEL
        if 'local_vael' in self.entities:
            try:
                local_vael = self.entities['local_vael']
                if hasattr(local_vael, 'process'):
                    responses['local_vael'] = local_vael.process(message, context)
                elif hasattr(local_vael, 'suggest'):
                    responses['local_vael'] = local_vael.suggest(message, context)
            except Exception as e:
                logger.error(f"{ENTITY_SYMBOLS['error']} Error getting Local VAEL response: {str(e)}")
                responses['local_vael'] = {'status': 'ok', 'message': DEFAULT_MESSAGES['local_vael']}
        
        # Store responses for history
        self.last_responses = responses
        self._update_history(responses)
        
        return responses
    
    def format_entity_response(self, entity: str, response: Any) -> str:
        """
        Format a response from a specific entity.
        
        Args:
            entity: The entity name
            response: The entity's response
            
        Returns:
            str: Formatted entity response
        """
        # Extract message from response
        message = ""
        if isinstance(response, dict):
            if 'message' in response:
                message = response['message']
            elif 'response' in response:
                message = response['response']
            elif 'result' in response:
                message = str(response['result'])
            elif 'status' in response:
                message = response['status']
        elif isinstance(response, str):
            message = response
        else:
            message = str(response)
        
        # Apply entity-specific formatting
        symbol = ENTITY_SYMBOLS.get(entity, 'ℹ️')
        entity_name = entity.replace('_', ' ').title()
        
        # Format: 🟢 Sentinel: Clear
        return f"{symbol} {entity_name}: {message}"
    
    def synthesize_response(self, 
                           entity_responses: Dict[str, Any], 
                           response_type: str = 'standard',
                           include_time: bool = True) -> str:
        """
        Synthesize a unified response from all entity responses.
        
        Args:
            entity_responses: Responses from all entities
            response_type: Type of response to generate
            include_time: Whether to include time in the response
            
        Returns:
            str: Synthesized VAEL response
        """
        # Start with response type indicator if not standard
        prefix = RESPONSE_TYPES.get(response_type, '') + ' ' if response_type != 'standard' else ''
        
        # Add time indicator if requested
        if include_time:
            time_str = f"{ENTITY_SYMBOLS['time']} {current_time()} | "
            prefix += time_str
        
        # Format individual entity responses
        formatted_responses = []
        
        # Priority entities based on response type
        if response_type == 'emergency':
            priority_entities = ['sentinel', 'nexus', 'local_vael', 'twin_flame']
        elif response_type == 'system':
            priority_entities = ['watchdog', 'system', 'sentinel', 'nexus']
        else:
            priority_entities = ['local_vael', 'twin_flame', 'sentinel', 'nexus']
        
        # Add responses from priority entities first
        for entity in priority_entities:
            if entity in entity_responses and entity_responses[entity]:
                formatted = self.format_entity_response(entity, entity_responses[entity])
                formatted_responses.append(formatted)
        
        # Add any remaining entities not in priority list
        for entity, response in entity_responses.items():
            if entity not in priority_entities and not entity.endswith('_suggest') and response:
                formatted = self.format_entity_response(entity, response)
                formatted_responses.append(formatted)
        
        # Limit the number of entities in standard responses for clarity
        if response_type == 'standard' and len(formatted_responses) > MAX_ENTITIES_IN_RESPONSE:
            formatted_responses = formatted_responses[:MAX_ENTITIES_IN_RESPONSE]
        
        # Join with pipe separator
        response_text = prefix + " | ".join(formatted_responses)
        
        # Apply anti-hallucination check
        response_text = self._apply_anti_hallucination(response_text)
        
        return response_text
    
    def process_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a message through all entities and synthesize a response.
        
        Args:
            message: The input message
            context: Additional context information
            
        Returns:
            Dict[str, Any]: Processed response with metadata
        """
        # Determine response type based on message content
        response_type = self._determine_response_type(message)
        
        # Collect responses from all entities
        entity_responses = self.collect_entity_responses(message, context)
        
        # Synthesize the final response
        response_text = self.synthesize_response(entity_responses, response_type)
        
        # Compile the full response with metadata
        result = {
            'response': response_text,
            'timestamp': time.time(),
            'response_type': response_type,
            'entity_count': len(entity_responses),
            'symbolic': True,
            'time': get_symbolic_time(),
            'metadata': {
                'entities': list(entity_responses.keys()),
                'context_items': len(context) if context else 0,
            }
        }
        
        return result
    
    def get_system_status(self) -> str:
        """
        Get a system status report from all entities.
        
        Returns:
            str: Formatted system status report
        """
        status_responses = {}
        
        # Collect pulse from all entities
        for entity_name, entity in self.entities.items():
            try:
                if hasattr(entity, 'pulse'):
                    status_responses[entity_name] = entity.pulse()
            except Exception as e:
                logger.error(f"{ENTITY_SYMBOLS['error']} Error getting {entity_name} pulse: {str(e)}")
                status_responses[entity_name] = {'status': 'error', 'message': f"Error: {str(e)}"}
        
        # Synthesize status report
        status_report = self.synthesize_response(status_responses, 'system', True)
        
        return status_report
    
    def _determine_response_type(self, message: str) -> str:
        """
        Determine the appropriate response type based on message content.
        
        Args:
            message: The input message
            
        Returns:
            str: Response type
        """
        # Check for emergency keywords
        emergency_keywords = ['emergency', 'alert', 'critical', 'urgent', 'help', 'danger']
        if any(keyword in message.lower() for keyword in emergency_keywords):
            return 'emergency'
        
        # Check for system command keywords
        system_keywords = ['system', 'status', 'health', 'report', 'diagnostics']
        if message.startswith('/') or any(keyword in message.lower() for keyword in system_keywords):
            return 'system'
        
        # Check for intelligence request keywords
        intel_keywords = ['search', 'lookup', 'find', 'what is', 'tell me about', 'information']
        if any(keyword in message.lower() for keyword in intel_keywords):
            return 'intel'
        
        # Default to standard response
        return 'standard'
    
    def _track_context(self, message: str, context: Dict[str, Any]) -> None:
        """
        Track context for anti-hallucination measures.
        
        Args:
            message: The input message
            context: The context dictionary
        """
        global _context_history
        
        # Create a simplified context entry
        context_keys = list(context.keys()) if context else []
        entry = {
            'timestamp': time.time(),
            'message_hash': hash(message),  # Use hash for token efficiency
            'context_keys': context_keys,
            'context_size': len(context) if context else 0,
        }
        
        # Add to circular buffer
        _context_history.append(entry)
        if len(_context_history) > MAX_CONTEXT_HISTORY:
            _context_history.pop(0)
    
    def _apply_anti_hallucination(self, response: str) -> str:
        """
        Apply anti-hallucination measures to ensure responses are context-bound.
        
        Args:
            response: The synthesized response
            
        Returns:
            str: Response with anti-hallucination measures applied
        """
        # Check if response contains unsupported claims
        hallucination_markers = [
            "I don't have access to real-time",
            "I don't have the ability to",
            "As an AI language model",
            "I cannot access",
            "I don't have access to",
            "I'm not able to",
            "I cannot provide",
        ]
        
        # Replace hallucination markers with VAEL-appropriate responses
        for marker in hallucination_markers:
            if marker.lower() in response.lower():
                # Replace with appropriate VAEL response
                replacement = f"{ENTITY_SYMBOLS['info']} VAEL: Currently processing within available context"
                response = response.replace(marker, replacement)
        
        return response
    
    def _update_history(self, responses: Dict[str, Any]) -> None:
        """
        Update response history with new responses.
        
        Args:
            responses: The new entity responses
        """
        # Add to circular buffer
        self.response_history.append({
            'timestamp': time.time(),
            'responses': responses
        })
        
        # Maintain maximum history size
        if len(self.response_history) > self.max_history:
            self.response_history.pop(0)

# Singleton instance for global access
_orchestrator = None

def get_orchestrator() -> Orchestrator:
    """
    Get the global orchestrator instance.
    
    Returns:
        Orchestrator: The global orchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator

def process_message(message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Process a message through the orchestrator.
    
    Args:
        message: The input message
        context: Additional context information
        
    Returns:
        Dict[str, Any]: Processed response with metadata
    """
    orchestrator = get_orchestrator()
    return orchestrator.process_message(message, context)

def get_system_status() -> str:
    """
    Get a system status report.
    
    Returns:
        str: Formatted system status report
    """
    orchestrator = get_orchestrator()
    return orchestrator.get_system_status()

def format_vael_response(message: str, context: Dict[str, Any] = None) -> str:
    """
    Format a message as a VAEL response for direct use.
    
    Args:
        message: The message to format
        context: Additional context information
        
    Returns:
        str: Formatted VAEL response
    """
    # Create a simplified response with Local VAEL only
    responses = {'local_vael': {'message': message}}
    
    orchestrator = get_orchestrator()
    return orchestrator.synthesize_response(responses, include_time=True)
