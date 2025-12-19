"""Dimensional Combat System - Core mechanics for dimension-based combat.

This module replaces the Undertale-like soul modes with a dimensional perception
system where combat fundamentally changes based on the dimension you're fighting in.

Key Systems:
1. Dimension-Specific Movement Rules (1D→4D)
2. Perception States (replace soul modes)
3. Dimensional Attack Patterns
4. Battle Box Transformations
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .core import PlayerSoul


class CombatDimension(Enum):
    """The dimension in which combat takes place."""
    ONE_D = "1d"    # Linear - only horizontal movement
    TWO_D = "2d"    # Planar - standard 2D movement
    THREE_D = "3d"  # Spatial - depth/layering system
    FOUR_D = "4d"   # Temporal - past/future bullet prediction


class PerceptionState(Enum):
    """Player's perception state - replaces soul modes.
    
    Each state has trade-offs and is useful against specific attack types.
    """
    # Core perception states
    POINT = "point"       # 0D - Collapsed to a point, invulnerable but frozen
    LINE = "line"         # 1D - Only horizontal movement, immune to vertical attacks
    PLANE = "plane"       # 2D - Normal movement (default)
    VOLUME = "volume"     # 3D - Can phase between depth layers
    HYPER = "hyper"       # 4D - See bullet trajectories, slow time, transcendent
    
    # Special transitional states
    SHIFTING = "shifting"  # Currently transitioning between states
    FRACTURED = "fractured"  # Damaged perception, unpredictable movement


@dataclass
class DimensionalMovementRules:
    """Movement rules based on combat dimension."""
    
    dimension: CombatDimension = CombatDimension.TWO_D
    
    # Movement constraints
    allow_horizontal: bool = True
    allow_vertical: bool = True
    allow_depth: bool = False  # 3D depth movement
    allow_temporal: bool = False  # 4D time scrubbing
    
    # Movement modifiers
    speed_multiplier: float = 1.0
    momentum: float = 0.0  # 0 = instant stop, 1 = full momentum
    
    # Special mechanics
    wrap_horizontal: bool = False  # Tesseract wrapping
    wrap_vertical: bool = False
    gravity_direction: Tuple[float, float] = (0.0, 1.0)
    gravity_strength: float = 0.0
    
    @classmethod
    def for_dimension(cls, dimension: CombatDimension) -> "DimensionalMovementRules":
        """Get movement rules for a specific dimension."""
        if dimension == CombatDimension.ONE_D:
            return cls(
                dimension=dimension,
                allow_horizontal=True,
                allow_vertical=False,
                speed_multiplier=1.2,  # Faster in 1D
                momentum=0.3,  # Slight sliding
            )
        elif dimension == CombatDimension.TWO_D:
            return cls(
                dimension=dimension,
                allow_horizontal=True,
                allow_vertical=True,
                speed_multiplier=1.0,
            )
        elif dimension == CombatDimension.THREE_D:
            return cls(
                dimension=dimension,
                allow_horizontal=True,
                allow_vertical=True,
                allow_depth=True,
                speed_multiplier=0.9,  # Slightly slower due to depth management
            )
        elif dimension == CombatDimension.FOUR_D:
            return cls(
                dimension=dimension,
                allow_horizontal=True,
                allow_vertical=True,
                allow_depth=True,
                allow_temporal=True,
                wrap_horizontal=True,
                wrap_vertical=True,
                speed_multiplier=0.85,
            )
        return cls()


@dataclass
class PerceptionAbilities:
    """Abilities available in each perception state."""
    
    state: PerceptionState = PerceptionState.PLANE
    
    # Movement abilities
    can_move: bool = True
    horizontal_only: bool = False
    vertical_only: bool = False
    can_phase: bool = False  # Phase through bullets momentarily
    
    # Defensive abilities
    invulnerable: bool = False
    damage_reduction: float = 0.0  # 0-1 percentage reduction
    can_block_direction: Optional[str] = None  # "horizontal", "vertical", "all"
    
    # Special abilities
    can_see_trajectories: bool = False  # See where bullets will go
    time_slow_factor: float = 1.0  # 1.0 = normal, 0.5 = half speed
    can_predict_attacks: bool = False  # See future attack patterns
    
    # Costs
    energy_drain_per_second: float = 0.0
    activation_cost: float = 0.0
    
    @classmethod
    def for_state(cls, state: PerceptionState) -> "PerceptionAbilities":
        """Get abilities for a perception state."""
        if state == PerceptionState.POINT:
            return cls(
                state=state,
                can_move=False,
                invulnerable=True,
                energy_drain_per_second=25.0,
                activation_cost=15.0,
            )
        elif state == PerceptionState.LINE:
            return cls(
                state=state,
                horizontal_only=True,
                can_block_direction="vertical",
                damage_reduction=0.5,  # 50% reduction from vertical attacks
                energy_drain_per_second=8.0,
                activation_cost=5.0,
            )
        elif state == PerceptionState.PLANE:
            return cls(
                state=state,
                # Default - no special abilities or costs
            )
        elif state == PerceptionState.VOLUME:
            return cls(
                state=state,
                can_phase=True,
                damage_reduction=0.25,
                energy_drain_per_second=12.0,
                activation_cost=10.0,
            )
        elif state == PerceptionState.HYPER:
            return cls(
                state=state,
                can_phase=True,
                can_see_trajectories=True,
                can_predict_attacks=True,
                time_slow_factor=0.6,
                damage_reduction=0.3,
                energy_drain_per_second=20.0,
                activation_cost=25.0,
            )
        elif state == PerceptionState.FRACTURED:
            return cls(
                state=state,
                damage_reduction=-0.25,  # Take MORE damage
            )
        return cls()


@dataclass
class DepthLayer:
    """A depth layer for 3D combat."""
    z: float  # Depth value (0 = foreground, 1 = background)
    name: str = "middle"
    color_tint: Tuple[int, int, int] = (255, 255, 255)
    scale: float = 1.0  # Visual scale
    speed_modifier: float = 1.0  # Bullets move slower in background


# Standard depth layers for 3D combat
DEPTH_LAYERS = [
    DepthLayer(z=0.0, name="foreground", color_tint=(255, 255, 255), scale=1.2, speed_modifier=1.2),
    DepthLayer(z=0.5, name="middle", color_tint=(200, 200, 200), scale=1.0, speed_modifier=1.0),
    DepthLayer(z=1.0, name="background", color_tint=(150, 150, 150), scale=0.8, speed_modifier=0.8),
]


@dataclass
class TemporalBulletState:
    """State of a bullet across time for 4D combat."""
    
    # Past states (ghosted)
    past_positions: List[Tuple[float, float]] = field(default_factory=list)
    past_max: int = 10
    
    # Future predictions (shown as trajectories)
    future_positions: List[Tuple[float, float]] = field(default_factory=list)
    future_steps: int = 15
    
    # Temporal properties
    exists_in_time: float = 0.0  # Current time position
    time_phase: float = 0.0  # 0-1, which "phase" of time it's in
    
    # Some bullets only exist at certain times
    active_time_start: float = 0.0
    active_time_end: float = float('inf')
    
    def is_active_at_time(self, time: float) -> bool:
        """Check if bullet exists at given time."""
        return self.active_time_start <= time <= self.active_time_end
    
    def record_position(self, x: float, y: float) -> None:
        """Record current position to past."""
        self.past_positions.append((x, y))
        if len(self.past_positions) > self.past_max:
            self.past_positions.pop(0)
    
    def predict_future(self, x: float, y: float, vx: float, vy: float, dt: float = 0.05) -> None:
        """Predict future positions."""
        self.future_positions.clear()
        px, py = x, y
        for _ in range(self.future_steps):
            px += vx * dt
            py += vy * dt
            self.future_positions.append((px, py))


@dataclass
class DimensionalBullet:
    """Enhanced bullet with dimensional properties."""
    
    # Base position
    x: float = 0.0
    y: float = 0.0
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    
    # Dimensional properties
    depth_layer: float = 0.5  # 3D: which layer (0=front, 1=back)
    temporal_state: Optional[TemporalBulletState] = None  # 4D: time data
    
    # Dimension it belongs to
    source_dimension: CombatDimension = CombatDimension.TWO_D
    
    # Attack direction (for 1D directional immunity)
    attack_direction: str = "both"  # "horizontal", "vertical", "both"
    
    # Visual
    radius: float = 8.0
    color: Tuple[int, int, int] = (255, 255, 255)
    shape: str = "circle"
    
    # Damage
    damage: int = 5
    active: bool = True
    
    def can_hit_in_perception(self, perception: PerceptionState) -> bool:
        """Check if this bullet can hit player in their current perception."""
        abilities = PerceptionAbilities.for_state(perception)
        
        # Invulnerable = no hits
        if abilities.invulnerable:
            return False
        
        # Check directional blocking
        if abilities.can_block_direction:
            if abilities.can_block_direction == "vertical" and self.attack_direction == "vertical":
                return False
            if abilities.can_block_direction == "horizontal" and self.attack_direction == "horizontal":
                return False
            if abilities.can_block_direction == "all":
                return False
        
        return True
    
    def get_damage_in_perception(self, perception: PerceptionState, base_damage: int) -> int:
        """Get actual damage based on perception state."""
        abilities = PerceptionAbilities.for_state(perception)
        
        if abilities.invulnerable:
            return 0
        
        damage = base_damage * (1.0 - abilities.damage_reduction)
        return max(1, int(damage))


@dataclass
class DimensionalCombatRules:
    """Complete ruleset for dimensional combat."""
    
    dimension: CombatDimension = CombatDimension.TWO_D
    movement_rules: DimensionalMovementRules = field(default_factory=DimensionalMovementRules)
    
    # Player perception
    current_perception: PerceptionState = PerceptionState.PLANE
    perception_energy: float = 100.0
    max_perception_energy: float = 100.0
    energy_regen_rate: float = 10.0  # Per second in PLANE state
    
    # Perception shift
    shift_cooldown: float = 0.0
    shift_cooldown_duration: float = 0.5
    is_shifting: bool = False
    shift_progress: float = 0.0
    target_perception: Optional[PerceptionState] = None
    
    # 3D combat
    player_depth: float = 0.5  # Which depth layer player is on
    depth_shift_speed: float = 2.0  # How fast player moves between layers
    
    # 4D combat
    time_position: float = 0.0  # Current time scrub position
    time_scrub_range: float = 2.0  # How far into past/future player can see
    bullet_predictions_visible: bool = False
    
    # Transcendence gauge (replaces old system)
    transcendence: float = 0.0
    transcendence_max: float = 100.0
    transcendence_active: bool = False
    transcendence_duration: float = 0.0
    
    def __post_init__(self):
        self.movement_rules = DimensionalMovementRules.for_dimension(self.dimension)
    
    def set_dimension(self, dimension: CombatDimension) -> None:
        """Change the combat dimension."""
        self.dimension = dimension
        self.movement_rules = DimensionalMovementRules.for_dimension(dimension)
        
        # Reset dimension-specific state
        if dimension == CombatDimension.THREE_D:
            self.player_depth = 0.5
        elif dimension == CombatDimension.FOUR_D:
            self.time_position = 0.0
            self.bullet_predictions_visible = True
    
    def can_shift_perception(self, target: PerceptionState) -> bool:
        """Check if player can shift to target perception."""
        if self.shift_cooldown > 0:
            return False
        if self.is_shifting:
            return False
        if target == self.current_perception:
            return False
        
        abilities = PerceptionAbilities.for_state(target)
        return self.perception_energy >= abilities.activation_cost
    
    def start_perception_shift(self, target: PerceptionState) -> bool:
        """Begin shifting to a new perception state."""
        if not self.can_shift_perception(target):
            return False
        
        abilities = PerceptionAbilities.for_state(target)
        self.perception_energy -= abilities.activation_cost
        
        self.is_shifting = True
        self.shift_progress = 0.0
        self.target_perception = target
        
        return True
    
    def update(self, dt: float) -> None:
        """Update dimensional combat state."""
        # Update cooldowns
        if self.shift_cooldown > 0:
            self.shift_cooldown = max(0, self.shift_cooldown - dt)
        
        # Update perception shift
        if self.is_shifting:
            self.shift_progress += dt * 3.0  # Shift takes ~0.33 seconds
            if self.shift_progress >= 1.0:
                self._complete_shift()
        
        # Energy management
        abilities = PerceptionAbilities.for_state(self.current_perception)
        
        if self.current_perception == PerceptionState.PLANE:
            # Regenerate energy in default state
            self.perception_energy = min(
                self.max_perception_energy,
                self.perception_energy + self.energy_regen_rate * dt
            )
        else:
            # Drain energy in other states
            self.perception_energy -= abilities.energy_drain_per_second * dt
            if self.perception_energy <= 0:
                self.perception_energy = 0
                self._force_return_to_plane()
        
        # Update transcendence
        if self.transcendence_active:
            self.transcendence_duration -= dt
            if self.transcendence_duration <= 0:
                self._end_transcendence()
    
    def _complete_shift(self) -> None:
        """Complete a perception shift."""
        self.current_perception = self.target_perception
        self.target_perception = None
        self.is_shifting = False
        self.shift_progress = 0.0
        self.shift_cooldown = self.shift_cooldown_duration
    
    def _force_return_to_plane(self) -> None:
        """Force return to plane perception (out of energy)."""
        self.current_perception = PerceptionState.PLANE
        self.is_shifting = False
        self.shift_progress = 0.0
        self.shift_cooldown = self.shift_cooldown_duration * 2  # Longer cooldown
    
    def add_transcendence(self, amount: float) -> None:
        """Add to transcendence gauge."""
        if not self.transcendence_active:
            self.transcendence = min(self.transcendence_max, self.transcendence + amount)
    
    def can_transcend(self) -> bool:
        """Check if transcendence can be activated."""
        return self.transcendence >= self.transcendence_max and not self.transcendence_active
    
    def activate_transcendence(self) -> bool:
        """Activate transcendence (4D perception)."""
        if not self.can_transcend():
            return False
        
        self.transcendence_active = True
        self.transcendence_duration = 6.0
        self.transcendence = 0
        self.current_perception = PerceptionState.HYPER
        
        return True
    
    def _end_transcendence(self) -> None:
        """End transcendence mode."""
        self.transcendence_active = False
        self.current_perception = PerceptionState.PLANE
    
    def apply_movement(
        self, 
        input_x: float, 
        input_y: float, 
        depth_input: float,
        soul_x: float, 
        soul_y: float, 
        speed: float, 
        dt: float,
        box_bounds: Tuple[float, float, float, float]
    ) -> Tuple[float, float, float]:
        """Apply dimensional movement rules. Returns new (x, y, depth)."""
        min_x, min_y, max_x, max_y = box_bounds
        
        # Get perception abilities
        abilities = PerceptionAbilities.for_state(self.current_perception)
        
        # Check if can move at all
        if not abilities.can_move:
            return soul_x, soul_y, self.player_depth
        
        # Apply movement constraints from perception
        if abilities.horizontal_only:
            input_y = 0
        if abilities.vertical_only:
            input_x = 0
        
        # Apply dimension movement rules
        rules = self.movement_rules
        
        if not rules.allow_horizontal:
            input_x = 0
        if not rules.allow_vertical:
            input_y = 0
        
        # Calculate new position
        move_speed = speed * rules.speed_multiplier
        
        # Apply time slow in HYPER state
        if abilities.time_slow_factor != 1.0:
            move_speed *= (1.0 / abilities.time_slow_factor)  # Player moves faster relatively
        
        new_x = soul_x + input_x * move_speed * dt
        new_y = soul_y + input_y * move_speed * dt
        
        # Handle wrapping (4D tesseract)
        if rules.wrap_horizontal:
            if new_x < min_x:
                new_x = max_x - (min_x - new_x)
            elif new_x > max_x:
                new_x = min_x + (new_x - max_x)
        else:
            new_x = max(min_x, min(max_x, new_x))
        
        if rules.wrap_vertical:
            if new_y < min_y:
                new_y = max_y - (min_y - new_y)
            elif new_y > max_y:
                new_y = min_y + (new_y - max_y)
        else:
            new_y = max(min_y, min(max_y, new_y))
        
        # Handle depth movement (3D)
        new_depth = self.player_depth
        if rules.allow_depth and depth_input != 0:
            new_depth = self.player_depth + depth_input * self.depth_shift_speed * dt
            new_depth = max(0.0, min(1.0, new_depth))
            self.player_depth = new_depth
        
        return new_x, new_y, new_depth
    
    def check_bullet_collision(
        self,
        bullet: DimensionalBullet,
        soul_x: float,
        soul_y: float,
        soul_radius: float
    ) -> Tuple[bool, int]:
        """Check if bullet hits player. Returns (hit, damage)."""
        # Check perception immunity
        if not bullet.can_hit_in_perception(self.current_perception):
            return False, 0
        
        # 3D depth check
        if self.dimension == CombatDimension.THREE_D:
            depth_diff = abs(bullet.depth_layer - self.player_depth)
            if depth_diff > 0.2:  # Different layers don't collide
                return False, 0
        
        # 4D temporal check
        if self.dimension == CombatDimension.FOUR_D and bullet.temporal_state:
            if not bullet.temporal_state.is_active_at_time(self.time_position):
                return False, 0
        
        # Standard distance check
        dist = math.sqrt((soul_x - bullet.x) ** 2 + (soul_y - bullet.y) ** 2)
        if dist >= soul_radius + bullet.radius:
            return False, 0
        
        # Calculate damage based on perception
        damage = bullet.get_damage_in_perception(self.current_perception, bullet.damage)
        
        return True, damage


# ============================================================================
# DIMENSION-SPECIFIC ATTACK PATTERN GENERATORS
# ============================================================================

class DimensionalPatternGenerator:
    """Generates attack patterns specific to each dimension."""
    
    @staticmethod
    def generate_1d_attack(
        box_bounds: Tuple[float, float, float, float],
        attack_type: str,
        difficulty: float = 1.0
    ) -> List[DimensionalBullet]:
        """Generate 1D attack patterns - all horizontal/linear."""
        min_x, min_y, max_x, max_y = box_bounds
        center_y = (min_y + max_y) / 2
        bullets = []
        
        if attack_type == "line_sweep":
            # Horizontal lines sweeping across
            num_lines = int(3 * difficulty)
            for i in range(num_lines):
                y = min_y + (max_y - min_y) * (i + 1) / (num_lines + 1)
                direction = 1 if i % 2 == 0 else -1
                start_x = min_x if direction > 0 else max_x
                
                bullets.append(DimensionalBullet(
                    x=start_x,
                    y=y,
                    velocity_x=200 * direction * difficulty,
                    velocity_y=0,
                    source_dimension=CombatDimension.ONE_D,
                    attack_direction="horizontal",
                    shape="line",
                ))
        
        elif attack_type == "converging_points":
            # Points converging on the line
            for i in range(int(8 * difficulty)):
                side = 1 if i % 2 == 0 else -1
                start_x = min_x if side > 0 else max_x
                y_offset = random.uniform(-30, 30)
                
                bullets.append(DimensionalBullet(
                    x=start_x,
                    y=center_y + y_offset,
                    velocity_x=180 * side * difficulty,
                    velocity_y=-y_offset * 2,  # Converge to center line
                    source_dimension=CombatDimension.ONE_D,
                    attack_direction="horizontal",
                    radius=6,
                ))
        
        elif attack_type == "segment_wave":
            # Wave of line segments
            num_segments = int(5 * difficulty)
            for i in range(num_segments):
                bullets.append(DimensionalBullet(
                    x=min_x - 20 - i * 50,
                    y=center_y,
                    velocity_x=150 * difficulty,
                    velocity_y=0,
                    source_dimension=CombatDimension.ONE_D,
                    attack_direction="horizontal",
                    shape="segment",
                    radius=15,
                ))
        
        return bullets
    
    @staticmethod
    def generate_2d_attack(
        box_bounds: Tuple[float, float, float, float],
        attack_type: str,
        difficulty: float = 1.0
    ) -> List[DimensionalBullet]:
        """Generate 2D attack patterns - geometric shapes."""
        min_x, min_y, max_x, max_y = box_bounds
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        bullets = []
        
        if attack_type == "triangle_formation":
            # Triangular bullet formations
            num_triangles = int(3 * difficulty)
            for t in range(num_triangles):
                angle_offset = t * (2 * math.pi / num_triangles)
                for i in range(3):  # 3 points of triangle
                    angle = angle_offset + i * (2 * math.pi / 3)
                    bullets.append(DimensionalBullet(
                        x=center_x,
                        y=center_y,
                        velocity_x=math.cos(angle) * 160 * difficulty,
                        velocity_y=math.sin(angle) * 160 * difficulty,
                        source_dimension=CombatDimension.TWO_D,
                        shape="triangle",
                    ))
        
        elif attack_type == "square_grid":
            # Grid of squares that rotate
            grid_size = int(3 * difficulty)
            spacing = min(max_x - min_x, max_y - min_y) / (grid_size + 1)
            for i in range(grid_size):
                for j in range(grid_size):
                    x = min_x + spacing * (i + 1)
                    y = min_y + spacing * (j + 1)
                    angle = random.uniform(0, 2 * math.pi)
                    bullets.append(DimensionalBullet(
                        x=x, y=y,
                        velocity_x=math.cos(angle) * 80 * difficulty,
                        velocity_y=math.sin(angle) * 80 * difficulty,
                        source_dimension=CombatDimension.TWO_D,
                        shape="square",
                        radius=10,
                    ))
        
        elif attack_type == "circle_spiral":
            # Spiral of circular bullets
            num_bullets = int(16 * difficulty)
            for i in range(num_bullets):
                angle = i * 0.5
                speed = 120 + i * 5
                bullets.append(DimensionalBullet(
                    x=center_x,
                    y=center_y,
                    velocity_x=math.cos(angle) * speed * difficulty,
                    velocity_y=math.sin(angle) * speed * difficulty,
                    source_dimension=CombatDimension.TWO_D,
                    shape="circle",
                ))
        
        return bullets
    
    @staticmethod
    def generate_3d_attack(
        box_bounds: Tuple[float, float, float, float],
        attack_type: str,
        difficulty: float = 1.0
    ) -> List[DimensionalBullet]:
        """Generate 3D attack patterns - depth layers."""
        min_x, min_y, max_x, max_y = box_bounds
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        bullets = []
        
        if attack_type == "depth_wave":
            # Waves at different depths
            for layer in [0.0, 0.5, 1.0]:
                num_bullets = int(6 * difficulty)
                for i in range(num_bullets):
                    angle = 2 * math.pi * i / num_bullets
                    bullets.append(DimensionalBullet(
                        x=center_x,
                        y=center_y,
                        velocity_x=math.cos(angle) * 140 * difficulty,
                        velocity_y=math.sin(angle) * 140 * difficulty,
                        depth_layer=layer,
                        source_dimension=CombatDimension.THREE_D,
                        shape="sphere",
                        color=DEPTH_LAYERS[int(layer * 2)].color_tint,
                    ))
        
        elif attack_type == "phasing_cubes":
            # Cubes that phase between layers
            num_cubes = int(8 * difficulty)
            for i in range(num_cubes):
                start_layer = random.choice([0.0, 0.5, 1.0])
                angle = random.uniform(0, 2 * math.pi)
                bullets.append(DimensionalBullet(
                    x=center_x + random.uniform(-50, 50),
                    y=center_y + random.uniform(-50, 50),
                    velocity_x=math.cos(angle) * 100 * difficulty,
                    velocity_y=math.sin(angle) * 100 * difficulty,
                    depth_layer=start_layer,
                    source_dimension=CombatDimension.THREE_D,
                    shape="cube",
                    radius=12,
                ))
        
        elif attack_type == "shadow_assault":
            # Bullets in background telegraph, then appear in foreground
            num_bullets = int(10 * difficulty)
            for i in range(num_bullets):
                x = random.uniform(min_x + 20, max_x - 20)
                y = min_y - 10
                # Background telegraphed bullet
                bullets.append(DimensionalBullet(
                    x=x, y=y,
                    velocity_x=0,
                    velocity_y=200 * difficulty,
                    depth_layer=1.0,  # Background
                    source_dimension=CombatDimension.THREE_D,
                    shape="shadow",
                    damage=0,  # Telegraph doesn't hurt
                ))
                # Delayed foreground bullet
                bullets.append(DimensionalBullet(
                    x=x, y=y - 50,  # Slightly delayed
                    velocity_x=0,
                    velocity_y=200 * difficulty,
                    depth_layer=0.0,  # Foreground - DOES hurt
                    source_dimension=CombatDimension.THREE_D,
                    shape="sphere",
                ))
        
        return bullets
    
    @staticmethod
    def generate_4d_attack(
        box_bounds: Tuple[float, float, float, float],
        attack_type: str,
        difficulty: float = 1.0
    ) -> List[DimensionalBullet]:
        """Generate 4D attack patterns - temporal bullets."""
        min_x, min_y, max_x, max_y = box_bounds
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        bullets = []
        
        if attack_type == "temporal_burst":
            # Bullets that exist at different times
            num_bullets = int(12 * difficulty)
            for i in range(num_bullets):
                angle = 2 * math.pi * i / num_bullets
                time_offset = (i % 3) * 0.5  # Stagger in time
                
                temporal = TemporalBulletState(
                    active_time_start=time_offset,
                    active_time_end=time_offset + 2.0,
                )
                
                bullets.append(DimensionalBullet(
                    x=center_x,
                    y=center_y,
                    velocity_x=math.cos(angle) * 150 * difficulty,
                    velocity_y=math.sin(angle) * 150 * difficulty,
                    temporal_state=temporal,
                    source_dimension=CombatDimension.FOUR_D,
                    shape="tesseract",
                ))
        
        elif attack_type == "past_echo":
            # Bullets that repeat from the past
            num_bullets = int(6 * difficulty)
            for i in range(num_bullets):
                x = random.uniform(min_x, max_x)
                y = random.uniform(min_y, max_y)
                
                for time_phase in [0.0, 1.0, 2.0]:  # Echo 3 times
                    temporal = TemporalBulletState(
                        active_time_start=time_phase,
                        active_time_end=time_phase + 0.8,
                    )
                    bullets.append(DimensionalBullet(
                        x=x, y=y,
                        velocity_x=random.uniform(-100, 100) * difficulty,
                        velocity_y=random.uniform(-100, 100) * difficulty,
                        temporal_state=temporal,
                        source_dimension=CombatDimension.FOUR_D,
                        shape="echo",
                        color=(150, 150, 255) if time_phase > 0 else (255, 255, 255),
                    ))
        
        elif attack_type == "future_convergence":
            # See where bullets WILL be, must position to avoid
            num_bullets = int(8 * difficulty)
            for i in range(num_bullets):
                # Bullets spiral inward from edges
                angle = 2 * math.pi * i / num_bullets
                start_x = center_x + math.cos(angle) * 200
                start_y = center_y + math.sin(angle) * 200
                
                temporal = TemporalBulletState(future_steps=20)
                temporal.predict_future(
                    start_x, start_y,
                    -math.cos(angle) * 100, -math.sin(angle) * 100
                )
                
                bullets.append(DimensionalBullet(
                    x=start_x,
                    y=start_y,
                    velocity_x=-math.cos(angle) * 100 * difficulty,
                    velocity_y=-math.sin(angle) * 100 * difficulty,
                    temporal_state=temporal,
                    source_dimension=CombatDimension.FOUR_D,
                    shape="tesseract",
                ))
        
        return bullets


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_dimension_from_enemy(enemy_dimension: str) -> CombatDimension:
    """Convert enemy dimension string to CombatDimension enum."""
    mapping = {
        "1d": CombatDimension.ONE_D,
        "2d": CombatDimension.TWO_D,
        "3d": CombatDimension.THREE_D,
        "4d": CombatDimension.FOUR_D,
    }
    return mapping.get(enemy_dimension.lower(), CombatDimension.TWO_D)


def get_recommended_perception(dimension: CombatDimension) -> PerceptionState:
    """Get the recommended starting perception for a dimension."""
    if dimension == CombatDimension.ONE_D:
        return PerceptionState.LINE
    elif dimension == CombatDimension.TWO_D:
        return PerceptionState.PLANE
    elif dimension == CombatDimension.THREE_D:
        return PerceptionState.VOLUME
    elif dimension == CombatDimension.FOUR_D:
        return PerceptionState.HYPER
    return PerceptionState.PLANE
