"""16-cell (hyperoctahedron) implementation."""
import math
import numpy as np
from typing import List, Tuple, Optional, Dict, Any

from ..core.math_4d import Vector4D, Matrix4D
from ..core.shape_4d import Shape4D

class SixteenCell(Shape4D):
    """A 16-cell (4D hyperoctahedron) implementation.
    
    The 16-cell is the 4D analog of the octahedron, with 8 vertices and 24 edges.
    It's one of the six convex regular 4-polytopes.
    """
    
    def __init__(self, size: float = 1.0, **kwargs):
        """Initialize a 16-cell with the given size.
        
        Args:
            size: The size (edge length) of the 16-cell
            **kwargs: Additional arguments to pass to Shape4D
        """
        super().__init__(**kwargs)
        self.size = size
        
        # Define the 8 vertices of a 16-cell (all permutations of (±1, 0, 0, 0))
        self._base_vertices = [
            np.array([1, 0, 0, 0], dtype=np.float32),
            np.array([-1, 0, 0, 0], dtype=np.float32),  # ±x
            np.array([0, 1, 0, 0], dtype=np.float32),
            np.array([0, -1, 0, 0], dtype=np.float32),  # ±y
            np.array([0, 0, 1, 0], dtype=np.float32),
            np.array([0, 0, -1, 0], dtype=np.float32),  # ±z
            np.array([0, 0, 0, 1], dtype=np.float32),
            np.array([0, 0, 0, -1], dtype=np.float32)   # ±w
        ]
        
        # Scale the vertices so the edge length ≈ size (base edge length is sqrt(2))
        scale = size / math.sqrt(2.0)
        self._base_vertices = [v * scale for v in self._base_vertices]
        
        # Define edges (each vertex connects to all others except its opposite)
        self._edges = [
            (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7),  # From +x
            (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),  # From -x
            (2, 4), (2, 5), (2, 6), (2, 7),                  # From +y
            (3, 4), (3, 5), (3, 6), (3, 7),                  # From -y
            (4, 6), (4, 7),                                  # From +z
            (5, 6), (5, 7),                                  # From -z
            # Note: The last edge (6,7) would connect the two W-axis vertices, but they don't connect in a 16-cell
        ]
        
        # Define triangular faces (8 regular octahedra)
        self._faces = [
            # Faces in the 3D subspaces (8 octahedra)
            (0, 2, 4), (0, 2, 5), (0, 3, 4), (0, 3, 5),  # +x octahedron
            (1, 2, 4), (1, 2, 5), (1, 3, 4), (1, 3, 5),  # -x octahedron
            (0, 2, 6), (0, 2, 7), (0, 3, 6), (0, 3, 7),  # +y octahedron
            (1, 2, 6), (1, 2, 7), (1, 3, 6), (1, 3, 7),  # -y octahedron
            (0, 4, 6), (0, 4, 7), (0, 5, 6), (0, 5, 7),  # +z octahedron
            (1, 4, 6), (1, 4, 7), (1, 5, 6), (1, 5, 7),  # -z octahedron
            (2, 4, 6), (2, 4, 7), (2, 5, 6), (2, 5, 7),  # +w octahedron
            (3, 4, 6), (3, 4, 7), (3, 5, 6), (3, 5, 7)   # -w octahedron
        ]
        
        # Define cells (8 octahedra)
        self._cells = [
            # Each cell is an octahedron formed by 6 vertices
            (0, 1, 2, 3, 4, 5),  # XY plane
            (0, 1, 2, 3, 6, 7),  # XW plane
            (0, 1, 4, 5, 6, 7),  # XZ plane
            (2, 3, 4, 5, 6, 7),  # YZW space
            (0, 2, 4, 6, 1, 3),  # XYW space
            (0, 2, 5, 7, 1, 3),  # XYW space (other diagonal)
            (0, 3, 4, 7, 1, 2),  # XZW space
            (0, 3, 5, 6, 1, 2)   # XZW space (other diagonal)
        ]
    
    @property
    def vertices(self) -> List[Vector4D]:
        """Get the vertices of the 16-cell in local space."""
        return self._base_vertices
    
    @property
    def edges(self) -> List[Tuple[int, int]]:
        """Get the edges of the 16-cell as vertex index pairs."""
        return self._edges
    
    @property
    def faces(self) -> List[Tuple[int, ...]]:
        """Get the triangular faces of the 16-cell as tuples of vertex indices."""
        return self._faces
    
    @property
    def cells(self) -> List[Tuple[int, ...]]:
        """Get the octahedral cells of the 16-cell as tuples of vertex indices."""
        return self._cells
    
    def get_transformed_vertices(self) -> np.ndarray:
        """Get the vertices after applying transformations and position offset.
        
        Returns:
            Array of shape (8, 4) containing the transformed vertex coordinates
        """
        # Use the parent class's method to transform vertices
        return np.array(super().get_transformed_vertices())
    
    def update(self, dt: float) -> None:
        """Update the 16-cell (can be used for animations).
        
        Args:
            dt: Delta time since last update
        """
        # Apply a gentle rotation for visual interest
        self.rotate(xy=0.3 * dt, zw=0.2 * dt, yw=0.15 * dt, xw=0.18 * dt)
