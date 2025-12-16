"""4D vector and matrix math utilities for 4D rendering."""
from typing import Tuple, List, Union
import numpy as np
import math

# Type aliases
Vector4D = np.ndarray  # Shape: (4,)
Matrix4D = np.ndarray  # Shape: (4, 4)
Vector3D = np.ndarray  # Shape: (3,)
Matrix3D = np.ndarray  # Shape: (3, 3)

def create_vector_4d(x: float = 0.0, y: float = 0.0, z: float = 0.0, w: float = 0.0) -> Vector4D:
    """Create a 4D vector.
    
    Args:
        x: X component
        y: Y component
        z: Z component
        w: W component (4th dimension)
        
    Returns:
        A 4D vector as a numpy array
    """
    return np.array([x, y, z, w], dtype=np.float32)

def create_translation_matrix_4d(x: float = 0.0, y: float = 0.0, z: float = 0.0, w: float = 0.0) -> Matrix4D:
    """Create a 4D translation matrix (homogeneous form).
    
    Args:
        x: Translation along X axis
        y: Translation along Y axis
        z: Translation along Z axis
        w: Translation along W axis (4th dimension)
        
    Returns:
        A 4x4 translation matrix
    
    Note:
        This matrix assumes homogeneous coordinates (the last component set to 1)
        rather than representing a true 4D translation on (x, y, z, w) positions.
        The default Shape4D pipeline applies translation separately to avoid this
        ambiguity.
    """
    matrix = np.eye(4, dtype=np.float32)
    matrix[0, 3] = x
    matrix[1, 3] = y
    matrix[2, 3] = z
    matrix[3, 3] = w
    return matrix

def create_scale_matrix_4d(sx: float = 1.0, sy: float = 1.0, sz: float = 1.0, sw: float = 1.0) -> Matrix4D:
    """Create a 4D scaling matrix.
    
    Args:
        sx: Scale factor along X axis
        sy: Scale factor along Y axis
        sz: Scale factor along Z axis
        sw: Scale factor along W axis (4th dimension)
        
    Returns:
        A 4x4 scaling matrix
    """
    return np.array([
        [sx, 0, 0, 0],
        [0, sy, 0, 0],
        [0, 0, sz, 0],
        [0, 0, 0, sw]
    ], dtype=np.float32)

