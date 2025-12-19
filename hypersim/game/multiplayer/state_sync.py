"""State synchronization for multiplayer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, TYPE_CHECKING
import time

import numpy as np

if TYPE_CHECKING:
    from hypersim.game.ecs.world import World
    from hypersim.game.ecs.entity import Entity


@dataclass
class NetworkEntity:
    """Networked entity state for synchronization."""
    entity_id: str
    owner_id: int  # Player who owns/controls this entity
    position: np.ndarray = field(default_factory=lambda: np.zeros(4))
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(4))
    rotation: float = 0.0
    health: float = 100.0
    dimension: str = "1d"
    tags: Set[str] = field(default_factory=set)
    custom_state: Dict = field(default_factory=dict)
    
    # Sync metadata
    last_update: float = 0.0
    dirty: bool = False  # Needs to be sent
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "entity_id": self.entity_id,
            "owner_id": self.owner_id,
            "position": self.position.tolist(),
            "velocity": self.velocity.tolist(),
            "rotation": self.rotation,
            "health": self.health,
            "dimension": self.dimension,
            "tags": list(self.tags),
            "custom_state": self.custom_state,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "NetworkEntity":
        """Deserialize from dictionary."""
        return cls(
            entity_id=data["entity_id"],
            owner_id=data.get("owner_id", 0),
            position=np.array(data.get("position", [0, 0, 0, 0])),
            velocity=np.array(data.get("velocity", [0, 0, 0, 0])),
            rotation=data.get("rotation", 0.0),
            health=data.get("health", 100.0),
            dimension=data.get("dimension", "1d"),
            tags=set(data.get("tags", [])),
            custom_state=data.get("custom_state", {}),
        )


@dataclass
class WorldState:
    """Complete world state snapshot for sync."""
    tick: int = 0
    timestamp: float = 0.0
    entities: Dict[str, NetworkEntity] = field(default_factory=dict)
    events: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "tick": self.tick,
            "timestamp": self.timestamp,
            "entities": {eid: e.to_dict() for eid, e in self.entities.items()},
            "events": self.events,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "WorldState":
        """Deserialize from dictionary."""
        return cls(
            tick=data.get("tick", 0),
            timestamp=data.get("timestamp", 0.0),
            entities={
                eid: NetworkEntity.from_dict(edata)
                for eid, edata in data.get("entities", {}).items()
            },
            events=data.get("events", []),
        )


class StateSynchronizer:
    """Handles state synchronization between clients."""
    
    def __init__(self, is_authority: bool = False):
        self.is_authority = is_authority  # Server or host
        self.local_player_id: int = 0
        
        # State tracking
        self._local_state = WorldState()
        self._remote_state = WorldState()
        self._pending_inputs: List[Dict] = []
        
        # Network entities
        self._network_entities: Dict[str, NetworkEntity] = {}
        self._owned_entities: Set[str] = set()  # Entities we control
        
        # Sync settings
        self.sync_rate = 20  # Updates per second
        self.interpolation_delay = 0.1  # Seconds of delay for interpolation
        
        # Timing
        self._last_sync_time = 0.0
        self._sync_interval = 1.0 / self.sync_rate
        
        # Prediction/reconciliation
        self._input_sequence = 0
        self._last_acknowledged_input = 0
        self._input_history: List[Dict] = []
    
    def register_entity(
        self,
        entity_id: str,
        owner_id: int,
        is_owned: bool = False
    ) -> NetworkEntity:
        """Register an entity for network sync."""
        net_entity = NetworkEntity(
            entity_id=entity_id,
            owner_id=owner_id,
        )
        self._network_entities[entity_id] = net_entity
        
        if is_owned:
            self._owned_entities.add(entity_id)
        
        return net_entity
    
    def unregister_entity(self, entity_id: str) -> None:
        """Unregister an entity from network sync."""
        self._network_entities.pop(entity_id, None)
        self._owned_entities.discard(entity_id)
    
    def update_from_world(self, world: "World") -> None:
        """Update network state from game world."""
        from hypersim.game.ecs.component import Transform, Velocity, Health, DimensionAnchor
        
        for entity_id in self._owned_entities:
            entity = world.get(entity_id)
            if not entity:
                continue
            
            net_entity = self._network_entities.get(entity_id)
            if not net_entity:
                continue
            
            # Update from components
            transform = entity.get(Transform)
            if transform:
                if not np.array_equal(net_entity.position, transform.position):
                    net_entity.position = transform.position.copy()
                    net_entity.dirty = True
            
            velocity = entity.get(Velocity)
            if velocity:
                if not np.array_equal(net_entity.velocity, velocity.linear):
                    net_entity.velocity = velocity.linear.copy()
                    net_entity.dirty = True
            
            health = entity.get(Health)
            if health:
                if net_entity.health != health.current:
                    net_entity.health = health.current
                    net_entity.dirty = True
            
            anchor = entity.get(DimensionAnchor)
            if anchor:
                if net_entity.dimension != anchor.dimension_id:
                    net_entity.dimension = anchor.dimension_id
                    net_entity.dirty = True
    
    def apply_to_world(self, world: "World") -> None:
        """Apply network state to game world (for remote entities)."""
        from hypersim.game.ecs.component import Transform, Velocity, Health
        
        for entity_id, net_entity in self._network_entities.items():
            if entity_id in self._owned_entities:
                continue  # Don't overwrite our own entities
            
            entity = world.get(entity_id)
            if not entity:
                continue
            
            # Interpolate position
            transform = entity.get(Transform)
            if transform:
                # Simple lerp toward network position
                lerp_factor = 0.2
                transform.position = (
                    transform.position * (1 - lerp_factor) +
                    net_entity.position * lerp_factor
                )
            
            velocity = entity.get(Velocity)
            if velocity:
                velocity.linear = net_entity.velocity.copy()
            
            health = entity.get(Health)
            if health:
                health.current = net_entity.health
    
    def record_input(self, input_state: Dict) -> int:
        """Record local input for prediction/reconciliation."""
        self._input_sequence += 1
        
        input_record = {
            "sequence": self._input_sequence,
            "timestamp": time.time(),
            **input_state,
        }
        
        self._input_history.append(input_record)
        self._pending_inputs.append(input_record)
        
        # Limit history size
        max_history = int(self.sync_rate * 2)
        if len(self._input_history) > max_history:
            self._input_history = self._input_history[-max_history:]
        
        return self._input_sequence
    
    def acknowledge_input(self, sequence: int) -> None:
        """Server acknowledged an input up to this sequence."""
        self._last_acknowledged_input = sequence
        
        # Remove acknowledged inputs from pending
        self._pending_inputs = [
            inp for inp in self._pending_inputs
            if inp["sequence"] > sequence
        ]
    
    def get_dirty_entities(self) -> List[NetworkEntity]:
        """Get entities that need to be synced."""
        dirty = []
        for entity_id in self._owned_entities:
            net_entity = self._network_entities.get(entity_id)
            if net_entity and net_entity.dirty:
                dirty.append(net_entity)
                net_entity.dirty = False
                net_entity.last_update = time.time()
        return dirty
    
    def receive_state_update(self, state_data: Dict) -> None:
        """Receive state update from server/host."""
        for entity_id, entity_data in state_data.get("entities", {}).items():
            if entity_id in self._owned_entities:
                continue  # Don't apply to our entities
            
            if entity_id in self._network_entities:
                net_entity = self._network_entities[entity_id]
                net_entity.position = np.array(entity_data.get("position", [0, 0, 0, 0]))
                net_entity.velocity = np.array(entity_data.get("velocity", [0, 0, 0, 0]))
                net_entity.health = entity_data.get("health", 100)
                net_entity.dimension = entity_data.get("dimension", "1d")
            else:
                # New entity from network
                self._network_entities[entity_id] = NetworkEntity.from_dict(entity_data)
    
    def create_state_snapshot(self) -> WorldState:
        """Create a full state snapshot for sync."""
        self._local_state.tick += 1
        self._local_state.timestamp = time.time()
        self._local_state.entities = self._network_entities.copy()
        return self._local_state
    
    def should_sync(self) -> bool:
        """Check if enough time has passed for next sync."""
        now = time.time()
        if now - self._last_sync_time >= self._sync_interval:
            self._last_sync_time = now
            return True
        return False
