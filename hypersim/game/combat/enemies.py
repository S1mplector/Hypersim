"""Combat enemy definitions and ACT system."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple

from .core import CombatStats, SoulMode


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
        if self.stats.hp_ratio < 0.25 and self.low_hp_dialogues:
            import random
            return random.choice(self.low_hp_dialogues)
        
        if self.times_hurt > 0 and self.hurt_dialogues:
            import random
            return random.choice(self.hurt_dialogues)
        
        if self.idle_dialogues:
            import random
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


# =============================================================================
# DIMENSIONAL ENEMIES
# =============================================================================

def create_1d_enemies() -> Dict[str, CombatEnemy]:
    """Create 1D dimensional enemies."""
    return {
        "line_walker": CombatEnemy(
            id="line_walker",
            name="Line Walker",
            stats=CombatStats(hp=15, max_hp=15, attack=5, defense=2),
            personality=EnemyPersonality.CONFUSED,
            dimension="1d",
            color=(100, 200, 255),
            encounter_text="* Line Walker blocks your path!",
            check_text="* LINE WALKER - ATK 5 DEF 2\n* Knows only forward and backward.\n* Seems confused by your width.",
            idle_dialogues=[
                "* Line Walker vibrates uncertainly.",
                "* Line Walker looks left and right... wait, it can't.",
                "* (It seems to only perceive one direction.)",
            ],
            hurt_dialogues=[
                "* Line Walker contracts in pain.",
                "* \"Ow... that came from... where?\"",
            ],
            low_hp_dialogues=[
                "* Line Walker is barely holding together.",
                "* \"Please... I just want to go forward...\"",
            ],
            spare_dialogue="* Line Walker extends past you gratefully.",
            kill_dialogue="* Line Walker collapses into a point.",
            act_options=[
                ACTOption(
                    id="check",
                    name="Check",
                    description="Examine the enemy.",
                    mood_change=0,
                    always_succeeds=True,
                ),
                ACTOption(
                    id="explain",
                    name="Explain",
                    description="Try to explain 2D to them.",
                    mood_change=25,
                    success_dialogue="* You try to explain 'width'.\n* Line Walker is fascinated!",
                ),
                ACTOption(
                    id="step_aside",
                    name="Step Aside",
                    description="Move perpendicular to its path.",
                    mood_change=50,
                    success_dialogue="* You step sideways.\n* Line Walker passes by, amazed.\n* \"You... disappeared?!\"",
                ),
                ACTOption(
                    id="point",
                    name="Point Forward",
                    description="Point in its direction of travel.",
                    mood_change=15,
                    success_dialogue="* You point forward.\n* Line Walker feels understood.",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="line_dash",
                    name="Line Dash",
                    duration=3.0,
                    pattern_type="horizontal_lines",
                    bullet_count=5,
                    bullet_speed=200,
                    attack_dialogue="* Line Walker charges back and forth!",
                ),
                EnemyAttackPattern(
                    id="pulse_wave",
                    name="Pulse Wave",
                    duration=4.0,
                    pattern_type="pulse",
                    wave_count=3,
                    bullet_speed=150,
                    attack_dialogue="* Line Walker pulses with energy!",
                ),
            ],
            xp_reward=5,
            gold_reward=3,
            spare_gold_reward=5,
        ),
        
        "segment_guardian": CombatEnemy(
            id="segment_guardian",
            name="Segment Guardian",
            stats=CombatStats(hp=25, max_hp=25, attack=8, defense=5),
            personality=EnemyPersonality.PROUD,
            dimension="1d",
            color=(255, 200, 100),
            encounter_text="* Segment Guardian stands firm!",
            check_text="* SEGMENT GUARDIAN - ATK 8 DEF 5\n* Proud of its clearly defined endpoints.\n* Won't let just anyone pass.",
            idle_dialogues=[
                "* Segment Guardian measures you carefully.",
                "* \"My length is EXACTLY optimal.\"",
                "* Segment Guardian flexes its endpoints.",
            ],
            spare_dialogue="* Segment Guardian extends to let you pass.",
            act_options=[
                ACTOption(id="check", name="Check", description="Examine the enemy.", mood_change=0),
                ACTOption(
                    id="compliment",
                    name="Compliment",
                    description="Praise its endpoints.",
                    mood_change=35,
                    success_dialogue="* You compliment its well-defined boundaries.\n* Segment Guardian beams with pride!",
                ),
                ACTOption(
                    id="measure",
                    name="Measure",
                    description="Respectfully measure its length.",
                    mood_change=40,
                    success_dialogue="* You measure carefully and nod approvingly.\n* Segment Guardian is flattered!",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="endpoint_thrust",
                    name="Endpoint Thrust",
                    duration=3.5,
                    pattern_type="thrust",
                    bullet_speed=250,
                ),
            ],
            xp_reward=8,
            gold_reward=5,
        ),
    }


def create_2d_enemies() -> Dict[str, CombatEnemy]:
    """Create 2D dimensional enemies."""
    return {
        "triangle_scout": CombatEnemy(
            id="triangle_scout",
            name="Triangle Scout",
            stats=CombatStats(hp=20, max_hp=20, attack=7, defense=3),
            personality=EnemyPersonality.AGGRESSIVE,
            dimension="2d",
            color=(255, 100, 100),
            encounter_text="* Triangle Scout points at you threateningly!",
            check_text="* TRIANGLE SCOUT - ATK 7 DEF 3\n* The simplest polygon.\n* Very pointy. Very aggressive.",
            idle_dialogues=[
                "* Triangle Scout rotates menacingly.",
                "* \"THREE SIDES! THREE CORNERS! PERFECT!\"",
                "* Triangle Scout's vertices gleam.",
            ],
            hurt_dialogues=[
                "* One of Triangle Scout's corners chips.",
                "* \"MY ANGLES!\"",
            ],
            spare_dialogue="* Triangle Scout rolls away, satisfied.",
            act_options=[
                ACTOption(id="check", name="Check", description="Examine the enemy."),
                ACTOption(
                    id="discuss_angles",
                    name="Angles",
                    description="Discuss interior angles.",
                    mood_change=30,
                    success_dialogue="* You discuss the beauty of 60° angles.\n* Triangle Scout nods rapidly!",
                ),
                ACTOption(
                    id="admire_vertices",
                    name="Admire",
                    description="Admire its sharp vertices.",
                    mood_change=35,
                    success_dialogue="* You comment on its sharp vertices.\n* Triangle Scout is pleased!",
                ),
                ACTOption(
                    id="challenge",
                    name="Challenge",
                    description="Challenge it to a rotation contest.",
                    mood_change=40,
                    success_dialogue="* You both spin! It's a tie!\n* Triangle Scout respects you now.",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="spin_attack",
                    name="Spin Attack",
                    duration=4.0,
                    pattern_type="spinning_triangles",
                    bullet_count=3,
                    bullet_speed=180,
                ),
                EnemyAttackPattern(
                    id="corner_shot",
                    name="Corner Shot",
                    duration=3.0,
                    pattern_type="aimed_triangles",
                    bullet_count=9,
                    bullet_speed=220,
                ),
            ],
            xp_reward=10,
            gold_reward=8,
        ),
        
        "square_citizen": CombatEnemy(
            id="square_citizen",
            name="Square Citizen",
            stats=CombatStats(hp=30, max_hp=30, attack=6, defense=8),
            personality=EnemyPersonality.TIMID,
            dimension="2d",
            color=(100, 150, 255),
            encounter_text="* Square Citizen nervously approaches!",
            check_text="* SQUARE CITIZEN - ATK 6 DEF 8\n* A law-abiding rectangle.\n* Seems uncomfortable with conflict.",
            idle_dialogues=[
                "* Square Citizen adjusts its right angles.",
                "* \"I-I'm just trying to tile peacefully...\"",
                "* Square Citizen looks for an exit.",
            ],
            spare_dialogue="* Square Citizen tiles away in relief.",
            act_options=[
                ACTOption(id="check", name="Check", description="Examine the enemy."),
                ACTOption(
                    id="reassure",
                    name="Reassure",
                    description="Tell them everything's okay.",
                    mood_change=40,
                    success_dialogue="* You speak calmly.\n* Square Citizen relaxes slightly.",
                ),
                ACTOption(
                    id="compliment_angles",
                    name="Right Angles",
                    description="Compliment their perfect right angles.",
                    mood_change=35,
                    success_dialogue="* \"R-really? You think they're nice?\"\n* Square Citizen blushes somehow.",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="grid_panic",
                    name="Grid Panic",
                    duration=3.5,
                    pattern_type="grid",
                    bullet_count=16,
                    bullet_speed=120,
                    attack_dialogue="* Square Citizen panics!",
                ),
            ],
            xp_reward=8,
            gold_reward=12,
            spare_gold_reward=10,
        ),
        
        "circle_mystic": CombatEnemy(
            id="circle_mystic",
            name="Circle Mystic",
            stats=CombatStats(hp=35, max_hp=35, attack=9, defense=4),
            personality=EnemyPersonality.PHILOSOPHICAL,
            dimension="2d",
            color=(200, 100, 255),
            encounter_text="* Circle Mystic rolls into view, contemplating infinity.",
            check_text="* CIRCLE MYSTIC - ATK 9 DEF 4\n* Has infinite sides, or zero?\n* Ponders the nature of π.",
            idle_dialogues=[
                "* \"Is my circumference truly endless?\"",
                "* Circle Mystic contemplates its center.",
                "* \"We are all just points rotating around meaning...\"",
            ],
            spare_dialogue="* Circle Mystic rolls away, at peace.",
            act_options=[
                ACTOption(id="check", name="Check", description="Examine the enemy."),
                ACTOption(
                    id="discuss_pi",
                    name="Discuss π",
                    description="Engage in mathematical philosophy.",
                    mood_change=45,
                    success_dialogue="* You discuss the transcendence of π.\n* Circle Mystic is deeply moved!",
                ),
                ACTOption(
                    id="meditate",
                    name="Meditate",
                    description="Meditate on circular nature.",
                    mood_change=50,
                    success_dialogue="* You both contemplate infinity.\n* A profound connection forms.",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="spiral_wisdom",
                    name="Spiral Wisdom",
                    duration=5.0,
                    pattern_type="spiral",
                    bullet_count=24,
                    bullet_speed=100,
                    attack_dialogue="* \"Let me show you the beauty of rotation...\"",
                ),
            ],
            xp_reward=15,
            gold_reward=10,
        ),
    }


def create_3d_enemies() -> Dict[str, CombatEnemy]:
    """Create 3D dimensional enemies."""
    return {
        "cube_guard": CombatEnemy(
            id="cube_guard",
            name="Cube Guard",
            stats=CombatStats(hp=45, max_hp=45, attack=10, defense=12),
            personality=EnemyPersonality.PROUD,
            dimension="3d",
            color=(150, 200, 255),
            encounter_text="* Cube Guard materializes in three dimensions!",
            check_text="* CUBE GUARD - ATK 10 DEF 12\n* 6 faces, 12 edges, 8 vertices.\n* Takes its job very seriously.",
            idle_dialogues=[
                "* Cube Guard stands at attention.",
                "* \"All six faces accounted for!\"",
                "* Cube Guard rotates to show all sides.",
            ],
            spare_dialogue="* Cube Guard salutes and rolls away.",
            act_options=[
                ACTOption(id="check", name="Check", description="Examine the enemy."),
                ACTOption(
                    id="salute",
                    name="Salute",
                    description="Give a formal salute.",
                    mood_change=40,
                    success_dialogue="* You salute respectfully.\n* Cube Guard returns the gesture!",
                ),
                ACTOption(
                    id="inspect",
                    name="Inspect",
                    description="Perform a formal inspection.",
                    mood_change=45,
                    success_dialogue="* \"Excellent form, soldier.\"\n* Cube Guard swells with pride!",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="face_assault",
                    name="Face Assault",
                    duration=4.0,
                    pattern_type="cube_faces",
                    bullet_count=6,
                    bullet_speed=180,
                ),
            ],
            xp_reward=20,
            gold_reward=15,
        ),
        
        "sphere_wanderer": CombatEnemy(
            id="sphere_wanderer",
            name="Sphere Wanderer",
            stats=CombatStats(hp=40, max_hp=40, attack=8, defense=6),
            personality=EnemyPersonality.LONELY,
            dimension="3d",
            color=(255, 180, 100),
            encounter_text="* Sphere Wanderer rolls towards you, seeking company.",
            check_text="* SPHERE WANDERER - ATK 8 DEF 6\n* Perfect in all directions.\n* Seems to want a friend.",
            idle_dialogues=[
                "* Sphere Wanderer bounces hopefully.",
                "* \"Will you... roll with me?\"",
                "* (It looks lonely.)",
            ],
            spare_dialogue="* Sphere Wanderer bounces away happily with a new friend!",
            act_options=[
                ACTOption(id="check", name="Check", description="Examine the enemy."),
                ACTOption(
                    id="play",
                    name="Play",
                    description="Play catch with them.",
                    mood_change=50,
                    success_dialogue="* You play catch!\n* Sphere Wanderer is overjoyed!",
                ),
                ACTOption(
                    id="befriend",
                    name="Befriend",
                    description="Offer friendship.",
                    mood_change=60,
                    success_dialogue="* You offer to be friends.\n* Sphere Wanderer cries happy tears!",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="bounce_around",
                    name="Bounce Around",
                    duration=4.0,
                    pattern_type="bouncing_spheres",
                    bullet_count=8,
                    bullet_speed=150,
                    attack_dialogue="* \"Play with me!\"",
                ),
            ],
            xp_reward=15,
            gold_reward=12,
            spare_gold_reward=20,
        ),
    }


def create_4d_enemies() -> Dict[str, CombatEnemy]:
    """Create 4D dimensional enemies."""
    return {
        "tesseract_guardian": CombatEnemy(
            id="tesseract_guardian",
            name="Tesseract Guardian",
            stats=CombatStats(hp=80, max_hp=80, attack=15, defense=15),
            personality=EnemyPersonality.GEOMETRIC,
            dimension="4d",
            color=(255, 100, 255),
            is_boss=True,
            encounter_text="* The Tesseract Guardian unfolds before you in impossible angles!",
            check_text="* TESSERACT GUARDIAN - ATK 15 DEF 15\n* 8 cells, 24 faces, 32 edges, 16 vertices.\n* Guards the secrets of hyperspace.",
            idle_dialogues=[
                "* The Guardian rotates through dimensions you can barely perceive.",
                "* \"You see only my shadow...\"",
                "* Reality warps around its form.",
            ],
            hurt_dialogues=[
                "* A corner phases out of existence briefly.",
                "* \"Impossible... you struck my W-axis!\"",
            ],
            low_hp_dialogues=[
                "* The Guardian's form flickers between states.",
                "* \"Perhaps... you are worthy of hyperspace...\"",
            ],
            spare_dialogue="* The Tesseract Guardian acknowledges you as a true 4D being.",
            act_options=[
                ACTOption(id="check", name="Check", description="Examine the enemy."),
                ACTOption(
                    id="perceive",
                    name="Perceive",
                    description="Try to perceive all 4 dimensions.",
                    mood_change=30,
                    success_dialogue="* You strain to see the W-axis.\n* The Guardian notices your effort.",
                ),
                ACTOption(
                    id="rotate_self",
                    name="4D Rotate",
                    description="Rotate yourself in 4D.",
                    mood_change=50,
                    requires_turn=2,
                    success_dialogue="* You rotate through the W-axis!\n* The Guardian is impressed!",
                ),
                ACTOption(
                    id="acknowledge",
                    name="Acknowledge",
                    description="Acknowledge its higher nature.",
                    mood_change=40,
                    success_dialogue="* \"At last... a being who understands.\"\n* The Guardian's hostility fades.",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="hypercube_unfold",
                    name="Hypercube Unfold",
                    duration=5.0,
                    pattern_type="tesseract",
                    bullet_count=16,
                    bullet_speed=200,
                    attack_dialogue="* The Guardian unfolds through reality!",
                ),
                EnemyAttackPattern(
                    id="dimensional_shift",
                    name="Dimensional Shift",
                    duration=4.0,
                    pattern_type="phase_shift",
                    bullet_count=12,
                    bullet_speed=180,
                    soul_mode=SoulMode.BLUE,
                    attack_dialogue="* Gravity shifts in 4D space!",
                ),
                EnemyAttackPattern(
                    id="vertex_storm",
                    name="Vertex Storm",
                    duration=6.0,
                    pattern_type="vertex_burst",
                    bullet_count=32,
                    bullet_speed=220,
                    attack_dialogue="* 16 vertices release energy simultaneously!",
                ),
            ],
            xp_reward=100,
            gold_reward=50,
            spare_gold_reward=100,
            spare_threshold=150,
        ),
    }


# Combined enemy registry
ALL_ENEMIES: Dict[str, CombatEnemy] = {}


def get_all_enemies() -> Dict[str, CombatEnemy]:
    """Get all enemies, creating fresh copies."""
    global ALL_ENEMIES
    if not ALL_ENEMIES:
        ALL_ENEMIES.update(create_1d_enemies())
        ALL_ENEMIES.update(create_2d_enemies())
        ALL_ENEMIES.update(create_3d_enemies())
        ALL_ENEMIES.update(create_4d_enemies())
    
    # Return copies to avoid modifying originals
    import copy
    return {k: copy.deepcopy(v) for k, v in ALL_ENEMIES.items()}


def get_enemy(enemy_id: str) -> Optional[CombatEnemy]:
    """Get a fresh copy of an enemy by ID."""
    enemies = get_all_enemies()
    return enemies.get(enemy_id)


def get_enemies_for_dimension(dimension: str) -> List[CombatEnemy]:
    """Get all enemies for a dimension."""
    enemies = get_all_enemies()
    return [e for e in enemies.values() if e.dimension == dimension]
