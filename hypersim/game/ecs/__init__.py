"""Entity Component System for cross-dimensional gameplay.

This module provides a lightweight ECS that allows entities to exist across
different dimensions while sharing common logic through systems.
"""

from .component import (
    Component,
    Transform,
    Velocity,
    Renderable,
    Collider,
    ColliderShape,
    Health,
    Controller,
    AIBrain,
    DimensionAnchor,
)
from .entity import Entity
from .system import System
from .world import World, GameEvent

__all__ = [
    "Component",
    "Transform",
    "Velocity",
    "Renderable",
    "Collider",
    "ColliderShape",
    "Health",
    "Controller",
    "AIBrain",
    "DimensionAnchor",
    "Entity",
    "System",
    "World",
    "GameEvent",
]
