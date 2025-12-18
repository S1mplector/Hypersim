"""Enhanced features for the 4D Sandbox.

This module provides modular feature classes:
- ObjectAnimator: Auto-rotate objects in 4D
- SpawnGizmo: Visual preview for object placement
- Minimap: 2D overview of 4D space (multiple projections)
- SandboxHUD: Rich heads-up display with stats and info
- ObjectSelector: Click to select and inspect objects
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Callable
from enum import Enum, auto

import numpy as np
import pygame

from .base_app import THEME, Fonts, Camera4D


# =============================================================================
# OBJECT ANIMATOR
# =============================================================================

@dataclass
class AnimationConfig:
    """Configuration for object animation."""
    speed_xy: float = 0.3
    speed_xz: float = 0.2
    speed_xw: float = 0.15
    speed_yz: float = 0.1
    speed_yw: float = 0.25
    speed_zw: float = 0.18
    enabled: bool = True


class ObjectAnimator:
    """Manages auto-rotation animations for 4D objects.
    
    Each object can have independent rotation speeds in all 6 planes.
    """
    
    def __init__(self):
        self.animations: Dict[int, AnimationConfig] = {}  # object_id -> config
        self.global_speed: float = 1.0
        self.paused: bool = False
    
    def register(self, obj_id: int, config: AnimationConfig = None) -> None:
        """Register an object for animation."""
        if config is None:
            # Randomize speeds slightly for variety
            config = AnimationConfig(
                speed_xy=0.3 + random.uniform(-0.1, 0.1),
                speed_xz=0.2 + random.uniform(-0.1, 0.1),
                speed_xw=0.15 + random.uniform(-0.05, 0.05),
                speed_yz=0.1 + random.uniform(-0.05, 0.05),
                speed_yw=0.25 + random.uniform(-0.1, 0.1),
                speed_zw=0.18 + random.uniform(-0.08, 0.08),
            )
        self.animations[obj_id] = config
    
    def unregister(self, obj_id: int) -> None:
        """Remove object from animation."""
        self.animations.pop(obj_id, None)
    
    def update(self, dt: float, objects: List[Any]) -> None:
        """Update all object rotations."""
        if self.paused:
            return
        
        effective_dt = dt * self.global_speed
        
        for i, obj in enumerate(objects):
            if i not in self.animations:
                continue
            
            config = self.animations[i]
            if not config.enabled:
                continue
            
            # Get the actual shape object
            shape = obj.obj if hasattr(obj, 'obj') else obj
            
            if hasattr(shape, 'rotate'):
                shape.rotate(
                    xy=config.speed_xy * effective_dt,
                    xz=config.speed_xz * effective_dt,
                    xw=config.speed_xw * effective_dt,
                    yz=config.speed_yz * effective_dt,
                    yw=config.speed_yw * effective_dt,
                    zw=config.speed_zw * effective_dt,
                )
    
    def toggle_pause(self) -> bool:
        """Toggle pause state. Returns new state."""
        self.paused = not self.paused
        return self.paused
    
    def set_speed(self, speed: float) -> None:
        """Set global animation speed multiplier."""
        self.global_speed = max(0.0, min(5.0, speed))


# =============================================================================
# SPAWN GIZMO
# =============================================================================

class SpawnMode(Enum):
    """Object spawn modes."""
    INSTANT = auto()      # Spawn immediately at crosshair
    PREVIEW = auto()      # Show preview before placing
    TRAJECTORY = auto()   # Throw with physics


@dataclass
class SpawnPreview:
    """Preview state for object spawning."""
    obj_type: str
    position: np.ndarray
    rotation: float = 0.0
    scale: float = 1.0
    color: Tuple[int, int, int] = (100, 200, 255)


class SpawnGizmo:
    """Visual gizmo for spawning objects with preview.
    
    Features:
    - Preview wireframe before placing
    - Adjustable distance, rotation, scale
    - Color picker
    - Object type selector wheel
    """
    
    OBJECT_TYPES = [
        ("Tesseract", "tesseract", (100, 180, 255)),
        ("16-Cell", "16cell", (255, 150, 100)),
        ("24-Cell", "24cell", (150, 255, 150)),
        ("5-Cell", "5cell", (255, 200, 100)),
        ("600-Cell", "600cell", (200, 150, 255)),
        ("Duoprism", "duoprism", (255, 150, 200)),
        ("Clifford", "clifford", (100, 255, 200)),
    ]
    
    OBJECT_3D_TYPES = [
        ("Cube", "cube", (255, 100, 100)),
        ("Tetra", "tetra", (100, 255, 100)),
        ("Octa", "octa", (100, 100, 255)),
    ]
    
    def __init__(self):
        self.active = False
        self.mode = SpawnMode.INSTANT
        self.preview: Optional[SpawnPreview] = None
        
        self.selected_4d_index = 0
        self.selected_3d_index = 0
        self.is_3d_mode = False
        
        self.spawn_distance = 5.0
        self.spawn_scale = 1.0
        self.spawn_rotation = 0.0
        
        self.wheel_open = False
        self.wheel_angle = 0.0
    
    def get_current_type(self) -> Tuple[str, str, Tuple[int, int, int]]:
        """Get currently selected object type."""
        if self.is_3d_mode:
            return self.OBJECT_3D_TYPES[self.selected_3d_index]
        return self.OBJECT_TYPES[self.selected_4d_index]
    
    def next_type(self) -> None:
        """Cycle to next object type."""
        if self.is_3d_mode:
            self.selected_3d_index = (self.selected_3d_index + 1) % len(self.OBJECT_3D_TYPES)
        else:
            self.selected_4d_index = (self.selected_4d_index + 1) % len(self.OBJECT_TYPES)
    
    def prev_type(self) -> None:
        """Cycle to previous object type."""
        if self.is_3d_mode:
            self.selected_3d_index = (self.selected_3d_index - 1) % len(self.OBJECT_3D_TYPES)
        else:
            self.selected_4d_index = (self.selected_4d_index - 1) % len(self.OBJECT_TYPES)
    
    def toggle_dimension(self) -> None:
        """Toggle between 4D and 3D object types."""
        self.is_3d_mode = not self.is_3d_mode
    
    def update_preview(self, camera: Camera4D) -> None:
        """Update preview position based on camera."""
        name, type_id, color = self.get_current_type()
        pos = camera.position + camera.get_forward() * self.spawn_distance
        
        self.preview = SpawnPreview(
            obj_type=type_id,
            position=pos.copy(),
            rotation=self.spawn_rotation,
            scale=self.spawn_scale,
            color=color,
        )
    
    def adjust_distance(self, delta: float) -> None:
        """Adjust spawn distance."""
        self.spawn_distance = max(1.0, min(20.0, self.spawn_distance + delta))
    
    def adjust_scale(self, delta: float) -> None:
        """Adjust spawn scale."""
        self.spawn_scale = max(0.2, min(5.0, self.spawn_scale + delta))
    
    def draw(self, screen: pygame.Surface, camera: Camera4D, width: int, height: int) -> None:
        """Draw spawn gizmo UI."""
        fonts = Fonts.get()
        
        # Draw current selection indicator
        name, type_id, color = self.get_current_type()
        dim_text = "3D" if self.is_3d_mode else "4D"
        
        # Bottom center panel
        panel_w, panel_h = 280, 80
        panel_x = (width - panel_w) // 2
        panel_y = height - panel_h - 20
        
        # Panel background
        surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        surf.fill((20, 25, 35, 220))
        screen.blit(surf, (panel_x, panel_y))
        pygame.draw.rect(screen, THEME.border, (panel_x, panel_y, panel_w, panel_h), 1, 8)
        
        # Object type with color indicator
        pygame.draw.circle(screen, color, (panel_x + 25, panel_y + 25), 10)
        text = fonts.body.render(f"{name} ({dim_text})", True, THEME.text_primary)
        screen.blit(text, (panel_x + 45, panel_y + 15))
        
        # Controls hint
        hint = fonts.small.render("[ / ] cycle  |  T: toggle 4D/3D  |  +/- scale", True, THEME.text_muted)
        screen.blit(hint, (panel_x + 15, panel_y + 50))
        
        # Preview crosshair with distance indicator
        cx, cy = width // 2, height // 2
        pygame.draw.circle(screen, (*color, 150), (cx, cy), 20, 2)
        
        dist_text = fonts.small.render(f"{self.spawn_distance:.1f}m", True, color)
        screen.blit(dist_text, (cx + 25, cy - 8))
    
    def draw_wheel(self, screen: pygame.Surface, width: int, height: int) -> None:
        """Draw object selection wheel."""
        if not self.wheel_open:
            return
        
        fonts = Fonts.get()
        cx, cy = width // 2, height // 2
        radius = 120
        
        # Dim background
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        # Draw wheel
        types = self.OBJECT_3D_TYPES if self.is_3d_mode else self.OBJECT_TYPES
        n = len(types)
        
        for i, (name, type_id, color) in enumerate(types):
            angle = (2 * math.pi * i / n) - math.pi / 2 + self.wheel_angle
            x = cx + int(radius * math.cos(angle))
            y = cy + int(radius * math.sin(angle))
            
            # Highlight selected
            selected = (i == self.selected_3d_index if self.is_3d_mode else i == self.selected_4d_index)
            
            if selected:
                pygame.draw.circle(screen, color, (x, y), 35)
                pygame.draw.circle(screen, THEME.text_primary, (x, y), 35, 3)
            else:
                pygame.draw.circle(screen, (*color[:3], 150), (x, y), 25)
            
            # Label
            label = fonts.small.render(name, True, THEME.text_primary if selected else THEME.text_muted)
            screen.blit(label, (x - label.get_width() // 2, y + 40))


# =============================================================================
# MINIMAP
# =============================================================================

class MinimapView(Enum):
    """Different minimap projection views."""
    XZ_TOP = auto()    # Top-down view (XZ plane, Y=0)
    XY_FRONT = auto()  # Front view (XY plane, Z=0)
    XW_4D = auto()     # 4D view (XW plane, showing W dimension)
    ZW_4D = auto()     # 4D side view (ZW plane)


class Minimap:
    """Minimap showing position in 4D space.
    
    Features:
    - Multiple projection views (XZ, XY, XW, ZW)
    - Object markers with depth coloring
    - Camera frustum indicator
    - Grid with axis labels
    - Toggleable between views
    """
    
    def __init__(self, x: int, y: int, size: int = 150):
        self.x = x
        self.y = y
        self.size = size
        self.view = MinimapView.XW_4D
        self.scale = 5.0  # World units per minimap radius
        self.visible = True
        
        # Visual settings
        self.bg_color = (20, 25, 35)
        self.grid_color = (40, 45, 60)
        self.axis_colors = {
            'X': (255, 100, 100),
            'Y': (100, 255, 100),
            'Z': (100, 100, 255),
            'W': (255, 200, 80),
        }
    
    def set_position(self, x: int, y: int) -> None:
        """Set minimap position."""
        self.x = x
        self.y = y
    
    def cycle_view(self) -> MinimapView:
        """Cycle to next view mode."""
        views = list(MinimapView)
        idx = views.index(self.view)
        self.view = views[(idx + 1) % len(views)]
        return self.view
    
    def _get_axes(self) -> Tuple[int, int, str, str]:
        """Get axis indices and labels for current view."""
        if self.view == MinimapView.XZ_TOP:
            return 0, 2, 'X', 'Z'
        elif self.view == MinimapView.XY_FRONT:
            return 0, 1, 'X', 'Y'
        elif self.view == MinimapView.XW_4D:
            return 0, 3, 'X', 'W'
        else:  # ZW_4D
            return 2, 3, 'Z', 'W'
    
    def _world_to_map(self, pos: np.ndarray, camera_pos: np.ndarray) -> Tuple[int, int]:
        """Convert world position to minimap coordinates."""
        ax1, ax2, _, _ = self._get_axes()
        
        # Relative to camera
        rel = pos - camera_pos
        
        # Scale to minimap
        half = self.size // 2
        mx = int(self.x + half + (rel[ax1] / self.scale) * half)
        my = int(self.y + half - (rel[ax2] / self.scale) * half)  # Flip Y
        
        return mx, my
    
    def draw(self, screen: pygame.Surface, camera: Camera4D, objects: List[Any]) -> None:
        """Draw the minimap."""
        if not self.visible:
            return
        
        fonts = Fonts.get()
        ax1, ax2, label1, label2 = self._get_axes()
        half = self.size // 2
        cx, cy = self.x + half, self.y + half
        
        # Background
        pygame.draw.rect(screen, self.bg_color, 
                        (self.x, self.y, self.size, self.size), border_radius=8)
        pygame.draw.rect(screen, THEME.border, 
                        (self.x, self.y, self.size, self.size), 1, 8)
        
        # Grid lines
        for i in range(-2, 3):
            offset = int(i * half / 2.5)
            # Horizontal
            pygame.draw.line(screen, self.grid_color, 
                           (self.x + 5, cy + offset), (self.x + self.size - 5, cy + offset), 1)
            # Vertical
            pygame.draw.line(screen, self.grid_color,
                           (cx + offset, self.y + 5), (cx + offset, self.y + self.size - 5), 1)
        
        # Axis lines through center
        pygame.draw.line(screen, self.axis_colors[label1], 
                        (self.x + 10, cy), (self.x + self.size - 10, cy), 2)
        pygame.draw.line(screen, self.axis_colors[label2],
                        (cx, self.y + 10), (cx, self.y + self.size - 10), 2)
        
        # Objects
        for world_obj in objects:
            pos = world_obj.position if hasattr(world_obj, 'position') else np.zeros(4)
            mx, my = self._world_to_map(pos, camera.position)
            
            # Only draw if within bounds
            if self.x + 5 < mx < self.x + self.size - 5 and self.y + 5 < my < self.y + self.size - 5:
                color = world_obj.color if hasattr(world_obj, 'color') else (150, 150, 150)
                is_3d = world_obj.is_3d if hasattr(world_obj, 'is_3d') else False
                
                if is_3d:
                    pygame.draw.rect(screen, color, (mx - 3, my - 3, 6, 6))
                else:
                    pygame.draw.circle(screen, color, (mx, my), 4)
        
        # Camera position (always at center)
        pygame.draw.circle(screen, (255, 255, 100), (cx, cy), 6)
        
        # Camera direction indicator
        forward = camera.get_forward()
        dir_x = int(cx + forward[ax1] * 15)
        dir_y = int(cy - forward[ax2] * 15)
        pygame.draw.line(screen, (255, 255, 100), (cx, cy), (dir_x, dir_y), 2)
        
        # View label
        view_names = {
            MinimapView.XZ_TOP: "Top (XZ)",
            MinimapView.XY_FRONT: "Front (XY)",
            MinimapView.XW_4D: "4D (XW)",
            MinimapView.ZW_4D: "4D (ZW)",
        }
        label = fonts.small.render(view_names[self.view], True, THEME.text_muted)
        screen.blit(label, (self.x + 5, self.y + 5))
        
        # Axis labels
        label_x = fonts.small.render(label1, True, self.axis_colors[label1])
        label_y = fonts.small.render(label2, True, self.axis_colors[label2])
        screen.blit(label_x, (self.x + self.size - 15, cy - 15))
        screen.blit(label_y, (cx + 5, self.y + 5))


# =============================================================================
# ENHANCED HUD
# =============================================================================

class SandboxHUD:
    """Rich heads-up display for the sandbox.
    
    Features:
    - Position/rotation display with visual indicators
    - FPS and performance stats
    - Object count and selection info
    - Context-sensitive hints
    - Compass for orientation
    - W-dimension depth gauge
    """
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.visible = True
        
        self.show_compass = True
        self.show_depth_gauge = True
        self.show_stats = True
        
        # Performance tracking
        self.fps_history: List[float] = []
        self.frame_times: List[float] = []
    
    def update_stats(self, fps: float, frame_time: float) -> None:
        """Update performance statistics."""
        self.fps_history.append(fps)
        self.frame_times.append(frame_time)
        
        # Keep last 60 samples
        if len(self.fps_history) > 60:
            self.fps_history.pop(0)
            self.frame_times.pop(0)
    
    def draw(self, screen: pygame.Surface, camera: Camera4D, 
             objects: List[Any], animator: ObjectAnimator = None) -> None:
        """Draw the full HUD."""
        if not self.visible:
            return
        
        fonts = Fonts.get()
        pos = camera.position
        
        # === TOP LEFT: Stats ===
        if self.show_stats:
            self._draw_stats(screen, fonts, objects, animator)
        
        # === TOP RIGHT: Compass ===
        if self.show_compass:
            self._draw_compass(screen, camera)
        
        # === BOTTOM LEFT: Position ===
        self._draw_position(screen, fonts, pos)
        
        # === RIGHT SIDE: W Depth Gauge ===
        if self.show_depth_gauge:
            self._draw_depth_gauge(screen, fonts, pos[3])
    
    def _draw_stats(self, screen: pygame.Surface, fonts: Fonts, 
                    objects: List[Any], animator: ObjectAnimator) -> None:
        """Draw performance and object stats."""
        y = 15
        
        # FPS
        avg_fps = sum(self.fps_history) / max(1, len(self.fps_history))
        fps_color = THEME.accent_green if avg_fps > 50 else (
            THEME.accent_orange if avg_fps > 30 else THEME.accent_red
        )
        text = fonts.mono.render(f"FPS: {avg_fps:.0f}", True, fps_color)
        screen.blit(text, (15, y))
        y += 20
        
        # Object counts
        n_4d = sum(1 for o in objects if not getattr(o, 'is_3d', False))
        n_3d = sum(1 for o in objects if getattr(o, 'is_3d', False))
        text = fonts.small.render(f"Objects: {n_4d} 4D, {n_3d} 3D", True, THEME.text_secondary)
        screen.blit(text, (15, y))
        y += 18
        
        # Animation status
        if animator:
            status = "⏸ Paused" if animator.paused else f"▶ {animator.global_speed:.1f}x"
            color = THEME.text_muted if animator.paused else THEME.accent_cyan
            text = fonts.small.render(f"Anim: {status}", True, color)
            screen.blit(text, (15, y))
    
    def _draw_compass(self, screen: pygame.Surface, camera: Camera4D) -> None:
        """Draw orientation compass."""
        cx = self.width - 60
        cy = 60
        radius = 40
        
        # Background circle
        pygame.draw.circle(screen, (20, 25, 35, 200), (cx, cy), radius)
        pygame.draw.circle(screen, THEME.border, (cx, cy), radius, 2)
        
        # Cardinal directions based on yaw
        yaw = camera.yaw
        directions = [
            ('N', 0, (100, 200, 255)),
            ('E', math.pi/2, THEME.text_muted),
            ('S', math.pi, THEME.text_muted),
            ('W', -math.pi/2, THEME.text_muted),
        ]
        
        fonts = Fonts.get()
        for label, angle, color in directions:
            # Rotate by negative yaw (compass rotates opposite to camera)
            rot_angle = angle - yaw - math.pi/2
            x = int(cx + (radius - 15) * math.cos(rot_angle))
            y = int(cy + (radius - 15) * math.sin(rot_angle))
            
            text = fonts.small.render(label, True, color)
            screen.blit(text, (x - text.get_width()//2, y - text.get_height()//2))
        
        # Center dot
        pygame.draw.circle(screen, THEME.accent_orange, (cx, cy), 4)
        
        # Forward indicator
        pygame.draw.polygon(screen, THEME.accent_orange, [
            (cx, cy - 12), (cx - 5, cy - 5), (cx + 5, cy - 5)
        ])
    
    def _draw_position(self, screen: pygame.Surface, fonts: Fonts, pos: np.ndarray) -> None:
        """Draw position display."""
        y = self.height - 75
        
        # Panel background
        panel = pygame.Surface((200, 60), pygame.SRCALPHA)
        panel.fill((20, 25, 35, 200))
        screen.blit(panel, (15, y))
        pygame.draw.rect(screen, THEME.border, (15, y, 200, 60), 1, 6)
        
        # Position values with colored labels
        axes = [('X', pos[0], (255, 100, 100)), 
                ('Y', pos[1], (100, 255, 100)),
                ('Z', pos[2], (100, 100, 255)), 
                ('W', pos[3], (255, 200, 80))]
        
        for i, (label, val, color) in enumerate(axes):
            x = 25 + (i % 2) * 95
            row_y = y + 10 + (i // 2) * 25
            
            label_surf = fonts.small.render(label + ":", True, color)
            val_surf = fonts.mono.render(f"{val:+.1f}", True, THEME.text_primary)
            
            screen.blit(label_surf, (x, row_y))
            screen.blit(val_surf, (x + 20, row_y))
    
    def _draw_depth_gauge(self, screen: pygame.Surface, fonts: Fonts, w_pos: float) -> None:
        """Draw W-dimension depth gauge."""
        x = self.width - 40
        gauge_height = 200
        y = (self.height - gauge_height) // 2
        
        # Background bar
        pygame.draw.rect(screen, (20, 25, 35), (x, y, 20, gauge_height), border_radius=10)
        pygame.draw.rect(screen, THEME.border, (x, y, 20, gauge_height), 1, 10)
        
        # Scale markings
        for i in range(5):
            mark_y = y + int(i * gauge_height / 4)
            pygame.draw.line(screen, THEME.text_muted, (x - 5, mark_y), (x, mark_y), 1)
        
        # Current position indicator
        # Map W from -10 to +10 to gauge
        w_clamped = max(-10, min(10, w_pos))
        indicator_y = int(y + gauge_height/2 - (w_clamped / 10) * (gauge_height/2))
        
        # Gradient fill from center to indicator
        center_y = y + gauge_height // 2
        if w_pos > 0:
            fill_rect = pygame.Rect(x + 3, indicator_y, 14, center_y - indicator_y)
            pygame.draw.rect(screen, (255, 200, 80), fill_rect, border_radius=5)
        elif w_pos < 0:
            fill_rect = pygame.Rect(x + 3, center_y, 14, indicator_y - center_y)
            pygame.draw.rect(screen, (80, 150, 255), fill_rect, border_radius=5)
        
        # Indicator triangle
        pygame.draw.polygon(screen, THEME.text_primary, [
            (x - 8, indicator_y),
            (x - 2, indicator_y - 5),
            (x - 2, indicator_y + 5),
        ])
        
        # Labels
        ana_label = fonts.small.render("Ana", True, (255, 200, 80))
        kata_label = fonts.small.render("Kata", True, (80, 150, 255))
        screen.blit(ana_label, (x - 25, y - 20))
        screen.blit(kata_label, (x - 25, y + gauge_height + 5))
        
        # Current value
        w_text = fonts.mono.render(f"{w_pos:+.1f}", True, THEME.text_primary)
        screen.blit(w_text, (x - 35, indicator_y - 8))


# =============================================================================
# OBJECT SELECTOR
# =============================================================================

class ObjectSelector:
    """Click-to-select objects for inspection and manipulation."""
    
    def __init__(self):
        self.selected_index: Optional[int] = None
        self.hover_index: Optional[int] = None
        self.selection_radius = 30  # Pixels
    
    def update(self, mouse_pos: Tuple[int, int], camera: Camera4D, 
               objects: List[Any], width: int, height: int) -> None:
        """Update hover state based on mouse position."""
        self.hover_index = None
        
        mx, my = mouse_pos
        
        for i, obj in enumerate(objects):
            # Get object center position
            pos = obj.position if hasattr(obj, 'position') else np.zeros(4)
            projected = camera.project(pos, width, height)
            
            if projected:
                px, py, _ = projected
                dist = math.sqrt((mx - px)**2 + (my - py)**2)
                
                if dist < self.selection_radius:
                    self.hover_index = i
                    break
    
    def click(self) -> Optional[int]:
        """Handle click - select hovered object."""
        if self.hover_index is not None:
            self.selected_index = self.hover_index
            return self.selected_index
        else:
            self.selected_index = None
            return None
    
    def deselect(self) -> None:
        """Clear selection."""
        self.selected_index = None
    
    def draw(self, screen: pygame.Surface, camera: Camera4D,
             objects: List[Any], width: int, height: int) -> None:
        """Draw selection highlights."""
        fonts = Fonts.get()
        
        # Draw hover highlight
        if self.hover_index is not None and self.hover_index < len(objects):
            obj = objects[self.hover_index]
            pos = obj.position if hasattr(obj, 'position') else np.zeros(4)
            projected = camera.project(pos, width, height)
            
            if projected:
                px, py, _ = projected
                pygame.draw.circle(screen, THEME.accent_cyan, (px, py), 25, 2)
        
        # Draw selection info panel
        if self.selected_index is not None and self.selected_index < len(objects):
            obj = objects[self.selected_index]
            self._draw_info_panel(screen, fonts, obj)
    
    def _draw_info_panel(self, screen: pygame.Surface, fonts: Fonts, obj: Any) -> None:
        """Draw info panel for selected object."""
        panel_w, panel_h = 220, 120
        panel_x, panel_y = 15, 200
        
        # Background
        surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        surf.fill((20, 25, 35, 230))
        screen.blit(surf, (panel_x, panel_y))
        pygame.draw.rect(screen, THEME.accent_cyan, (panel_x, panel_y, panel_w, panel_h), 2, 8)
        
        # Title
        is_3d = getattr(obj, 'is_3d', False)
        title = "3D Object" if is_3d else "4D Polytope"
        text = fonts.body.render(title, True, THEME.accent_cyan)
        screen.blit(text, (panel_x + 10, panel_y + 10))
        
        # Position
        pos = obj.position if hasattr(obj, 'position') else np.zeros(4)
        pos_text = f"Pos: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}, {pos[3]:.1f})"
        text = fonts.small.render(pos_text, True, THEME.text_secondary)
        screen.blit(text, (panel_x + 10, panel_y + 40))
        
        # Type info
        shape = obj.obj if hasattr(obj, 'obj') else obj
        type_name = type(shape).__name__
        text = fonts.small.render(f"Type: {type_name}", True, THEME.text_secondary)
        screen.blit(text, (panel_x + 10, panel_y + 60))
        
        # Geometry stats
        if hasattr(shape, 'vertices') and hasattr(shape, 'edges'):
            v_count = len(shape.vertices) if hasattr(shape.vertices, '__len__') else '?'
            e_count = len(shape.edges) if hasattr(shape.edges, '__len__') else '?'
            text = fonts.small.render(f"V: {v_count}  E: {e_count}", True, THEME.text_muted)
            screen.blit(text, (panel_x + 10, panel_y + 80))
        
        # Hint
        hint = fonts.small.render("Click elsewhere to deselect", True, THEME.text_muted)
        screen.blit(hint, (panel_x + 10, panel_y + panel_h - 20))


# =============================================================================
# DRAG & DROP SPAWNER MENU
# =============================================================================

@dataclass
class SpawnItem:
    """An item in the spawner menu."""
    name: str
    type_id: str
    color: Tuple[int, int, int]
    is_3d: bool = False
    icon_verts: List[Tuple[int, int]] = None  # Simplified icon vertices


class SpawnerMenu:
    """Collapsible drag-and-drop object spawner menu.
    
    Features:
    - Collapsible sidebar with object icons
    - Drag objects onto the scene to spawn
    - Search bar to filter objects by name
    - Filter tabs for 4D/3D/All
    - Click to spawn instantly
    """
    
    # 4D Objects
    ITEMS_4D = [
        SpawnItem("Tesseract", "tesseract", (100, 180, 255)),
        SpawnItem("16-Cell", "16cell", (255, 150, 100)),
        SpawnItem("24-Cell", "24cell", (150, 255, 150)),
        SpawnItem("5-Cell", "5cell", (255, 200, 100)),
        SpawnItem("600-Cell", "600cell", (200, 150, 255)),
        SpawnItem("Duoprism", "duoprism", (255, 150, 200)),
        SpawnItem("Clifford", "clifford", (100, 255, 200)),
    ]
    
    # 3D Objects
    ITEMS_3D = [
        SpawnItem("Cube", "cube", (255, 100, 100), is_3d=True),
        SpawnItem("Tetra", "tetra", (100, 255, 100), is_3d=True),
        SpawnItem("Octa", "octa", (100, 100, 255), is_3d=True),
    ]
    
    def __init__(self, screen_height: int):
        self.screen_height = screen_height
        self.expanded = True
        self.collapsed_width = 40
        self.expanded_width = 180
        
        # Menu position (left side)
        self.x = 0
        self.y = 60
        
        # Item dimensions
        self.item_height = 42
        self.item_padding = 5
        
        # Search and filter
        self.search_text = ""
        self.search_active = False
        self.filter_mode = "all"  # "all", "4d", "3d"
        
        # Drag state
        self.dragging: Optional[SpawnItem] = None
        self.drag_pos: Tuple[int, int] = (0, 0)
        self.hover_index: Optional[int] = None
        
        # Scroll
        self.scroll_offset = 0
        self.max_visible = 10
    
    @property
    def width(self) -> int:
        return self.expanded_width if self.expanded else self.collapsed_width
    
    @property
    def all_items(self) -> List[SpawnItem]:
        return self.ITEMS_4D + self.ITEMS_3D
    
    def get_filtered_items(self) -> List[SpawnItem]:
        """Get items filtered by search and type filter."""
        items = []
        
        # Apply type filter
        if self.filter_mode == "4d":
            items = self.ITEMS_4D.copy()
        elif self.filter_mode == "3d":
            items = self.ITEMS_3D.copy()
        else:
            items = self.all_items.copy()
        
        # Apply search filter
        if self.search_text:
            search_lower = self.search_text.lower()
            items = [item for item in items if search_lower in item.name.lower()]
        
        return items
    
    def toggle(self) -> None:
        """Toggle expanded/collapsed state."""
        self.expanded = not self.expanded
        if not self.expanded:
            self.search_active = False
    
    def get_menu_rect(self) -> pygame.Rect:
        """Get the menu bounding rectangle."""
        filtered = self.get_filtered_items()
        # Header (toggle) + search bar + filter tabs + items
        header_height = 85  # toggle + search + filters
        items_height = len(filtered) * self.item_height
        total_height = header_height + items_height + 10
        height = min(total_height, self.screen_height - self.y - 20)
        return pygame.Rect(self.x, self.y, self.width, height)
    
    def handle_event(self, event: pygame.event.Event, camera: Camera4D) -> Optional[Tuple[str, bool]]:
        """Handle mouse and keyboard events. Returns (type_id, is_3d) if object should spawn."""
        
        # Handle text input for search
        if event.type == pygame.KEYDOWN and self.search_active:
            if event.key == pygame.K_BACKSPACE:
                self.search_text = self.search_text[:-1]
                return None
            elif event.key == pygame.K_ESCAPE:
                self.search_active = False
                self.search_text = ""
                return None
            elif event.key == pygame.K_RETURN:
                # Spawn first matching item on Enter
                filtered = self.get_filtered_items()
                if filtered:
                    item = filtered[0]
                    return (item.type_id, item.is_3d)
                return None
            elif event.unicode and event.unicode.isprintable():
                self.search_text += event.unicode
                return None
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            menu_rect = self.get_menu_rect()
            
            # Check toggle button
            toggle_rect = pygame.Rect(self.x, self.y - 25, self.width, 25)
            if toggle_rect.collidepoint(mx, my):
                self.toggle()
                return None
            
            if not self.expanded:
                return None
            
            # Check search bar click
            search_rect = pygame.Rect(self.x + 5, self.y + 5, self.width - 10, 25)
            if search_rect.collidepoint(mx, my):
                self.search_active = True
                return None
            else:
                self.search_active = False
            
            # Check filter tabs
            filter_y = self.y + 35
            tab_width = (self.width - 10) // 3
            for i, mode in enumerate(["all", "4d", "3d"]):
                tab_rect = pygame.Rect(self.x + 5 + i * tab_width, filter_y, tab_width, 22)
                if tab_rect.collidepoint(mx, my):
                    self.filter_mode = mode
                    self.scroll_offset = 0
                    return None
            
            # Check if clicking on an item
            if menu_rect.collidepoint(mx, my):
                item_idx = self._get_item_at(my)
                filtered = self.get_filtered_items()
                if item_idx is not None and item_idx < len(filtered):
                    self.dragging = filtered[item_idx]
                    self.drag_pos = (mx, my)
        
        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            
            if self.dragging:
                self.drag_pos = (mx, my)
            else:
                # Update hover
                menu_rect = self.get_menu_rect()
                if menu_rect.collidepoint(mx, my) and self.expanded:
                    self.hover_index = self._get_item_at(my)
                else:
                    self.hover_index = None
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                mx, my = event.pos
                menu_rect = self.get_menu_rect()
                
                # If released outside menu, spawn object
                if not menu_rect.collidepoint(mx, my):
                    result = (self.dragging.type_id, self.dragging.is_3d)
                    self.dragging = None
                    return result
                else:
                    # Click inside menu = instant spawn
                    result = (self.dragging.type_id, self.dragging.is_3d)
                    self.dragging = None
                    return result
        
        elif event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            menu_rect = self.get_menu_rect()
            if menu_rect.collidepoint(mx, my):
                filtered = self.get_filtered_items()
                self.scroll_offset = max(0, min(
                    max(0, len(filtered) - self.max_visible),
                    self.scroll_offset - event.y
                ))
        
        return None
    
    def _get_item_at(self, y: int) -> Optional[int]:
        """Get item index at y position (in filtered list)."""
        # Header height: search bar (30) + filter tabs (27) + padding
        header_height = 65
        rel_y = y - self.y - header_height
        
        if rel_y < 0:
            return None
        
        idx = int(rel_y // self.item_height) + self.scroll_offset
        filtered = self.get_filtered_items()
        
        if 0 <= idx < len(filtered):
            return idx
        return None
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the spawner menu."""
        fonts = Fonts.get()
        menu_rect = self.get_menu_rect()
        
        # Toggle button
        toggle_rect = pygame.Rect(self.x, self.y - 25, self.width, 25)
        pygame.draw.rect(screen, THEME.bg_card, toggle_rect, border_radius=4)
        pygame.draw.rect(screen, THEME.border, toggle_rect, 1, 4)
        
        arrow = "◀" if self.expanded else "▶"
        label = f"{arrow} Objects" if self.expanded else arrow
        text = fonts.small.render(label, True, THEME.text_secondary)
        screen.blit(text, (toggle_rect.x + 8, toggle_rect.y + 5))
        
        if not self.expanded:
            # Draw collapsed indicator dots
            for i, item in enumerate(self.all_items[:6]):
                y = self.y + i * 10
                pygame.draw.circle(screen, item.color, (self.x + 20, y + 5), 4)
            return
        
        # Menu background
        surf = pygame.Surface((menu_rect.width, menu_rect.height), pygame.SRCALPHA)
        surf.fill((20, 25, 35, 245))
        screen.blit(surf, (menu_rect.x, menu_rect.y))
        pygame.draw.rect(screen, THEME.border, menu_rect, 1, 6)
        
        y = menu_rect.y + 5
        
        # Search bar
        search_rect = pygame.Rect(self.x + 5, y, self.width - 10, 25)
        search_bg = THEME.bg_active if self.search_active else THEME.bg_card
        pygame.draw.rect(screen, search_bg, search_rect, border_radius=4)
        border_color = THEME.accent_cyan if self.search_active else THEME.border
        pygame.draw.rect(screen, border_color, search_rect, 1, 4)
        
        # Search icon/placeholder
        if self.search_text:
            search_display = self.search_text
            if self.search_active:
                search_display += "|"  # Cursor
            text = fonts.small.render(search_display, True, THEME.text_primary)
        else:
            text = fonts.small.render("🔍 Search...", True, THEME.text_muted)
        screen.blit(text, (search_rect.x + 8, search_rect.y + 5))
        
        y += 30
        
        # Filter tabs
        tab_width = (self.width - 10) // 3
        filter_labels = [("All", "all"), ("4D", "4d"), ("3D", "3d")]
        for i, (label, mode) in enumerate(filter_labels):
            tab_rect = pygame.Rect(self.x + 5 + i * tab_width, y, tab_width, 22)
            
            is_active = self.filter_mode == mode
            if is_active:
                color = THEME.accent_purple if mode == "4d" else (
                    THEME.accent_orange if mode == "3d" else THEME.accent_cyan
                )
                pygame.draw.rect(screen, color, tab_rect, border_radius=3)
                text = fonts.small.render(label, True, THEME.bg_dark)
            else:
                pygame.draw.rect(screen, THEME.bg_card, tab_rect, border_radius=3)
                pygame.draw.rect(screen, THEME.border, tab_rect, 1, 3)
                text = fonts.small.render(label, True, THEME.text_secondary)
            
            screen.blit(text, (tab_rect.x + tab_rect.width//2 - text.get_width()//2, 
                              tab_rect.y + 4))
        
        y += 30
        
        # Filtered items
        filtered = self.get_filtered_items()
        
        if not filtered:
            no_match = fonts.small.render("No matches", True, THEME.text_muted)
            screen.blit(no_match, (self.x + 10, y + 10))
        else:
            # Draw visible items
            visible_start = self.scroll_offset
            visible_end = min(visible_start + self.max_visible, len(filtered))
            
            for i in range(visible_start, visible_end):
                item = filtered[i]
                self._draw_item(screen, fonts, item, menu_rect.x, y, i, menu_rect.width)
                y += self.item_height
            
            # Scroll indicator
            if len(filtered) > self.max_visible:
                total = len(filtered)
                bar_height = 60
                bar_y = menu_rect.y + 65 + int((self.scroll_offset / total) * (menu_rect.height - 85))
                pygame.draw.rect(screen, THEME.border_light, 
                               (menu_rect.x + menu_rect.width - 6, bar_y, 4, bar_height), 
                               border_radius=2)
        
        # Draw drag preview
        if self.dragging:
            self._draw_drag_preview(screen, fonts)
    
    def _draw_item(self, screen: pygame.Surface, fonts: Fonts, 
                   item: SpawnItem, x: int, y: int, idx: int, width: int) -> None:
        """Draw a single menu item."""
        item_rect = pygame.Rect(x + 5, y, width - 10, self.item_height - 5)
        
        # Hover highlight
        if self.hover_index == idx:
            pygame.draw.rect(screen, THEME.bg_hover, item_rect, border_radius=4)
        
        pygame.draw.rect(screen, THEME.border, item_rect, 1, 4)
        
        # Color indicator
        pygame.draw.circle(screen, item.color, (x + 22, y + self.item_height // 2 - 2), 8)
        
        # Icon shape (simplified)
        if item.is_3d:
            # Square for 3D
            pygame.draw.rect(screen, item.color, (x + 16, y + self.item_height // 2 - 8, 12, 12), 2)
        else:
            # Diamond for 4D
            cx, cy = x + 22, y + self.item_height // 2 - 2
            points = [(cx, cy - 8), (cx + 8, cy), (cx, cy + 8), (cx - 8, cy)]
            pygame.draw.polygon(screen, item.color, points, 2)
        
        # Name
        text = fonts.small.render(item.name, True, THEME.text_primary)
        screen.blit(text, (x + 40, y + self.item_height // 2 - 8))
        
        # Dimension badge
        dim = "3D" if item.is_3d else "4D"
        badge_color = THEME.accent_orange if item.is_3d else THEME.accent_purple
        badge = fonts.small.render(dim, True, badge_color)
        screen.blit(badge, (x + width - 35, y + self.item_height // 2 - 8))
    
    def _draw_drag_preview(self, screen: pygame.Surface, fonts: Fonts) -> None:
        """Draw preview while dragging."""
        if not self.dragging:
            return
        
        mx, my = self.drag_pos
        
        # Draw object preview at cursor
        size = 40
        
        # Background
        surf = pygame.Surface((size + 20, size + 20), pygame.SRCALPHA)
        surf.fill((20, 25, 35, 180))
        screen.blit(surf, (mx - size//2 - 10, my - size//2 - 10))
        
        # Shape
        if self.dragging.is_3d:
            # Cube wireframe
            pygame.draw.rect(screen, self.dragging.color, 
                           (mx - size//2, my - size//2, size, size), 2)
        else:
            # Tesseract-like shape
            outer = size // 2
            inner = size // 3
            # Outer square
            pygame.draw.rect(screen, self.dragging.color,
                           (mx - outer, my - outer, outer * 2, outer * 2), 2)
            # Inner square
            pygame.draw.rect(screen, self.dragging.color,
                           (mx - inner, my - inner, inner * 2, inner * 2), 2)
            # Connect corners
            pygame.draw.line(screen, self.dragging.color, (mx - outer, my - outer), (mx - inner, my - inner), 1)
            pygame.draw.line(screen, self.dragging.color, (mx + outer, my - outer), (mx + inner, my - inner), 1)
            pygame.draw.line(screen, self.dragging.color, (mx - outer, my + outer), (mx - inner, my + inner), 1)
            pygame.draw.line(screen, self.dragging.color, (mx + outer, my + outer), (mx + inner, my + inner), 1)
        
        # Label
        label = fonts.small.render(self.dragging.name, True, self.dragging.color)
        screen.blit(label, (mx - label.get_width()//2, my + size//2 + 5))
        
        # Hint
        hint = fonts.small.render("Release to spawn", True, THEME.text_muted)
        screen.blit(hint, (mx - hint.get_width()//2, my + size//2 + 22))
