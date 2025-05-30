"""
VAEL Core - Modular Entity Orchestration System
Version: 0.1.0 (2025-05-30)

This package provides a unified interface to all VAEL Core entities:
- local_vael: Primary local reasoning engine
- twin_flame: Bi-hemisphere processing
- sentinel: Alert and monitoring system
- nexus: Intrusion detection system
- watchdog: Process guardian
- manus_interface: Cloud bridge

Each entity exposes standard methods:
- pulse(): Health status check
- sync(): Configuration reload
- suggest(context): Entity-specific recommendations
"""

__version__ = '0.1.0'
__author__ = 'Factory AI'
__status__ = 'Development'

# Lazy imports to minimize token usage
_modules = {}

def _get_module(name):
    """Lazy load module only when needed"""
    if name not in _modules:
        if name == 'local_vael':
            from . import local_vael
            _modules[name] = local_vael
        elif name == 'twin_flame':
            from . import twin_flame
            _modules[name] = twin_flame
        elif name == 'sentinel':
            from . import sentinel
            _modules[name] = sentinel
        elif name == 'nexus':
            from . import nexus
            _modules[name] = nexus
        elif name == 'watchdog':
            from . import watchdog
            _modules[name] = watchdog
        elif name == 'manus_interface':
            from . import manus_interface
            _modules[name] = manus_interface
    return _modules.get(name)

# Unified interface functions
def pulse(entity=None):
    """Get health status of specified entity or all entities.
    
    Args:
        entity (str, optional): Entity name or None for all entities.
        
    Returns:
        dict: Health status with entity names as keys and status as values.
    """
    if entity:
        module = _get_module(entity)
        return {entity: module.pulse()} if module else {entity: "🔴 Not found"}
    
    results = {}
    for name in ['local_vael', 'twin_flame', 'sentinel', 'nexus', 'watchdog', 'manus_interface']:
        try:
            module = _get_module(name)
            results[name] = module.pulse() if module else "🔴 Not loaded"
        except Exception as e:
            results[name] = f"🔴 Error: {str(e)}"
    return results

def sync(entity=None):
    """Reload configuration for specified entity or all entities.
    
    Args:
        entity (str, optional): Entity name or None for all entities.
        
    Returns:
        dict: Sync status with entity names as keys and status as values.
    """
    if entity:
        module = _get_module(entity)
        return {entity: module.sync()} if module else {entity: "🔴 Not found"}
    
    results = {}
    for name in ['local_vael', 'twin_flame', 'nexus', 'manus_interface']:
        try:
            module = _get_module(name)
            if module and hasattr(module, 'sync'):
                results[name] = module.sync()
            else:
                results[name] = "⚪ No sync method"
        except Exception as e:
            results[name] = f"🔴 Error: {str(e)}"
    return results

def suggest(context, entity=None):
    """Get recommendations from specified entity or appropriate entity.
    
    Args:
        context (dict): Context information for the suggestion.
        entity (str, optional): Entity name or None for auto-routing.
        
    Returns:
        dict: Suggestions with entity names as keys and recommendations as values.
    """
    if entity:
        module = _get_module(entity)
        return {entity: module.suggest(context)} if module else {entity: "🔴 Not found"}
    
    # Auto-route to appropriate entity based on context
    if 'alert' in context:
        module = _get_module('sentinel')
        return {'sentinel': module.suggest(context)} if module else {'sentinel': "🔴 Not loaded"}
    elif 'security' in context or 'anomaly' in context:
        module = _get_module('nexus')
        return {'nexus': module.suggest(context)} if module else {'nexus': "🔴 Not loaded"}
    elif 'creative' in context or 'analytical' in context:
        module = _get_module('twin_flame')
        return {'twin_flame': module.suggest(context)} if module else {'twin_flame': "🔴 Not loaded"}
    else:
        # Default to local_vael
        module = _get_module('local_vael')
        return {'local_vael': module.suggest(context)} if module else {'local_vael': "🔴 Not loaded"}

# Version and system info
def version():
    """Return version information for VAEL Core and all loaded entities."""
    info = {
        'vael_core': __version__,
        'status': __status__,
    }
    
    # Add entity versions if available
    for name in ['local_vael', 'twin_flame', 'sentinel', 'nexus', 'watchdog', 'manus_interface']:
        module = _get_module(name)
        if module and hasattr(module, '__version__'):
            info[name] = module.__version__
    
    return info
