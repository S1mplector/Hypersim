"""1D Line renderer - renders entities on a line."""
from __future__ import annotations

import math
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
        self.scale = 19.0  # Pixels per unit (tighter, more zoomed-in feel)
        self.sprite_scale = 1.28  # Visual scale multiplier for 1D entities
        self.background_color = (6, 9, 20)
        self._base_line_y = self.height // 2
        self.line_y = self._base_line_y  # Y position of the line on screen
        self.line_height = 126  # Height of the visible line strip
        self.visibility_radius = 20.0  # How far the player can see (in world units)
        self.fog_enabled = True
        self._bg_time = 0.0
        self._screen_shake = 0.0
        self._shake_offset = (0, 0)
        self._dimensional_strain = 0.0
        self._dimensional_axis = 0.0
        self._dimensional_flash = 0.0
        self._strain_origin_x = self.width // 2
        
        # Subtle parallax stars for better depth in 1D.
        rng = np.random.default_rng(42)
        self._background_stars = [
            {
                "x": float(rng.uniform(-120.0, self.width + 120.0)),
                "y": float(rng.uniform(40.0, self.height - 60.0)),
                "size": float(rng.uniform(0.7, 2.2)),
                "parallax": float(rng.uniform(0.03, 0.14)),
                "phase": float(rng.uniform(0.0, math.pi * 2.0)),
                "twinkle": float(rng.uniform(0.8, 2.4)),
            }
            for _ in range(140)
        ]
        
        # Ambient drifting motes to make the world feel less static.
        self._ambient_motes = [
            {
                "x": float(rng.uniform(-120.0, self.width + 120.0)),
                "y_offset": float(rng.uniform(-72.0, 72.0)),
                "size": float(rng.uniform(1.0, 2.8)),
                "speed": float(rng.uniform(12.0, 34.0)),
                "phase": float(rng.uniform(0.0, math.pi * 2.0)),
                "trail": float(rng.uniform(6.0, 14.0)),
            }
            for _ in range(52)
        ]
        self._fx_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Particle system for entity effects
        self.particle_system = ParticleSystem1D(screen, self.line_y)
        self._last_dt = 1/60  # Default delta time
        
        # Healing mechanic state
        self._healing_check_timer = 0.0
        self._healing_check_interval = 0.5  # Check every 0.5 seconds

    def set_dimensional_strain(
        self,
        bend_strength: float,
        bend_axis: float,
        flash_strength: float,
        shake_strength: float,
    ) -> None:
        """Set transient 1D instability caused by impossible movement attempts."""
        self._dimensional_strain = max(0.0, float(bend_strength))
        self._dimensional_axis = float(np.clip(bend_axis, -1.0, 1.0))
        self._dimensional_flash = max(0.0, float(flash_strength))
        self._screen_shake = max(0.0, float(shake_strength))

    def world_to_screen(self, world_x: float, world_y: float = 0.0) -> tuple[int, int]:
        """Convert world coordinates to screen coordinates with current shake applied."""
        screen_x, screen_y = super().world_to_screen(world_x, world_y)
        return screen_x + int(self._shake_offset[0]), screen_y + int(self._shake_offset[1])

    def _line_y_at_screen_x(self, screen_x: int, offset: float = 0.0, bend_scale: float = 1.0) -> int:
        """Return the current bent line height for a screen-space x position."""
        base_y = self.line_y + offset
        if self._dimensional_strain <= 0.001 or abs(self._dimensional_axis) <= 0.001:
            return int(base_y)

        spread = 54.0 + 48.0 * self._dimensional_strain
        dx = (screen_x - self._strain_origin_x) / spread
        gaussian = math.exp(-(dx * dx))
        local_bend = gaussian * self._dimensional_axis * 16.0 * self._dimensional_strain * bend_scale
        ripple = math.sin(dx * 4.2 - self._bg_time * 16.0) * 2.6 * gaussian * self._dimensional_strain * bend_scale
        return int(base_y + local_bend + ripple)

    def _draw_confusion_halo(self, screen_x: int, line_y: int, intensity: float) -> None:
        """Draw visible panic/confusion around an entity."""
        count = 3
        radius = self._sz(18) + int(self._sz(3) * min(2.0, intensity))
        for idx in range(count):
            orbit = self._bg_time * (3.0 + idx) + idx * 2.1 + screen_x * 0.01
            dot_x = screen_x + int(math.cos(orbit) * radius)
            dot_y = line_y - self._sz(14) + int(math.sin(orbit * 1.3) * self._sz(7))
            pygame.draw.circle(self.screen, (255, 230, 150), (dot_x, dot_y), self._sz(2))
        arc_rect = pygame.Rect(0, 0, self._sz(28), self._sz(18))
        arc_rect.center = (screen_x, line_y - self._sz(20))
        pygame.draw.arc(self.screen, (255, 210, 140), arc_rect, 0.15, math.pi - 0.15, 2)
    
    def render(self, world: "World", dimension_spec: Optional["DimensionSpec"] = None) -> None:
        """Render the 1D world."""
        self.clear()
        self._bg_time += self._last_dt
        if self._screen_shake > 0.01:
            max_offset = max(1, int(8 * self._screen_shake))
            self._shake_offset = (
                int(np.random.randint(-max_offset, max_offset + 1)),
                int(np.random.randint(-max_offset, max_offset + 1)),
            )
        else:
            self._shake_offset = (0, 0)
        self.line_y = self._base_line_y + int(self._shake_offset[1])
        self.particle_system.line_y = self.line_y
        
        # Update particle system
        self.particle_system.update(self._last_dt)
        
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
        self._strain_origin_x = player_screen_x

        # Draw the line background after camera/strain origin are known.
        self._draw_line_background()
        
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

        if self._dimensional_flash > 0.01:
            flash = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            flash.fill((205, 228, 255, int(58 * self._dimensional_flash)))
            self.screen.blit(flash, (0, 0))
        
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
        # Atmosphere and star field.
        self._draw_background_stars()
        self._draw_energy_bands()
        
        # Draw gradient background strip around the line.
        strip_top = self.line_y - self.line_height // 2
        strip_rect = pygame.Rect(0, strip_top, self.width, self.line_height)

        strip = pygame.Surface((self.width, self.line_height), pygame.SRCALPHA)
        for y in range(self.line_height):
            t = abs((y / max(1, self.line_height - 1)) - 0.5) * 2.0
            alpha = int(145 * (1.0 - t * 0.75))
            color = (16 + int(20 * (1.0 - t)), 22 + int(18 * (1.0 - t)), 42 + int(26 * (1.0 - t)), max(0, alpha))
            pygame.draw.line(strip, color, (0, y), (self.width, y), 1)
        self.screen.blit(strip, (0, strip_top))

        def line_points(step: int, offset: float = 0.0, bend_scale: float = 1.0) -> list[tuple[int, int]]:
            return [
                (sx, self._line_y_at_screen_x(sx, offset=offset, bend_scale=bend_scale))
                for sx in range(-20, self.width + 21, step)
            ]

        # Upper/lower guide rails.
        rail_color = (52, 72, 108)
        upper = line_points(12, offset=-24.0, bend_scale=0.42)
        lower = line_points(12, offset=24.0, bend_scale=0.42)
        if len(upper) > 1:
            pygame.draw.lines(self.screen, rail_color, False, upper, 1)
        if len(lower) > 1:
            pygame.draw.lines(self.screen, rail_color, False, lower, 1)

        # Draw the main line with glow.
        main_points = line_points(10)
        if len(main_points) > 1:
            pygame.draw.lines(self.screen, (22, 34, 62), False, main_points, 8)
            pygame.draw.lines(self.screen, (86, 122, 182), False, main_points, 3)
            pygame.draw.lines(self.screen, (140, 184, 238), False, main_points, 1)
        
        # Slight oscillating waveform to make the line feel alive.
        wave_points = []
        for sx in range(0, self.width + 20, 20):
            wx = (sx - self.width / 2) / self.scale + self.camera_offset[0]
            offset = math.sin(wx * 0.8 + self._bg_time * 2.2) * 3.0
            wave_points.append((sx, self._line_y_at_screen_x(sx, offset=-14 + offset, bend_scale=0.65)))
        if len(wave_points) > 1:
            pygame.draw.lines(self.screen, (90, 116, 165), False, wave_points, 1)
        
        # Ambient motes above/below the line add subtle kinetic movement.
        self._draw_ambient_motes()
        
        # Draw grid markers (major/minor).
        grid_spacing = 2.5  # World units
        start_world = self.camera_offset[0] - self.width / (2 * self.scale)
        end_world = self.camera_offset[0] + self.width / (2 * self.scale)
        
        marker_start = int(start_world / grid_spacing) * grid_spacing
        for wx in np.arange(marker_start, end_world + grid_spacing, grid_spacing):
            sx, _ = self.world_to_screen(wx)
            if 0 <= sx <= self.width:
                is_major = int(abs(round(wx))) % 10 == 0
                marker_len = 16 if is_major else 8
                marker_color = (74, 98, 142) if is_major else (44, 56, 88)
                marker_y = self._line_y_at_screen_x(sx, bend_scale=0.52)
                pygame.draw.line(
                    self.screen,
                    marker_color,
                    (sx, marker_y - marker_len),
                    (sx, marker_y + marker_len),
                    1
                )
    
    def _draw_background_stars(self) -> None:
        """Draw a subtle parallax star field."""
        for star in self._background_stars:
            x = ((star["x"] - self.camera_offset[0] * self.scale * star["parallax"]) + self.width + 140) % (self.width + 280) - 140
            y = star["y"]
            twinkle = 0.65 + 0.35 * math.sin(self._bg_time * star["twinkle"] + star["phase"])
            size = max(1, int(star["size"] * (0.8 + twinkle * 0.6)))
            color_value = int(120 + 100 * twinkle)
            color = (color_value, color_value + 12, min(255, color_value + 35))
            pygame.draw.circle(self.screen, color, (int(x), int(y)), size)

    def _draw_energy_bands(self) -> None:
        """Draw animated background bands to make the line world feel active."""
        overlay = self._fx_overlay
        overlay.fill((0, 0, 0, 0))
        bands = [
            {"amp": 11.0, "speed": 1.2, "offset": -58.0, "color": (34, 56, 96, 42), "step": 22, "thickness": 2},
            {"amp": 9.0, "speed": 1.6, "offset": 56.0, "color": (28, 46, 82, 38), "step": 24, "thickness": 2},
            {"amp": 6.0, "speed": 2.3, "offset": -34.0, "color": (55, 88, 138, 30), "step": 26, "thickness": 1},
        ]
        for i, band in enumerate(bands):
            points = []
            for sx in range(0, self.width + band["step"], band["step"]):
                wx = (sx - self.width / 2) / self.scale + self.camera_offset[0]
                phase = wx * 0.7 + self._bg_time * band["speed"] + i * 1.3
                y = self.line_y + band["offset"] + math.sin(phase) * band["amp"]
                points.append((sx, int(y)))
            if len(points) > 1:
                pygame.draw.lines(
                    overlay,
                    band["color"],
                    False,
                    points,
                    band["thickness"],
                )
        self.screen.blit(overlay, (0, 0))

    def _draw_ambient_motes(self) -> None:
        """Draw drifting glow motes around the line."""
        overlay = self._fx_overlay
        overlay.fill((0, 0, 0, 0))
        span = self.width + 260.0
        for mote in self._ambient_motes:
            mote["x"] -= mote["speed"] * self._last_dt
            if mote["x"] < -130.0:
                mote["x"] += span
            
            y = self.line_y + mote["y_offset"] + math.sin(self._bg_time * 1.8 + mote["phase"]) * 6.0
            flicker = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(self._bg_time * 3.1 + mote["phase"]))
            alpha = int(80 * flicker)
            size = max(1, int(mote["size"] * (0.8 + 0.4 * flicker)))
            x = int(mote["x"])
            yi = int(y)
            trail = int(mote["trail"])
            
            pygame.draw.line(
                overlay,
                (120, 170, 230, int(alpha * 0.45)),
                (x - trail, yi),
                (x, yi),
                max(1, size - 1),
            )
            pygame.draw.circle(overlay, (170, 220, 255, alpha), (x, yi), size)
        self.screen.blit(overlay, (0, 0))
    
    def _fade_color(self, color: tuple[int, int, int], alpha: int) -> tuple[int, int, int]:
        """Apply alpha fade to an RGB color."""
        f = max(0.0, min(1.0, alpha / 255.0))
        return (
            int(color[0] * f),
            int(color[1] * f),
            int(color[2] * f),
        )

    def _sz(self, value: float) -> int:
        """Scale pixel sizes for 1D sprites."""
        return max(1, int(round(value * self.sprite_scale)))
    
    def _draw_glow_circle(
        self,
        x: int,
        y: int,
        radius: int,
        color: tuple[int, int, int],
        alpha: int,
    ) -> None:
        """Draw a soft glowing circle."""
        r = max(1, radius)
        surf = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
        glow_alpha = max(15, alpha)
        pygame.draw.circle(surf, (*color, glow_alpha), (r + 4, r + 4), r)
        self.screen.blit(surf, (x - r - 4, y - r - 4))
    
    def _render_entity(self, entity: "Entity", player_x: float) -> None:
        """Render a single entity on the line."""
        transform = entity.get(Transform)
        renderable = entity.get(Renderable)
        brain = entity.get(AIBrain)
        
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
        base_size = self._sz(8)
        confused_timer = float(brain.get_state("confused_timer", 0.0)) if brain else 0.0
        local_line_y = self._line_y_at_screen_x(screen_x)
        if confused_timer > 0.0:
            phase = float(brain.get_state("confusion_phase", 0.0))
            screen_x += int(math.sin(self._bg_time * 15.0 + phase + world_x * 0.3) * self._sz(min(4.0, 1.2 + confused_timer * 1.8)))
            local_line_y += int(math.cos(self._bg_time * 12.0 + phase) * self._sz(min(3.0, 0.8 + confused_timer * 0.8)))
        
        old_line_y = self.line_y
        self.line_y = local_line_y
        
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
        
        self.line_y = old_line_y
        if confused_timer > 0.0:
            self._draw_confusion_halo(screen_x, local_line_y, confused_timer)
    
    def _draw_player(self, screen_x: int, color: tuple, alpha: int) -> None:
        """Draw the player entity."""
        main_color = self._fade_color(color, alpha)
        glow_color = (
            min(255, main_color[0] + 50),
            min(255, main_color[1] + 70),
            min(255, main_color[2] + 90),
        )
        pulse = 1.0 + 0.15 * math.sin(self._bg_time * 6.0)
        
        # Halo
        self._draw_glow_circle(screen_x, self.line_y, self._sz(22 * pulse), glow_color, 44)
        self._draw_glow_circle(screen_x, self.line_y, self._sz(15 * pulse), glow_color, 82)
        
        # Core and ring
        pygame.draw.circle(self.screen, main_color, (screen_x, self.line_y), self._sz(10))
        pygame.draw.circle(self.screen, (235, 248, 255), (screen_x, self.line_y), self._sz(5))
        pygame.draw.circle(self.screen, (140, 220, 255), (screen_x, self.line_y), self._sz(14), max(1, self._sz(2) // 2))

        if self._dimensional_strain > 0.02:
            stretch = 1.0 + self._dimensional_strain * 0.7
            axis_pull = -self._dimensional_axis * self._sz(10 + 8 * self._dimensional_strain)
            arc_rect = pygame.Rect(0, 0, self._sz(34), int(self._sz(28) * stretch))
            arc_rect.center = (screen_x, self.line_y + axis_pull * 0.2)
            pygame.draw.ellipse(self.screen, (185, 230, 255), arc_rect, 2)
            pygame.draw.line(
                self.screen,
                (215, 240, 255),
                (screen_x, self.line_y - axis_pull),
                (screen_x, self.line_y + axis_pull),
                max(1, self._sz(2) // 2),
            )
            for idx in range(3):
                surge = 18 + idx * 10
                alpha_ring = max(18, 80 - idx * 22)
                self._draw_glow_circle(
                    screen_x,
                    self.line_y + int(axis_pull * 0.25),
                    self._sz(surge * self._dimensional_strain),
                    (170, 220, 255),
                    alpha_ring,
                )
    
    def _draw_enemy(self, entity: "Entity", screen_x: int, color: tuple, alpha: int) -> None:
        """Draw an enemy entity."""
        health = entity.get(Health)
        base = self._fade_color(color, alpha)
        
        if entity.has_tag("point_spirit"):
            self._draw_point_spirit(screen_x, base, alpha)
        elif entity.has_tag("line_walker"):
            self._draw_line_walker(screen_x, base, alpha)
        elif entity.has_tag("forward_sentinel"):
            self._draw_forward_sentinel(screen_x, base, alpha)
        elif entity.has_tag("void_echo"):
            self._draw_void_echo(screen_x, base, alpha)
        elif entity.has_tag("toll_collector"):
            self._draw_toll_collector(screen_x, base, alpha)
        elif entity.has_tag("segment_guardian"):
            self._draw_segment_guardian(screen_x, base, alpha)
        else:
            self._draw_hostile_generic(screen_x, base, alpha)
        
        # Health bar
        if health and health.ratio < 1.0:
            bar_width = self._sz(22)
            bar_height = self._sz(4)
            bar_x = screen_x - bar_width // 2
            bar_y = self.line_y - self._sz(24)
            
            # Background
            pygame.draw.rect(self.screen, (60, 20, 20), (bar_x, bar_y, bar_width, bar_height))
            # Health
            pygame.draw.rect(
                self.screen, (200, 50, 50),
                (bar_x, bar_y, int(bar_width * health.ratio), bar_height)
            )
    
    def _draw_hostile_generic(self, screen_x: int, color: tuple, alpha: int) -> None:
        enemy_color = (
            min(255, color[0] + 40),
            max(40, color[1] - 30),
            max(40, color[2] - 40),
        )
        dx = self._sz(9)
        dy = self._sz(13)
        points = [
            (screen_x, self.line_y - dy),
            (screen_x + dx, self.line_y),
            (screen_x, self.line_y + dy),
            (screen_x - dx, self.line_y),
        ]
        pygame.draw.polygon(self.screen, enemy_color, points)
        pygame.draw.polygon(self.screen, (255, 128, 128), points, max(1, self._sz(2) // 2))
    
    def _draw_point_spirit(self, screen_x: int, color: tuple, alpha: int) -> None:
        spirit = (max(140, color[0]), max(160, color[1]), max(180, color[2]))
        self._draw_glow_circle(screen_x, self.line_y, self._sz(20), spirit, 46)
        pygame.draw.circle(self.screen, spirit, (screen_x, self.line_y), self._sz(9))
        pygame.draw.circle(self.screen, (255, 255, 245), (screen_x, self.line_y - self._sz(1)), self._sz(3))
    
    def _draw_line_walker(self, screen_x: int, color: tuple, alpha: int) -> None:
        offset = int(math.sin(self._bg_time * 4.0 + screen_x * 0.02) * self._sz(3))
        c1 = (max(90, color[0]), min(255, color[1] + 30), min(255, color[2] + 30))
        c2 = (min(255, c1[0] + 35), min(255, c1[1] + 20), min(255, c1[2] + 10))
        half = self._sz(11)
        orb = self._sz(7)
        pygame.draw.line(self.screen, c2, (screen_x - half, self.line_y - offset), (screen_x + half, self.line_y + offset), self._sz(3))
        pygame.draw.circle(self.screen, c1, (screen_x - self._sz(9), self.line_y - offset), orb)
        pygame.draw.circle(self.screen, c1, (screen_x + self._sz(9), self.line_y + offset), orb)
    
    def _draw_forward_sentinel(self, screen_x: int, color: tuple, alpha: int) -> None:
        blade = (min(255, color[0] + 80), max(45, color[1] - 40), max(45, color[2] - 40))
        self._draw_glow_circle(screen_x + self._sz(5), self.line_y, self._sz(18), blade, 36)
        dx = self._sz(13)
        dy = self._sz(11)
        points = [
            (screen_x - dx, self.line_y - dy),
            (screen_x + dx, self.line_y),
            (screen_x - dx, self.line_y + dy),
        ]
        pygame.draw.polygon(self.screen, blade, points)
        pygame.draw.line(
            self.screen,
            (255, 180, 150),
            (screen_x - self._sz(9), self.line_y),
            (screen_x + self._sz(11), self.line_y),
            max(1, self._sz(2) // 2),
        )
    
    def _draw_void_echo(self, screen_x: int, color: tuple, alpha: int) -> None:
        base = (max(50, color[0] - 20), max(50, color[1] - 10), min(255, color[2] + 30))
        radius = self._sz(11) + int(self._sz(2) * math.sin(self._bg_time * 3.0 + screen_x * 0.01))
        pygame.draw.circle(self.screen, base, (screen_x, self.line_y), radius, max(1, self._sz(2) // 2))
        pygame.draw.circle(self.screen, (120, 90, 160), (screen_x + self._sz(3), self.line_y - self._sz(2)), self._sz(5), 1)
        pygame.draw.line(
            self.screen,
            (90, 80, 130),
            (screen_x - radius, self.line_y + self._sz(2)),
            (screen_x + radius, self.line_y - self._sz(2)),
            1,
        )
    
    def _draw_toll_collector(self, screen_x: int, color: tuple, alpha: int) -> None:
        coin = (220, 185, 95)
        radius = self._sz(10)
        self._draw_glow_circle(screen_x, self.line_y, self._sz(16), coin, 46)
        pygame.draw.circle(self.screen, coin, (screen_x, self.line_y), radius)
        pygame.draw.circle(self.screen, (255, 236, 170), (screen_x, self.line_y), radius, max(1, self._sz(2) // 2))
        pygame.draw.line(
            self.screen,
            (120, 90, 40),
            (screen_x, self.line_y - self._sz(5)),
            (screen_x, self.line_y + self._sz(5)),
            max(1, self._sz(2) // 2),
        )
    
    def _draw_segment_guardian(self, screen_x: int, color: tuple, alpha: int) -> None:
        guardian = (255, 190, 110)
        self._draw_glow_circle(screen_x, self.line_y, self._sz(26), guardian, 44)
        dx = self._sz(13)
        dy = self._sz(15)
        mid_y = self._sz(8)
        points = [
            (screen_x, self.line_y - dy),
            (screen_x + dx, self.line_y - mid_y),
            (screen_x + dx, self.line_y + mid_y),
            (screen_x, self.line_y + dy),
            (screen_x - dx, self.line_y + mid_y),
            (screen_x - dx, self.line_y - mid_y),
        ]
        pygame.draw.polygon(self.screen, guardian, points)
        pygame.draw.polygon(self.screen, (255, 230, 170), points, max(1, self._sz(2) // 2))
        orbit_x = screen_x + int(math.cos(self._bg_time * 2.5) * self._sz(19))
        orbit_y = self.line_y + int(math.sin(self._bg_time * 2.5) * self._sz(8))
        pygame.draw.circle(self.screen, (255, 240, 190), (orbit_x, orbit_y), self._sz(3))
    
    def _draw_pickup(self, entity: "Entity", screen_x: int, alpha: int) -> None:
        """Draw a pickup item."""
        pickup = entity.get(Pickup)
        
        # Yellow/gold for pickups
        color = (255, 220, 50)
        
        # Pulsing effect
        pulse = abs(pygame.time.get_ticks() % 1000 - 500) / 500.0
        size = self._sz(6 + pulse * 3)
        
        self._draw_glow_circle(screen_x, self.line_y, size + self._sz(7), color, 40)
        pygame.draw.circle(self.screen, color, (screen_x, self.line_y), size)
        pygame.draw.circle(self.screen, (255, 255, 200), (screen_x, self.line_y), size, max(1, self._sz(2) // 2))
    
    def _draw_portal(self, entity: "Entity", screen_x: int, alpha: int) -> None:
        """Draw a dimension portal."""
        portal = entity.get(Portal)
        
        # Purple for portals
        color = (150, 50, 255) if portal.active else (80, 40, 100)
        
        # Draw portal frame
        pygame.draw.circle(self.screen, color, (screen_x, self.line_y), self._sz(15), max(1, self._sz(3) // 2))
        pygame.draw.circle(self.screen, (200, 150, 255), (screen_x, self.line_y), self._sz(10), max(1, self._sz(2) // 2))
        
        # Inner glow
        if portal.active:
            for i in range(5):
                a = 100 - i * 20
                pygame.draw.circle(
                    self.screen,
                    (150 + i * 20, 100, 255),
                    (screen_x, self.line_y),
                    self._sz(max(2, 8 - i))
                )
    
    def _draw_first_point(self, screen_x: int, alpha: int) -> None:
        """Draw the First Point NPC with special purple glow effect."""
        # Purple color for the First Point
        base_color = (180, 100, 255)
        
        # Pulse animation
        pulse = math.sin(pygame.time.get_ticks() / 800.0) * 0.15 + 1.0
        
        # Draw outer glow layers (largest to smallest)
        glow_layers = 10
        max_glow_radius = self._sz(60 * pulse)
        
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
        max_core_radius = self._sz(20 * pulse)
        
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
        center_size = self._sz(6 * pulse)
        pygame.draw.circle(self.screen, (255, 255, 255), (screen_x, self.line_y), center_size)
        
        # Draw interaction hint when player is nearby
        font = pygame.font.Font(None, 18)
        hint_text = font.render("Press E to talk", True, (200, 180, 255))
        hint_rect = hint_text.get_rect(center=(screen_x, self.line_y - self._sz(45)))
        self.screen.blit(hint_text, hint_rect)
    
    def _draw_npc(self, entity: "Entity", screen_x: int, color: tuple, alpha: int) -> None:
        """Draw a friendly NPC entity."""
        c = self._fade_color(color, alpha)
        glow_color = (
            min(255, c[0] + 40),
            min(255, c[1] + 40),
            min(255, c[2] + 40)
        )
        self._draw_glow_circle(screen_x, self.line_y, self._sz(16), glow_color, 46)
        pygame.draw.circle(self.screen, c, (screen_x, self.line_y), self._sz(10))
        
        # White highlight
        pygame.draw.circle(self.screen, (255, 255, 255), (screen_x, self.line_y), self._sz(4))
    
    def _draw_point(self, screen_x: int, color: tuple, size: int, alpha: int) -> None:
        """Draw a generic point entity."""
        c = self._fade_color(color, alpha)
        self._draw_glow_circle(screen_x, self.line_y, size + self._sz(5), c, 30)
        pygame.draw.circle(self.screen, c, (screen_x, self.line_y), size)
    
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
                elif entity.has_tag("enemy") or entity.has_tag("encounter_trigger"):
                    pygame.draw.circle(self.screen, (255, 80, 80), (mx, my), 3)
                elif entity.has_tag("friendly"):
                    pygame.draw.circle(self.screen, (120, 220, 160), (mx, my), 3)
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
        dim_text = font.render("1D - Monodia", True, (150, 170, 215))
        self.screen.blit(dim_text, (self.width - 150, self.height - 30))
        
        # Realm hint based on player position to make traversal feel less abstract.
        if player:
            transform = player.get(Transform)
            if transform is not None:
                x = float(transform.position[0])
                if x < -10.0:
                    realm = "Backward Void"
                elif x < 5.0:
                    realm = "Origin Point"
                elif x < 20.0:
                    realm = "Forward Path"
                elif x < 30.0:
                    realm = "Midpoint Station"
                else:
                    realm = "The Endpoint"
                realm_text = font.render(realm, True, (180, 190, 215))
                realm_rect = realm_text.get_rect(center=(self.width // 2, 52))
                self.screen.blit(realm_text, realm_rect)
