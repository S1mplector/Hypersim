"""Evolution tree UI for visualizing and selecting 4D shapes."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Callable

import pygame
import numpy as np

from hypersim.game.evolution_expanded import (
    Shape4D, ShapeFamily, ShapeRarity, SHAPES_4D, EVOLUTION_PATHS,
    get_shapes_by_family, get_available_shapes
)


@dataclass
class TreeNode:
    """A node in the evolution tree visualization."""
    shape: Shape4D
    x: float
    y: float
    unlocked: bool = False
    available: bool = False
    selected: bool = False


class EvolutionTreeUI:
    """Visual evolution tree for 4D shape selection."""
    
    # Family colors
    FAMILY_COLORS = {
        ShapeFamily.REGULAR: (100, 200, 255),
        ShapeFamily.UNIFORM: (150, 180, 220),
        ShapeFamily.CELL_24: (180, 120, 255),
        ShapeFamily.PRISM: (200, 150, 150),
        ShapeFamily.DUOPRISM: (150, 200, 150),
        ShapeFamily.EXOTIC: (255, 150, 200),
        ShapeFamily.SPECIAL: (255, 200, 100),
        ShapeFamily.TRANSCENDENT: (255, 255, 200),
    }
    
    # Rarity border colors
    RARITY_COLORS = {
        ShapeRarity.COMMON: (150, 150, 150),
        ShapeRarity.UNCOMMON: (100, 200, 100),
        ShapeRarity.RARE: (100, 150, 255),
        ShapeRarity.EPIC: (200, 100, 255),
        ShapeRarity.LEGENDARY: (255, 180, 50),
        ShapeRarity.MYTHIC: (255, 100, 100),
    }
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # State
        self.visible = False
        self.nodes: Dict[str, TreeNode] = {}
        self.selected_shape: Optional[str] = None
        self.hovered_shape: Optional[str] = None
        self.unlocked_shapes: Set[str] = {"pentachoron"}
        self.current_xp = 0
        
        # View controls
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.zoom = 1.0
        self.dragging = False
        self.drag_start = (0, 0)
        
        # Animation
        self.animation_time = 0.0
        self.selected_rotation = 0.0
        
        # Layout
        self._layout_tree()
        
        # Fonts
        self._font_title = pygame.font.Font(None, 48)
        self._font_name = pygame.font.Font(None, 24)
        self._font_small = pygame.font.Font(None, 18)
        self._font_desc = pygame.font.Font(None, 20)
        
        # Callbacks
        self.on_select: Optional[Callable[[str], None]] = None
        self.on_close: Optional[Callable] = None
    
    def _layout_tree(self) -> None:
        """Layout nodes in the tree by family."""
        self.nodes.clear()
        
        # Organize by family
        families = list(ShapeFamily)
        family_y_offset = 0
        
        for family in families:
            shapes = get_shapes_by_family(family)
            if not shapes:
                continue
            
            # Sort by XP required
            shapes.sort(key=lambda s: s.xp_required)
            
            # Layout horizontally within family
            family_width = len(shapes) * 120
            start_x = -family_width // 2
            
            for i, shape in enumerate(shapes):
                x = start_x + i * 120 + 60
                y = family_y_offset
                
                self.nodes[shape.id] = TreeNode(
                    shape=shape,
                    x=x,
                    y=y,
                    unlocked=shape.id in self.unlocked_shapes,
                )
            
            family_y_offset += 150
    
    def set_state(self, unlocked: Set[str], current_xp: int, current_shape: str) -> None:
        """Update the tree state."""
        self.unlocked_shapes = unlocked
        self.current_xp = current_xp
        self.selected_shape = current_shape
        
        # Update node states
        available = get_available_shapes(unlocked, current_xp)
        available_ids = {s.id for s in available}
        
        for node in self.nodes.values():
            node.unlocked = node.shape.id in unlocked
            node.available = node.shape.id in available_ids
            node.selected = node.shape.id == current_shape
    
    def show(self) -> None:
        self.visible = True
        # Center on current shape
        if self.selected_shape and self.selected_shape in self.nodes:
            node = self.nodes[self.selected_shape]
            self.camera_x = -node.x
            self.camera_y = -node.y + 100
    
    def hide(self) -> None:
        self.visible = False
    
    def update(self, dt: float) -> None:
        """Update animations."""
        if not self.visible:
            return
        
        self.animation_time += dt
        self.selected_rotation += dt * 0.5
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input. Returns True if consumed."""
        if not self.visible:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
                if self.on_close:
                    self.on_close()
                return True
            elif event.key == pygame.K_RETURN:
                if self.hovered_shape:
                    self._select_shape(self.hovered_shape)
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check for node click
                mouse_x, mouse_y = event.pos
                clicked = self._get_node_at(mouse_x, mouse_y)
                if clicked:
                    self._select_shape(clicked)
                else:
                    # Start dragging
                    self.dragging = True
                    self.drag_start = event.pos
                return True
            elif event.button == 4:  # Scroll up
                self.zoom = min(2.0, self.zoom * 1.1)
                return True
            elif event.button == 5:  # Scroll down
                self.zoom = max(0.5, self.zoom / 1.1)
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
                return True
        
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                dx = event.pos[0] - self.drag_start[0]
                dy = event.pos[1] - self.drag_start[1]
                self.camera_x += dx / self.zoom
                self.camera_y += dy / self.zoom
                self.drag_start = event.pos
                return True
            else:
                # Update hover
                self.hovered_shape = self._get_node_at(*event.pos)
        
        return False
    
    def _get_node_at(self, mouse_x: int, mouse_y: int) -> Optional[str]:
        """Get shape ID at mouse position."""
        for shape_id, node in self.nodes.items():
            sx = self.width // 2 + (node.x + self.camera_x) * self.zoom
            sy = self.height // 2 + (node.y + self.camera_y) * self.zoom
            
            dist = math.sqrt((mouse_x - sx) ** 2 + (mouse_y - sy) ** 2)
            if dist < 40 * self.zoom:
                return shape_id
        return None
    
    def _select_shape(self, shape_id: str) -> None:
        """Select a shape."""
        node = self.nodes.get(shape_id)
        if not node:
            return
        
        if node.available or node.unlocked:
            if self.on_select:
                self.on_select(shape_id)
    
    def draw(self) -> None:
        """Draw the evolution tree."""
        if not self.visible:
            return
        
        # Darken background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title = self._font_title.render("4D EVOLUTION", True, (200, 150, 255))
        title_rect = title.get_rect(center=(self.width // 2, 40))
        self.screen.blit(title, title_rect)
        
        # XP display
        xp_text = self._font_name.render(f"Evolution XP: {self.current_xp}", True, (180, 180, 100))
        self.screen.blit(xp_text, (20, 20))
        
        # Draw connections first
        self._draw_connections()
        
        # Draw nodes
        for shape_id, node in self.nodes.items():
            self._draw_node(node)
        
        # Draw info panel for hovered/selected
        self._draw_info_panel()
        
        # Legend
        self._draw_legend()
        
        # Controls hint
        hint = self._font_small.render(
            "Scroll: Zoom | Drag: Pan | Click: Select | ESC: Close",
            True, (100, 100, 120)
        )
        hint_rect = hint.get_rect(center=(self.width // 2, self.height - 20))
        self.screen.blit(hint, hint_rect)
    
    def _draw_connections(self) -> None:
        """Draw connections between shapes."""
        for shape_id, node in self.nodes.items():
            shape = node.shape
            
            # Draw lines to prerequisites
            for req_id in shape.requires_shapes:
                req_node = self.nodes.get(req_id)
                if not req_node:
                    continue
                
                sx = self.width // 2 + (node.x + self.camera_x) * self.zoom
                sy = self.height // 2 + (node.y + self.camera_y) * self.zoom
                ex = self.width // 2 + (req_node.x + self.camera_x) * self.zoom
                ey = self.height // 2 + (req_node.y + self.camera_y) * self.zoom
                
                # Color based on unlocked state
                if node.unlocked:
                    color = (100, 200, 100)
                elif node.available:
                    color = (200, 200, 100)
                else:
                    color = (60, 60, 80)
                
                pygame.draw.line(self.screen, color, (sx, sy), (ex, ey), 2)
    
    def _draw_node(self, node: TreeNode) -> None:
        """Draw a single tree node."""
        shape = node.shape
        
        # Calculate screen position
        sx = self.width // 2 + (node.x + self.camera_x) * self.zoom
        sy = self.height // 2 + (node.y + self.camera_y) * self.zoom
        
        # Skip if off screen
        if sx < -50 or sx > self.width + 50 or sy < -50 or sy > self.height + 50:
            return
        
        radius = int(35 * self.zoom)
        
        # Background color based on family
        bg_color = self.FAMILY_COLORS.get(shape.family, (100, 100, 100))
        
        # Adjust based on state
        if not node.unlocked and not node.available:
            bg_color = tuple(c // 3 for c in bg_color)
        elif node.available and not node.unlocked:
            bg_color = tuple(c // 2 for c in bg_color)
        
        # Draw node background
        pygame.draw.circle(self.screen, bg_color, (int(sx), int(sy)), radius)
        
        # Border based on rarity
        border_color = self.RARITY_COLORS.get(shape.rarity, (150, 150, 150))
        border_width = 2 if not node.selected else 4
        
        if node.selected:
            # Animated selection ring
            pulse = 0.2 * math.sin(self.animation_time * 3) + 1.0
            border_color = (255, 220, 100)
            pygame.draw.circle(
                self.screen, border_color,
                (int(sx), int(sy)), int(radius * pulse), border_width
            )
        else:
            pygame.draw.circle(self.screen, border_color, (int(sx), int(sy)), radius, border_width)
        
        # Hover highlight
        if node.shape.id == self.hovered_shape:
            pygame.draw.circle(self.screen, (255, 255, 255), (int(sx), int(sy)), radius + 3, 1)
        
        # Draw shape preview (simplified polytope icon)
        self._draw_shape_icon(sx, sy, shape, radius * 0.6, node.unlocked or node.available)
        
        # Name below
        if self.zoom > 0.7:
            name_color = (200, 200, 220) if node.unlocked else (120, 120, 140)
            name = self._font_small.render(shape.short_name, True, name_color)
            name_rect = name.get_rect(center=(int(sx), int(sy) + radius + 12))
            self.screen.blit(name, name_rect)
        
        # XP requirement
        if not node.unlocked and self.zoom > 0.7:
            xp_color = (100, 200, 100) if node.available else (150, 100, 100)
            xp_text = self._font_small.render(f"{shape.xp_required} XP", True, xp_color)
            xp_rect = xp_text.get_rect(center=(int(sx), int(sy) + radius + 26))
            self.screen.blit(xp_text, xp_rect)
    
    def _draw_shape_icon(self, x: float, y: float, shape: Shape4D, size: float, bright: bool) -> None:
        """Draw a simplified icon for a shape."""
        alpha = 1.0 if bright else 0.4
        color = tuple(int(c * alpha) for c in shape.color)
        
        # Different icons per family
        if shape.family == ShapeFamily.REGULAR:
            # Regular polygon approximation
            sides = min(8, shape.cells)
            points = []
            for i in range(sides):
                angle = 2 * math.pi * i / sides - math.pi / 2
                px = x + math.cos(angle) * size
                py = y + math.sin(angle) * size
                points.append((px, py))
            if len(points) >= 3:
                pygame.draw.polygon(self.screen, color, points, 2)
        
        elif shape.family == ShapeFamily.EXOTIC:
            # Spiral/twisted shape
            points = []
            for i in range(12):
                angle = 2 * math.pi * i / 12 + self.selected_rotation
                r = size * (0.5 + 0.5 * math.sin(i * 0.5))
                px = x + math.cos(angle) * r
                py = y + math.sin(angle) * r
                points.append((px, py))
            pygame.draw.lines(self.screen, color, True, points, 2)
        
        elif shape.family == ShapeFamily.PRISM:
            # Extruded shape
            pygame.draw.rect(
                self.screen, color,
                (x - size * 0.5, y - size * 0.7, size, size * 1.4), 2
            )
            pygame.draw.line(self.screen, color, (x - size * 0.5, y), (x + size * 0.5, y), 1)
        
        else:
            # Default: circle with cross
            pygame.draw.circle(self.screen, color, (int(x), int(y)), int(size * 0.8), 2)
            pygame.draw.line(self.screen, color, (x - size * 0.5, y), (x + size * 0.5, y), 1)
            pygame.draw.line(self.screen, color, (x, y - size * 0.5), (x, y + size * 0.5), 1)
    
    def _draw_info_panel(self) -> None:
        """Draw info panel for selected/hovered shape."""
        shape_id = self.hovered_shape or self.selected_shape
        if not shape_id:
            return
        
        node = self.nodes.get(shape_id)
        if not node:
            return
        
        shape = node.shape
        
        # Panel position
        panel_width = 280
        panel_height = 200
        panel_x = self.width - panel_width - 20
        panel_y = 80
        
        # Background
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((20, 20, 30, 230))
        self.screen.blit(panel_surface, (panel_x, panel_y))
        
        # Border
        border_color = self.RARITY_COLORS.get(shape.rarity, (150, 150, 150))
        pygame.draw.rect(self.screen, border_color, (panel_x, panel_y, panel_width, panel_height), 2)
        
        # Content
        y = panel_y + 10
        
        # Name and rarity
        name = self._font_name.render(shape.name, True, shape.color)
        self.screen.blit(name, (panel_x + 10, y))
        y += 25
        
        rarity_text = self._font_small.render(f"{shape.rarity.name} - {shape.family.value}", True, border_color)
        self.screen.blit(rarity_text, (panel_x + 10, y))
        y += 20
        
        # Geometry
        geom = f"{shape.vertices}v {shape.edges}e {shape.faces}f {shape.cells}c"
        geom_text = self._font_small.render(geom, True, (150, 150, 170))
        self.screen.blit(geom_text, (panel_x + 10, y))
        y += 20
        
        # Stats
        stats = [
            f"HP: +{int(shape.health_bonus)}",
            f"SPD: +{shape.speed_bonus:.1f}",
            f"W: {shape.w_perception:.1f}",
            f"DR: {int(shape.damage_reduction * 100)}%",
        ]
        stats_text = self._font_small.render(" | ".join(stats), True, (180, 180, 200))
        self.screen.blit(stats_text, (panel_x + 10, y))
        y += 25
        
        # Description (wrapped)
        desc_lines = self._wrap_text(shape.description, self._font_small, panel_width - 20)
        for line in desc_lines[:3]:
            desc_text = self._font_small.render(line, True, (140, 140, 160))
            self.screen.blit(desc_text, (panel_x + 10, y))
            y += 16
        
        # Requirements
        y = panel_y + panel_height - 30
        if shape.xp_required > 0:
            req_color = (100, 200, 100) if self.current_xp >= shape.xp_required else (200, 100, 100)
            req_text = self._font_small.render(f"Requires: {shape.xp_required} XP", True, req_color)
            self.screen.blit(req_text, (panel_x + 10, y))
    
    def _draw_legend(self) -> None:
        """Draw family color legend."""
        x = 20
        y = self.height - 120
        
        legend_title = self._font_small.render("Families:", True, (150, 150, 170))
        self.screen.blit(legend_title, (x, y))
        y += 18
        
        for family in [ShapeFamily.REGULAR, ShapeFamily.UNIFORM, ShapeFamily.EXOTIC, ShapeFamily.PRISM]:
            color = self.FAMILY_COLORS.get(family, (100, 100, 100))
            pygame.draw.circle(self.screen, color, (x + 8, y + 6), 6)
            label = self._font_small.render(family.value.title(), True, (130, 130, 150))
            self.screen.blit(label, (x + 20, y))
            y += 16
    
    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        """Wrap text to fit width."""
        words = text.split()
        lines = []
        current = ""
        
        for word in words:
            test = current + (" " if current else "") + word
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        
        if current:
            lines.append(current)
        
        return lines
