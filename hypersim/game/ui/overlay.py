"""Overlay management for UI layers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, List, Optional, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    pass


class OverlayPriority(IntEnum):
    """Drawing priority for overlays (higher = on top)."""
    BACKGROUND = 0
    GAME_UI = 10
    DIALOGUE = 20
    MENU = 30
    NOTIFICATION = 40
    DEBUG = 100


class Overlay(ABC):
    """Base class for UI overlays."""
    
    def __init__(self, priority: OverlayPriority = OverlayPriority.GAME_UI):
        self.priority = priority
        self.visible = True
        self.blocks_input = False
        self.blocks_game = False
    
    @abstractmethod
    def update(self, dt: float) -> None:
        """Update overlay state."""
        pass
    
    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the overlay."""
        pass
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input event. Returns True if consumed."""
        return False
    
    def show(self) -> None:
        self.visible = True
    
    def hide(self) -> None:
        self.visible = False


@dataclass
class Notification:
    """A timed notification message."""
    text: str
    duration: float
    elapsed: float = 0.0
    color: tuple = (255, 255, 255)
    icon: Optional[str] = None


class NotificationOverlay(Overlay):
    """Displays temporary notifications."""
    
    def __init__(self):
        super().__init__(OverlayPriority.NOTIFICATION)
        self._notifications: List[Notification] = []
        self._max_visible = 5
    
    def push(
        self,
        text: str,
        duration: float = 3.0,
        color: tuple = (255, 255, 255),
        icon: Optional[str] = None
    ) -> None:
        """Push a notification."""
        self._notifications.append(Notification(
            text=text,
            duration=duration,
            color=color,
            icon=icon,
        ))
        
        # Limit queue size
        while len(self._notifications) > self._max_visible * 2:
            self._notifications.pop(0)
    
    def update(self, dt: float) -> None:
        """Update notifications."""
        for notif in self._notifications[:]:
            notif.elapsed += dt
            if notif.elapsed >= notif.duration:
                self._notifications.remove(notif)
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw notifications."""
        if not self._notifications:
            return
        
        font = pygame.font.Font(None, 24)
        y = 80
        
        for notif in self._notifications[:self._max_visible]:
            # Calculate fade
            fade_in = min(1.0, notif.elapsed / 0.3)
            fade_out = min(1.0, (notif.duration - notif.elapsed) / 0.5)
            alpha = min(fade_in, fade_out)
            
            # Draw background
            text_surface = font.render(notif.text, True, notif.color)
            text_width = text_surface.get_width()
            
            bg_rect = pygame.Rect(
                screen.get_width() - text_width - 30,
                y - 5,
                text_width + 20,
                30
            )
            
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            bg_surface.fill((20, 20, 30, int(180 * alpha)))
            screen.blit(bg_surface, bg_rect.topleft)
            
            # Draw border
            border_color = tuple(int(c * alpha) for c in notif.color)
            pygame.draw.rect(screen, border_color, bg_rect, 1)
            
            # Draw text
            text_alpha_surface = pygame.Surface(text_surface.get_size(), pygame.SRCALPHA)
            text_alpha_surface.blit(text_surface, (0, 0))
            text_alpha_surface.set_alpha(int(255 * alpha))
            screen.blit(text_alpha_surface, (bg_rect.x + 10, y))
            
            y += 35


class OverlayManager:
    """Manages multiple UI overlays."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self._overlays: Dict[str, Overlay] = {}
        self._sorted_overlays: List[Overlay] = []
        
        # Add default overlays
        self.notifications = NotificationOverlay()
        self.add("notifications", self.notifications)
    
    def add(self, name: str, overlay: Overlay) -> None:
        """Add an overlay."""
        self._overlays[name] = overlay
        self._sort_overlays()
    
    def remove(self, name: str) -> None:
        """Remove an overlay."""
        if name in self._overlays:
            del self._overlays[name]
            self._sort_overlays()
    
    def get(self, name: str) -> Optional[Overlay]:
        """Get an overlay by name."""
        return self._overlays.get(name)
    
    def _sort_overlays(self) -> None:
        """Sort overlays by priority."""
        self._sorted_overlays = sorted(
            self._overlays.values(),
            key=lambda o: o.priority
        )
    
    def update(self, dt: float) -> None:
        """Update all overlays."""
        for overlay in self._sorted_overlays:
            if overlay.visible:
                overlay.update(dt)
    
    def draw(self) -> None:
        """Draw all overlays."""
        for overlay in self._sorted_overlays:
            if overlay.visible:
                overlay.draw(self.screen)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle event through overlays (top to bottom). Returns True if consumed."""
        for overlay in reversed(self._sorted_overlays):
            if overlay.visible and overlay.handle_event(event):
                return True
        return False
    
    def should_block_game(self) -> bool:
        """Check if any overlay should block game updates."""
        return any(
            o.visible and o.blocks_game
            for o in self._sorted_overlays
        )
    
    def notify(self, text: str, duration: float = 3.0, color: tuple = (255, 255, 255)) -> None:
        """Shortcut to push a notification."""
        self.notifications.push(text, duration, color)
