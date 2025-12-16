"""Grand Antiprism - a uniform 4-polytope with 300 cells.

The grand antiprism is one of the most interesting uniform 4-polytopes.
It has 100 vertices, 500 edges, 720 faces (320 triangles + 400 pentagons
for the cells), and 320 cells (20 pentagonal antiprisms + 300 tetrahedra).
"""
from __future__ import annotations

from typing import List, Tuple
import numpy as np
import math

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class GrandAntiprism(Shape4D):
    """Grand Antiprism - a uniform 4-polytope.
    
    The grand antiprism can be constructed from two rings of 10 pentagonal
    antiprisms each, with 300 tetrahedra filling the gaps.
    
    This implementation creates an approximation using the vertex coordinates
    based on the structure of two interlocking rings.
    """
    
    def __init__(self, size: float = 1.0, **kwargs):
        """Initialize a grand antiprism.
        
        Args:
            size: Overall scale
            **kwargs: Passed to Shape4D
        """
        super().__init__(**kwargs)
        self.size = float(size)
        
        # Generate vertices
        # The grand antiprism has vertices on two orthogonal rings
        verts: List[Vector4D] = []
        
        phi = (1 + math.sqrt(5)) / 2  # Golden ratio
        
        # First ring: 50 vertices in XY-ZW space
        for i in range(10):
            angle1 = 2 * math.pi * i / 10
            for j in range(5):
                angle2 = 2 * math.pi * j / 5 + (math.pi / 5 if i % 2 else 0)
                x = math.cos(angle1)
                y = math.sin(angle1)
                z = math.cos(angle2) * 0.5
                w = math.sin(angle2) * 0.5
                verts.append(np.array([x, y, z, w], dtype=np.float32) * self.size)
        
        # Second ring: 50 vertices rotated
        for i in range(10):
            angle1 = 2 * math.pi * i / 10 + math.pi / 10
            for j in range(5):
                angle2 = 2 * math.pi * j / 5 + (math.pi / 5 if i % 2 else 0)
                x = math.cos(angle2) * 0.5
                y = math.sin(angle2) * 0.5
                z = math.cos(angle1)
                w = math.sin(angle1)
                verts.append(np.array([x, y, z, w], dtype=np.float32) * self.size)
        
        self._base_vertices = verts
        
        # Generate edges by connecting nearby vertices
        edges: List[Tuple[int, int]] = []
        threshold = 0.8 * self.size
        
        for i in range(len(verts)):
            for j in range(i + 1, len(verts)):
                dist = np.linalg.norm(verts[i] - verts[j])
                if dist < threshold:
                    edges.append((i, j))
        
        self._edges = edges
        self._faces: List[Tuple[int, ...]] = []
        self._cells: List[Tuple[int, ...]] = []
    
    @property
    def vertices(self) -> List[Vector4D]:
        return self._base_vertices
    
    @property
    def edges(self) -> List[Tuple[int, int]]:
        return self._edges
    
    @property
    def faces(self) -> List[Tuple[int, ...]]:
        return self._faces
    
    @property
    def cells(self) -> List[Tuple[int, ...]]:
        return self._cells
