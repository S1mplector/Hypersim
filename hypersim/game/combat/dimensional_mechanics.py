"""Unique dimensional combat mechanics that differentiate from Undertale.

This module introduces mechanics based on the dimensional theme:
1. DIMENSIONAL SHIFT - Player can shift perception during combat
2. PERCEPTION ATTACKS - Enemies manipulate dimensional perception  
3. REALITY WARPING - Battle box changes shape/properties
4. GEOMETRIC RESONANCE - Attacks resonate with geometric forms
5. TRANSCENDENCE GAUGE - Build up to temporary 4D perception
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple

from .core import PlayerSoul, SoulMode, CombatStats


class PerceptionLevel(Enum):
    """Player's current dimensional perception in combat."""
    POINT = "0d"      # Collapsed - can only exist at one spot (invulnerable but frozen)
    LINE = "1d"       # Can only dodge left/right
    PLANE = "2d"      # Normal 2D movement (default)
    VOLUME = "3d"     # Can "phase" briefly through bullets by moving in Z
    HYPER = "4d"      # Transcendent - see bullet trajectories, slow time


class RealityWarpType(Enum):
    """Types of battle box warping effects."""
    NONE = auto()
    SHRINK = auto()           # Box slowly shrinks
    EXPAND = auto()           # Box expands
    ROTATE = auto()           # Box rotates (visual + affects movement)
    FOLD = auto()             # Box folds in half (wrapping movement)
    TESSERACT = auto()        # Box becomes 4D (corners connect)
    OSCILLATE = auto()        # Box pulses in size
    SPLIT = auto()            # Box splits into multiple sections
    GRAVITY_SHIFT = auto()    # Gravity changes direction
    MIRROR = auto()           # Mirrored controls


@dataclass
class DimensionalShiftState:
    """Manages the player's ability to shift dimensional perception."""
    
    current_perception: PerceptionLevel = PerceptionLevel.PLANE
    
    # Shift resources
    shift_energy: float = 100.0
    max_shift_energy: float = 100.0
    energy_regen_rate: float = 5.0  # Per second
    
    # Shift costs
    shift_costs: Dict[PerceptionLevel, float] = field(default_factory=lambda: {
        PerceptionLevel.POINT: 30.0,    # Expensive - invuln
        PerceptionLevel.LINE: 10.0,     # Cheap - restriction
        PerceptionLevel.PLANE: 0.0,     # Default - free
        PerceptionLevel.VOLUME: 25.0,   # Phase ability
        PerceptionLevel.HYPER: 50.0,    # Most powerful
    })
    
    # Active shift
    shift_active: bool = False
    shift_duration: float = 0.0
    shift_max_duration: float = 3.0
    
    # Cooldowns
    shift_cooldown: float = 0.0
    cooldown_duration: float = 2.0
    
    # Transcendence (earned through combat)
    transcendence_gauge: float = 0.0
    transcendence_max: float = 100.0
    transcendence_active: bool = False
    transcendence_duration: float = 0.0
    
    def can_shift_to(self, level: PerceptionLevel) -> bool:
        """Check if player can shift to a perception level."""
        if self.shift_cooldown > 0:
            return False
        if level == self.current_perception:
            return False
        cost = self.shift_costs.get(level, 50.0)
        return self.shift_energy >= cost
    
    def shift_to(self, level: PerceptionLevel) -> bool:
        """Attempt to shift perception."""
        if not self.can_shift_to(level):
            return False
        
        cost = self.shift_costs.get(level, 50.0)
        self.shift_energy -= cost
        self.current_perception = level
        self.shift_active = True
        self.shift_duration = 0.0
        
        return True
    
    def update(self, dt: float) -> None:
        """Update shift state."""
        # Regenerate energy when in default state
        if self.current_perception == PerceptionLevel.PLANE and not self.shift_active:
            self.shift_energy = min(
                self.max_shift_energy,
                self.shift_energy + self.energy_regen_rate * dt
            )
        
        # Update cooldown
        if self.shift_cooldown > 0:
            self.shift_cooldown -= dt
        
        # Update active shift duration
        if self.shift_active:
            self.shift_duration += dt
            if self.shift_duration >= self.shift_max_duration:
                self._end_shift()
        
        # Update transcendence
        if self.transcendence_active:
            self.transcendence_duration -= dt
            if self.transcendence_duration <= 0:
                self._end_transcendence()
    
    def _end_shift(self) -> None:
        """End the current shift."""
        self.shift_active = False
        self.shift_cooldown = self.cooldown_duration
        
        # Return to plane perception
        if self.current_perception != PerceptionLevel.PLANE:
            self.current_perception = PerceptionLevel.PLANE
    
    def add_transcendence(self, amount: float) -> None:
        """Add to transcendence gauge (from grazing, ACTs, etc.)."""
        if not self.transcendence_active:
            self.transcendence_gauge = min(
                self.transcendence_max,
                self.transcendence_gauge + amount
            )
    
    def can_transcend(self) -> bool:
        """Check if transcendence can be activated."""
        return (self.transcendence_gauge >= self.transcendence_max and 
                not self.transcendence_active)
    
    def activate_transcendence(self) -> bool:
        """Activate 4D transcendence mode."""
        if not self.can_transcend():
            return False
        
        self.transcendence_active = True
        self.transcendence_duration = 5.0  # 5 seconds of power
        self.transcendence_gauge = 0.0
        self.current_perception = PerceptionLevel.HYPER
        
        return True
    
    def _end_transcendence(self) -> None:
        """End transcendence mode."""
        self.transcendence_active = False
        self.current_perception = PerceptionLevel.PLANE


