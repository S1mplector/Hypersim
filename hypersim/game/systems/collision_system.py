"""Collision detection system."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Set, Tuple, TYPE_CHECKING

import numpy as np

from hypersim.game.ecs.system import System
from hypersim.game.ecs.component import Transform, Collider, ColliderShape, DimensionAnchor

if TYPE_CHECKING:
    from hypersim.game.ecs.world import World
    from hypersim.game.ecs.entity import Entity


@dataclass
class CollisionPair:
    """Represents a collision between two entities."""
    entity_a: str
    entity_b: str
    overlap: float
    normal: np.ndarray


class CollisionSystem(System):
    """Detects collisions between entities."""
    
    priority = 30  # After physics
    required_components = (Transform, Collider)
    
    def __init__(self):
        self._collisions: List[CollisionPair] = []
        self._checked_pairs: Set[Tuple[str, str]] = set()
    
    @property
    def collisions(self) -> List[CollisionPair]:
        """Get collisions detected this frame."""
        return self._collisions
    
    def update(self, world: "World", dt: float) -> None:
        """Detect collisions between all collidable entities."""
        self._collisions.clear()
        self._checked_pairs.clear()
        
        entities = self.query(world)
        
        # Broad phase: group by dimension
        by_dimension: dict[str, List["Entity"]] = {}
        for entity in entities:
            anchor = entity.get(DimensionAnchor)
            dim = anchor.dimension_id if anchor else "default"
            if dim not in by_dimension:
                by_dimension[dim] = []
            by_dimension[dim].append(entity)
        
        # Narrow phase: check pairs within same dimension
        for dim_entities in by_dimension.values():
            for i, entity_a in enumerate(dim_entities):
                for entity_b in dim_entities[i + 1:]:
                    self._check_pair(entity_a, entity_b, world)
    
    def _check_pair(self, entity_a: "Entity", entity_b: "Entity", world: "World") -> None:
        """Check collision between two entities."""
        pair_key = tuple(sorted([entity_a.id, entity_b.id]))
        if pair_key in self._checked_pairs:
            return
        self._checked_pairs.add(pair_key)
        
        collider_a = entity_a.get(Collider)
        collider_b = entity_b.get(Collider)
        transform_a = entity_a.get(Transform)
        transform_b = entity_b.get(Transform)
        
        # Layer mask check
        if not (collider_a.mask & (1 << collider_b.layer)) or \
           not (collider_b.mask & (1 << collider_a.layer)):
            return
        
        # Get positions
        pos_a = transform_a.position + collider_a.offset[:len(transform_a.position)]
        pos_b = transform_b.position + collider_b.offset[:len(transform_b.position)]
        
        # Dispatch to appropriate collision check
        collision = self._test_collision(
            pos_a, collider_a.shape, collider_a.size,
            pos_b, collider_b.shape, collider_b.size,
        )
        
        if collision:
            overlap, normal = collision
            pair = CollisionPair(
                entity_a=entity_a.id,
                entity_b=entity_b.id,
                overlap=overlap,
                normal=normal,
            )
            self._collisions.append(pair)
            
            # Emit collision events
            world.emit(
                "collision",
                entity_a=entity_a.id,
                entity_b=entity_b.id,
                is_trigger=collider_a.is_trigger or collider_b.is_trigger,
            )
    
    def _test_collision(
        self,
        pos_a: np.ndarray, shape_a: ColliderShape, size_a: np.ndarray,
        pos_b: np.ndarray, shape_b: ColliderShape, size_b: np.ndarray,
    ) -> Tuple[float, np.ndarray] | None:
        """Test collision between two shapes. Returns (overlap, normal) or None."""
        
        # 1D: Segment-segment overlap
        if shape_a == ColliderShape.SEGMENT and shape_b == ColliderShape.SEGMENT:
            return self._segment_segment(pos_a[0], size_a[0], pos_b[0], size_b[0])
        
        # Point vs segment
        if shape_a == ColliderShape.POINT and shape_b == ColliderShape.SEGMENT:
            return self._point_segment(pos_a[0], pos_b[0], size_b[0])
        if shape_b == ColliderShape.POINT and shape_a == ColliderShape.SEGMENT:
            result = self._point_segment(pos_b[0], pos_a[0], size_a[0])
            if result:
                return (result[0], -result[1])
            return None
        
        # Circle-circle (2D)
        if shape_a == ColliderShape.CIRCLE and shape_b == ColliderShape.CIRCLE:
            return self._circle_circle(pos_a[:2], size_a[0], pos_b[:2], size_b[0])
        
        # AABB-AABB
        if shape_a == ColliderShape.AABB and shape_b == ColliderShape.AABB:
            return self._aabb_aabb(pos_a, size_a, pos_b, size_b)
        
        # Point-point (same position check)
        if shape_a == ColliderShape.POINT and shape_b == ColliderShape.POINT:
            dist = np.linalg.norm(pos_a - pos_b)
            if dist < 0.1:  # Threshold
                normal = np.zeros_like(pos_a)
                normal[0] = 1.0
                return (0.1 - dist, normal)
        
        return None
    
    def _segment_segment(
        self, x1: float, half_w1: float, x2: float, half_w2: float
    ) -> Tuple[float, np.ndarray] | None:
        """1D segment overlap test."""
        left1, right1 = x1 - half_w1, x1 + half_w1
        left2, right2 = x2 - half_w2, x2 + half_w2
        
        overlap = min(right1, right2) - max(left1, left2)
        if overlap > 0:
            normal = np.array([1.0, 0.0, 0.0, 0.0]) if x1 < x2 else np.array([-1.0, 0.0, 0.0, 0.0])
            return (overlap, normal)
        return None
    
    def _point_segment(
        self, px: float, seg_x: float, half_w: float
    ) -> Tuple[float, np.ndarray] | None:
        """Point inside segment test."""
        left, right = seg_x - half_w, seg_x + half_w
        if left <= px <= right:
            # Distance to nearest edge
            dist_left = px - left
            dist_right = right - px
            overlap = min(dist_left, dist_right)
            normal = np.array([1.0, 0.0, 0.0, 0.0]) if dist_left < dist_right else np.array([-1.0, 0.0, 0.0, 0.0])
            return (overlap, normal)
        return None
    
    def _circle_circle(
        self, c1: np.ndarray, r1: float, c2: np.ndarray, r2: float
    ) -> Tuple[float, np.ndarray] | None:
        """Circle-circle overlap test."""
        delta = c2 - c1
        dist = np.linalg.norm(delta)
        overlap = (r1 + r2) - dist
        
        if overlap > 0:
            if dist > 0.0001:
                normal_2d = delta / dist
            else:
                normal_2d = np.array([1.0, 0.0])
            normal = np.array([normal_2d[0], normal_2d[1], 0.0, 0.0])
            return (overlap, normal)
        return None
    
    def _aabb_aabb(
        self, pos_a: np.ndarray, size_a: np.ndarray, pos_b: np.ndarray, size_b: np.ndarray
    ) -> Tuple[float, np.ndarray] | None:
        """Axis-aligned bounding box overlap test."""
        dims = min(len(pos_a), len(pos_b), len(size_a), len(size_b))
        
        for i in range(dims):
            half_a = size_a[i] / 2 if i < len(size_a) else 0.5
            half_b = size_b[i] / 2 if i < len(size_b) else 0.5
            
            overlap = (half_a + half_b) - abs(pos_a[i] - pos_b[i])
            if overlap <= 0:
                return None
        
        # Find minimum overlap axis
        min_overlap = float('inf')
        min_axis = 0
        for i in range(dims):
            half_a = size_a[i] / 2 if i < len(size_a) else 0.5
            half_b = size_b[i] / 2 if i < len(size_b) else 0.5
            overlap = (half_a + half_b) - abs(pos_a[i] - pos_b[i])
            if overlap < min_overlap:
                min_overlap = overlap
                min_axis = i
        
        normal = np.zeros(4)
        normal[min_axis] = 1.0 if pos_a[min_axis] < pos_b[min_axis] else -1.0
        return (min_overlap, normal)
