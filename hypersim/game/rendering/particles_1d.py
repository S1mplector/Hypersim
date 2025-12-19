"""1D Particle System - Unique visual effects for Line entities.

Each entity type has distinct particle behaviors:
- Point Spirits: Soft, floating wisps that fade in/out
- Forward Sentinels: Sharp, aggressive spikes pointing forward
- Void Echoes: Dark, swirling particles that phase in/out
- Line Walkers: Confused, jittery particles moving erratically
- The First Point: Majestic purple aura with healing capabilities
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

import pygame
import numpy as np

if TYPE_CHECKING:
    from hypersim.game.ecs.entity import Entity


class ParticleType(Enum):
    """Types of particles for different entities."""
    POINT_SPIRIT = auto()      # Gentle floating wisps
    FORWARD_SENTINEL = auto()  # Aggressive forward spikes
    VOID_ECHO = auto()         # Phasing dark particles
    LINE_WALKER = auto()       # Confused jittery motion
    FIRST_POINT = auto()       # Majestic purple aura
    HEALING = auto()           # Flowing healing particles
    GENERIC = auto()           # Default particle


@dataclass
class Particle:
    """A single particle."""
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    size: float = 3.0
    alpha: float = 1.0
    life: float = 2.0
    max_life: float = 2.0
    color: Tuple[int, int, int] = (255, 255, 255)
    particle_type: ParticleType = ParticleType.GENERIC
    
    # Special properties
    phase: float = 0.0  # For oscillation effects
    target_x: Optional[float] = None  # For homing particles
    target_y: Optional[float] = None


class ParticleEmitter:
    """Emits particles for a specific entity."""
    
    def __init__(
        self,
        entity_id: str,
        particle_type: ParticleType,
        base_x: float,
        base_y: float,
        color: Tuple[int, int, int] = (255, 255, 255),
    ):
        self.entity_id = entity_id
        self.particle_type = particle_type
        self.base_x = base_x
        self.base_y = base_y
        self.color = color
        self.particles: List[Particle] = []
        self.emit_timer = 0.0
        self.emit_rate = 0.1  # Seconds between emissions
        self._time = 0.0
        
        # Configure based on particle type
        self._configure_emitter()
    
    def _configure_emitter(self) -> None:
        """Configure emitter based on particle type."""
        if self.particle_type == ParticleType.POINT_SPIRIT:
            self.emit_rate = 0.15
            self.max_particles = 8
        elif self.particle_type == ParticleType.FORWARD_SENTINEL:
            self.emit_rate = 0.08
            self.max_particles = 12
        elif self.particle_type == ParticleType.VOID_ECHO:
            self.emit_rate = 0.12
            self.max_particles = 10
        elif self.particle_type == ParticleType.LINE_WALKER:
            self.emit_rate = 0.1
            self.max_particles = 6
        elif self.particle_type == ParticleType.FIRST_POINT:
            self.emit_rate = 0.08
            self.max_particles = 20
        elif self.particle_type == ParticleType.HEALING:
            self.emit_rate = 0.05
            self.max_particles = 15
        else:
            self.emit_rate = 0.2
            self.max_particles = 5
    
    def update(self, dt: float, new_x: Optional[float] = None, new_y: Optional[float] = None) -> None:
        """Update emitter and all particles."""
        self._time += dt
        
        # Update position if provided
        if new_x is not None:
            self.base_x = new_x
        if new_y is not None:
            self.base_y = new_y
        
        # Emit new particles
        self.emit_timer += dt
        if self.emit_timer >= self.emit_rate and len(self.particles) < self.max_particles:
            self.emit_timer = 0.0
            self._emit_particle()
        
        # Update existing particles
        for p in self.particles[:]:
            self._update_particle(p, dt)
            p.life -= dt
            if p.life <= 0:
                self.particles.remove(p)
    
    def _emit_particle(self) -> None:
        """Emit a new particle based on type."""
        if self.particle_type == ParticleType.POINT_SPIRIT:
            self._emit_point_spirit()
        elif self.particle_type == ParticleType.FORWARD_SENTINEL:
            self._emit_forward_sentinel()
        elif self.particle_type == ParticleType.VOID_ECHO:
            self._emit_void_echo()
        elif self.particle_type == ParticleType.LINE_WALKER:
            self._emit_line_walker()
        elif self.particle_type == ParticleType.FIRST_POINT:
            self._emit_first_point()
        else:
            self._emit_generic()
    
    def _emit_point_spirit(self) -> None:
        """Emit gentle floating wisps."""
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(5, 15)
        
        self.particles.append(Particle(
            x=self.base_x + math.cos(angle) * distance,
            y=self.base_y + math.sin(angle) * distance,
            vx=random.uniform(-5, 5),
            vy=random.uniform(-15, -5),  # Float upward
            size=random.uniform(2, 4),
            alpha=random.uniform(0.4, 0.8),
            life=random.uniform(1.5, 2.5),
            max_life=2.5,
            color=(
                min(255, self.color[0] + random.randint(-20, 20)),
                min(255, self.color[1] + random.randint(-20, 20)),
                min(255, self.color[2] + random.randint(-10, 10)),
            ),
            particle_type=ParticleType.POINT_SPIRIT,
            phase=random.uniform(0, 2 * math.pi),
        ))
    
    def _emit_forward_sentinel(self) -> None:
        """Emit aggressive forward-pointing spikes."""
        # Spikes pointing in forward direction (positive X)
        self.particles.append(Particle(
            x=self.base_x + random.uniform(5, 15),
            y=self.base_y + random.uniform(-8, 8),
            vx=random.uniform(30, 60),  # Fast forward motion
            vy=random.uniform(-10, 10),
            size=random.uniform(2, 5),
            alpha=random.uniform(0.7, 1.0),
            life=random.uniform(0.3, 0.6),
            max_life=0.6,
            color=(
                min(255, self.color[0] + random.randint(0, 50)),
                max(0, self.color[1] - random.randint(0, 30)),
                max(0, self.color[2] - random.randint(0, 30)),
            ),
            particle_type=ParticleType.FORWARD_SENTINEL,
        ))
    
    def _emit_void_echo(self) -> None:
        """Emit dark, phasing particles."""
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(10, 25)
        
        self.particles.append(Particle(
            x=self.base_x + math.cos(angle) * distance,
            y=self.base_y + math.sin(angle) * distance,
            vx=math.cos(angle) * -10,  # Move toward center
            vy=math.sin(angle) * -10,
            size=random.uniform(3, 6),
            alpha=random.uniform(0.3, 0.6),
            life=random.uniform(1.0, 2.0),
            max_life=2.0,
            color=(
                max(0, self.color[0] - random.randint(30, 60)),
                max(0, self.color[1] - random.randint(20, 40)),
                min(255, self.color[2] + random.randint(0, 30)),
            ),
            particle_type=ParticleType.VOID_ECHO,
            phase=random.uniform(0, 2 * math.pi),
        ))
    
    def _emit_line_walker(self) -> None:
        """Emit confused, jittery particles."""
        self.particles.append(Particle(
            x=self.base_x + random.uniform(-10, 10),
            y=self.base_y + random.uniform(-10, 10),
            vx=random.uniform(-40, 40),  # Erratic motion
            vy=random.uniform(-40, 40),
            size=random.uniform(1, 3),
            alpha=random.uniform(0.5, 0.9),
            life=random.uniform(0.2, 0.5),
            max_life=0.5,
            color=self.color,
            particle_type=ParticleType.LINE_WALKER,
        ))
    
    def _emit_first_point(self) -> None:
        """Emit majestic purple aura particles."""
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(30, 70)
        
        self.particles.append(Particle(
            x=self.base_x + math.cos(angle) * distance,
            y=self.base_y + math.sin(angle) * distance,
            vx=math.cos(angle) * -12,  # Slowly move toward center
            vy=math.sin(angle) * -12,
            size=random.uniform(2, 5),
            alpha=random.uniform(0.4, 0.7),
            life=random.uniform(2.0, 3.5),
            max_life=3.5,
            color=(
                180 + random.randint(-20, 20),
                100 + random.randint(-20, 20),
                255,
            ),
            particle_type=ParticleType.FIRST_POINT,
            phase=random.uniform(0, 2 * math.pi),
        ))
    
    def _emit_generic(self) -> None:
        """Emit generic particles."""
        self.particles.append(Particle(
            x=self.base_x + random.uniform(-5, 5),
            y=self.base_y + random.uniform(-5, 5),
            vx=random.uniform(-10, 10),
            vy=random.uniform(-10, 10),
            size=random.uniform(2, 4),
            alpha=0.7,
            life=1.0,
            max_life=1.0,
            color=self.color,
        ))
    
    def _update_particle(self, p: Particle, dt: float) -> None:
        """Update a single particle based on its type."""
        # Update position
        p.x += p.vx * dt
        p.y += p.vy * dt
        
        # Type-specific behavior
        if p.particle_type == ParticleType.POINT_SPIRIT:
            # Gentle floating oscillation
            p.phase += dt * 3
            p.x += math.sin(p.phase) * 0.5
            p.alpha = 0.6 * (p.life / p.max_life) * (0.7 + 0.3 * math.sin(p.phase * 2))
            
        elif p.particle_type == ParticleType.FORWARD_SENTINEL:
            # Accelerate forward, fade quickly
            p.vx *= 1.05
            p.alpha = p.life / p.max_life
            p.size *= 0.95  # Shrink
            
        elif p.particle_type == ParticleType.VOID_ECHO:
            # Phase in and out of existence
            p.phase += dt * 4
            visibility = 0.5 + 0.5 * math.sin(p.phase)
            p.alpha = 0.5 * (p.life / p.max_life) * visibility
            
        elif p.particle_type == ParticleType.LINE_WALKER:
            # Sudden direction changes
            if random.random() < 0.1:
                p.vx = random.uniform(-40, 40)
                p.vy = random.uniform(-40, 40)
            p.alpha = p.life / p.max_life
            
        elif p.particle_type == ParticleType.FIRST_POINT:
            # Majestic spiral motion
            p.phase += dt * 2
            spiral = math.sin(p.phase) * 5
            p.x += spiral * dt
            p.alpha = 0.5 * (p.life / p.max_life)
            
        elif p.particle_type == ParticleType.HEALING:
            # Move toward target
            if p.target_x is not None and p.target_y is not None:
                dx = p.target_x - p.x
                dy = p.target_y - p.y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > 1:
                    speed = 150 + (1 - p.life / p.max_life) * 100  # Speed up as life decreases
                    p.vx = (dx / dist) * speed
                    p.vy = (dy / dist) * speed
            p.alpha = 0.8 * (p.life / p.max_life)
        else:
            # Generic fade
            p.alpha = p.life / p.max_life
    
    def emit_healing_particles(self, target_x: float, target_y: float, count: int = 8) -> None:
        """Emit healing particles that flow toward a target."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(20, 50)
            
            self.particles.append(Particle(
                x=self.base_x + math.cos(angle) * distance,
                y=self.base_y + math.sin(angle) * distance,
                vx=0,
                vy=0,
                size=random.uniform(3, 6),
                alpha=0.9,
                life=random.uniform(0.8, 1.5),
                max_life=1.5,
                color=(
                    100 + random.randint(0, 50),
                    220 + random.randint(0, 35),
                    100 + random.randint(0, 50),
                ),
                particle_type=ParticleType.HEALING,
                target_x=target_x,
                target_y=target_y,
            ))


