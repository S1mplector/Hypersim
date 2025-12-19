"""Base classes and shared utilities for enemy definitions.

Re-exports core combat classes for convenience.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

from ..core import CombatStats, SoulMode


class EnemyPersonality(Enum):
    """Enemy personality types that affect dialogue and ACT options."""
    AGGRESSIVE = auto()    # Wants to fight
    TIMID = auto()         # Scared, can be comforted
    LONELY = auto()        # Wants attention/friendship
    PROUD = auto()         # Responds to compliments
    CONFUSED = auto()      # Doesn't understand the situation
    PLAYFUL = auto()       # Treats combat as a game
    PHILOSOPHICAL = auto() # Questions existence/dimensions
    GEOMETRIC = auto()     # Obsessed with shapes


class EnemyMood(Enum):
    """Current mood of enemy - affects sparability and attacks."""
    HOSTILE = auto()       # Full aggression
    AGGRESSIVE = auto()    # Somewhat hostile
    NEUTRAL = auto()       # Default state
    CURIOUS = auto()       # Interested in player
    FRIENDLY = auto()      # Warming up
    SPAREABLE = auto()     # Can be spared


@dataclass
class ACTOption:
    """An ACT option for interacting with an enemy."""
    id: str
    name: str
    description: str
    
    # Effects
    mood_change: int = 0           # Change to enemy mood (positive = friendlier)
    damage: int = 0                # Damage to enemy (usually 0)
    self_damage: int = 0           # Damage to player
    heal: int = 0                  # Healing to player
    
    # Requirements
    requires_item: Optional[str] = None
    requires_mood: Optional[EnemyMood] = None
    requires_turn: int = 0         # Minimum turn number
    uses: int = -1                 # -1 = unlimited, otherwise limited uses
    
    # Dialogue response
    success_dialogue: str = ""
    fail_dialogue: str = ""
    
    # Special effects
    changes_soul_mode: Optional[SoulMode] = None
    special_effect: Optional[str] = None
    
    # Flags
    always_succeeds: bool = True
    ends_turn: bool = True


@dataclass
class EnemyAttackPattern:
    """Definition of an enemy attack pattern."""
    id: str
    name: str
    duration: float = 3.0
    
    # Pattern type
    pattern_type: str = "bullets"  # bullets, wave, geometric, chase, etc.
    
    # Bullet parameters
    bullet_count: int = 10
    bullet_speed: float = 150.0
    bullet_size: float = 8.0
    
    # Wave parameters
    wave_count: int = 1
    wave_delay: float = 0.5
    
    # Soul mode for this attack
    soul_mode: SoulMode = SoulMode.RED
    
    # Difficulty scaling
    base_difficulty: float = 1.0
    
    # Special properties
    telegraphed: bool = False      # Shows warning before attack
    grazing_bonus: bool = False    # Bonus for near-misses
    
    # Dialogue during attack
    attack_dialogue: str = ""


@dataclass
class CombatEnemy:
    """A combat encounter enemy."""
    id: str
    name: str
    
    # Stats
    stats: CombatStats = field(default_factory=CombatStats)
    
    # Personality
    personality: EnemyPersonality = EnemyPersonality.AGGRESSIVE
    mood: EnemyMood = EnemyMood.NEUTRAL
    mood_points: int = 0           # Progress towards spareable
    spare_threshold: int = 100     # Points needed to spare
    
    # Visual
    sprite_id: str = ""
    color: Tuple[int, int, int] = (255, 255, 255)
    
    # Dimensional origin
    dimension: str = "1d"
    
    # Dialogue
    encounter_text: str = ""       # Text when battle starts
    check_text: str = ""           # Text when using CHECK
    idle_dialogues: List[str] = field(default_factory=list)
    hurt_dialogues: List[str] = field(default_factory=list)
    low_hp_dialogues: List[str] = field(default_factory=list)
    spare_dialogue: str = ""       # When enemy is spared
    kill_dialogue: str = ""        # When enemy is killed
    
    # ACT options
    act_options: List[ACTOption] = field(default_factory=list)
    
    # Attack patterns
    attack_patterns: List[EnemyAttackPattern] = field(default_factory=list)
    current_pattern_index: int = 0
    
    # Combat state
    turns_taken: int = 0
    times_spared: int = 0          # Times player chose spare when not ready
    times_hurt: int = 0
    acted_this_turn: List[str] = field(default_factory=list)
    
    # Rewards
    xp_reward: int = 10
    gold_reward: int = 5
    spare_gold_reward: int = 0     # Extra gold for sparing
    
    # Flags
    can_spare: bool = True
    can_flee: bool = True
    is_boss: bool = False
    
    @property
    def is_spareable(self) -> bool:
        """Check if enemy can currently be spared."""
        return self.mood == EnemyMood.SPAREABLE or self.mood_points >= self.spare_threshold
    
    @property
    def hp_ratio(self) -> float:
        return self.stats.hp_ratio
    
    def add_mood_points(self, amount: int) -> None:
        """Add mood points and potentially change mood."""
        self.mood_points += amount
        self._update_mood()
    
    def _update_mood(self) -> None:
        """Update mood based on mood points."""
        if self.mood_points >= self.spare_threshold:
            self.mood = EnemyMood.SPAREABLE
        elif self.mood_points >= self.spare_threshold * 0.75:
            self.mood = EnemyMood.FRIENDLY
        elif self.mood_points >= self.spare_threshold * 0.5:
            self.mood = EnemyMood.CURIOUS
        elif self.mood_points >= self.spare_threshold * 0.25:
            self.mood = EnemyMood.NEUTRAL
        elif self.mood_points < 0:
            self.mood = EnemyMood.HOSTILE
    
    def get_next_attack(self) -> EnemyAttackPattern:
        """Get the next attack pattern."""
        if not self.attack_patterns:
            return EnemyAttackPattern(id="default", name="Default", duration=2.0)
        
        pattern = self.attack_patterns[self.current_pattern_index]
        self.current_pattern_index = (self.current_pattern_index + 1) % len(self.attack_patterns)
        return pattern
    
    def get_dialogue(self) -> str:
        """Get appropriate dialogue based on state."""
        import random
        
        if self.stats.hp_ratio < 0.25 and self.low_hp_dialogues:
            return random.choice(self.low_hp_dialogues)
        
        if self.times_hurt > 0 and self.hurt_dialogues:
            return random.choice(self.hurt_dialogues)
        
        if self.idle_dialogues:
            return random.choice(self.idle_dialogues)
        
        return "..."
    
    def perform_act(self, act_id: str) -> Tuple[bool, str, int]:
        """Perform an ACT option. Returns (success, dialogue, mood_change)."""
        for act in self.act_options:
            if act.id == act_id:
                self.acted_this_turn.append(act_id)
                
                # Check requirements
                if act.requires_mood and self.mood != act.requires_mood:
                    return False, act.fail_dialogue or "It doesn't seem effective...", 0
                
                if act.requires_turn > self.turns_taken:
                    return False, "It's too early for that...", 0
                
                if act.uses == 0:
                    return False, "You can't do that anymore...", 0
                
                # Apply effects
                if act.uses > 0:
                    act.uses -= 1
                
                self.add_mood_points(act.mood_change)
                
                dialogue = act.success_dialogue or f"You {act.name}."
                
                return True, dialogue, act.mood_change
        
        return False, "Nothing happened.", 0
    
    def end_turn(self) -> None:
        """Called at end of turn."""
        self.turns_taken += 1
        self.acted_this_turn.clear()


# Utility function for creating CHECK ACT option
def check_act() -> ACTOption:
    """Create a standard CHECK ACT option."""
    return ACTOption(
        id="check",
        name="Check",
        description="Examine the enemy.",
        mood_change=0,
        always_succeeds=True,
    )
