"""UI Animation utilities for polished visual effects.

Provides reusable animation components:
- Easing functions
- Tweening system
- Screen transitions
- Particle effects
- Text effects
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple

import pygame


# =============================================================================
# EASING FUNCTIONS
# =============================================================================

class Easing(Enum):
    """Easing function types."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    BOUNCE = "bounce"
    ELASTIC = "elastic"
    BACK = "back"


def ease(t: float, easing: Easing = Easing.LINEAR) -> float:
    """Apply easing function to t (0.0 to 1.0)."""
    t = max(0.0, min(1.0, t))
    
    if easing == Easing.LINEAR:
        return t
    
    elif easing == Easing.EASE_IN:
        return t * t * t
    
    elif easing == Easing.EASE_OUT:
        return 1 - (1 - t) ** 3
    
    elif easing == Easing.EASE_IN_OUT:
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - ((-2 * t + 2) ** 3) / 2
    
    elif easing == Easing.BOUNCE:
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375
    
    elif easing == Easing.ELASTIC:
        if t == 0 or t == 1:
            return t
        return -(2 ** (10 * t - 10)) * math.sin((t * 10 - 10.75) * (2 * math.pi) / 3)
    
    elif easing == Easing.BACK:
        c1 = 1.70158
        c3 = c1 + 1
        return c3 * t * t * t - c1 * t * t
    
    return t


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b."""
    return a + (b - a) * t


def lerp_color(c1: Tuple[int, ...], c2: Tuple[int, ...], t: float) -> Tuple[int, ...]:
    """Lerp between two colors."""
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


# =============================================================================
# TWEEN SYSTEM
# =============================================================================

@dataclass
class Tween:
    """A single tween animation."""
    start_value: float
    end_value: float
    duration: float
    easing: Easing = Easing.EASE_OUT
    delay: float = 0.0
    
    # State
    elapsed: float = 0.0
    started: bool = False
    finished: bool = False
    
    # Callbacks
    on_complete: Optional[Callable] = None
    
    @property
    def value(self) -> float:
        """Get current tweened value."""
        if self.elapsed < self.delay:
            return self.start_value
        
        t = (self.elapsed - self.delay) / self.duration if self.duration > 0 else 1.0
        t = min(1.0, t)
        eased_t = ease(t, self.easing)
        return lerp(self.start_value, self.end_value, eased_t)
    
    @property
    def progress(self) -> float:
        """Get progress (0.0 to 1.0)."""
        if self.elapsed < self.delay:
            return 0.0
        return min(1.0, (self.elapsed - self.delay) / self.duration) if self.duration > 0 else 1.0
    
    def update(self, dt: float) -> bool:
        """Update tween. Returns True if still running."""
        if self.finished:
            return False
        
        self.elapsed += dt
        self.started = self.elapsed >= self.delay
        
        if self.elapsed >= self.delay + self.duration:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return False
        
        return True


class TweenManager:
    """Manages multiple tweens."""
    
    def __init__(self):
        self.tweens: Dict[str, Tween] = {}
    
    def add(self, name: str, tween: Tween) -> None:
        """Add a tween."""
        self.tweens[name] = tween
    
    def get(self, name: str) -> Optional[float]:
        """Get a tween's current value."""
        tween = self.tweens.get(name)
        return tween.value if tween else None
    
    def is_running(self, name: str) -> bool:
        """Check if a tween is running."""
        tween = self.tweens.get(name)
        return tween is not None and not tween.finished
    
    def update(self, dt: float) -> None:
        """Update all tweens."""
        finished = []
        for name, tween in self.tweens.items():
            if not tween.update(dt):
                finished.append(name)
        
        # Clean up finished tweens
        for name in finished:
            del self.tweens[name]


# =============================================================================
# SCREEN TRANSITIONS
# =============================================================================

class TransitionType(Enum):
    """Types of screen transitions."""
    FADE = "fade"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    WIPE = "wipe"
    DIMENSIONAL = "dimensional"  # Special 4D-themed transition


