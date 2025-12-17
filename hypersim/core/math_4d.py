"""4D Vector and Matrix Mathematics for HyperSim.

This module provides the fundamental mathematical operations for 4D geometry,
including vectors, matrices, rotations, and projections.

4D GEOMETRY FUNDAMENTALS
========================

Coordinate System
-----------------
We use a right-handed 4D coordinate system with axes:
- X: right (+) / left (-)
- Y: up (+) / down (-)
- Z: forward (+) / backward (-)
- W: ana (+) / kata (-) — the fourth spatial dimension

The W axis is perpendicular to all three familiar spatial axes.
Think of it as "another direction" that we cannot directly perceive.

Rotations in 4D
---------------
In 3D, rotation occurs around an AXIS (a 1D line).
In 4D, rotation occurs in a PLANE (a 2D surface).

With 4 axes, we have C(4,2) = 6 rotation planes:
- XY plane: rotation in the familiar horizontal plane
- XZ plane: "yaw" — looking left/right
- YZ plane: "pitch" — looking up/down
- XW plane: 4D rotation mixing X and W
- YW plane: 4D rotation mixing Y and W
- ZW plane: 4D rotation mixing Z and W

Each rotation is described by the standard 2D rotation formula:
    x' = x·cos(θ) - y·sin(θ)
    y' = x·sin(θ) + y·cos(θ)
applied to the two axes of the plane.

4D Perspective Projection
-------------------------
Just as 3D→2D projection divides by Z (depth), 4D→3D projection divides by W.

The projection formula from 4D point (x, y, z, w) to 3D:
    x' = x · d / (d - w)
    y' = y · d / (d - w)
    z' = z · d / (d - w)

where d is the viewing distance. Points with larger W appear smaller
(they are "further away" in the 4th dimension).

References
----------
- Coxeter, H.S.M. "Regular Polytopes" (1973)
- Hanson, A.J. "Visualizing Quaternions" (2006)
- Hollasch, S.R. "Four-Space Visualization of 4D Objects" (1991)
"""
from typing import Tuple, List, Union
import numpy as np
import math

# =============================================================================
# TYPE ALIASES
# =============================================================================

Vector4D = np.ndarray  # Shape: (4,) — represents a point or direction in 4D
Matrix4D = np.ndarray  # Shape: (4, 4) — represents a 4D linear transformation
Vector3D = np.ndarray  # Shape: (3,)
Matrix3D = np.ndarray  # Shape: (3, 3)

# =============================================================================
# CONSTANTS
# =============================================================================

# Axis indices for clarity
X, Y, Z, W = 0, 1, 2, 3

# Rotation plane pairs (axis1, axis2)
PLANE_XY = (X, Y)
PLANE_XZ = (X, Z)
PLANE_XW = (X, W)
PLANE_YZ = (Y, Z)
PLANE_YW = (Y, W)
PLANE_ZW = (Z, W)

# All 6 rotation planes
ALL_PLANES = [PLANE_XY, PLANE_XZ, PLANE_XW, PLANE_YZ, PLANE_YW, PLANE_ZW]

# =============================================================================
# VECTOR OPERATIONS
# =============================================================================

def create_vector_4d(x: float = 0.0, y: float = 0.0, z: float = 0.0, w: float = 0.0) -> Vector4D:
    """Create a 4D vector.
    
    Args:
        x: X component (right/left)
        y: Y component (up/down)
        z: Z component (forward/backward)
        w: W component (ana/kata — 4th dimension)
        
    Returns:
        A 4D vector as a numpy array of shape (4,)
        
    Example:
        >>> v = create_vector_4d(1, 2, 3, 4)
        >>> print(v)  # [1. 2. 3. 4.]
    """
    return np.array([x, y, z, w], dtype=np.float32)


def vec4(x: float = 0.0, y: float = 0.0, z: float = 0.0, w: float = 0.0) -> Vector4D:
    """Shorthand for create_vector_4d."""
    return np.array([x, y, z, w], dtype=np.float32)


def length_4d(v: Vector4D) -> float:
    """Compute the Euclidean length (magnitude) of a 4D vector.
    
    The 4D length is: ||v|| = sqrt(x² + y² + z² + w²)
    
    Args:
        v: A 4D vector
        
    Returns:
        The scalar length of the vector
    """
    return float(np.linalg.norm(v))


def length_squared_4d(v: Vector4D) -> float:
    """Compute the squared length of a 4D vector (avoids sqrt).
    
    Args:
        v: A 4D vector
        
    Returns:
        The squared length: x² + y² + z² + w²
    """
    return float(np.dot(v, v))


