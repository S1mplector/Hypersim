"""Dimensional Enemy AI - Enemies that use dimensional mechanics strategically.

This module provides AI behavior for enemies that:
1. React to player's perception state
2. Use perception attacks to disrupt the player
3. Adapt attack patterns based on dimension
4. Have dimension-specific special abilities
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

from .dimensional_combat import (
    CombatDimension, PerceptionState, DimensionalCombatRules,
    DimensionalBullet, DimensionalPatternGenerator
)

if TYPE_CHECKING:
    from .enemies import CombatEnemy


class EnemyAIType(Enum):
    """Types of enemy AI behavior."""
    PASSIVE = auto()      # Just attacks, no special tactics
    REACTIVE = auto()     # Reacts to player perception
    AGGRESSIVE = auto()   # Tries to overwhelm player
    TACTICAL = auto()     # Uses perception attacks strategically
    BOSS = auto()         # Complex multi-phase behavior


class PerceptionAttackType(Enum):
    """Types of perception-altering attacks enemies can use."""
    COLLAPSE = auto()     # Force player to lower dimension
    EXPAND = auto()       # Force player to higher dimension (overwhelming)
    INVERT = auto()       # Invert player controls
    BLIND = auto()        # Reduce player visibility
    LOCK = auto()         # Prevent perception shifts
    FRACTURE = auto()     # Damage player's perception stability


@dataclass
class PerceptionAttack:
    """A perception-altering attack an enemy can use."""
    attack_type: PerceptionAttackType
    target_perception: Optional[PerceptionState] = None
    duration: float = 3.0
    cooldown: float = 8.0
    
    # For display
    dialogue: str = ""
    
    def get_effect_text(self) -> str:
        """Get the effect text for this attack."""
        texts = {
            PerceptionAttackType.COLLAPSE: "* Reality collapses around you!",
            PerceptionAttackType.EXPAND: "* Too many dimensions flood your senses!",
            PerceptionAttackType.INVERT: "* Everything is backwards!",
            PerceptionAttackType.BLIND: "* Your perception dims...",
            PerceptionAttackType.LOCK: "* Your perception is locked in place!",
            PerceptionAttackType.FRACTURE: "* Your perception fractures!",
        }
        return self.dialogue or texts.get(self.attack_type, "* Something strange happens...")


@dataclass
class DimensionalEnemyAI:
    """AI controller for dimension-aware enemies."""
    
    ai_type: EnemyAIType = EnemyAIType.REACTIVE
    dimension: CombatDimension = CombatDimension.TWO_D
    
    # Perception attacks this enemy can use
    perception_attacks: List[PerceptionAttack] = field(default_factory=list)
    perception_attack_cooldown: float = 0.0
    
    # Attack pattern preferences
    preferred_patterns: List[str] = field(default_factory=list)
    pattern_weights: Dict[str, float] = field(default_factory=dict)
    
    # Behavior thresholds
    aggression: float = 0.5  # 0-1, affects attack frequency/intensity
    perception_attack_chance: float = 0.2  # Chance to use perception attack
    
    # State tracking
    turns_since_perception_attack: int = 0
    player_perception_history: List[PerceptionState] = field(default_factory=list)
    
    # Boss phases
    current_phase: int = 0
    phase_thresholds: List[float] = field(default_factory=lambda: [0.75, 0.5, 0.25])
    
    def update(self, dt: float) -> None:
        """Update AI state."""
        if self.perception_attack_cooldown > 0:
            self.perception_attack_cooldown -= dt
    
    def record_player_perception(self, perception: PerceptionState) -> None:
        """Record player's perception state for analysis."""
        self.player_perception_history.append(perception)
        if len(self.player_perception_history) > 20:
            self.player_perception_history.pop(0)
    
    def get_player_tendency(self) -> Optional[PerceptionState]:
        """Analyze what perception state the player uses most."""
        if len(self.player_perception_history) < 5:
            return None
        
        counts = {}
        for p in self.player_perception_history:
            counts[p] = counts.get(p, 0) + 1
        
        return max(counts.items(), key=lambda x: x[1])[0]
    
    def should_use_perception_attack(self, enemy_hp_ratio: float) -> bool:
        """Decide if enemy should use a perception attack this turn."""
        if self.perception_attack_cooldown > 0:
            return False
        
        if not self.perception_attacks:
            return False
        
        # Increase chance when low on HP
        adjusted_chance = self.perception_attack_chance
        if enemy_hp_ratio < 0.5:
            adjusted_chance *= 1.5
        if enemy_hp_ratio < 0.25:
            adjusted_chance *= 2.0
        
        # Tactical AI waits for good opportunities
        if self.ai_type == EnemyAIType.TACTICAL:
            player_tendency = self.get_player_tendency()
            if player_tendency and player_tendency != PerceptionState.PLANE:
                adjusted_chance *= 1.5  # Player relies on a specific perception
        
        return random.random() < adjusted_chance
    
    def select_perception_attack(
        self, 
        player_perception: PerceptionState
    ) -> Optional[PerceptionAttack]:
        """Select the best perception attack to use."""
        if not self.perception_attacks:
            return None
        
        # For tactical AI, counter the player's current perception
        if self.ai_type == EnemyAIType.TACTICAL:
            counters = {
                PerceptionState.POINT: PerceptionAttackType.EXPAND,  # Force out of invuln
                PerceptionState.LINE: PerceptionAttackType.COLLAPSE,  # Even more restricted
                PerceptionState.PLANE: PerceptionAttackType.FRACTURE,  # Disrupt default
                PerceptionState.VOLUME: PerceptionAttackType.COLLAPSE,  # Remove phasing
                PerceptionState.HYPER: PerceptionAttackType.BLIND,  # Counter trajectory sight
            }
            
            target_type = counters.get(player_perception)
            for attack in self.perception_attacks:
                if attack.attack_type == target_type:
                    return attack
        
        # Otherwise, random selection
        return random.choice(self.perception_attacks)
    
    def apply_perception_attack(
        self, 
        attack: PerceptionAttack,
        rules: DimensionalCombatRules
    ) -> str:
        """Apply a perception attack to the player. Returns effect text."""
        self.perception_attack_cooldown = attack.cooldown
        self.turns_since_perception_attack = 0
        
        if attack.attack_type == PerceptionAttackType.COLLAPSE:
            # Force to lower perception
            if rules.current_perception == PerceptionState.HYPER:
                rules.current_perception = PerceptionState.VOLUME
            elif rules.current_perception == PerceptionState.VOLUME:
                rules.current_perception = PerceptionState.PLANE
            elif rules.current_perception == PerceptionState.PLANE:
                rules.current_perception = PerceptionState.LINE
        
        elif attack.attack_type == PerceptionAttackType.EXPAND:
            # Force to unstable higher perception (costs energy)
            rules.perception_energy = max(0, rules.perception_energy - 30)
            rules.current_perception = PerceptionState.FRACTURED
        
        elif attack.attack_type == PerceptionAttackType.LOCK:
            # Increase shift cooldown dramatically
            rules.shift_cooldown = max(rules.shift_cooldown, attack.duration)
        
        elif attack.attack_type == PerceptionAttackType.FRACTURE:
            rules.current_perception = PerceptionState.FRACTURED
            rules.perception_energy = max(0, rules.perception_energy - 15)
        
        return attack.get_effect_text()
    
    def select_attack_pattern(
        self, 
        player_perception: PerceptionState,
        difficulty: float = 1.0
    ) -> Tuple[str, float]:
        """Select attack pattern based on AI type and player state.
        
        Returns: (pattern_name, difficulty_modifier)
        """
        patterns_1d = ["line_sweep", "converging_points", "segment_wave"]
        patterns_2d = ["triangle_formation", "square_grid", "circle_spiral"]
        patterns_3d = ["depth_wave", "phasing_cubes", "shadow_assault"]
        patterns_4d = ["temporal_burst", "past_echo", "future_convergence"]
        
        dimension_patterns = {
            CombatDimension.ONE_D: patterns_1d,
            CombatDimension.TWO_D: patterns_2d,
            CombatDimension.THREE_D: patterns_3d,
            CombatDimension.FOUR_D: patterns_4d,
        }
        
        available = dimension_patterns.get(self.dimension, patterns_2d)
        
        # Use preferred patterns if set
        if self.preferred_patterns:
            available = [p for p in available if p in self.preferred_patterns] or available
        
        # Tactical AI picks patterns that counter player perception
        difficulty_mod = 1.0
        if self.ai_type == EnemyAIType.TACTICAL:
            if player_perception == PerceptionState.LINE:
                # Player restricted to horizontal - use vertical attacks
                difficulty_mod = 1.2
            elif player_perception == PerceptionState.POINT:
                # Player is frozen - wait out or prepare big attack
                difficulty_mod = 0.8  # Lighter attack, save for when they move
            elif player_perception == PerceptionState.VOLUME:
                # Player can phase - use multi-layer attacks
                if self.dimension == CombatDimension.THREE_D:
                    available = ["depth_wave"]  # Hard to dodge with phasing
                difficulty_mod = 1.3
        
        # Aggressive AI increases difficulty
        if self.ai_type == EnemyAIType.AGGRESSIVE:
            difficulty_mod *= 1.0 + self.aggression * 0.5
        
        pattern = random.choice(available)
        return pattern, difficulty * difficulty_mod
    
    def get_boss_phase(self, hp_ratio: float) -> int:
        """Get current boss phase based on HP."""
        phase = 0
        for threshold in self.phase_thresholds:
            if hp_ratio <= threshold:
                phase += 1
        return phase
    
    def update_boss_phase(self, hp_ratio: float) -> Optional[str]:
        """Check and update boss phase. Returns phase transition text if changed."""
        new_phase = self.get_boss_phase(hp_ratio)
        
        if new_phase > self.current_phase:
            self.current_phase = new_phase
            
            # Phase transition effects
            phase_texts = [
                "* The enemy's form shifts!",
                "* Reality warps around the enemy!",
                "* The enemy reveals its true power!",
                "* FINAL FORM ACHIEVED",
            ]
            
            # Increase aggression with each phase
            self.aggression = min(1.0, self.aggression + 0.2)
            
            return phase_texts[min(new_phase - 1, len(phase_texts) - 1)]
        
        return None