@dataclass
class ScreenTransition:
    """A screen transition effect."""
    transition_type: TransitionType
    duration: float = 0.5
    color: Tuple[int, int, int] = (0, 0, 0)
    easing: Easing = Easing.EASE_IN_OUT
    
    # State
    progress: float = 0.0
    phase: str = "in"  # "in", "hold", "out"
    finished: bool = False
    
    # Callback when transition reaches middle
    on_midpoint: Optional[Callable] = None
    _midpoint_called: bool = False
    
    def update(self, dt: float) -> None:
        """Update transition."""
        if self.finished:
            return
        
        self.progress += dt / self.duration
        
        if self.progress >= 0.5 and not self._midpoint_called:
            self._midpoint_called = True
            self.phase = "out"
            if self.on_midpoint:
                self.on_midpoint()
        
        if self.progress >= 1.0:
            self.progress = 1.0
            self.finished = True
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw transition effect."""
        if self.finished:
            return
        
        width, height = screen.get_size()
        
        # Calculate alpha/position based on phase
        if self.phase == "in":
            t = ease(self.progress * 2, self.easing)
        else:
            t = ease(1 - (self.progress - 0.5) * 2, self.easing)
        
        if self.transition_type == TransitionType.FADE:
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            alpha = int(255 * t)
            overlay.fill((*self.color, alpha))
            screen.blit(overlay, (0, 0))
        
        elif self.transition_type == TransitionType.SLIDE_LEFT:
            x = int(width * (1 - t))
            pygame.draw.rect(screen, self.color, (x, 0, width, height))
        
        elif self.transition_type == TransitionType.SLIDE_RIGHT:
            x = int(-width * (1 - t))
            pygame.draw.rect(screen, self.color, (x, 0, width, height))
        
        elif self.transition_type == TransitionType.WIPE:
            w = int(width * t)
            pygame.draw.rect(screen, self.color, (0, 0, w, height))
        
        elif self.transition_type == TransitionType.DIMENSIONAL:
            # Cool 4D-themed transition with concentric shapes
            self._draw_dimensional_transition(screen, t)
    
    def _draw_dimensional_transition(self, screen: pygame.Surface, t: float) -> None:
        """Draw special dimensional transition."""
        width, height = screen.get_size()
        center = (width // 2, height // 2)
        max_radius = int(math.sqrt(width**2 + height**2) / 2)
        
        # Draw expanding/contracting circles
        num_rings = 8
        for i in range(num_rings):
            phase = (t + i / num_rings) % 1.0
            radius = int(max_radius * phase)
            if radius > 0:
                alpha = int(255 * (1 - phase))
                color = (*self.color, alpha)
                surf = pygame.Surface((width, height), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, center, radius, 3)
                screen.blit(surf, (0, 0))
        
        # Center fade
        center_alpha = int(255 * t)
        center_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        center_surf.fill((*self.color, center_alpha))
        screen.blit(center_surf, (0, 0))


# =============================================================================
# PARTICLES
# =============================================================================

@dataclass
class Particle:
    """A single particle."""
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    size: float = 4.0
    color: Tuple[int, int, int] = (255, 255, 255)
    alpha: float = 1.0
    lifetime: float = 1.0
    age: float = 0.0
    gravity: float = 0.0
    friction: float = 0.98
    shrink: bool = True
    
    @property
    def alive(self) -> bool:
        return self.age < self.lifetime
    
    def update(self, dt: float) -> None:
        """Update particle."""
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.vx *= self.friction
        self.vy *= self.friction
        
        # Fade and shrink
        life_ratio = 1 - (self.age / self.lifetime)
        self.alpha = life_ratio
        if self.shrink:
            self.size = max(0, self.size * (0.95 + 0.05 * life_ratio))


class ParticleSystem:
    """Manages particle effects."""
    
    def __init__(self, max_particles: int = 500):
        self.particles: List[Particle] = []
        self.max_particles = max_particles
    
    def emit(self, x: float, y: float, count: int = 10, **kwargs) -> None:
        """Emit particles at position."""
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            
            # Add some randomness
            vx = kwargs.get("vx", 0) + random.uniform(-50, 50)
            vy = kwargs.get("vy", 0) + random.uniform(-50, 50)
            size = kwargs.get("size", 4) * random.uniform(0.5, 1.5)
            lifetime = kwargs.get("lifetime", 1.0) * random.uniform(0.8, 1.2)
            
            self.particles.append(Particle(
                x=x + random.uniform(-5, 5),
                y=y + random.uniform(-5, 5),
                vx=vx,
                vy=vy,
                size=size,
                color=kwargs.get("color", (255, 255, 255)),
                lifetime=lifetime,
                gravity=kwargs.get("gravity", 0),
                friction=kwargs.get("friction", 0.98),
            ))
    
    def emit_burst(self, x: float, y: float, count: int = 20, 
                   speed: float = 100, **kwargs) -> None:
        """Emit particles in a burst pattern."""
        for i in range(count):
            angle = (i / count) * 2 * math.pi
            vx = math.cos(angle) * speed * random.uniform(0.5, 1.5)
            vy = math.sin(angle) * speed * random.uniform(0.5, 1.5)
            
            self.particles.append(Particle(
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                **kwargs
            ))
    
    def update(self, dt: float) -> None:
        """Update all particles."""
        for particle in self.particles:
            particle.update(dt)
        
        # Remove dead particles
        self.particles = [p for p in self.particles if p.alive]
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw all particles."""
        for particle in self.particles:
            if particle.alpha <= 0:
                continue
            
            color = particle.color
            alpha = int(255 * particle.alpha)
            size = int(particle.size)
            
            if size > 0:
                surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*color, alpha), (size, size), size)
                screen.blit(surf, (int(particle.x - size), int(particle.y - size)))


