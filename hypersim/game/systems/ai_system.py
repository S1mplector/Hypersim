"""AI system - processes NPC behaviors."""
from __future__ import annotations

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
