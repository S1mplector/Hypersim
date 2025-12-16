"""Improved Pygame renderer with modern architecture.

This is the next-generation renderer for HyperSim, featuring:
- Proper 4D camera system
- Multiple render modes (wireframe, solid, depth-colored)
- Configurable input handling
- HUD system for stats and controls
- Performance optimizations
- Post-processing effects support
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, List, Optional, Dict, Any, Tuple, Callable
import numpy as np
import pygame

if TYPE_CHECKING:
    from hypersim.core.shape_4d import Shape4D

from .camera_4d import Camera4D
from .render_pipeline import RenderPipeline, RenderStyle, RenderMode, RenderStats
from .hud import HUD, Anchor, HUDStyle
from .input_manager import InputManager, InputAction


@dataclass
class RendererConfig:
    """Configuration for the renderer."""
    width: int = 1024
    height: int = 768
    title: str = "HyperSim"
    background_color: Tuple[int, int, int] = (8, 8, 16)
    target_fps: int = 60
    vsync: bool = True
    
    # Camera defaults
    camera_distance: float = 5.0
    projection_scale: float = 150.0
    w_perspective: float = 0.3
    
    # Rendering defaults
    default_render_mode: RenderMode = RenderMode.WIREFRAME
    default_line_width: int = 2
    default_color: Tuple[int, int, int] = (100, 200, 255)
    depth_sorting: bool = True
    
    # Animation
    auto_spin: bool = True
    spin_speeds: Dict[str, float] = field(default_factory=lambda: {
        "xy": 0.4, "xw": 0.6, "yw": 0.5, "zw": 0.3
    })
    
    # UI
    show_fps: bool = True
    show_stats: bool = False
    show_help_on_start: bool = False


class Renderer:
    """Modern 4D renderer with full feature set.
    
    This renderer provides a complete solution for visualizing 4D objects
    with support for multiple render modes, proper depth handling,
    configurable controls, and a HUD system.
    """
    
    def __init__(self, config: Optional[RendererConfig] = None):
        """Initialize the renderer.
        
        Args:
            config: Optional configuration, uses defaults if not provided
        """
        self.config = config or RendererConfig()
        
        # Initialize Pygame
        pygame.init()
        pygame.display.set_caption(self.config.title)
        
        flags = pygame.DOUBLEBUF | pygame.HWSURFACE
        self.screen = pygame.display.set_mode(
            (self.config.width, self.config.height),
            flags
        )
        
        # Core systems
        self.camera = Camera4D(
            screen_width=self.config.width,
            screen_height=self.config.height,
            projection_distance=self.config.camera_distance,
            scale=self.config.projection_scale,
            w_perspective_factor=self.config.w_perspective,
        )
        
        self.pipeline = RenderPipeline(self.screen, self.camera)
        self.pipeline.default_style = RenderStyle(
            mode=self.config.default_render_mode,
            color=self.config.default_color,
            line_width=self.config.default_line_width,
        )
        
        self.hud = HUD(self.screen)
        self.input = InputManager()
        
        # Scene management
        self._objects: List[Tuple["Shape4D", RenderStyle]] = []
        self._object_styles: Dict[int, RenderStyle] = {}
        
        # State
        self._running = False
        self._paused = False
        self._auto_spin = self.config.auto_spin
        self._current_mode = self.config.default_render_mode
        self._show_stats = self.config.show_stats
        self._show_help = self.config.show_help_on_start
        
        # Performance tracking
        self.clock = pygame.time.Clock()
        self._fps = 0.0
        self._frame_count = 0
        self._last_fps_update = pygame.time.get_ticks()
        self._last_stats = RenderStats()
        
        # Set up input callbacks
        self._setup_input_callbacks()
        
        # Set up HUD
        self._setup_hud()
    
    def _setup_input_callbacks(self) -> None:
        """Configure input action callbacks."""
        # One-shot actions
        self.input.on_action(InputAction.QUIT, self._on_quit)
        self.input.on_action(InputAction.RESET_VIEW, self._on_reset_view)
        self.input.on_action(InputAction.TOGGLE_SPIN, self._on_toggle_spin)
        self.input.on_action(InputAction.TOGGLE_FACES, self._on_toggle_render_mode)
        self.input.on_action(InputAction.TOGGLE_INFO, self._on_toggle_stats)
        self.input.on_action(InputAction.ZOOM_IN, lambda: self.camera.zoom(1 / self.camera.zoom_speed))
        self.input.on_action(InputAction.ZOOM_OUT, lambda: self.camera.zoom(self.camera.zoom_speed))
        
        # Continuous actions
        self.input.on_continuous(InputAction.CAMERA_FORWARD, lambda dt: self.camera.move(0, 0, dt * 2, 0))
        self.input.on_continuous(InputAction.CAMERA_BACKWARD, lambda dt: self.camera.move(0, 0, -dt * 2, 0))
        self.input.on_continuous(InputAction.CAMERA_LEFT, lambda dt: self.camera.move(-dt * 2, 0, 0, 0))
        self.input.on_continuous(InputAction.CAMERA_RIGHT, lambda dt: self.camera.move(dt * 2, 0, 0, 0))
        self.input.on_continuous(InputAction.CAMERA_UP, lambda dt: self.camera.move(0, dt * 2, 0, 0))
        self.input.on_continuous(InputAction.CAMERA_DOWN, lambda dt: self.camera.move(0, -dt * 2, 0, 0))
        self.input.on_continuous(InputAction.CAMERA_W_POSITIVE, lambda dt: self.camera.move_w(dt * 2))
        self.input.on_continuous(InputAction.CAMERA_W_NEGATIVE, lambda dt: self.camera.move_w(-dt * 2))
    
    def _setup_hud(self) -> None:
        """Configure HUD elements."""
        if self.config.show_fps:
            self.hud.add_element(
                "fps",
                lambda: f"FPS: {self._fps:.0f}",
                anchor=Anchor.TOP_RIGHT,
                style=HUDStyle(font_size=16, color=(150, 200, 150), background_color=None),
            )
    
    def _on_quit(self) -> None:
        """Handle quit action."""
        self._running = False
    
    def _on_reset_view(self) -> None:
        """Handle reset view action."""
        self.camera.reset()
    
    def _on_toggle_spin(self) -> None:
        """Handle toggle spin action."""
        self._auto_spin = not self._auto_spin
    
    def _on_toggle_render_mode(self) -> None:
        """Cycle through render modes."""
        modes = [RenderMode.WIREFRAME, RenderMode.DEPTH_COLORED, RenderMode.SOLID, RenderMode.POINTS]
        try:
            idx = modes.index(self._current_mode)
            self._current_mode = modes[(idx + 1) % len(modes)]
        except ValueError:
            self._current_mode = RenderMode.WIREFRAME
        
        # Update all object styles
        self.pipeline.default_style.mode = self._current_mode
        for obj_id in self._object_styles:
            self._object_styles[obj_id].mode = self._current_mode
    
    def _on_toggle_stats(self) -> None:
        """Toggle stats display."""
        self._show_stats = not self._show_stats
        self.hud.toggle_stats()
    
    # Public API
    
    def add_object(
        self,
        obj: "Shape4D",
        style: Optional[RenderStyle] = None,
    ) -> None:
        """Add an object to the scene.
        
        Args:
            obj: Shape4D object to add
            style: Optional render style
        """
        obj_style = style or RenderStyle(
            mode=self._current_mode,
            color=getattr(obj, 'color', self.config.default_color),
            line_width=getattr(obj, 'line_width', self.config.default_line_width),
        )
        self._objects.append((obj, obj_style))
        self._object_styles[id(obj)] = obj_style
    
    def remove_object(self, obj: "Shape4D") -> bool:
        """Remove an object from the scene.
        
        Args:
            obj: Object to remove
            
        Returns:
            True if object was removed
        """
        for i, (o, _) in enumerate(self._objects):
            if o is obj:
                self._objects.pop(i)
                self._object_styles.pop(id(obj), None)
                return True
        return False
    
    def clear_objects(self) -> None:
        """Remove all objects from the scene."""
        self._objects.clear()
        self._object_styles.clear()
    
    def set_object_style(self, obj: "Shape4D", style: RenderStyle) -> None:
        """Set the render style for a specific object.
        
        Args:
            obj: Object to update
            style: New render style
        """
        obj_id = id(obj)
        if obj_id in self._object_styles:
            self._object_styles[obj_id] = style
            for i, (o, _) in enumerate(self._objects):
                if o is obj:
                    self._objects[i] = (obj, style)
                    break
    
    def set_render_mode(self, mode: RenderMode) -> None:
        """Set the global render mode.
        
        Args:
            mode: New render mode
        """
        self._current_mode = mode
        self.pipeline.default_style.mode = mode
        for obj_id in self._object_styles:
            self._object_styles[obj_id].mode = mode
    
    @property
    def objects(self) -> List["Shape4D"]:
        """Get list of objects in the scene."""
        return [obj for obj, _ in self._objects]
    
    @property
    def auto_spin(self) -> bool:
        """Get auto-spin state."""
        return self._auto_spin
    
    @auto_spin.setter
    def auto_spin(self, value: bool) -> None:
        """Set auto-spin state."""
        self._auto_spin = value
    
    # Rendering methods
    
    def clear(self) -> None:
        """Clear the screen."""
        self.screen.fill(self.config.background_color)
    
    def render_object(
        self,
        obj: "Shape4D",
        color: Optional[Tuple[int, int, int]] = None,
        width: int = 2,
        mode: Optional[RenderMode] = None,
    ) -> None:
        """Render a single object.
        
        Args:
            obj: Object to render
            color: Optional color override
            width: Line width
            mode: Optional render mode override
        """
        style = RenderStyle(
            mode=mode or self._current_mode,
            color=color or self.config.default_color,
            line_width=width,
        )
        self.pipeline.render_object(obj, style)
    
    def render_4d_object(
        self,
        obj: "Shape4D",
        color: Any = None,
        width: int = 2,
    ) -> None:
        """Render a 4D object (compatibility method).
        
        Args:
            obj: Object to render
            color: Color (tuple or Color object)
            width: Line width
        """
        if hasattr(color, 'to_tuple'):
            color = color.to_tuple()[:3]
        elif color is None:
            color = self.config.default_color
        
        self.render_object(obj, color=color, width=width)
    
    def draw_line_4d(
        self,
        start: np.ndarray,
        end: np.ndarray,
        color: Any,
        width: int = 2,
    ) -> None:
        """Draw a 4D line.
        
        Args:
            start: Start point (4D)
            end: End point (4D)
            color: Line color
            width: Line width
        """
        if hasattr(color, 'to_tuple'):
            color = color.to_tuple()[:3]
        
        p1 = self.camera.project_4d_to_2d(np.asarray(start))
        p2 = self.camera.project_4d_to_2d(np.asarray(end))
        
        pygame.draw.line(
            self.screen,
            color,
            (p1[0], p1[1]),
            (p2[0], p2[1]),
            width
        )
    
    # Main loop methods
    
    def handle_events(self) -> bool:
        """Process input events.
        
        Returns:
            False if should quit, True otherwise
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Mouse orbit
            if event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:
                    dx, dy = event.rel
                    self.camera.orbit(dx * 0.01, -dy * 0.01)
            
            # Mouse zoom
            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.camera.zoom(1 / 1.1)
                else:
                    self.camera.zoom(1.1)
            
            # Help toggle
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:
                    self._show_help = not self._show_help
                    self.hud.toggle_help()
        
        return self._running
    
    def update(self, dt: float) -> None:
        """Update the scene.
        
        Args:
            dt: Delta time in seconds
        """
        # Clamp dt to avoid huge jumps
        dt = min(dt, 0.1)
        
        # Update input
        self.input.update(dt)
        
        # Update FPS counter
        self._frame_count += 1
        now = pygame.time.get_ticks()
        if now - self._last_fps_update > 500:
            self._fps = self._frame_count * 1000.0 / (now - self._last_fps_update)
            self._frame_count = 0
            self._last_fps_update = now
        
        # Auto-spin objects
        if self._auto_spin:
            speeds = self.config.spin_speeds
            for obj, _ in self._objects:
                if hasattr(obj, 'rotate'):
                    obj.rotate(
                        xy=speeds.get('xy', 0) * dt,
                        xw=speeds.get('xw', 0) * dt,
                        yw=speeds.get('yw', 0) * dt,
                        zw=speeds.get('zw', 0) * dt,
                    )
        
        # Update objects that have update methods
        for obj, _ in self._objects:
            if hasattr(obj, 'update'):
                obj.update(dt)
    
    def render(self) -> None:
        """Render the current frame."""
        self.clear()
        
        # Begin render pass
        self.pipeline.begin_frame()
        
        # Queue all objects
        for obj, style in self._objects:
            self.pipeline.queue_object(obj, style)
        
        # Render and get stats
        self._last_stats = self.pipeline.render_frame()
        
        # Render HUD
        stats = {
            'vertices': self._last_stats.vertices_processed,
            'edges': self._last_stats.edges_rendered,
            'objects': self._last_stats.objects_rendered,
            'render_ms': self._last_stats.render_time_ms,
        }
        self.hud.render(fps=self._fps, stats=stats if self._show_stats else None)
        
        # Flip display
        pygame.display.flip()
    
    def run(self, target_fps: Optional[int] = None) -> None:
        """Run the main render loop.
        
        Args:
            target_fps: Optional FPS override
        """
        fps = target_fps or self.config.target_fps
        self._running = True
        last_time = pygame.time.get_ticks() / 1000.0
        
        while self._running:
            # Calculate delta time
            now = pygame.time.get_ticks() / 1000.0
            dt = now - last_time
            last_time = now
            
            # Handle events
            if not self.handle_events():
                break
            
            # Update and render
            self.update(dt)
            self.render()
            
            # Cap framerate
            self.clock.tick(fps)
        
        pygame.quit()
    
    # Compatibility methods for old API
    
    def render_hypercube(self, obj: Any, color: Any = None, width: int = 2) -> None:
        """Render a hypercube (compatibility)."""
        self.render_4d_object(obj, color, width)
    
    def render_simplex(self, obj: Any, color: Any = None, width: int = 2) -> None:
        """Render a simplex (compatibility)."""
        self.render_4d_object(obj, color, width)


# Convenience alias
PygameRendererV2 = Renderer
