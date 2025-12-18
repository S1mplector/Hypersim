"""Entity class with component bag."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, Iterator, Optional, Set, Type, TypeVar

from .component import Component

C = TypeVar("C", bound=Component)


@dataclass
class Entity:
    """Game entity with attached components and tags."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    components: Dict[Type[Component], Component] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    active: bool = True
    
    def add(self, component: Component) -> "Entity":
        """Add a component to this entity. Returns self for chaining."""
        self.components[type(component)] = component
        return self
    
    def remove(self, component_type: Type[C]) -> Optional[C]:
        """Remove and return a component by type."""
        return self.components.pop(component_type, None)
    
    def get(self, component_type: Type[C]) -> Optional[C]:
        """Get a component by type, or None if not present."""
        return self.components.get(component_type)
    
    def has(self, component_type: Type[Component]) -> bool:
        """Check if entity has a component type."""
        return component_type in self.components
    
    def has_all(self, *component_types: Type[Component]) -> bool:
        """Check if entity has all specified component types."""
        return all(ct in self.components for ct in component_types)
    
    def has_any(self, *component_types: Type[Component]) -> bool:
        """Check if entity has any of the specified component types."""
        return any(ct in self.components for ct in component_types)
    
    def tag(self, *tags: str) -> "Entity":
        """Add tags to this entity. Returns self for chaining."""
        self.tags.update(tags)
        return self
    
    def untag(self, *tags: str) -> "Entity":
        """Remove tags from this entity. Returns self for chaining."""
        self.tags.difference_update(tags)
        return self
    
    def has_tag(self, tag: str) -> bool:
        """Check if entity has a specific tag."""
        return tag in self.tags
    
    def has_tags(self, *tags: str) -> bool:
        """Check if entity has all specified tags."""
        return all(t in self.tags for t in tags)
    
    def __iter__(self) -> Iterator[Component]:
        """Iterate over all components."""
        return iter(self.components.values())
    
    def __repr__(self) -> str:
        comp_names = [c.__class__.__name__ for c in self.components.values()]
        return f"Entity(id={self.id!r}, tags={self.tags}, components={comp_names})"


def create_entity(
    entity_id: Optional[str] = None,
    tags: Optional[Set[str]] = None,
    **components: Component,
) -> Entity:
    """Factory function to create an entity with components.
    
    Usage:
        entity = create_entity(
            entity_id="player",
            tags={"player", "controllable"},
            transform=Transform(position=np.array([0.0])),
            velocity=Velocity(),
            controller=Controller(),
        )
    """
    ent = Entity(
        id=entity_id or str(uuid.uuid4())[:8],
        tags=tags or set(),
    )
    for component in components.values():
        ent.add(component)
    return ent
