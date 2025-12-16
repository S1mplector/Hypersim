"""Animation and keyframe system for 4D objects.

Provides tools for creating scripted animations with keyframes,
easing functions, and timeline management.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)
import math
import numpy as np

if TYPE_CHECKING:
    from hypersim.core.shape_4d import Shape4D


class EasingFunction(Enum):
    """Built-in easing functions for smooth animations."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    EASE_IN_QUAD = "ease_in_quad"
    EASE_OUT_QUAD = "ease_out_quad"
    EASE_IN_OUT_QUAD = "ease_in_out_quad"
    EASE_IN_CUBIC = "ease_in_cubic"
    EASE_OUT_CUBIC = "ease_out_cubic"
    EASE_IN_OUT_CUBIC = "ease_in_out_cubic"
    EASE_IN_ELASTIC = "ease_in_elastic"
    EASE_OUT_ELASTIC = "ease_out_elastic"
    EASE_OUT_BOUNCE = "ease_out_bounce"


def _apply_easing(t: float, easing: EasingFunction) -> float:
    """Apply an easing function to a normalized time value.
    
    Args:
        t: Normalized time (0 to 1)
        easing: The easing function to apply
        
    Returns:
        Eased value (0 to 1)
    """
    t = max(0.0, min(1.0, t))
    
    if easing == EasingFunction.LINEAR:
        return t
    elif easing == EasingFunction.EASE_IN:
        return t * t
    elif easing == EasingFunction.EASE_OUT:
        return 1 - (1 - t) ** 2
    elif easing == EasingFunction.EASE_IN_OUT:
        return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2
    elif easing == EasingFunction.EASE_IN_QUAD:
        return t * t
    elif easing == EasingFunction.EASE_OUT_QUAD:
        return 1 - (1 - t) * (1 - t)
    elif easing == EasingFunction.EASE_IN_OUT_QUAD:
        return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2
    elif easing == EasingFunction.EASE_IN_CUBIC:
        return t * t * t
    elif easing == EasingFunction.EASE_OUT_CUBIC:
        return 1 - (1 - t) ** 3
    elif easing == EasingFunction.EASE_IN_OUT_CUBIC:
        return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2
    elif easing == EasingFunction.EASE_IN_ELASTIC:
        if t == 0 or t == 1:
            return t
        return -math.pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * (2 * math.pi / 3))
    elif easing == EasingFunction.EASE_OUT_ELASTIC:
        if t == 0 or t == 1:
            return t
        return math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1
    elif easing == EasingFunction.EASE_OUT_BOUNCE:
        n1, d1 = 7.5625, 2.75
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375
    
    return t


@dataclass
class Keyframe:
    """A single keyframe in an animation.
    
    Attributes:
        time: Time of this keyframe in seconds
        property: The property being animated (e.g., "position", "rotation.xy")
        value: The value at this keyframe
        easing: Easing function to use when interpolating TO this keyframe
    """
    time: float
    property: str
    value: Any
    easing: EasingFunction = EasingFunction.LINEAR


@dataclass
class AnimationTrack:
    """A track containing keyframes for a single property.
    
    Attributes:
        property: The property being animated
        keyframes: List of keyframes sorted by time
    """
    property: str
    keyframes: List[Keyframe] = field(default_factory=list)
    
    def add_keyframe(
        self,
        time: float,
        value: Any,
        easing: EasingFunction = EasingFunction.LINEAR,
    ) -> None:
        """Add a keyframe to this track.
        
        Args:
            time: Time in seconds
            value: Value at this keyframe
            easing: Easing function for interpolation
        """
        kf = Keyframe(time=time, property=self.property, value=value, easing=easing)
        self.keyframes.append(kf)
        self.keyframes.sort(key=lambda k: k.time)
    
    def get_value_at(self, time: float) -> Optional[Any]:
        """Get the interpolated value at a given time.
        
        Args:
            time: Time in seconds
            
        Returns:
            Interpolated value, or None if no keyframes
        """
        if not self.keyframes:
            return None
        
        # Before first keyframe
        if time <= self.keyframes[0].time:
            return self.keyframes[0].value
        
        # After last keyframe
        if time >= self.keyframes[-1].time:
            return self.keyframes[-1].value
        
        # Find surrounding keyframes
        for i in range(len(self.keyframes) - 1):
            kf1 = self.keyframes[i]
            kf2 = self.keyframes[i + 1]
            
            if kf1.time <= time <= kf2.time:
                # Calculate normalized time
                duration = kf2.time - kf1.time
                if duration == 0:
                    return kf2.value
                
                t = (time - kf1.time) / duration
                t = _apply_easing(t, kf2.easing)
                
                # Interpolate based on value type
                return self._interpolate(kf1.value, kf2.value, t)
        
        return self.keyframes[-1].value
    
    def _interpolate(self, v1: Any, v2: Any, t: float) -> Any:
        """Interpolate between two values.
        
        Args:
            v1: Start value
            v2: End value
            t: Interpolation factor (0 to 1)
            
        Returns:
            Interpolated value
        """
        # Handle numpy arrays
        if isinstance(v1, np.ndarray) and isinstance(v2, np.ndarray):
            return v1 + (v2 - v1) * t
        
        # Handle lists/tuples
        if isinstance(v1, (list, tuple)) and isinstance(v2, (list, tuple)):
            result = [a + (b - a) * t for a, b in zip(v1, v2)]
            return type(v1)(result)
        
        # Handle numbers
        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            return v1 + (v2 - v1) * t
        
        # Handle dicts (for rotation)
        if isinstance(v1, dict) and isinstance(v2, dict):
            return {k: v1.get(k, 0) + (v2.get(k, 0) - v1.get(k, 0)) * t for k in set(v1) | set(v2)}
        
        # Non-interpolatable: step at midpoint
        return v1 if t < 0.5 else v2
    
    @property
    def duration(self) -> float:
        """Get the duration of this track."""
        if not self.keyframes:
            return 0.0
        return self.keyframes[-1].time - self.keyframes[0].time


