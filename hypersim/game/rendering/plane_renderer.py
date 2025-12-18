"""2D Plane renderer - renders entities on a 2D plane."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import pygame
import numpy as np

from .base_renderer import DimensionRenderer
from hypersim.game.ecs.component import (
    Transform, Renderable, Collider, ColliderShape,
    Health, DimensionAnchor, Pickup, Portal
)

if TYPE_CHECKING:
    from hypersim.game.ecs.world import World
    from hypersim.game.ecs.entity import Entity
    from hypersim.game.dimensions import DimensionSpec


class PlaneRenderer(DimensionRenderer):
    """Renderer for 2D plane world (top-down view)."""
    
    dimension_id = "2d"
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.scale = 20.0  # Pixels per unit
        self.background_color = (8, 12, 20)
        self.grid_enabled = True
        self.grid_size = 2.0  # World units
    
    def render(self, world: "World", dimension_spec: Optional["DimensionSpec"] = None) -> None:
        """Render the 2D world."""
        self.clear()
        
        # Follow player
        player = world.find_player()
        if player:
            self.follow_entity(world, player.id, lerp=0.1)
        
        # Draw grid
        if self.grid_enabled:
            self._draw_grid()
        
        # Get all entities in 2D dimension
        entities = world.in_dimension("2d")
        
        # Sort by layer for proper z-ordering
        def get_layer(e):
            r = e.get(Renderable)
            return r.layer if r else 0
        entities.sort(key=get_layer)
        
        # Render entities
        for entity in entities:
            if not entity.active:
                continue
            self._render_entity(entity)
        
        # Draw UI overlay
        self._draw_ui(world, player)
    
    def _draw_grid(self) -> None:
        """Draw background grid."""
        # Calculate visible world bounds
        half_w = self.width / (2 * self.scale)
        half_h = self.height / (2 * self.scale)
        
        min_x = self.camera_offset[0] - half_w
        max_x = self.camera_offset[0] + half_w
        min_y = self.camera_offset[1] - half_h
        max_y = self.camera_offset[1] + half_h
        
        grid_color = (20, 25, 35)
        
        # Vertical lines
        start_x = int(min_x / self.grid_size) * self.grid_size
        for wx in np.arange(start_x, max_x + self.grid_size, self.grid_size):
            sx, _ = self.world_to_screen(wx, 0)
            pygame.draw.line(self.screen, grid_color, (sx, 0), (sx, self.height), 1)
        
        # Horizontal lines
        start_y = int(min_y / self.grid_size) * self.grid_size
        for wy in np.arange(start_y, max_y + self.grid_size, self.grid_size):
            _, sy = self.world_to_screen(0, wy)
            pygame.draw.line(self.screen, grid_color, (0, sy), (self.width, sy), 1)
    
    def _render_entity(self, entity: "Entity") -> None:
        """Render a single entity."""
        transform = entity.get(Transform)
        renderable = entity.get(Renderable)
        
        if not transform:
            return
        if renderable and not renderable.visible:
            return
        
        world_x = transform.position[0]
        world_y = transform.position[1] if len(transform.position) > 1 else 0
        screen_pos = self.world_to_screen(world_x, world_y)
        
        # Check if on screen
        margin = 50
        if not (-margin <= screen_pos[0] <= self.width + margin and 
                -margin <= screen_pos[1] <= self.height + margin):
            return
        
        color = renderable.color if renderable else (255, 255, 255)
        
        # Different rendering for different entity types
        if entity.has_tag("player"):
            self._draw_player(entity, screen_pos, color)
        elif entity.has_tag("enemy"):
            self._draw_enemy(entity, screen_pos, color)
        elif entity.get(Pickup):
            self._draw_pickup(entity, screen_pos)
        elif entity.get(Portal):
            self._draw_portal(entity, screen_pos)
        else:
            # Generic entity
            self._draw_generic(entity, screen_pos, color)
    
    def _draw_player(self, entity: "Entity", pos: tuple, color: tuple) -> None:
        """Draw the player entity."""
        # Glow effect
        for i in range(3):
            size = 18 - i * 4
            glow_color = (
                min(255, color[0] + 30),
                min(255, color[1] + 80),
                min(255, color[2] + 100)
            )
            pygame.draw.circle(self.screen, glow_color, pos, size)
        
        # Core
        pygame.draw.circle(self.screen, (255, 255, 255), pos, 8)
        
        # Direction indicator
        controller = entity.get(Transform)
        # Simple triangle pointing in movement direction
        pygame.draw.polygon(
            self.screen,
            (200, 230, 255),
            [
                (pos[0], pos[1] - 12),
                (pos[0] - 6, pos[1] + 4),
                (pos[0] + 6, pos[1] + 4),
            ]
        )
    
    def _draw_enemy(self, entity: "Entity", pos: tuple, color: tuple) -> None:
        """Draw an enemy entity."""
        health = entity.get(Health)
        collider = entity.get(Collider)
        
        # Size based on collider
        size = 12
        if collider and len(collider.size) > 0:
            size = int(collider.size[0] * self.scale / 2)
        
        # Red color for enemies
        enemy_color = (200, 60, 60)
        
        # Draw as diamond
        points = [
            (pos[0], pos[1] - size),
            (pos[0] + size, pos[1]),
            (pos[0], pos[1] + size),
            (pos[0] - size, pos[1]),
        ]
        pygame.draw.polygon(self.screen, enemy_color, points)
        pygame.draw.polygon(self.screen, (255, 120, 120), points, 2)
        
        # Health bar
        if health and health.ratio < 1.0:
            bar_width = size * 2
            bar_height = 4
            bar_x = pos[0] - bar_width // 2
            bar_y = pos[1] - size - 8
            
            pygame.draw.rect(self.screen, (60, 20, 20), (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(
                self.screen, (200, 50, 50),
                (bar_x, bar_y, int(bar_width * health.ratio), bar_height)
            )
    
    def _draw_pickup(self, entity: "Entity", pos: tuple) -> None:
        """Draw a pickup item."""
        pickup = entity.get(Pickup)
        
        # Golden color
        color = (255, 220, 50)
        
        # Pulsing effect
        pulse = abs(pygame.time.get_ticks() % 1000 - 500) / 500.0
        size = int(8 + pulse * 4)
        
        pygame.draw.circle(self.screen, color, pos, size)
        pygame.draw.circle(self.screen, (255, 255, 200), pos, size, 2)
        
        # Sparkle
        if pygame.time.get_ticks() % 200 < 100:
            pygame.draw.circle(self.screen, (255, 255, 255), (pos[0] - 3, pos[1] - 3), 2)
    
    def _draw_portal(self, entity: "Entity", pos: tuple) -> None:
        """Draw a dimension portal."""
        portal = entity.get(Portal)
        
        active_color = (150, 50, 255)
        inactive_color = (80, 40, 100)
        color = active_color if portal.active else inactive_color
        
        # Animated rings
        time = pygame.time.get_ticks() / 1000.0
        
        for i in range(3):
            offset = (time * 2 + i * 0.3) % 1.0
            ring_size = int(10 + offset * 15)
            alpha = int(255 * (1 - offset))
            ring_color = (
                min(255, color[0] + int(offset * 50)),
                min(255, color[1] + int(offset * 30)),
                min(255, color[2])
            )
            pygame.draw.circle(self.screen, ring_color, pos, ring_size, 2)
        
        # Core
        pygame.draw.circle(self.screen, (200, 150, 255), pos, 8)
    
    def _draw_generic(self, entity: "Entity", pos: tuple, color: tuple) -> None:
        """Draw a generic entity."""
        collider = entity.get(Collider)
        
        if collider:
            if collider.shape == ColliderShape.CIRCLE:
                radius = int(collider.size[0] * self.scale) if len(collider.size) > 0 else 10
                pygame.draw.circle(self.screen, color, pos, radius)
                pygame.draw.circle(self.screen, (255, 255, 255), pos, radius, 1)
            elif collider.shape == ColliderShape.AABB:
                w = int(collider.size[0] * self.scale) if len(collider.size) > 0 else 20
                h = int(collider.size[1] * self.scale) if len(collider.size) > 1 else w
                rect = pygame.Rect(pos[0] - w // 2, pos[1] - h // 2, w, h)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 1)
        else:
            pygame.draw.circle(self.screen, color, pos, 8)
    
    def _draw_ui(self, world: "World", player: Optional["Entity"]) -> None:
        """Draw UI overlay."""
        font = pygame.font.Font(None, 24)
        
        # Player health
        if player:
            health = player.get(Health)
            if health:
                bar_width = 150
                bar_height = 15
                bar_x = 20
                bar_y = self.height - 40
                
                pygame.draw.rect(self.screen, (40, 20, 20), (bar_x, bar_y, bar_width, bar_height))
                pygame.draw.rect(
                    self.screen, (50, 180, 80),
                    (bar_x, bar_y, int(bar_width * health.ratio), bar_height)
                )
                pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height), 1)
                
                health_text = font.render(f"HP: {int(health.current)}/{int(health.max)}", True, (200, 200, 200))
                self.screen.blit(health_text, (bar_x + bar_width + 10, bar_y))
        
        # Dimension label
        dim_text = font.render("2D - Plane World", True, (150, 150, 200))
        self.screen.blit(dim_text, (self.width - 140, self.height - 30))
        
        # Coordinates
        if player:
            transform = player.get(Transform)
            if transform:
                x = transform.position[0]
                y = transform.position[1] if len(transform.position) > 1 else 0
                coord_text = font.render(f"({x:.1f}, {y:.1f})", True, (100, 100, 120))
                self.screen.blit(coord_text, (20, 20))
