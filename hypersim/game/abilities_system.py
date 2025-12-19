"""Ability effects system - implements actual ability behaviors."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from hypersim.game.ecs.entity import Entity
    from hypersim.game.ecs.world import World
    from hypersim.game.session import GameSession


class AbilityTargetType(Enum):
    """How an ability selects its target."""
    SELF = "self"
    POINT = "point"
    DIRECTION = "direction"
    ENTITY = "entity"
    AREA = "area"


@dataclass
class AbilityDef:
    """Definition for an ability."""
    id: str
    name: str
    description: str = ""
    dimension_req: Optional[str] = None  # None = usable in any dimension
    min_dimension_order: int = 0  # Minimum dimension order to use
    cooldown: float = 1.0  # Seconds
    cost: float = 0.0  # Energy/mana cost
    target_type: AbilityTargetType = AbilityTargetType.SELF
    range: float = 10.0  # For targeted abilities
    duration: float = 0.0  # For effects with duration
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AbilityInstance:
    """Runtime state for an ability."""
    definition: AbilityDef
    cooldown_remaining: float = 0.0
    active: bool = False
    active_timer: float = 0.0
    
    @property
    def is_ready(self) -> bool:
        return self.cooldown_remaining <= 0
    
    def trigger_cooldown(self) -> None:
        self.cooldown_remaining = self.definition.cooldown
    
    def tick(self, dt: float) -> None:
        if self.cooldown_remaining > 0:
            self.cooldown_remaining = max(0, self.cooldown_remaining - dt)
        if self.active:
            self.active_timer -= dt
            if self.active_timer <= 0:
                self.active = False


# Effect function signature: (entity, world, session, ability_def, **kwargs) -> bool
EffectFunction = Callable[["Entity", "World", "GameSession", AbilityDef], bool]


class AbilitySystem:
    """Manages ability execution and effects."""
    
    def __init__(self):
        self._definitions: Dict[str, AbilityDef] = {}
        self._effects: Dict[str, EffectFunction] = {}
        self._instances: Dict[str, Dict[str, AbilityInstance]] = {}  # entity_id -> ability_id -> instance
        
        # Register built-in abilities
        self._register_builtin_abilities()
    
    def _register_builtin_abilities(self) -> None:
        """Register all built-in ability definitions and effects."""
        
        # 1D Abilities
        self.register(
            AbilityDef(
                id="ping_neighbors",
                name="Ping Neighbors",
                description="Reveal entities within range for a brief moment.",
                dimension_req="1d",
                cooldown=3.0,
                duration=2.0,
                params={"radius": 15.0},
            ),
            self._effect_ping_neighbors
        )
        
        # 2D Abilities
        self.register(
            AbilityDef(
                id="fold_line",
                name="Fold Line",
                description="Teleport a 1D entity to a new position on the line.",
                min_dimension_order=1,
                cooldown=5.0,
                target_type=AbilityTargetType.ENTITY,
                range=20.0,
                params={"teleport_distance": 10.0},
            ),
            self._effect_fold_line
        )
        
        self.register(
            AbilityDef(
                id="sketch_path",
                name="Sketch Path",
                description="Draw a temporary wall that blocks enemies.",
                dimension_req="2d",
                cooldown=8.0,
                duration=5.0,
                target_type=AbilityTargetType.DIRECTION,
                params={"length": 5.0},
            ),
            self._effect_sketch_path
        )
        
        # 3D Abilities
        self.register(
            AbilityDef(
                id="slice_plane",
                name="Slice Plane",
                description="View a cross-section of 3D space at a chosen height.",
                min_dimension_order=2,
                cooldown=2.0,
                duration=3.0,
                target_type=AbilityTargetType.SELF,
            ),
            self._effect_slice_plane
        )
        
        self.register(
            AbilityDef(
                id="carry_line",
                name="Carry Line Being",
                description="Pick up and relocate a 1D entity.",
                min_dimension_order=2,
                cooldown=10.0,
                target_type=AbilityTargetType.ENTITY,
                range=5.0,
            ),
            self._effect_carry_line
        )
        
        # 4D Abilities
        self.register(
            AbilityDef(
                id="rotate_hyperplanes",
                name="Rotate Hyperplanes",
                description="Rotate 4D objects to reveal hidden geometry.",
                dimension_req="4d",
                cooldown=1.0,
                target_type=AbilityTargetType.SELF,
                params={"rotation_speed": 1.0},
            ),
            self._effect_rotate_hyperplanes
        )
        
        self.register(
            AbilityDef(
                id="spawn_slices",
                name="Spawn Slices",
                description="Create 3D cross-section objects from 4D geometry.",
                dimension_req="4d",
                cooldown=15.0,
                duration=10.0,
                target_type=AbilityTargetType.POINT,
                range=15.0,
            ),
            self._effect_spawn_slices
        )
        
        self.register(
            AbilityDef(
                id="stabilize_lower",
                name="Stabilize Lower Dimension",
                description="Freeze time in a lower dimension briefly.",
                dimension_req="4d",
                cooldown=20.0,
                duration=5.0,
                target_type=AbilityTargetType.SELF,
                params={"target_dimension": "3d"},
            ),
            self._effect_stabilize_lower
        )
        
        # Universal abilities
        self.register(
            AbilityDef(
                id="dash",
                name="Dash",
                description="Quick burst of speed in movement direction.",
                cooldown=2.0,
                duration=0.2,
                target_type=AbilityTargetType.DIRECTION,
                params={"speed_multiplier": 3.0},
            ),
            self._effect_dash
        )
    
    def register(self, definition: AbilityDef, effect: EffectFunction) -> None:
        """Register an ability definition and its effect function."""
        self._definitions[definition.id] = definition
        self._effects[definition.id] = effect
    
    def get_definition(self, ability_id: str) -> Optional[AbilityDef]:
        """Get an ability definition by ID."""
        return self._definitions.get(ability_id)
    
    def grant_ability(self, entity_id: str, ability_id: str) -> bool:
        """Grant an ability to an entity."""
        if ability_id not in self._definitions:
            return False
        
        if entity_id not in self._instances:
            self._instances[entity_id] = {}
        
        if ability_id not in self._instances[entity_id]:
            self._instances[entity_id][ability_id] = AbilityInstance(
                definition=self._definitions[ability_id]
            )
        
        return True
    
    def has_ability(self, entity_id: str, ability_id: str) -> bool:
        """Check if an entity has an ability."""
        return (
            entity_id in self._instances and
            ability_id in self._instances[entity_id]
        )
    
    def can_use(
        self,
        entity_id: str,
        ability_id: str,
        current_dimension: str,
        dimension_order: int,
    ) -> bool:
        """Check if an entity can currently use an ability."""
        if not self.has_ability(entity_id, ability_id):
            return False
        
        instance = self._instances[entity_id][ability_id]
        definition = instance.definition
        
        if not instance.is_ready:
            return False
        
        # Check dimension requirements
        if definition.dimension_req and definition.dimension_req != current_dimension:
            return False
        
        if dimension_order < definition.min_dimension_order:
            return False
        
        return True
    
    def use_ability(
        self,
        entity: "Entity",
        ability_id: str,
        world: "World",
        session: "GameSession",
        **kwargs
    ) -> bool:
        """Attempt to use an ability. Returns True if successful."""
        entity_id = entity.id
        
        if not self.has_ability(entity_id, ability_id):
            return False
        
        instance = self._instances[entity_id][ability_id]
        
        if not instance.is_ready:
            return False
        
        # Get effect function
        effect_fn = self._effects.get(ability_id)
        if not effect_fn:
            return False
        
        # Execute effect
        success = effect_fn(entity, world, session, instance.definition, **kwargs)
        
        if success:
            instance.trigger_cooldown()
            if instance.definition.duration > 0:
                instance.active = True
                instance.active_timer = instance.definition.duration
            
            world.emit(
                "ability_used",
                entity_id=entity_id,
                ability_id=ability_id,
            )
        
        return success
    
    def tick(self, dt: float) -> None:
        """Update all ability cooldowns and active effects."""
        for entity_instances in self._instances.values():
            for instance in entity_instances.values():
                instance.tick(dt)
    
    def get_cooldown(self, entity_id: str, ability_id: str) -> float:
        """Get remaining cooldown for an ability."""
        if not self.has_ability(entity_id, ability_id):
            return 0.0
        return self._instances[entity_id][ability_id].cooldown_remaining
    
    def is_active(self, entity_id: str, ability_id: str) -> bool:
        """Check if an ability effect is currently active."""
        if not self.has_ability(entity_id, ability_id):
            return False
        return self._instances[entity_id][ability_id].active
    
    # =========================================================================
    # Effect implementations
    # =========================================================================
    
    def _effect_ping_neighbors(
        self,
        entity: "Entity",
        world: "World",
        session: "GameSession",
        definition: AbilityDef,
        **kwargs
    ) -> bool:
        """Reveal nearby entities temporarily."""
        from hypersim.game.ecs.component import Transform, Renderable
        
        transform = entity.get(Transform)
        if not transform:
            return False
        
        radius = definition.params.get("radius", 15.0)
        
        # Find entities within radius
        for other in world.entities.values():
            if other.id == entity.id:
                continue
            
            other_transform = other.get(Transform)
            if not other_transform:
                continue
            
            dist = abs(other_transform.position[0] - transform.position[0])
            if dist <= radius:
                # Mark as revealed (renderer can check this)
                renderable = other.get(Renderable)
                if renderable:
                    renderable.glow = 1.0
        
        world.emit("ping_activated", entity_id=entity.id, radius=radius)
        return True
    
    def _effect_fold_line(
        self,
        entity: "Entity",
        world: "World",
        session: "GameSession",
        definition: AbilityDef,
        **kwargs
    ) -> bool:
        """Teleport a 1D entity along the line."""
        from hypersim.game.ecs.component import Transform, DimensionAnchor
        
        target_id = kwargs.get("target_entity_id")
        if not target_id:
            return False
        
        target = world.get(target_id)
        if not target:
            return False
        
        anchor = target.get(DimensionAnchor)
        if not anchor or anchor.dimension_id != "1d":
            return False
        
        target_transform = target.get(Transform)
        if not target_transform:
            return False
        
        # Teleport along X axis
        distance = definition.params.get("teleport_distance", 10.0)
        direction = kwargs.get("direction", 1)
        target_transform.position[0] += distance * direction
        
        world.emit("entity_teleported", entity_id=target_id)
        return True
    
    def _effect_sketch_path(
        self,
        entity: "Entity",
        world: "World",
        session: "GameSession",
        definition: AbilityDef,
        **kwargs
    ) -> bool:
        """Create a temporary wall/barrier."""
        from hypersim.game.ecs.entity import Entity as NewEntity
        from hypersim.game.ecs.component import Transform, Renderable, Collider, ColliderShape, DimensionAnchor
        
        transform = entity.get(Transform)
        if not transform:
            return False
        
        # Create wall entity
        wall_length = definition.params.get("length", 5.0)
        direction = np.array(kwargs.get("direction", [1.0, 0.0, 0.0, 0.0]))
        
        wall_pos = transform.position.copy()
        wall_pos[:2] += direction[:2] * 2  # Offset from player
        
        wall = NewEntity(id=f"sketch_wall_{id(definition)}")
        wall.add(Transform(position=wall_pos))
        wall.add(Renderable(color=(100, 200, 255), visible=True))
        wall.add(Collider(
            shape=ColliderShape.AABB,
            size=np.array([wall_length, 0.5]),
        ))
        wall.add(DimensionAnchor(dimension_id="2d"))
        wall.tag("temporary", "wall", "sketch")
        
        world.spawn(wall)
        
        # Schedule removal after duration
        world.emit("sketch_created", entity_id=wall.id, duration=definition.duration)
        return True
    
    def _effect_slice_plane(
        self,
        entity: "Entity",
        world: "World",
        session: "GameSession",
        definition: AbilityDef,
        **kwargs
    ) -> bool:
        """Activate slice view mode."""
        world.emit("slice_view_activated", entity_id=entity.id, duration=definition.duration)
        return True
    
    def _effect_carry_line(
        self,
        entity: "Entity",
        world: "World",
        session: "GameSession",
        definition: AbilityDef,
        **kwargs
    ) -> bool:
        """Pick up a 1D entity."""
        from hypersim.game.ecs.component import DimensionAnchor
        
        target_id = kwargs.get("target_entity_id")
        if not target_id:
            return False
        
        target = world.get(target_id)
        if not target:
            return False
        
        anchor = target.get(DimensionAnchor)
        if not anchor or anchor.dimension_id != "1d":
            return False
        
        # Attach target to carrier
        target.tag("carried")
        world.emit("entity_carried", carrier_id=entity.id, carried_id=target_id)
        return True
    
    def _effect_rotate_hyperplanes(
        self,
        entity: "Entity",
        world: "World",
        session: "GameSession",
        definition: AbilityDef,
        **kwargs
    ) -> bool:
        """Rotate 4D projection planes."""
        rotation_speed = definition.params.get("rotation_speed", 1.0)
        plane = kwargs.get("plane", "xw")
        
        world.emit(
            "hyperplane_rotation",
            entity_id=entity.id,
            plane=plane,
            speed=rotation_speed,
        )
        return True
    
    def _effect_spawn_slices(
        self,
        entity: "Entity",
        world: "World",
        session: "GameSession",
        definition: AbilityDef,
        **kwargs
    ) -> bool:
        """Spawn 3D cross-sections from 4D objects."""
        from hypersim.game.ecs.component import Transform
        
        transform = entity.get(Transform)
        if not transform:
            return False
        
        target_pos = kwargs.get("target_position", transform.position[:3])
        
        world.emit(
            "slices_spawned",
            entity_id=entity.id,
            position=target_pos,
            duration=definition.duration,
        )
        return True
    
    def _effect_stabilize_lower(
        self,
        entity: "Entity",
        world: "World",
        session: "GameSession",
        definition: AbilityDef,
        **kwargs
    ) -> bool:
        """Freeze time in a lower dimension."""
        target_dim = definition.params.get("target_dimension", "3d")
        
        # Pause all entities in target dimension
        for other in world.in_dimension(target_dim):
            other.tag("time_frozen")
        
        world.emit(
            "dimension_stabilized",
            entity_id=entity.id,
            dimension=target_dim,
            duration=definition.duration,
        )
        return True
    
    def _effect_dash(
        self,
        entity: "Entity",
        world: "World",
        session: "GameSession",
        definition: AbilityDef,
        **kwargs
    ) -> bool:
        """Quick dash in movement direction."""
        from hypersim.game.ecs.component import Velocity, Controller
        
        velocity = entity.get(Velocity)
        controller = entity.get(Controller)
        
        if not velocity or not controller:
            return False
        
        multiplier = definition.params.get("speed_multiplier", 3.0)
        
        # Boost velocity in input direction
        if np.linalg.norm(controller.input_vector) > 0.1:
            dash_dir = controller.input_vector / np.linalg.norm(controller.input_vector)
            velocity.linear[:len(dash_dir)] = dash_dir * controller.speed * multiplier
        
        world.emit("dash_activated", entity_id=entity.id)
        return True


# Global ability system instance
_ability_system: Optional[AbilitySystem] = None


def get_ability_system() -> AbilitySystem:
    """Get or create the global ability system."""
    global _ability_system
    if _ability_system is None:
        _ability_system = AbilitySystem()
    return _ability_system
