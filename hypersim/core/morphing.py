"""Object morphing and interpolation for 4D shapes.

Provides smooth transitions between different 4D objects
by interpolating vertices, with support for different
interpolation strategies.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Tuple, Optional, Callable, TYPE_CHECKING
import numpy as np
import math

if TYPE_CHECKING:
    from .shape_4d import Shape4D


class MorphStrategy(Enum):
    """Strategies for morphing between shapes with different vertex counts."""
    NEAREST = auto()      # Map to nearest vertex
    DISTRIBUTE = auto()   # Distribute vertices evenly
    CENTROID = auto()     # Morph to/from centroid
    SPHERE = auto()       # Morph via sphere projection


class EasingType(Enum):
    """Easing functions for morphing."""
    LINEAR = auto()
    EASE_IN = auto()
    EASE_OUT = auto()
    EASE_IN_OUT = auto()
    ELASTIC = auto()
    BOUNCE = auto()
    OVERSHOOT = auto()


def apply_easing(t: float, easing: EasingType) -> float:
    """Apply an easing function to parameter t."""
    t = max(0.0, min(1.0, t))
    
    if easing == EasingType.LINEAR:
        return t
    elif easing == EasingType.EASE_IN:
        return t * t * t
    elif easing == EasingType.EASE_OUT:
        return 1 - (1 - t) ** 3
    elif easing == EasingType.EASE_IN_OUT:
        return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2
    elif easing == EasingType.ELASTIC:
        if t == 0 or t == 1:
            return t
        return -math.pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * (2 * math.pi / 3)) if t < 1 else 1
    elif easing == EasingType.BOUNCE:
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375
    elif easing == EasingType.OVERSHOOT:
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)
    
    return t


@dataclass
class MorphState:
    """State of a morphing operation."""
    source_vertices: np.ndarray
    target_vertices: np.ndarray
    source_edges: List[Tuple[int, int]]
    target_edges: List[Tuple[int, int]]
    progress: float = 0.0
    easing: EasingType = EasingType.EASE_IN_OUT
    
    @property
    def current_vertices(self) -> np.ndarray:
        """Get interpolated vertices at current progress."""
        t = apply_easing(self.progress, self.easing)
        return self.source_vertices + (self.target_vertices - self.source_vertices) * t
    
    @property
    def current_edges(self) -> List[Tuple[int, int]]:
        """Get edges at current progress (blend based on progress)."""
        if self.progress < 0.5:
            return self.source_edges
        return self.target_edges


class ShapeMorpher:
    """Handles morphing between 4D shapes.
    
    Supports shapes with different vertex counts by using
    various mapping strategies.
    """
    
    def __init__(
        self,
        strategy: MorphStrategy = MorphStrategy.DISTRIBUTE,
        easing: EasingType = EasingType.EASE_IN_OUT,
    ):
        self.strategy = strategy
        self.easing = easing
        self._morph_state: Optional[MorphState] = None
        self._is_morphing = False
        self._duration = 1.0
        self._elapsed = 0.0
    
    def start_morph(
        self,
        source: "Shape4D",
        target: "Shape4D",
        duration: float = 1.0,
    ) -> None:
        """Start morphing from source to target shape.
        
        Args:
            source: Starting shape
            target: Target shape
            duration: Morph duration in seconds
        """
        source_verts = np.array(source.get_transformed_vertices(), dtype=np.float32)
        target_verts = np.array(target.get_transformed_vertices(), dtype=np.float32)
        
        # Match vertex counts
        matched_source, matched_target = self._match_vertices(
            source_verts, target_verts
        )
        
        self._morph_state = MorphState(
            source_vertices=matched_source,
            target_vertices=matched_target,
            source_edges=list(source.edges),
            target_edges=list(target.edges),
            progress=0.0,
            easing=self.easing,
        )
        
        self._duration = duration
        self._elapsed = 0.0
        self._is_morphing = True
    
    def _match_vertices(
        self,
        source: np.ndarray,
        target: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Match vertex arrays to same size.
        
        Args:
            source: Source vertices (N, 4)
            target: Target vertices (M, 4)
            
        Returns:
            Matched arrays of same size
        """
        n_source = len(source)
        n_target = len(target)
        
        if n_source == n_target:
            # Same size - optionally reorder for better matching
            return source, self._reorder_nearest(source, target)
        
        # Need to adjust sizes
        max_size = max(n_source, n_target)
        
        if self.strategy == MorphStrategy.NEAREST:
            return self._match_nearest(source, target, max_size)
        elif self.strategy == MorphStrategy.DISTRIBUTE:
            return self._match_distribute(source, target, max_size)
        elif self.strategy == MorphStrategy.CENTROID:
            return self._match_centroid(source, target, max_size)
        elif self.strategy == MorphStrategy.SPHERE:
            return self._match_sphere(source, target, max_size)
        
        return self._match_distribute(source, target, max_size)
    
    def _reorder_nearest(
        self,
        source: np.ndarray,
        target: np.ndarray,
    ) -> np.ndarray:
        """Reorder target vertices to minimize total distance to source."""
        n = len(source)
        reordered = np.zeros_like(target)
        used = set()
        
        for i in range(n):
            best_j = -1
            best_dist = float('inf')
            
            for j in range(n):
                if j in used:
                    continue
                dist = np.linalg.norm(source[i] - target[j])
                if dist < best_dist:
                    best_dist = dist
                    best_j = j
            
            if best_j >= 0:
                reordered[i] = target[best_j]
                used.add(best_j)
        
        return reordered
    
    def _match_nearest(
        self,
        source: np.ndarray,
        target: np.ndarray,
        size: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Match by mapping to nearest vertices."""
        matched_source = np.zeros((size, 4), dtype=np.float32)
        matched_target = np.zeros((size, 4), dtype=np.float32)
        
        # Expand smaller array by duplicating nearest vertices
        for i in range(size):
            if i < len(source):
                matched_source[i] = source[i]
            else:
                # Find nearest in source
                idx = i % len(source)
                matched_source[i] = source[idx]
            
            if i < len(target):
                matched_target[i] = target[i]
            else:
                idx = i % len(target)
                matched_target[i] = target[idx]
        
        return matched_source, matched_target
    
    def _match_distribute(
        self,
        source: np.ndarray,
        target: np.ndarray,
        size: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Match by distributing vertices evenly."""
        matched_source = np.zeros((size, 4), dtype=np.float32)
        matched_target = np.zeros((size, 4), dtype=np.float32)
        
        for i in range(size):
            # Interpolate along vertex list
            t_source = i / max(1, size - 1) * (len(source) - 1)
            t_target = i / max(1, size - 1) * (len(target) - 1)
            
            # Linear interpolation
            idx_s = int(t_source)
            frac_s = t_source - idx_s
            if idx_s >= len(source) - 1:
                matched_source[i] = source[-1]
            else:
                matched_source[i] = source[idx_s] * (1 - frac_s) + source[idx_s + 1] * frac_s
            
            idx_t = int(t_target)
            frac_t = t_target - idx_t
            if idx_t >= len(target) - 1:
                matched_target[i] = target[-1]
            else:
                matched_target[i] = target[idx_t] * (1 - frac_t) + target[idx_t + 1] * frac_t
        
        return matched_source, matched_target
    
    def _match_centroid(
        self,
        source: np.ndarray,
        target: np.ndarray,
        size: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Match via centroid - extra vertices collapse to center."""
        matched_source = np.zeros((size, 4), dtype=np.float32)
        matched_target = np.zeros((size, 4), dtype=np.float32)
        
        source_centroid = np.mean(source, axis=0)
        target_centroid = np.mean(target, axis=0)
        
        for i in range(size):
            if i < len(source):
                matched_source[i] = source[i]
            else:
                matched_source[i] = source_centroid
            
            if i < len(target):
                matched_target[i] = target[i]
            else:
                matched_target[i] = target_centroid
        
        return matched_source, matched_target
    
    def _match_sphere(
        self,
        source: np.ndarray,
        target: np.ndarray,
        size: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Match via sphere projection - morph through spherical form."""
        matched_source = np.zeros((size, 4), dtype=np.float32)
        matched_target = np.zeros((size, 4), dtype=np.float32)
        
        # Normalize to unit sphere
        source_norms = np.linalg.norm(source, axis=1, keepdims=True)
        source_norms[source_norms < 0.001] = 1
        source_unit = source / source_norms
        
        target_norms = np.linalg.norm(target, axis=1, keepdims=True)
        target_norms[target_norms < 0.001] = 1
        target_unit = target / target_norms
        
        # Match using distribute strategy on unit sphere
        return self._match_distribute(source, target, size)
    
    def update(self, dt: float) -> bool:
        """Update the morph progress.
        
        Args:
            dt: Delta time in seconds
            
        Returns:
            True if still morphing, False if complete
        """
        if not self._is_morphing or self._morph_state is None:
            return False
        
        self._elapsed += dt
        self._morph_state.progress = min(1.0, self._elapsed / self._duration)
        
        if self._morph_state.progress >= 1.0:
            self._is_morphing = False
            return False
        
        return True
    
    @property
    def is_morphing(self) -> bool:
        """Check if currently morphing."""
        return self._is_morphing
    
    @property
    def progress(self) -> float:
        """Get current morph progress (0-1)."""
        return self._morph_state.progress if self._morph_state else 0.0
    
    @property
    def vertices(self) -> Optional[np.ndarray]:
        """Get current interpolated vertices."""
        return self._morph_state.current_vertices if self._morph_state else None
    
    @property
    def edges(self) -> List[Tuple[int, int]]:
        """Get current edges."""
        return self._morph_state.current_edges if self._morph_state else []
    
    def cancel(self) -> None:
        """Cancel current morph."""
        self._is_morphing = False
        self._morph_state = None


class MorphableShape:
    """A shape that can morph between different forms.
    
    Wraps a Shape4D and provides morphing capabilities.
    """
    
    def __init__(self, initial_shape: "Shape4D"):
        self._current_shape = initial_shape
        self._morpher = ShapeMorpher()
        self._cached_vertices: Optional[np.ndarray] = None
        self._cached_edges: List[Tuple[int, int]] = []
    
    def morph_to(
        self,
        target: "Shape4D",
        duration: float = 1.0,
        strategy: MorphStrategy = MorphStrategy.DISTRIBUTE,
        easing: EasingType = EasingType.EASE_IN_OUT,
    ) -> None:
        """Start morphing to a new shape.
        
        Args:
            target: Target shape
            duration: Morph duration
            strategy: Vertex matching strategy
            easing: Easing function
        """
        self._morpher.strategy = strategy
        self._morpher.easing = easing
        self._morpher.start_morph(self._current_shape, target, duration)
    
    def update(self, dt: float) -> None:
        """Update morph state."""
        if self._morpher.is_morphing:
            self._morpher.update(dt)
            self._cached_vertices = self._morpher.vertices
            self._cached_edges = self._morpher.edges
    
    @property
    def is_morphing(self) -> bool:
        return self._morpher.is_morphing
    
    @property
    def vertices(self) -> np.ndarray:
        """Get current vertices."""
        if self._morpher.is_morphing and self._cached_vertices is not None:
            return self._cached_vertices
        return np.array(self._current_shape.get_transformed_vertices())
    
    @property
    def edges(self) -> List[Tuple[int, int]]:
        """Get current edges."""
        if self._morpher.is_morphing:
            return self._cached_edges
        return list(self._current_shape.edges)
