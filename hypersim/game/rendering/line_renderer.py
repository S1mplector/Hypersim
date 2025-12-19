"""1D Line renderer - renders entities on a line."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import pygame
import numpy as np

from .base_renderer import DimensionRenderer
from .particles_1d import ParticleSystem1D, ParticleType, get_particle_type_for_entity
from hypersim.game.ecs.component import (
    Transform, Renderable, Collider, ColliderShape, 
    Health, DimensionAnchor, Pickup, Portal, AIBrain
)

if TYPE_CHECKING:
    from hypersim.game.ecs.world import World
    from hypersim.game.ecs.entity import Entity
    from hypersim.game.dimensions import DimensionSpec


class LineRenderer(DimensionRenderer):
    """Renderer for 1D line world."""
    
    dimension_id = "1d"
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.scale = 15.0  # Pixels per unit
        self.background_color = (5, 5, 15)
        self.line_y = self.height // 2  # Y position of the line on screen
        self.line_height = 80  # Height of the visible line strip
        self.visibility_radius = 15.0  # How far the player can see (in world units)
        self.fog_enabled = True
        
        # Particle system for entity effects
        self.particle_system = ParticleSystem1D(screen, self.line_y)
        self._last_dt = 1/60  # Default delta time
        
        # Healing mechanic state
        self._healing_check_timer = 0.0
        self._healing_check_interval = 0.5  # Check every 0.5 seconds
    
    def render(self, world: "World", dimension_spec: Optional["DimensionSpec"] = None) -> None:
        """Render the 1D world."""
        self.clear()
        
        # Update particle system
        self.particle_system.update(self._last_dt)
        
        # Draw the line background
        self._draw_line_background()
        
        # Get player for visibility calculations
        player = world.find_player()
        player_x = 0.0
        player_screen_x = self.width // 2
        if player:
            transform = player.get(Transform)
            if transform:
                player_x = transform.position[0]
                # Update camera to follow player
                self.camera_offset[0] = player_x
                player_screen_x = self.world_to_screen(player_x, 0)[0]
        
        # Get all entities in 1D dimension
        entities = world.in_dimension("1d")
        
        # Sort by position for consistent rendering
        def get_x(e):
            t = e.get(Transform)
            return t.position[0] if t else 0
        entities.sort(key=get_x)
        
        # Check for First Point healing
        self._check_healing(world, player, player_x, player_screen_x)
        
        # Draw particles behind entities
        self.particle_system.draw()
        
        # Render entities and update their particle emitters
        for entity in entities:
            if not entity.active:
                continue
            self._render_entity(entity, player_x)
            self._update_entity_particles(entity, player_x)
        
        # Draw UI overlay
        self._draw_ui(world, player)
    
    def set_delta_time(self, dt: float) -> None:
        """Set the delta time for particle updates."""
        self._last_dt = dt
    
    def _check_healing(self, world: "World", player: Optional["Entity"], player_x: float, player_screen_x: int) -> None:
        """Check if player needs healing from the First Point."""
        if not player:
            return
        
        self._healing_check_timer += self._last_dt
        if self._healing_check_timer < self._healing_check_interval:
            return
        self._healing_check_timer = 0.0
        
        # Check player health
        player_health = player.get(Health)
        if not player_health or player_health.current >= player_health.max:
            return
        
        # Find the First Point
        first_point = world.get("the_first_point")
        if not first_point or not first_point.active:
            return
        
        fp_transform = first_point.get(Transform)
        if not fp_transform:
            return
        
        # Check distance (must be close for healing)
        distance = abs(player_x - fp_transform.position[0])
        if distance > 5.0:  # Must be within 5 units
            return
        
        # Trigger healing particles
        fp_screen_x = self.world_to_screen(fp_transform.position[0], 0)[0]
        if self.particle_system.trigger_healing("the_first_point", player_screen_x, 12):
            # Actually heal the player
            heal_amount = min(5, player_health.max - player_health.current)
            player_health.current += heal_amount
    
    def _update_entity_particles(self, entity: "Entity", player_x: float) -> None:
        """Update or create particle emitter for an entity."""
        # Skip player - they don't need ambient particles
        if entity.has_tag("player"):
            return
        
        # Skip pickups and portals
        if entity.get(Pickup) or entity.get(Portal):
            return
        
        transform = entity.get(Transform)
        if not transform:
            return
        
        screen_x = self.world_to_screen(transform.position[0], 0)[0]
        
        # Skip if off screen
        if screen_x < -100 or screen_x > self.width + 100:
            return
        
        # Get particle type for this entity
        particle_type = get_particle_type_for_entity(entity)
        
        # Get color from renderable
        renderable = entity.get(Renderable)
        color = renderable.color if renderable else (255, 255, 255)
        
        # Get or create emitter
        emitter = self.particle_system.get_or_create_emitter(
            entity.id,
            particle_type,
            screen_x,
            color,
        )
        
        # Update position
        self.particle_system.update_emitter_position(entity.id, screen_x)
    
    def _draw_line_background(self) -> None:
        """Draw the line/track background."""
        # Draw gradient background strip
        strip_top = self.line_y - self.line_height // 2
        strip_rect = pygame.Rect(0, strip_top, self.width, self.line_height)
        
        # Dark background for the strip
        pygame.draw.rect(self.screen, (15, 15, 30), strip_rect)
        
        # Draw the main line
        pygame.draw.line(
            self.screen,
            (40, 40, 80),
            (0, self.line_y),
            (self.width, self.line_y),
            3
        )
        
        # Draw grid markers
        grid_spacing = 5.0  # World units
        start_world = self.camera_offset[0] - self.width / (2 * self.scale)
        end_world = self.camera_offset[0] + self.width / (2 * self.scale)
        
        marker_start = int(start_world / grid_spacing) * grid_spacing
        for wx in np.arange(marker_start, end_world + grid_spacing, grid_spacing):
            sx, _ = self.world_to_screen(wx)
            if 0 <= sx <= self.width:
                pygame.draw.line(
                    self.screen,
                    (30, 30, 60),
                    (sx, self.line_y - 10),
                    (sx, self.line_y + 10),
                    1
                )
    
    def _render_entity(self, entity: "Entity", player_x: float) -> None:
        """Render a single entity on the line."""
        transform = entity.get(Transform)
        renderable = entity.get(Renderable)
        
        if not transform:
            return
        
        world_x = transform.position[0]
        screen_x, _ = self.world_to_screen(world_x)
        
        # Check visibility (fog of war)
        distance = abs(world_x - player_x)
        if self.fog_enabled and distance > self.visibility_radius:
            return
        
        # Calculate alpha based on distance (fog effect)
        alpha = 255
        if self.fog_enabled and distance > self.visibility_radius * 0.7:
            fade_start = self.visibility_radius * 0.7
            fade_range = self.visibility_radius - fade_start
            alpha = int(255 * (1 - (distance - fade_start) / fade_range))
            alpha = max(0, min(255, alpha))
        
        # Determine color and size
        color = renderable.color if renderable else (255, 255, 255)
        base_size = 8
        
        # Different rendering for different entity types
        if entity.has_tag("player"):
            self._draw_player(screen_x, color, alpha)
        elif entity.has_tag("the_first_point"):
            self._draw_first_point(screen_x, alpha)
        elif entity.has_tag("npc") or entity.has_tag("friendly"):
            self._draw_npc(entity, screen_x, color, alpha)
        elif entity.has_tag("enemy") or entity.has_tag("encounter_trigger"):
            self._draw_enemy(entity, screen_x, color, alpha)
        elif entity.get(Pickup):
            self._draw_pickup(entity, screen_x, alpha)
        elif entity.get(Portal):
            self._draw_portal(entity, screen_x, alpha)
        else:
            # Generic entity
            self._draw_point(screen_x, color, base_size, alpha)
    
    def _draw_player(self, screen_x: int, color: tuple, alpha: int) -> None:
        """Draw the player entity."""
        # Glowing circle for player
        for i in range(3):
            size = 12 - i * 3
            a = alpha // (i + 1)
            glow_color = (
                min(255, color[0] + 50),
                min(255, color[1] + 50),
                min(255, color[2] + 100)
            )
            pygame.draw.circle(
                self.screen,
                (*glow_color,),
                (screen_x, self.line_y),
                size
            )
        
        # Core
        pygame.draw.circle(
            self.screen,
            (255, 255, 255),
            (screen_x, self.line_y),
            5
        )
    
    def _draw_enemy(self, entity: "Entity", screen_x: int, color: tuple, alpha: int) -> None:
        """Draw an enemy entity."""
        health = entity.get(Health)
        
        # Red-ish color for enemies
        enemy_color = (200, 50, 50)
        
        # Draw as angular shape
        points = [
            (screen_x, self.line_y - 12),
            (screen_x + 8, self.line_y),
            (screen_x, self.line_y + 12),
            (screen_x - 8, self.line_y),
        ]
        pygame.draw.polygon(self.screen, enemy_color, points)
        pygame.draw.polygon(self.screen, (255, 100, 100), points, 2)
        
        # Health bar
        if health and health.ratio < 1.0:
            bar_width = 20
            bar_height = 4
            bar_x = screen_x - bar_width // 2
            bar_y = self.line_y - 20
            
            # Background
            pygame.draw.rect(self.screen, (60, 20, 20), (bar_x, bar_y, bar_width, bar_height))
            # Health
            pygame.draw.rect(
                self.screen, (200, 50, 50),
                (bar_x, bar_y, int(bar_width * health.ratio), bar_height)
            )
    
    def _draw_pickup(self, entity: "Entity", screen_x: int, alpha: int) -> None:
        """Draw a pickup item."""
        pickup = entity.get(Pickup)
        
        # Yellow/gold for pickups
        color = (255, 220, 50)
        
        # Pulsing effect
        pulse = abs(pygame.time.get_ticks() % 1000 - 500) / 500.0
        size = int(6 + pulse * 3)
        
        pygame.draw.circle(self.screen, color, (screen_x, self.line_y), size)
        pygame.draw.circle(self.screen, (255, 255, 200), (screen_x, self.line_y), size, 2)
    
    def _draw_portal(self, entity: "Entity", screen_x: int, alpha: int) -> None:
        """Draw a dimension portal."""
        portal = entity.get(Portal)
        
        # Purple for portals
        color = (150, 50, 255) if portal.active else (80, 40, 100)
        
        # Swirling effect
        angle = pygame.time.get_ticks() / 500.0
        
        # Draw portal frame
        pygame.draw.circle(self.screen, color, (screen_x, self.line_y), 15, 3)
        pygame.draw.circle(self.screen, (200, 150, 255), (screen_x, self.line_y), 10, 2)
        
        # Inner glow
        if portal.active:
            for i in range(5):
                a = 100 - i * 20
                pygame.draw.circle(
                    self.screen,
                    (150 + i * 20, 100, 255),
                    (screen_x, self.line_y),
                    8 - i
                )
    
    def _draw_first_point(self, screen_x: int, alpha: int) -> None:
        """Draw the First Point NPC with special purple glow effect."""
        import math
        
        # Purple color for the First Point
        base_color = (180, 100, 255)
        
        # Pulse animation
        pulse = math.sin(pygame.time.get_ticks() / 800.0) * 0.15 + 1.0
        
        # Draw outer glow layers (largest to smallest)
        glow_layers = 10
        max_glow_radius = int(60 * pulse)
        
        for i in range(glow_layers, 0, -1):
            layer_ratio = i / glow_layers
            radius = int(max_glow_radius * layer_ratio)
            
            # Glow gets more transparent at outer edges
            layer_alpha = int(40 * (1 - layer_ratio) * (alpha / 255))
            
            glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            glow_color = (*base_color, layer_alpha)
            pygame.draw.circle(glow_surf, glow_color, (radius, radius), radius)
            self.screen.blit(glow_surf, (screen_x - radius, self.line_y - radius))
        
        # Draw inner core layers
        core_layers = 5
        max_core_radius = int(20 * pulse)
        
        for i in range(core_layers):
            layer_ratio = (core_layers - i) / core_layers
            radius = int(max_core_radius * layer_ratio)
            
            # Blend toward white at center
            blend = 1 - layer_ratio
            core_color = (
                int(base_color[0] + (255 - base_color[0]) * blend),
                int(base_color[1] + (255 - base_color[1]) * blend),
                int(base_color[2] + (255 - base_color[2]) * blend),
                int(255 * (alpha / 255))
            )
            
            core_surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(core_surf, core_color, (radius + 2, radius + 2), radius)
            self.screen.blit(core_surf, (screen_x - radius - 2, self.line_y - radius - 2))
        
        # Draw bright center point
        center_size = int(6 * pulse)
        pygame.draw.circle(self.screen, (255, 255, 255), (screen_x, self.line_y), center_size)
        
        # Draw interaction hint when player is nearby
        font = pygame.font.Font(None, 18)
        hint_text = font.render("Press E to talk", True, (200, 180, 255, int(180 * (alpha / 255))))
        hint_rect = hint_text.get_rect(center=(screen_x, self.line_y - 45))
        self.screen.blit(hint_text, hint_rect)
    
    def _draw_npc(self, entity: "Entity", screen_x: int, color: tuple, alpha: int) -> None:
        """Draw a friendly NPC entity."""
        # Draw with a soft glow
        glow_color = (
            min(255, color[0] + 30),
            min(255, color[1] + 30),
            min(255, color[2] + 30)
        )
        
        # Outer glow
        pygame.draw.circle(self.screen, glow_color, (screen_x, self.line_y), 14)
        pygame.draw.circle(self.screen, color, (screen_x, self.line_y), 10)
        
        # White highlight
        pygame.draw.circle(self.screen, (255, 255, 255), (screen_x, self.line_y), 4)
    
    def _draw_point(self, screen_x: int, color: tuple, size: int, alpha: int) -> None:
        """Draw a generic point entity."""
        pygame.draw.circle(self.screen, color, (screen_x, self.line_y), size)
    
    def _draw_ui(self, world: "World", player: Optional["Entity"]) -> None:
        """Draw UI overlay."""
        font = pygame.font.Font(None, 24)
        
        # Draw minimap at top
        minimap_height = 30
        minimap_rect = pygame.Rect(50, 10, self.width - 100, minimap_height)
        pygame.draw.rect(self.screen, (20, 20, 40), minimap_rect)
        pygame.draw.rect(self.screen, (60, 60, 100), minimap_rect, 1)
        
        # Draw entities on minimap
        entities = world.in_dimension("1d")
        world_min = -50.0
        world_max = 50.0
        
        for entity in entities:
            transform = entity.get(Transform)
            if not transform:
                continue
            
            wx = transform.position[0]
            if world_min <= wx <= world_max:
                ratio = (wx - world_min) / (world_max - world_min)
                mx = int(minimap_rect.left + ratio * minimap_rect.width)
                my = minimap_rect.centery
                
                if entity.has_tag("player"):
                    pygame.draw.circle(self.screen, (100, 200, 255), (mx, my), 4)
                elif entity.has_tag("enemy"):
                    pygame.draw.circle(self.screen, (255, 80, 80), (mx, my), 3)
                elif entity.get(Portal):
                    pygame.draw.circle(self.screen, (180, 100, 255), (mx, my), 3)
        
        # Draw player health if available
        if player:
            health = player.get(Health)
            if health:
                bar_width = 180
                bar_height = 20
                bar_x = 20
                bar_y = self.height - 50
                
                # HP Label above bar
                hp_label = font.render("HP", True, (255, 255, 255))
                self.screen.blit(hp_label, (bar_x, bar_y - 20))
                
                # Dark background with slight transparency effect
                bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
                pygame.draw.rect(self.screen, (20, 10, 15), bg_rect)
                
                # Health fill with gradient effect (brighter at top)
                fill_width = int(bar_width * health.ratio)
                if fill_width > 0:
                    # Determine color based on health percentage
                    ratio = health.ratio
                    if ratio > 0.5:
                        # Green to yellow
                        r = int(255 * (1 - (ratio - 0.5) * 2))
                        g = 220
                        b = 50
                    else:
                        # Yellow to red
                        r = 255
                        g = int(220 * ratio * 2)
                        b = 50
                    
                    health_color = (r, g, b)
                    
                    # Main health bar
                    pygame.draw.rect(self.screen, health_color, (bar_x, bar_y, fill_width, bar_height))
                    
                    # Highlight at top for 3D effect
                    highlight_color = (min(255, r + 60), min(255, g + 40), min(255, b + 30))
                    pygame.draw.rect(self.screen, highlight_color, (bar_x, bar_y, fill_width, 4))
                    
                    # Shadow at bottom
                    shadow_color = (max(0, r - 60), max(0, g - 60), max(0, b - 30))
                    pygame.draw.rect(self.screen, shadow_color, (bar_x, bar_y + bar_height - 3, fill_width, 3))
                
                # Border with slight glow effect
                pygame.draw.rect(self.screen, (80, 80, 100), bg_rect, 2)
                
                # Numeric display to the right
                health_text = font.render(f"{int(health.current)} / {int(health.max)}", True, (255, 255, 255))
                self.screen.blit(health_text, (bar_x + bar_width + 12, bar_y + 2))
        
        # Dimension label
        dim_text = font.render("1D - Line World", True, (150, 150, 200))
        self.screen.blit(dim_text, (self.width - 130, self.height - 30))
