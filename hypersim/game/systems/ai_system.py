"""AI system - processes NPC behaviors."""
from __future__ import annotations

import math
from typing import Optional, TYPE_CHECKING

import numpy as np

from hypersim.game.ecs.system import System
from hypersim.game.ecs.component import AIBrain, Transform, Velocity, DimensionAnchor

if TYPE_CHECKING:
    from hypersim.game.ecs.world import World
    from hypersim.game.ecs.entity import Entity


class AISystem(System):
    """Processes AI behaviors for NPCs."""
    
    priority = 10  # After input, before physics
    required_components = (AIBrain, Transform, Velocity)
    
    def update(self, world: "World", dt: float) -> None:
        """Update AI behaviors for all NPCs."""
        player = world.find_player()
        player_pos = None
        if player:
            player_transform = player.get(Transform)
            if player_transform:
                player_pos = player_transform.position.copy()
        
        for entity in self.query(world):
            if not entity.active:
                continue
            
            brain = entity.get(AIBrain)
            transform = entity.get(Transform)
            velocity = entity.get(Velocity)

            confused_timer = float(brain.get_state("confused_timer", 0.0))
            if confused_timer > 0.0:
                brain.set_state("confused_timer", max(0.0, confused_timer - dt))
                confusion_level = max(0.0, float(brain.get_state("confusion_level", 0.0)) - dt * 0.4)
                brain.set_state("confusion_level", confusion_level)
                self._behavior_confused(entity, brain, transform, velocity, dt)
                continue
            
            # Dispatch to behavior handler
            if brain.behavior == "idle":
                self._behavior_idle(entity, brain, transform, velocity, dt)
            elif brain.behavior == "patrol":
                self._behavior_patrol(entity, brain, transform, velocity, dt)
            elif brain.behavior == "chase":
                self._behavior_chase(entity, brain, transform, velocity, player_pos, dt)
            elif brain.behavior == "oscillate":
                self._behavior_oscillate(entity, brain, transform, velocity, dt)
    
    def _behavior_idle(
        self, entity: "Entity", brain: AIBrain, transform: Transform, velocity: Velocity, dt: float
    ) -> None:
        """Idle behavior - no movement."""
        velocity.linear.fill(0)
    
    def _behavior_patrol(
        self, entity: "Entity", brain: AIBrain, transform: Transform, velocity: Velocity, dt: float
    ) -> None:
        """Patrol between waypoints."""
        if not brain.patrol_points:
            velocity.linear.fill(0)
            return
        
        target = brain.patrol_points[brain.patrol_index]
        direction = target - transform.position[:len(target)]
        distance = np.linalg.norm(direction)
        
        if distance < 0.5:  # Reached waypoint
            brain.patrol_index = (brain.patrol_index + 1) % len(brain.patrol_points)
            return
        
        # Move toward waypoint
        speed = brain.get_state("speed", 3.0)
        direction_normalized = direction / distance
        velocity.linear[:len(direction_normalized)] = direction_normalized * speed
    
    def _behavior_chase(
        self, entity: "Entity", brain: AIBrain, transform: Transform, velocity: Velocity,
        player_pos: Optional[np.ndarray], dt: float
    ) -> None:
        """Chase the player if in range."""
        if player_pos is None:
            self._behavior_idle(entity, brain, transform, velocity, dt)
            return
        
        direction = player_pos[:len(transform.position)] - transform.position
        distance = np.linalg.norm(direction)
        
        if distance > brain.detect_range:
            # Out of range, idle or patrol
            velocity.linear.fill(0)
            return
        
        if distance < brain.attack_range:
            # In attack range
            velocity.linear.fill(0)
            return
        
        # Chase
        speed = brain.get_state("speed", 4.0)
        direction_normalized = direction / distance
        velocity.linear[:len(direction_normalized)] = direction_normalized * speed
    
    def _behavior_oscillate(
        self, entity: "Entity", brain: AIBrain, transform: Transform, velocity: Velocity, dt: float
    ) -> None:
        """Oscillate back and forth (1D blocker enemy)."""
        # Get oscillation parameters
        center = brain.get_state("center", transform.position[0])
        amplitude = brain.get_state("amplitude", 3.0)
        speed = brain.get_state("speed", 2.0)
        direction = brain.get_state("direction", 1)
        
        # Check bounds
        current_x = transform.position[0]
        if current_x >= center + amplitude:
            direction = -1
            brain.set_state("direction", direction)
        elif current_x <= center - amplitude:
            direction = 1
            brain.set_state("direction", direction)
        
        velocity.linear.fill(0)
        velocity.linear[0] = direction * speed

    def _behavior_confused(
        self, entity: "Entity", brain: AIBrain, transform: Transform, velocity: Velocity, dt: float
    ) -> None:
        """Temporarily destabilize an entity after witnessing impossible movement."""
        level = float(brain.get_state("confusion_level", 0.0))
        phase = float(brain.get_state("confusion_phase", 0.0)) + dt * (5.0 + level * 2.5)
        axis_bias = float(brain.get_state("confusion_axis", 0.0))
        brain.set_state("confusion_phase", phase)

        velocity.linear.fill(0)

        anchor = entity.get(DimensionAnchor)
        if anchor and anchor.dimension_id != "1d":
            return

        center = float(brain.get_state("center", transform.position[0]))
        pull_to_center = (center - float(transform.position[0])) * 0.9
        jitter = math.sin(phase * 2.2 + transform.position[0] * 0.35) * (0.35 + level * 0.8)
        impossible_pull = axis_bias * math.sin(phase * 0.8) * (0.15 + level * 0.45)

        if brain.behavior == "stationary":
            velocity.linear[0] = jitter * 0.4 + impossible_pull * 0.3
            return

        speed_cap = max(1.0, float(brain.get_state("speed", 2.0)) * (0.45 + min(0.6, level * 0.18)))
        velocity.linear[0] = float(np.clip(pull_to_center + jitter + impossible_pull, -speed_cap, speed_cap))