def distance_4d(a: Vector4D, b: Vector4D) -> float:
    """Compute the Euclidean distance between two 4D points.
    
    Args:
        a: First 4D point
        b: Second 4D point
        
    Returns:
        The distance ||b - a||
    """
    return float(np.linalg.norm(b - a))

# =============================================================================
# MATRIX OPERATIONS
# =============================================================================

def identity_4d() -> Matrix4D:
    """Create a 4x4 identity matrix."""
    return np.eye(4, dtype=np.float32)


def create_translation_matrix_4d(x: float = 0.0, y: float = 0.0, z: float = 0.0, w: float = 0.0) -> Matrix4D:
    """Create a 4D translation matrix (homogeneous form).
    
    Note: True 4D translation requires a 5x5 homogeneous matrix.
    This 4x4 version stores translation in the last column but
    Shape4D applies translation as a separate vector addition.
    
    Args:
        x: Translation along X axis
        y: Translation along Y axis
        z: Translation along Z axis
        w: Translation along W axis (4th dimension)
        
    Returns:
        A 4x4 matrix with translation in the last column
    """
    matrix = np.eye(4, dtype=np.float32)
    matrix[0, 3] = x
    matrix[1, 3] = y
    matrix[2, 3] = z
    return matrix

def create_scale_matrix_4d(sx: float = 1.0, sy: float = 1.0, sz: float = 1.0, sw: float = 1.0) -> Matrix4D:
    """Create a 4D scaling matrix.
    
    Args:
        sx: Scale factor along X axis
        sy: Scale factor along Y axis
        sz: Scale factor along Z axis
        sw: Scale factor along W axis (4th dimension)
        
    Returns:
        A 4x4 diagonal scaling matrix
    """
    return np.diag([sx, sy, sz, sw]).astype(np.float32)


def uniform_scale_4d(s: float) -> Matrix4D:
    """Create a uniform 4D scaling matrix."""
    return np.diag([s, s, s, s]).astype(np.float32)


# =============================================================================
# 4D ROTATION MATRICES
# =============================================================================

def rotation_matrix_plane(axis1: int, axis2: int, angle: float) -> Matrix4D:
    """Create a rotation matrix for rotation in a single plane.
    
    In 4D, rotation occurs in a 2D plane defined by two axes.
    This applies the standard 2D rotation formula:
        x' = x·cos(θ) - y·sin(θ)
        y' = x·sin(θ) + y·cos(θ)
    to the specified axes, leaving the other two unchanged.
    
    Args:
        axis1: First axis index (0=X, 1=Y, 2=Z, 3=W)
        axis2: Second axis index (0=X, 1=Y, 2=Z, 3=W)
        angle: Rotation angle in radians (positive = counterclockwise)
        
    Returns:
        A 4x4 rotation matrix
        
    Example:
        >>> # Rotate 45° in the XY plane
        >>> R = rotation_matrix_plane(0, 1, math.pi/4)
    """
    c, s = math.cos(angle), math.sin(angle)
    m = np.eye(4, dtype=np.float32)
    m[axis1, axis1] = c
    m[axis1, axis2] = -s
    m[axis2, axis1] = s
    m[axis2, axis2] = c
    return m


def rotation_xy(angle: float) -> Matrix4D:
    """Rotation in the XY plane (like 2D rotation when viewed from +Z)."""
    return rotation_matrix_plane(X, Y, angle)


def rotation_xz(angle: float) -> Matrix4D:
    """Rotation in the XZ plane (yaw - looking left/right)."""
    return rotation_matrix_plane(X, Z, angle)


def rotation_yz(angle: float) -> Matrix4D:
    """Rotation in the YZ plane (pitch - looking up/down)."""
    return rotation_matrix_plane(Y, Z, angle)


def rotation_xw(angle: float) -> Matrix4D:
    """Rotation in the XW plane (4D rotation mixing X and W)."""
    return rotation_matrix_plane(X, W, angle)


def rotation_yw(angle: float) -> Matrix4D:
    """Rotation in the YW plane (4D rotation mixing Y and W)."""
    return rotation_matrix_plane(Y, W, angle)


def rotation_zw(angle: float) -> Matrix4D:
    """Rotation in the ZW plane (4D rotation mixing Z and W)."""
    return rotation_matrix_plane(Z, W, angle)


