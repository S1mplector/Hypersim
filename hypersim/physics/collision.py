"""4D Collision detection system.

Provides collision detection for 4D objects using bounding volumes
and precise intersection tests.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from hypersim.core.shape_4d import Shape4D


@dataclass
class BoundingHypersphere:
    """4D bounding hypersphere."""
    center: np.ndarray  # 4D point
    radius: float
    
    @classmethod
    def from_vertices(cls, vertices: List[np.ndarray]) -> "BoundingHypersphere":
        """Create bounding sphere from vertices using Ritter's algorithm."""
        if not vertices:
            return cls(np.zeros(4), 0.0)
        
        vertices = np.array(vertices)
        
        # Find centroid
        center = np.mean(vertices, axis=0)
        
        # Find radius as max distance from center
        distances = np.linalg.norm(vertices - center, axis=1)
        radius = np.max(distances)
        
        return cls(center=center.astype(np.float32), radius=float(radius))
    
    @classmethod
    def from_shape(cls, shape: "Shape4D") -> "BoundingHypersphere":
        """Create bounding sphere from a Shape4D."""
        vertices = shape.get_transformed_vertices()
        return cls.from_vertices(vertices)
    
    def contains_point(self, point: np.ndarray) -> bool:
        """Check if a point is inside the sphere."""
        return np.linalg.norm(point - self.center) <= self.radius
    
    def intersects(self, other: "BoundingHypersphere") -> bool:
        """Check intersection with another hypersphere."""
        distance = np.linalg.norm(self.center - other.center)
        return distance <= (self.radius + other.radius)


@dataclass
class BoundingHyperbox:
    """4D axis-aligned bounding hyperbox (AABB)."""
    min_corner: np.ndarray  # 4D point (x_min, y_min, z_min, w_min)
    max_corner: np.ndarray  # 4D point (x_max, y_max, z_max, w_max)
    
    @classmethod
    def from_vertices(cls, vertices: List[np.ndarray]) -> "BoundingHyperbox":
        """Create AABB from vertices."""
        if not vertices:
            return cls(np.zeros(4), np.zeros(4))
        
        vertices = np.array(vertices)
        min_corner = np.min(vertices, axis=0)
        max_corner = np.max(vertices, axis=0)
        
        return cls(
            min_corner=min_corner.astype(np.float32),
            max_corner=max_corner.astype(np.float32),
        )
    
    @classmethod
    def from_shape(cls, shape: "Shape4D") -> "BoundingHyperbox":
        """Create AABB from a Shape4D."""
        vertices = shape.get_transformed_vertices()
        return cls.from_vertices(vertices)
    
    @property
    def center(self) -> np.ndarray:
        """Get center of the box."""
        return (self.min_corner + self.max_corner) / 2
    
    @property
    def extents(self) -> np.ndarray:
        """Get half-extents of the box."""
        return (self.max_corner - self.min_corner) / 2
    
    def contains_point(self, point: np.ndarray) -> bool:
        """Check if a point is inside the box."""
        return np.all(point >= self.min_corner) and np.all(point <= self.max_corner)
    
    def intersects(self, other: "BoundingHyperbox") -> bool:
        """Check intersection with another hyperbox."""
        return np.all(self.min_corner <= other.max_corner) and \
               np.all(self.max_corner >= other.min_corner)


@dataclass
class CollisionInfo:
    """Information about a collision."""
    colliding: bool
    point: Optional[np.ndarray] = None  # Contact point
    normal: Optional[np.ndarray] = None  # Collision normal
    depth: float = 0.0  # Penetration depth
    object_a: Optional["Shape4D"] = None
    object_b: Optional["Shape4D"] = None


def check_sphere_sphere(
    a: BoundingHypersphere,
    b: BoundingHypersphere,
) -> CollisionInfo:
    """Check collision between two hyperspheres.
    
    Returns detailed collision information.
    """
    diff = b.center - a.center
    distance = np.linalg.norm(diff)
    sum_radii = a.radius + b.radius
    
    if distance > sum_radii:
        return CollisionInfo(colliding=False)
    
    # Calculate collision info
    if distance > 0.0001:
        normal = diff / distance
    else:
        normal = np.array([1, 0, 0, 0], dtype=np.float32)
    
    depth = sum_radii - distance
    point = a.center + normal * (a.radius - depth / 2)
    
    return CollisionInfo(
        colliding=True,
        point=point,
        normal=normal,
        depth=depth,
    )


