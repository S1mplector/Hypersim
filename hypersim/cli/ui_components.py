"""Reusable UI components for Pygame-based interfaces.

Provides modern, animated UI elements including buttons, panels,
sliders, tabs, and more.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, List, Optional, Tuple, Dict, Any
import pygame
import math


# Color palette
class Colors:
    """Modern color palette for UI."""
    BG_DARK = (8, 10, 18)
    BG_PANEL = (16, 20, 32)
    BG_HOVER = (24, 30, 48)
    BG_ACTIVE = (32, 40, 64)
    
    TEXT_PRIMARY = (240, 240, 250)
    TEXT_SECONDARY = (180, 185, 200)
    TEXT_MUTED = (120, 125, 140)
    
    ACCENT_BLUE = (80, 160, 255)
    ACCENT_CYAN = (80, 220, 220)
    ACCENT_GREEN = (100, 220, 140)
    ACCENT_ORANGE = (255, 180, 80)
    ACCENT_PURPLE = (180, 120, 255)
    ACCENT_PINK = (255, 120, 180)
    
    BORDER = (50, 55, 70)
    BORDER_HOVER = (80, 90, 120)
    
    SUCCESS = (80, 200, 120)
    WARNING = (255, 200, 80)
    ERROR = (255, 100, 100)


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation."""
    return a + (b - a) * t


def lerp_color(c1: Tuple[int, ...], c2: Tuple[int, ...], t: float) -> Tuple[int, ...]:
    """Interpolate between two colors."""
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(len(c1)))