class ParticleSystem1D:
    """Manages all particle emitters for 1D entities."""
    
    def __init__(self, screen: pygame.Surface, line_y: int):
        self.screen = screen
        self.line_y = line_y
        self.emitters: Dict[str, ParticleEmitter] = {}
        
        # Healing state
        self._healing_active = False
        self._healing_timer = 0.0
        self._healing_cooldown = 3.0  # Seconds between heals
        self._last_heal_time = -self._healing_cooldown
    
    def get_or_create_emitter(
        self,
        entity_id: str,
        particle_type: ParticleType,
        screen_x: float,
        color: Tuple[int, int, int] = (255, 255, 255),
    ) -> ParticleEmitter:
        """Get existing emitter or create a new one."""
        if entity_id not in self.emitters:
            self.emitters[entity_id] = ParticleEmitter(
                entity_id=entity_id,
                particle_type=particle_type,
                base_x=screen_x,
                base_y=self.line_y,
                color=color,
            )
        return self.emitters[entity_id]
    
    def update(self, dt: float) -> None:
        """Update all emitters."""
        self._healing_timer += dt
        
        for emitter in list(self.emitters.values()):
            emitter.update(dt)
    
    def update_emitter_position(self, entity_id: str, screen_x: float) -> None:
        """Update an emitter's position."""
        if entity_id in self.emitters:
            self.emitters[entity_id].base_x = screen_x
    
    def remove_emitter(self, entity_id: str) -> None:
        """Remove an emitter."""
        if entity_id in self.emitters:
            del self.emitters[entity_id]
    
    def trigger_healing(
        self,
        source_id: str,
        target_screen_x: float,
        particle_count: int = 10,
    ) -> bool:
        """Trigger healing particles from source to target.
        
        Returns True if healing was triggered, False if on cooldown.
        """
        if self._healing_timer - self._last_heal_time < self._healing_cooldown:
            return False
        
        if source_id not in self.emitters:
            return False
        
        emitter = self.emitters[source_id]
        emitter.emit_healing_particles(target_screen_x, self.line_y, particle_count)
        self._last_heal_time = self._healing_timer
        self._healing_active = True
        
        return True
    
    def draw(self) -> None:
        """Draw all particles."""
        for emitter in self.emitters.values():
            for p in emitter.particles:
                if p.alpha <= 0:
                    continue
                
                color = (*p.color, int(255 * min(1.0, p.alpha)))
                size = int(max(1, p.size))
                
                # Create surface for particle
                if p.particle_type == ParticleType.FORWARD_SENTINEL:
                    # Draw as elongated spike
                    self._draw_spike(p, color)
                elif p.particle_type == ParticleType.VOID_ECHO:
                    # Draw with fuzzy edges
                    self._draw_void_particle(p, color)
                elif p.particle_type == ParticleType.HEALING:
                    # Draw as glowing orb
                    self._draw_healing_particle(p, color)
                else:
                    # Default circular particle
                    self._draw_circle_particle(p, color, size)
    
    def _draw_circle_particle(self, p: Particle, color: tuple, size: int) -> None:
        """Draw a circular particle with glow."""
        # Outer glow
        glow_size = size * 2
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        glow_color = (*color[:3], int(color[3] * 0.3))
        pygame.draw.circle(glow_surf, glow_color, (glow_size, glow_size), glow_size)
        self.screen.blit(glow_surf, (int(p.x) - glow_size, int(p.y) - glow_size))
        
        # Core
        core_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(core_surf, color, (size, size), size)
        self.screen.blit(core_surf, (int(p.x) - size, int(p.y) - size))
    
    def _draw_spike(self, p: Particle, color: tuple) -> None:
        """Draw a spike-shaped particle."""
        length = int(p.size * 3)
        width = int(p.size)
        
        # Calculate spike points
        points = [
            (int(p.x) - width, int(p.y) - width // 2),
            (int(p.x) + length, int(p.y)),
            (int(p.x) - width, int(p.y) + width // 2),
        ]
        
        spike_surf = pygame.Surface((length + width * 2, width * 2), pygame.SRCALPHA)
        adjusted_points = [
            (pt[0] - (int(p.x) - width), pt[1] - (int(p.y) - width // 2))
            for pt in points
        ]
        pygame.draw.polygon(spike_surf, color, adjusted_points)
        self.screen.blit(spike_surf, (int(p.x) - width, int(p.y) - width // 2))
    
    def _draw_void_particle(self, p: Particle, color: tuple) -> None:
        """Draw a void particle with phasing effect."""
        size = int(p.size)
        
        # Multiple overlapping circles for fuzzy effect
        for i in range(3):
            offset = i * 2
            alpha_mod = 1.0 - (i * 0.3)
            layer_color = (*color[:3], int(color[3] * alpha_mod))
            
            surf = pygame.Surface(((size + offset) * 2, (size + offset) * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, layer_color, (size + offset, size + offset), size + offset)
            self.screen.blit(surf, (int(p.x) - size - offset, int(p.y) - size - offset))
    
    def _draw_healing_particle(self, p: Particle, color: tuple) -> None:
        """Draw a healing particle as a glowing orb with trail."""
        size = int(p.size)
        
        # Bright glow
        glow_size = size * 3
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        glow_color = (*color[:3], int(color[3] * 0.4))
        pygame.draw.circle(glow_surf, glow_color, (glow_size, glow_size), glow_size)
        self.screen.blit(glow_surf, (int(p.x) - glow_size, int(p.y) - glow_size))
        
        # Bright core
        core_color = (
            min(255, color[0] + 50),
            min(255, color[1] + 50),
            min(255, color[2] + 50),
            color[3],
        )
        core_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(core_surf, core_color, (size, size), size)
        self.screen.blit(core_surf, (int(p.x) - size, int(p.y) - size))


def get_particle_type_for_entity(entity: "Entity") -> ParticleType:
    """Determine the particle type for an entity based on its tags."""
    if entity.has_tag("the_first_point"):
        return ParticleType.FIRST_POINT
    elif entity.has_tag("point_spirit"):
        return ParticleType.POINT_SPIRIT
    elif entity.has_tag("forward_sentinel"):
        return ParticleType.FORWARD_SENTINEL
    elif entity.has_tag("void_echo"):
        return ParticleType.VOID_ECHO
    elif entity.has_tag("line_walker"):
        return ParticleType.LINE_WALKER
    else:
        return ParticleType.GENERIC
