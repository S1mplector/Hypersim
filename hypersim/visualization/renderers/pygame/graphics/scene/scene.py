"""Scene management for the Pygame renderer.

This module provides the Scene class which manages a collection of renderable
objects and handles the rendering process.
"""

from __future__ import annotations

from typing import List, Any, Optional, Protocol, runtime_checkable
import numpy as np

from ...graphics.color import Color

__all__ = ["Scene", "Renderable"]


@runtime_checkable
class Renderable(Protocol):
    """Protocol for objects that can be rendered.
    
    Any object that implements the render() method can be added to a Scene.
    """
    def render(self, renderer: Any) -> None:
        """Render the object using the provided renderer.
        
        Args:
            renderer: The renderer to use for drawing
        """
        ...


class Scene:
    """Manages a collection of renderable objects and handles rendering."""
    
    def __init__(self, background_color: Color = Color(0, 0, 0)) -> None:
        """Initialize the scene with a background color.
        
        Args:
            background_color: The background color of the scene
        """
        self.background_color = background_color
        self.objects: List[Renderable] = []
        self.zbuffer: Optional[np.ndarray] = None
    
    def add_object(self, obj: Renderable) -> None:
        """Add a renderable object to the scene.
        
        Args:
            obj: The object to add (must implement the Renderable protocol)
        """
        self.objects.append(obj)
    
    def remove_object(self, obj: Renderable) -> None:
        """Remove a renderable object from the scene.
        
        Args:
            obj: The object to remove
        """
        if obj in self.objects:
            self.objects.remove(obj)
    
    def clear(self) -> None:
        """Remove all objects from the scene."""
        self.objects.clear()
    
    def update(self, dt: float) -> None:
        """Update all objects in the scene.
        
        Args:
            dt: Time since last update in seconds
        """
        for obj in self.objects:
            if hasattr(obj, 'update'):
                obj.update(dt)
    
    def render(self, renderer: Any) -> None:
        """Render all objects in the scene.
        
        Args:
            renderer: The renderer to use for drawing
        """
        # Clear the screen and z-buffer
        renderer.clear()
        
        # Render all objects
        for obj in self.objects:
            render_fn = getattr(obj, "render", None)
            if callable(render_fn):
                render_fn(renderer)
            elif hasattr(renderer, "render_4d_object") and hasattr(obj, "get_transformed_vertices"):
                # Fallback for simple wireframe objects that expose vertices/edges
                renderer.render_4d_object(obj)