def ease_out_cubic(t: float) -> float:
    """Cubic ease-out function."""
    return 1 - (1 - t) ** 3


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out function."""
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


@dataclass
class Animation:
    """Simple animation state."""
    start_value: float = 0.0
    end_value: float = 1.0
    duration: float = 0.3
    elapsed: float = 0.0
    easing: Callable[[float], float] = ease_out_cubic
    
    @property
    def progress(self) -> float:
        if self.duration <= 0:
            return 1.0
        return min(1.0, self.elapsed / self.duration)
    
    @property
    def value(self) -> float:
        return lerp(self.start_value, self.end_value, self.easing(self.progress))
    
    @property
    def finished(self) -> bool:
        return self.elapsed >= self.duration
    
    def update(self, dt: float) -> None:
        self.elapsed += dt
    
    def reset(self, start: float, end: float, duration: float = 0.3) -> None:
        self.start_value = start
        self.end_value = end
        self.duration = duration
        self.elapsed = 0.0


class Button:
    """Animated button with hover and click effects."""
    
    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        on_click: Optional[Callable[[], None]] = None,
        color: Tuple[int, int, int] = Colors.ACCENT_BLUE,
        font_size: int = 18,
        icon: Optional[str] = None,
    ):
        self.rect = rect
        self.text = text
        self.on_click = on_click
        self.color = color
        self.font_size = font_size
        self.icon = icon
        
        self.hovered = False
        self.pressed = False
        self.enabled = True
        self.visible = True
        
        self._hover_anim = Animation(0, 0, 0.15)
        self._press_anim = Animation(0, 0, 0.1)
        self._font = pygame.font.SysFont("Arial", font_size)
    
    def update(self, dt: float, mouse_pos: Tuple[int, int]) -> None:
        if not self.visible:
            return
        
        was_hovered = self.hovered
        self.hovered = self.rect.collidepoint(mouse_pos) and self.enabled
        
        if self.hovered and not was_hovered:
            self._hover_anim.reset(self._hover_anim.value, 1.0, 0.15)
        elif not self.hovered and was_hovered:
            self._hover_anim.reset(self._hover_anim.value, 0.0, 0.15)
        
        self._hover_anim.update(dt)
        self._press_anim.update(dt)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible or not self.enabled:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
                self._press_anim.reset(0, 1, 0.05)
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed:
                self.pressed = False
                self._press_anim.reset(1, 0, 0.1)
                if self.rect.collidepoint(event.pos) and self.on_click:
                    self.on_click()
                return True
        
        return False
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        
        hover_t = self._hover_anim.value
        press_t = self._press_anim.value
        
        # Background
        bg_color = lerp_color(Colors.BG_PANEL, Colors.BG_HOVER, hover_t)
        if press_t > 0:
            bg_color = lerp_color(bg_color, Colors.BG_ACTIVE, press_t)
        
        # Draw rounded rect
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=6)
        
        # Border
        border_color = lerp_color(Colors.BORDER, self.color, hover_t * 0.5)
        pygame.draw.rect(surface, border_color, self.rect, width=1, border_radius=6)
        
        # Accent line at bottom when hovered
        if hover_t > 0:
            accent_rect = pygame.Rect(
                self.rect.x + 4,
                self.rect.bottom - 3,
                int((self.rect.width - 8) * hover_t),
                2
            )
            pygame.draw.rect(surface, self.color, accent_rect, border_radius=1)
        
        # Text
        text_color = lerp_color(Colors.TEXT_SECONDARY, Colors.TEXT_PRIMARY, hover_t)
        if not self.enabled:
            text_color = Colors.TEXT_MUTED
        
        text_surf = self._font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        
        # Slight scale effect on press
        if press_t > 0:
            scale = 1 - press_t * 0.05
            text_rect.y += int(press_t * 2)
        
        surface.blit(text_surf, text_rect)


class Slider:
    """Horizontal slider with smooth animation."""
    
    def __init__(
        self,
        rect: pygame.Rect,
        min_value: float = 0.0,
        max_value: float = 1.0,
        value: float = 0.5,
        on_change: Optional[Callable[[float], None]] = None,
        label: str = "",
        color: Tuple[int, int, int] = Colors.ACCENT_BLUE,
    ):
        self.rect = rect
        self.min_value = min_value
        self.max_value = max_value
        self._value = value
        self.on_change = on_change
        self.label = label
        self.color = color
        
        self.dragging = False
        self.hovered = False
        self.visible = True
        
        self._font = pygame.font.SysFont("Arial", 14)
        self._value_font = pygame.font.SysFont("Arial", 12)
    
    @property
    def value(self) -> float:
        return self._value
    
    @value.setter
    def value(self, v: float) -> None:
        old = self._value
        self._value = max(self.min_value, min(self.max_value, v))
        if old != self._value and self.on_change:
            self.on_change(self._value)
    
    @property
    def normalized(self) -> float:
        range_ = self.max_value - self.min_value
        if range_ == 0:
            return 0
        return (self._value - self.min_value) / range_
    
    def update(self, dt: float, mouse_pos: Tuple[int, int]) -> None:
        if not self.visible:
            return
        
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        if self.dragging:
            rel_x = mouse_pos[0] - self.rect.x
            normalized = max(0, min(1, rel_x / self.rect.width))
            self.value = self.min_value + normalized * (self.max_value - self.min_value)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                rel_x = event.pos[0] - self.rect.x
                normalized = max(0, min(1, rel_x / self.rect.width))
                self.value = self.min_value + normalized * (self.max_value - self.min_value)
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True
        
        return False
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        
        # Label
        if self.label:
            label_surf = self._font.render(self.label, True, Colors.TEXT_SECONDARY)
            surface.blit(label_surf, (self.rect.x, self.rect.y - 20))
        
        # Track
        track_rect = pygame.Rect(
            self.rect.x, self.rect.centery - 3,
            self.rect.width, 6
        )
        pygame.draw.rect(surface, Colors.BG_PANEL, track_rect, border_radius=3)
        
        # Fill
        fill_width = int(self.rect.width * self.normalized)
        if fill_width > 0:
            fill_rect = pygame.Rect(
                self.rect.x, self.rect.centery - 3,
                fill_width, 6
            )
            pygame.draw.rect(surface, self.color, fill_rect, border_radius=3)
        
        # Handle
        handle_x = self.rect.x + fill_width
        handle_radius = 10 if (self.hovered or self.dragging) else 8
        handle_color = Colors.TEXT_PRIMARY if self.dragging else self.color
        pygame.draw.circle(surface, handle_color, (handle_x, self.rect.centery), handle_radius)
        
        # Value display
        value_text = f"{self._value:.2f}"
        value_surf = self._value_font.render(value_text, True, Colors.TEXT_MUTED)
        surface.blit(value_surf, (self.rect.right + 10, self.rect.centery - 6))


class Panel:
    """Container panel with optional title and collapse."""
    
    def __init__(
        self,
        rect: pygame.Rect,
        title: str = "",
        collapsible: bool = False,
        collapsed: bool = False,
        bg_color: Tuple[int, int, int, int] = (*Colors.BG_PANEL, 230),
    ):
        self.rect = rect
        self.title = title
        self.collapsible = collapsible
        self.collapsed = collapsed
        self.bg_color = bg_color
        self.visible = True
        
        self._title_font = pygame.font.SysFont("Arial", 16, bold=True)
        self._collapse_anim = Animation(0 if collapsed else 1, 0 if collapsed else 1, 0)
        self._content_height = rect.height - 40 if title else rect.height
    
    def toggle_collapse(self) -> None:
        if not self.collapsible:
            return
        self.collapsed = not self.collapsed
        target = 0 if self.collapsed else 1
        self._collapse_anim.reset(self._collapse_anim.value, target, 0.25)
    
    def update(self, dt: float) -> None:
        self._collapse_anim.update(dt)
    
    @property
    def content_rect(self) -> pygame.Rect:
        """Get the rect for content area."""
        if self.title:
            return pygame.Rect(
                self.rect.x + 10,
                self.rect.y + 40,
                self.rect.width - 20,
                int(self._content_height * self._collapse_anim.value)
            )
        return pygame.Rect(
            self.rect.x + 10,
            self.rect.y + 10,
            self.rect.width - 20,
            int((self.rect.height - 20) * self._collapse_anim.value)
        )
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        
        # Calculate current height
        if self.title:
            current_height = 40 + int(self._content_height * self._collapse_anim.value)
        else:
            current_height = int(self.rect.height * self._collapse_anim.value)
        
        draw_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, current_height)
        
        # Background
        bg_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
        bg_surf.fill(self.bg_color)
        surface.blit(bg_surf, draw_rect.topleft)
        
        # Border
        pygame.draw.rect(surface, Colors.BORDER, draw_rect, width=1, border_radius=8)
        
        # Title
        if self.title:
            title_surf = self._title_font.render(self.title, True, Colors.TEXT_PRIMARY)
            surface.blit(title_surf, (self.rect.x + 15, self.rect.y + 12))
            
            # Collapse indicator
            if self.collapsible:
                indicator_x = self.rect.right - 25
                indicator_y = self.rect.y + 20
                angle = math.pi * (1 - self._collapse_anim.value) / 2
                
                points = [
                    (indicator_x - 5, indicator_y - 3),
                    (indicator_x + 5, indicator_y - 3),
                    (indicator_x, indicator_y + 4),
                ]
                if self._collapse_anim.value < 0.5:
                    points = [
                        (indicator_x - 3, indicator_y - 5),
                        (indicator_x - 3, indicator_y + 5),
                        (indicator_x + 4, indicator_y),
                    ]
                pygame.draw.polygon(surface, Colors.TEXT_MUTED, points)


class TabBar:
    """Horizontal tab bar."""
    
    def __init__(
        self,
        rect: pygame.Rect,
        tabs: List[str],
        on_change: Optional[Callable[[int], None]] = None,
    ):
        self.rect = rect
        self.tabs = tabs
        self.on_change = on_change
        self.selected = 0
        self.visible = True
        
        self._font = pygame.font.SysFont("Arial", 15)
        self._indicator_anim = Animation(0, 0, 0.2)
        self._indicator_pos = 0.0
    
    def select(self, index: int) -> None:
        if 0 <= index < len(self.tabs) and index != self.selected:
            old = self.selected
            self.selected = index
            self._indicator_anim.reset(old, index, 0.2)
            if self.on_change:
                self.on_change(index)
    
    def update(self, dt: float) -> None:
        self._indicator_anim.update(dt)
        self._indicator_pos = self._indicator_anim.value
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                tab_width = self.rect.width / len(self.tabs)
                clicked_tab = int((event.pos[0] - self.rect.x) / tab_width)
                self.select(clicked_tab)
                return True
        
        return False
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        
        # Background
        pygame.draw.rect(surface, Colors.BG_PANEL, self.rect, border_radius=6)
        
        tab_width = self.rect.width / len(self.tabs)
        
        # Indicator
        indicator_x = self.rect.x + self._indicator_pos * tab_width
        indicator_rect = pygame.Rect(
            int(indicator_x) + 4, self.rect.y + 4,
            int(tab_width) - 8, self.rect.height - 8
        )
        pygame.draw.rect(surface, Colors.BG_ACTIVE, indicator_rect, border_radius=4)
        
        # Tab labels
        for i, tab in enumerate(self.tabs):
            tab_rect = pygame.Rect(
                self.rect.x + i * tab_width, self.rect.y,
                tab_width, self.rect.height
            )
            
            color = Colors.TEXT_PRIMARY if i == self.selected else Colors.TEXT_MUTED
            text_surf = self._font.render(tab, True, color)
            text_rect = text_surf.get_rect(center=tab_rect.center)
            surface.blit(text_surf, text_rect)


class SearchBox:
    """Text input for search."""
    
    def __init__(
        self,
        rect: pygame.Rect,
        placeholder: str = "Search...",
        on_change: Optional[Callable[[str], None]] = None,
    ):
        self.rect = rect
        self.placeholder = placeholder
        self.on_change = on_change
        self.text = ""
        self.focused = False
        self.visible = True
        
        self._font = pygame.font.SysFont("Arial", 16)
        self._cursor_visible = True
        self._cursor_timer = 0.0
    
    def update(self, dt: float, mouse_pos: Tuple[int, int] = (0, 0)) -> None:
        if self.focused:
            self._cursor_timer += dt
            if self._cursor_timer > 0.5:
                self._cursor_visible = not self._cursor_visible
                self._cursor_timer = 0
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.focused = self.rect.collidepoint(event.pos)
            return self.focused
        
        if event.type == pygame.KEYDOWN and self.focused:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                if self.on_change:
                    self.on_change(self.text)
                return True
            elif event.key == pygame.K_ESCAPE:
                self.focused = False
                return True
            elif event.unicode and event.unicode.isprintable():
                self.text += event.unicode
                if self.on_change:
                    self.on_change(self.text)
                return True
        
        return False
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        
        # Background
        bg_color = Colors.BG_ACTIVE if self.focused else Colors.BG_PANEL
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=6)
        
        # Border
        border_color = Colors.ACCENT_BLUE if self.focused else Colors.BORDER
        pygame.draw.rect(surface, border_color, self.rect, width=1, border_radius=6)
        
        # Search icon
        icon_x = self.rect.x + 12
        icon_y = self.rect.centery
        pygame.draw.circle(surface, Colors.TEXT_MUTED, (icon_x, icon_y - 2), 6, 1)
        pygame.draw.line(surface, Colors.TEXT_MUTED, (icon_x + 4, icon_y + 2), (icon_x + 8, icon_y + 6), 2)
        
        # Text or placeholder
        text_x = self.rect.x + 30
        if self.text:
            text_surf = self._font.render(self.text, True, Colors.TEXT_PRIMARY)
        else:
            text_surf = self._font.render(self.placeholder, True, Colors.TEXT_MUTED)
        
        surface.blit(text_surf, (text_x, self.rect.centery - text_surf.get_height() // 2))
        
        # Cursor
        if self.focused and self._cursor_visible:
            cursor_x = text_x + self._font.size(self.text)[0] + 2
            pygame.draw.line(
                surface, Colors.TEXT_PRIMARY,
                (cursor_x, self.rect.y + 8),
                (cursor_x, self.rect.bottom - 8),
                2
            )


class Toggle:
    """Toggle switch."""
    
    def __init__(
        self,
        pos: Tuple[int, int],
        label: str = "",
        value: bool = False,
        on_change: Optional[Callable[[bool], None]] = None,
    ):
        self.pos = pos
        self.label = label
        self._value = value
        self.on_change = on_change
        self.visible = True
        
        self._anim = Animation(1.0 if value else 0.0, 1.0 if value else 0.0, 0)
        self._font = pygame.font.SysFont("Arial", 14)
        
        self.rect = pygame.Rect(pos[0], pos[1], 44, 24)
    
    @property
    def value(self) -> bool:
        return self._value
    
    @value.setter
    def value(self, v: bool) -> None:
        if v != self._value:
            self._value = v
            self._anim.reset(self._anim.value, 1.0 if v else 0.0, 0.2)
            if self.on_change:
                self.on_change(v)
    
    def toggle(self) -> None:
        self.value = not self._value
    
    def update(self, dt: float) -> None:
        self._anim.update(dt)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.toggle()
                return True
        
        return False
    
    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        
        t = self._anim.value
        
        # Track
        track_color = lerp_color(Colors.BG_PANEL, Colors.ACCENT_GREEN, t)
        pygame.draw.rect(surface, track_color, self.rect, border_radius=12)
        
        # Border
        pygame.draw.rect(surface, Colors.BORDER, self.rect, width=1, border_radius=12)
        
        # Knob
        knob_x = int(lerp(self.rect.x + 12, self.rect.right - 12, t))
        pygame.draw.circle(surface, Colors.TEXT_PRIMARY, (knob_x, self.rect.centery), 9)
        
        # Label
        if self.label:
            label_surf = self._font.render(self.label, True, Colors.TEXT_SECONDARY)
            surface.blit(label_surf, (self.rect.right + 10, self.rect.centery - 7))


class Toast:
    """Temporary notification message."""
    
    def __init__(
        self,
        message: str,
        duration: float = 3.0,
        color: Tuple[int, int, int] = Colors.ACCENT_BLUE,
    ):
        self.message = message
        self.duration = duration
        self.color = color
        self.elapsed = 0.0
        
        self._font = pygame.font.SysFont("Arial", 16)
    
    @property
    def finished(self) -> bool:
        return self.elapsed >= self.duration
    
    def update(self, dt: float) -> None:
        self.elapsed += dt
    
    def draw(self, surface: pygame.Surface, pos: Tuple[int, int]) -> None:
        # Fade animation
        fade_in = min(1.0, self.elapsed / 0.3)
        fade_out = max(0.0, 1.0 - (self.elapsed - self.duration + 0.3) / 0.3) if self.elapsed > self.duration - 0.3 else 1.0
        alpha = int(255 * fade_in * fade_out)
        
        if alpha <= 0:
            return
        
        text_surf = self._font.render(self.message, True, Colors.TEXT_PRIMARY)
        width = text_surf.get_width() + 30
        height = 40
        
        # Background
        bg_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (*self.color, alpha), (0, 0, width, height), border_radius=8)
        
        # Slide up animation
        y_offset = int((1 - fade_in) * 20)
        
        surface.blit(bg_surf, (pos[0] - width // 2, pos[1] + y_offset))
        
        # Text with alpha
        text_surf.set_alpha(alpha)
        surface.blit(text_surf, (pos[0] - text_surf.get_width() // 2, pos[1] + y_offset + 10))
