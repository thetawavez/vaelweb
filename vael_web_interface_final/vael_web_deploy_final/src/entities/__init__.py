"""
VAEL Entity System - Base Classes and Registry
---------------------------------------------
This module defines the foundational structure for all symbolic entities in the VAEL system.
Each entity (Sentinel, Watchdog, TwinFlame, etc.) inherits from the base Entity class,
providing a consistent interface for activation, pulse emission, self-diagnostics, and processing.

The EntityRegistry manages all entities and provides centralized access to entity capabilities.
"""

import time
import logging
import threading
import uuid
from typing import Dict, List, Any, Optional, Callable, Union

# Configure logger
logger = logging.getLogger(__name__)

class Entity:
    """Base class for all VAEL symbolic entities.
    
    Each entity has standard interfaces for:
    - Activation/deactivation
    - Pulse emission (heartbeat)
    - Self-diagnostics
    - Data processing
    """
    
    def __init__(self, name: str, socketio=None):
        """Initialize a new entity.
        
        Args:
            name: Unique identifier for this entity
            socketio: Flask-SocketIO instance for emitting events
        """
        self.name = name
        self.socketio = socketio
        self._active = False
        self._created_at = time.time()
        self._last_pulse = 0
        self._pulse_count = 0
        self._id = str(uuid.uuid4())
        logger.info(f"Entity {name} initialized with ID {self._id}")
    
    def activate(self) -> bool:
        """Activate this entity."""
        self._active = True
        logger.info(f"Entity {self.name} activated")
        return True
    
    def deactivate(self) -> bool:
        """Deactivate this entity."""
        self._active = False
        logger.info(f"Entity {self.name} deactivated")
        return True
    
    def is_active(self) -> bool:
        """Check if entity is active."""
        return self._active
    
    def pulse(self) -> bool:
        """Emit a heartbeat pulse."""
        now = time.time()
        self._last_pulse = now
        self._pulse_count += 1
        
        if self.socketio and self._active:
            self.socketio.emit('pulse', {
                'entity': self.name,
                'id': self._id,
                'ts': now,
                'count': self._pulse_count
            })
            logger.debug(f"Entity {self.name} emitted pulse #{self._pulse_count}")
        return True
    
    def sync(self) -> bool:
        """Sync state with Codex memory.
        
        Override in subclasses to implement entity-specific synchronization.
        """
        logger.debug(f"Entity {self.name} sync() called - default implementation")
        return True
    
    def suggest(self) -> List[str]:
        """Self-diagnostic - return improvement suggestions.
        
        Override in subclasses to provide entity-specific diagnostics.
        """
        uptime = time.time() - self._created_at
        return [
            f"Entity {self.name} running for {uptime:.1f} seconds",
            f"Pulse count: {self._pulse_count}",
            "No specific suggestions available - override suggest() method"
        ]
    
    def process(self, data: Any) -> Any:
        """Process incoming data.
        
        Override in subclasses to implement entity-specific processing.
        
        Args:
            data: The data to process
            
        Returns:
            Processed data
        """
        logger.debug(f"Entity {self.name} process() called - default implementation")
        return data
    
    def __str__(self) -> str:
        """String representation of this entity."""
        status = "active" if self._active else "inactive"
        return f"Entity({self.name}, {status}, pulses={self._pulse_count})"


class EntityRegistry:
    """Registry for all VAEL entities.
    
    Provides centralized access to entity capabilities and management.
    """
    
    def __init__(self, socketio=None):
        """Initialize the entity registry.
        
        Args:
            socketio: Flask-SocketIO instance to pass to entities
        """
        self._entities: Dict[str, Entity] = {}
        self.socketio = socketio
        logger.info("Entity registry initialized")
    
    def register(self, entity: Entity) -> bool:
        """Register an entity with the system.
        
        Args:
            entity: The entity to register
            
        Returns:
            True if registration successful, False otherwise
        """
        if entity.name in self._entities:
            logger.warning(f"Entity {entity.name} already registered, replacing")
        
        self._entities[entity.name] = entity
        if entity.socketio is None and self.socketio is not None:
            entity.socketio = self.socketio
        
        logger.info(f"Entity {entity.name} registered")
        return True
    
    def get(self, name: str) -> Optional[Entity]:
        """Get an entity by name.
        
        Args:
            name: The name of the entity to retrieve
            
        Returns:
            The entity if found, None otherwise
        """
        return self._entities.get(name)
    
    def list_entities(self) -> List[str]:
        """List all registered entity names."""
        return list(self._entities.keys())
    
    def activate_all(self) -> bool:
        """Activate all registered entities."""
        for entity in self._entities.values():
            entity.activate()
        return True
    
    def deactivate_all(self) -> bool:
        """Deactivate all registered entities."""
        for entity in self._entities.values():
            entity.deactivate()
        return True
    
    def pulse_all(self) -> bool:
        """Emit pulse from all active entities."""
        for entity in self._entities.values():
            if entity.is_active():
                entity.pulse()
        return True
    
    def sync_all(self) -> Dict[str, bool]:
        """Sync all entities and return results."""
        results = {}
        for name, entity in self._entities.items():
            if entity.is_active():
                results[name] = entity.sync()
        return results
    
    def suggest_all(self) -> Dict[str, List[str]]:
        """Get suggestions from all active entities."""
        suggestions = {}
        for name, entity in self._entities.items():
            if entity.is_active():
                suggestions[name] = entity.suggest()
        return suggestions
    
    def process_chain(self, data: Any, entity_names: List[str] = None) -> Any:
        """Process data through a chain of entities.
        
        Args:
            data: The data to process
            entity_names: List of entity names to process through, in order.
                          If None, uses all active entities.
                          
        Returns:
            The processed data
        """
        if entity_names is None:
            entity_names = [name for name, entity in self._entities.items() 
                           if entity.is_active()]
        
        result = data
        for name in entity_names:
            entity = self._entities.get(name)
            if entity and entity.is_active():
                result = entity.process(result)
        
        return result
    
    def __len__(self) -> int:
        """Get the number of registered entities."""
        return len(self._entities)


# Global registry instance
registry = EntityRegistry()


def start_heartbeat(interval: int = 5) -> threading.Thread:
    """Start a heartbeat thread that pulses all active entities.
    
    Args:
        interval: Seconds between pulses
        
    Returns:
        The started thread
    """
    def _beat():
        while True:
            registry.pulse_all()
            time.sleep(interval)
    
    thread = threading.Thread(target=_beat, daemon=True, name="VAEL-heartbeat")
    thread.start()
    logger.info(f"Heartbeat started with interval {interval}s")
    return thread


def set_socketio(socketio) -> None:
    """Set the SocketIO instance for the registry and all entities.
    
    Args:
        socketio: Flask-SocketIO instance
    """
    registry.socketio = socketio
    for entity in registry._entities.values():
        entity.socketio = socketio
