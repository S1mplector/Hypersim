"""Vectorized NumPy operations for high-performance 4D computations.

This module provides optimized batch operations for transforming and
projecting large numbers of vertices, useful for complex objects like
the 600-cell (720 edges) or animated scenes with many objects.
"""
from __future__ import annotations

from typing import Tuple
import numpy as np

from .math_4d import Matrix4D, Vector4D


def batch_transform_vertices(
    vertices: np.ndarray,
    rotation_matrix: Matrix4D,
    position: Vector4D,
    scale: float = 1.0,
) -> np.ndarray:
    """Transform multiple vertices in a single vectorized operation.
    
    Args:
        vertices: Array of shape (N, 4) containing N 4D vertices
        rotation_matrix: 4x4 rotation matrix
        position: Translation vector (4,)
        scale: Uniform scale factor
        
    Returns:
        Transformed vertices array of shape (N, 4)
    """
    vertices = np.asarray(vertices, dtype=np.float32)
    
    # Apply scale
    if scale != 1.0:
        vertices = vertices * scale
    
    # Apply rotation: (N, 4) @ (4, 4).T = (N, 4)
    rotated = vertices @ rotation_matrix.T
    
    # Apply translation
    if np.any(position):
        rotated = rotated + position
    
    return rotated


def batch_project_4d_to_3d(
    vertices_4d: np.ndarray,
    distance: float = 5.0,
) -> np.ndarray:
    """Project multiple 4D vertices to 3D using perspective projection.
    
    Vectorized version of perspective_projection_4d_to_3d for better
    performance with large vertex arrays.
    
    Args:
        vertices_4d: Array of shape (N, 4)
        distance: Projection distance
        
    Returns:
        3D vertices array of shape (N, 3)
    """
    vertices_4d = np.asarray(vertices_4d, dtype=np.float32)
    
    w = vertices_4d[:, 3]
    denominator = np.clip(distance - w, 0.05, None)
    perspective_factor = distance / denominator
    
    # Apply perspective to x, y, z
    vertices_3d = vertices_4d[:, :3] * perspective_factor[:, np.newaxis]
    
    return vertices_3d


def batch_project_to_screen(
    vertices_4d: np.ndarray,
    screen_width: int,
    screen_height: int,
    scale: float = 120.0,
    w_factor: float = 0.3,
) -> Tuple[np.ndarray, np.ndarray]:
    """Project 4D vertices directly to 2D screen coordinates.
    
    Combines 4D-to-3D projection and 3D-to-2D screen mapping in one
    vectorized operation.
    
    Args:
        vertices_4d: Array of shape (N, 4)
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels
        scale: Projection scale factor
        w_factor: W coordinate influence on scale
        
    Returns:
        Tuple of:
        - screen_coords: Integer array of shape (N, 2) with (x, y) screen coordinates
        - depths: Float array of shape (N,) with depth values for sorting
    """
    vertices_4d = np.asarray(vertices_4d, dtype=np.float32)
    
    x = vertices_4d[:, 0]
    y = vertices_4d[:, 1]
    z = vertices_4d[:, 2]
    w = vertices_4d[:, 3]
    
    # W-based scaling
    w_scale = 1.0 / (1.0 + np.abs(w) * w_factor)
    
    # Screen coordinates
    screen_x = (x * w_scale * scale + screen_width / 2).astype(np.int32)
    screen_y = (-y * w_scale * scale + screen_height / 2).astype(np.int32)
    
    screen_coords = np.stack([screen_x, screen_y], axis=1)
    depths = z * w_scale
    
    return screen_coords, depths


def batch_compute_edge_midpoints(
    vertices: np.ndarray,
    edges: np.ndarray,
) -> np.ndarray:
    """Compute midpoints of all edges for depth sorting.
    
    Args:
        vertices: Array of shape (N, 4) or (N, 3)
        edges: Array of shape (E, 2) with vertex indices
        
    Returns:
        Midpoints array of shape (E, vertices.shape[1])
    """
    vertices = np.asarray(vertices)
    edges = np.asarray(edges)
    
    v1 = vertices[edges[:, 0]]
    v2 = vertices[edges[:, 1]]
    
    return (v1 + v2) / 2


def batch_compute_edge_depths(
    vertices_4d: np.ndarray,
    edges: np.ndarray,
    w_factor: float = 0.3,
) -> np.ndarray:
    """Compute depth values for all edges for sorting.
    
    Args:
        vertices_4d: Array of shape (N, 4)
        edges: Array of shape (E, 2)
        w_factor: W coordinate influence
        
    Returns:
        Depths array of shape (E,)
    """
    vertices_4d = np.asarray(vertices_4d, dtype=np.float32)
    edges = np.asarray(edges)
    
    # Get edge endpoint vertices
    v1 = vertices_4d[edges[:, 0]]
    v2 = vertices_4d[edges[:, 1]]
    
    # Compute w-adjusted z for each endpoint
    z1 = v1[:, 2] / (1.0 + np.abs(v1[:, 3]) * w_factor)
    z2 = v2[:, 2] / (1.0 + np.abs(v2[:, 3]) * w_factor)
    
    # Average depth
    return (z1 + z2) / 2


