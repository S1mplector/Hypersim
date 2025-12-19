"""Perception System - Replaces Undertale's Soul Modes with dimensional perception.

Instead of colored souls that change your movement type, players shift their
dimensional perception to counter different attack types. This is the core
defensive mechanic of the dimensional combat system.

Key differences from Soul Modes:
1. Player CHOOSES when to shift (strategic, not forced)
2. Each perception has energy cost and trade-offs
3. Perceptions counter specific attack TYPES, not just movement changes
4. Building resonance with a dimension unlocks stronger perception abilities
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable

import pygame

from .dimensional_combat import (
    PerceptionState, PerceptionAbilities, CombatDimension,
    DimensionalCombatRules, DimensionalBullet
)


class PerceptionShiftResult(Enum):
    """Result of attempting a perception shift."""
    SUCCESS = auto()
    NOT_ENOUGH_ENERGY = auto()
    ON_COOLDOWN = auto()
    ALREADY_IN_STATE = auto()
    BLOCKED_BY_ENEMY = auto()  # Some enemies can block shifts


@dataclass
class PerceptionMeter:
    """Visual meter showing perception energy and state."""
    
    x: float
    y: float
    width: float = 150
    height: float = 12
    
    # Colors for each perception state
    state_colors: Dict[PerceptionState, Tuple[int, int, int]] = field(default_factory=lambda: {
        PerceptionState.POINT: (100, 100, 255),     # Blue - collapsed
        PerceptionState.LINE: (100, 200, 255),      # Cyan - linear
        PerceptionState.PLANE: (255, 255, 255),     # White - default
        PerceptionState.VOLUME: (200, 100, 255),    # Purple - spatial
        PerceptionState.HYPER: (255, 200, 100),     # Gold - transcendent
        PerceptionState.SHIFTING: (200, 200, 200),  # Gray - transitioning
        PerceptionState.FRACTURED: (255, 100, 100), # Red - damaged
    })
    
    def draw(
        self, 
        screen: pygame.Surface, 
        rules: DimensionalCombatRules,
        font: Optional[pygame.font.Font] = None
    ) -> None:
        """Draw the perception meter."""
        if font is None:
            font = pygame.font.Font(None, 18)
        
        # Background
        pygame.draw.rect(screen, (30, 30, 40),
                        (int(self.x), int(self.y), int(self.width), int(self.height)))
        
        # Energy fill
        fill_ratio = rules.perception_energy / rules.max_perception_energy
        fill_width = int(self.width * fill_ratio)
        
        # Color based on current perception
        color = self.state_colors.get(rules.current_perception, (255, 255, 255))
        
        # Pulsing effect when low energy
        if fill_ratio < 0.25:
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 0.5 + 0.5
            color = tuple(int(c * pulse) for c in color)
        
        pygame.draw.rect(screen, color,
                        (int(self.x), int(self.y), fill_width, int(self.height)))
        
        # Border
        border_color = (100, 100, 120)
        if rules.is_shifting:
            border_color = (255, 255, 255)
        pygame.draw.rect(screen, border_color,
                        (int(self.x), int(self.y), int(self.width), int(self.height)), 1)
        
        # Label
        state_name = rules.current_perception.value.upper()
        if rules.is_shifting and rules.target_perception:
            state_name = f"{state_name}→{rules.target_perception.value.upper()}"
        
        label = font.render(f"[{state_name}]", True, color)
        screen.blit(label, (self.x + self.width + 5, self.y - 2))
        
        # Shift progress bar
        if rules.is_shifting:
            progress_y = self.y + self.height + 2
            pygame.draw.rect(screen, (50, 50, 60),
                           (int(self.x), int(progress_y), int(self.width), 4))
            pygame.draw.rect(screen, (255, 255, 255),
                           (int(self.x), int(progress_y), 
                            int(self.width * rules.shift_progress), 4))


@dataclass  
class TranscendenceMeter:
    """Visual meter for transcendence gauge."""
    
    x: float
    y: float
    width: float = 150
    height: float = 10
    
    def draw(
        self,
        screen: pygame.Surface,
        rules: DimensionalCombatRules,
        font: Optional[pygame.font.Font] = None
    ) -> None:
        """Draw transcendence meter."""
        if font is None:
            font = pygame.font.Font(None, 18)
        
        # Background
        pygame.draw.rect(screen, (40, 35, 20),
                        (int(self.x), int(self.y), int(self.width), int(self.height)))
        
        # Fill
        fill_ratio = rules.transcendence / rules.transcendence_max
        fill_width = int(self.width * fill_ratio)
        
        # Gradient from orange to gold
        color = (255, int(150 + 50 * fill_ratio), int(50 + 50 * fill_ratio))
        
        pygame.draw.rect(screen, color,
                        (int(self.x), int(self.y), fill_width, int(self.height)))
        
        # Border
        border_color = (150, 120, 50)
        if rules.can_transcend():
            # Pulsing when ready
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.008))
            border_color = (255, int(200 + 55 * pulse), int(100 * pulse))
        
        pygame.draw.rect(screen, border_color,
                        (int(self.x), int(self.y), int(self.width), int(self.height)), 1)
        
        # Label
        if rules.transcendence_active:
            label_text = f"HYPER! {rules.transcendence_duration:.1f}s"
            label_color = (255, 220, 100)
        elif rules.can_transcend():
            label_text = "[T] TRANSCEND!"
            label_color = (255, 200, 100)
        else:
            label_text = "TRANSCENDENCE"
            label_color = (150, 120, 80)
        
        label = font.render(label_text, True, label_color)
        screen.blit(label, (self.x + self.width + 5, self.y - 2))


@dataclass
class PerceptionHUD:
    """Full HUD for perception system."""
    
    screen_width: int
    screen_height: int
    
    # Sub-components
    perception_meter: Optional[PerceptionMeter] = None
    transcendence_meter: Optional[TranscendenceMeter] = None
    
    # Hotkey display
    show_hotkeys: bool = True
    hotkey_fade: float = 1.0
    
    def __post_init__(self):
        # Position meters in top-right
        meter_x = self.screen_width - 200
        self.perception_meter = PerceptionMeter(x=meter_x, y=15)
        self.transcendence_meter = TranscendenceMeter(x=meter_x, y=35)
    
    def draw(
        self,
        screen: pygame.Surface,
        rules: DimensionalCombatRules,
        dimension: CombatDimension
    ) -> None:
        """Draw the full perception HUD."""
        font = pygame.font.Font(None, 18)
        
        # Draw meters
        self.perception_meter.draw(screen, rules, font)
        self.transcendence_meter.draw(screen, rules, font)
        
        # Draw dimension indicator
        self._draw_dimension_indicator(screen, dimension, font)
        
        # Draw available perception shifts
        self._draw_perception_options(screen, rules, font)
        
        # Draw hotkeys
        if self.show_hotkeys:
            self._draw_hotkeys(screen, rules, dimension, font)
    
    def _draw_dimension_indicator(
        self,
        screen: pygame.Surface,
        dimension: CombatDimension,
        font: pygame.font.Font
    ) -> None:
        """Draw current dimension indicator."""
        dim_colors = {
            CombatDimension.ONE_D: (100, 200, 255),
            CombatDimension.TWO_D: (255, 255, 255),
            CombatDimension.THREE_D: (200, 150, 255),
            CombatDimension.FOUR_D: (255, 200, 100),
        }
        
        dim_names = {
            CombatDimension.ONE_D: "1D - LINEAR",
            CombatDimension.TWO_D: "2D - PLANAR",
            CombatDimension.THREE_D: "3D - SPATIAL",
            CombatDimension.FOUR_D: "4D - TEMPORAL",
        }
        
        color = dim_colors.get(dimension, (255, 255, 255))
        name = dim_names.get(dimension, "UNKNOWN")
        
        # Draw in top-left
        label = font.render(f"DIMENSION: {name}", True, color)
        screen.blit(label, (15, 15))
    
    def _draw_perception_options(
        self,
        screen: pygame.Surface,
        rules: DimensionalCombatRules,
        font: pygame.font.Font
    ) -> None:
        """Draw available perception shift options."""
        x = 15
        y = 35
        
        states = [
            (PerceptionState.POINT, "0D", pygame.K_1),
            (PerceptionState.LINE, "1D", pygame.K_2),
            (PerceptionState.PLANE, "2D", pygame.K_3),
            (PerceptionState.VOLUME, "3D", pygame.K_4),
        ]
        
        for state, label, key in states:
            can_shift = rules.can_shift_perception(state)
            is_current = rules.current_perception == state
            
            # Color based on availability
            if is_current:
                color = (255, 255, 100)
                bg_color = (60, 60, 40)
            elif can_shift:
                color = (200, 200, 200)
                bg_color = (40, 40, 50)
            else:
                color = (80, 80, 80)
                bg_color = (30, 30, 35)
            
            # Background
            box_width = 35
            pygame.draw.rect(screen, bg_color, (x, y, box_width, 18))
            
            # Border
            border_color = color if is_current else (60, 60, 70)
            pygame.draw.rect(screen, border_color, (x, y, box_width, 18), 1)
            
            # Label
            text = font.render(label, True, color)
            screen.blit(text, (x + 5, y + 2))
            
            x += box_width + 5
    
    def _draw_hotkeys(
        self,
        screen: pygame.Surface,
        rules: DimensionalCombatRules,
        dimension: CombatDimension,
        font: pygame.font.Font
    ) -> None:
        """Draw control hints."""
        hints = [
            "[1-4] Shift Perception",
            "[T] Transcend" if rules.can_transcend() else "",
        ]
        
        # Add dimension-specific hints
        if dimension == CombatDimension.THREE_D:
            hints.append("[Q/E] Shift Depth")
        elif dimension == CombatDimension.FOUR_D:
            hints.append("[Q/E] Time Scrub")
        
        y = self.screen_height - 60
        for hint in hints:
            if hint:
                text = font.render(hint, True, (100, 100, 120))
                screen.blit(text, (self.screen_width - 150, y))
                y += 15


class PerceptionController:
    """Handles perception state input and transitions."""
    
    def __init__(self, rules: DimensionalCombatRules):
        self.rules = rules
        
        # Input mapping
        self.key_to_perception = {
            pygame.K_1: PerceptionState.POINT,
            pygame.K_2: PerceptionState.LINE,
            pygame.K_3: PerceptionState.PLANE,
            pygame.K_4: PerceptionState.VOLUME,
        }
        
        # Depth/time scrub input
        self.depth_input: float = 0.0
        self.time_input: float = 0.0
    
    def handle_input(self, event: pygame.event.Event) -> bool:
        """Handle perception-related input. Returns True if consumed."""
        if event.type == pygame.KEYDOWN:
            # Perception shifts
            if event.key in self.key_to_perception:
                target = self.key_to_perception[event.key]
                result = self._try_shift(target)
                return result == PerceptionShiftResult.SUCCESS
            
            # Transcendence
            if event.key == pygame.K_t:
                if self.rules.activate_transcendence():
                    return True
            
            # Depth/time controls
            if event.key == pygame.K_q:
                self.depth_input = -1.0
                self.time_input = -1.0
                return True
            elif event.key == pygame.K_e:
                self.depth_input = 1.0
                self.time_input = 1.0
                return True
        
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_q:
                self.depth_input = 0.0
                self.time_input = 0.0
            elif event.key == pygame.K_e:
                self.depth_input = 0.0
                self.time_input = 0.0
        
        return False
    
    def _try_shift(self, target: PerceptionState) -> PerceptionShiftResult:
        """Attempt to shift perception state."""
        if target == self.rules.current_perception:
            return PerceptionShiftResult.ALREADY_IN_STATE
        
        if self.rules.shift_cooldown > 0:
            return PerceptionShiftResult.ON_COOLDOWN
        
        abilities = PerceptionAbilities.for_state(target)
        if self.rules.perception_energy < abilities.activation_cost:
            return PerceptionShiftResult.NOT_ENOUGH_ENERGY
        
        if self.rules.start_perception_shift(target):
            return PerceptionShiftResult.SUCCESS
        
        return PerceptionShiftResult.BLOCKED_BY_ENEMY
    
    def get_movement_modifiers(self) -> Tuple[float, float, float, float]:
        """Get movement modifiers based on current perception.
        
        Returns: (x_mult, y_mult, depth_input, time_input)
        """
        abilities = PerceptionAbilities.for_state(self.rules.current_perception)
        
        x_mult = 1.0
        y_mult = 1.0
        
        if not abilities.can_move:
            x_mult = 0.0
            y_mult = 0.0
        elif abilities.horizontal_only:
            y_mult = 0.0
        elif abilities.vertical_only:
            x_mult = 0.0
        
        return x_mult, y_mult, self.depth_input, self.time_input


@dataclass
class DimensionalResonance:
    """Tracks resonance with each dimension for combat bonuses.
    
    Building resonance unlocks stronger abilities and affects available ACTs.
    """
    
    # Resonance levels (0-100)
    point_resonance: float = 0.0   # 0D - stillness, focus
    line_resonance: float = 0.0    # 1D - direction, determination  
    plane_resonance: float = 0.0   # 2D - balance, awareness
    volume_resonance: float = 0.0  # 3D - depth, understanding
    hyper_resonance: float = 0.0   # 4D - transcendence, unity
    
    max_resonance: float = 100.0
    decay_rate: float = 1.0  # Per second
    
    # Bonuses at high resonance
    resonance_thresholds = {
        25: "minor",   # Minor bonus
        50: "moderate", # Moderate bonus
        75: "major",   # Major bonus
        100: "master", # Master level
    }
    
    def add_resonance(self, dimension: str, amount: float) -> None:
        """Add resonance to a dimension."""
        if dimension == "point" or dimension == "0d":
            self.point_resonance = min(self.max_resonance, self.point_resonance + amount)
        elif dimension == "line" or dimension == "1d":
            self.line_resonance = min(self.max_resonance, self.line_resonance + amount)
        elif dimension == "plane" or dimension == "2d":
            self.plane_resonance = min(self.max_resonance, self.plane_resonance + amount)
        elif dimension == "volume" or dimension == "3d":
            self.volume_resonance = min(self.max_resonance, self.volume_resonance + amount)
        elif dimension == "hyper" or dimension == "4d":
            self.hyper_resonance = min(self.max_resonance, self.hyper_resonance + amount)
    
    def get_resonance(self, dimension: str) -> float:
        """Get resonance for a dimension."""
        mapping = {
            "point": self.point_resonance, "0d": self.point_resonance,
            "line": self.line_resonance, "1d": self.line_resonance,
            "plane": self.plane_resonance, "2d": self.plane_resonance,
            "volume": self.volume_resonance, "3d": self.volume_resonance,
            "hyper": self.hyper_resonance, "4d": self.hyper_resonance,
        }
        return mapping.get(dimension.lower(), 0.0)
    
    def get_bonus_tier(self, dimension: str) -> str:
        """Get the bonus tier for a dimension based on resonance."""
        resonance = self.get_resonance(dimension)
        
        tier = "none"
        for threshold, tier_name in sorted(self.resonance_thresholds.items()):
            if resonance >= threshold:
                tier = tier_name
        
        return tier
    
    def update(self, dt: float) -> None:
        """Decay resonance over time."""
        decay = self.decay_rate * dt
        self.point_resonance = max(0, self.point_resonance - decay)
        self.line_resonance = max(0, self.line_resonance - decay)
        self.plane_resonance = max(0, self.plane_resonance - decay)
        self.volume_resonance = max(0, self.volume_resonance - decay)
        self.hyper_resonance = max(0, self.hyper_resonance - decay)
    
    def get_damage_multiplier(self) -> float:
        """Get damage multiplier based on total resonance."""
        total = (self.point_resonance + self.line_resonance + 
                 self.plane_resonance + self.volume_resonance + 
                 self.hyper_resonance)
        # Up to 50% bonus damage at max resonance
        return 1.0 + (total / (self.max_resonance * 5)) * 0.5
    
    def get_defense_bonus(self, attack_dimension: str) -> float:
        """Get defense bonus against attacks from a specific dimension."""
        resonance = self.get_resonance(attack_dimension)
        # Up to 30% damage reduction at max resonance with matching dimension
        return resonance / self.max_resonance * 0.3
    
    def get_available_acts(self, base_acts: List[str]) -> List[str]:
        """Filter available ACTs based on resonance levels."""
        available = list(base_acts)
        
        # Add resonance-unlocked ACTs
        if self.get_bonus_tier("point") in ["major", "master"]:
            available.append("point_collapse")  # Defensive ACT
        
        if self.get_bonus_tier("line") in ["major", "master"]:
            available.append("line_focus")  # Directional attack boost
        
        if self.get_bonus_tier("plane") in ["moderate", "major", "master"]:
            available.append("geometric_meditation")  # Heal/defense
        
        if self.get_bonus_tier("volume") in ["major", "master"]:
            available.append("phase_mastery")  # Enhanced phasing
        
        if self.get_bonus_tier("hyper") in ["master"]:
            available.append("transcendent_strike")  # Ultimate attack
        
        return available


@dataclass
class ResonanceMeter:
    """Visual display for dimensional resonance."""
    
    x: float
    y: float
    width: float = 100
    bar_height: float = 8
    spacing: float = 3
    
    dimension_colors = {
        "point": (100, 100, 255),
        "line": (100, 200, 255),
        "plane": (255, 255, 255),
        "volume": (200, 100, 255),
        "hyper": (255, 200, 100),
    }
    
    def draw(
        self,
        screen: pygame.Surface,
        resonance: DimensionalResonance,
        font: Optional[pygame.font.Font] = None
    ) -> None:
        """Draw resonance meters."""
        if font is None:
            font = pygame.font.Font(None, 14)
        
        y = self.y
        
        dimensions = ["point", "line", "plane", "volume", "hyper"]
        labels = ["0D", "1D", "2D", "3D", "4D"]
        
        for dim, label in zip(dimensions, labels):
            value = resonance.get_resonance(dim)
            color = self.dimension_colors[dim]
            tier = resonance.get_bonus_tier(dim)
            
            # Background
            pygame.draw.rect(screen, (30, 30, 40),
                           (int(self.x), int(y), int(self.width), int(self.bar_height)))
            
            # Fill
            fill_width = int(self.width * value / resonance.max_resonance)
            pygame.draw.rect(screen, color,
                           (int(self.x), int(y), fill_width, int(self.bar_height)))
            
            # Border (brighter if has bonus tier)
            border_color = (60, 60, 70) if tier == "none" else color
            pygame.draw.rect(screen, border_color,
                           (int(self.x), int(y), int(self.width), int(self.bar_height)), 1)
            
            # Label
            label_text = font.render(label, True, color)
            screen.blit(label_text, (self.x - 22, y - 1))
            
            # Tier indicator
            if tier != "none":
                tier_text = font.render(tier[0].upper(), True, (255, 255, 200))
                screen.blit(tier_text, (self.x + self.width + 3, y - 1))
            
            y += self.bar_height + self.spacing


# Resonance building actions during combat
RESONANCE_ACTIONS: Dict[str, Callable[[DimensionalResonance, float], str]] = {
    "graze": lambda res, amount: (
        res.add_resonance("plane", amount),
        "Plane resonance increased!"
    )[1],
    
    "perfect_dodge": lambda res, amount: (
        res.add_resonance("volume", amount * 1.5),
        "Volume resonance increased!"
    )[1],
    
    "stay_still": lambda res, amount: (
        res.add_resonance("point", amount),
        "Point resonance increased!"
    )[1],
    
    "directional_dodge": lambda res, amount: (
        res.add_resonance("line", amount),
        "Line resonance increased!"
    )[1],
    
    "predict_attack": lambda res, amount: (
        res.add_resonance("hyper", amount * 2),
        "Hyper resonance increased!"
    )[1],
}
