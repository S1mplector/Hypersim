"""HUD (Heads-Up Display) system for rendering overlays.

Provides a flexible system for rendering UI elements, statistics,
and information overlays on top of the 3D scene.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Tuple, Optional, Dict, Callable, Any
import pygame


class Anchor(Enum):
    """Anchor points for HUD elements."""
    TOP_LEFT = auto()
    TOP_CENTER = auto()
    TOP_RIGHT = auto()
    CENTER_LEFT = auto()
    CENTER = auto()
    CENTER_RIGHT = auto()
    BOTTOM_LEFT = auto()
    BOTTOM_CENTER = auto()
    BOTTOM_RIGHT = auto()


@dataclass
class HUDStyle:
    """Style configuration for HUD elements."""
    font_name: str = "Arial"
    font_size: int = 18
    color: Tuple[int, int, int] = (220, 220, 240)
    background_color: Optional[Tuple[int, int, int, int]] = (10, 10, 20, 180)
    padding: int = 10
    margin: int = 15
    line_spacing: int = 4


@dataclass
class HUDElement:
    """A single HUD element."""
    content: str | Callable[[], str]
    anchor: Anchor = Anchor.TOP_LEFT
    style: Optional[HUDStyle] = None
    visible: bool = True
    order: int = 0


class HUD:
    """Manages HUD elements and rendering.
    
    Provides methods to add, remove, and render various UI elements
    including text, panels, and dynamic content.
    """
    
    def __init__(self, screen: pygame.Surface):
        """Initialize the HUD system.
        
        Args:
            screen: Pygame surface to render to
        """
        self.screen = screen
        self.default_style = HUDStyle()
        self._elements: Dict[str, HUDElement] = {}
        self._fonts: Dict[Tuple[str, int], pygame.font.Font] = {}
        
        # Built-in panels
        self._stats_visible = False
        self._help_visible = False
        self._info_panel_data: Dict[str, Any] = {}
    
    def _get_font(self, style: HUDStyle) -> pygame.font.Font:
        """Get or create a font for the given style."""
        key = (style.font_name, style.font_size)
        if key not in self._fonts:
            try:
                self._fonts[key] = pygame.font.SysFont(style.font_name, style.font_size)
            except Exception:
                self._fonts[key] = pygame.font.Font(None, style.font_size)
        return self._fonts[key]
    
    def add_element(
        self,
        name: str,
        content: str | Callable[[], str],
        anchor: Anchor = Anchor.TOP_LEFT,
        style: Optional[HUDStyle] = None,
        order: int = 0,
    ) -> None:
        """Add a HUD element.
        
        Args:
            name: Unique identifier for the element
            content: Static text or callable that returns text
            anchor: Screen anchor point
            style: Optional style override
            order: Render order (lower = first)
        """
        self._elements[name] = HUDElement(
            content=content,
            anchor=anchor,
            style=style,
            order=order,
        )
    
    def remove_element(self, name: str) -> None:
        """Remove a HUD element by name."""
        self._elements.pop(name, None)
    
    def set_visible(self, name: str, visible: bool) -> None:
        """Set visibility of a HUD element."""
        if name in self._elements:
            self._elements[name].visible = visible
    
    def toggle_stats(self) -> None:
        """Toggle the statistics panel."""
        self._stats_visible = not self._stats_visible
    
    def toggle_help(self) -> None:
        """Toggle the help panel."""
        self._help_visible = not self._help_visible
    
    def update_info_panel(self, data: Dict[str, Any]) -> None:
        """Update the info panel data."""
        self._info_panel_data.update(data)
    
    def render(
        self,
        fps: float = 0.0,
        stats: Optional[Dict[str, Any]] = None,
        help_text: Optional[List[str]] = None,
    ) -> None:
        """Render all HUD elements.
        
        Args:
            fps: Current FPS for stats panel
            stats: Additional stats to display
            help_text: Help text lines
        """
        # Render custom elements
        sorted_elements = sorted(
            self._elements.values(),
            key=lambda e: e.order
        )
        
        for element in sorted_elements:
            if not element.visible:
                continue
            self._render_element(element)
        
        # Render built-in panels
        if self._stats_visible:
            self._render_stats_panel(fps, stats or {})
        
        if self._help_visible:
            self._render_help_panel(help_text or self._default_help())
        
        if self._info_panel_data:
            self._render_info_panel()
    
    def _render_element(self, element: HUDElement) -> None:
        """Render a single HUD element."""
        style = element.style or self.default_style
        font = self._get_font(style)
        
        # Get content
        if callable(element.content):
            text = element.content()
        else:
            text = element.content
        
        lines = text.split('\n')
        
        # Calculate total size
        line_surfaces = [font.render(line, True, style.color) for line in lines]
        total_width = max(s.get_width() for s in line_surfaces) + style.padding * 2
        total_height = sum(s.get_height() for s in line_surfaces) + style.line_spacing * (len(lines) - 1) + style.padding * 2
        
        # Calculate position
        x, y = self._get_anchor_position(element.anchor, total_width, total_height, style.margin)
        
        # Draw background
        if style.background_color:
            bg_surface = pygame.Surface((total_width, total_height), pygame.SRCALPHA)
            bg_surface.fill(style.background_color)
            self.screen.blit(bg_surface, (x, y))
        
        # Draw text
        current_y = y + style.padding
        for surface in line_surfaces:
            self.screen.blit(surface, (x + style.padding, current_y))
            current_y += surface.get_height() + style.line_spacing
    
    def _get_anchor_position(
        self,
        anchor: Anchor,
        width: int,
        height: int,
        margin: int,
    ) -> Tuple[int, int]:
        """Calculate position based on anchor point."""
        sw, sh = self.screen.get_size()
        
        if anchor in (Anchor.TOP_LEFT, Anchor.CENTER_LEFT, Anchor.BOTTOM_LEFT):
            x = margin
        elif anchor in (Anchor.TOP_CENTER, Anchor.CENTER, Anchor.BOTTOM_CENTER):
            x = (sw - width) // 2
        else:
            x = sw - width - margin
        
        if anchor in (Anchor.TOP_LEFT, Anchor.TOP_CENTER, Anchor.TOP_RIGHT):
            y = margin
        elif anchor in (Anchor.CENTER_LEFT, Anchor.CENTER, Anchor.CENTER_RIGHT):
            y = (sh - height) // 2
        else:
            y = sh - height - margin
        
        return x, y
    
    def _render_stats_panel(self, fps: float, stats: Dict[str, Any]) -> None:
        """Render the statistics panel."""
        style = HUDStyle(font_size=16, color=(180, 220, 180))
        font = self._get_font(style)
        
        lines = [
            f"FPS: {fps:.1f}",
            f"Vertices: {stats.get('vertices', 0)}",
            f"Edges: {stats.get('edges', 0)}",
            f"Objects: {stats.get('objects', 0)}",
        ]
        
        if 'render_ms' in stats:
            lines.append(f"Render: {stats['render_ms']:.2f}ms")
        
        line_surfaces = [font.render(line, True, style.color) for line in lines]
        width = max(s.get_width() for s in line_surfaces) + 20
        height = sum(s.get_height() for s in line_surfaces) + 15 * (len(lines) - 1) + 20
        
        x, y = self.screen.get_width() - width - 15, 15
        
        bg = pygame.Surface((width, height), pygame.SRCALPHA)
        bg.fill((10, 20, 10, 200))
        self.screen.blit(bg, (x, y))
        
        current_y = y + 10
        for surface in line_surfaces:
            self.screen.blit(surface, (x + 10, current_y))
            current_y += surface.get_height() + 5
    
    def _render_help_panel(self, lines: List[str]) -> None:
        """Render the help panel."""
        style = HUDStyle(font_size=16, color=(200, 200, 220))
        font = self._get_font(style)
        
        line_surfaces = [font.render(line, True, style.color) for line in lines]
        width = max(s.get_width() for s in line_surfaces) + 30
        height = sum(s.get_height() for s in line_surfaces) + 8 * (len(lines) - 1) + 30
        
        x = (self.screen.get_width() - width) // 2
        y = (self.screen.get_height() - height) // 2
        
        bg = pygame.Surface((width, height), pygame.SRCALPHA)
        bg.fill((20, 20, 40, 230))
        self.screen.blit(bg, (x, y))
        
        # Title
        title_font = self._get_font(HUDStyle(font_size=20))
        title = title_font.render("Controls", True, (255, 255, 255))
        self.screen.blit(title, (x + (width - title.get_width()) // 2, y + 10))
        
        current_y = y + 40
        for surface in line_surfaces:
            self.screen.blit(surface, (x + 15, current_y))
            current_y += surface.get_height() + 4
    
    def _render_info_panel(self) -> None:
        """Render the info panel with current object data."""
        if not self._info_panel_data:
            return
        
        style = HUDStyle(font_size=16, color=(220, 220, 240))
        font = self._get_font(style)
        
        lines = []
        for key, value in self._info_panel_data.items():
            if isinstance(value, float):
                lines.append(f"{key}: {value:.3f}")
            else:
                lines.append(f"{key}: {value}")
        
        if not lines:
            return
        
        line_surfaces = [font.render(line, True, style.color) for line in lines]
        width = max(s.get_width() for s in line_surfaces) + 20
        height = sum(s.get_height() for s in line_surfaces) + 5 * (len(lines) - 1) + 20
        
        x, y = 15, self.screen.get_height() - height - 15
        
        bg = pygame.Surface((width, height), pygame.SRCALPHA)
        bg.fill((20, 20, 40, 200))
        self.screen.blit(bg, (x, y))
        
        current_y = y + 10
        for surface in line_surfaces:
            self.screen.blit(surface, (x + 10, current_y))
            current_y += surface.get_height() + 5
    
    def _default_help(self) -> List[str]:
        """Get default help text."""
        return [
            "Mouse Drag: Orbit camera",
            "Scroll: Zoom in/out",
            "W/A/S/D: Move camera",
            "Q/E: Move up/down",
            "Z/X: Move along W axis",
            "+/-: Adjust projection",
            "T: Toggle auto-spin",
            "F: Toggle solid/wireframe",
            "Tab: Toggle stats",
            "H: Toggle help",
            "R: Reset view",
            "ESC: Quit",
        ]