def check_box_box(
    a: BoundingHyperbox,
    b: BoundingHyperbox,
) -> CollisionInfo:
    """Check collision between two hyperboxes.
    
    Uses separating axis theorem in 4D.
    """
    if not a.intersects(b):
        return CollisionInfo(colliding=False)
    
    # Find overlap in each axis
    overlaps = []
    for i in range(4):
        overlap_min = max(a.min_corner[i], b.min_corner[i])
        overlap_max = min(a.max_corner[i], b.max_corner[i])
        overlaps.append(overlap_max - overlap_min)
    
    # Minimum overlap axis is the collision normal
    min_axis = np.argmin(overlaps)
    depth = overlaps[min_axis]
    
    # Normal points from a to b
    normal = np.zeros(4, dtype=np.float32)
    normal[min_axis] = 1.0 if a.center[min_axis] < b.center[min_axis] else -1.0
    
    # Contact point is center of overlap region
    overlap_min = np.maximum(a.min_corner, b.min_corner)
    overlap_max = np.minimum(a.max_corner, b.max_corner)
    point = (overlap_min + overlap_max) / 2
    
    return CollisionInfo(
        colliding=True,
        point=point,
        normal=normal,
        depth=depth,
    )


def check_sphere_box(
    sphere: BoundingHypersphere,
    box: BoundingHyperbox,
) -> CollisionInfo:
    """Check collision between hypersphere and hyperbox."""
    # Find closest point on box to sphere center
    closest = np.clip(sphere.center, box.min_corner, box.max_corner)
    
    # Check distance
    diff = sphere.center - closest
    distance = np.linalg.norm(diff)
    
    if distance > sphere.radius:
        return CollisionInfo(colliding=False)
    
    # Collision detected
    if distance > 0.0001:
        normal = diff / distance
    else:
        # Sphere center is inside box
        # Find nearest face
        to_min = sphere.center - box.min_corner
        to_max = box.max_corner - sphere.center
        distances = np.concatenate([to_min, to_max])
        min_idx = np.argmin(distances)
        normal = np.zeros(4, dtype=np.float32)
        if min_idx < 4:
            normal[min_idx] = -1.0
        else:
            normal[min_idx - 4] = 1.0
        distance = distances[min_idx]
    
    depth = sphere.radius - distance
    point = closest
    
    return CollisionInfo(
        colliding=True,
        point=point,
        normal=normal,
        depth=depth,
    )


class CollisionDetector:
    """Manages collision detection for multiple objects."""
    
    def __init__(self):
        self._objects: List[Tuple["Shape4D", BoundingHypersphere]] = []
        self._collision_pairs: List[Tuple[int, int]] = []
    
    def add_object(self, shape: "Shape4D") -> int:
        """Add an object to collision detection.
        
        Returns:
            Index of the object
        """
        bounds = BoundingHypersphere.from_shape(shape)
        self._objects.append((shape, bounds))
        return len(self._objects) - 1
    
    def remove_object(self, index: int) -> None:
        """Remove an object by index."""
        if 0 <= index < len(self._objects):
            self._objects.pop(index)
    
    def update_bounds(self) -> None:
        """Update all bounding volumes."""
        for i, (shape, _) in enumerate(self._objects):
            self._objects[i] = (shape, BoundingHypersphere.from_shape(shape))
    
    def detect_collisions(self) -> List[CollisionInfo]:
        """Detect all collisions between objects.
        
        Returns:
            List of collision information
        """
        collisions = []
        n = len(self._objects)
        
        # Broad phase: sphere-sphere check
        for i in range(n):
            for j in range(i + 1, n):
                shape_a, bounds_a = self._objects[i]
                shape_b, bounds_b = self._objects[j]
                
                info = check_sphere_sphere(bounds_a, bounds_b)
                if info.colliding:
                    info.object_a = shape_a
                    info.object_b = shape_b
                    collisions.append(info)
        
        return collisions
    
    def raycast(
        self,
        origin: np.ndarray,
        direction: np.ndarray,
        max_distance: float = float('inf'),
    ) -> Optional[Tuple["Shape4D", float, np.ndarray]]:
        """Cast a ray and find the first intersection.
        
        Args:
            origin: Ray origin (4D)
            direction: Ray direction (4D, normalized)
            max_distance: Maximum distance to check
            
        Returns:
            Tuple of (hit_object, distance, hit_point) or None
        """
        direction = direction / np.linalg.norm(direction)
        closest_hit = None
        closest_dist = max_distance
        
        for shape, bounds in self._objects:
            # Sphere intersection test
            oc = origin - bounds.center
            a = np.dot(direction, direction)
            b = 2 * np.dot(oc, direction)
            c = np.dot(oc, oc) - bounds.radius ** 2
            
            discriminant = b * b - 4 * a * c
            if discriminant >= 0:
                t = (-b - np.sqrt(discriminant)) / (2 * a)
                if 0 < t < closest_dist:
                    closest_dist = t
                    hit_point = origin + direction * t
                    closest_hit = (shape, t, hit_point)
        
        return closest_hit
    
    def point_query(self, point: np.ndarray) -> List["Shape4D"]:
        """Find all objects containing a point.
        
        Args:
            point: 4D point to test
            
        Returns:
            List of shapes containing the point
        """
        results = []
        for shape, bounds in self._objects:
            if bounds.contains_point(point):
                results.append(shape)
        return results