@dataclass
class RealityWarpEffect:
    """An active reality warp effect on the battle box."""
    warp_type: RealityWarpType
    intensity: float = 1.0
    duration: float = 5.0
    elapsed: float = 0.0
    
    # Effect parameters
    rotation_angle: float = 0.0
    rotation_speed: float = 0.5
    scale_factor: float = 1.0
    fold_axis: str = "horizontal"  # or "vertical"
    gravity_direction: Tuple[float, float] = (0.0, 1.0)
    
    @property
    def progress(self) -> float:
        return self.elapsed / self.duration if self.duration > 0 else 1.0
    
    @property
    def active(self) -> bool:
        return self.elapsed < self.duration
    
    def update(self, dt: float) -> None:
        """Update the warp effect."""
        self.elapsed += dt
        
        if self.warp_type == RealityWarpType.ROTATE:
            self.rotation_angle += self.rotation_speed * dt * self.intensity
        
        elif self.warp_type == RealityWarpType.OSCILLATE:
            self.scale_factor = 1.0 + 0.3 * math.sin(self.elapsed * 3) * self.intensity
        
        elif self.warp_type == RealityWarpType.SHRINK:
            self.scale_factor = max(0.4, 1.0 - self.progress * 0.6 * self.intensity)
        
        elif self.warp_type == RealityWarpType.EXPAND:
            self.scale_factor = min(1.5, 1.0 + self.progress * 0.5 * self.intensity)


@dataclass  
class GeometricResonance:
    """Tracks resonance with geometric forms for bonus effects."""
    
    # Resonance with each dimensional form
    point_resonance: float = 0.0    # Stillness, focus
    line_resonance: float = 0.0     # Direction, determination
    plane_resonance: float = 0.0    # Balance, awareness
    volume_resonance: float = 0.0   # Depth, understanding
    hyper_resonance: float = 0.0    # Transcendence, unity
    
    max_resonance: float = 100.0
    decay_rate: float = 2.0  # Per second
    
    def add_resonance(self, form: str, amount: float) -> None:
        """Add resonance to a geometric form."""
        if form == "point":
            self.point_resonance = min(self.max_resonance, self.point_resonance + amount)
        elif form == "line":
            self.line_resonance = min(self.max_resonance, self.line_resonance + amount)
        elif form == "plane":
            self.plane_resonance = min(self.max_resonance, self.plane_resonance + amount)
        elif form == "volume":
            self.volume_resonance = min(self.max_resonance, self.volume_resonance + amount)
        elif form == "hyper":
            self.hyper_resonance = min(self.max_resonance, self.hyper_resonance + amount)
    
    def update(self, dt: float) -> None:
        """Decay resonance over time."""
        decay = self.decay_rate * dt
        self.point_resonance = max(0, self.point_resonance - decay)
        self.line_resonance = max(0, self.line_resonance - decay)
        self.plane_resonance = max(0, self.plane_resonance - decay)
        self.volume_resonance = max(0, self.volume_resonance - decay)
        self.hyper_resonance = max(0, self.hyper_resonance - decay)
    
    def get_dominant_form(self) -> Optional[str]:
        """Get the form with highest resonance."""
        forms = {
            "point": self.point_resonance,
            "line": self.line_resonance,
            "plane": self.plane_resonance,
            "volume": self.volume_resonance,
            "hyper": self.hyper_resonance,
        }
        
        max_form = max(forms.items(), key=lambda x: x[1])
        if max_form[1] > 20:  # Threshold for dominance
            return max_form[0]
        return None
    
    def get_damage_multiplier(self) -> float:
        """Get damage multiplier based on resonance."""
        total = (self.point_resonance + self.line_resonance + 
                 self.plane_resonance + self.volume_resonance + 
                 self.hyper_resonance)
        return 1.0 + (total / self.max_resonance / 5) * 0.5  # Up to 1.5x


