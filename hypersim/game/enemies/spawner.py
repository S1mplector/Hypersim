"""Enemy spawner and wave system."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING
import random

import numpy as np

from hypersim.game.ecs.entity import Entity
from hypersim.game.ecs.component import (
    Transform, Velocity, Renderable, Collider, ColliderShape,
    Health, AIBrain, DimensionAnchor
)

if TYPE_CHECKING:
    from hypersim.game.ecs.world import World


@dataclass
class EnemyTemplate:
    """Template for spawning enemies."""
    name: str
    behavior: str
    health: float = 50.0
    speed: float = 3.0
    detect_range: float = 10.0
    attack_range: float = 2.0
    size: float = 0.6
    color: tuple = (200, 50, 50)
    damage: float = 10.0
    tags: List[str] = field(default_factory=list)


@dataclass
class WaveConfig:
    """Configuration for an enemy wave."""
    enemies: List[Dict]  # [{"template": "name", "count": N, "position_range": [min, max]}]
    delay_before: float = 2.0  # Seconds before wave starts
    spawn_interval: float = 0.5  # Seconds between spawns


# Pre-defined enemy templates
DEFAULT_TEMPLATES: Dict[str, EnemyTemplate] = {
    "blocker_1d": EnemyTemplate(
        name="Blocker",
        behavior="oscillate",
        health=30,
        speed=2.0,
        size=0.8,
        color=(200, 50, 50),
    ),
    "chaser_1d": EnemyTemplate(
        name="Chaser",
        behavior="chase",
        health=25,
        speed=4.0,
        detect_range=8.0,
        size=0.5,
        color=(255, 80, 80),
    ),
    "patroller_2d": EnemyTemplate(
        name="Patroller",
        behavior="patrol",
        health=50,
        speed=3.0,
        detect_range=10.0,
        size=0.6,
        color=(200, 50, 50),
    ),
    "shooter_2d": EnemyTemplate(
        name="Shooter",
        behavior="shooter",
        health=40,
        speed=0.0,
        detect_range=15.0,
        size=0.7,
        color=(200, 100, 50),
        damage=15.0,
        tags=["ranged"],
    ),
    "flyer_3d": EnemyTemplate(
        name="Flyer",
        behavior="chase",
        health=60,
        speed=5.0,
        detect_range=18.0,
        size=0.7,
        color=(255, 100, 50),
        tags=["flyer"],
    ),
    "tank_3d": EnemyTemplate(
        name="Tank",
        behavior="chase",
        health=150,
        speed=2.0,
        detect_range=12.0,
        attack_range=3.0,
        size=1.2,
        color=(150, 50, 50),
        damage=25.0,
        tags=["heavy"],
    ),
    "shifter_4d": EnemyTemplate(
        name="Shifter",
        behavior="chase",
        health=80,
        speed=4.0,
        detect_range=12.0,
        size=0.6,
        color=(255, 50, 150),
        tags=["shifter"],
    ),
}


class EnemySpawner:
    """Spawns enemies based on templates and wave configurations."""
    
    def __init__(self, world: "World", dimension: str):
        self.world = world
        self.dimension = dimension
        self.templates: Dict[str, EnemyTemplate] = DEFAULT_TEMPLATES.copy()
        self._enemy_counter = 0
        
        # Wave state
        self._current_wave: Optional[WaveConfig] = None
        self._wave_timer = 0.0
        self._spawn_queue: List[Dict] = []
        self._spawn_timer = 0.0
    
    def register_template(self, name: str, template: EnemyTemplate) -> None:
        """Register a custom enemy template."""
        self.templates[name] = template
    
    def spawn(
        self,
        template_name: str,
        position: np.ndarray,
        patrol_points: Optional[List[np.ndarray]] = None,
        **overrides
    ) -> Entity:
        """Spawn an enemy from a template at a position."""
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Unknown enemy template: {template_name}")
        
        self._enemy_counter += 1
        enemy_id = f"enemy_{self._enemy_counter}"
        
        # Determine collider shape based on dimension
        collider_map = {
            "1d": ColliderShape.SEGMENT,
            "2d": ColliderShape.CIRCLE,
            "3d": ColliderShape.SPHERE,
            "4d": ColliderShape.SPHERE,
        }
        
        # Apply overrides
        health = overrides.get("health", template.health)
        speed = overrides.get("speed", template.speed)
        color = overrides.get("color", template.color)
        size = overrides.get("size", template.size)
        
        enemy = Entity(id=enemy_id)
        enemy.add(Transform(position=position.copy()))
        enemy.add(Velocity())
        enemy.add(Renderable(color=color))
        enemy.add(Collider(
            shape=collider_map.get(self.dimension, ColliderShape.CIRCLE),
            size=np.array([size]),
        ))
        enemy.add(Health(current=health, max=health))
        enemy.add(AIBrain(
            behavior=template.behavior,
            patrol_points=patrol_points or [],
            detect_range=overrides.get("detect_range", template.detect_range),
            attack_range=overrides.get("attack_range", template.attack_range),
            state={
                "speed": speed,
                "center": position[0] if len(position) > 0 else 0,
                "amplitude": overrides.get("amplitude", 3.0),
                "direction": 1,
            },
        ))
        enemy.add(DimensionAnchor(dimension_id=self.dimension))
        enemy.tag("enemy")
        
        for tag in template.tags:
            enemy.tag(tag)
        
        self.world.spawn(enemy)
        return enemy
    
    def spawn_random(
        self,
        template_name: str,
        bounds_min: np.ndarray,
        bounds_max: np.ndarray,
        **overrides
    ) -> Entity:
        """Spawn an enemy at a random position within bounds."""
        position = np.random.uniform(bounds_min, bounds_max)
        return self.spawn(template_name, position, **overrides)
    
    def start_wave(self, wave: WaveConfig) -> None:
        """Start a wave of enemies."""
        self._current_wave = wave
        self._wave_timer = wave.delay_before
        self._spawn_queue = []
        
        # Build spawn queue
        for enemy_config in wave.enemies:
            template = enemy_config.get("template", "patroller_2d")
            count = enemy_config.get("count", 1)
            pos_range = enemy_config.get("position_range", [[-10, -10], [10, 10]])
            
            for _ in range(count):
                self._spawn_queue.append({
                    "template": template,
                    "bounds_min": np.array(pos_range[0]),
                    "bounds_max": np.array(pos_range[1]),
                })
        
        random.shuffle(self._spawn_queue)
        self._spawn_timer = 0.0
    
    def update(self, dt: float) -> bool:
        """Update wave spawning. Returns True if wave is complete."""
        if not self._current_wave:
            return True
        
        # Wait for wave to start
        if self._wave_timer > 0:
            self._wave_timer -= dt
            return False
        
        # Spawn enemies
        if self._spawn_queue:
            self._spawn_timer -= dt
            if self._spawn_timer <= 0:
                config = self._spawn_queue.pop(0)
                self.spawn_random(
                    config["template"],
                    config["bounds_min"],
                    config["bounds_max"],
                )
                self._spawn_timer = self._current_wave.spawn_interval
            return False
        
        # Wave complete
        self._current_wave = None
        return True
    
    def get_enemy_count(self) -> int:
        """Get current number of active enemies."""
        return len([e for e in self.world.with_tag("enemy") if e.active])
