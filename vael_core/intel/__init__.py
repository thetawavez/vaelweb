"""
VAEL Core - Intelligence Module
------------------------------
Provides real-time information access for VAEL entities.

This module serves as the gateway to external information sources,
allowing VAEL to access current data from the internet, APIs,
and other real-time sources to maintain context-bound responses.
"""

import importlib
import logging
import os
import time
import json
from typing import Dict, List, Any, Optional, Union, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'intel.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('vael.intel')

# Intelligence source symbols for token-efficient representation
INTEL_SYMBOLS = {
    'search': '🔍',      # Search engine results
    'weather': '🌦️',     # Weather information
    'wiki': '📚',        # Wikipedia information
    'news': '📰',        # News information
    'time': '🕒',        # Time-related information
    'location': '📍',    # Location information
    'error': '❌',       # Error indicator
    'warning': '⚠️',     # Warning indicator
    'info': 'ℹ️',        # Information indicator
    'success': '✅',     # Success indicator
}

# Registry of available intelligence sources
_intel_sources = {}

# Cache for intelligence results to reduce API calls
_intel_cache = {}
MAX_CACHE_SIZE = 100
CACHE_EXPIRY = 300  # 5 minutes in seconds

class IntelSource:
    """Base class for intelligence sources."""
    
    def __init__(self, name: str, symbol: str = None):
        """
        Initialize an intelligence source.
        
        Args:
            name: The name of the source
            symbol: The symbol to represent the source
        """
        self.name = name
        self.symbol = symbol or INTEL_SYMBOLS.get(name.lower(), 'ℹ️')
        self.last_query_time = 0
        self.query_count = 0
    
    def query(self, query_text: str, **kwargs) -> Dict[str, Any]:
        """
        Query the intelligence source.
        
        Args:
            query_text: The query text
            **kwargs: Additional query parameters
            
        Returns:
            Dict[str, Any]: The query results
        """
        raise NotImplementedError("Subclasses must implement query()")
    
    def format_response(self, response: Dict[str, Any]) -> str:
        """
        Format the response for display.
        
        Args:
            response: The response data
            
        Returns:
            str: The formatted response
        """
        if 'error' in response:
            return f"{self.symbol} {self.name}: Error - {response['error']}"
        
        if 'result' in response:
            return f"{self.symbol} {self.name}: {response['result']}"
        
        return f"{self.symbol} {self.name}: No results"

def register_source(source: IntelSource) -> None:
    """
    Register an intelligence source.
    
    Args:
        source: The intelligence source to register
    """
    _intel_sources[source.name.lower()] = source
    logger.info(f"{source.symbol} Registered intelligence source: {source.name}")

def get_source(name: str) -> Optional[IntelSource]:
    """
    Get an intelligence source by name.
    
    Args:
        name: The name of the source
        
    Returns:
        Optional[IntelSource]: The intelligence source, or None if not found
    """
    return _intel_sources.get(name.lower())

def list_sources() -> List[str]:
    """
    List all available intelligence sources.
    
    Returns:
        List[str]: List of source names
    """
    return list(_intel_sources.keys())

def query(source_name: str, query_text: str, **kwargs) -> Dict[str, Any]:
    """
    Query an intelligence source.
    
    Args:
        source_name: The name of the source to query
        query_text: The query text
        **kwargs: Additional query parameters
        
    Returns:
        Dict[str, Any]: The query results
    """
    # Check cache first
    cache_key = f"{source_name}:{query_text}:{json.dumps(kwargs)}"
    if cache_key in _intel_cache:
        cache_entry = _intel_cache[cache_key]
        if time.time() - cache_entry['timestamp'] < CACHE_EXPIRY:
            logger.info(f"{INTEL_SYMBOLS['info']} Cache hit for {source_name}: {query_text}")
            return cache_entry['result']
    
    # Get the source
    source = get_source(source_name)
    if not source:
        error_result = {
            'error': f"Intelligence source '{source_name}' not found",
            'available_sources': list_sources()
        }
        logger.error(f"{INTEL_SYMBOLS['error']} {error_result['error']}")
        return error_result
    
    try:
        # Query the source
        logger.info(f"{source.symbol} Querying {source.name}: {query_text}")
        result = source.query(query_text, **kwargs)
        
        # Update source stats
        source.last_query_time = time.time()
        source.query_count += 1
        
        # Cache the result
        _intel_cache[cache_key] = {
            'timestamp': time.time(),
            'result': result
        }
        
        # Trim cache if needed
        if len(_intel_cache) > MAX_CACHE_SIZE:
            # Remove oldest entries
            sorted_cache = sorted(_intel_cache.items(), key=lambda x: x[1]['timestamp'])
            for key, _ in sorted_cache[:len(_intel_cache) - MAX_CACHE_SIZE]:
                del _intel_cache[key]
        
        return result
    except Exception as e:
        error_result = {
            'error': str(e),
            'source': source_name,
            'query': query_text
        }
        logger.error(f"{INTEL_SYMBOLS['error']} Error querying {source_name}: {str(e)}")
        return error_result

def format_intel_response(source_name: str, response: Dict[str, Any]) -> str:
    """
    Format an intelligence response for display.
    
    Args:
        source_name: The name of the source
        response: The response data
        
    Returns:
        str: The formatted response
    """
    source = get_source(source_name)
    if source:
        return source.format_response(response)
    
    # Default formatting if source not found
    symbol = INTEL_SYMBOLS.get(source_name.lower(), 'ℹ️')
    
    if 'error' in response:
        return f"{symbol} {source_name.title()}: Error - {response['error']}"
    
    if 'result' in response:
        return f"{symbol} {source_name.title()}: {response['result']}"
    
    return f"{symbol} {source_name.title()}: No results"

def discover_sources() -> List[str]:
    """
    Discover and register available intelligence sources.
    
    Returns:
        List[str]: List of discovered source names
    """
    discovered = []
    
    # Try to import and register known sources
    source_modules = [
        ('google', 'vael_core.intel.google'),
        ('weather', 'vael_core.intel.weather'),
        ('wiki', 'vael_core.intel.wiki'),
        ('news', 'vael_core.intel.news'),
    ]
    
    for name, module_path in source_modules:
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, 'get_source'):
                source = module.get_source()
                register_source(source)
                discovered.append(name)
                logger.info(f"{INTEL_SYMBOLS.get(name, 'ℹ️')} Discovered intelligence source: {name}")
        except ImportError:
            logger.warning(f"{INTEL_SYMBOLS['warning']} Intelligence source module not found: {module_path}")
        except Exception as e:
            logger.error(f"{INTEL_SYMBOLS['error']} Error loading intelligence source {name}: {str(e)}")
    
    return discovered

# Initialize on import
discover_sources()