def create_rotation_matrix_4d(angle_xy: float = 0.0, angle_xz: float = 0.0,
                           angle_xw: float = 0.0, angle_yz: float = 0.0,
                           angle_yw: float = 0.0, angle_zw: float = 0.0) -> Matrix4D:
    """Create a 4D rotation matrix from the given rotation angles.
    
    In 4D, rotations happen in planes (as opposed to around axes in 3D).
    Each pair of axes defines a plane of rotation.
    
    Args:
        angle_xy: Rotation angle in the XY plane (radians)
        angle_xz: Rotation angle in the XZ plane (radians)
        angle_xw: Rotation angle in the XW plane (radians)
        angle_yz: Rotation angle in the YZ plane (radians)
        angle_yw: Rotation angle in the YW plane (radians)
        angle_zw: Rotation angle in the ZW plane (radians)
        
    Returns:
        A 4x4 rotation matrix
    """
    # Start with identity matrix
    rot = np.eye(4, dtype=np.float32)
    
    # Apply each rotation in sequence
    if angle_xy != 0:
        c, s = math.cos(angle_xy), math.sin(angle_xy)
        rot_xy = np.array([
            [c, -s, 0, 0],
            [s, c, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        rot = np.dot(rot_xy, rot)
    
    if angle_xz != 0:
        c, s = math.cos(angle_xz), math.sin(angle_xz)
        rot_xz = np.array([
            [c, 0, -s, 0],
            [0, 1, 0, 0],
            [s, 0, c, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        rot = np.dot(rot_xz, rot)
    
    if angle_xw != 0:
        c, s = math.cos(angle_xw), math.sin(angle_xw)
        rot_xw = np.array([
            [c, 0, 0, -s],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [s, 0, 0, c]
        ], dtype=np.float32)
        rot = np.dot(rot_xw, rot)
    
    if angle_yz != 0:
        c, s = math.cos(angle_yz), math.sin(angle_yz)
        rot_yz = np.array([
            [1, 0, 0, 0],
            [0, c, -s, 0],
            [0, s, c, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        rot = np.dot(rot_yz, rot)
    
    if angle_yw != 0:
        c, s = math.cos(angle_yw), math.sin(angle_yw)
        rot_yw = np.array([
            [1, 0, 0, 0],
            [0, c, 0, -s],
            [0, 0, 1, 0],
            [0, s, 0, c]
        ], dtype=np.float32)
        rot = np.dot(rot_yw, rot)
    
    if angle_zw != 0:
        c, s = math.cos(angle_zw), math.sin(angle_zw)
        rot_zw = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, c, -s],
            [0, 0, s, c]
        ], dtype=np.float32)
        rot = np.dot(rot_zw, rot)
    
    return rot

def perspective_projection_4d_to_3d(points_4d: np.ndarray, distance: float = 5.0) -> np.ndarray:
    """Project 4D points to 3D using perspective projection.
    
    Args:
        points_4d: Array of 4D points, shape (n, 4)
        distance: Distance from the 4D camera to the projection hyperplane
        
    Returns:
        Array of 3D points, shape (n, 3)
    """
    # Ensure input is at least 2D
    points_4d = np.atleast_2d(points_4d)
    
    # 4D perspective projection: project from 4D to 3D hyperplane
    # The correct formula for 4D perspective projection is:
    # For each point (x, y, z, w), project to (x', y', z') where:
    # x' = x * distance / (distance - w)
    # y' = y * distance / (distance - w) 
    # z' = z * distance / (distance - w)
    
    w = points_4d[:, 3]
    
    # Avoid division by zero and handle points behind the camera
    denominator = distance - w
    # Clamp to positive epsilon to avoid flips/infinite scale
    denominator = np.clip(denominator, 0.05, None)
    
    perspective_factor = distance / denominator
    
    # Apply perspective to x, y, z coordinates
    points_3d = points_4d[:, :3] * perspective_factor[:, np.newaxis]
    
    return points_3d

def normalize_vector(v: np.ndarray) -> np.ndarray:
    """Normalize a vector to unit length.
    
    Args:
        v: Input vector (can be any dimension)
        
    Returns:
        Normalized vector with the same shape as input
    """
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm

def dot_product_4d(v1: Vector4D, v2: Vector4D) -> float:
    """Compute the dot product of two 4D vectors.
    
    Args:
        v1: First 4D vector
        v2: Second 4D vector
        
    Returns:
        Dot product as a float
    """
    return np.dot(v1, v2)

def cross_product_4d(a: Vector4D, b: Vector4D, c: Vector4D) -> Vector4D:
    """Compute the generalized cross product of three 4D vectors.
    
    In 4D, the cross product of three vectors gives a fourth vector that is
    perpendicular to all three input vectors.
    
    Args:
        a: First 4D vector
        b: Second 4D vector
        c: Third 4D vector
        
    Returns:
        A 4D vector perpendicular to a, b, and c
    """
    # Using the determinant method for 4D cross product
    # | i  j  k  l |
    # | a0 a1 a2 a3 |
    # | b0 b1 b2 b3 |
    # | c0 c1 c2 c3 |
    
    # Calculate the 3x3 subdeterminants with sign alternation
    i = np.linalg.det(np.array([
        [a[1], a[2], a[3]],
        [b[1], b[2], b[3]],
        [c[1], c[2], c[3]]
    ]))
    
    j = -np.linalg.det(np.array([
        [a[0], a[2], a[3]],
        [b[0], b[2], b[3]],
        [c[0], c[2], c[3]]
    ]))
    
    k = np.linalg.det(np.array([
        [a[0], a[1], a[3]],
        [b[0], b[1], b[3]],
        [c[0], c[1], c[3]]
    ]))
    
    l = -np.linalg.det(np.array([
        [a[0], a[1], a[2]],
        [b[0], b[1], b[2]],
        [c[0], c[1], c[2]]
    ]))
    
    return np.array([i, j, k, l], dtype=np.float32)

def create_look_at_matrix(eye: Vector4D, target: Vector4D, up: Vector4D) -> Matrix4D:
    """Create an orthonormal 4D view matrix using Gram–Schmidt.
    
    The returned matrix contains the view basis (rows = right, up, forward,
    ana). Translation is not baked in; consumers should subtract the eye
    position separately when transforming points into view space.
    """
    eps = 1e-6

    def _gram_schmidt(vectors: List[np.ndarray]) -> List[np.ndarray]:
        basis: List[np.ndarray] = []
        for vec in vectors:
            v = np.asarray(vec, dtype=np.float32)
            for b in basis:
                v = v - np.dot(v, b) * b
            n = np.linalg.norm(v)
            if n < eps:
                continue
            basis.append(v / n)
            if len(basis) == 4:
                break
        return basis

    # Forward points from eye toward target; fall back if degenerate
    forward = target - eye
    if np.linalg.norm(forward) < eps:
        forward = np.array([0.0, 0.0, 1.0, 0.0], dtype=np.float32)
    forward = normalize_vector(forward)

    # Choose an up candidate that is not parallel to forward
    up_candidate = np.asarray(up, dtype=np.float32)
    if np.linalg.norm(up_candidate) < eps or abs(np.dot(up_candidate, forward)) > 0.95:
        # Pick a fallback axis with minimal alignment to forward
        axes = np.eye(4, dtype=np.float32)
        for axis in axes:
            if abs(np.dot(axis, forward)) < 0.8:
                up_candidate = axis
                break

    # Build an orthonormal basis via Gram–Schmidt
    candidates = [
        forward,
        up_candidate,
        np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32),
        np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32),
        np.array([0.0, 0.0, 1.0, 0.0], dtype=np.float32),
        np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
    ]
    basis = _gram_schmidt(candidates)
    # Ensure we always have four basis vectors by pulling from canonical axes
    if len(basis) < 4:
        axes = np.eye(4, dtype=np.float32)
        for axis in axes:
            if len(basis) >= 4:
                break
            basis = _gram_schmidt(basis + [axis])

    if len(basis) < 4:
        raise ValueError("Unable to construct a stable 4D view basis")

    forward = basis[0]
    # Use the next two orthogonal vectors for right and up to preserve a
    # meaningful orientation, and the remaining vector as the 4th axis.
    right = basis[2] if len(basis) > 2 else basis[1]
    up_vec = basis[1]
    ana = basis[3]

    rotation = np.eye(4, dtype=np.float32)
    rotation[0, :4] = right
    rotation[1, :4] = up_vec
    rotation[2, :4] = forward
    rotation[3, :4] = ana
    return rotation
