"""Runcinated Tesseract - a uniform 4-polytope.

The runcinated tesseract (or runcinated 8-cell) is formed by expanding
the cells of a tesseract outward. It has 64 vertices, 192 edges,
192 faces, and 80 cells.
"""
from __future__ import annotations

from typing import List, Tuple
import numpy as np
from itertools import combinations

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class RuncinatedTesseract(Shape4D):
    """Runcinated Tesseract - expanded hypercube.
    
    The runcination operation expands the cells of the tesseract,
    creating a uniform 4-polytope with:
    - 64 vertices
    - 192 edges  
    - 192 faces (64 triangles, 96 squares, 32 more squares)
    - 80 cells (8 cubes, 32 triangular prisms, 16 tetrahedra, 24 cubes)
    
    Vertices are permutations of (±1, ±1, ±1, ±(1+√2)) and their variants.
    """
    
    def __init__(self, size: float = 1.0, **kwargs):
        """Initialize a runcinated tesseract.
        
        Args:
            size: Overall scale
            **kwargs: Passed to Shape4D
        """
        super().__init__(**kwargs)
        self.size = float(size)
        
        sqrt2 = np.sqrt(2)
        a = 1.0
        b = 1.0 + sqrt2
        
        # Generate vertices: all permutations with sign changes
        verts_set = set()
        
        # Type 1: (±1, ±1, ±1, ±(1+√2)) - 16 vertices per permutation
        coords = [a, a, a, b]
        for perm in self._permutations(coords):
            for signs in self._sign_combinations(4):
                v = tuple(perm[i] * signs[i] for i in range(4))
                verts_set.add(v)
        
        # Type 2: (±1, ±1, ±(1+√2), ±1)
        coords = [a, a, b, a]
        for perm in self._permutations(coords):
            for signs in self._sign_combinations(4):
                v = tuple(perm[i] * signs[i] for i in range(4))
                verts_set.add(v)
        
        # Type 3: (±1, ±(1+√2), ±1, ±1)
        coords = [a, b, a, a]
        for perm in self._permutations(coords):
            for signs in self._sign_combinations(4):
                v = tuple(perm[i] * signs[i] for i in range(4))
                verts_set.add(v)
        
        # Type 4: (±(1+√2), ±1, ±1, ±1)
        coords = [b, a, a, a]
        for perm in self._permutations(coords):
            for signs in self._sign_combinations(4):
                v = tuple(perm[i] * signs[i] for i in range(4))
                verts_set.add(v)
        
        # Convert to list and scale
        verts: List[Vector4D] = [
            np.array(v, dtype=np.float32) * self.size / b
            for v in sorted(verts_set)
        ]
        self._base_vertices = verts
        
        # Generate edges by finding vertices at the correct distance
        edges: List[Tuple[int, int]] = []
        edge_length = 2.0 * self.size / b  # Normalized edge length
        tolerance = 0.1 * edge_length
        
        for i in range(len(verts)):
            for j in range(i + 1, len(verts)):
                dist = np.linalg.norm(verts[i] - verts[j])
                if abs(dist - edge_length) < tolerance:
                    edges.append((i, j))
        
        self._edges = edges
        self._faces: List[Tuple[int, ...]] = []
        self._cells: List[Tuple[int, ...]] = []
    
    def _permutations(self, coords: List[float]) -> List[Tuple[float, ...]]:
        """Generate unique permutations of coordinates."""
        from itertools import permutations as itertools_perms
        return list(set(itertools_perms(coords)))
    
    def _sign_combinations(self, n: int) -> List[Tuple[int, ...]]:
        """Generate all sign combinations for n coordinates."""
        result = []
        for i in range(2**n):
            signs = tuple(1 if (i >> j) & 1 else -1 for j in range(n))
            result.append(signs)
        return result
    
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
