"""Bullet patterns and attack systems for combat."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple

from .core import PlayerSoul, SoulMode


class BulletType(Enum):
    """Types of bullets with different behaviors."""
    NORMAL = auto()       # White - always damages
    ORANGE = auto()       # Orange - damages if stationary
    CYAN = auto()         # Cyan/Light Blue - damages if moving
    GREEN = auto()        # Green - heals instead of damages
    YELLOW = auto()       # Yellow - can be destroyed by shooting
    PURPLE = auto()       # Purple - homes towards player
    BLUE = auto()         # Blue - affected by gravity


@dataclass
class Bullet:
    """A single bullet/projectile in the battle box."""
    x: float
    y: float
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    
    # Appearance
    bullet_type: BulletType = BulletType.NORMAL
    radius: float = 8.0
    color: Tuple[int, int, int] = (255, 255, 255)
    shape: str = "circle"  # circle, square, triangle, star, bone, etc.
    
    # Behavior
    lifetime: float = 10.0
    age: float = 0.0
    damage: int = 5
    
    # Special behaviors
    homing: bool = False
    homing_strength: float = 2.0
    gravity_affected: bool = False
    gravity: float = 200.0
    bounces: bool = False
    bounces_remaining: int = 0
    spinning: bool = False
    spin_speed: float = 0.0
    spin_angle: float = 0.0
    
    # Wave behavior
    wave_amplitude: float = 0.0
    wave_frequency: float = 0.0
    wave_offset: float = 0.0
    
    # State
    active: bool = True
    
    def update(self, dt: float, soul: PlayerSoul, box_bounds: Tuple[float, float, float, float]) -> None:
        """Update bullet position and behavior."""
        if not self.active:
            return
        
        self.age += dt
        if self.age >= self.lifetime:
            self.active = False
            return
        
        # Homing behavior
        if self.homing:
            dx = soul.x - self.x
            dy = soul.y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                self.velocity_x += (dx / dist) * self.homing_strength * dt * 100
                self.velocity_y += (dy / dist) * self.homing_strength * dt * 100
        
        # Gravity
        if self.gravity_affected:
            self.velocity_y += self.gravity * dt
        
        # Wave motion
        if self.wave_amplitude > 0:
            wave_offset = math.sin(self.age * self.wave_frequency + self.wave_offset) * self.wave_amplitude
            # Apply perpendicular to velocity
            speed = math.sqrt(self.velocity_x ** 2 + self.velocity_y ** 2)
            if speed > 0:
                perp_x = -self.velocity_y / speed
                perp_y = self.velocity_x / speed
                self.x += perp_x * wave_offset * dt * 10
                self.y += perp_y * wave_offset * dt * 10
        
        # Move
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        
        # Spinning
        if self.spinning:
            self.spin_angle += self.spin_speed * dt
        
        # Bounds checking
        min_x, min_y, max_x, max_y = box_bounds
        
        if self.bounces and self.bounces_remaining > 0:
            if self.x < min_x or self.x > max_x:
                self.velocity_x *= -1
                self.bounces_remaining -= 1
                self.x = max(min_x, min(max_x, self.x))
            if self.y < min_y or self.y > max_y:
                self.velocity_y *= -1
                self.bounces_remaining -= 1
                self.y = max(min_y, min(max_y, self.y))
        else:
            # Deactivate if out of bounds (with margin)
            margin = self.radius * 2
            if (self.x < min_x - margin or self.x > max_x + margin or
                self.y < min_y - margin or self.y > max_y + margin):
                self.active = False
    
    def check_hit(self, soul: PlayerSoul, soul_moving: bool) -> bool:
        """Check if bullet hits soul. Returns True if hit should register."""
        if not self.active or soul.invincible:
            return False
        
        # Distance check
        dist = math.sqrt((self.x - soul.x) ** 2 + (self.y - soul.y) ** 2)
        if dist >= self.radius + soul.radius:
            return False
        
        # Special bullet type rules
        if self.bullet_type == BulletType.ORANGE:
            return not soul_moving  # Only hits if standing still
        elif self.bullet_type == BulletType.CYAN:
            return soul_moving  # Only hits if moving
        elif self.bullet_type == BulletType.GREEN:
            return False  # Never damages (heals handled separately)
        
        return True


@dataclass
class BulletPattern:
    """A pattern of bullets spawned together or over time."""
    bullets: List[Bullet] = field(default_factory=list)
    
    # Spawning
    spawn_interval: float = 0.0  # 0 = all at once
    spawn_timer: float = 0.0
    spawn_index: int = 0
    bullets_to_spawn: List[Bullet] = field(default_factory=list)
    
    # Pattern state
    active: bool = True
    completed: bool = False
    
    def update(self, dt: float, soul: PlayerSoul, box_bounds: Tuple[float, float, float, float]) -> List[Bullet]:
        """Update pattern and return newly spawned bullets."""
        new_bullets = []
        
        # Timed spawning
        if self.spawn_interval > 0 and self.bullets_to_spawn:
            self.spawn_timer += dt
            while self.spawn_timer >= self.spawn_interval and self.spawn_index < len(self.bullets_to_spawn):
                new_bullets.append(self.bullets_to_spawn[self.spawn_index])
                self.spawn_index += 1
                self.spawn_timer -= self.spawn_interval
            
            if self.spawn_index >= len(self.bullets_to_spawn):
                self.completed = True
        
        # Update existing bullets
        for bullet in self.bullets:
            bullet.update(dt, soul, box_bounds)
        
        # Remove inactive bullets
        self.bullets = [b for b in self.bullets if b.active]
        
        # Add new bullets
        self.bullets.extend(new_bullets)
        
        # Check if pattern is done
        if self.completed and not self.bullets:
            self.active = False
        
        return new_bullets


@dataclass
class AttackWave:
    """A single wave of an attack - one pattern or set of patterns."""
    patterns: List[BulletPattern] = field(default_factory=list)
    duration: float = 3.0
    soul_mode: SoulMode = SoulMode.RED
    dialogue: str = ""
    
    # Timing
    delay: float = 0.0  # Delay before wave starts
    started: bool = False
    elapsed: float = 0.0
    
    @property
    def active(self) -> bool:
        return any(p.active for p in self.patterns)
    
    @property
    def all_bullets(self) -> List[Bullet]:
        bullets = []
        for pattern in self.patterns:
            bullets.extend(pattern.bullets)
        return bullets


@dataclass
class AttackSequence:
    """A full attack sequence made of multiple waves."""
    waves: List[AttackWave] = field(default_factory=list)
    current_wave_index: int = 0
    
    # Timing
    total_duration: float = 0.0
    elapsed: float = 0.0
    
    # State
    active: bool = True
    completed: bool = False
    
    def __post_init__(self):
        self.total_duration = sum(w.duration + w.delay for w in self.waves)
    
    @property
    def current_wave(self) -> Optional[AttackWave]:
        if 0 <= self.current_wave_index < len(self.waves):
            return self.waves[self.current_wave_index]
        return None
    
    def advance_wave(self) -> bool:
        """Move to next wave. Returns True if there are more waves."""
        self.current_wave_index += 1
        return self.current_wave_index < len(self.waves)


# =============================================================================
# PATTERN GENERATORS
# =============================================================================

class PatternGenerator:
    """Generates bullet patterns for various attack types."""
    
    @staticmethod
    def circle_burst(
        center_x: float, center_y: float,
        bullet_count: int = 8,
        speed: float = 150.0,
        bullet_type: BulletType = BulletType.NORMAL,
        radius: float = 8.0,
        offset_angle: float = 0.0
    ) -> List[Bullet]:
        """Create bullets in a circular burst pattern."""
        bullets = []
        for i in range(bullet_count):
            angle = (2 * math.pi * i / bullet_count) + offset_angle
            bullets.append(Bullet(
                x=center_x,
                y=center_y,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
                bullet_type=bullet_type,
                radius=radius,
            ))
        return bullets
    
    @staticmethod
    def spiral(
        center_x: float, center_y: float,
        bullet_count: int = 24,
        speed: float = 100.0,
        spiral_rate: float = 0.5,
        spawn_interval: float = 0.1
    ) -> BulletPattern:
        """Create a spiral pattern that spawns over time."""
        bullets = []
        for i in range(bullet_count):
            angle = i * spiral_rate
            bullets.append(Bullet(
                x=center_x,
                y=center_y,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
            ))
        
        return BulletPattern(
            bullets_to_spawn=bullets,
            spawn_interval=spawn_interval,
        )
    
    @staticmethod
    def wall(
        start_x: float, start_y: float,
        end_x: float, end_y: float,
        bullet_count: int = 10,
        velocity_x: float = 0.0,
        velocity_y: float = 150.0,
        bullet_type: BulletType = BulletType.NORMAL
    ) -> List[Bullet]:
        """Create a wall of bullets."""
        bullets = []
        for i in range(bullet_count):
            t = i / max(1, bullet_count - 1)
            x = start_x + (end_x - start_x) * t
            y = start_y + (end_y - start_y) * t
            bullets.append(Bullet(
                x=x, y=y,
                velocity_x=velocity_x,
                velocity_y=velocity_y,
                bullet_type=bullet_type,
            ))
        return bullets
    
    @staticmethod
    def aimed_shot(
        origin_x: float, origin_y: float,
        target_x: float, target_y: float,
        speed: float = 200.0,
        spread: float = 0.0,
        count: int = 1
    ) -> List[Bullet]:
        """Create bullets aimed at a target."""
        bullets = []
        dx = target_x - origin_x
        dy = target_y - origin_y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist == 0:
            return bullets
        
        base_angle = math.atan2(dy, dx)
        
        for i in range(count):
            if count > 1:
                angle_offset = (i - (count - 1) / 2) * spread
            else:
                angle_offset = 0
            
            angle = base_angle + angle_offset
            bullets.append(Bullet(
                x=origin_x,
                y=origin_y,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
            ))
        
        return bullets
    
    @staticmethod
    def sine_wave(
        start_x: float, y: float,
        direction: float = 1.0,  # 1 = right, -1 = left
        bullet_count: int = 12,
        speed: float = 120.0,
        amplitude: float = 30.0,
        frequency: float = 5.0,
        spawn_interval: float = 0.15
    ) -> BulletPattern:
        """Create bullets that move in a sine wave pattern."""
        bullets = []
        for i in range(bullet_count):
            bullet = Bullet(
                x=start_x,
                y=y,
                velocity_x=speed * direction,
                velocity_y=0,
                wave_amplitude=amplitude,
                wave_frequency=frequency,
                wave_offset=i * 0.5,
            )
            bullets.append(bullet)
        
        return BulletPattern(
            bullets_to_spawn=bullets,
            spawn_interval=spawn_interval,
        )
    
    @staticmethod
    def bone_attack(
        side: str,  # "left", "right", "top", "bottom"
        box_bounds: Tuple[float, float, float, float],
        gap_y: float,
        gap_height: float = 40.0,
        speed: float = 200.0
    ) -> List[Bullet]:
        """Create a bone-style attack with a gap to dodge through."""
        min_x, min_y, max_x, max_y = box_bounds
        bullets = []
        
        if side == "left":
            x = min_x
            vx, vy = speed, 0
        elif side == "right":
            x = max_x
            vx, vy = -speed, 0
        elif side == "top":
            x = (min_x + max_x) / 2
            vx, vy = 0, speed
        else:  # bottom
            x = (min_x + max_x) / 2
            vx, vy = 0, -speed
        
        # Create bones above and below gap
        bone_spacing = 20
        
        if side in ["left", "right"]:
            # Vertical bones
            for y in range(int(min_y), int(gap_y - gap_height / 2), bone_spacing):
                bullets.append(Bullet(x=x, y=y, velocity_x=vx, velocity_y=vy, shape="bone"))
            for y in range(int(gap_y + gap_height / 2), int(max_y), bone_spacing):
                bullets.append(Bullet(x=x, y=y, velocity_x=vx, velocity_y=vy, shape="bone"))
        
        return bullets
    
    @staticmethod
    def bouncing_bullets(
        box_bounds: Tuple[float, float, float, float],
        count: int = 5,
        speed: float = 180.0,
        bounces: int = 3
    ) -> List[Bullet]:
        """Create bullets that bounce off walls."""
        min_x, min_y, max_x, max_y = box_bounds
        bullets = []
        
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            x = random.uniform(min_x + 20, max_x - 20)
            y = random.uniform(min_y + 20, max_y - 20)
            
            bullets.append(Bullet(
                x=x, y=y,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
                bounces=True,
                bounces_remaining=bounces,
            ))
        
        return bullets
    
    @staticmethod
    def homing_attack(
        origin_x: float, origin_y: float,
        count: int = 3,
        speed: float = 80.0,
        homing_strength: float = 3.0,
        spawn_interval: float = 0.5
    ) -> BulletPattern:
        """Create homing bullets."""
        bullets = []
        for i in range(count):
            angle = random.uniform(0, 2 * math.pi)
            bullets.append(Bullet(
                x=origin_x,
                y=origin_y,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
                homing=True,
                homing_strength=homing_strength,
                bullet_type=BulletType.PURPLE,
                color=(200, 100, 255),
            ))
        
        return BulletPattern(
            bullets_to_spawn=bullets,
            spawn_interval=spawn_interval,
        )
    
    @staticmethod
    def gravity_drop(
        box_bounds: Tuple[float, float, float, float],
        count: int = 8,
        gravity: float = 300.0
    ) -> List[Bullet]:
        """Create bullets that fall with gravity."""
        min_x, min_y, max_x, max_y = box_bounds
        bullets = []
        
        spacing = (max_x - min_x) / (count + 1)
        for i in range(count):
            x = min_x + spacing * (i + 1)
            bullets.append(Bullet(
                x=x,
                y=min_y,
                velocity_x=random.uniform(-20, 20),
                velocity_y=0,
                gravity_affected=True,
                gravity=gravity,
                bullet_type=BulletType.BLUE,
                color=(100, 100, 255),
            ))
        
        return bullets


# =============================================================================
# ATTACK BUILDERS
# =============================================================================

def build_attack_from_pattern(
    pattern_type: str,
    box_bounds: Tuple[float, float, float, float],
    duration: float,
    difficulty: float = 1.0,
    **kwargs
) -> AttackSequence:
    """Build an attack sequence from a pattern type."""
    min_x, min_y, max_x, max_y = box_bounds
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    waves = []
    
    if pattern_type == "horizontal_lines":
        # Horizontal lines moving across
        for i in range(3):
            direction = 1 if i % 2 == 0 else -1
            start_x = min_x if direction > 0 else max_x
            bullets = PatternGenerator.wall(
                start_x, min_y, start_x, max_y,
                bullet_count=int(8 * difficulty),
                velocity_x=200 * direction * difficulty,
                velocity_y=0
            )
            pattern = BulletPattern(bullets=bullets)
            waves.append(AttackWave(patterns=[pattern], duration=duration / 3, delay=i * 0.8))
    
    elif pattern_type == "pulse":
        # Expanding circles
        for i in range(int(3 * difficulty)):
            bullets = PatternGenerator.circle_burst(
                center_x, center_y,
                bullet_count=int(12 * difficulty),
                speed=150 * difficulty,
                offset_angle=i * 0.3
            )
            pattern = BulletPattern(bullets=bullets)
            waves.append(AttackWave(patterns=[pattern], duration=duration / 3, delay=i * 0.5))
    
    elif pattern_type == "spinning_triangles":
        # Spinning triangle projectiles
        for i in range(int(4 * difficulty)):
            bullets = PatternGenerator.circle_burst(
                center_x, center_y,
                bullet_count=3,
                speed=180 * difficulty,
                offset_angle=i * math.pi / 6
            )
            for b in bullets:
                b.shape = "triangle"
                b.spinning = True
                b.spin_speed = 5.0
            pattern = BulletPattern(bullets=bullets)
            waves.append(AttackWave(patterns=[pattern], duration=duration / 4, delay=i * 0.4))
    
    elif pattern_type == "grid":
        # Grid of bullets
        bullets = []
        grid_size = int(4 * difficulty)
        spacing_x = (max_x - min_x) / (grid_size + 1)
        spacing_y = (max_y - min_y) / (grid_size + 1)
        for i in range(grid_size):
            for j in range(grid_size):
                x = min_x + spacing_x * (i + 1)
                y = min_y + spacing_y * (j + 1)
                bullets.append(Bullet(
                    x=x, y=y,
                    velocity_x=random.uniform(-50, 50) * difficulty,
                    velocity_y=random.uniform(-50, 50) * difficulty,
                ))
        pattern = BulletPattern(bullets=bullets)
        waves.append(AttackWave(patterns=[pattern], duration=duration))
    
    elif pattern_type == "spiral":
        pattern = PatternGenerator.spiral(
            center_x, center_y,
            bullet_count=int(24 * difficulty),
            speed=120 * difficulty,
            spawn_interval=0.08 / difficulty
        )
        waves.append(AttackWave(patterns=[pattern], duration=duration))
    
    elif pattern_type == "bouncing_spheres":
        bullets = PatternGenerator.bouncing_bullets(
            box_bounds,
            count=int(5 * difficulty),
            speed=180 * difficulty,
            bounces=int(4 * difficulty)
        )
        pattern = BulletPattern(bullets=bullets)
        waves.append(AttackWave(patterns=[pattern], duration=duration))
    
    elif pattern_type == "tesseract":
        # Complex 4D-themed attack
        for i in range(4):
            bullets = PatternGenerator.circle_burst(
                center_x, center_y,
                bullet_count=8,
                speed=200 * difficulty,
                offset_angle=i * math.pi / 4
            )
            for b in bullets:
                b.shape = "square"
            pattern = BulletPattern(bullets=bullets)
            waves.append(AttackWave(patterns=[pattern], duration=duration / 4, delay=i * 0.3))
    
    elif pattern_type == "phase_shift":
        # Blue soul gravity attack
        bullets = PatternGenerator.gravity_drop(box_bounds, count=int(10 * difficulty))
        pattern = BulletPattern(bullets=bullets)
        waves.append(AttackWave(
            patterns=[pattern],
            duration=duration,
            soul_mode=SoulMode.BLUE
        ))
    
    else:
        # Default: simple aimed shots
        bullets = PatternGenerator.aimed_shot(
            center_x, min_y,
            center_x, center_y,
            speed=150 * difficulty,
            spread=0.5,
            count=int(5 * difficulty)
        )
        pattern = BulletPattern(bullets=bullets)
        waves.append(AttackWave(patterns=[pattern], duration=duration))
    
    return AttackSequence(waves=waves)