class Animation:
    """A complete animation consisting of multiple tracks.
    
    Can animate position, rotation, scale, and custom properties
    of Shape4D objects.
    """
    
    def __init__(self, name: str = "Untitled"):
        """Initialize an animation.
        
        Args:
            name: Name of this animation
        """
        self.name = name
        self.tracks: Dict[str, AnimationTrack] = {}
        self._current_time: float = 0.0
        self._playing: bool = False
        self._loop: bool = False
        self._speed: float = 1.0
    
    def add_track(self, property: str) -> AnimationTrack:
        """Add or get an animation track for a property.
        
        Args:
            property: Property name (e.g., "position", "rotation.xy", "scale")
            
        Returns:
            The AnimationTrack for this property
        """
        if property not in self.tracks:
            self.tracks[property] = AnimationTrack(property=property)
        return self.tracks[property]
    
    def keyframe(
        self,
        time: float,
        property: str,
        value: Any,
        easing: EasingFunction = EasingFunction.LINEAR,
    ) -> "Animation":
        """Add a keyframe (fluent API).
        
        Args:
            time: Time in seconds
            property: Property name
            value: Value at this keyframe
            easing: Easing function
            
        Returns:
            Self for chaining
        """
        track = self.add_track(property)
        track.add_keyframe(time, value, easing)
        return self
    
    @property
    def duration(self) -> float:
        """Get the total duration of this animation."""
        if not self.tracks:
            return 0.0
        return max(track.duration for track in self.tracks.values())
    
    @property
    def current_time(self) -> float:
        """Get the current playback time."""
        return self._current_time
    
    @current_time.setter
    def current_time(self, value: float) -> None:
        """Set the current playback time."""
        self._current_time = max(0.0, value)
        if self._loop and self._current_time > self.duration:
            self._current_time = self._current_time % self.duration
    
    def play(self, loop: bool = False, speed: float = 1.0) -> None:
        """Start playing the animation.
        
        Args:
            loop: Whether to loop
            speed: Playback speed multiplier
        """
        self._playing = True
        self._loop = loop
        self._speed = speed
    
    def pause(self) -> None:
        """Pause playback."""
        self._playing = False
    
    def stop(self) -> None:
        """Stop and reset playback."""
        self._playing = False
        self._current_time = 0.0
    
    def update(self, dt: float) -> bool:
        """Update the animation.
        
        Args:
            dt: Delta time in seconds
            
        Returns:
            True if animation is still playing, False if finished
        """
        if not self._playing:
            return False
        
        self._current_time += dt * self._speed
        
        if self._current_time >= self.duration:
            if self._loop:
                self._current_time = self._current_time % self.duration
            else:
                self._current_time = self.duration
                self._playing = False
                return False
        
        return True
    
    def apply_to(self, obj: "Shape4D") -> None:
        """Apply the current animation state to an object.
        
        Args:
            obj: The Shape4D object to animate
        """
        for prop, track in self.tracks.items():
            value = track.get_value_at(self._current_time)
            if value is None:
                continue
            
            # Handle different property types
            if prop == "position":
                obj.set_position(value)
            elif prop == "scale":
                obj.set_scale(value)
            elif prop == "rotation":
                # Full rotation dict
                obj.rotation = dict(value)
                obj.invalidate_cache()
            elif prop.startswith("rotation."):
                # Single rotation plane
                plane = prop.split(".")[1]
                obj.rotation[plane] = value
                obj.invalidate_cache()
            elif prop == "visible":
                obj.visible = bool(value)
            elif hasattr(obj, prop):
                setattr(obj, prop, value)
    
    def get_state_at(self, time: float) -> Dict[str, Any]:
        """Get all property values at a given time.
        
        Args:
            time: Time in seconds
            
        Returns:
            Dict mapping property names to values
        """
        state = {}
        for prop, track in self.tracks.items():
            value = track.get_value_at(time)
            if value is not None:
                state[prop] = value
        return state


