"""3D Volume renderer - wireframe 3D with perspective projection."""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional, List, Tuple

import pygame
import numpy as np
from numpy.typing import NDArray

from .base_renderer import DimensionRenderer
from hypersim.game.ecs.component import (
    Transform, Renderable, Collider, ColliderShape,
    Health, DimensionAnchor, Pickup, Portal
)

if TYPE_CHECKING:
    from hypersim.game.ecs.world import World
    from hypersim.game.ecs.entity import Entity
    from hypersim.game.dimensions import DimensionSpec
    from hypersim.game.controllers.volume_controller import VolumeController


class VolumeRenderer(DimensionRenderer):
    """Renderer for 3D volume world (wireframe FPS view)."""
    
    dimension_id = "3d"
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.background_color = (5, 8, 15)
        self.fov = 90.0  # Field of view in degrees
        self.near_plane = 0.1
        self.far_plane = 100.0
        
        # Camera state
        self.camera_pos = np.array([0.0, 1.5, 0.0])  # Eye height
        self.camera_yaw = 0.0
        self.camera_pitch = 0.0
        
        # Projection matrix cache
        self._update_projection()
        
        # Floor grid
        self.grid_enabled = True
        self.grid_size = 40
        self.grid_spacing = 2.0
        
        # Crosshair
        self.crosshair_enabled = True
    
    def _update_projection(self) -> None:
        """Update the perspective projection matrix."""
        aspect = self.width / self.height
        fov_rad = math.radians(self.fov)
        f = 1.0 / math.tan(fov_rad / 2)
        
        self.proj_matrix = np.array([
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (self.far_plane + self.near_plane) / (self.near_plane - self.far_plane), -1],
            [0, 0, (2 * self.far_plane * self.near_plane) / (self.near_plane - self.far_plane), 0]
        ])
    
    def _get_view_matrix(self) -> NDArray:
        """Compute the view matrix from camera orientation."""
        cos_yaw = math.cos(self.camera_yaw)
        sin_yaw = math.sin(self.camera_yaw)
        cos_pitch = math.cos(self.camera_pitch)
        sin_pitch = math.sin(self.camera_pitch)
        
        # Forward, right, up vectors
        forward = np.array([
            -sin_yaw * cos_pitch,
            sin_pitch,
            -cos_yaw * cos_pitch
        ])
        right = np.array([cos_yaw, 0.0, -sin_yaw])
        up = np.cross(right, forward)
        
        # View matrix (rotation part)
        rotation = np.array([
            [right[0], right[1], right[2]],
            [up[0], up[1], up[2]],
            [-forward[0], -forward[1], -forward[2]]
        ])
        
        # Translation
        translated_pos = -rotation @ self.camera_pos[:3]
        
        view = np.eye(4)
        view[:3, :3] = rotation
        view[:3, 3] = translated_pos
        
        return view
    
    def project_point(self, point: NDArray) -> Optional[Tuple[int, int, float]]:
        """Project a 3D point to screen coordinates.
        
        Returns:
            (screen_x, screen_y, depth) or None if behind camera
        """
        # Transform to view space
        view = self._get_view_matrix()
        p = np.array([point[0], point[1], point[2], 1.0])
        view_pos = view @ p
        
        # Behind camera check
        if view_pos[2] >= -self.near_plane:
            return None
        
        # Project
        proj_pos = self.proj_matrix @ view_pos
        
        if proj_pos[3] == 0:
            return None
        
        # Perspective divide
        ndc = proj_pos[:3] / abs(proj_pos[3])
        
        # NDC to screen
        screen_x = int((ndc[0] + 1) * self.width / 2)
        screen_y = int((1 - ndc[1]) * self.height / 2)
        depth = -view_pos[2]
        
        return (screen_x, screen_y, depth)
    
    def render(self, world: "World", dimension_spec: Optional["DimensionSpec"] = None) -> None:
        """Render the 3D world."""
        self.clear()
        
        # Update camera from player
        player = world.find_player()
        if player:
            self._update_camera_from_player(player)
        
        # Draw floor grid
        if self.grid_enabled:
            self._draw_floor_grid()
        
        # Get entities in 3D
        entities = world.in_dimension("3d")
        
        # Sort by distance for proper rendering
        def get_dist(e):
            t = e.get(Transform)
            if not t:
                return float('inf')
            return np.linalg.norm(t.position[:3] - self.camera_pos)
        
        entities.sort(key=get_dist, reverse=True)  # Far to near
        
        # Render entities
        for entity in entities:
            if not entity.active:
                continue
            if entity.has_tag("player"):
                continue  # Don't render player in FPS view
            self._render_entity(entity)
        
        # Draw crosshair
        if self.crosshair_enabled:
            self._draw_crosshair()
        
        # Draw UI
        self._draw_ui(world, player)
    
    def _update_camera_from_player(self, player: "Entity") -> None:
        """Update camera position and orientation from player."""
        transform = player.get(Transform)
        if transform:
            self.camera_pos = transform.position[:3].copy()
            self.camera_pos[1] += 1.5  # Eye height
        
        # Get controller for orientation
        from hypersim.game.ecs.component import Controller
        controller = player.get(Controller)
        if controller and hasattr(controller, 'yaw'):
            self.camera_yaw = controller.yaw
            self.camera_pitch = controller.pitch
    
    def _draw_floor_grid(self) -> None:
        """Draw a floor grid for spatial reference."""
        grid_color = (30, 35, 45)
        grid_color_major = (50, 55, 70)
        
        half = self.grid_size // 2
        
        for i in range(-half, half + 1):
            # Lines parallel to X axis
            start = np.array([i * self.grid_spacing, 0.0, -half * self.grid_spacing])
            end = np.array([i * self.grid_spacing, 0.0, half * self.grid_spacing])
            color = grid_color_major if i % 5 == 0 else grid_color
            self._draw_line_3d(start, end, color)
            
            # Lines parallel to Z axis
            start = np.array([-half * self.grid_spacing, 0.0, i * self.grid_spacing])
            end = np.array([half * self.grid_spacing, 0.0, i * self.grid_spacing])
            self._draw_line_3d(start, end, color)
    
    def _draw_line_3d(self, start: NDArray, end: NDArray, color: Tuple[int, int, int], width: int = 1) -> None:
        """Draw a line in 3D space."""
        p1 = self.project_point(start)
        p2 = self.project_point(end)
        
        if p1 is None or p2 is None:
            return
        
        # Clip to screen bounds (roughly)
        if not self._line_visible(p1, p2):
            return
        
        pygame.draw.line(self.screen, color, (p1[0], p1[1]), (p2[0], p2[1]), width)
    
    def _line_visible(self, p1: Tuple, p2: Tuple) -> bool:
        """Check if a line is at least partially visible."""
        margin = 100
        if (p1[0] < -margin and p2[0] < -margin) or (p1[0] > self.width + margin and p2[0] > self.width + margin):
            return False
        if (p1[1] < -margin and p2[1] < -margin) or (p1[1] > self.height + margin and p2[1] > self.height + margin):
            return False
        return True
    
    def _render_entity(self, entity: "Entity") -> None:
        """Render a single entity in 3D."""
        transform = entity.get(Transform)
        renderable = entity.get(Renderable)
        
        if not transform:
            return
        if renderable and not renderable.visible:
            return
        
        pos = transform.position[:3]
        color = renderable.color if renderable else (255, 255, 255)
        
        # Project center point
        center = self.project_point(pos)
        if center is None:
            return
        
        # Different rendering based on entity type
        if entity.has_tag("enemy"):
            self._draw_enemy_3d(entity, pos, color, center)
        elif entity.get(Pickup):
            self._draw_pickup_3d(entity, pos, center)
        elif entity.get(Portal):
            self._draw_portal_3d(entity, pos, center)
        else:
            self._draw_generic_3d(entity, pos, color, center)
    
    def _draw_enemy_3d(self, entity: "Entity", pos: NDArray, color: Tuple, center: Tuple) -> None:
        """Draw an enemy as a wireframe shape."""
        health = entity.get(Health)
        
        # Draw as wireframe diamond/octahedron
        size = 0.8
        vertices = [
            pos + np.array([0, size, 0]),      # Top
            pos + np.array([size, 0, 0]),      # Right
            pos + np.array([0, 0, size]),      # Front
            pos + np.array([-size, 0, 0]),     # Left
            pos + np.array([0, 0, -size]),     # Back
            pos + np.array([0, -size, 0]),     # Bottom
        ]
        
        edges = [
            (0, 1), (0, 2), (0, 3), (0, 4),  # Top to middle
            (5, 1), (5, 2), (5, 3), (5, 4),  # Bottom to middle
            (1, 2), (2, 3), (3, 4), (4, 1),  # Middle ring
        ]
        
        enemy_color = (200, 60, 60)
        for e in edges:
            self._draw_line_3d(vertices[e[0]], vertices[e[1]], enemy_color, 2)
        
        # Health bar (billboard)
        if health and health.ratio < 1.0:
            bar_pos = pos + np.array([0, size + 0.3, 0])
            proj = self.project_point(bar_pos)
            if proj:
                bar_width = 30
                bar_height = 4
                bar_x = proj[0] - bar_width // 2
                bar_y = proj[1]
                pygame.draw.rect(self.screen, (60, 20, 20), (bar_x, bar_y, bar_width, bar_height))
                pygame.draw.rect(self.screen, (200, 50, 50), (bar_x, bar_y, int(bar_width * health.ratio), bar_height))
    
    def _draw_pickup_3d(self, entity: "Entity", pos: NDArray, center: Tuple) -> None:
        """Draw a pickup as a rotating cube wireframe."""
        time = pygame.time.get_ticks() / 1000.0
        angle = time * 2
        
        size = 0.3
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        # Rotated cube vertices
        base_verts = [
            np.array([-1, -1, -1]),
            np.array([1, -1, -1]),
            np.array([1, 1, -1]),
            np.array([-1, 1, -1]),
            np.array([-1, -1, 1]),
            np.array([1, -1, 1]),
            np.array([1, 1, 1]),
            np.array([-1, 1, 1]),
        ]
        
        vertices = []
        for v in base_verts:
            # Rotate around Y axis
            rotated = np.array([
                v[0] * cos_a - v[2] * sin_a,
                v[1],
                v[0] * sin_a + v[2] * cos_a
            ])
            vertices.append(pos + rotated * size)
        
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # Bottom
            (4, 5), (5, 6), (6, 7), (7, 4),  # Top
            (0, 4), (1, 5), (2, 6), (3, 7),  # Sides
        ]
        
        color = (255, 220, 50)
        for e in edges:
            self._draw_line_3d(vertices[e[0]], vertices[e[1]], color, 1)
    
    def _draw_portal_3d(self, entity: "Entity", pos: NDArray, center: Tuple) -> None:
        """Draw a portal as an animated ring."""
        portal = entity.get(Portal)
        time = pygame.time.get_ticks() / 1000.0
        
        color = (150, 80, 255) if portal.active else (80, 40, 100)
        
        # Draw vertical ring
        segments = 16
        radius = 1.5
        
        for i in range(segments):
            angle1 = (i / segments) * 2 * math.pi
            angle2 = ((i + 1) / segments) * 2 * math.pi
            
            # Ring in XY plane (vertical)
            p1 = pos + np.array([math.cos(angle1) * radius, math.sin(angle1) * radius, 0])
            p2 = pos + np.array([math.cos(angle2) * radius, math.sin(angle2) * radius, 0])
            self._draw_line_3d(p1, p2, color, 2)
        
        # Inner glow rings (animated)
        for r in range(3):
            inner_radius = radius * (0.3 + 0.2 * r)
            offset = (time * 3 + r * 0.3) % 1.0
            inner_color = (
                min(255, color[0] + int(offset * 50)),
                min(255, color[1] + int(offset * 30)),
                color[2]
            )
            
            for i in range(segments):
                angle1 = (i / segments) * 2 * math.pi
                angle2 = ((i + 1) / segments) * 2 * math.pi
                p1 = pos + np.array([math.cos(angle1) * inner_radius, math.sin(angle1) * inner_radius, 0])
                p2 = pos + np.array([math.cos(angle2) * inner_radius, math.sin(angle2) * inner_radius, 0])
                self._draw_line_3d(p1, p2, inner_color, 1)
    
    def _draw_generic_3d(self, entity: "Entity", pos: NDArray, color: Tuple, center: Tuple) -> None:
        """Draw a generic entity as a wireframe cube."""
        collider = entity.get(Collider)
        size = 0.5
        if collider and len(collider.size) > 0:
            size = collider.size[0]
        
        # Cube vertices
        vertices = [
            pos + np.array([-size, -size, -size]),
            pos + np.array([size, -size, -size]),
            pos + np.array([size, size, -size]),
            pos + np.array([-size, size, -size]),
            pos + np.array([-size, -size, size]),
            pos + np.array([size, -size, size]),
            pos + np.array([size, size, size]),
            pos + np.array([-size, size, size]),
        ]
        
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7),
        ]
        
        for e in edges:
            self._draw_line_3d(vertices[e[0]], vertices[e[1]], color, 1)
    
    def _draw_crosshair(self) -> None:
        """Draw a crosshair in the center of the screen."""
        cx, cy = self.width // 2, self.height // 2
        size = 10
        color = (200, 200, 200)
        
        pygame.draw.line(self.screen, color, (cx - size, cy), (cx + size, cy), 1)
        pygame.draw.line(self.screen, color, (cx, cy - size), (cx, cy + size), 1)
    
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
                pygame.draw.rect(self.screen, (50, 180, 80), (bar_x, bar_y, int(bar_width * health.ratio), bar_height))
                pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height), 1)
                
                health_text = font.render(f"HP: {int(health.current)}/{int(health.max)}", True, (200, 200, 200))
                self.screen.blit(health_text, (bar_x + bar_width + 10, bar_y))
            
            # Position
            transform = player.get(Transform)
            if transform:
                pos = transform.position
                coord_text = font.render(
                    f"({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})",
                    True, (100, 100, 120)
                )
                self.screen.blit(coord_text, (20, 20))
        
        # Dimension label
        dim_text = font.render("3D - Volume Space", True, (150, 150, 200))
        self.screen.blit(dim_text, (self.width - 150, self.height - 30))
        
        # Controls hint
        controls = font.render("WASD: Move | Mouse: Look | Space: Up | Ctrl: Down", True, (80, 80, 100))
        self.screen.blit(controls, (10, self.height - 20))