def create_rotation_matrix_4d(angle_xy: float = 0.0, angle_xz: float = 0.0,
                              angle_xw: float = 0.0, angle_yz: float = 0.0,
                              angle_yw: float = 0.0, angle_zw: float = 0.0) -> Matrix4D:
    """Create a combined 4D rotation matrix from angles in all 6 planes.
    
    In 4D, there are 6 independent rotation planes (one for each pair of axes).
    This function composes rotations in a fixed order: XY, XZ, XW, YZ, YW, ZW.
    
    Note: Rotation order matters! Different orders give different results.
    For camera-style control, typically use XZ (yaw) and YZ (pitch) first.
    
    Args:
        angle_xy: Rotation in XY plane (radians)
        angle_xz: Rotation in XZ plane (radians) — yaw
        angle_xw: Rotation in XW plane (radians) — 4D rotation
        angle_yz: Rotation in YZ plane (radians) — pitch
        angle_yw: Rotation in YW plane (radians) — 4D rotation
        angle_zw: Rotation in ZW plane (radians) — 4D rotation
        
    Returns:
        A 4x4 rotation matrix (composition of all non-zero rotations)
    """
    rot = np.eye(4, dtype=np.float32)
    
    if angle_xy != 0:
        rot = rotation_xy(angle_xy) @ rot
    if angle_xz != 0:
        rot = rotation_xz(angle_xz) @ rot
    if angle_xw != 0:
        rot = rotation_xw(angle_xw) @ rot
    if angle_yz != 0:
        rot = rotation_yz(angle_yz) @ rot
    if angle_yw != 0:
        rot = rotation_yw(angle_yw) @ rot
    if angle_zw != 0:
        rot = rotation_zw(angle_zw) @ rot
    
    return rot

# =============================================================================
# 4D PERSPECTIVE PROJECTION
# =============================================================================

def perspective_projection_4d_to_3d(points_4d: np.ndarray, distance: float = 5.0) -> np.ndarray:
    """Project 4D points to 3D using perspective projection.
    
    This is analogous to how a 3D camera projects to 2D:
    - In 3D→2D: we divide by Z (depth)
    - In 4D→3D: we divide by W (4D depth)
    
    The projection formula:
        x' = x · d / (d - w)
        y' = y · d / (d - w)
        z' = z · d / (d - w)
    
    where d is the viewing distance. Points with larger W appear smaller
    (further away in 4D). Points with W > d are "behind" the 4D camera.
    
    Args:
        points_4d: Array of 4D points, shape (n, 4) or (4,)
        distance: Distance from 4D viewpoint to projection hyperplane
        
    Returns:
        Array of 3D points, shape (n, 3)
    """
    points_4d = np.atleast_2d(points_4d)
    w = points_4d[:, 3]
    
    # Compute perspective divisor: (distance - w)
    # Points at w=0 project at scale 1.0
    # Points at w>0 project smaller (further in 4D)
    # Points at w<0 project larger (closer in 4D)
    denominator = distance - w
    
    # Clamp to avoid division by zero or negative (behind camera)
    denominator = np.clip(denominator, 0.1, None)
    
    # Perspective scale factor
    scale = distance / denominator
    
    # Apply to XYZ coordinates
    points_3d = points_4d[:, :3] * scale[:, np.newaxis]
    
    return points_3d


def project_4d_to_2d(point_4d: Vector4D, distance_4d: float = 5.0, 
                     distance_3d: float = 5.0, screen_scale: float = 200.0) -> Tuple[float, float, float]:
    """Project a single 4D point to 2D screen coordinates.
    
    Performs two perspective projections:
    1. 4D → 3D (divide by W)
    2. 3D → 2D (divide by Z)
    
    Args:
        point_4d: A 4D point (x, y, z, w)
        distance_4d: 4D viewing distance
        distance_3d: 3D viewing distance
        screen_scale: Scale factor for screen coordinates
        
    Returns:
        (screen_x, screen_y, depth) where depth can be used for sorting
    """
    x, y, z, w = point_4d
    
    # 4D perspective: divide by (distance_4d - w)
    denom_4d = max(0.1, distance_4d - w)
    scale_4d = distance_4d / denom_4d
    x3 = x * scale_4d
    y3 = y * scale_4d
    z3 = z * scale_4d
    
    # 3D perspective: divide by (distance_3d - z3) or use z3 as depth
    denom_3d = max(0.1, distance_3d + z3)
    scale_3d = distance_3d / denom_3d
    
    screen_x = x3 * scale_3d * screen_scale
    screen_y = -y3 * scale_3d * screen_scale  # Flip Y for screen coords
    
    # Combined depth for sorting (larger = further)
    depth = denom_4d + z3 * 0.1
    
    return (screen_x, screen_y, depth)