@dataclass
class GrazingSystem:
    """Tracks near-misses (grazing) for bonus rewards."""
    
    graze_distance: float = 20.0  # Pixels for a graze
    graze_count: int = 0
    combo_count: int = 0
    combo_timer: float = 0.0
    combo_timeout: float = 0.5  # Seconds to maintain combo
    
    # Rewards
    transcendence_per_graze: float = 2.0
    resonance_per_graze: float = 1.0
    
    # Tracking
    grazed_bullets: set = field(default_factory=set)
    
    def check_graze(self, soul_x: float, soul_y: float, 
                    bullet_id: int, bullet_x: float, bullet_y: float,
                    bullet_radius: float, soul_radius: float) -> bool:
        """Check if soul grazed a bullet."""
        if bullet_id in self.grazed_bullets:
            return False
        
        dist = math.sqrt((soul_x - bullet_x)**2 + (soul_y - bullet_y)**2)
        hit_dist = bullet_radius + soul_radius
        graze_dist = hit_dist + self.graze_distance
        
        if hit_dist < dist <= graze_dist:
            self.grazed_bullets.add(bullet_id)
            self.graze_count += 1
            self.combo_count += 1
            self.combo_timer = self.combo_timeout
            return True
        
        return False
    
    def update(self, dt: float) -> None:
        """Update combo timer."""
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo_count = 0
    
    def get_rewards(self) -> Tuple[float, float]:
        """Get transcendence and resonance rewards for grazing."""
        combo_mult = 1.0 + self.combo_count * 0.1
        return (
            self.transcendence_per_graze * combo_mult,
            self.resonance_per_graze * combo_mult
        )
    
    def reset(self) -> None:
        """Reset for new attack phase."""
        self.grazed_bullets.clear()


class PerceptionAttack:
    """Special attacks that manipulate player perception."""
    
    @staticmethod
    def dimension_collapse(shift_state: DimensionalShiftState) -> str:
        """Force player to lower perception."""
        if shift_state.current_perception == PerceptionLevel.PLANE:
            shift_state.current_perception = PerceptionLevel.LINE
            return "* Reality collapses! You can only move left and right!"
        elif shift_state.current_perception == PerceptionLevel.VOLUME:
            shift_state.current_perception = PerceptionLevel.PLANE
            return "* Your higher perception fades!"
        return "* You feel reality pressing in..."
    
    @staticmethod
    def dimension_invert(shift_state: DimensionalShiftState) -> str:
        """Invert player controls temporarily."""
        # This would be handled by the battle system
        return "* Everything is backwards!"
    
    @staticmethod
    def dimension_blind(shift_state: DimensionalShiftState) -> str:
        """Temporarily reduce visibility."""
        return "* Your perception dims... you can barely see!"
    
    @staticmethod
    def dimension_overload(shift_state: DimensionalShiftState) -> str:
        """Give player too much perception (overwhelming)."""
        if shift_state.shift_energy > 50:
            shift_state.shift_energy = max(0, shift_state.shift_energy - 30)
            return "* Too many dimensions! Your mind reels!"
        return "* You feel overwhelmed by infinite possibility..."


