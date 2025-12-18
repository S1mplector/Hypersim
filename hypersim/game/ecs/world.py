"""World container managing entities and game events."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Type

from .component import Component, DimensionAnchor
from .entity import Entity
from .system import System, SystemGroup


@dataclass
class GameEvent:
    """Event emitted during gameplay for objective tracking and effects."""
    
    event_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    source_entity_id: Optional[str] = None


EventCallback = Callable[[GameEvent], None]


class World:
    """Container for all entities, systems, and game state."""
    
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.systems: SystemGroup = SystemGroup()
        self._pending_events: List[GameEvent] = []
        self._event_listeners: Dict[str, List[EventCallback]] = {}
        self._entities_by_tag: Dict[str, Set[str]] = {}
        self._entities_by_dimension: Dict[str, Set[str]] = {}
    
    # -------------------------------------------------------------------------
    # Entity management
    # -------------------------------------------------------------------------
    def spawn(self, entity: Entity) -> Entity:
        """Add an entity to the world."""
        self.entities[entity.id] = entity
        
        # Index by tags
        for tag in entity.tags:
            if tag not in self._entities_by_tag:
                self._entities_by_tag[tag] = set()
            self._entities_by_tag[tag].add(entity.id)
        
        # Index by dimension
        anchor = entity.get(DimensionAnchor)
        if anchor:
            dim = anchor.dimension_id
            if dim not in self._entities_by_dimension:
                self._entities_by_dimension[dim] = set()
            self._entities_by_dimension[dim].add(entity.id)
        
        self.systems.notify_entity_added(entity)
        return entity
    
    def despawn(self, entity_id: str) -> Optional[Entity]:
        """Remove an entity from the world."""
        entity = self.entities.pop(entity_id, None)
        if entity:
            # Remove from tag index
            for tag in entity.tags:
                if tag in self._entities_by_tag:
                    self._entities_by_tag[tag].discard(entity_id)
            
            # Remove from dimension index
            anchor = entity.get(DimensionAnchor)
            if anchor and anchor.dimension_id in self._entities_by_dimension:
                self._entities_by_dimension[anchor.dimension_id].discard(entity_id)
            
            self.systems.notify_entity_removed(entity)
        return entity
    
    def get(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID."""
        return self.entities.get(entity_id)
    
    def clear(self) -> None:
        """Remove all entities."""
        for entity_id in list(self.entities.keys()):
            self.despawn(entity_id)
    
    # -------------------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------------------
    def with_components(self, *component_types: Type[Component]) -> List[Entity]:
        """Get all active entities with the specified components."""
        return [
            e for e in self.entities.values()
            if e.active and e.has_all(*component_types)
        ]
    
    def with_tag(self, tag: str) -> List[Entity]:
        """Get all entities with a specific tag."""
        ids = self._entities_by_tag.get(tag, set())
        return [self.entities[eid] for eid in ids if eid in self.entities]
    
    def with_tags(self, *tags: str) -> List[Entity]:
        """Get all entities with all specified tags."""
        if not tags:
            return list(self.entities.values())
        result_ids = self._entities_by_tag.get(tags[0], set()).copy()
        for tag in tags[1:]:
            result_ids &= self._entities_by_tag.get(tag, set())
        return [self.entities[eid] for eid in result_ids if eid in self.entities]
    
    def in_dimension(self, dimension_id: str) -> List[Entity]:
        """Get all entities in a specific dimension."""
        ids = self._entities_by_dimension.get(dimension_id, set())
        return [self.entities[eid] for eid in ids if eid in self.entities]
    
    def find_player(self) -> Optional[Entity]:
        """Convenience method to find the player entity."""
        players = self.with_tag("player")
        return players[0] if players else None
    
    # -------------------------------------------------------------------------
    # Systems
    # -------------------------------------------------------------------------
    def add_system(self, system: System) -> None:
        """Add a system to the world."""
        self.systems.add(system)
    
    def remove_system(self, system_type: Type[System]) -> bool:
        """Remove a system by type."""
        return self.systems.remove(system_type)
    
    def update(self, dt: float) -> None:
        """Update all systems."""
        self.systems.update(self, dt)
    
    # -------------------------------------------------------------------------
    # Events
    # -------------------------------------------------------------------------
    def emit(self, event_type: str, source_entity_id: Optional[str] = None, **data) -> None:
        """Emit a game event for later processing."""
        event = GameEvent(event_type=event_type, data=data, source_entity_id=source_entity_id)
        self._pending_events.append(event)
        
        # Immediate notification to listeners
        if event_type in self._event_listeners:
            for callback in self._event_listeners[event_type]:
                callback(event)
    
    def drain_events(self) -> List[GameEvent]:
        """Get and clear all pending events."""
        events = self._pending_events
        self._pending_events = []
        return events
    
    def on_event(self, event_type: str, callback: EventCallback) -> None:
        """Register a callback for an event type."""
        if event_type not in self._event_listeners:
            self._event_listeners[event_type] = []
        self._event_listeners[event_type].append(callback)
    
    def off_event(self, event_type: str, callback: EventCallback) -> bool:
        """Unregister a callback. Returns True if removed."""
        if event_type not in self._event_listeners:
            return False
        try:
            self._event_listeners[event_type].remove(callback)
            return True
        except ValueError:
            return False
    
    # -------------------------------------------------------------------------
    # Iteration
    # -------------------------------------------------------------------------
    def __iter__(self) -> Iterator[Entity]:
        return iter(self.entities.values())
    
    def __len__(self) -> int:
        return len(self.entities)
    
    def __contains__(self, entity_id: str) -> bool:
        return entity_id in self.entities
