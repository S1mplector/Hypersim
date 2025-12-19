"""YAML-based world/level loader."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
import numpy as np

from hypersim.game.ecs.world import World
from hypersim.game.ecs.entity import Entity
from hypersim.game.ecs.component import (
    Transform, Velocity, Renderable, Collider, ColliderShape,
    Health, Controller, AIBrain, DimensionAnchor, Pickup, Portal
)
from hypersim.game.objectives import ObjectiveSpec, ObjectiveType


@dataclass
class EntityDefinition:
    """Definition for spawning an entity."""
    type: str
    position: List[float]
    params: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class WorldDefinition:
    """Complete world/level definition loaded from YAML."""
    id: str
    dimension: str
    name: str = ""
    description: str = ""
    spawn: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    bounds: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    entities: List[EntityDefinition] = field(default_factory=list)
    objectives: List[ObjectiveSpec] = field(default_factory=list)
    next_world: Optional[str] = None
    music: Optional[str] = None


class WorldLoader:
    """Loads world definitions from YAML files and spawns entities."""
    
    def __init__(self, content_path: Optional[Path] = None):
        if content_path is None:
            # Default to package content directory
            content_path = Path(__file__).parent / "worlds"
        self.content_path = Path(content_path)
        self._cache: Dict[str, WorldDefinition] = {}
        
        # Entity type factories
        self._entity_factories: Dict[str, callable] = {
            "player": self._create_player,
            "enemy": self._create_enemy,
            "pickup": self._create_pickup,
            "portal": self._create_portal,
            "obstacle": self._create_obstacle,
            "trigger": self._create_trigger,
        }
    
    def load(self, world_id: str) -> WorldDefinition:
        """Load a world definition by ID."""
        if world_id in self._cache:
            return self._cache[world_id]
        
        # Try to find the YAML file
        yaml_path = self.content_path / f"{world_id}.yaml"
        if not yaml_path.exists():
            yaml_path = self.content_path / f"{world_id}.yml"
        
        if not yaml_path.exists():
            raise FileNotFoundError(f"World definition not found: {world_id}")
        
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        world_def = self._parse_world(data)
        self._cache[world_id] = world_def
        return world_def
    
    def _parse_world(self, data: Dict[str, Any]) -> WorldDefinition:
        """Parse raw YAML data into a WorldDefinition."""
        world_data = data.get("world", {})
        
        # Parse entities
        entities = []
        for ent_data in data.get("entities", []):
            entities.append(EntityDefinition(
                type=ent_data.get("type", "obstacle"),
                position=ent_data.get("position", [0.0]),
                params=ent_data.get("params", {}),
                tags=ent_data.get("tags", []),
            ))
        
        # Parse objectives
        objectives = []
        for obj_data in data.get("objectives", []):
            obj_type = ObjectiveType(obj_data.get("type", "custom_event"))
            objectives.append(ObjectiveSpec(
                id=obj_data.get("id", "objective"),
                type=obj_type,
                target=float(obj_data.get("target", 1.0)),
                description=obj_data.get("description", ""),
                params=obj_data.get("params", {}),
            ))
        
        # Parse bounds
        bounds = {}
        for axis, bound in world_data.get("bounds", {}).items():
            if isinstance(bound, list) and len(bound) == 2:
                bounds[axis] = (float(bound[0]), float(bound[1]))
        
        return WorldDefinition(
            id=world_data.get("id", "unknown"),
            dimension=world_data.get("dimension", "1d"),
            name=world_data.get("name", ""),
            description=world_data.get("description", ""),
            spawn=world_data.get("spawn", [0.0, 0.0, 0.0, 0.0]),
            bounds=bounds,
            entities=entities,
            objectives=objectives,
            next_world=world_data.get("next_world"),
            music=world_data.get("music"),
        )
    
    def spawn_world(self, world_def: WorldDefinition, game_world: World) -> Entity:
        """Spawn all entities from a world definition into a game world.
        
        Returns:
            The player entity
        """
        dimension = world_def.dimension
        
        # Spawn player at spawn point
        spawn_pos = np.array(world_def.spawn + [0.0] * (4 - len(world_def.spawn)))
        player = self._create_player(dimension, spawn_pos, {})
        game_world.spawn(player)
        
        # Spawn all other entities
        for ent_def in world_def.entities:
            entity = self._create_entity(ent_def, dimension)
            if entity:
                game_world.spawn(entity)
        
        return player
    
    def _create_entity(self, ent_def: EntityDefinition, dimension: str) -> Optional[Entity]:
        """Create an entity from its definition."""
        factory = self._entity_factories.get(ent_def.type)
        if not factory:
            print(f"Warning: Unknown entity type '{ent_def.type}'")
            return None
        
        # Pad position to 4D
        pos = np.array(ent_def.position + [0.0] * (4 - len(ent_def.position)))
        
        entity = factory(dimension, pos, ent_def.params)
        
        # Add custom tags
        for tag in ent_def.tags:
            entity.tag(tag)
        
        return entity
    
    def _create_player(self, dimension: str, position: np.ndarray, params: Dict) -> Entity:
        """Create a player entity."""
        controller_map = {
            "1d": "line", "2d": "plane", "3d": "volume", "4d": "hyper"
        }
        collider_map = {
            "1d": ColliderShape.SEGMENT,
            "2d": ColliderShape.CIRCLE,
            "3d": ColliderShape.SPHERE,
            "4d": ColliderShape.SPHERE,
        }
        
        player = Entity(id="player")
        player.add(Transform(position=position.copy()))
        player.add(Velocity())
        player.add(Renderable(color=params.get("color", (80, 200, 255)), glow=1.0))
        player.add(Collider(
            shape=collider_map.get(dimension, ColliderShape.CIRCLE),
            size=np.array([params.get("size", 0.5)]),
        ))
        player.add(Health(
            current=params.get("health", 100),
            max=params.get("max_health", 100),
        ))
        player.add(Controller(
            controller_type=controller_map.get(dimension, "plane"),
            speed=params.get("speed", 8.0),
        ))
        player.add(DimensionAnchor(dimension_id=dimension))
        player.tag("player", "controllable")
        
        return player
    
    def _create_enemy(self, dimension: str, position: np.ndarray, params: Dict) -> Entity:
        """Create an enemy entity."""
        collider_map = {
            "1d": ColliderShape.SEGMENT,
            "2d": ColliderShape.CIRCLE,
            "3d": ColliderShape.SPHERE,
            "4d": ColliderShape.SPHERE,
        }
        
        enemy_id = params.get("id", f"enemy_{id(params)}")
        behavior = params.get("behavior", "idle")
        
        # Parse patrol points if provided
        patrol_points = []
        for pt in params.get("patrol_points", []):
            patrol_points.append(np.array(pt + [0.0] * (4 - len(pt))))
        
        enemy = Entity(id=enemy_id)
        enemy.add(Transform(position=position.copy()))
        enemy.add(Velocity())
        enemy.add(Renderable(color=params.get("color", (200, 50, 50))))
        enemy.add(Collider(
            shape=collider_map.get(dimension, ColliderShape.CIRCLE),
            size=np.array([params.get("size", 0.6)]),
        ))
        enemy.add(Health(
            current=params.get("health", 50),
            max=params.get("max_health", 50),
        ))
        enemy.add(AIBrain(
            behavior=behavior,
            patrol_points=patrol_points,
            detect_range=params.get("detect_range", 10.0),
            attack_range=params.get("attack_range", 2.0),
            state={
                "speed": params.get("speed", 3.0),
                "center": position[0],
                "amplitude": params.get("amplitude", 3.0),
                "direction": 1,
            },
        ))
        enemy.add(DimensionAnchor(dimension_id=dimension))
        enemy.tag("enemy")
        
        return enemy
    
    def _create_pickup(self, dimension: str, position: np.ndarray, params: Dict) -> Entity:
        """Create a pickup entity."""
        collider_map = {
            "1d": ColliderShape.SEGMENT,
            "2d": ColliderShape.CIRCLE,
            "3d": ColliderShape.SPHERE,
            "4d": ColliderShape.SPHERE,
        }
        
        pickup_id = params.get("id", f"pickup_{id(params)}")
        
        pickup = Entity(id=pickup_id)
        pickup.add(Transform(position=position.copy()))
        pickup.add(Renderable(color=params.get("color", (255, 220, 50))))
        pickup.add(Collider(
            shape=collider_map.get(dimension, ColliderShape.CIRCLE),
            size=np.array([params.get("size", 0.4)]),
            is_trigger=True,
        ))
        pickup.add(Pickup(
            item_type=params.get("item", "energy"),
            item_id=params.get("item_id", ""),
            value=params.get("value", 1),
        ))
        pickup.add(DimensionAnchor(dimension_id=dimension))
        pickup.tag("pickup")
        
        return pickup
    
    def _create_portal(self, dimension: str, position: np.ndarray, params: Dict) -> Entity:
        """Create a portal entity."""
        collider_map = {
            "1d": ColliderShape.SEGMENT,
            "2d": ColliderShape.CIRCLE,
            "3d": ColliderShape.SPHERE,
            "4d": ColliderShape.SPHERE,
        }
        
        portal_id = params.get("id", f"portal_{id(params)}")
        
        portal = Entity(id=portal_id)
        portal.add(Transform(position=position.copy()))
        portal.add(Renderable(color=params.get("color", (150, 50, 255))))
        portal.add(Collider(
            shape=collider_map.get(dimension, ColliderShape.CIRCLE),
            size=np.array([params.get("size", 1.0)]),
            is_trigger=True,
        ))
        portal.add(Portal(
            target_dimension=params.get("target_dimension", ""),
            target_world=params.get("target_world", ""),
            target_position=np.array(params["target_position"]) if "target_position" in params else None,
            requires_key=params.get("requires_key"),
            active=params.get("active", True),
        ))
        portal.add(DimensionAnchor(dimension_id=dimension))
        portal.tag("portal")
        
        return portal
    
    def _create_obstacle(self, dimension: str, position: np.ndarray, params: Dict) -> Entity:
        """Create a static obstacle entity."""
        collider_map = {
            "1d": ColliderShape.SEGMENT,
            "2d": ColliderShape.AABB,
            "3d": ColliderShape.AABB,
            "4d": ColliderShape.AABB,
        }
        
        obstacle_id = params.get("id", f"obstacle_{id(params)}")
        size = params.get("size", [1.0])
        if isinstance(size, (int, float)):
            size = [size]
        
        obstacle = Entity(id=obstacle_id)
        obstacle.add(Transform(position=position.copy()))
        obstacle.add(Renderable(
            color=params.get("color", (100, 100, 100)),
            visible=params.get("visible", True),
        ))
        obstacle.add(Collider(
            shape=collider_map.get(dimension, ColliderShape.AABB),
            size=np.array(size),
            is_trigger=False,
        ))
        obstacle.add(DimensionAnchor(dimension_id=dimension))
        obstacle.tag("obstacle")
        
        return obstacle
    
    def _create_trigger(self, dimension: str, position: np.ndarray, params: Dict) -> Entity:
        """Create an invisible trigger zone."""
        collider_map = {
            "1d": ColliderShape.SEGMENT,
            "2d": ColliderShape.AABB,
            "3d": ColliderShape.AABB,
            "4d": ColliderShape.AABB,
        }
        
        trigger_id = params.get("id", f"trigger_{id(params)}")
        size = params.get("size", [2.0])
        if isinstance(size, (int, float)):
            size = [size]
        
        trigger = Entity(id=trigger_id)
        trigger.add(Transform(position=position.copy()))
        trigger.add(Renderable(visible=False))
        trigger.add(Collider(
            shape=collider_map.get(dimension, ColliderShape.AABB),
            size=np.array(size),
            is_trigger=True,
        ))
        trigger.add(DimensionAnchor(dimension_id=dimension))
        trigger.tag("trigger", params.get("trigger_type", "generic"))
        
        return trigger
    
    def register_entity_type(self, type_name: str, factory: callable) -> None:
        """Register a custom entity type factory."""
        self._entity_factories[type_name] = factory
