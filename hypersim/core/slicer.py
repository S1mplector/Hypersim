"""Cross-section slicing for 4D objects.

This module provides utilities to compute 3D cross-sections of 4D objects
at a given W value, allowing visualization of "slices" through the 4th dimension.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from hypersim.core.shape_4d import Shape4D

from hypersim.core.math_4d import Vector4D


@dataclass
class CrossSection:
    """A 3D cross-section of a 4D object at a specific W value."""
    w_value: float
    vertices_3d: List[np.ndarray]  # List of (x, y, z) points
    edges: List[Tuple[int, int]]   # Indices into vertices_3d
    source_edge_map: List[int]     # Maps each edge to source 4D edge index


def slice_edge_at_w(
    v1: Vector4D, 
    v2: Vector4D, 
    w_target: float
) -> Optional[np.ndarray]:
    """Find the point where an edge crosses a W hyperplane.
    
    Args:
        v1: First vertex of the edge (4D)
        v2: Second vertex of the edge (4D)
        w_target: The W value of the slicing hyperplane
        
    Returns:
        3D point (x, y, z) where the edge crosses the hyperplane,
        or None if the edge doesn't cross it.
    """
    w1, w2 = v1[3], v2[3]
    
    # Check if edge crosses the W plane
    if (w1 - w_target) * (w2 - w_target) > 0:
        return None  # Both vertices on same side
    
    # Handle edge exactly at the plane
    if abs(w1 - w2) < 1e-10:
        if abs(w1 - w_target) < 1e-10:
            # Edge lies in the plane, return midpoint
            mid = (v1[:3] + v2[:3]) / 2
            return mid
        return None
    
    # Interpolate to find crossing point
    t = (w_target - w1) / (w2 - w1)
    if t < 0 or t > 1:
        return None
    
    point_3d = v1[:3] + t * (v2[:3] - v1[:3])
    return point_3d


def compute_cross_section(
    shape: "Shape4D",
    w_value: float = 0.0,
    tolerance: float = 1e-6
) -> CrossSection:
    """Compute a 3D cross-section of a 4D shape at a given W value.
    
    This finds where each edge of the 4D shape crosses the W=w_value hyperplane,
    creating a 3D representation of the slice.
    
    Args:
        shape: The 4D shape to slice
        w_value: The W coordinate of the slicing hyperplane
        tolerance: Tolerance for vertex deduplication
        
    Returns:
        CrossSection containing the 3D vertices and edges of the slice
    """
    vertices_4d = shape.get_transformed_vertices()
    edges_4d = shape.edges
    
    # Find intersection points for each edge
    intersection_points: List[np.ndarray] = []
    edge_to_points: List[Tuple[int, int]] = []  # (point_idx, source_edge_idx)
    source_edges: List[int] = []
    
    for edge_idx, (i, j) in enumerate(edges_4d):
        v1 = np.array(vertices_4d[i])
        v2 = np.array(vertices_4d[j])
        
        point = slice_edge_at_w(v1, v2, w_value)
        if point is not None:
            # Check for duplicate points
            found_duplicate = False
            for existing_idx, existing_point in enumerate(intersection_points):
                if np.linalg.norm(point - existing_point) < tolerance:
                    edge_to_points.append((existing_idx, edge_idx))
                    found_duplicate = True
                    break
            
            if not found_duplicate:
                edge_to_points.append((len(intersection_points), edge_idx))
                intersection_points.append(point)
    
    # Build edges in the cross-section
    # Connect points that share a face in the original 4D object
    slice_edges: List[Tuple[int, int]] = []
    source_edge_map: List[int] = []
    
    # For each face in the 4D shape, check which edges contribute points
    if hasattr(shape, 'faces') and shape.faces:
        for face in shape.faces:
            face_points = []
            for edge_idx, (i, j) in enumerate(edges_4d):
                # Check if this edge is part of the face
                if i in face and j in face:
                    # Find if this edge contributed a point
                    for pt_idx, src_edge in edge_to_points:
                        if src_edge == edge_idx:
                            face_points.append((pt_idx, edge_idx))
                            break
            
            # Connect consecutive points on this face
            if len(face_points) >= 2:
                for k in range(len(face_points)):
                    p1_idx = face_points[k][0]
                    p2_idx = face_points[(k + 1) % len(face_points)][0]
                    if p1_idx != p2_idx:
                        edge = (min(p1_idx, p2_idx), max(p1_idx, p2_idx))
                        if edge not in slice_edges:
                            slice_edges.append(edge)
                            source_edge_map.append(face_points[k][1])
    else:
        # Fallback: connect points from adjacent edges
        # This is less accurate but works for shapes without face data
        point_indices = [pt[0] for pt in edge_to_points]
        if len(point_indices) >= 2:
            # Simple approach: create a convex hull-like connection
            for i in range(len(point_indices)):
                for j in range(i + 1, len(point_indices)):
                    dist = np.linalg.norm(
                        intersection_points[point_indices[i]] - 
                        intersection_points[point_indices[j]]
                    )
                    if dist < 2.0:  # Connect nearby points
                        edge = (point_indices[i], point_indices[j])
                        if edge not in slice_edges:
                            slice_edges.append(edge)
                            source_edge_map.append(-1)
    
    return CrossSection(
        w_value=w_value,
        vertices_3d=intersection_points,
        edges=slice_edges,
        source_edge_map=source_edge_map
    )


def compute_w_range(shape: "Shape4D") -> Tuple[float, float]:
    """Get the range of W values for a shape.
    
    Args:
        shape: The 4D shape
        
    Returns:
        Tuple of (min_w, max_w)
    """
    vertices = shape.get_transformed_vertices()
    w_values = [v[3] for v in vertices]
    return min(w_values), max(w_values)


class SliceAnimator:
    """Animate slicing through a 4D object along the W axis."""
    
    def __init__(self, shape: "Shape4D", steps: int = 100):
        """Initialize the slice animator.
        
        Args:
            shape: The 4D shape to slice
            steps: Number of steps for the animation
        """
        self.shape = shape
        self.steps = steps
        self.current_step = 0
        self.w_min, self.w_max = compute_w_range(shape)
        self._direction = 1  # 1 for forward, -1 for backward
        
    @property
    def current_w(self) -> float:
        """Get the current W value for slicing."""
        t = self.current_step / max(1, self.steps - 1)
        return self.w_min + t * (self.w_max - self.w_min)
    
    def get_slice(self) -> CrossSection:
        """Get the cross-section at the current W value."""
        return compute_cross_section(self.shape, self.current_w)
    
    def step(self) -> None:
        """Advance the animation by one step."""
        self.current_step += self._direction
        if self.current_step >= self.steps:
            self.current_step = self.steps - 1
            self._direction = -1
        elif self.current_step < 0:
            self.current_step = 0
            self._direction = 1
    
    def reset(self) -> None:
        """Reset the animation to the beginning."""
        self.current_step = 0
        self._direction = 1