# =============================================================================
# VECTOR ALGEBRA
# =============================================================================

def normalize_vector(v: np.ndarray) -> np.ndarray:
    """Normalize a vector to unit length.
    
    Args:
        v: Input vector (any dimension)
        
    Returns:
        Unit vector in the same direction, or zero vector if input is zero
    """
    norm = np.linalg.norm(v)
    if norm < 1e-10:
        return v.copy()
    return v / norm


def normalize_4d(v: Vector4D) -> Vector4D:
    """Normalize a 4D vector to unit length."""
    return normalize_vector(v).astype(np.float32)


def dot_product_4d(v1: Vector4D, v2: Vector4D) -> float:
    """Compute the dot product of two 4D vectors.
    
    The 4D dot product: v1·v2 = x1*x2 + y1*y2 + z1*z2 + w1*w2
    
    Geometric interpretation:
    - If result > 0: vectors point in similar directions
    - If result = 0: vectors are perpendicular
    - If result < 0: vectors point in opposite directions
    
    Args:
        v1: First 4D vector
        v2: Second 4D vector
        
    Returns:
        Scalar dot product
    """
    return float(np.dot(v1, v2))


def cross_product_4d(a: Vector4D, b: Vector4D, c: Vector4D) -> Vector4D:
    """Compute the 4D cross product of three vectors.
    
    In 4D, the cross product takes THREE vectors and produces a fourth
    vector perpendicular to all three. This is analogous to how the 3D
    cross product takes two vectors and produces a third perpendicular to both.
    
    Mathematically, this is the 4D analog computed via the determinant:
    
        | e_x  e_y  e_z  e_w |
        | a_x  a_y  a_z  a_w |
        | b_x  b_y  b_z  b_w |
        | c_x  c_y  c_z  c_w |
    
    where e_x, e_y, e_z, e_w are the standard basis vectors.
    
    Args:
        a: First 4D vector
        b: Second 4D vector
        c: Third 4D vector
        
    Returns:
        A 4D vector perpendicular to a, b, and c
    """
    # Compute cofactors (3x3 subdeterminants)
    # Sign pattern: +, -, +, -
    
    result_x = np.linalg.det(np.array([
        [a[1], a[2], a[3]],
        [b[1], b[2], b[3]],
        [c[1], c[2], c[3]]
    ], dtype=np.float64))
    
    result_y = -np.linalg.det(np.array([
        [a[0], a[2], a[3]],
        [b[0], b[2], b[3]],
        [c[0], c[2], c[3]]
    ], dtype=np.float64))
    
    result_z = np.linalg.det(np.array([
        [a[0], a[1], a[3]],
        [b[0], b[1], b[3]],
        [c[0], c[1], c[3]]
    ], dtype=np.float64))
    
    result_w = -np.linalg.det(np.array([
        [a[0], a[1], a[2]],
        [b[0], b[1], b[2]],
        [c[0], c[1], c[2]]
    ], dtype=np.float64))
    
    return np.array([result_x, result_y, result_z, result_w], dtype=np.float32)


def lerp_4d(a: Vector4D, b: Vector4D, t: float) -> Vector4D:
    """Linear interpolation between two 4D vectors.
    
    Args:
        a: Start vector (t=0)
        b: End vector (t=1)
        t: Interpolation parameter [0, 1]
        
    Returns:
        Interpolated vector: a + t*(b - a)
    """
    return (a * (1 - t) + b * t).astype(np.float32)


def slerp_4d(a: Vector4D, b: Vector4D, t: float) -> Vector4D:
    """Spherical linear interpolation between two 4D unit vectors.
    
    Interpolates along the great circle on the 4D hypersphere.
    
    Args:
        a: Start unit vector (t=0)
        b: End unit vector (t=1)
        t: Interpolation parameter [0, 1]
        
    Returns:
        Interpolated unit vector
    """
    # Normalize inputs
    a = normalize_4d(a)
    b = normalize_4d(b)
    
    # Compute angle between vectors
    dot = np.clip(np.dot(a, b), -1.0, 1.0)
    
    # If vectors are nearly parallel, use linear interpolation
    if abs(dot) > 0.9995:
        return normalize_4d(lerp_4d(a, b, t))
    
    theta = math.acos(dot)
    sin_theta = math.sin(theta)
    
    # Spherical interpolation
    factor_a = math.sin((1 - t) * theta) / sin_theta
    factor_b = math.sin(t * theta) / sin_theta
    
    return (a * factor_a + b * factor_b).astype(np.float32)