def depth_sort_edges(
    edges: np.ndarray,
    depths: np.ndarray,
    back_to_front: bool = True,
) -> np.ndarray:
    """Sort edges by depth for proper rendering order.
    
    Args:
        edges: Array of shape (E, 2)
        depths: Array of shape (E,) with depth values
        back_to_front: If True, sort far to near (for opaque rendering)
        
    Returns:
        Sorted edges array
    """
    order = np.argsort(depths)
    if back_to_front:
        order = order[::-1]
    return edges[order]


def batch_rotation_matrix_4d(
    angle_xy: float = 0.0,
    angle_xz: float = 0.0,
    angle_xw: float = 0.0,
    angle_yz: float = 0.0,
    angle_yw: float = 0.0,
    angle_zw: float = 0.0,
) -> np.ndarray:
    """Create a combined 4D rotation matrix efficiently.
    
    Creates all rotation matrices and combines them in a single
    operation rather than sequential multiplications.
    
    Args:
        angle_xy to angle_zw: Rotation angles in radians
        
    Returns:
        Combined 4x4 rotation matrix
    """
    result = np.eye(4, dtype=np.float32)
    
    # Pre-compute all trig values
    angles = [angle_xy, angle_xz, angle_xw, angle_yz, angle_yw, angle_zw]
    cos_vals = np.cos(angles)
    sin_vals = np.sin(angles)
    
    # XY rotation
    if angle_xy != 0:
        rot = np.eye(4, dtype=np.float32)
        rot[0, 0] = cos_vals[0]
        rot[0, 1] = -sin_vals[0]
        rot[1, 0] = sin_vals[0]
        rot[1, 1] = cos_vals[0]
        result = rot @ result
    
    # XZ rotation
    if angle_xz != 0:
        rot = np.eye(4, dtype=np.float32)
        rot[0, 0] = cos_vals[1]
        rot[0, 2] = -sin_vals[1]
        rot[2, 0] = sin_vals[1]
        rot[2, 2] = cos_vals[1]
        result = rot @ result
    
    # XW rotation
    if angle_xw != 0:
        rot = np.eye(4, dtype=np.float32)
        rot[0, 0] = cos_vals[2]
        rot[0, 3] = -sin_vals[2]
        rot[3, 0] = sin_vals[2]
        rot[3, 3] = cos_vals[2]
        result = rot @ result
    
    # YZ rotation
    if angle_yz != 0:
        rot = np.eye(4, dtype=np.float32)
        rot[1, 1] = cos_vals[3]
        rot[1, 2] = -sin_vals[3]
        rot[2, 1] = sin_vals[3]
        rot[2, 2] = cos_vals[3]
        result = rot @ result
    
    # YW rotation
    if angle_yw != 0:
        rot = np.eye(4, dtype=np.float32)
        rot[1, 1] = cos_vals[4]
        rot[1, 3] = -sin_vals[4]
        rot[3, 1] = sin_vals[4]
        rot[3, 3] = cos_vals[4]
        result = rot @ result
    
    # ZW rotation
    if angle_zw != 0:
        rot = np.eye(4, dtype=np.float32)
        rot[2, 2] = cos_vals[5]
        rot[2, 3] = -sin_vals[5]
        rot[3, 2] = sin_vals[5]
        rot[3, 3] = cos_vals[5]
        result = rot @ result
    
    return result


def compute_bounding_box_vectorized(vertices: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Compute axis-aligned bounding box of vertices.
    
    Args:
        vertices: Array of shape (N, 4)
        
    Returns:
        Tuple of (min_corner, max_corner) each of shape (4,)
    """
    vertices = np.asarray(vertices)
    return np.min(vertices, axis=0), np.max(vertices, axis=0)


def compute_centroid(vertices: np.ndarray) -> np.ndarray:
    """Compute the centroid of a set of vertices.
    
    Args:
        vertices: Array of shape (N, 4)
        
    Returns:
        Centroid vector of shape (4,)
    """
    return np.mean(vertices, axis=0)


def normalize_vertices_to_unit(vertices: np.ndarray) -> np.ndarray:
    """Normalize vertices to fit within a unit hypersphere.
    
    Args:
        vertices: Array of shape (N, 4)
        
    Returns:
        Normalized vertices array
    """
    vertices = np.asarray(vertices, dtype=np.float32)
    centroid = compute_centroid(vertices)
    centered = vertices - centroid
    max_dist = np.max(np.linalg.norm(centered, axis=1))
    if max_dist > 0:
        centered = centered / max_dist
    return centered
