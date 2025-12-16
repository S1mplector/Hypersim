"""Save and load state functionality for HyperSim scenes.

This module provides utilities to serialize and deserialize the state
of 4D objects and scenes, allowing users to save and restore their work.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Type, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from hypersim.core.shape_4d import Shape4D
    from hypersim.engine.scene import Scene


@dataclass
class ObjectState:
    """Serializable state of a 4D object."""
    class_name: str
    module_name: str
    position: List[float]
    rotation: Dict[str, float]
    scale: float
    color: List[int]
    line_width: int
    visible: bool
    init_kwargs: Dict[str, Any]


def serialize_object(obj: "Shape4D") -> ObjectState:
    """Serialize a Shape4D object to a state representation.
    
    Args:
        obj: The 4D object to serialize
        
    Returns:
        ObjectState containing all necessary data to reconstruct the object
    """
    # Get init kwargs from object attributes
    init_kwargs = {}
    
    # Common parameters
    if hasattr(obj, "size"):
        init_kwargs["size"] = obj.size
    if hasattr(obj, "height"):
        init_kwargs["height"] = obj.height
    if hasattr(obj, "radius"):
        init_kwargs["radius"] = obj.radius
    if hasattr(obj, "width"):
        init_kwargs["width"] = obj.width
    if hasattr(obj, "m"):
        init_kwargs["m"] = obj.m
    if hasattr(obj, "n"):
        init_kwargs["n"] = obj.n
    if hasattr(obj, "segments"):
        init_kwargs["segments"] = obj.segments
    if hasattr(obj, "segments_u"):
        init_kwargs["segments_u"] = obj.segments_u
    if hasattr(obj, "segments_v"):
        init_kwargs["segments_v"] = obj.segments_v
    if hasattr(obj, "stacks"):
        init_kwargs["stacks"] = obj.stacks
    if hasattr(obj, "divisions"):
        init_kwargs["divisions"] = obj.divisions
    if hasattr(obj, "p"):
        init_kwargs["p"] = obj.p
    if hasattr(obj, "q"):
        init_kwargs["q"] = obj.q
    
    return ObjectState(
        class_name=obj.__class__.__name__,
        module_name=obj.__class__.__module__,
        position=obj.position.tolist(),
        rotation=dict(obj.rotation),
        scale=obj.scale,
        color=list(obj.color) if hasattr(obj, "color") else [255, 255, 255],
        line_width=obj.line_width if hasattr(obj, "line_width") else 1,
        visible=obj.visible if hasattr(obj, "visible") else True,
        init_kwargs=init_kwargs,
    )


def deserialize_object(state: ObjectState) -> "Shape4D":
    """Deserialize an ObjectState back into a Shape4D object.
    
    Args:
        state: The serialized state
        
    Returns:
        Reconstructed Shape4D object
    """
    import importlib
    
    # Import the class
    module = importlib.import_module(state.module_name)
    cls = getattr(module, state.class_name)
    
    # Create the object
    obj = cls(**state.init_kwargs)
    
    # Restore state
    obj.set_position(state.position)
    obj.rotation = state.rotation
    obj.scale = state.scale
    obj.color = tuple(state.color)
    obj.line_width = state.line_width
    obj.visible = state.visible
    obj.invalidate_cache()
    
    return obj


@dataclass
class SceneState:
    """Serializable state of a scene."""
    objects: List[Dict[str, Any]]
    metadata: Dict[str, Any]


def serialize_scene(scene: "Scene", metadata: Optional[Dict[str, Any]] = None) -> SceneState:
    """Serialize a scene to a state representation.
    
    Args:
        scene: The scene to serialize
        metadata: Optional metadata to include (e.g., camera position, timestamp)
        
    Returns:
        SceneState containing all objects and metadata
    """
    objects = []
    for obj in scene.objects():
        state = serialize_object(obj)
        objects.append(asdict(state))
    
    return SceneState(
        objects=objects,
        metadata=metadata or {}
    )


def deserialize_scene(state: SceneState) -> "Scene":
    """Deserialize a SceneState back into a Scene.
    
    Args:
        state: The serialized scene state
        
    Returns:
        Reconstructed Scene with all objects
    """
    from hypersim.engine.scene import Scene
    
    scene = Scene()
    for obj_data in state.objects:
        obj_state = ObjectState(**obj_data)
        obj = deserialize_object(obj_state)
        scene.add(obj)
    
    return scene


def save_scene(scene: "Scene", path: str | Path, metadata: Optional[Dict[str, Any]] = None) -> None:
    """Save a scene to a JSON file.
    
    Args:
        scene: The scene to save
        path: Path to save the file
        metadata: Optional metadata to include
    """
    path = Path(path)
    state = serialize_scene(scene, metadata)
    
    with open(path, "w") as f:
        json.dump(asdict(state), f, indent=2)


def load_scene(path: str | Path) -> "Scene":
    """Load a scene from a JSON file.
    
    Args:
        path: Path to the scene file
        
    Returns:
        Loaded scene
    """
    path = Path(path)
    
    with open(path, "r") as f:
        data = json.load(f)
    
    state = SceneState(**data)
    return deserialize_scene(state)


def save_object(obj: "Shape4D", path: str | Path) -> None:
    """Save a single object to a JSON file.
    
    Args:
        obj: The object to save
        path: Path to save the file
    """
    path = Path(path)
    state = serialize_object(obj)
    
    with open(path, "w") as f:
        json.dump(asdict(state), f, indent=2)


def load_object(path: str | Path) -> "Shape4D":
    """Load a single object from a JSON file.
    
    Args:
        path: Path to the object file
        
    Returns:
        Loaded object
    """
    path = Path(path)
    
    with open(path, "r") as f:
        data = json.load(f)
    
    state = ObjectState(**data)
    return deserialize_object(state)
