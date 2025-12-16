from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass, field
from .math_4d import (
    Matrix4D,
    Vector4D,
    create_rotation_matrix_4d,
    create_scale_matrix_4d,
)

@dataclass
class Shape4D(ABC):
    """Abstract base class for all 4D geometric objects.
    
    This class defines the common interface and functionality for all 4D shapes
    in the hypersim project. All 4D shapes should inherit from this class and
    implement the abstract methods.
    """
    
    # Basic properties
    position: Vector4D = field(default_factory=lambda: np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32))
    rotation: Dict[str, float] = field(default_factory=lambda: {
        'xy': 0.0, 'xz': 0.0, 'xw': 0.0,
        'yz': 0.0, 'yw': 0.0, 'zw': 0.0
    })
    scale: float = 1.0
    color: Tuple[int, int, int] = (255, 255, 255)
    line_width: int = 1
    visible: bool = True
    
    # Transformation matrix cache
    _transform_matrix: Optional[Matrix4D] = field(init=False, default=None)
    _transform_dirty: bool = field(init=False, default=True)
    
    # Vertex cache for performance
    _cached_vertices: Optional[List[Vector4D]] = field(init=False, default=None)
    _vertices_dirty: bool = field(init=False, default=True)
    
    # Abstract properties
    @property
    @abstractmethod
    def vertices(self) -> List[Vector4D]:
        """Get the vertices of the shape in local space.
        
        Returns:
            List of 4D vectors representing the vertices.
        """
        pass
    
    @property
    @abstractmethod
    def edges(self) -> List[Tuple[int, int]]:
        """Get the edges of the shape as vertex index pairs.
        
        Returns:
            List of tuples where each tuple contains two vertex indices.
        """
        pass
    
    @property
    @abstractmethod
    def faces(self) -> List[Tuple[int, ...]]:
        """Get the faces of the shape as tuples of vertex indices.
        
        Returns:
            List of tuples where each tuple contains vertex indices forming a face.
        """
        pass
    
    # Common properties with default implementations
    @property
    def vertex_count(self) -> int:
        """Get the number of vertices in the shape."""
        return len(self.vertices)
    
    @property
    def edge_count(self) -> int:
        """Get the number of edges in the shape."""
        return len(self.edges)
    
    @property
    def face_count(self) -> int:
        """Get the number of faces in the shape."""
        return len(self.faces)

    @property
    def cell_count(self) -> int:
        """Get the number of 4D cells in the shape."""
        return len(self.cells)

    # Convenience getters (compat with overlays/UI expecting methods)
    def get_vertex_count(self) -> int:
        """Return vertex count (method form)."""
        return self.vertex_count

    def get_edge_count(self) -> int:
        """Return edge count (method form)."""
        return self.edge_count

    def get_face_count(self) -> int:
        """Return face count (method form)."""
        return self.face_count

    def get_cell_count(self) -> int:
        """Return cell count (method form)."""
        return self.cell_count

    def get_position(self) -> Vector4D:
        """Return current position vector."""
        return self.position
    
    # Transformation methods
    def get_transform_matrix(self) -> Matrix4D:
        """Get the current transformation matrix, computing it if necessary."""
        if self._transform_dirty or self._transform_matrix is None:
            self._update_transform_matrix()
        return self._transform_matrix
    
    def _update_transform_matrix(self) -> None:
        """Update the linear (rotation/scale) portion of the transform matrix.

        Translation is handled separately when applying the transform so we do not
        need to rely on homogeneous coordinates here.
        """
        # Start with identity matrix
        transform = np.eye(4, dtype=np.float32)

        # Apply rotations (order matters!)
        for plane, angle in self.rotation.items():
            if angle != 0:
                rot_args = {
                    'angle_xy': 0.0,
                    'angle_xz': 0.0,
                    'angle_xw': 0.0,
                    'angle_yz': 0.0,
                    'angle_yw': 0.0,
                    'angle_zw': 0.0
                }
                rot_args[f'angle_{plane}'] = angle
                rot_matrix = create_rotation_matrix_4d(**rot_args)
                transform = rot_matrix @ transform

        # Apply uniform scale
        if self.scale != 1.0:
            scale_matrix = create_scale_matrix_4d(
                sx=self.scale,
                sy=self.scale,
                sz=self.scale,
                sw=self.scale
            )
            transform = scale_matrix @ transform

        self._transform_matrix = transform
        self._transform_dirty = False
    
    def set_position(self, x=None, y=None, z=None, w=None, position=None) -> None:
        """Set the position of the shape in 4D space.
        
        Can be called in several ways:
            - set_position(x, y, z, w)
            - set_position(position=[x, y, z, w])
            - set_position([x, y, z, w])
        
        Args:
            x: X coordinate (optional if position is provided)
            y: Y coordinate (optional if position is provided)
            z: Z coordinate (optional if position is provided)
            w: W coordinate (optional if position is provided)
            position: Optional array-like of shape (4,) containing [x, y, z, w] coordinates
        """
        # If first argument is a sequence and no other args are provided, treat it as position
        if (isinstance(x, (list, tuple, np.ndarray)) and 
                y is None and z is None and w is None and position is None):
            position = x
            x = y = z = w = None
            
        if position is not None:
            self.position = np.asarray(position, dtype=np.float32)
        else:
            new_pos = self.position.copy()
            if x is not None:
                new_pos[0] = float(x)
            if y is not None:
                new_pos[1] = float(y)
            if z is not None:
                new_pos[2] = float(z)
            if w is not None:
                new_pos[3] = float(w)
            self.position = new_pos
            
        self._transform_dirty = True
        self._vertices_dirty = True
    
    def translate(self, dx: float, dy: float, dz: float, dw: float) -> None:
        """Translate the shape by the given deltas."""
        self.position += np.array([dx, dy, dz, dw], dtype=np.float32)
        self._transform_dirty = True
        self._vertices_dirty = True
    
    def rotate(self, **rotations: float) -> None:
        """Rotate the shape in one or more planes.
        
        Args:
            **rotations: Keyword arguments where keys are rotation planes ('xy', 'xz', etc.)
                        and values are rotation angles in radians.
        """
        for plane, angle in rotations.items():
            key = plane[6:] if plane.startswith("angle_") else plane
            if key in self.rotation:
                self.rotation[key] = (self.rotation[key] + angle) % (2 * np.pi)
                self._transform_dirty = True
                self._vertices_dirty = True
    
    def set_rotation(self, **rotations: float) -> None:
        """Set the rotation of the shape in one or more planes.
        
        Args:
            **rotations: Keyword arguments where keys are rotation planes ('xy', 'xz', etc.)
                        and values are rotation angles in radians.
        """
        for plane, angle in rotations.items():
            key = plane[6:] if plane.startswith("angle_") else plane
            if key in self.rotation:
                self.rotation[key] = angle % (2 * np.pi)
                self._transform_dirty = True
                self._vertices_dirty = True
    
    def set_scale(self, scale: float) -> None:
        """Set the scale of the shape."""
        self.scale = scale
        self._transform_dirty = True
        self._vertices_dirty = True
    
    def get_transformed_vertices(self) -> List[Vector4D]:
        """Get the vertices transformed by the current transformation matrix.
        
        Results are cached for performance. Cache is invalidated when
        position, rotation, or scale changes.
        """
        if not self._vertices_dirty and self._cached_vertices is not None:
            return self._cached_vertices
        
        transform = self.get_transform_matrix()
        translated = []
        has_position = np.any(self.position)
        for vertex in self.vertices:
            v = transform @ vertex
            if has_position:
                v = v + self.position
            translated.append(v)
        
        self._cached_vertices = translated
        self._vertices_dirty = False
        return translated
    
    def invalidate_cache(self) -> None:
        """Manually invalidate the vertex cache."""
        self._vertices_dirty = True
        self._transform_dirty = True
    
    def get_bounding_box(self) -> Tuple[Vector4D, Vector4D]:
        """Get the axis-aligned bounding box of the shape.
        
        Returns:
            A tuple (min_corner, max_corner) representing the bounding box.
        """
        if not self.vertices:
            return np.zeros(4), np.zeros(4)
            
        vertices = np.array(self.get_transformed_vertices())
        return np.min(vertices, axis=0), np.max(vertices, axis=0)
    
    def is_visible(self, camera_position: Vector4D, fov: float = np.pi/4) -> bool:
        """Check if the shape is potentially visible from the given camera position.
        
        Args:
            camera_position: The position of the camera in 4D space.
            fov: The field of view in radians.
            
        Returns:
            True if the shape is potentially visible, False otherwise.
        """
        if not self.visible:
            return False
            
        # Simple distance-based visibility check
        min_corner, max_corner = self.get_bounding_box()
        center = (min_corner + max_corner) / 2
        extent = max_corner - min_corner
        radius = np.linalg.norm(extent) / 2
        
        distance = np.linalg.norm(center - camera_position)
        return distance - radius < 1.0 / np.tan(fov/2)  # Simplified visibility check

    # Rendering 
    def render(self, renderer: Any) -> None:
        """Default render hook so shapes can be added directly to scenes."""
        render_fn = getattr(renderer, "render_4d_object", None)
        if not callable(render_fn):
            return
        color = getattr(self, "color", (255, 255, 255))
        width = getattr(self, "line_width", 1)
        render_fn(self, color=color, width=width)

    # Optional geometry slots
    @property
    def cells(self) -> List[Tuple[int, ...]]:
        """Return 4D cells; override in subclasses."""
        return []
