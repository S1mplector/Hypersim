"""Behavior tree system for enemy AI."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from hypersim.game.ecs.entity import Entity
    from hypersim.game.ecs.world import World


class NodeStatus(Enum):
    """Status returned by behavior tree nodes."""
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


class BehaviorNode(ABC):
    """Base class for behavior tree nodes."""
    
    @abstractmethod
    def tick(self, entity: "Entity", world: "World", dt: float) -> NodeStatus:
        """Execute this node. Returns status."""
        pass
    
    def reset(self) -> None:
        """Reset node state for next execution."""
        pass


class ActionNode(BehaviorNode):
    """Leaf node that executes an action."""
    
    def __init__(self, action: Callable[["Entity", "World", float], NodeStatus]):
        self.action = action
    
    def tick(self, entity: "Entity", world: "World", dt: float) -> NodeStatus:
        return self.action(entity, world, dt)


class ConditionNode(BehaviorNode):
    """Leaf node that checks a condition."""
    
    def __init__(self, condition: Callable[["Entity", "World"], bool]):
        self.condition = condition
    
    def tick(self, entity: "Entity", world: "World", dt: float) -> NodeStatus:
        if self.condition(entity, world):
            return NodeStatus.SUCCESS
        return NodeStatus.FAILURE


class SequenceNode(BehaviorNode):
    """Composite node that runs children in sequence until one fails."""
    
    def __init__(self, children: List[BehaviorNode]):
        self.children = children
        self._current_index = 0
    
    def tick(self, entity: "Entity", world: "World", dt: float) -> NodeStatus:
        while self._current_index < len(self.children):
            child = self.children[self._current_index]
            status = child.tick(entity, world, dt)
            
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
            elif status == NodeStatus.FAILURE:
                self._current_index = 0
                return NodeStatus.FAILURE
            
            self._current_index += 1
        
        self._current_index = 0
        return NodeStatus.SUCCESS
    
    def reset(self) -> None:
        self._current_index = 0
        for child in self.children:
            child.reset()


class SelectorNode(BehaviorNode):
    """Composite node that runs children until one succeeds."""
    
    def __init__(self, children: List[BehaviorNode]):
        self.children = children
        self._current_index = 0
    
    def tick(self, entity: "Entity", world: "World", dt: float) -> NodeStatus:
        while self._current_index < len(self.children):
            child = self.children[self._current_index]
            status = child.tick(entity, world, dt)
            
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
            elif status == NodeStatus.SUCCESS:
                self._current_index = 0
                return NodeStatus.SUCCESS
            
            self._current_index += 1
        
        self._current_index = 0
        return NodeStatus.FAILURE
    
    def reset(self) -> None:
        self._current_index = 0
        for child in self.children:
            child.reset()


class BehaviorTree:
    """Container for a behavior tree with a root node."""
    
    def __init__(self, root: BehaviorNode):
        self.root = root
    
    def tick(self, entity: "Entity", world: "World", dt: float) -> NodeStatus:
        """Execute the behavior tree."""
        return self.root.tick(entity, world, dt)
    
    def reset(self) -> None:
        """Reset tree state."""
        self.root.reset()


# ============================================================================
# Common conditions
# ============================================================================

def player_in_range(detect_range: float) -> Callable[["Entity", "World"], bool]:
    """Create condition: is player within detection range?"""
    def condition(entity: "Entity", world: "World") -> bool:
        from hypersim.game.ecs.component import Transform
        
        player = world.find_player()
        if not player:
            return False
        
        entity_transform = entity.get(Transform)
        player_transform = player.get(Transform)
        
        if not entity_transform or not player_transform:
            return False
        
        dist = np.linalg.norm(
            entity_transform.position[:3] - player_transform.position[:3]
        )
        return dist <= detect_range
    
    return condition


def player_in_attack_range(attack_range: float) -> Callable[["Entity", "World"], bool]:
    """Create condition: is player within attack range?"""
    def condition(entity: "Entity", world: "World") -> bool:
        from hypersim.game.ecs.component import Transform
        
        player = world.find_player()
        if not player:
            return False
        
        entity_transform = entity.get(Transform)
        player_transform = player.get(Transform)
        
        if not entity_transform or not player_transform:
            return False
        
        dist = np.linalg.norm(
            entity_transform.position[:3] - player_transform.position[:3]
        )
        return dist <= attack_range
    
    return condition


def has_line_of_sight() -> Callable[["Entity", "World"], bool]:
    """Create condition: does entity have line of sight to player?"""
    def condition(entity: "Entity", world: "World") -> bool:
        # Simplified: always true (no obstacle checking yet)
        player = world.find_player()
        return player is not None
    
    return condition


# ============================================================================
# Common actions
# ============================================================================

def move_toward_player(speed: float) -> Callable[["Entity", "World", float], NodeStatus]:
    """Create action: move toward player."""
    def action(entity: "Entity", world: "World", dt: float) -> NodeStatus:
        from hypersim.game.ecs.component import Transform, Velocity
        
        player = world.find_player()
        if not player:
            return NodeStatus.FAILURE
        
        entity_transform = entity.get(Transform)
        entity_velocity = entity.get(Velocity)
        player_transform = player.get(Transform)
        
        if not entity_transform or not entity_velocity or not player_transform:
            return NodeStatus.FAILURE
        
        direction = player_transform.position[:3] - entity_transform.position[:3]
        dist = np.linalg.norm(direction)
        
        if dist < 0.5:
            entity_velocity.linear.fill(0)
            return NodeStatus.SUCCESS
        
        direction /= dist
        entity_velocity.linear[:3] = direction * speed
        
        return NodeStatus.RUNNING
    
    return action


def patrol_waypoints(speed: float) -> Callable[["Entity", "World", float], NodeStatus]:
    """Create action: patrol between waypoints."""
    def action(entity: "Entity", world: "World", dt: float) -> NodeStatus:
        from hypersim.game.ecs.component import Transform, Velocity, AIBrain
        
        entity_transform = entity.get(Transform)
        entity_velocity = entity.get(Velocity)
        brain = entity.get(AIBrain)
        
        if not entity_transform or not entity_velocity or not brain:
            return NodeStatus.FAILURE
        
        if not brain.patrol_points:
            entity_velocity.linear.fill(0)
            return NodeStatus.SUCCESS
        
        target = brain.patrol_points[brain.patrol_index]
        direction = target[:3] - entity_transform.position[:3]
        dist = np.linalg.norm(direction)
        
        if dist < 0.5:
            brain.patrol_index = (brain.patrol_index + 1) % len(brain.patrol_points)
            return NodeStatus.RUNNING
        
        direction /= dist
        entity_velocity.linear[:3] = direction * speed
        
        return NodeStatus.RUNNING
    
    return action


def oscillate_1d(speed: float, amplitude: float) -> Callable[["Entity", "World", float], NodeStatus]:
    """Create action: oscillate back and forth on X axis."""
    def action(entity: "Entity", world: "World", dt: float) -> NodeStatus:
        from hypersim.game.ecs.component import Transform, Velocity, AIBrain
        
        entity_transform = entity.get(Transform)
        entity_velocity = entity.get(Velocity)
        brain = entity.get(AIBrain)
        
        if not entity_transform or not entity_velocity:
            return NodeStatus.FAILURE
        
        center = brain.get_state("center", entity_transform.position[0]) if brain else entity_transform.position[0]
        direction = brain.get_state("direction", 1) if brain else 1
        
        current_x = entity_transform.position[0]
        
        if current_x >= center + amplitude:
            direction = -1
            if brain:
                brain.set_state("direction", direction)
        elif current_x <= center - amplitude:
            direction = 1
            if brain:
                brain.set_state("direction", direction)
        
        entity_velocity.linear.fill(0)
        entity_velocity.linear[0] = direction * speed
        
        return NodeStatus.RUNNING
    
    return action


def attack_player(damage: float, cooldown: float) -> Callable[["Entity", "World", float], NodeStatus]:
    """Create action: attack the player."""
    def action(entity: "Entity", world: "World", dt: float) -> NodeStatus:
        from hypersim.game.ecs.component import AIBrain
        
        brain = entity.get(AIBrain)
        if not brain:
            return NodeStatus.FAILURE
        
        # Check cooldown
        last_attack = brain.get_state("last_attack_time", -999.0)
        current_time = brain.get_state("elapsed_time", 0.0) + dt
        brain.set_state("elapsed_time", current_time)
        
        if current_time - last_attack < cooldown:
            return NodeStatus.RUNNING
        
        # Perform attack
        brain.set_state("last_attack_time", current_time)
        world.emit("enemy_attack", entity_id=entity.id, damage=damage)
        
        return NodeStatus.SUCCESS
    
    return action


def idle() -> Callable[["Entity", "World", float], NodeStatus]:
    """Create action: stand idle."""
    def action(entity: "Entity", world: "World", dt: float) -> NodeStatus:
        from hypersim.game.ecs.component import Velocity
        
        velocity = entity.get(Velocity)
        if velocity:
            velocity.linear.fill(0)
        
        return NodeStatus.SUCCESS
    
    return action


# ============================================================================
# Pre-built behavior trees
# ============================================================================

def create_patrol_tree(speed: float = 3.0, detect_range: float = 10.0, chase_speed: float = 4.0) -> BehaviorTree:
    """Create a patrol behavior tree that chases player when in range."""
    return BehaviorTree(
        SelectorNode([
            # If player in range, chase
            SequenceNode([
                ConditionNode(player_in_range(detect_range)),
                ActionNode(move_toward_player(chase_speed)),
            ]),
            # Otherwise patrol
            ActionNode(patrol_waypoints(speed)),
        ])
    )


def create_chase_tree(speed: float = 4.0, detect_range: float = 15.0, attack_range: float = 2.0) -> BehaviorTree:
    """Create a chase-focused behavior tree."""
    return BehaviorTree(
        SelectorNode([
            # Attack if in range
            SequenceNode([
                ConditionNode(player_in_attack_range(attack_range)),
                ActionNode(attack_player(10.0, 1.0)),
            ]),
            # Chase if detected
            SequenceNode([
                ConditionNode(player_in_range(detect_range)),
                ActionNode(move_toward_player(speed)),
            ]),
            # Idle
            ActionNode(idle()),
        ])
    )


def create_shooter_tree(detect_range: float = 20.0, shoot_cooldown: float = 2.0) -> BehaviorTree:
    """Create a stationary shooter behavior tree."""
    return BehaviorTree(
        SelectorNode([
            # Shoot if player in range and has line of sight
            SequenceNode([
                ConditionNode(player_in_range(detect_range)),
                ConditionNode(has_line_of_sight()),
                ActionNode(attack_player(15.0, shoot_cooldown)),
            ]),
            # Idle
            ActionNode(idle()),
        ])
    )


def create_oscillate_tree(speed: float = 2.0, amplitude: float = 3.0) -> BehaviorTree:
    """Create an oscillating blocker behavior tree."""
    return BehaviorTree(
        ActionNode(oscillate_1d(speed, amplitude))
    )
