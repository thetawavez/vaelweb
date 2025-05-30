"""
VAEL Sentinel Core - Advanced Security Operations
-------------------------------------------------
This module extends the Sentinel entity with advanced security capabilities:
- Symbolic thread safety management
- Memory isolation enforcement
- Emergency response protocols
- Deep inspection of entity communications
- Security lockdown procedures

These core functions ensure the integrity and safety of the VAEL system
beyond basic rule-based threat detection.
"""

import os
import time
import logging
import threading
import json
import hashlib
import base64
from enum import Enum, auto
from typing import Dict, List, Set, Any, Optional, Callable, Tuple, Union
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Security levels for the VAEL system."""
    NORMAL = auto()       # Standard operations
    ELEVATED = auto()     # Heightened awareness
    HIGH = auto()         # Potential threat detected
    CRITICAL = auto()     # Active threat, emergency protocols
    LOCKDOWN = auto()     # Complete system isolation


class MemoryZone(Enum):
    """Memory isolation zones for entity operations."""
    PUBLIC = auto()       # Shared memory, accessible by all entities
    PROTECTED = auto()    # Limited access memory
    PRIVATE = auto()      # Entity-specific memory
    SECURE = auto()       # High-security memory for sensitive operations
    VAULT = auto()        # Encrypted storage for critical data


class EmergencyProtocol(Enum):
    """Emergency response protocols."""
    WATCHDOG_RESTART = auto()     # Trigger watchdog to restart affected components
    MEMORY_ISOLATION = auto()     # Isolate affected memory zones
    ENTITY_QUARANTINE = auto()    # Quarantine compromised entities
    SYSTEM_ROLLBACK = auto()      # Roll back to last known good state
    OPERATOR_ALERT = auto()       # Alert human operator
    FULL_LOCKDOWN = auto()        # Complete system shutdown and isolation


class ThreadGuard:
    """Ensures symbolic thread safety across entity operations.
    
    ThreadGuard prevents race conditions and deadlocks between symbolic
    entities by managing access to shared resources and enforcing
    thread safety protocols.
    """
    
    def __init__(self):
        """Initialize a new ThreadGuard."""
        self._locks: Dict[str, threading.RLock] = {}
        self._owners: Dict[str, str] = {}
        self._access_log: List[Dict[str, Any]] = []
        self._max_log_size = 1000
        self._global_lock = threading.RLock()
    
    def acquire(self, resource_id: str, entity_id: str, timeout: float = 5.0) -> bool:
        """Acquire a lock on a symbolic resource.
        
        Args:
            resource_id: Identifier for the resource
            entity_id: Identifier for the requesting entity
            timeout: Maximum time to wait for lock acquisition
            
        Returns:
            True if lock acquired, False otherwise
        """
        with self._global_lock:
            if resource_id not in self._locks:
                self._locks[resource_id] = threading.RLock()
        
        lock = self._locks[resource_id]
        acquired = lock.acquire(blocking=True, timeout=timeout)
        
        if acquired:
            with self._global_lock:
                self._owners[resource_id] = entity_id
                self._log_access(resource_id, entity_id, "acquire", True)
            return True
        else:
            self._log_access(resource_id, entity_id, "acquire", False)
            logger.warning(f"Entity {entity_id} failed to acquire lock on {resource_id}")
            return False
    
    def release(self, resource_id: str, entity_id: str) -> bool:
        """Release a lock on a symbolic resource.
        
        Args:
            resource_id: Identifier for the resource
            entity_id: Identifier for the releasing entity
            
        Returns:
            True if lock released, False otherwise
        """
        with self._global_lock:
            if resource_id not in self._locks:
                logger.warning(f"Entity {entity_id} tried to release non-existent lock on {resource_id}")
                return False
            
            if resource_id not in self._owners:
                logger.warning(f"Entity {entity_id} tried to release unowned lock on {resource_id}")
                return False
            
            if self._owners[resource_id] != entity_id:
                logger.error(
                    f"Entity {entity_id} tried to release lock on {resource_id} "
                    f"owned by {self._owners[resource_id]}"
                )
                return False
        
        try:
            self._locks[resource_id].release()
            with self._global_lock:
                del self._owners[resource_id]
                self._log_access(resource_id, entity_id, "release", True)
            return True
        except RuntimeError as e:
            logger.error(f"Error releasing lock on {resource_id}: {e}")
            self._log_access(resource_id, entity_id, "release", False, str(e))
            return False
    
    def _log_access(self, resource_id: str, entity_id: str, 
                   operation: str, success: bool, error: str = None) -> None:
        """Log resource access for auditing.
        
        Args:
            resource_id: Identifier for the resource
            entity_id: Identifier for the entity
            operation: Type of operation (acquire/release)
            success: Whether the operation succeeded
            error: Error message if operation failed
        """
        entry = {
            "timestamp": time.time(),
            "resource_id": resource_id,
            "entity_id": entity_id,
            "operation": operation,
            "success": success
        }
        
        if error:
            entry["error"] = error
        
        self._access_log.append(entry)
        
        # Trim log if it gets too large
        if len(self._access_log) > self._max_log_size:
            self._access_log = self._access_log[-self._max_log_size:]
    
    def get_resource_owner(self, resource_id: str) -> Optional[str]:
        """Get the current owner of a resource.
        
        Args:
            resource_id: Identifier for the resource
            
        Returns:
            Entity ID of the owner, or None if resource is not locked
        """
        with self._global_lock:
            return self._owners.get(resource_id)
    
    def list_locked_resources(self) -> Dict[str, str]:
        """List all currently locked resources and their owners.
        
        Returns:
            Dictionary mapping resource IDs to owner entity IDs
        """
        with self._global_lock:
            return self._owners.copy()
    
    def force_release(self, resource_id: str) -> bool:
        """Force release a lock in emergency situations.
        
        This should only be used in critical scenarios as it can
        lead to data corruption if the owning entity is mid-operation.
        
        Args:
            resource_id: Identifier for the resource
            
        Returns:
            True if lock was force-released, False otherwise
        """
        with self._global_lock:
            if resource_id not in self._locks:
                return False
            
            # Log this emergency operation
            owner = self._owners.get(resource_id, "unknown")
            logger.critical(f"Force releasing lock on {resource_id} owned by {owner}")
            
            try:
                # Attempt to release the lock
                self._locks[resource_id] = threading.RLock()  # Replace with new lock
                if resource_id in self._owners:
                    del self._owners[resource_id]
                return True
            except Exception as e:
                logger.error(f"Failed to force release lock on {resource_id}: {e}")
                return False
    
    def detect_deadlocks(self) -> List[Dict[str, Any]]:
        """Detect potential deadlocks in the system.
        
        Returns:
            List of potential deadlock scenarios
        """
        # This is a simplified deadlock detection algorithm
        # In a real system, this would be more sophisticated
        deadlocks = []
        
        # Look for entities waiting on resources for too long
        current_time = time.time()
        with self._global_lock:
            for entry in reversed(self._access_log):
                if entry["operation"] == "acquire" and not entry["success"]:
                    # Check if this resource is still locked
                    resource_id = entry["resource_id"]
                    if resource_id in self._owners:
                        # This is a potential deadlock
                        deadlock = {
                            "waiting_entity": entry["entity_id"],
                            "resource_id": resource_id,
                            "owner_entity": self._owners[resource_id],
                            "waiting_since": entry["timestamp"],
                            "waiting_time": current_time - entry["timestamp"]
                        }
                        deadlocks.append(deadlock)
        
        return deadlocks


class MemoryIsolation:
    """Enforces memory isolation between entities.
    
    MemoryIsolation prevents unauthorized access to memory zones,
    enforces access controls, and detects memory isolation violations.
    """
    
    def __init__(self):
        """Initialize a new MemoryIsolation manager."""
        self._zones: Dict[MemoryZone, Dict[str, Any]] = {
            zone: {} for zone in MemoryZone
        }
        self._permissions: Dict[str, Set[MemoryZone]] = {}
        self._access_log: List[Dict[str, Any]] = []
        self._max_log_size = 1000
        self._lock = threading.RLock()
    
    def grant_permission(self, entity_id: str, zone: MemoryZone) -> bool:
        """Grant an entity permission to access a memory zone.
        
        Args:
            entity_id: Identifier for the entity
            zone: Memory zone to grant access to
            
        Returns:
            True if permission granted, False otherwise
        """
        with self._lock:
            if entity_id not in self._permissions:
                self._permissions[entity_id] = set()
            
            self._permissions[entity_id].add(zone)
            logger.info(f"Granted {entity_id} access to {zone.name} memory zone")
            return True
    
    def revoke_permission(self, entity_id: str, zone: MemoryZone) -> bool:
        """Revoke an entity's permission to access a memory zone.
        
        Args:
            entity_id: Identifier for the entity
            zone: Memory zone to revoke access from
            
        Returns:
            True if permission revoked, False otherwise
        """
        with self._lock:
            if entity_id not in self._permissions:
                return False
            
            if zone in self._permissions[entity_id]:
                self._permissions[entity_id].remove(zone)
                logger.info(f"Revoked {entity_id} access to {zone.name} memory zone")
                return True
            
            return False
    
    def has_permission(self, entity_id: str, zone: MemoryZone) -> bool:
        """Check if an entity has permission to access a memory zone.
        
        Args:
            entity_id: Identifier for the entity
            zone: Memory zone to check access for
            
        Returns:
            True if entity has permission, False otherwise
        """
        with self._lock:
            if entity_id not in self._permissions:
                return False
            
            return zone in self._permissions[entity_id]
    
    def write(self, entity_id: str, zone: MemoryZone, key: str, value: Any) -> bool:
        """Write data to a memory zone.
        
        Args:
            entity_id: Identifier for the writing entity
            zone: Memory zone to write to
            key: Key for the data
            value: Data to write
            
        Returns:
            True if write succeeded, False otherwise
        """
        if not self.has_permission(entity_id, zone):
            self._log_access(entity_id, zone, key, "write", False, "Permission denied")
            logger.warning(f"Entity {entity_id} denied write access to {zone.name}/{key}")
            return False
        
        with self._lock:
            self._zones[zone][key] = value
            self._log_access(entity_id, zone, key, "write", True)
            return True
    
    def read(self, entity_id: str, zone: MemoryZone, key: str) -> Tuple[bool, Any]:
        """Read data from a memory zone.
        
        Args:
            entity_id: Identifier for the reading entity
            zone: Memory zone to read from
            key: Key for the data
            
        Returns:
            Tuple of (success, value) where success is True if read succeeded
        """
        if not self.has_permission(entity_id, zone):
            self._log_access(entity_id, zone, key, "read", False, "Permission denied")
            logger.warning(f"Entity {entity_id} denied read access to {zone.name}/{key}")
            return False, None
        
        with self._lock:
            if key not in self._zones[zone]:
                self._log_access(entity_id, zone, key, "read", False, "Key not found")
                return False, None
            
            value = self._zones[zone][key]
            self._log_access(entity_id, zone, key, "read", True)
            return True, value
    
    def delete(self, entity_id: str, zone: MemoryZone, key: str) -> bool:
        """Delete data from a memory zone.
        
        Args:
            entity_id: Identifier for the deleting entity
            zone: Memory zone to delete from
            key: Key for the data to delete
            
        Returns:
            True if delete succeeded, False otherwise
        """
        if not self.has_permission(entity_id, zone):
            self._log_access(entity_id, zone, key, "delete", False, "Permission denied")
            logger.warning(f"Entity {entity_id} denied delete access to {zone.name}/{key}")
            return False
        
        with self._lock:
            if key not in self._zones[zone]:
                self._log_access(entity_id, zone, key, "delete", False, "Key not found")
                return False
            
            del self._zones[zone][key]
            self._log_access(entity_id, zone, key, "delete", True)
            return True
    
    def _log_access(self, entity_id: str, zone: MemoryZone, key: str,
                   operation: str, success: bool, error: str = None) -> None:
        """Log memory access for auditing.
        
        Args:
            entity_id: Identifier for the entity
            zone: Memory zone accessed
            key: Key accessed
            operation: Type of operation (read/write/delete)
            success: Whether the operation succeeded
            error: Error message if operation failed
        """
        entry = {
            "timestamp": time.time(),
            "entity_id": entity_id,
            "zone": zone.name,
            "key": key,
            "operation": operation,
            "success": success
        }
        
        if error:
            entry["error"] = error
        
        with self._lock:
            self._access_log.append(entry)
            
            # Trim log if it gets too large
            if len(self._access_log) > self._max_log_size:
                self._access_log = self._access_log[-self._max_log_size:]
    
    def secure_store(self, entity_id: str, key: str, value: Any, 
                    passphrase: str) -> bool:
        """Store data in the SECURE memory zone with encryption.
        
        Args:
            entity_id: Identifier for the storing entity
            key: Key for the data
            value: Data to store
            passphrase: Encryption passphrase
            
        Returns:
            True if storage succeeded, False otherwise
        """
        if not self.has_permission(entity_id, MemoryZone.SECURE):
            logger.warning(f"Entity {entity_id} denied secure store access")
            return False
        
        try:
            # Simple encryption for demonstration
            # In a real system, this would use proper cryptography
            value_str = json.dumps(value)
            hash_key = hashlib.sha256(passphrase.encode()).digest()
            encoded = base64.b64encode(value_str.encode()).decode()
            
            # Store with metadata
            secure_value = {
                "data": encoded,
                "hash": hashlib.sha256(value_str.encode()).hexdigest(),
                "created_at": time.time(),
                "created_by": entity_id
            }
            
            return self.write(entity_id, MemoryZone.SECURE, key, secure_value)
        except Exception as e:
            logger.error(f"Secure store failed: {e}")
            return False
    
    def secure_retrieve(self, entity_id: str, key: str, 
                       passphrase: str) -> Tuple[bool, Any]:
        """Retrieve data from the SECURE memory zone with decryption.
        
        Args:
            entity_id: Identifier for the retrieving entity
            key: Key for the data
            passphrase: Decryption passphrase
            
        Returns:
            Tuple of (success, value) where success is True if retrieval succeeded
        """
        if not self.has_permission(entity_id, MemoryZone.SECURE):
            logger.warning(f"Entity {entity_id} denied secure retrieve access")
            return False, None
        
        try:
            success, secure_value = self.read(entity_id, MemoryZone.SECURE, key)
            if not success or not secure_value:
                return False, None
            
            # Simple decryption for demonstration
            encoded = secure_value["data"]
            decoded = base64.b64decode(encoded.encode()).decode()
            
            # Verify hash
            computed_hash = hashlib.sha256(decoded.encode()).hexdigest()
            if computed_hash != secure_value["hash"]:
                logger.error(f"Secure retrieve failed: hash mismatch for {key}")
                return False, None
            
            return True, json.loads(decoded)
        except Exception as e:
            logger.error(f"Secure retrieve failed: {e}")
            return False, None
    
    def list_keys(self, entity_id: str, zone: MemoryZone) -> List[str]:
        """List all keys in a memory zone.
        
        Args:
            entity_id: Identifier for the entity
            zone: Memory zone to list keys from
            
        Returns:
            List of keys in the zone
        """
        if not self.has_permission(entity_id, zone):
            logger.warning(f"Entity {entity_id} denied list access to {zone.name}")
            return []
        
        with self._lock:
            return list(self._zones[zone].keys())
    
    def isolate_zone(self, zone: MemoryZone) -> bool:
        """Isolate a memory zone by revoking all permissions.
        
        Args:
            zone: Memory zone to isolate
            
        Returns:
            True if isolation succeeded, False otherwise
        """
        with self._lock:
            for entity_id in list(self._permissions.keys()):
                if zone in self._permissions[entity_id]:
                    self._permissions[entity_id].remove(zone)
            
            logger.warning(f"Memory zone {zone.name} isolated - all permissions revoked")
            return True
    
    def clear_zone(self, zone: MemoryZone) -> bool:
        """Clear all data from a memory zone.
        
        Args:
            zone: Memory zone to clear
            
        Returns:
            True if clearing succeeded, False otherwise
        """
        with self._lock:
            self._zones[zone] = {}
            logger.warning(f"Memory zone {zone.name} cleared")
            return True
    
    def backup_zone(self, zone: MemoryZone, file_path: str) -> bool:
        """Backup a memory zone to a file.
        
        Args:
            zone: Memory zone to backup
            file_path: Path to save the backup
            
        Returns:
            True if backup succeeded, False otherwise
        """
        try:
            with self._lock:
                zone_data = self._zones[zone]
            
            with open(file_path, 'w') as f:
                json.dump(zone_data, f, indent=2)
            
            logger.info(f"Memory zone {zone.name} backed up to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup memory zone {zone.name}: {e}")
            return False
    
    def restore_zone(self, zone: MemoryZone, file_path: str) -> bool:
        """Restore a memory zone from a backup file.
        
        Args:
            zone: Memory zone to restore
            file_path: Path to the backup file
            
        Returns:
            True if restore succeeded, False otherwise
        """
        try:
            with open(file_path, 'r') as f:
                zone_data = json.load(f)
            
            with self._lock:
                self._zones[zone] = zone_data
            
            logger.info(f"Memory zone {zone.name} restored from {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore memory zone {zone.name}: {e}")
            return False


class EmergencyResponse:
    """Manages emergency response protocols for critical security events.
    
    EmergencyResponse provides mechanisms for responding to security
    incidents, isolating compromised components, and recovering system
    integrity.
    """
    
    def __init__(self, socketio=None):
        """Initialize a new EmergencyResponse manager.
        
        Args:
            socketio: Flask-SocketIO instance for emitting events
        """
        self._socketio = socketio
        self._current_level = SecurityLevel.NORMAL
        self._active_protocols: Dict[EmergencyProtocol, Dict[str, Any]] = {}
        self._incident_log: List[Dict[str, Any]] = []
        self._max_log_size = 1000
        self._handlers: Dict[EmergencyProtocol, List[Callable]] = {
            protocol: [] for protocol in EmergencyProtocol
        }
        self._lock = threading.RLock()
    
    def set_security_level(self, level: SecurityLevel) -> bool:
        """Set the current security level.
        
        Args:
            level: New security level
            
        Returns:
            True if level was set, False otherwise
        """
        with self._lock:
            old_level = self._current_level
            self._current_level = level
            
            # Log the level change
            self._log_incident(
                "security_level_change",
                f"Security level changed from {old_level.name} to {level.name}",
                severity=level.value
            )
            
            # Emit event if socketio is available
            if self._socketio:
                self._socketio.emit('security_level_change', {
                    'old_level': old_level.name,
                    'new_level': level.name,
                    'timestamp': time.time()
                })
            
            logger.warning(f"Security level changed from {old_level.name} to {level.name}")
            return True
    
    def get_security_level(self) -> SecurityLevel:
        """Get the current security level.
        
        Returns:
            Current security level
        """
        return self._current_level
    
    def activate_protocol(self, protocol: EmergencyProtocol, 
                         reason: str, data: Dict[str, Any] = None) -> bool:
        """Activate an emergency response protocol.
        
        Args:
            protocol: Protocol to activate
            reason: Reason for activation
            data: Additional data for the protocol
            
        Returns:
            True if protocol was activated, False otherwise
        """
        with self._lock:
            # Check if protocol is already active
            if protocol in self._active_protocols:
                logger.warning(f"Protocol {protocol.name} is already active")
                return False
            
            # Create protocol activation record
            activation = {
                "protocol": protocol,
                "reason": reason,
                "activated_at": time.time(),
                "data": data or {},
                "status": "active"
            }
            
            self._active_protocols[protocol] = activation
            
            # Log the activation
            self._log_incident(
                "protocol_activation",
                f"Emergency protocol {protocol.name} activated: {reason}",
                severity=SecurityLevel.HIGH.value,
                protocol=protocol.name,
                data=data
            )
            
            # Emit event if socketio is available
            if self._socketio:
                self._socketio.emit('emergency_protocol', {
                    'action': 'activated',
                    'protocol': protocol.name,
                    'reason': reason,
                    'timestamp': time.time()
                })
            
            logger.critical(f"Emergency protocol {protocol.name} activated: {reason}")
            
            # Execute protocol handlers
            self._execute_protocol_handlers(protocol, activation)
            
            return True
    
    def deactivate_protocol(self, protocol: EmergencyProtocol, 
                           reason: str = None) -> bool:
        """Deactivate an emergency response protocol.
        
        Args:
            protocol: Protocol to deactivate
            reason: Reason for deactivation
            
        Returns:
            True if protocol was deactivated, False otherwise
        """
        with self._lock:
            # Check if protocol is active
            if protocol not in self._active_protocols:
                logger.warning(f"Protocol {protocol.name} is not active")
                return False
            
            # Update protocol record
            activation = self._active_protocols[protocol]
            activation["status"] = "deactivated"
            activation["deactivated_at"] = time.time()
            activation["deactivation_reason"] = reason or "Manual deactivation"
            
            # Remove from active protocols
            del self._active_protocols[protocol]
            
            # Log the deactivation
            self._log_incident(
                "protocol_deactivation",
                f"Emergency protocol {protocol.name} deactivated: {reason or 'Manual deactivation'}",
                severity=SecurityLevel.ELEVATED.value,
                protocol=protocol.name
            )
            
            # Emit event if socketio is available
            if self._socketio:
                self._socketio.emit('emergency_protocol', {
                    'action': 'deactivated',
                    'protocol': protocol.name,
                    'reason': reason or "Manual deactivation",
                    'timestamp': time.time()
                })
            
            logger.warning(f"Emergency protocol {protocol.name} deactivated: {reason or 'Manual deactivation'}")
            
            return True
    
    def is_protocol_active(self, protocol: EmergencyProtocol) -> bool:
        """Check if an emergency protocol is currently active.
        
        Args:
            protocol: Protocol to check
            
        Returns:
            True if protocol is active, False otherwise
        """
        return protocol in self._active_protocols
    
    def list_active_protocols(self) -> List[Dict[str, Any]]:
        """List all currently active emergency protocols.
        
        Returns:
            List of active protocol details
        """
        with self._lock:
            return [
                {
                    "protocol": p.name,
                    "reason": details["reason"],
                    "activated_at": details["activated_at"],
                    "data": details["data"]
                }
                for p, details in self._active_protocols.items()
            ]
    
    def register_protocol_handler(self, protocol: EmergencyProtocol, 
                                 handler: Callable) -> bool:
        """Register a handler function for an emergency protocol.
        
        Args:
            protocol: Protocol to handle
            handler: Handler function
            
        Returns:
            True if handler was registered, False otherwise
        """
        with self._lock:
            if protocol not in self._handlers:
                self._handlers[protocol] = []
            
            self._handlers[protocol].append(handler)
            logger.info(f"Registered handler for protocol {protocol.name}")
            return True
    
    def _execute_protocol_handlers(self, protocol: EmergencyProtocol, 
                                  activation: Dict[str, Any]) -> None:
        """Execute all handlers for a protocol.
        
        Args:
            protocol: Protocol being activated
            activation: Activation details
        """
        if protocol not in self._handlers:
            return
        
        for handler in self._handlers[protocol]:
            try:
                handler(activation)
            except Exception as e:
                logger.error(f"Error in protocol handler for {protocol.name}: {e}")
    
    def _log_incident(self, incident_type: str, description: str, 
                     severity: int = 0, **kwargs) -> None:
        """Log a security incident.
        
        Args:
            incident_type: Type of incident
            description: Description of the incident
            severity: Severity level (0-5)
            **kwargs: Additional incident details
        """
        incident = {
            "timestamp": time.time(),
            "type": incident_type,
            "description": description,
            "severity": severity
        }
        
        # Add any additional details
        incident.update(kwargs)
        
        with self._lock:
            self._incident_log.append(incident)
            
            # Trim log if it gets too large
            if len(self._incident_log) > self._max_log_size:
                self._incident_log = self._incident_log[-self._max_log_size:]
    
    def get_incident_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get the security incident log.
        
        Args:
            limit: Maximum number of incidents to return
            
        Returns:
            List of incident records
        """
        with self._lock:
            return sorted(
                self._incident_log[-limit:],
                key=lambda x: x["timestamp"],
                reverse=True
            )
    
    def system_lockdown(self, reason: str, 
                       duration: int = 300) -> bool:
        """Initiate a full system lockdown.
        
        This is the most severe emergency response, isolating all
        system components and requiring operator intervention.
        
        Args:
            reason: Reason for the lockdown
            duration: Duration in seconds (0 for indefinite)
            
        Returns:
            True if lockdown was initiated, False otherwise
        """
        # Set security level to LOCKDOWN
        self.set_security_level(SecurityLevel.LOCKDOWN)
        
        # Activate FULL_LOCKDOWN protocol
        self.activate_protocol(
            EmergencyProtocol.FULL_LOCKDOWN,
            reason,
            {"duration": duration}
        )
        
        # Log the lockdown
        self._log_incident(
            "system_lockdown",
            f"System lockdown initiated: {reason}",
            severity=SecurityLevel.LOCKDOWN.value,
            duration=duration
        )
        
        # Emit event if socketio is available
        if self._socketio:
            self._socketio.emit('system_lockdown', {
                'reason': reason,
                'duration': duration,
                'timestamp': time.time()
            })
        
        logger.critical(f"SYSTEM LOCKDOWN INITIATED: {reason}")
        
        # If duration is not indefinite, schedule automatic release
        if duration > 0:
            def release_lockdown():
                time.sleep(duration)
                self.release_lockdown("Automatic release after timeout")
            
            threading.Thread(target=release_lockdown, daemon=True).start()
        
        return True
    
    def release_lockdown(self, reason: str) -> bool:
        """Release a system lockdown.
        
        Args:
            reason: Reason for releasing the lockdown
            
        Returns:
            True if lockdown was released, False otherwise
        """
        # Check if we're actually in lockdown
        if self._current_level != SecurityLevel.LOCKDOWN:
            logger.warning("Attempted to release lockdown when not in lockdown state")
            return False
        
        # Set security level to HIGH (still elevated, but operational)
        self.set_security_level(SecurityLevel.HIGH)
        
        # Deactivate FULL_LOCKDOWN protocol
        if self.is_protocol_active(EmergencyProtocol.FULL_LOCKDOWN):
            self.deactivate_protocol(EmergencyProtocol.FULL_LOCKDOWN, reason)
        
        # Log the release
        self._log_incident(
            "lockdown_release",
            f"System lockdown released: {reason}",
            severity=SecurityLevel.HIGH.value
        )
        
        # Emit event if socketio is available
        if self._socketio:
            self._socketio.emit('lockdown_release', {
                'reason': reason,
                'timestamp': time.time()
            })
        
        logger.warning(f"System lockdown released: {reason}")
        
        return True
    
    def generate_incident_report(self, start_time: float = None, 
                               end_time: float = None) -> Dict[str, Any]:
        """Generate a comprehensive incident report.
        
        Args:
            start_time: Start time for the report (Unix timestamp)
            end_time: End time for the report (Unix timestamp)
            
        Returns:
            Incident report data
        """
        start_time = start_time or 0
        end_time = end_time or time.time()
        
        with self._lock:
            # Filter incidents by time range
            incidents = [
                inc for inc in self._incident_log
                if start_time <= inc["timestamp"] <= end_time
            ]
            
            # Count incidents by type
            incident_types = {}
            for inc in incidents:
                inc_type = inc["type"]
                if inc_type not in incident_types:
                    incident_types[inc_type] = 0
                incident_types[inc_type] += 1
            
            # Count incidents by severity
            severity_counts = {}
            for inc in incidents:
                severity = inc["severity"]
                if severity not in severity_counts:
                    severity_counts[severity] = 0
                severity_counts[severity] += 1
            
            # Generate report
            report = {
                "generated_at": time.time(),
                "start_time": start_time,
                "end_time": end_time,
                "total_incidents": len(incidents),
                "incident_types": incident_types,
                "severity_counts": severity_counts,
                "highest_severity": max([inc["severity"] for inc in incidents]) if incidents else 0,
                "protocols_activated": [
                    inc for inc in incidents
                    if inc["type"] == "protocol_activation"
                ],
                "security_level_changes": [
                    inc for inc in incidents
                    if inc["type"] == "security_level_change"
                ],
                "lockdowns": [
                    inc for inc in incidents
                    if inc["type"] in ["system_lockdown", "lockdown_release"]
                ]
            }
            
            return report


