"""4D Particle system for visual effects.

Provides particle emitters and systems for creating
visual effects like explosions, trails, and ambient particles.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Tuple, Optional, Callable
import numpy as np
import random


class EmitterShape(Enum):
    """Shapes for particle emission."""
    POINT = auto()
    SPHERE = auto()
    BOX = auto()
    RING = auto()      # 2D ring in specified plane
    HYPERSPHERE = auto()  # 4D sphere surface


@dataclass
class ParticleConfig:
    """Configuration for particles."""
    # Lifetime
    lifetime_min: float = 1.0
    lifetime_max: float = 2.0
    
    # Initial velocity
    speed_min: float = 0.5
    speed_max: float = 2.0
    
    # Size
    size_start: float = 4.0
    size_end: float = 1.0
    
    # Color
    color_start: Tuple[int, int, int] = (255, 255, 255)
    color_end: Tuple[int, int, int] = (100, 100, 100)
    
    # Alpha
    alpha_start: int = 255
    alpha_end: int = 0
    
    # Physics
    gravity: np.ndarray = field(default_factory=lambda: np.array([0, -1, 0, 0], dtype=np.float32))
    gravity_scale: float = 0.5
    drag: float = 0.02
    
    # Rotation (angular velocity range)
    rotation_speed_min: float = 0.0
    rotation_speed_max: float = 2.0


@dataclass
class Particle4D:
    """A single particle in 4D space."""
    position: np.ndarray
    velocity: np.ndarray
    lifetime: float
    max_lifetime: float
    size_start: float
    size_end: float
    color_start: Tuple[int, int, int]
    color_end: Tuple[int, int, int]
    alpha_start: int
    alpha_end: int
    rotation: float = 0.0
    rotation_speed: float = 0.0
    
    @property
    def alive(self) -> bool:
        """Check if particle is still alive."""
        return self.lifetime > 0
    
    @property
    def age_ratio(self) -> float:
        """Get age as ratio of lifetime (0 = new, 1 = dead)."""
        return 1.0 - (self.lifetime / self.max_lifetime)
    
    @property
    def current_size(self) -> float:
        """Get current size based on age."""
        t = self.age_ratio
        return self.size_start + (self.size_end - self.size_start) * t
    
    @property
    def current_color(self) -> Tuple[int, int, int]:
        """Get current color based on age."""
        t = self.age_ratio
        return tuple(
            int(self.color_start[i] + (self.color_end[i] - self.color_start[i]) * t)
            for i in range(3)
        )
    
    @property
    def current_alpha(self) -> int:
        """Get current alpha based on age."""
        t = self.age_ratio
        return int(self.alpha_start + (self.alpha_end - self.alpha_start) * t)
    
    def update(self, dt: float, gravity: np.ndarray, drag: float) -> None:
        """Update particle state."""
        if not self.alive:
            return
        
        # Apply gravity
        self.velocity += gravity * dt
        
        # Apply drag
        self.velocity *= (1 - drag)
        
        # Update position
        self.position += self.velocity * dt
        
        # Update rotation
        self.rotation += self.rotation_speed * dt
        
        # Update lifetime
        self.lifetime -= dt


class ParticleEmitter:
    """Emits particles from a source."""
    
    def __init__(
        self,
        position: np.ndarray,
        config: Optional[ParticleConfig] = None,
        shape: EmitterShape = EmitterShape.POINT,
        shape_size: float = 1.0,
        emission_rate: float = 10.0,  # Particles per second
        max_particles: int = 1000,
    ):
        self.position = np.array(position, dtype=np.float32)
        self.config = config or ParticleConfig()
        self.shape = shape
        self.shape_size = shape_size
        self.emission_rate = emission_rate
        self.max_particles = max_particles
        
        self.particles: List[Particle4D] = []
        self._emission_accumulator = 0.0
        self.enabled = True
        self.direction: Optional[np.ndarray] = None  # Optional emission direction
        self.spread: float = 1.0  # Spread angle (0 = focused, 1 = omnidirectional)
    
    def emit(self, count: int = 1) -> List[Particle4D]:
        """Emit particles immediately."""
        new_particles = []
        
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            
            particle = self._create_particle()
            self.particles.append(particle)
            new_particles.append(particle)
        
        return new_particles
    
    def _create_particle(self) -> Particle4D:
        """Create a new particle."""
        cfg = self.config
        
        # Position based on emitter shape
        pos = self._get_emission_position()
        
        # Velocity based on direction and spread
        vel = self._get_emission_velocity()
        
        # Randomize properties
        lifetime = random.uniform(cfg.lifetime_min, cfg.lifetime_max)
        rotation_speed = random.uniform(cfg.rotation_speed_min, cfg.rotation_speed_max)
        
        return Particle4D(
            position=pos,
            velocity=vel,
            lifetime=lifetime,
            max_lifetime=lifetime,
            size_start=cfg.size_start,
            size_end=cfg.size_end,
            color_start=cfg.color_start,
            color_end=cfg.color_end,
            alpha_start=cfg.alpha_start,
            alpha_end=cfg.alpha_end,
            rotation_speed=rotation_speed,
        )
    
    def _get_emission_position(self) -> np.ndarray:
        """Get position for new particle based on emitter shape."""
        if self.shape == EmitterShape.POINT:
            return self.position.copy()
        
        elif self.shape == EmitterShape.SPHERE:
            # Random point in 3D sphere (XYZ)
            direction = np.random.randn(4).astype(np.float32)
            direction[3] = 0  # Keep W at emitter position
            norm = np.linalg.norm(direction)
            if norm > 0:
                direction /= norm
            radius = random.uniform(0, self.shape_size)
            return self.position + direction * radius
        
        elif self.shape == EmitterShape.BOX:
            offset = np.array([
                random.uniform(-self.shape_size, self.shape_size),
                random.uniform(-self.shape_size, self.shape_size),
                random.uniform(-self.shape_size, self.shape_size),
                random.uniform(-self.shape_size / 2, self.shape_size / 2),
            ], dtype=np.float32)
            return self.position + offset
        
        elif self.shape == EmitterShape.RING:
            angle = random.uniform(0, 2 * np.pi)
            offset = np.array([
                np.cos(angle) * self.shape_size,
                np.sin(angle) * self.shape_size,
                0, 0
            ], dtype=np.float32)
            return self.position + offset
        
        elif self.shape == EmitterShape.HYPERSPHERE:
            # Random point on 4D hypersphere surface
            direction = np.random.randn(4).astype(np.float32)
            norm = np.linalg.norm(direction)
            if norm > 0:
                direction /= norm
            return self.position + direction * self.shape_size
        
        return self.position.copy()
    
    def _get_emission_velocity(self) -> np.ndarray:
        """Get velocity for new particle."""
        cfg = self.config
        speed = random.uniform(cfg.speed_min, cfg.speed_max)
        
        if self.direction is not None:
            # Use specified direction with spread
            base_dir = self.direction / np.linalg.norm(self.direction)
            
            # Add random spread
            spread_vec = np.random.randn(4).astype(np.float32) * self.spread
            direction = base_dir + spread_vec
            norm = np.linalg.norm(direction)
            if norm > 0:
                direction /= norm
        else:
            # Random direction
            direction = np.random.randn(4).astype(np.float32)
            norm = np.linalg.norm(direction)
            if norm > 0:
                direction /= norm
        
        return direction * speed
    
    def update(self, dt: float) -> None:
        """Update emitter and all particles."""
        # Automatic emission
        if self.enabled:
            self._emission_accumulator += self.emission_rate * dt
            while self._emission_accumulator >= 1.0:
                self.emit(1)
                self._emission_accumulator -= 1.0
        
        # Update particles
        gravity = self.config.gravity * self.config.gravity_scale
        drag = self.config.drag
        
        for particle in self.particles:
            particle.update(dt, gravity, drag)
        
        # Remove dead particles
        self.particles = [p for p in self.particles if p.alive]
    
    def clear(self) -> None:
        """Remove all particles."""
        self.particles.clear()
    
    @property
    def particle_count(self) -> int:
        """Get current particle count."""
        return len(self.particles)


class ParticleSystem:
    """Manages multiple particle emitters."""
    
    def __init__(self):
        self.emitters: List[ParticleEmitter] = []
        self.global_time_scale: float = 1.0
    
    def add_emitter(self, emitter: ParticleEmitter) -> int:
        """Add an emitter and return its index."""
        self.emitters.append(emitter)
        return len(self.emitters) - 1
    
    def remove_emitter(self, index: int) -> None:
        """Remove an emitter by index."""
        if 0 <= index < len(self.emitters):
            self.emitters.pop(index)
    
    def create_emitter(
        self,
        position: np.ndarray,
        config: Optional[ParticleConfig] = None,
        **kwargs,
    ) -> ParticleEmitter:
        """Create and add a new emitter."""
        emitter = ParticleEmitter(position, config, **kwargs)
        self.emitters.append(emitter)
        return emitter
    
    def update(self, dt: float) -> None:
        """Update all emitters."""
        dt *= self.global_time_scale
        for emitter in self.emitters:
            emitter.update(dt)
    
    def get_all_particles(self) -> List[Particle4D]:
        """Get all particles from all emitters."""
        particles = []
        for emitter in self.emitters:
            particles.extend(emitter.particles)
        return particles
    
    @property
    def total_particles(self) -> int:
        """Get total particle count."""
        return sum(e.particle_count for e in self.emitters)
    
    def clear(self) -> None:
        """Clear all emitters and particles."""
        for emitter in self.emitters:
            emitter.clear()
        self.emitters.clear()
    
    # Preset effects
    
    @classmethod
    def create_explosion(
        cls,
        position: np.ndarray,
        intensity: float = 1.0,
    ) -> "ParticleSystem":
        """Create an explosion effect."""
        system = cls()
        
        config = ParticleConfig(
            lifetime_min=0.5 * intensity,
            lifetime_max=1.5 * intensity,
            speed_min=2.0 * intensity,
            speed_max=5.0 * intensity,
            size_start=8.0,
            size_end=2.0,
            color_start=(255, 200, 50),
            color_end=(255, 50, 0),
            alpha_start=255,
            alpha_end=0,
            gravity_scale=0.3,
            drag=0.05,
        )
        
        emitter = ParticleEmitter(
            position=position,
            config=config,
            shape=EmitterShape.POINT,
            emission_rate=0,  # Burst only
            max_particles=200,
        )
        
        # Burst emission
        emitter.emit(int(100 * intensity))
        emitter.enabled = False
        
        system.emitters.append(emitter)
        return system
    
    @classmethod
    def create_fountain(
        cls,
        position: np.ndarray,
        direction: np.ndarray = None,
    ) -> "ParticleSystem":
        """Create a fountain effect."""
        system = cls()
        
        if direction is None:
            direction = np.array([0, 1, 0, 0], dtype=np.float32)
        
        config = ParticleConfig(
            lifetime_min=1.0,
            lifetime_max=2.0,
            speed_min=3.0,
            speed_max=5.0,
            size_start=4.0,
            size_end=2.0,
            color_start=(100, 200, 255),
            color_end=(50, 100, 200),
            gravity_scale=1.0,
        )
        
        emitter = ParticleEmitter(
            position=position,
            config=config,
            shape=EmitterShape.POINT,
            emission_rate=50,
            max_particles=500,
        )
        emitter.direction = direction
        emitter.spread = 0.2
        
        system.emitters.append(emitter)
        return system
    
    @classmethod
    def create_ambient(
        cls,
        center: np.ndarray,
        radius: float = 5.0,
    ) -> "ParticleSystem":
        """Create ambient floating particles."""
        system = cls()
        
        config = ParticleConfig(
            lifetime_min=3.0,
            lifetime_max=6.0,
            speed_min=0.1,
            speed_max=0.3,
            size_start=2.0,
            size_end=2.0,
            color_start=(200, 200, 255),
            color_end=(100, 100, 200),
            alpha_start=100,
            alpha_end=0,
            gravity_scale=0.0,
            drag=0.0,
        )
        
        emitter = ParticleEmitter(
            position=center,
            config=config,
            shape=EmitterShape.HYPERSPHERE,
            shape_size=radius,
            emission_rate=5,
            max_particles=100,
        )
        
        system.emitters.append(emitter)
        return system
    
    @classmethod
    def create_trail(
        cls,
        start_position: np.ndarray,
    ) -> "ParticleSystem":
        """Create a particle trail effect."""
        system = cls()
        
        config = ParticleConfig(
            lifetime_min=0.3,
            lifetime_max=0.5,
            speed_min=0.0,
            speed_max=0.1,
            size_start=4.0,
            size_end=1.0,
            color_start=(255, 255, 255),
            color_end=(100, 150, 255),
            alpha_start=200,
            alpha_end=0,
            gravity_scale=0.0,
            drag=0.1,
        )
        
        emitter = ParticleEmitter(
            position=start_position,
            config=config,
            shape=EmitterShape.POINT,
            emission_rate=30,
            max_particles=100,
        )
        emitter.enabled = True
        
        system.emitters.append(emitter)
        return system
