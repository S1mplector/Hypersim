"""Base renderer interface for dimension-specific rendering."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

import pygame

if TYPE_CHECKING:
    from hypersim.game.ecs.world import World
    from hypersim.game.dimensions import DimensionSpec


class DimensionRenderer(ABC):
    """Base class for dimension-specific renderers."""
    
    dimension_id: str = "base"
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.camera_offset = [0.0, 0.0]
        self.scale = 20.0  # Pixels per unit
        self.background_color = (10, 10, 20)
    
    @abstractmethod
    def render(self, world: "World", dimension_spec: Optional["DimensionSpec"] = None) -> None:
        """Render all entities in the world for this dimension."""
        pass
    
    def world_to_screen(self, world_x: float, world_y: float = 0.0) -> tuple[int, int]:
        """Convert world coordinates to screen coordinates."""
        screen_x = int((world_x - self.camera_offset[0]) * self.scale + self.width / 2)
        screen_y = int(self.height / 2 - (world_y - self.camera_offset[1]) * self.scale)
        return (screen_x, screen_y)
    
    def screen_to_world(self, screen_x: int, screen_y: int) -> tuple[float, float]:
        """Convert screen coordinates to world coordinates."""
        world_x = (screen_x - self.width / 2) / self.scale + self.camera_offset[0]
        world_y = (self.height / 2 - screen_y) / self.scale + self.camera_offset[1]
        return (world_x, world_y)
    
    def clear(self) -> None:
        """Clear the screen with background color."""
        self.screen.fill(self.background_color)
    
    def follow_entity(self, world: "World", entity_id: str, lerp: float = 0.1) -> None:
        """Smoothly follow an entity with the camera."""
        from hypersim.game.ecs.component import Transform
        
        entity = world.get(entity_id)
        if not entity:
            return
        
        transform = entity.get(Transform)
        if not transform:
            return
        
        target_x = transform.position[0] if len(transform.position) > 0 else 0
        target_y = transform.position[1] if len(transform.position) > 1 else 0
        
        self.camera_offset[0] += (target_x - self.camera_offset[0]) * lerp
        self.camera_offset[1] += (target_y - self.camera_offset[1]) * lerp
