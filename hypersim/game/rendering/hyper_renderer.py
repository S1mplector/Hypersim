"""4D Hyper renderer - integrates existing HyperSim 4D visualization."""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional, List, Tuple

import pygame
import numpy as np
from numpy.typing import NDArray

from .volume_renderer import VolumeRenderer
from hypersim.game.ecs.component import (
    Transform, Renderable, Collider, ColliderShape,
    Health, DimensionAnchor, Pickup, Portal
)

if TYPE_CHECKING:
    from hypersim.game.ecs.world import World
    from hypersim.game.ecs.entity import Entity
    from hypersim.game.dimensions import DimensionSpec
    from hypersim.game.evolution import EvolutionState, PolytopeForm


class HyperRenderer(VolumeRenderer):
    """Renderer for 4D hyperspace - extends 3D with W-axis slicing."""
    
    dimension_id = "4d"
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.background_color = (3, 5, 12)
        
        # 4D projection settings
        self.w_slice = 0.0  # Current W position for cross-section
        self.w_thickness = 0.5  # How thick the W slice is
        self.projection_distance_4d = 3.0  # 4D perspective distance
        
        # Visualization modes
        self.show_w_indicator = True
        self.show_lower_dims = True  # Show 1D/2D/3D as overlays
        
        # 4D rotation angles (for objects)
        self.rotation_xw = 0.0
        self.rotation_yw = 0.0
        self.rotation_zw = 0.0
        
        # Player polytope rendering
        self._player_rotation = 0.0
        self._evolution_state: Optional["EvolutionState"] = None
        self._evolution_ui = None
    
    def project_point_4d(self, point: NDArray) -> Optional[Tuple[int, int, float]]:
        """Project a 4D point to screen coordinates via 4D→3D→2D projection.
        
        Args:
            point: 4D point (x, y, z, w)
            
        Returns:
            (screen_x, screen_y, depth) or None if not visible
        """
        if len(point) < 4:
            # Treat as 3D point
            return self.project_point(point)
        
        # Apply 4D rotations
        p4d = self._rotate_4d(point)
        
        # 4D to 3D perspective projection
        w = p4d[3] - self.w_slice
        
        # Check if within W slice
        if abs(w) > self.w_thickness * 2:
            return None
        
        # Perspective factor based on W distance
        w_factor = self.projection_distance_4d / (self.projection_distance_4d + w)
        if w_factor <= 0:
            return None
        
        # Project to 3D
        p3d = np.array([
            p4d[0] * w_factor,
            p4d[1] * w_factor,
            p4d[2] * w_factor
        ])
        
        # Then project 3D to 2D
        result = self.project_point(p3d)
        if result:
            # Adjust depth based on W
            return (result[0], result[1], result[2] + abs(w) * 10)
        return None
    
    def _rotate_4d(self, point: NDArray) -> NDArray:
        """Apply 4D rotations to a point."""
        p = point.copy()
        
        # XW rotation
        if self.rotation_xw != 0:
            cos_a = math.cos(self.rotation_xw)
            sin_a = math.sin(self.rotation_xw)
            x, w = p[0], p[3]
            p[0] = x * cos_a - w * sin_a
            p[3] = x * sin_a + w * cos_a
        
        # YW rotation
        if self.rotation_yw != 0:
            cos_a = math.cos(self.rotation_yw)
            sin_a = math.sin(self.rotation_yw)
            y, w = p[1], p[3]
            p[1] = y * cos_a - w * sin_a
            p[3] = y * sin_a + w * cos_a
        
        # ZW rotation
        if self.rotation_zw != 0:
            cos_a = math.cos(self.rotation_zw)
            sin_a = math.sin(self.rotation_zw)
            z, w = p[2], p[3]
            p[2] = z * cos_a - w * sin_a
            p[3] = z * sin_a + w * cos_a
        
        return p
    
    def set_evolution_state(self, state: "EvolutionState") -> None:
        """Set the player's evolution state for rendering."""
        self._evolution_state = state
    
    def render(self, world: "World", dimension_spec: Optional["DimensionSpec"] = None) -> None:
        """Render the 4D world."""
        self.clear()
        
        # Update rotation animation
        self._player_rotation += 0.02
        
        # Update camera from player
        player = world.find_player()
        if player:
            self._update_camera_from_player_4d(player)
        
        # Draw floor grid (in current W slice)
        if self.grid_enabled:
            self._draw_floor_grid()
        
        # Draw W-axis indicator
        if self.show_w_indicator:
            self._draw_w_indicator()
        
        # Get entities in 4D
        entities = world.in_dimension("4d")
        
        # Also show entities from lower dimensions if enabled
        if self.show_lower_dims:
            entities.extend(world.in_dimension("3d"))
            entities.extend(world.in_dimension("2d"))
            entities.extend(world.in_dimension("1d"))
        
        # Sort by 4D distance
        def get_dist_4d(e):
            t = e.get(Transform)
            if not t:
                return float('inf')
            pos = t.position
            cam = np.array([*self.camera_pos, self.w_slice])
            return np.linalg.norm(pos[:4] - cam[:4])
        
        entities.sort(key=get_dist_4d, reverse=True)
        
        # Render entities
        for entity in entities:
            if not entity.active:
                continue
            if entity.has_tag("player"):
                continue
            self._render_entity_4d(entity)
        
        # Draw player polytope form in corner
        if self._evolution_state:
            self._draw_player_polytope_hud()
        
        # Draw crosshair
        if self.crosshair_enabled:
            self._draw_crosshair()
        
        # Draw UI
        self._draw_ui_4d(world, player)
    
    def _draw_player_polytope_hud(self) -> None:
        """Draw the player's polytope form as a rotating HUD element."""
        from hypersim.game.evolution import (
            generate_polytope_vertices, generate_polytope_edges, POLYTOPE_FORMS
        )
        
        if not self._evolution_state:
            return
        
        form = self._evolution_state.current_form
        form_def = POLYTOPE_FORMS[form]
        
        # Position in bottom-left corner
        center_x = 100
        center_y = self.height - 120
        size = 50
        
        # Draw background circle
        pygame.draw.circle(self.screen, (20, 20, 40), (center_x, center_y), size + 15)
        pygame.draw.circle(self.screen, form_def.color, (center_x, center_y), size + 15, 2)
        
        # Generate and project polytope
        vertices = generate_polytope_vertices(form, scale=1.0)
        edges = generate_polytope_edges(form, vertices)
        
        # Rotate in multiple planes for nice animation
        angle = self._player_rotation
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        cos_b = math.cos(angle * 0.7)
        sin_b = math.sin(angle * 0.7)
        
        projected = []
        for v in vertices:
            # XW rotation
            x = v[0] * cos_a - v[3] * sin_a
            w = v[0] * sin_a + v[3] * cos_a
            
            # YZ rotation
            y = v[1] * cos_b - v[2] * sin_b
            z = v[1] * sin_b + v[2] * cos_b
            
            # 4D to 2D projection with perspective
            perspective = 2.5 / (2.5 + w * 0.3)
            px = int(center_x + x * size * perspective)
            py = int(center_y - y * size * perspective)
            
            projected.append((px, py, perspective))
        
        # Draw edges with depth-based alpha
        for i, j in edges:
            p1, p2 = projected[i], projected[j]
            alpha = min(1.0, (p1[2] + p2[2]) / 2)
            edge_color = tuple(int(c * alpha * form_def.glow_intensity) for c in form_def.color)
            pygame.draw.line(self.screen, edge_color, (p1[0], p1[1]), (p2[0], p2[1]), 1)
        
        # Draw vertices
        for px, py, depth in projected:
            radius = max(1, int(2 * depth))
            vertex_color = tuple(int(c * depth) for c in form_def.color)
            pygame.draw.circle(self.screen, vertex_color, (px, py), radius)
        
        # Draw form name below
        font = pygame.font.Font(None, 20)
        name_text = font.render(form_def.short_name, True, form_def.color)
        name_rect = name_text.get_rect(center=(center_x, center_y + size + 25))
        self.screen.blit(name_text, name_rect)
        
        # Draw evolution progress if not max
        if self._evolution_state.next_form:
            progress = self._evolution_state.evolution_progress
            bar_width = 60
            bar_x = center_x - bar_width // 2
            bar_y = center_y + size + 38
            
            pygame.draw.rect(self.screen, (40, 40, 60), (bar_x, bar_y, bar_width, 6))
            if progress > 0:
                fill_width = int(bar_width * progress)
                pygame.draw.rect(self.screen, form_def.color, (bar_x, bar_y, fill_width, 6))
            pygame.draw.rect(self.screen, (80, 80, 100), (bar_x, bar_y, bar_width, 6), 1)
    
    def set_camera_orientation(self, yaw: float, pitch: float) -> None:
        """Set camera orientation from the input controller."""
        self.camera_yaw = yaw
        self.camera_pitch = pitch
    
    def _update_camera_from_player_4d(self, player: "Entity") -> None:
        """Update camera from 4D player position (orientation set externally)."""
        transform = player.get(Transform)
        if transform:
            self.camera_pos = transform.position[:3].copy()
            self.camera_pos[1] += 1.5
            if len(transform.position) > 3:
                self.w_slice = transform.position[3]
    
    def _render_entity_4d(self, entity: "Entity") -> None:
        """Render an entity in 4D space."""
        transform = entity.get(Transform)
        renderable = entity.get(Renderable)
        anchor = entity.get(DimensionAnchor)
        
        if not transform:
            return
        if renderable and not renderable.visible:
            return
        
        pos = transform.position
        dim = anchor.dimension_id if anchor else "4d"
        
        # Alpha based on W distance
        w_dist = abs(pos[3] - self.w_slice) if len(pos) > 3 else 0
        if w_dist > self.w_thickness * 2:
            return
        
        alpha = 1.0 - (w_dist / (self.w_thickness * 2))
        
        color = renderable.color if renderable else (255, 255, 255)
        # Fade color based on W distance
        faded_color = tuple(int(c * alpha) for c in color)
        
        # Different rendering based on entity type and dimension
        if entity.has_tag("enemy"):
            self._draw_enemy_4d(entity, pos, faded_color)
        elif entity.get(Pickup):
            self._draw_pickup_4d(entity, pos, alpha)
        elif entity.get(Portal):
            self._draw_portal_4d(entity, pos, alpha)
        elif dim in ("1d", "2d"):
            self._draw_lower_dim_entity(entity, pos, dim, alpha)
        else:
            self._draw_generic_4d(entity, pos, faded_color)
    
    def _draw_enemy_4d(self, entity: "Entity", pos: NDArray, color: Tuple) -> None:
        """Draw an enemy in 4D - 16-cell shape."""
        size = 0.8
        
        # 16-cell (4D cross-polytope) vertices
        vertices_4d = [
            pos + np.array([size, 0, 0, 0]),
            pos + np.array([-size, 0, 0, 0]),
            pos + np.array([0, size, 0, 0]),
            pos + np.array([0, -size, 0, 0]),
            pos + np.array([0, 0, size, 0]),
            pos + np.array([0, 0, -size, 0]),
            pos + np.array([0, 0, 0, size]),
            pos + np.array([0, 0, 0, -size]),
        ]
        
        # Edges connect each vertex to non-opposite vertices
        edges = []
        for i in range(8):
            for j in range(i + 1, 8):
                # Don't connect opposite vertices
                if (i // 2) != (j // 2) or (i % 2) == (j % 2):
                    edges.append((i, j))
        
        enemy_color = (200, 60, 60)
        for e in edges:
            self._draw_line_4d(vertices_4d[e[0]], vertices_4d[e[1]], enemy_color, 1)
    
    def _draw_pickup_4d(self, entity: "Entity", pos: NDArray, alpha: float) -> None:
        """Draw a pickup in 4D - tesseract."""
        time = pygame.time.get_ticks() / 1000.0
        size = 0.3
        
        # Tesseract vertices
        vertices_4d = []
        for w in [-1, 1]:
            for z in [-1, 1]:
                for y in [-1, 1]:
                    for x in [-1, 1]:
                        v = pos + np.array([x * size, y * size, z * size, w * size * 0.5])
                        vertices_4d.append(v)
        
        # Tesseract edges
        edges = []
        for i in range(16):
            for j in range(i + 1, 16):
                # Connect if exactly one coordinate differs
                diff = bin(i ^ j).count('1')
                if diff == 1:
                    edges.append((i, j))
        
        color = (int(255 * alpha), int(220 * alpha), int(50 * alpha))
        for e in edges:
            self._draw_line_4d(vertices_4d[e[0]], vertices_4d[e[1]], color, 1)
    
    def _draw_portal_4d(self, entity: "Entity", pos: NDArray, alpha: float) -> None:
        """Draw a 4D portal - hypersphere cross-section."""
        portal = entity.get(Portal)
        time = pygame.time.get_ticks() / 1000.0
        
        color = (int(150 * alpha), int(80 * alpha), int(255 * alpha))
        
        # Draw as nested spheres at different W slices
        for w_offset in [-0.3, 0.0, 0.3]:
            pos_w = pos.copy()
            pos_w[3] += w_offset
            
            segments = 12
            radius = 1.2 * (1 - abs(w_offset))
            
            for plane in ['xy', 'xz', 'yz']:
                for i in range(segments):
                    angle1 = (i / segments) * 2 * math.pi + time
                    angle2 = ((i + 1) / segments) * 2 * math.pi + time
                    
                    if plane == 'xy':
                        p1 = pos_w + np.array([math.cos(angle1) * radius, math.sin(angle1) * radius, 0, 0])
                        p2 = pos_w + np.array([math.cos(angle2) * radius, math.sin(angle2) * radius, 0, 0])
                    elif plane == 'xz':
                        p1 = pos_w + np.array([math.cos(angle1) * radius, 0, math.sin(angle1) * radius, 0])
                        p2 = pos_w + np.array([math.cos(angle2) * radius, 0, math.sin(angle2) * radius, 0])
                    else:
                        p1 = pos_w + np.array([0, math.cos(angle1) * radius, math.sin(angle1) * radius, 0])
                        p2 = pos_w + np.array([0, math.cos(angle2) * radius, math.sin(angle2) * radius, 0])
                    
                    self._draw_line_4d(p1, p2, color, 1)
    
    def _draw_lower_dim_entity(self, entity: "Entity", pos: NDArray, dim: str, alpha: float) -> None:
        """Draw a lower-dimensional entity as a projection."""
        color = (int(100 * alpha), int(150 * alpha), int(200 * alpha))
        
        if dim == "1d":
            # Draw as a line segment
            p1 = pos.copy()
            p2 = pos.copy()
            p1[0] -= 0.5
            p2[0] += 0.5
            self._draw_line_4d(p1, p2, color, 2)
        elif dim == "2d":
            # Draw as a square
            size = 0.5
            verts = [
                pos + np.array([-size, -size, 0, 0]),
                pos + np.array([size, -size, 0, 0]),
                pos + np.array([size, size, 0, 0]),
                pos + np.array([-size, size, 0, 0]),
            ]
            for i in range(4):
                self._draw_line_4d(verts[i], verts[(i + 1) % 4], color, 1)
    
    def _draw_generic_4d(self, entity: "Entity", pos: NDArray, color: Tuple) -> None:
        """Draw a generic 4D entity as a tesseract."""
        size = 0.5
        
        vertices_4d = []
        for w in [-1, 1]:
            for z in [-1, 1]:
                for y in [-1, 1]:
                    for x in [-1, 1]:
                        v = pos + np.array([x * size, y * size, z * size, w * size * 0.3])
                        vertices_4d.append(v)
        
        edges = []
        for i in range(16):
            for j in range(i + 1, 16):
                if bin(i ^ j).count('1') == 1:
                    edges.append((i, j))
        
        for e in edges:
            self._draw_line_4d(vertices_4d[e[0]], vertices_4d[e[1]], color, 1)
    
    def _draw_line_4d(self, start: NDArray, end: NDArray, color: Tuple, width: int = 1) -> None:
        """Draw a line in 4D space."""
        p1 = self.project_point_4d(start)
        p2 = self.project_point_4d(end)
        
        if p1 is None or p2 is None:
            return
        
        if not self._line_visible(p1, p2):
            return
        
        pygame.draw.line(self.screen, color, (p1[0], p1[1]), (p2[0], p2[1]), width)
    
    def _draw_w_indicator(self) -> None:
        """Draw W-axis position indicator."""
        # Draw on right side of screen
        x = self.width - 40
        y_top = 100
        y_bottom = self.height - 100
        height = y_bottom - y_top
        
        # Background
        pygame.draw.rect(self.screen, (30, 30, 50), (x - 10, y_top - 10, 30, height + 20))
        pygame.draw.rect(self.screen, (80, 80, 120), (x - 10, y_top - 10, 30, height + 20), 1)
        
        # W axis line
        pygame.draw.line(self.screen, (100, 100, 150), (x, y_top), (x, y_bottom), 2)
        
        # Current W position
        w_range = 5.0  # -5 to +5
        w_normalized = (self.w_slice + w_range) / (2 * w_range)
        w_normalized = max(0, min(1, w_normalized))
        marker_y = int(y_bottom - w_normalized * height)
        
        pygame.draw.circle(self.screen, (150, 200, 255), (x, marker_y), 8)
        pygame.draw.circle(self.screen, (255, 255, 255), (x, marker_y), 8, 2)
        
        # Labels
        font = pygame.font.Font(None, 20)
        w_text = font.render(f"W:{self.w_slice:.1f}", True, (200, 200, 255))
        self.screen.blit(w_text, (x - 25, marker_y - 25))
        
        label = font.render("W", True, (150, 150, 200))
        self.screen.blit(label, (x - 5, y_top - 30))
    
    def _draw_ui_4d(self, world: "World", player: Optional["Entity"]) -> None:
        """Draw 4D-specific UI."""
        # Call parent UI
        self._draw_ui(world, player)
        
        # Override dimension label
        font = pygame.font.Font(None, 24)
        
        # Clear and redraw dimension label
        dim_rect = pygame.Rect(self.width - 160, self.height - 35, 160, 25)
        pygame.draw.rect(self.screen, self.background_color, dim_rect)
        
        dim_text = font.render("4D - Hyperspace", True, (180, 150, 255))
        self.screen.blit(dim_text, (self.width - 140, self.height - 30))
        
        # 4D-specific controls hint
        controls_rect = pygame.Rect(5, self.height - 25, 500, 20)
        pygame.draw.rect(self.screen, self.background_color, controls_rect)
        
        controls = font.render("WASD: Move | Q/E: W-axis | Mouse: Look | Space/Ctrl: Up/Down", True, (80, 80, 120))
        self.screen.blit(controls, (10, self.height - 20))
