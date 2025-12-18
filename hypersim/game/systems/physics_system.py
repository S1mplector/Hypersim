"""Physics system - applies velocity to transforms."""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from hypersim.game.ecs.system import System
from hypersim.game.ecs.component import Transform, Velocity

if TYPE_CHECKING:
    from hypersim.game.ecs.world import World


class PhysicsSystem(System):
    """System that applies velocity to entity positions."""
    
    priority = 20  # After input, before collision
    required_components = (Transform, Velocity)
    
    def __init__(self, friction: float = 0.0, gravity: float = 0.0):
        self.friction = friction
        self.gravity = gravity
        self.bounds: dict[str, tuple[float, float]] = {}  # dimension_id -> (min, max) per axis
    
    def set_bounds(self, dimension_id: str, axis: int, min_val: float, max_val: float) -> None:
        """Set world bounds for a dimension axis."""
        key = f"{dimension_id}_{axis}"
        self.bounds[key] = (min_val, max_val)
    
    def update(self, world: "World", dt: float) -> None:
        """Apply velocity to all entities with Transform and Velocity."""
        for entity in self.query(world):
            transform = entity.get(Transform)
            velocity = entity.get(Velocity)
            
            # Apply gravity (if any, typically Y axis)
            if self.gravity != 0:
                velocity.linear[1] -= self.gravity * dt
            
            # Apply velocity to position
            transform.position += velocity.linear[:len(transform.position)] * dt
            
            # Apply friction
            if self.friction > 0:
                velocity.linear *= (1.0 - self.friction * dt)
            
            # Clamp to bounds if set
            self._apply_bounds(entity, transform)
    
    def _apply_bounds(self, entity, transform: Transform) -> None:
        """Clamp entity position to world bounds."""
        from hypersim.game.ecs.component import DimensionAnchor
        
        anchor = entity.get(DimensionAnchor)
        if not anchor:
            return
        
        dim_id = anchor.dimension_id
        for axis in range(len(transform.position)):
            key = f"{dim_id}_{axis}"
            if key in self.bounds:
                min_val, max_val = self.bounds[key]
                transform.position[axis] = np.clip(transform.position[axis], min_val, max_val)