class AnimationSequence:
    """A sequence of animations played one after another."""
    
    def __init__(self):
        self.animations: List[Animation] = []
        self._current_index: int = 0
        self._playing: bool = False
        self._loop: bool = False
    
    def add(self, animation: Animation) -> "AnimationSequence":
        """Add an animation to the sequence.
        
        Args:
            animation: Animation to add
            
        Returns:
            Self for chaining
        """
        self.animations.append(animation)
        return self
    
    @property
    def duration(self) -> float:
        """Get total duration of the sequence."""
        return sum(a.duration for a in self.animations)
    
    @property
    def current_animation(self) -> Optional[Animation]:
        """Get the currently playing animation."""
        if 0 <= self._current_index < len(self.animations):
            return self.animations[self._current_index]
        return None
    
    def play(self, loop: bool = False) -> None:
        """Start playing the sequence."""
        self._playing = True
        self._loop = loop
        self._current_index = 0
        if self.current_animation:
            self.current_animation.play()
    
    def stop(self) -> None:
        """Stop the sequence."""
        self._playing = False
        self._current_index = 0
        for anim in self.animations:
            anim.stop()
    
    def update(self, dt: float) -> bool:
        """Update the sequence.
        
        Args:
            dt: Delta time
            
        Returns:
            True if still playing
        """
        if not self._playing or not self.animations:
            return False
        
        current = self.current_animation
        if current is None:
            return False
        
        if not current.update(dt):
            # Current animation finished
            self._current_index += 1
            
            if self._current_index >= len(self.animations):
                if self._loop:
                    self._current_index = 0
                    self.animations[0].stop()
                    self.animations[0].play()
                else:
                    self._playing = False
                    return False
            else:
                self.animations[self._current_index].play()
        
        return True
    
    def apply_to(self, obj: "Shape4D") -> None:
        """Apply current state to an object."""
        if self.current_animation:
            self.current_animation.apply_to(obj)


def create_rotation_animation(
    duration: float = 2.0,
    rotations: Optional[Dict[str, float]] = None,
    easing: EasingFunction = EasingFunction.EASE_IN_OUT,
) -> Animation:
    """Create a simple rotation animation.
    
    Args:
        duration: Animation duration in seconds
        rotations: Dict of rotation planes to amounts (radians)
        easing: Easing function
        
    Returns:
        Configured Animation
    """
    if rotations is None:
        rotations = {"xy": 2 * math.pi}
    
    anim = Animation(name="Rotation")
    
    for plane, amount in rotations.items():
        track = anim.add_track(f"rotation.{plane}")
        track.add_keyframe(0.0, 0.0, EasingFunction.LINEAR)
        track.add_keyframe(duration, amount, easing)
    
    return anim


def create_position_animation(
    start: List[float],
    end: List[float],
    duration: float = 1.0,
    easing: EasingFunction = EasingFunction.EASE_IN_OUT,
) -> Animation:
    """Create a simple position animation.
    
    Args:
        start: Starting position [x, y, z, w]
        end: Ending position [x, y, z, w]
        duration: Animation duration
        easing: Easing function
        
    Returns:
        Configured Animation
    """
    anim = Animation(name="Position")
    track = anim.add_track("position")
    track.add_keyframe(0.0, np.array(start, dtype=np.float32), EasingFunction.LINEAR)
    track.add_keyframe(duration, np.array(end, dtype=np.float32), easing)
    return anim


def create_scale_pulse(
    min_scale: float = 0.8,
    max_scale: float = 1.2,
    duration: float = 1.0,
) -> Animation:
    """Create a pulsing scale animation.
    
    Args:
        min_scale: Minimum scale
        max_scale: Maximum scale
        duration: Full cycle duration
        
    Returns:
        Configured Animation
    """
    anim = Animation(name="Scale Pulse")
    track = anim.add_track("scale")
    track.add_keyframe(0.0, min_scale, EasingFunction.LINEAR)
    track.add_keyframe(duration / 2, max_scale, EasingFunction.EASE_IN_OUT)
    track.add_keyframe(duration, min_scale, EasingFunction.EASE_IN_OUT)
    return anim
