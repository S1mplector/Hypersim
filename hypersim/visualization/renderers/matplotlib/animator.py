"""Matplotlib animation support for 4D objects.

Provides tools to create rotating animations and save them as
GIF or video files.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple, Callable
import numpy as np

import matplotlib.pyplot as plt
from matplotlib import animation
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Line3DCollection

if TYPE_CHECKING:
    from hypersim.core.shape_4d import Shape4D

from hypersim.core.math_4d import perspective_projection_4d_to_3d


class MatplotlibAnimator:
    """Create animations of 4D objects using matplotlib.
    
    Supports rotation animations in both 3D view space and 4D object space,
    with export to GIF, MP4, or other video formats.
    """
    
    def __init__(
        self,
        figsize: Tuple[int, int] = (8, 8),
        projection_distance: float = 5.0,
        style: str = "dark_background",
        dpi: int = 100,
    ):
        """Initialize the animator.
        
        Args:
            figsize: Figure size in inches
            projection_distance: Distance for 4D to 3D projection
            style: Matplotlib style
            dpi: Figure DPI
        """
        self.figsize = figsize
        self.projection_distance = projection_distance
        self.style = style
        self.dpi = dpi
    
    def animate_rotation_3d(
        self,
        obj: "Shape4D",
        frames: int = 120,
        interval: int = 50,
        color: str = "cyan",
        linewidth: float = 1.5,
        axis_limit: float = 2.0,
        elevation: float = 20.0,
        title: Optional[str] = None,
    ) -> animation.FuncAnimation:
        """Create a 3D view rotation animation.
        
        Rotates the camera around the object while keeping the 4D
        orientation fixed.
        
        Args:
            obj: The 4D object to animate
            frames: Number of animation frames
            interval: Milliseconds between frames
            color: Line color
            linewidth: Line width
            axis_limit: Axis limits
            elevation: Camera elevation angle
            title: Figure title
            
        Returns:
            matplotlib FuncAnimation object
        """
        if self.style:
            plt.style.use(self.style)
        
        fig = plt.figure(figsize=self.figsize, dpi=self.dpi)
        ax = fig.add_subplot(111, projection='3d')
        
        # Project object to 3D
        vertices_4d = np.array(obj.get_transformed_vertices())
        vertices_3d = perspective_projection_4d_to_3d(
            vertices_4d, self.projection_distance
        )
        
        # Create line segments
        segments = [[vertices_3d[a], vertices_3d[b]] for a, b in obj.edges]
        lines = Line3DCollection(segments, colors=color, linewidths=linewidth)
        ax.add_collection3d(lines)
        
        ax.set_xlim(-axis_limit, axis_limit)
        ax.set_ylim(-axis_limit, axis_limit)
        ax.set_zlim(-axis_limit, axis_limit)
        ax.set_box_aspect([1, 1, 1])
        
        if title:
            ax.set_title(title)
        
        def update(frame):
            azim = 360 * frame / frames
            ax.view_init(elev=elevation, azim=azim)
            return lines,
        
        anim = animation.FuncAnimation(
            fig, update, frames=frames, interval=interval, blit=False
        )
        
        return anim
    
    def animate_rotation_4d(
        self,
        obj: "Shape4D",
        frames: int = 120,
        interval: int = 50,
        color: str = "cyan",
        linewidth: float = 1.5,
        axis_limit: float = 2.0,
        elevation: float = 20.0,
        azimuth: float = 45.0,
        rotation_planes: Optional[dict] = None,
        title: Optional[str] = None,
    ) -> animation.FuncAnimation:
        """Create a 4D rotation animation.
        
        Rotates the object in 4D space while keeping the camera fixed.
        
        Args:
            obj: The 4D object to animate
            frames: Number of animation frames
            interval: Milliseconds between frames
            color: Line color
            linewidth: Line width
            axis_limit: Axis limits
            elevation: Camera elevation
            azimuth: Camera azimuth
            rotation_planes: Dict of rotation speeds per plane
                            e.g., {"xy": 0.05, "xw": 0.03}
            title: Figure title
            
        Returns:
            matplotlib FuncAnimation object
        """
        if rotation_planes is None:
            rotation_planes = {"xy": 0.05, "xw": 0.03, "yw": 0.02}
        
        if self.style:
            plt.style.use(self.style)
        
        fig = plt.figure(figsize=self.figsize, dpi=self.dpi)
        ax = fig.add_subplot(111, projection='3d')
        
        # Initial projection
        vertices_4d = np.array(obj.get_transformed_vertices())
        vertices_3d = perspective_projection_4d_to_3d(
            vertices_4d, self.projection_distance
        )
        
        segments = [[vertices_3d[a], vertices_3d[b]] for a, b in obj.edges]
        lines = Line3DCollection(segments, colors=color, linewidths=linewidth)
        ax.add_collection3d(lines)
        
        ax.set_xlim(-axis_limit, axis_limit)
        ax.set_ylim(-axis_limit, axis_limit)
        ax.set_zlim(-axis_limit, axis_limit)
        ax.set_box_aspect([1, 1, 1])
        ax.view_init(elev=elevation, azim=azimuth)
        
        if title:
            ax.set_title(title)
        
        # Store initial rotation
        initial_rotation = dict(obj.rotation)
        
        def update(frame):
            # Apply 4D rotation
            obj.rotate(**rotation_planes)
            
            # Re-project
            vertices_4d = np.array(obj.get_transformed_vertices())
            vertices_3d = perspective_projection_4d_to_3d(
                vertices_4d, self.projection_distance
            )
            
            # Update segments
            new_segments = [[vertices_3d[a], vertices_3d[b]] for a, b in obj.edges]
            lines.set_segments(new_segments)
            
            return lines,
        
        def reset():
            # Reset rotation when animation restarts
            obj.rotation = dict(initial_rotation)
            obj.invalidate_cache()
        
        anim = animation.FuncAnimation(
            fig, update, frames=frames, interval=interval, blit=False
        )
        
        return anim
    
    def animate_slice(
        self,
        obj: "Shape4D",
        frames: int = 60,
        interval: int = 80,
        color: str = "cyan",
        slice_color: str = "yellow",
        linewidth: float = 1.0,
        slice_linewidth: float = 2.0,
        axis_limit: float = 2.0,
        title: Optional[str] = None,
    ) -> animation.FuncAnimation:
        """Create an animation slicing through 4D along the W axis.
        
        Args:
            obj: The 4D object to slice
            frames: Number of frames
            interval: Milliseconds between frames
            color: Color for full object (faded)
            slice_color: Color for the slice
            linewidth: Line width for full object
            slice_linewidth: Line width for slice
            axis_limit: Axis limits
            title: Figure title
            
        Returns:
            matplotlib FuncAnimation object
        """
        from hypersim.core.slicer import compute_cross_section, compute_w_range
        
        if self.style:
            plt.style.use(self.style)
        
        fig = plt.figure(figsize=self.figsize, dpi=self.dpi)
        ax = fig.add_subplot(111, projection='3d')
        
        # Get W range
        w_min, w_max = compute_w_range(obj)
        
        # Draw faded full object
        vertices_4d = np.array(obj.get_transformed_vertices())
        vertices_3d = perspective_projection_4d_to_3d(
            vertices_4d, self.projection_distance
        )
        segments = [[vertices_3d[a], vertices_3d[b]] for a, b in obj.edges]
        full_lines = Line3DCollection(
            segments, colors=color, linewidths=linewidth, alpha=0.2
        )
        ax.add_collection3d(full_lines)
        
        # Placeholder for slice lines
        slice_lines = Line3DCollection([], colors=slice_color, linewidths=slice_linewidth)
        ax.add_collection3d(slice_lines)
        
        ax.set_xlim(-axis_limit, axis_limit)
        ax.set_ylim(-axis_limit, axis_limit)
        ax.set_zlim(-axis_limit, axis_limit)
        ax.set_box_aspect([1, 1, 1])
        
        if title:
            ax.set_title(title)
        
        def update(frame):
            # Oscillate W value
            t = frame / frames
            w = w_min + (w_max - w_min) * (0.5 + 0.5 * np.sin(2 * np.pi * t))
            
            # Compute cross-section
            cross_section = compute_cross_section(obj, w)
            
            if cross_section.vertices_3d:
                slice_segments = []
                for a, b in cross_section.edges:
                    if a < len(cross_section.vertices_3d) and b < len(cross_section.vertices_3d):
                        slice_segments.append([
                            cross_section.vertices_3d[a],
                            cross_section.vertices_3d[b]
                        ])
                slice_lines.set_segments(slice_segments)
            else:
                slice_lines.set_segments([])
            
            return slice_lines,
        
        anim = animation.FuncAnimation(
            fig, update, frames=frames, interval=interval, blit=False
        )
        
        return anim
    
    def save(
        self,
        anim: animation.FuncAnimation,
        path: str,
        fps: int = 30,
        writer: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Save an animation to file.
        
        Args:
            anim: The animation to save
            path: Output file path (.gif, .mp4, etc.)
            fps: Frames per second
            writer: Animation writer ('pillow' for GIF, 'ffmpeg' for MP4)
            **kwargs: Additional arguments passed to save()
        """
        if writer is None:
            if path.endswith('.gif'):
                writer = 'pillow'
            else:
                writer = 'ffmpeg'
        
        anim.save(path, writer=writer, fps=fps, dpi=self.dpi, **kwargs)