@dataclass
class DimensionalCombatState:
    """Complete state for dimensional combat mechanics."""
    
    shift_state: DimensionalShiftState = field(default_factory=DimensionalShiftState)
    resonance: GeometricResonance = field(default_factory=GeometricResonance)
    grazing: GrazingSystem = field(default_factory=GrazingSystem)
    
    # Active reality warps
    active_warps: List[RealityWarpEffect] = field(default_factory=list)
    
    # Control modifiers
    controls_inverted: bool = False
    invert_timer: float = 0.0
    visibility: float = 1.0  # 1.0 = full, 0.0 = blind
    visibility_target: float = 1.0
    
    # Phase ability (3D perception)
    phase_active: bool = False
    phase_cooldown: float = 0.0
    
    def update(self, dt: float) -> None:
        """Update all dimensional combat systems."""
        self.shift_state.update(dt)
        self.resonance.update(dt)
        self.grazing.update(dt)
        
        # Update warps
        for warp in self.active_warps:
            warp.update(dt)
        self.active_warps = [w for w in self.active_warps if w.active]
        
        # Update control inversion
        if self.invert_timer > 0:
            self.invert_timer -= dt
            if self.invert_timer <= 0:
                self.controls_inverted = False
        
        # Smooth visibility changes
        if self.visibility != self.visibility_target:
            diff = self.visibility_target - self.visibility
            self.visibility += diff * 3.0 * dt
        
        # Phase cooldown
        if self.phase_cooldown > 0:
            self.phase_cooldown -= dt
    
    def add_warp(self, warp_type: RealityWarpType, duration: float = 5.0, 
                 intensity: float = 1.0) -> None:
        """Add a reality warp effect."""
        warp = RealityWarpEffect(
            warp_type=warp_type,
            duration=duration,
            intensity=intensity
        )
        self.active_warps.append(warp)
    
    def get_movement_modifier(self) -> Tuple[float, float, float, float]:
        """Get movement constraints based on perception."""
        perception = self.shift_state.current_perception
        
        # Returns (x_mult, y_mult, can_phase, time_slow)
        if perception == PerceptionLevel.POINT:
            return (0.0, 0.0, False, 0.0)  # Frozen
        elif perception == PerceptionLevel.LINE:
            return (1.0, 0.0, False, 1.0)  # Only X movement
        elif perception == PerceptionLevel.PLANE:
            return (1.0, 1.0, False, 1.0)  # Normal
        elif perception == PerceptionLevel.VOLUME:
            return (1.0, 1.0, True, 1.0)   # Can phase
        elif perception == PerceptionLevel.HYPER:
            return (1.2, 1.2, True, 0.5)   # Fast + phase + slow time
        
        return (1.0, 1.0, False, 1.0)
    
    def apply_warp_to_position(self, x: float, y: float, 
                               box_center: Tuple[float, float]) -> Tuple[float, float]:
        """Apply warp effects to a position."""
        cx, cy = box_center
        
        for warp in self.active_warps:
            if warp.warp_type == RealityWarpType.ROTATE:
                # Rotate around center
                dx, dy = x - cx, y - cy
                cos_a = math.cos(warp.rotation_angle)
                sin_a = math.sin(warp.rotation_angle)
                x = cx + dx * cos_a - dy * sin_a
                y = cy + dx * sin_a + dy * cos_a
            
            elif warp.warp_type == RealityWarpType.FOLD:
                # Wrap position around fold axis
                if warp.fold_axis == "horizontal":
                    if y > cy:
                        y = cy - (y - cy)
                else:
                    if x > cx:
                        x = cx - (x - cx)
        
        return (x, y)
    
    def try_phase(self) -> bool:
        """Attempt to phase through bullets (3D perception)."""
        if self.phase_cooldown > 0:
            return False
        
        modifiers = self.get_movement_modifier()
        if not modifiers[2]:  # can_phase
            return False
        
        self.phase_active = True
        self.phase_cooldown = 1.0  # 1 second cooldown
        return True


# Special dimensional ACT effects
DIMENSIONAL_ACT_EFFECTS: Dict[str, Callable[[DimensionalCombatState], str]] = {
    "perceive_deeper": lambda state: (
        state.shift_state.add_transcendence(15),
        "* You focus on the deeper dimensions...\n* Transcendence gauge increased!"
    )[1],
    
    "geometric_meditation": lambda state: (
        state.resonance.add_resonance("plane", 30),
        "* You meditate on geometric harmony.\n* Plane resonance increased!"
    )[1],
    
    "line_focus": lambda state: (
        state.resonance.add_resonance("line", 40),
        "* You focus your mind to a single line.\n* Your determination grows!"
    )[1],
    
    "point_collapse": lambda state: (
        state.shift_state.shift_to(PerceptionLevel.POINT),
        "* You collapse your perception to a point.\n* You are invulnerable but cannot move!"
    )[1] if state.shift_state.can_shift_to(PerceptionLevel.POINT) else "* Not enough shift energy...",
    
    "expand_perception": lambda state: (
        state.shift_state.shift_to(PerceptionLevel.VOLUME),
        "* You expand your perception to 3D!\n* You can phase through attacks!"
    )[1] if state.shift_state.can_shift_to(PerceptionLevel.VOLUME) else "* Not enough shift energy...",
}