# =============================================================================
# VIEW / CAMERA MATRICES
# =============================================================================

def create_look_at_matrix(eye: Vector4D, target: Vector4D, up: Vector4D) -> Matrix4D:
    """Create an orthonormal 4D view matrix using Gram–Schmidt orthogonalization.
    
    Constructs a basis where:
    - Forward: direction from eye to target
    - Up: perpendicular to forward, as close to 'up' as possible
    - Right: perpendicular to forward and up
    - Ana: perpendicular to all three (the 4th basis vector)
    
    The returned matrix transforms world coordinates to view coordinates.
    Translation is NOT included - subtract eye position separately.
    
    Args:
        eye: Camera position in 4D
        target: Point the camera is looking at
        up: Approximate up direction (will be orthogonalized)
        
    Returns:
        4x4 orthonormal view matrix
    """
    eps = 1e-6

    def _gram_schmidt(vectors: List[np.ndarray]) -> List[np.ndarray]:
        """Orthogonalize a list of vectors using Gram-Schmidt."""
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

    # Forward: eye -> target
    forward = target - eye
    if np.linalg.norm(forward) < eps:
        forward = np.array([0.0, 0.0, 1.0, 0.0], dtype=np.float32)
    forward = normalize_vector(forward)

    # Up candidate (will be orthogonalized)
    up_candidate = np.asarray(up, dtype=np.float32)
    if np.linalg.norm(up_candidate) < eps or abs(np.dot(up_candidate, forward)) > 0.95:
        # Fallback: find axis with minimal alignment to forward
        for axis in np.eye(4, dtype=np.float32):
            if abs(np.dot(axis, forward)) < 0.8:
                up_candidate = axis
                break

    # Build orthonormal basis
    candidates = [
        forward, up_candidate,
        vec4(1, 0, 0, 0), vec4(0, 1, 0, 0),
        vec4(0, 0, 1, 0), vec4(0, 0, 0, 1),
    ]
    basis = _gram_schmidt(candidates)
    
    # Ensure we have 4 basis vectors
    while len(basis) < 4:
        for axis in np.eye(4, dtype=np.float32):
            basis = _gram_schmidt(basis + [axis])
            if len(basis) >= 4:
                break

    if len(basis) < 4:
        raise ValueError("Unable to construct a stable 4D view basis")

    # Assign basis vectors
    forward_vec = basis[0]
    up_vec = basis[1]
    right_vec = basis[2] if len(basis) > 2 else basis[1]
    ana_vec = basis[3]

    # Build view matrix (basis vectors as rows)
    view = np.eye(4, dtype=np.float32)
    view[0, :] = right_vec
    view[1, :] = up_vec
    view[2, :] = forward_vec
    view[3, :] = ana_vec
    
    return view


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def angle_between_4d(v1: Vector4D, v2: Vector4D) -> float:
    """Compute the angle between two 4D vectors in radians.
    
    Args:
        v1: First vector
        v2: Second vector
        
    Returns:
        Angle in radians [0, π]
    """
    v1_norm = normalize_4d(v1)
    v2_norm = normalize_4d(v2)
    dot = np.clip(np.dot(v1_norm, v2_norm), -1.0, 1.0)
    return float(math.acos(dot))


def project_onto_4d(v: Vector4D, onto: Vector4D) -> Vector4D:
    """Project vector v onto vector 'onto'.
    
    Args:
        v: Vector to project
        onto: Vector to project onto
        
    Returns:
        The projection of v onto 'onto'
    """
    onto_norm = normalize_4d(onto)
    return (np.dot(v, onto_norm) * onto_norm).astype(np.float32)


def reject_from_4d(v: Vector4D, from_vec: Vector4D) -> Vector4D:
    """Compute the rejection of v from 'from_vec' (component perpendicular).
    
    Args:
        v: Vector to reject
        from_vec: Vector to reject from
        
    Returns:
        The component of v perpendicular to 'from_vec'
    """
    return (v - project_onto_4d(v, from_vec)).astype(np.float32)


def reflect_4d(v: Vector4D, normal: Vector4D) -> Vector4D:
    """Reflect vector v across a hyperplane with the given normal.
    
    Args:
        v: Vector to reflect
        normal: Normal to the hyperplane (will be normalized)
        
    Returns:
        Reflected vector
    """
    n = normalize_4d(normal)
    return (v - 2 * np.dot(v, n) * n).astype(np.float32)