# Singleton instances for global use
thread_guard = ThreadGuard()
memory_isolation = MemoryIsolation()
emergency_response = None  # Initialized with socketio in create_emergency_response()


def create_emergency_response(socketio) -> EmergencyResponse:
    """Create and initialize the emergency response system.
    
    Args:
        socketio: Flask-SocketIO instance
        
    Returns:
        Initialized EmergencyResponse instance
    """
    global emergency_response
    emergency_response = EmergencyResponse(socketio)
    
    # Register default protocol handlers
    emergency_response.register_protocol_handler(
        EmergencyProtocol.OPERATOR_ALERT,
        lambda activation: socketio.emit('operator_alert', {
            'reason': activation['reason'],
            'data': activation['data'],
            'timestamp': activation['activated_at']
        })
    )
    
    logger.info("Emergency response system initialized")
    return emergency_response


def get_emergency_response() -> Optional[EmergencyResponse]:
    """Get the global emergency response instance.
    
    Returns:
        EmergencyResponse instance or None if not initialized
    """
    return emergency_response


def symbolic_thread_safety(resource_id: str, entity_id: str):
    """Decorator for ensuring symbolic thread safety.
    
    Args:
        resource_id: Identifier for the resource
        entity_id: Identifier for the entity
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            acquired = thread_guard.acquire(resource_id, entity_id)
            if not acquired:
                logger.error(f"Failed to acquire lock on {resource_id} for {entity_id}")
                return None
            
            try:
                return func(*args, **kwargs)
            finally:
                thread_guard.release(resource_id, entity_id)
        
        return wrapper
    
    return decorator
