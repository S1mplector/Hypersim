"""Matplotlib-based 4D renderer implementation.

Provides static rendering of 4D objects projected to 3D, displayed
using matplotlib's 3D plotting capabilities.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple, Union
import numpy as np

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Line3DCollection, Poly3DCollection

if TYPE_CHECKING:
    from hypersim.core.shape_4d import Shape4D

from hypersim.core.math_4d import perspective_projection_4d_to_3d


class MatplotlibRenderer:
    """Matplotlib-based renderer for 4D objects.
    
    This renderer projects 4D objects to 3D and displays them using
    matplotlib's mplot3d toolkit. Suitable for static visualization,
    Jupyter notebooks, and saving publication-quality figures.
    """
    
    def __init__(
        self,
        figsize: Tuple[int, int] = (10, 8),
        projection_distance: float = 5.0,
        style: str = "dark_background",
        dpi: int = 100,
    ):
        """Initialize the matplotlib renderer.
        
        Args:
            figsize: Figure size in inches (width, height)
            projection_distance: Distance for 4D to 3D projection
            style: Matplotlib style to use
            dpi: Figure DPI for rendering
        """
        self.figsize = figsize
        self.projection_distance = projection_distance
        self.style = style
        self.dpi = dpi
        
        self._fig: Optional[plt.Figure] = None
        self._ax: Optional[Axes3D] = None
        self._objects: List[Tuple["Shape4D", dict]] = []
    
    def _setup_figure(self) -> None:
        """Create or reset the figure and axes."""
        if self.style:
            plt.style.use(self.style)
        
        self._fig = plt.figure(figsize=self.figsize, dpi=self.dpi)
        self._ax = self._fig.add_subplot(111, projection='3d')
        self._ax.set_box_aspect([1, 1, 1])
    
    def add_object(
        self,
        obj: "Shape4D",
        color: str = "cyan",
        linewidth: float = 1.0,
        alpha: float = 1.0,
        label: Optional[str] = None,
    ) -> None:
        """Add a 4D object to be rendered.
        
        Args:
            obj: The Shape4D object to render
            color: Line color (matplotlib color string)
            linewidth: Line width for edges
            alpha: Transparency (0-1)
            label: Optional label for legend
        """
        self._objects.append((obj, {
            "color": color,
            "linewidth": linewidth,
            "alpha": alpha,
            "label": label,
        }))
    
    def clear(self) -> None:
        """Clear all objects from the renderer."""
        self._objects.clear()
    
    def _project_object(self, obj: "Shape4D") -> np.ndarray:
        """Project a 4D object to 3D coordinates."""
        vertices_4d = np.array(obj.get_transformed_vertices())
        vertices_3d = perspective_projection_4d_to_3d(
            vertices_4d, self.projection_distance
        )
        return vertices_3d
    
    def render(
        self,
        title: Optional[str] = None,
        show_axes: bool = True,
        axis_limit: float = 2.0,
        elevation: float = 20.0,
        azimuth: float = 45.0,
        show: bool = True,
    ) -> plt.Figure:
        """Render all added objects.
        
        Args:
            title: Optional figure title
            show_axes: Whether to show coordinate axes
            axis_limit: Axis limits (-limit to +limit)
            elevation: Camera elevation angle in degrees
            azimuth: Camera azimuth angle in degrees
            show: Whether to display the figure (set False for saving)
            
        Returns:
            The matplotlib Figure object
        """
        self._setup_figure()
        
        for obj, style in self._objects:
            vertices_3d = self._project_object(obj)
            edges = obj.edges
            
            # Create line segments for edges
            segments = []
            for a, b in edges:
                segments.append([vertices_3d[a], vertices_3d[b]])
            
            if segments:
                lines = Line3DCollection(
                    segments,
                    colors=style["color"],
                    linewidths=style["linewidth"],
                    alpha=style["alpha"],
                    label=style["label"],
                )
                self._ax.add_collection3d(lines)
        
        # Set view and limits
        self._ax.set_xlim(-axis_limit, axis_limit)
        self._ax.set_ylim(-axis_limit, axis_limit)
        self._ax.set_zlim(-axis_limit, axis_limit)
        self._ax.view_init(elev=elevation, azim=azimuth)
        
        if not show_axes:
            self._ax.set_axis_off()
        else:
            self._ax.set_xlabel('X')
            self._ax.set_ylabel('Y')
            self._ax.set_zlabel('Z')
        
        if title:
            self._ax.set_title(title)
        
        # Add legend if any objects have labels
        if any(style.get("label") for _, style in self._objects):
            self._ax.legend()
        
        plt.tight_layout()
        
        if show:
            plt.show()
        
        return self._fig
    
    def render_object(
        self,
        obj: "Shape4D",
        color: str = "cyan",
        linewidth: float = 1.0,
        alpha: float = 1.0,
        title: Optional[str] = None,
        show: bool = True,
        **kwargs,
    ) -> plt.Figure:
        """Convenience method to render a single object.
        
        Args:
            obj: The Shape4D object to render
            color: Line color
            linewidth: Line width
            alpha: Transparency
            title: Figure title
            show: Whether to display
            **kwargs: Additional arguments passed to render()
            
        Returns:
            The matplotlib Figure object
        """
        self.clear()
        self.add_object(obj, color=color, linewidth=linewidth, alpha=alpha)
        return self.render(title=title, show=show, **kwargs)
    
    def render_faces(
        self,
        obj: "Shape4D",
        face_color: str = "cyan",
        edge_color: str = "white",
        alpha: float = 0.3,
        linewidth: float = 0.5,
        title: Optional[str] = None,
        show: bool = True,
        **kwargs,
    ) -> plt.Figure:
        """Render an object with filled faces.
        
        Args:
            obj: The Shape4D object to render
            face_color: Fill color for faces
            edge_color: Edge color
            alpha: Face transparency
            linewidth: Edge line width
            title: Figure title
            show: Whether to display
            **kwargs: Additional arguments
            
        Returns:
            The matplotlib Figure object
        """
        self._setup_figure()
        
        vertices_3d = self._project_object(obj)
        
        if hasattr(obj, 'faces') and obj.faces:
            # Render faces as polygons
            polygons = []
            for face in obj.faces:
                polygon = [vertices_3d[i] for i in face]
                polygons.append(polygon)
            
            if polygons:
                poly_collection = Poly3DCollection(
                    polygons,
                    facecolors=face_color,
                    edgecolors=edge_color,
                    linewidths=linewidth,
                    alpha=alpha,
                )
                self._ax.add_collection3d(poly_collection)
        
        # Also draw edges for clarity
        edges = obj.edges
        segments = [[vertices_3d[a], vertices_3d[b]] for a, b in edges]
        if segments:
            lines = Line3DCollection(
                segments,
                colors=edge_color,
                linewidths=linewidth,
                alpha=1.0,
            )
            self._ax.add_collection3d(lines)
        
        axis_limit = kwargs.get("axis_limit", 2.0)
        self._ax.set_xlim(-axis_limit, axis_limit)
        self._ax.set_ylim(-axis_limit, axis_limit)
        self._ax.set_zlim(-axis_limit, axis_limit)
        self._ax.view_init(
            elev=kwargs.get("elevation", 20.0),
            azim=kwargs.get("azimuth", 45.0)
        )
        
        if not kwargs.get("show_axes", True):
            self._ax.set_axis_off()
        
        if title:
            self._ax.set_title(title)
        
        plt.tight_layout()
        
        if show:
            plt.show()
        
        return self._fig
    
    def save(
        self,
        path: str,
        dpi: Optional[int] = None,
        transparent: bool = False,
        **kwargs,
    ) -> None:
        """Save the current figure to file.
        
        Args:
            path: Output file path (supports png, pdf, svg, etc.)
            dpi: Output DPI (uses figure DPI if not specified)
            transparent: Whether to use transparent background
            **kwargs: Additional arguments passed to savefig()
        """
        if self._fig is None:
            raise RuntimeError("No figure to save. Call render() first.")
        
        self._fig.savefig(
            path,
            dpi=dpi or self.dpi,
            transparent=transparent,
            bbox_inches='tight',
            **kwargs,
        )
    
    def close(self) -> None:
        """Close the figure and free resources."""
        if self._fig is not None:
            plt.close(self._fig)
            self._fig = None
            self._ax = None
