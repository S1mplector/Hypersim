"""Dimensional Battle Box - Battle arena that transforms based on dimension.

The battle box is no longer just a static rectangle. It transforms to reflect
the dimensional nature of combat:

1D: Collapses to a horizontal line
2D: Standard rectangular box
3D: Shows depth layers with parallax
4D: Tesseract with wrapping edges and temporal visualization
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Tuple

import pygame

from .dimensional_combat import (
    CombatDimension, PerceptionState, DEPTH_LAYERS,
    DimensionalBullet, TemporalBulletState
)


class BoxTransformState(Enum):
    """Current transformation state of the box."""
    STABLE = auto()
    TRANSFORMING = auto()
    WARPING = auto()


@dataclass
class DimensionalBattleBox:
    """Battle box that transforms based on combat dimension."""
    
    # Base position and size
    base_x: float
    base_y: float
    base_width: float
    base_height: float
    
    # Current display position/size (may differ during transformation)
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    
    # Dimension
    current_dimension: CombatDimension = CombatDimension.TWO_D
    target_dimension: Optional[CombatDimension] = None
    
    # Transformation
    transform_state: BoxTransformState = BoxTransformState.STABLE
    transform_progress: float = 0.0
    transform_speed: float = 2.0
    
    # Animation targets
    target_x: float = 0.0
    target_y: float = 0.0
    target_width: float = 0.0
    target_height: float = 0.0
    animation_speed: float = 8.0
    
    # Visual effects
    border_color: Tuple[int, int, int] = (255, 255, 255)
    border_width: int = 3
    glow_intensity: float = 0.0
    rotation: float = 0.0  # For 4D tesseract effect
    
    # 3D depth visualization
    depth_layer_offsets: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    show_depth_layers: bool = False
    
    # 4D tesseract visualization
    tesseract_rotation: float = 0.0
    show_edge_connections: bool = False
    time_indicator: float = 0.0
    
    # 1D collapse
    collapse_progress: float = 0.0  # 0 = full box, 1 = line
    
    def __post_init__(self):
        self.x = self.base_x
        self.y = self.base_y
        self.width = self.base_width
        self.height = self.base_height
        self.target_x = self.base_x
        self.target_y = self.base_y
        self.target_width = self.base_width
        self.target_height = self.base_height
    
    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Get (min_x, min_y, max_x, max_y)."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)
    
    @property
    def center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    @property
    def effective_height(self) -> float:
        """Get effective height (may be reduced in 1D)."""
        if self.current_dimension == CombatDimension.ONE_D:
            return max(60, self.height * (1 - self.collapse_progress * 0.7))
        return self.height
    
    def set_dimension(self, dimension: CombatDimension, instant: bool = False) -> None:
        """Set the combat dimension, triggering transformation."""
        if dimension == self.current_dimension and self.transform_state == BoxTransformState.STABLE:
            return
        
        self.target_dimension = dimension
        
        if instant:
            self._apply_dimension_immediately(dimension)
        else:
            self.transform_state = BoxTransformState.TRANSFORMING
            self.transform_progress = 0.0
    
    def _apply_dimension_immediately(self, dimension: CombatDimension) -> None:
        """Instantly apply dimension transformation."""
        self.current_dimension = dimension
        self.target_dimension = None
        self.transform_state = BoxTransformState.STABLE
        self.transform_progress = 1.0
        
        self._configure_for_dimension(dimension)
    
    def _configure_for_dimension(self, dimension: CombatDimension) -> None:
        """Configure box properties for a dimension."""
        if dimension == CombatDimension.ONE_D:
            self.collapse_progress = 1.0
            self.show_depth_layers = False
            self.show_edge_connections = False
            # Collapse to a wider line corridor in the center (easier to see/play)
            center_y = self.base_y + self.base_height / 2
            line_height = 80  # Wider corridor for better visibility
            self.target_y = center_y - line_height / 2
            self.target_height = line_height
            self.target_x = self.base_x
            self.target_width = self.base_width
            self.border_color = (100, 200, 255)  # Blue tint for 1D
            
        elif dimension == CombatDimension.TWO_D:
            self.collapse_progress = 0.0
            self.show_depth_layers = False
            self.show_edge_connections = False
            self.target_x = self.base_x
            self.target_y = self.base_y
            self.target_width = self.base_width
            self.target_height = self.base_height
            self.border_color = (255, 255, 255)  # White for 2D
            
        elif dimension == CombatDimension.THREE_D:
            self.collapse_progress = 0.0
            self.show_depth_layers = True
            self.show_edge_connections = False
            self.target_x = self.base_x
            self.target_y = self.base_y
            self.target_width = self.base_width
            self.target_height = self.base_height
            self.border_color = (200, 150, 255)  # Purple tint for 3D
            
        elif dimension == CombatDimension.FOUR_D:
            self.collapse_progress = 0.0
            self.show_depth_layers = True
            self.show_edge_connections = True
            self.target_x = self.base_x
            self.target_y = self.base_y
            self.target_width = self.base_width
            self.target_height = self.base_height
            self.border_color = (255, 200, 100)  # Gold tint for 4D
    
    def update(self, dt: float) -> None:
        """Update battle box state and animations."""
        # Handle dimension transformation
        if self.transform_state == BoxTransformState.TRANSFORMING:
            self.transform_progress += self.transform_speed * dt
            
            if self.transform_progress >= 1.0:
                self.transform_progress = 1.0
                self.current_dimension = self.target_dimension
                self.target_dimension = None
                self.transform_state = BoxTransformState.STABLE
                self._configure_for_dimension(self.current_dimension)
            else:
                # Interpolate transformation
                self._interpolate_transformation()
        
        # Animate towards target position
        self.x += (self.target_x - self.x) * self.animation_speed * dt
        self.y += (self.target_y - self.y) * self.animation_speed * dt
        self.width += (self.target_width - self.width) * self.animation_speed * dt
        self.height += (self.target_height - self.height) * self.animation_speed * dt
        
        # Dimension-specific updates
        if self.current_dimension == CombatDimension.THREE_D:
            self._update_3d_effects(dt)
        elif self.current_dimension == CombatDimension.FOUR_D:
            self._update_4d_effects(dt)
        
        # Update glow
        if self.transform_state == BoxTransformState.TRANSFORMING:
            self.glow_intensity = abs(math.sin(self.transform_progress * math.pi)) * 0.5
        else:
            self.glow_intensity = max(0, self.glow_intensity - dt * 2)
    
    def _interpolate_transformation(self) -> None:
        """Interpolate between dimensions during transformation."""
        t = self.transform_progress
        # Smooth step
        t = t * t * (3 - 2 * t)
        
        # During transformation, create visual distortion
        self.glow_intensity = 0.3 + abs(math.sin(t * math.pi)) * 0.5
        
        if self.target_dimension == CombatDimension.ONE_D:
            self.collapse_progress = t
        elif self.current_dimension == CombatDimension.ONE_D:
            self.collapse_progress = 1 - t
    
    def _update_3d_effects(self, dt: float) -> None:
        """Update 3D depth layer effects."""
        # Subtle parallax movement
        for i in range(len(self.depth_layer_offsets)):
            self.depth_layer_offsets[i] = math.sin(pygame.time.get_ticks() * 0.001 + i) * 3
    
    def _update_4d_effects(self, dt: float) -> None:
        """Update 4D tesseract effects."""
        self.tesseract_rotation += dt * 0.5
        self.time_indicator = (self.time_indicator + dt * 0.3) % 1.0
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the dimensional battle box."""
        if self.current_dimension == CombatDimension.ONE_D:
            self._draw_1d_box(screen)
        elif self.current_dimension == CombatDimension.TWO_D:
            self._draw_2d_box(screen)
        elif self.current_dimension == CombatDimension.THREE_D:
            self._draw_3d_box(screen)
        elif self.current_dimension == CombatDimension.FOUR_D:
            self._draw_4d_box(screen)
        
        # Draw glow effect during transformation
        if self.glow_intensity > 0:
            self._draw_glow(screen)
    
    def _draw_1d_box(self, screen: pygame.Surface) -> None:
        """Draw 1D collapsed line corridor."""
        center_y = self.y + self.height / 2
        effective_h = self.effective_height
        top_y = center_y - effective_h / 2
        bottom_y = center_y + effective_h / 2
        
        # Background fill (dark blue gradient feel)
        bg_rect = pygame.Rect(int(self.x), int(top_y), int(self.width), int(effective_h))
        pygame.draw.rect(screen, (15, 30, 50), bg_rect)
        
        # Center line (the "true" 1D line - glowing)
        pygame.draw.line(screen, (60, 120, 180),
                        (self.x, center_y), (self.x + self.width, center_y), 3)
        pygame.draw.line(screen, (100, 180, 255),
                        (self.x, center_y), (self.x + self.width, center_y), 1)
        
        # Border lines (top and bottom)
        pygame.draw.line(screen, self.border_color, 
                        (self.x, top_y), (self.x + self.width, top_y), 3)
        pygame.draw.line(screen, self.border_color,
                        (self.x, bottom_y), (self.x + self.width, bottom_y), 3)
        
        # Endpoints (vertical caps)
        pygame.draw.line(screen, self.border_color,
                        (self.x, top_y), (self.x, bottom_y), 3)
        pygame.draw.line(screen, self.border_color,
                        (self.x + self.width, top_y), (self.x + self.width, bottom_y), 3)
        
        # Direction arrows (larger, more visible)
        arrow_y = center_y
        arrow_size = 12
        # Left arrow
        pygame.draw.polygon(screen, (100, 200, 255), [
            (self.x + 20, arrow_y),
            (self.x + 20 + arrow_size, arrow_y - arrow_size),
            (self.x + 20 + arrow_size, arrow_y + arrow_size),
        ])
        # Right arrow  
        pygame.draw.polygon(screen, (100, 200, 255), [
            (self.x + self.width - 20, arrow_y),
            (self.x + self.width - 20 - arrow_size, arrow_y - arrow_size),
            (self.x + self.width - 20 - arrow_size, arrow_y + arrow_size),
        ])
        
        # "1D" label
        font = pygame.font.Font(None, 24)
        label = font.render("1D", True, (80, 160, 220))
        screen.blit(label, (self.x + 5, top_y - 20))
    
    def _draw_2d_box(self, screen: pygame.Surface) -> None:
        """Draw standard 2D battle box."""
        rect = pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))
        pygame.draw.rect(screen, self.border_color, rect, self.border_width)
    
    def _draw_3d_box(self, screen: pygame.Surface) -> None:
        """Draw 3D box with depth layers."""
        # Draw background layers first (back to front)
        for i, layer in enumerate(reversed(DEPTH_LAYERS)):
            offset = self.depth_layer_offsets[2 - i] if i < len(self.depth_layer_offsets) else 0
            layer_alpha = int(100 + layer.z * 100)
            
            # Layer rectangle (slightly offset and scaled)
            scale = layer.scale
            layer_w = self.width * scale
            layer_h = self.height * scale
            layer_x = self.x + (self.width - layer_w) / 2 + offset
            layer_y = self.y + (self.height - layer_h) / 2
            
            rect = pygame.Rect(int(layer_x), int(layer_y), int(layer_w), int(layer_h))
            
            # Draw layer border with depth-based color
            color = tuple(int(c * (0.5 + 0.5 * (1 - layer.z))) for c in self.border_color)
            pygame.draw.rect(screen, color, rect, max(1, int(self.border_width * scale)))
        
        # Draw depth indicator
        self._draw_depth_indicator(screen)
    
    def _draw_depth_indicator(self, screen: pygame.Surface) -> None:
        """Draw indicator showing depth layers."""
        indicator_x = self.x + self.width + 10
        indicator_y = self.y
        indicator_h = self.height
        indicator_w = 20
        
        # Background
        pygame.draw.rect(screen, (40, 40, 60),
                        (int(indicator_x), int(indicator_y), int(indicator_w), int(indicator_h)))
        
        # Layer markers
        for layer in DEPTH_LAYERS:
            y_pos = indicator_y + indicator_h * layer.z
            color = layer.color_tint
            pygame.draw.line(screen, color,
                           (indicator_x, y_pos), (indicator_x + indicator_w, y_pos), 2)
            
            # Label
            font = pygame.font.Font(None, 16)
            label = font.render(layer.name[0].upper(), True, color)
            screen.blit(label, (indicator_x + indicator_w + 2, y_pos - 6))
    
    def _draw_4d_box(self, screen: pygame.Surface) -> None:
        """Draw 4D tesseract-style box."""
        cx, cy = self.center
        
        # Inner cube (current 3D slice)
        inner_rect = pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))
        pygame.draw.rect(screen, self.border_color, inner_rect, self.border_width)
        
        # Outer cube (4D projection) - offset and scaled
        outer_scale = 1.15
        outer_offset = 15 * math.sin(self.tesseract_rotation)
        outer_w = self.width * outer_scale
        outer_h = self.height * outer_scale
        outer_x = cx - outer_w / 2 + outer_offset
        outer_y = cy - outer_h / 2 + outer_offset * 0.5
        
        outer_rect = pygame.Rect(int(outer_x), int(outer_y), int(outer_w), int(outer_h))
        outer_color = tuple(int(c * 0.5) for c in self.border_color)
        pygame.draw.rect(screen, outer_color, outer_rect, 1)
        
        # Connect corners (tesseract edges)
        if self.show_edge_connections:
            corners_inner = [
                (self.x, self.y),
                (self.x + self.width, self.y),
                (self.x + self.width, self.y + self.height),
                (self.x, self.y + self.height),
            ]
            corners_outer = [
                (outer_x, outer_y),
                (outer_x + outer_w, outer_y),
                (outer_x + outer_w, outer_y + outer_h),
                (outer_x, outer_y + outer_h),
            ]
            
            for inner, outer in zip(corners_inner, corners_outer):
                # Pulsing connection lines
                alpha = int(128 + 127 * math.sin(self.tesseract_rotation * 2))
                line_color = (*self.border_color[:2], min(255, self.border_color[2] + 50))
                pygame.draw.line(screen, line_color, inner, outer, 1)
        
        # Time indicator bar
        self._draw_time_indicator(screen)
        
        # Wrapping indicators at edges
        self._draw_wrap_indicators(screen)
    
    def _draw_time_indicator(self, screen: pygame.Surface) -> None:
        """Draw temporal position indicator for 4D."""
        bar_x = self.x
        bar_y = self.y - 20
        bar_w = self.width
        bar_h = 8
        
        # Background
        pygame.draw.rect(screen, (40, 40, 60),
                        (int(bar_x), int(bar_y), int(bar_w), int(bar_h)))
        
        # Time position
        time_x = bar_x + bar_w * self.time_indicator
        pygame.draw.rect(screen, (255, 200, 100),
                        (int(time_x - 2), int(bar_y), 4, int(bar_h)))
        
        # Labels
        font = pygame.font.Font(None, 14)
        past_label = font.render("PAST", True, (150, 150, 200))
        future_label = font.render("FUTURE", True, (200, 200, 150))
        screen.blit(past_label, (bar_x, bar_y - 12))
        screen.blit(future_label, (bar_x + bar_w - 35, bar_y - 12))
    
    def _draw_wrap_indicators(self, screen: pygame.Surface) -> None:
        """Draw indicators showing tesseract wrapping."""
        # Arrows at edges showing wraparound
        arrow_color = (255, 200, 100, 150)
        cx, cy = self.center
        
        # Left edge wraps to right
        self._draw_wrap_arrow(screen, self.x, cy, "left")
        # Right edge wraps to left
        self._draw_wrap_arrow(screen, self.x + self.width, cy, "right")
        # Top wraps to bottom
        self._draw_wrap_arrow(screen, cx, self.y, "up")
        # Bottom wraps to top
        self._draw_wrap_arrow(screen, cx, self.y + self.height, "down")
    
    def _draw_wrap_arrow(self, screen: pygame.Surface, x: float, y: float, direction: str) -> None:
        """Draw a single wrap indicator arrow."""
        size = 6
        color = (255, 200, 100)
        
        if direction == "left":
            points = [(x - 3, y), (x - 3 - size, y - size), (x - 3 - size, y + size)]
        elif direction == "right":
            points = [(x + 3, y), (x + 3 + size, y - size), (x + 3 + size, y + size)]
        elif direction == "up":
            points = [(x, y - 3), (x - size, y - 3 - size), (x + size, y - 3 - size)]
        elif direction == "down":
            points = [(x, y + 3), (x - size, y + 3 + size), (x + size, y + 3 + size)]
        else:
            return
        
        pygame.draw.polygon(screen, color, points)
    
    def _draw_glow(self, screen: pygame.Surface) -> None:
        """Draw glow effect around the box."""
        if self.glow_intensity <= 0:
            return
        
        glow_surface = pygame.Surface((int(self.width + 20), int(self.height + 20)), pygame.SRCALPHA)
        glow_color = (*self.border_color, int(self.glow_intensity * 100))
        
        for i in range(3):
            expand = i * 3
            rect = pygame.Rect(10 - expand, 10 - expand, 
                             int(self.width + expand * 2), int(self.height + expand * 2))
            pygame.draw.rect(glow_surface, glow_color, rect, 2)
        
        screen.blit(glow_surface, (self.x - 10, self.y - 10))
    
    def draw_bullets_with_depth(
        self, 
        screen: pygame.Surface, 
        bullets: List[DimensionalBullet],
        player_depth: float = 0.5
    ) -> None:
        """Draw bullets with 3D depth sorting."""
        if self.current_dimension != CombatDimension.THREE_D:
            return
        
        # Sort bullets by depth (back to front)
        sorted_bullets = sorted(bullets, key=lambda b: b.depth_layer, reverse=True)
        
        for bullet in sorted_bullets:
            # Get depth layer info
            layer_idx = min(2, max(0, int(bullet.depth_layer * 2)))
            layer = DEPTH_LAYERS[layer_idx]
            
            # Scale and tint based on depth
            scale = layer.scale
            tint = layer.color_tint
            
            # Apply tint to bullet color
            color = tuple(
                int(bc * tc / 255) 
                for bc, tc in zip(bullet.color, tint)
            )
            
            # Draw bullet
            radius = int(bullet.radius * scale)
            pygame.draw.circle(screen, color, (int(bullet.x), int(bullet.y)), radius)
            
            # Highlight bullets at player's depth
            if abs(bullet.depth_layer - player_depth) < 0.2:
                pygame.draw.circle(screen, (255, 255, 255), 
                                 (int(bullet.x), int(bullet.y)), radius, 1)
    
    def draw_temporal_bullets(
        self,
        screen: pygame.Surface,
        bullets: List[DimensionalBullet],
        current_time: float,
        show_predictions: bool = True
    ) -> None:
        """Draw bullets with temporal visualization for 4D."""
        if self.current_dimension != CombatDimension.FOUR_D:
            return
        
        for bullet in bullets:
            if not bullet.temporal_state:
                continue
            
            temporal = bullet.temporal_state
            
            # Draw past positions (ghosted)
            for i, (px, py) in enumerate(temporal.past_positions):
                alpha = int(50 + 50 * (i / max(1, len(temporal.past_positions))))
                ghost_color = (*bullet.color[:2], min(255, bullet.color[2] + 50))
                radius = int(bullet.radius * (0.5 + 0.5 * i / max(1, temporal.past_max)))
                
                # Create ghost surface
                ghost_surf = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(ghost_surf, (*ghost_color, alpha), 
                                 (radius + 1, radius + 1), radius)
                screen.blit(ghost_surf, (px - radius - 1, py - radius - 1))
            
            # Draw future predictions
            if show_predictions and temporal.future_positions:
                for i, (fx, fy) in enumerate(temporal.future_positions):
                    alpha = int(100 - 80 * (i / len(temporal.future_positions)))
                    pred_color = (255, 200, 100)  # Golden prediction color
                    
                    pred_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                    pygame.draw.circle(pred_surf, (*pred_color, alpha), (4, 4), 3)
                    screen.blit(pred_surf, (fx - 4, fy - 4))
                
                # Draw trajectory line
                if len(temporal.future_positions) > 1:
                    points = [(int(bullet.x), int(bullet.y))] + \
                             [(int(x), int(y)) for x, y in temporal.future_positions]
                    pygame.draw.lines(screen, (255, 200, 100, 100), False, points, 1)
            
            # Draw current bullet (if active at current time)
            if temporal.is_active_at_time(current_time):
                pygame.draw.circle(screen, bullet.color, 
                                 (int(bullet.x), int(bullet.y)), int(bullet.radius))
            else:
                # Draw faded if not active at current time
                faded_surf = pygame.Surface((int(bullet.radius * 2 + 2),) * 2, pygame.SRCALPHA)
                pygame.draw.circle(faded_surf, (*bullet.color, 80),
                                 (int(bullet.radius + 1),) * 2, int(bullet.radius))
                screen.blit(faded_surf, (bullet.x - bullet.radius - 1, bullet.y - bullet.radius - 1))


def create_dimensional_battlebox(
    screen_width: int,
    screen_height: int,
    dimension: CombatDimension = CombatDimension.TWO_D
) -> DimensionalBattleBox:
    """Create a dimensional battle box centered on screen."""
    box_width = 300
    box_height = 150
    box_x = screen_width // 2 - box_width // 2
    box_y = screen_height // 2 - box_height // 2 + 50  # Offset down for UI
    
    box = DimensionalBattleBox(
        base_x=box_x,
        base_y=box_y,
        base_width=box_width,
        base_height=box_height,
    )
    box.set_dimension(dimension, instant=True)
    
    return box