def create_ai_for_enemy(enemy: "CombatEnemy") -> DimensionalEnemyAI:
    """Create appropriate AI for an enemy based on their properties."""
    dimension = get_dimension_from_string(getattr(enemy, 'dimension', '2d'))
    is_boss = getattr(enemy, 'is_boss', False)
    
    # Determine AI type
    if is_boss:
        ai_type = EnemyAIType.BOSS
    elif dimension == CombatDimension.FOUR_D:
        ai_type = EnemyAIType.TACTICAL
    elif dimension == CombatDimension.THREE_D:
        ai_type = EnemyAIType.REACTIVE
    else:
        ai_type = EnemyAIType.PASSIVE
    
    # Build perception attacks based on dimension
    perception_attacks = []
    
    if dimension == CombatDimension.ONE_D:
        perception_attacks.append(PerceptionAttack(
            attack_type=PerceptionAttackType.COLLAPSE,
            dialogue="* Reality compresses to a line!",
            cooldown=10.0,
        ))
    
    elif dimension == CombatDimension.TWO_D:
        perception_attacks.append(PerceptionAttack(
            attack_type=PerceptionAttackType.INVERT,
            dialogue="* Your perception flips!",
            cooldown=8.0,
        ))
    
    elif dimension == CombatDimension.THREE_D:
        perception_attacks.extend([
            PerceptionAttack(
                attack_type=PerceptionAttackType.COLLAPSE,
                dialogue="* Depth collapses around you!",
                cooldown=8.0,
            ),
            PerceptionAttack(
                attack_type=PerceptionAttackType.BLIND,
                dialogue="* Shadows obscure your vision!",
                cooldown=12.0,
            ),
        ])
    
    elif dimension == CombatDimension.FOUR_D:
        perception_attacks.extend([
            PerceptionAttack(
                attack_type=PerceptionAttackType.FRACTURE,
                dialogue="* Time splinters your perception!",
                cooldown=6.0,
            ),
            PerceptionAttack(
                attack_type=PerceptionAttackType.EXPAND,
                dialogue="* Too many timelines flood your mind!",
                cooldown=10.0,
            ),
            PerceptionAttack(
                attack_type=PerceptionAttackType.LOCK,
                dialogue="* Your perception is frozen in time!",
                cooldown=15.0,
            ),
        ])
    
    # Boss gets all attacks with lower cooldowns
    if is_boss:
        for attack in perception_attacks:
            attack.cooldown *= 0.7
        
        # Add extra attacks for bosses
        perception_attacks.append(PerceptionAttack(
            attack_type=PerceptionAttackType.FRACTURE,
            dialogue="* Your dimensional awareness shatters!",
            cooldown=5.0,
        ))
    
    return DimensionalEnemyAI(
        ai_type=ai_type,
        dimension=dimension,
        perception_attacks=perception_attacks,
        aggression=0.7 if is_boss else 0.5,
        perception_attack_chance=0.3 if is_boss else 0.15,
    )


