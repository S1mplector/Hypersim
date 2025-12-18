"""System base class and common systems."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Tuple, Type

from .component import Component

if TYPE_CHECKING:
    from .entity import Entity
    from .world import World


class System(ABC):
    """Base class for all systems. Override update() to implement logic."""
    
    priority: int = 0
    required_components: Tuple[Type[Component], ...] = ()
    
    @abstractmethod
    def update(self, world: "World", dt: float) -> None:
        """Process entities each frame.
        
        Args:
            world: The game world containing entities
            dt: Delta time in seconds since last update
        """
        pass
    
    def query(self, world: "World") -> List["Entity"]:
        """Get all entities matching this system's required components."""
        if not self.required_components:
            return list(world.entities.values())
        return [
            e for e in world.entities.values()
            if e.active and e.has_all(*self.required_components)
        ]
    
    def on_entity_added(self, entity: "Entity") -> None:
        """Called when an entity is added to the world."""
        pass
    
    def on_entity_removed(self, entity: "Entity") -> None:
        """Called when an entity is removed from the world."""
        pass


class SystemGroup:
    """Ordered collection of systems that execute together."""
    
    def __init__(self, name: str = "default"):
        self.name = name
        self._systems: List[System] = []
        self._sorted = True
    
    def add(self, system: System) -> None:
        """Add a system to the group."""
        self._systems.append(system)
        self._sorted = False
    
    def remove(self, system_type: Type[System]) -> bool:
        """Remove a system by type. Returns True if removed."""
        for i, sys in enumerate(self._systems):
            if isinstance(sys, system_type):
                del self._systems[i]
                return True
        return False
    
    def get(self, system_type: Type[System]) -> System | None:
        """Get a system by type."""
        for sys in self._systems:
            if isinstance(sys, system_type):
                return sys
        return None
    
    def update(self, world: "World", dt: float) -> None:
        """Update all systems in priority order."""
        if not self._sorted:
            self._systems.sort(key=lambda s: s.priority)
            self._sorted = True
        for system in self._systems:
            system.update(world, dt)
    
    def notify_entity_added(self, entity: "Entity") -> None:
        """Notify all systems of a new entity."""
        for system in self._systems:
            system.on_entity_added(entity)
    
    def notify_entity_removed(self, entity: "Entity") -> None:
        """Notify all systems of entity removal."""
        for system in self._systems:
            system.on_entity_removed(entity)
    
    def __iter__(self):
        return iter(self._systems)
    
    def __len__(self):
        return len(self._systems)
