"""Pygame renderer package for 3D/4D visualization.

This package provides a Pygame-based renderer for 3D and 4D graphics. The main
entry point is the :class:`PygameRenderer` class, which manages the rendering
window, camera, and scene graph.

Basic usage::

    from hypersim.visualization.renderers.pygame import PygameRenderer, Color
    from hypersim.core.math_4d import create_vector_4d

    # Create a renderer
    renderer = PygameRenderer(800, 600, "4D Scene")
    
    # Add objects to the scene
    class MyObject:
        def render(self, renderer):
            start = create_vector_4d(0, 0, 0, 0)
            end = create_vector_4d(1, 1, 1, 1)
            renderer.draw_line_4d(start, end, Color(255, 0, 0))
    
    renderer.add_object(MyObject())
    
    # Run the render loop
    renderer.run()

For the improved renderer with more features::

    from hypersim.visualization.renderers.pygame import Renderer, RendererConfig, RenderMode

The implementation is organized into several submodules:

- :mod:`.core`: Core rendering components (renderer, camera, shaders)
- :mod:`.graphics`: Graphics-related components (colors, primitives, scene)
- :mod:`.input`: Input handling
- :mod:`.ui`: User interface components
- :mod:`.utils`: Utility functions
"""

from __future__ import annotations

from .graphics.color import Color
from .core.renderer import PygameRenderer

# New improved renderer components
from .renderer_v2 import Renderer, RendererConfig, PygameRendererV2
from .render_pipeline import RenderPipeline, RenderStyle, RenderMode, RenderStats
from .camera_4d import Camera4D
from .hud import HUD, HUDStyle, Anchor
from .input_manager import InputManager, InputAction
from .face_renderer import FaceRenderer
from .stereo import StereoRenderer, StereoMode

__all__: list[str] = [
    # Legacy
    "Color",
    "PygameRenderer",
    # New renderer
    "Renderer",
    "RendererConfig",
    "PygameRendererV2",
    # Pipeline
    "RenderPipeline",
    "RenderStyle",
    "RenderMode",
    "RenderStats",
    # Camera
    "Camera4D",
    # HUD
    "HUD",
    "HUDStyle",
    "Anchor",
    # Input
    "InputManager",
    "InputAction",
    # Face rendering
    "FaceRenderer",
    # Stereo
    "StereoRenderer",
    "StereoMode",
]