def get_dimension_from_string(dim_str: str) -> CombatDimension:
    """Convert dimension string to enum."""
    mapping = {
        "1d": CombatDimension.ONE_D,
        "2d": CombatDimension.TWO_D,
        "3d": CombatDimension.THREE_D,
        "4d": CombatDimension.FOUR_D,
    }
    return mapping.get(dim_str.lower(), CombatDimension.TWO_D)


# Pre-built AI behaviors for specific enemy types
ENEMY_AI_PRESETS: Dict[str, DimensionalEnemyAI] = {
    "point_spirit": DimensionalEnemyAI(
        ai_type=EnemyAIType.PASSIVE,
        dimension=CombatDimension.ONE_D,
        aggression=0.3,
    ),
    
    "line_walker": DimensionalEnemyAI(
        ai_type=EnemyAIType.REACTIVE,
        dimension=CombatDimension.ONE_D,
        perception_attacks=[
            PerceptionAttack(
                attack_type=PerceptionAttackType.COLLAPSE,
                dialogue="* The Line Walker forces you onto its path!",
            ),
        ],
        aggression=0.5,
    ),
    
    "tesseract_guardian": DimensionalEnemyAI(
        ai_type=EnemyAIType.BOSS,
        dimension=CombatDimension.FOUR_D,
        perception_attacks=[
            PerceptionAttack(
                attack_type=PerceptionAttackType.FRACTURE,
                dialogue="* 4D geometry shatters your perception!",
                cooldown=5.0,
            ),
            PerceptionAttack(
                attack_type=PerceptionAttackType.EXPAND,
                dialogue="* The Tesseract unfolds through your mind!",
                cooldown=8.0,
            ),
            PerceptionAttack(
                attack_type=PerceptionAttackType.LOCK,
                dialogue="* Your perception is trapped in a hypercube!",
                cooldown=10.0,
            ),
        ],
        aggression=0.8,
        perception_attack_chance=0.35,
        phase_thresholds=[0.7, 0.4, 0.15],
    ),
    
    "threshold_guardian": DimensionalEnemyAI(
        ai_type=EnemyAIType.BOSS,
        dimension=CombatDimension.FOUR_D,
        perception_attacks=[
            PerceptionAttack(
                attack_type=PerceptionAttackType.FRACTURE,
                dialogue="* Reality itself rejects your perception!",
                cooldown=4.0,
            ),
            PerceptionAttack(
                attack_type=PerceptionAttackType.EXPAND,
                dialogue="* INFINITE DIMENSIONS CONVERGE!",
                cooldown=6.0,
            ),
            PerceptionAttack(
                attack_type=PerceptionAttackType.COLLAPSE,
                dialogue="* You are compressed to nothing!",
                cooldown=7.0,
            ),
            PerceptionAttack(
                attack_type=PerceptionAttackType.LOCK,
                dialogue="* The Threshold seals your perception!",
                cooldown=12.0,
            ),
        ],
        aggression=0.9,
        perception_attack_chance=0.4,
        phase_thresholds=[0.8, 0.6, 0.4, 0.2],
    ),
}


def get_enemy_ai(enemy_id: str, enemy: Optional["CombatEnemy"] = None) -> DimensionalEnemyAI:
    """Get AI for an enemy by ID, or create one dynamically."""
    if enemy_id in ENEMY_AI_PRESETS:
        return ENEMY_AI_PRESETS[enemy_id]
    
    if enemy:
        return create_ai_for_enemy(enemy)
    
    return DimensionalEnemyAI()
