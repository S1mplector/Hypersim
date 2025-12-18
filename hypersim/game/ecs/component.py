"""Base component and built-in component types."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray


class Component:
    """Base class for all components. Subclass to create custom components."""
    pass


@dataclass
class Transform(Component):
    """Position, rotation, and scale in N-dimensional space."""
    
    position: NDArray = field(default_factory=lambda: np.zeros(4))
    rotation: NDArray = field(default_factory=lambda: np.eye(4))
    scale: float = 1.0
    
    def __post_init__(self) -> None:
        self.position = np.asarray(self.position, dtype=np.float64)
        if self.position.ndim == 0:
            self.position = np.array([float(self.position)])
    
    @property
    def dimensions(self) -> int:
        """Number of spatial dimensions this transform operates in."""
        return len(self.position)
    
    def translate(self, delta: NDArray) -> None:
        """Move by delta vector."""
        delta = np.asarray(delta, dtype=np.float64)
        if len(delta) < len(self.position):
            padded = np.zeros_like(self.position)
            padded[:len(delta)] = delta
            delta = padded
        self.position[:len(delta)] += delta[:len(self.position)]
    
    def set_position_axis(self, axis: int, value: float) -> None:
        """Set position on a specific axis."""
        if axis < len(self.position):
            self.position[axis] = value


@dataclass
class Velocity(Component):
    """Linear and angular velocity."""
    
    linear: NDArray = field(default_factory=lambda: np.zeros(4))
    angular: NDArray = field(default_factory=lambda: np.zeros(6))  # 6 rotation planes in 4D
    
    def __post_init__(self) -> None:
        self.linear = np.asarray(self.linear, dtype=np.float64)
        self.angular = np.asarray(self.angular, dtype=np.float64)


class ColliderShape(str, Enum):
    """Supported collider shapes."""
    POINT = "point"
    SEGMENT = "segment"  # 1D
    CIRCLE = "circle"    # 2D
    AABB = "aabb"        # 2D/3D axis-aligned bounding box
    SPHERE = "sphere"    # 3D/4D
    CAPSULE = "capsule"


@dataclass
class Collider(Component):
    """Collision detection shape and properties."""
    
    shape: ColliderShape = ColliderShape.POINT
    size: NDArray = field(default_factory=lambda: np.array([1.0]))
    offset: NDArray = field(default_factory=lambda: np.zeros(4))
    is_trigger: bool = False
    layer: int = 0
    mask: int = 0xFFFF
    
    def __post_init__(self) -> None:
        self.size = np.asarray(self.size, dtype=np.float64)
        self.offset = np.asarray(self.offset, dtype=np.float64)


@dataclass
class Renderable(Component):
    """Visual representation of an entity."""
    
    mesh_id: str = "default"
    color: Tuple[int, int, int] = (255, 255, 255)
    alpha: int = 255
    layer: int = 0
    visible: bool = True
    glow: float = 0.0  # 0-1, for effects like player visibility in 1D


@dataclass
class Health(Component):
    """Health and damage state."""
    
    current: float = 100.0
    max: float = 100.0
    invuln_timer: float = 0.0
    invuln_duration: float = 0.5
    
    @property
    def ratio(self) -> float:
        """Health as fraction of max."""
        return self.current / self.max if self.max > 0 else 0.0
    
    @property
    def is_alive(self) -> bool:
        return self.current > 0
    
    @property
    def is_invulnerable(self) -> bool:
        return self.invuln_timer > 0
    
    def take_damage(self, amount: float) -> float:
        """Apply damage, respecting invulnerability. Returns actual damage taken."""
        if self.is_invulnerable or amount <= 0:
            return 0.0
        actual = min(amount, self.current)
        self.current -= actual
        self.invuln_timer = self.invuln_duration
        return actual
    
    def heal(self, amount: float) -> float:
        """Restore health. Returns actual healing done."""
        if amount <= 0:
            return 0.0
        actual = min(amount, self.max - self.current)
        self.current += actual
        return actual
    
    def tick(self, dt: float) -> None:
        """Update timers."""
        if self.invuln_timer > 0:
            self.invuln_timer = max(0.0, self.invuln_timer - dt)


@dataclass
class Controller(Component):
    """Input-driven movement controller."""
    
    controller_type: str = "line"  # "line", "plane", "volume", "hyper"
    speed: float = 5.0
    input_vector: NDArray = field(default_factory=lambda: np.zeros(4))
    enabled: bool = True
    
    def __post_init__(self) -> None:
        self.input_vector = np.asarray(self.input_vector, dtype=np.float64)
    
    def set_input(self, axis: int, value: float) -> None:
        """Set input on a specific axis (-1 to 1)."""
        if axis < len(self.input_vector):
            self.input_vector[axis] = np.clip(value, -1.0, 1.0)
    
    def clear_input(self) -> None:
        """Reset input vector to zero."""
        self.input_vector.fill(0.0)


@dataclass
class AIBrain(Component):
    """NPC behavior controller."""
    
    behavior: str = "idle"  # "idle", "patrol", "chase", "attack"
    state: Dict[str, Any] = field(default_factory=dict)
    detect_range: float = 10.0
    attack_range: float = 2.0
    patrol_points: List[NDArray] = field(default_factory=list)
    patrol_index: int = 0
    target_entity_id: Optional[str] = None
    
    def set_state(self, key: str, value: Any) -> None:
        self.state[key] = value
    
    def get_state(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)


@dataclass
class DimensionAnchor(Component):
    """Defines which dimension an entity exists in and visibility rules."""
    
    dimension_id: str = "1d"
    visible_from: List[str] = field(default_factory=list)
    can_interact_with: List[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        if not self.visible_from:
            self.visible_from = [self.dimension_id]
        if not self.can_interact_with:
            self.can_interact_with = [self.dimension_id]
    
    def is_visible_from(self, observer_dimension: str) -> bool:
        """Check if entity is visible from another dimension."""
        return observer_dimension in self.visible_from
    
    def can_interact_from(self, actor_dimension: str) -> bool:
        """Check if entity can be interacted with from another dimension."""
        return actor_dimension in self.can_interact_with


@dataclass
class Pickup(Component):
    """Collectible item component."""
    
    item_type: str = "generic"
    item_id: str = ""
    value: int = 1
    collected: bool = False


@dataclass
class Portal(Component):
    """Dimension or level transition portal."""
    
    target_dimension: str = ""
    target_world: str = ""
    target_position: Optional[NDArray] = None
    requires_key: Optional[str] = None
    active: bool = True
