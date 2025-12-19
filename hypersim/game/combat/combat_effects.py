"""Combat Visual Effects - Particles, animations, and feedback for dimensional combat.

This module handles all visual effects during combat:
- Hit/damage effects
- Perception shift animations
- Transcendence activation
- Bullet trail effects
- Dimension transition effects
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Tuple

import pygame

from .dimensional_combat import PerceptionState, CombatDimension


class EffectType(Enum):
    """Types of combat effects."""
    PARTICLE = auto()
    FLASH = auto()
    SHAKE = auto()
    TEXT_POPUP = auto()
    TRAIL = auto()
    RING = auto()
    DISTORTION = auto()


@dataclass
class Particle:
    """A single particle for visual effects."""
    x: float
    y: float
    velocity_x: float
    velocity_y: float
    
    color: Tuple[int, int, int] = (255, 255, 255)
    size: float = 4.0
    lifetime: float = 1.0
    age: float = 0.0
    
    gravity: float = 0.0
    friction: float = 0.98
    fade: bool = True
    shrink: bool = True
    
    @property
    def alive(self) -> bool:
        return self.age < self.lifetime
    
    @property
    def alpha(self) -> int:
        if not self.fade:
            return 255
        return int(255 * (1 - self.age / self.lifetime))
    
    @property
    def current_size(self) -> float:
        if not self.shrink:
            return self.size
        return self.size * (1 - self.age / self.lifetime * 0.7)
    
    def update(self, dt: float) -> None:
        self.age += dt
        self.velocity_x *= self.friction
        self.velocity_y *= self.friction
        self.velocity_y += self.gravity * dt
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
    
    def draw(self, screen: pygame.Surface) -> None:
        if not self.alive:
            return
        
        size = max(1, int(self.current_size))
        alpha = self.alpha
        
        if alpha < 255:
            surf = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, alpha), (size + 1, size + 1), size)
            screen.blit(surf, (int(self.x - size - 1), int(self.y - size - 1)))
        else:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)


@dataclass
class TextPopup:
    """Floating text popup (damage numbers, etc)."""
    x: float
    y: float
    text: str
    color: Tuple[int, int, int] = (255, 255, 255)
    
    velocity_y: float = -50.0
    lifetime: float = 1.0
    age: float = 0.0
    font_size: int = 24
    
    @property
    def alive(self) -> bool:
        return self.age < self.lifetime
    
    def update(self, dt: float) -> None:
        self.age += dt
        self.y += self.velocity_y * dt
        self.velocity_y *= 0.95
    
    def draw(self, screen: pygame.Surface) -> None:
        if not self.alive:
            return
        
        alpha = int(255 * (1 - self.age / self.lifetime))
        font = pygame.font.Font(None, self.font_size)
        text_surf = font.render(self.text, True, self.color)
        
        # Create alpha surface
        alpha_surf = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
        alpha_surf.blit(text_surf, (0, 0))
        alpha_surf.set_alpha(alpha)
        
        screen.blit(alpha_surf, (int(self.x - text_surf.get_width() / 2), int(self.y)))


@dataclass
class ScreenShake:
    """Screen shake effect."""
    intensity: float = 10.0
    duration: float = 0.3
    elapsed: float = 0.0
    
    offset_x: float = 0.0
    offset_y: float = 0.0
    
    @property
    def active(self) -> bool:
        return self.elapsed < self.duration
    
    def update(self, dt: float) -> None:
        self.elapsed += dt
        if self.active:
            decay = 1 - self.elapsed / self.duration
            self.offset_x = random.uniform(-1, 1) * self.intensity * decay
            self.offset_y = random.uniform(-1, 1) * self.intensity * decay
        else:
            self.offset_x = 0
            self.offset_y = 0


@dataclass
class ScreenFlash:
    """Full screen flash effect."""
    color: Tuple[int, int, int] = (255, 255, 255)
    duration: float = 0.2
    elapsed: float = 0.0
    max_alpha: int = 200
    
    @property
    def active(self) -> bool:
        return self.elapsed < self.duration
    
    @property
    def alpha(self) -> int:
        if not self.active:
            return 0
        return int(self.max_alpha * (1 - self.elapsed / self.duration))
    
    def update(self, dt: float) -> None:
        self.elapsed += dt
    
    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
        
        flash_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        flash_surf.fill((*self.color, self.alpha))
        screen.blit(flash_surf, (0, 0))


@dataclass
class RingEffect:
    """Expanding ring effect."""
    x: float
    y: float
    color: Tuple[int, int, int] = (255, 255, 255)
    
    start_radius: float = 10.0
    end_radius: float = 100.0
    duration: float = 0.5
    elapsed: float = 0.0
    thickness: int = 3
    
    @property
    def active(self) -> bool:
        return self.elapsed < self.duration
    
    @property
    def radius(self) -> float:
        t = self.elapsed / self.duration
        return self.start_radius + (self.end_radius - self.start_radius) * t
    
    @property
    def alpha(self) -> int:
        return int(255 * (1 - self.elapsed / self.duration))
    
    def update(self, dt: float) -> None:
        self.elapsed += dt
    
    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return
        
        radius = int(self.radius)
        surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, self.alpha), 
                          (radius + 2, radius + 2), radius, self.thickness)
        screen.blit(surf, (int(self.x - radius - 2), int(self.y - radius - 2)))


@dataclass
class TrailSegment:
    """A single segment of a trail effect."""
    x: float
    y: float
    age: float = 0.0
    max_age: float = 0.3


class TrailEffect:
    """Trail following an object."""
    
    def __init__(self, color: Tuple[int, int, int] = (255, 255, 255), 
                 max_length: int = 15, segment_life: float = 0.3):
        self.color = color
        self.max_length = max_length
        self.segment_life = segment_life
        self.segments: List[TrailSegment] = []
    
    def add_point(self, x: float, y: float) -> None:
        self.segments.append(TrailSegment(x, y, max_age=self.segment_life))
        if len(self.segments) > self.max_length:
            self.segments.pop(0)
    
    def update(self, dt: float) -> None:
        for seg in self.segments:
            seg.age += dt
        self.segments = [s for s in self.segments if s.age < s.max_age]
    
    def draw(self, screen: pygame.Surface) -> None:
        if len(self.segments) < 2:
            return
        
        for i in range(1, len(self.segments)):
            seg = self.segments[i]
            prev = self.segments[i - 1]
            
            alpha = int(255 * (1 - seg.age / seg.max_age) * (i / len(self.segments)))
            thickness = max(1, int(3 * (i / len(self.segments))))
            
            surf = pygame.Surface((abs(int(seg.x - prev.x)) + 10, 
                                  abs(int(seg.y - prev.y)) + 10), pygame.SRCALPHA)
            # Draw on main screen directly for simplicity
            pygame.draw.line(screen, (*self.color, min(255, alpha)), 
                           (int(prev.x), int(prev.y)), (int(seg.x), int(seg.y)), thickness)


class CombatEffectsManager:
    """Manages all combat visual effects."""
    
    def __init__(self):
        self.particles: List[Particle] = []
        self.text_popups: List[TextPopup] = []
        self.rings: List[RingEffect] = []
        self.trails: dict[str, TrailEffect] = {}
        
        self.screen_shake: Optional[ScreenShake] = None
        self.screen_flash: Optional[ScreenFlash] = None
        
        # Perception colors
        self.perception_colors = {
            PerceptionState.POINT: (100, 100, 255),
            PerceptionState.LINE: (100, 200, 255),
            PerceptionState.PLANE: (255, 255, 255),
            PerceptionState.VOLUME: (200, 100, 255),
            PerceptionState.HYPER: (255, 200, 100),
        }
        
        # Dimension colors
        self.dimension_colors = {
            CombatDimension.ONE_D: (100, 200, 255),
            CombatDimension.TWO_D: (255, 255, 255),
            CombatDimension.THREE_D: (200, 150, 255),
            CombatDimension.FOUR_D: (255, 200, 100),
        }
    
    def update(self, dt: float) -> None:
        """Update all effects."""
        # Update particles
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]
        
        # Update text popups
        for t in self.text_popups:
            t.update(dt)
        self.text_popups = [t for t in self.text_popups if t.alive]
        
        # Update rings
        for r in self.rings:
            r.update(dt)
        self.rings = [r for r in self.rings if r.active]
        
        # Update trails
        for trail in self.trails.values():
            trail.update(dt)
        
        # Update screen effects
        if self.screen_shake:
            self.screen_shake.update(dt)
            if not self.screen_shake.active:
                self.screen_shake = None
        
        if self.screen_flash:
            self.screen_flash.update(dt)
            if not self.screen_flash.active:
                self.screen_flash = None
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw all effects."""
        # Draw trails first (behind everything)
        for trail in self.trails.values():
            trail.draw(screen)
        
        # Draw particles
        for p in self.particles:
            p.draw(screen)
        
        # Draw rings
        for r in self.rings:
            r.draw(screen)
        
        # Draw text popups
        for t in self.text_popups:
            t.draw(screen)
        
        # Draw screen flash last
        if self.screen_flash:
            self.screen_flash.draw(screen)
    
    def get_screen_offset(self) -> Tuple[float, float]:
        """Get current screen shake offset."""
        if self.screen_shake and self.screen_shake.active:
            return self.screen_shake.offset_x, self.screen_shake.offset_y
        return 0.0, 0.0
    
    # === EFFECT SPAWNERS ===
    
    def spawn_damage_particles(self, x: float, y: float, damage: int) -> None:
        """Spawn particles when player takes damage."""
        num_particles = min(20, 5 + damage)
        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 250)
            self.particles.append(Particle(
                x=x + random.uniform(-5, 5),
                y=y + random.uniform(-5, 5),
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
                color=(255, 50, 50),
                size=random.uniform(2, 5),
                lifetime=random.uniform(0.3, 0.6),
                gravity=200,
            ))
        
        # Add shake
        self.screen_shake = ScreenShake(intensity=min(15, 5 + damage * 0.5), duration=0.2)
        
        # Add flash
        self.screen_flash = ScreenFlash(color=(255, 0, 0), duration=0.1, max_alpha=100)
    
    def spawn_damage_number(self, x: float, y: float, damage: int, is_critical: bool = False) -> None:
        """Spawn floating damage number."""
        color = (255, 255, 0) if is_critical else (255, 100, 100)
        text = f"-{damage}" if not is_critical else f"-{damage}!"
        font_size = 28 if is_critical else 22
        
        self.text_popups.append(TextPopup(
            x=x + random.uniform(-10, 10),
            y=y - 20,
            text=text,
            color=color,
            font_size=font_size,
        ))
    
    def spawn_heal_effect(self, x: float, y: float, amount: int) -> None:
        """Spawn healing effect."""
        # Green particles rising
        for _ in range(10):
            self.particles.append(Particle(
                x=x + random.uniform(-15, 15),
                y=y + random.uniform(-10, 10),
                velocity_x=random.uniform(-20, 20),
                velocity_y=random.uniform(-80, -40),
                color=(100, 255, 100),
                size=random.uniform(3, 6),
                lifetime=0.8,
                gravity=-50,
            ))
        
        # Heal number
        self.text_popups.append(TextPopup(
            x=x,
            y=y - 20,
            text=f"+{amount}",
            color=(100, 255, 100),
            font_size=24,
        ))
    
    def spawn_perception_shift_effect(self, x: float, y: float, 
                                      from_state: PerceptionState,
                                      to_state: PerceptionState) -> None:
        """Spawn effect when perception shifts."""
        from_color = self.perception_colors.get(from_state, (255, 255, 255))
        to_color = self.perception_colors.get(to_state, (255, 255, 255))
        
        # Outward ring of old perception
        self.rings.append(RingEffect(
            x=x, y=y,
            color=from_color,
            start_radius=10,
            end_radius=60,
            duration=0.4,
        ))
        
        # Inward particles of new perception
        for i in range(16):
            angle = 2 * math.pi * i / 16
            dist = 50
            self.particles.append(Particle(
                x=x + math.cos(angle) * dist,
                y=y + math.sin(angle) * dist,
                velocity_x=-math.cos(angle) * 150,
                velocity_y=-math.sin(angle) * 150,
                color=to_color,
                size=4,
                lifetime=0.35,
            ))
        
        # Brief flash
        self.screen_flash = ScreenFlash(color=to_color, duration=0.15, max_alpha=80)
    
    def spawn_transcendence_effect(self, x: float, y: float) -> None:
        """Spawn effect when transcendence activates."""
        gold = (255, 200, 100)
        
        # Multiple expanding rings
        for i in range(3):
            self.rings.append(RingEffect(
                x=x, y=y,
                color=gold,
                start_radius=5 + i * 10,
                end_radius=120 + i * 30,
                duration=0.6 + i * 0.1,
                thickness=4 - i,
            ))
        
        # Burst of particles
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(150, 300)
            self.particles.append(Particle(
                x=x,
                y=y,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
                color=gold,
                size=random.uniform(3, 7),
                lifetime=random.uniform(0.5, 1.0),
            ))
        
        # Big flash
        self.screen_flash = ScreenFlash(color=gold, duration=0.3, max_alpha=180)
        self.screen_shake = ScreenShake(intensity=8, duration=0.3)
    
    def spawn_graze_effect(self, x: float, y: float) -> None:
        """Spawn effect for grazing a bullet."""
        # Small sparkle
        for _ in range(5):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 80)
            self.particles.append(Particle(
                x=x,
                y=y,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
                color=(200, 200, 255),
                size=2,
                lifetime=0.2,
            ))
    
    def spawn_dimension_transition(self, screen_width: int, screen_height: int,
                                   from_dim: CombatDimension,
                                   to_dim: CombatDimension) -> None:
        """Spawn effect when combat dimension changes."""
        to_color = self.dimension_colors.get(to_dim, (255, 255, 255))
        
        # Lines sweeping across screen
        for i in range(20):
            start_x = -50
            y = screen_height * i / 20
            self.particles.append(Particle(
                x=start_x,
                y=y,
                velocity_x=random.uniform(400, 600),
                velocity_y=0,
                color=to_color,
                size=3,
                lifetime=1.0,
                fade=True,
                shrink=False,
            ))
        
        self.screen_flash = ScreenFlash(color=to_color, duration=0.4, max_alpha=150)
    
    def spawn_enemy_hit_effect(self, x: float, y: float, damage: int) -> None:
        """Spawn effect when enemy is hit."""
        # White flash particles
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(80, 150)
            self.particles.append(Particle(
                x=x + random.uniform(-20, 20),
                y=y + random.uniform(-20, 20),
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
                color=(255, 255, 255),
                size=random.uniform(2, 4),
                lifetime=0.3,
            ))
        
        # Damage number
        self.text_popups.append(TextPopup(
            x=x,
            y=y - 30,
            text=str(damage),
            color=(255, 255, 255),
            font_size=26,
        ))
    
    def spawn_bullet_destroy_effect(self, x: float, y: float, 
                                    color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        """Spawn effect when bullet is destroyed."""
        for _ in range(6):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(40, 80)
            self.particles.append(Particle(
                x=x,
                y=y,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
                color=color,
                size=2,
                lifetime=0.2,
            ))
    
    def update_soul_trail(self, soul_id: str, x: float, y: float, 
                          color: Tuple[int, int, int]) -> None:
        """Update trail for a soul."""
        if soul_id not in self.trails:
            self.trails[soul_id] = TrailEffect(color=color)
        
        self.trails[soul_id].color = color
        self.trails[soul_id].add_point(x, y)
    
    def clear_all(self) -> None:
        """Clear all effects."""
        self.particles.clear()
        self.text_popups.clear()
        self.rings.clear()
        self.trails.clear()
        self.screen_shake = None
        self.screen_flash = None


# Singleton for easy access
_effects_manager: Optional[CombatEffectsManager] = None


def get_effects_manager() -> CombatEffectsManager:
    """Get or create the global effects manager."""
    global _effects_manager
    if _effects_manager is None:
        _effects_manager = CombatEffectsManager()
    return _effects_manager
