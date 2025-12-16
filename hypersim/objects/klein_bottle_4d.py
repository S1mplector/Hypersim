"""Klein Bottle embedded in 4D.

Mathematical Background
=======================
The Klein bottle is a famous non-orientable surface that cannot be embedded
in 3D without self-intersection. However, it CAN be embedded in 4D without
any self-intersection, making 4D the natural home for this object.

The Klein bottle is topologically:
- A closed surface (no boundary)
- Non-orientable (has only one side)
- Genus 1 (one "handle" in non-orientable sense)
- Euler characteristic χ = 0

In 4D, we can visualize the Klein bottle properly because the fourth
dimension provides the "room" needed for the surface to pass through
itself without intersection.

Parametric Equations
--------------------
The figure-8 immersion (Lawson's parametrization) in 4D:

x(u,v) = (r + cos(u/2)sin(v) - sin(u/2)sin(2v)) cos(u)
y(u,v) = (r + cos(u/2)sin(v) - sin(u/2)sin(2v)) sin(u)
z(u,v) = sin(u/2)sin(v) + cos(u/2)sin(2v)
w(u,v) = cos(v)

Where u ∈ [0, 2π), v ∈ [0, 2π), and r is the major radius.

Topological Properties
----------------------
- Euler characteristic: χ = V - E + F = 0
- Orientability: Non-orientable
- Fundamental group: π₁ = ⟨a,b | aba = b⟩
- Homology: H₀ = ℤ, H₁ = ℤ ⊕ ℤ₂, H₂ = 0

The non-orientability means that if you travel around the bottle,
you can return to your starting point with your orientation reversed
(like on a Möbius strip, but in 2D surface form).

Relationship to Möbius Strip
----------------------------
The Klein bottle can be constructed by gluing two Möbius strips together
along their boundaries. This is why both are non-orientable.

Applications
------------
- Topology education and visualization
- Study of non-orientable manifolds
- Computer graphics and 4D visualization
- Understanding fiber bundles (Klein bottle is a ℤ₂ bundle over S¹)

References
----------
- Lawson, H.B. "Complete minimal surfaces in S³" (1970)
- Francis, G.K. "A Topological Picturebook" (1987)
"""
from __future__ import annotations

from typing import List, Tuple
import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class KleinBottle4D(Shape4D):
    """Klein bottle properly embedded in 4D space.
    
    In 4D, the Klein bottle can exist without self-intersection,
    unlike its 3D immersion. This parametrization uses the figure-8
    form which shows the bottle's structure clearly.
    
    Attributes:
        radius: Major radius of the bottle
        segments_u: Number of segments around the tube
        segments_v: Number of segments along the tube
        
    Topological Properties:
        - Euler characteristic: 0
        - Orientable: No
        - Genus (non-orientable): 2
    """
    
    def __init__(
        self,
        radius: float = 1.0,
        segments_u: int = 40,
        segments_v: int = 20,
        **kwargs
    ):
        """Initialize a Klein bottle in 4D.
        
        Args:
            radius: Major radius
            segments_u: Segments around circumference
            segments_v: Segments around tube
            **kwargs: Additional arguments passed to Shape4D
        """
        super().__init__(**kwargs)
        self.radius = float(radius)
        self.segments_u = max(8, segments_u)
        self.segments_v = max(8, segments_v)
        
        self._base_vertices = self._generate_vertices()
        self._edges = self._generate_edges()
        self._faces: List[Tuple[int, ...]] = self._generate_faces()
        self._cells: List[Tuple[int, ...]] = []
    
    def _generate_vertices(self) -> List[Vector4D]:
        """Generate vertices using the figure-8 parametrization."""
        vertices = []
        r = self.radius
        
        for i in range(self.segments_u):
            u = 2 * np.pi * i / self.segments_u
            
            for j in range(self.segments_v):
                v = 2 * np.pi * j / self.segments_v
                
                # Figure-8 Klein bottle parametrization
                cos_u = np.cos(u)
                sin_u = np.sin(u)
                cos_v = np.cos(v)
                sin_v = np.sin(v)
                cos_u2 = np.cos(u / 2)
                sin_u2 = np.sin(u / 2)
                sin_2v = np.sin(2 * v)
                
                # Radial factor
                rho = r + cos_u2 * sin_v - sin_u2 * sin_2v
                
                x = rho * cos_u
                y = rho * sin_u
                z = sin_u2 * sin_v + cos_u2 * sin_2v
                w = cos_v * 0.5  # Scale W to make it visible in projection
                
                vertices.append(np.array([x, y, z, w], dtype=np.float32))
        
        return vertices
    
    def _generate_edges(self) -> List[Tuple[int, int]]:
        """Generate edges forming the surface mesh."""
        edges = []
        nu, nv = self.segments_u, self.segments_v
        
        for i in range(nu):
            for j in range(nv):
                current = i * nv + j
                
                # Edge to next in u direction (wraps)
                next_u = ((i + 1) % nu) * nv + j
                edges.append((current, next_u))
                
                # Edge to next in v direction (wraps)
                next_v = i * nv + ((j + 1) % nv)
                edges.append((current, next_v))
        
        return edges
    
    def _generate_faces(self) -> List[Tuple[int, ...]]:
        """Generate quadrilateral faces."""
        faces = []
        nu, nv = self.segments_u, self.segments_v
        
        for i in range(nu):
            for j in range(nv):
                # Four corners of each quad
                i1 = i * nv + j
                i2 = ((i + 1) % nu) * nv + j
                i3 = ((i + 1) % nu) * nv + ((j + 1) % nv)
                i4 = i * nv + ((j + 1) % nv)
                
                faces.append((i1, i2, i3, i4))
        
        return faces
    
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
    
    def get_info(self) -> dict:
        """Return topological and geometric information."""
        return {
            "name": "Klein Bottle (4D embedding)",
            "topological_type": "Non-orientable closed surface",
            "euler_characteristic": 0,
            "orientable": False,
            "genus_nonorientable": 2,
            "fundamental_group": "⟨a,b | aba = b⟩",
            "vertices": len(self._base_vertices),
            "edges": len(self._edges),
            "faces": len(self._faces),
            "parametrization": "Figure-8 (Lawson)",
            "can_embed_in_3d": False,
            "can_embed_in_4d": True,
        }