# =============================================================================
# TEXT EFFECTS
# =============================================================================

class TextEffect(Enum):
    """Text animation effects."""
    NONE = "none"
    WAVE = "wave"
    SHAKE = "shake"
    RAINBOW = "rainbow"
    GLITCH = "glitch"
    TYPEWRITER = "typewriter"


def render_text_with_effect(
    text: str,
    font: pygame.font.Font,
    base_color: Tuple[int, int, int],
    effect: TextEffect,
    time: float,
    **kwargs
) -> pygame.Surface:
    """Render text with animated effect."""
    
    if effect == TextEffect.NONE:
        return font.render(text, True, base_color)
    
    # Calculate total width needed
    char_surfaces = []
    total_width = 0
    max_height = font.get_linesize()
    
    for i, char in enumerate(text):
        char_surf = font.render(char, True, base_color)
        char_surfaces.append((char, char_surf, i))
        total_width += char_surf.get_width()
    
    # Create output surface with extra space for effects
    padding = 20
    result = pygame.Surface((total_width + padding, max_height + padding), pygame.SRCALPHA)
    
    x = padding // 2
    for char, char_surf, i in char_surfaces:
        y_offset = 0
        x_offset = 0
        color = base_color
        
        if effect == TextEffect.WAVE:
            amplitude = kwargs.get("amplitude", 5)
            speed = kwargs.get("speed", 5)
            y_offset = int(math.sin(time * speed + i * 0.5) * amplitude)
        
        elif effect == TextEffect.SHAKE:
            intensity = kwargs.get("intensity", 2)
            x_offset = random.randint(-intensity, intensity)
            y_offset = random.randint(-intensity, intensity)
        
        elif effect == TextEffect.RAINBOW:
            hue = (time * 100 + i * 20) % 360
            color = hsv_to_rgb(hue, 0.8, 1.0)
            char_surf = font.render(char, True, color)
        
        elif effect == TextEffect.GLITCH:
            if random.random() < 0.1:
                x_offset = random.randint(-5, 5)
                color = random.choice([(255, 0, 0), (0, 255, 0), (0, 0, 255)])
                char_surf = font.render(char, True, color)
        
        result.blit(char_surf, (x + x_offset, padding // 2 + y_offset))
        x += char_surf.get_width()
    
    return result


def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
    """Convert HSV to RGB."""
    h = h / 360
    i = int(h * 6)
    f = h * 6 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    
    r, g, b = [
        (v, t, p),
        (q, v, p),
        (p, v, t),
        (p, q, v),
        (t, p, v),
        (v, p, q),
    ][i % 6]
    
    return (int(r * 255), int(g * 255), int(b * 255))


# =============================================================================
# CONVENIENCE
# =============================================================================

# Global particle system
_particles: Optional[ParticleSystem] = None


def get_particles() -> ParticleSystem:
    """Get global particle system."""
    global _particles
    if _particles is None:
        _particles = ParticleSystem()
    return _particles


def create_transition(
    transition_type: TransitionType = TransitionType.FADE,
    duration: float = 0.5,
    color: Tuple[int, int, int] = (0, 0, 0),
    on_midpoint: Optional[Callable] = None
) -> ScreenTransition:
    """Create a screen transition."""
    return ScreenTransition(
        transition_type=transition_type,
        duration=duration,
        color=color,
        on_midpoint=on_midpoint,
    )
