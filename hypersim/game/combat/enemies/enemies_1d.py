"""1D Dimension Enemies - The Line.

Enemies that exist in one-dimensional space:
- Point Spirit: Dimensionless awareness
- Line Walker: Confused by width
- Forward Sentinel: Aggressive guardian of forward
- Void Echo: Philosophical being from the backward void
- Toll Collector: Playful gatekeeper
- Segment Guardian: BOSS - Guards passage to 2D
"""
from typing import Dict

from ..core import CombatStats, SoulMode
from .base import (
    CombatEnemy, EnemyPersonality, EnemyMood,
    ACTOption, EnemyAttackPattern, check_act
)


def create_1d_enemies() -> Dict[str, CombatEnemy]:
    """Create all 1D enemies."""
    return {
        **_create_basic_enemies(),
        **_create_advanced_enemies(),
        **_create_boss_enemies(),
    }


def _create_basic_enemies() -> Dict[str, CombatEnemy]:
    """Basic 1D enemies."""
    return {
        "point_spirit": CombatEnemy(
            id="point_spirit",
            name="Point Spirit",
            stats=CombatStats(hp=8, max_hp=8, attack=3, defense=0),
            personality=EnemyPersonality.TIMID,
            dimension="1d",
            color=(255, 255, 200),
            encounter_text="* A tiny Point Spirit appears!\n* It has no dimension at all - just pure existence.",
            check_text="* POINT SPIRIT - ATK 3 DEF 0\n* A consciousness before extension.\n* It remembers being nothing.\n* Fragile but profound.",
            idle_dialogues=[
                "* Point Spirit flickers in and out of perception.",
                "* \"I am... here. Just here.\"",
                "* The Spirit contemplates its own existence.",
                "* \"Before I was, there was only potential.\"",
            ],
            spare_dialogue="* Point Spirit fades peacefully.\n* \"Thank you... for seeing me.\"",
            kill_dialogue="* Point Spirit collapses into true nothing.",
            act_options=[
                check_act(),
                ACTOption(
                    id="acknowledge",
                    name="Acknowledge",
                    description="Simply acknowledge its existence.",
                    mood_change=50,
                    success_dialogue="* You acknowledge the Point Spirit.\n* It glows brighter!\n* \"You... see me? I EXIST!\"",
                ),
                ACTOption(
                    id="contemplate",
                    name="Contemplate",
                    description="Contemplate the nature of points.",
                    mood_change=40,
                    success_dialogue="* You contemplate existence without extension.\n* The Spirit resonates with understanding.",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="existence_pulse",
                    name="Existence Pulse",
                    duration=2.5,
                    pattern_type="point_collapse",  # New dimensional pattern
                    bullet_count=4,
                    bullet_speed=100,
                    base_difficulty=0.6,
                    attack_dialogue="* Point Spirit pulses with pure existence!",
                ),
            ],
            xp_reward=3,
            gold_reward=2,
            spare_gold_reward=8,
            spare_threshold=50,
        ),
        
        "line_walker": CombatEnemy(
            id="line_walker",
            name="Line Walker",
            stats=CombatStats(hp=15, max_hp=15, attack=5, defense=2),
            personality=EnemyPersonality.CONFUSED,
            dimension="1d",
            color=(100, 200, 255),
            encounter_text="* Line Walker blocks your path!\n* It seems confused by your presence.",
            check_text="* LINE WALKER - ATK 5 DEF 2\n* Knows only forward and backward.\n* Has walked this line for eons.\n* Seems confused by your... width?",
            idle_dialogues=[
                "* Line Walker vibrates uncertainly.",
                "* Line Walker looks left and right... wait, it can't.",
                "* \"Where did you come from? There's only forward and back...\"",
                "* Line Walker pulses with confusion.",
            ],
            hurt_dialogues=[
                "* Line Walker contracts in pain.",
                "* \"Ow... that came from... WHERE?\"",
                "* \"You hit me from a direction I can't perceive!\"",
            ],
            low_hp_dialogues=[
                "* Line Walker is barely holding together.",
                "* \"Please... I just want to go forward...\"",
                "* \"Is there really more than the Line?\"",
            ],
            spare_dialogue="* Line Walker extends past you gratefully.\n* \"Maybe... the Line isn't everything.\"",
            kill_dialogue="* Line Walker collapses into a point.\n* The Line feels slightly shorter.",
            act_options=[
                check_act(),
                ACTOption(
                    id="explain",
                    name="Explain",
                    description="Try to explain 2D to them.",
                    mood_change=25,
                    success_dialogue="* You try to explain 'width'.\n* Line Walker is fascinated!\n* \"A direction... perpendicular to forward?!\"",
                ),
                ACTOption(
                    id="step_aside",
                    name="Step Aside",
                    description="Move perpendicular to its path.",
                    mood_change=50,
                    success_dialogue="* You step sideways.\n* Line Walker passes by, amazed.\n* \"You... DISAPPEARED?! And came BACK?!\"",
                ),
                ACTOption(
                    id="point",
                    name="Point Forward",
                    description="Point in its direction of travel.",
                    mood_change=15,
                    success_dialogue="* You point forward.\n* Line Walker feels understood.\n* \"Yes! Forward! You get it!\"",
                ),
                ACTOption(
                    id="walk_together",
                    name="Walk With",
                    description="Walk alongside in its direction.",
                    mood_change=35,
                    success_dialogue="* You walk forward together.\n* Line Walker is overjoyed!\n* \"A companion on the eternal path!\"",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="line_dash",
                    name="Line Dash",
                    duration=3.0,
                    pattern_type="line_sweep",  # 1D pattern
                    bullet_count=5,
                    bullet_speed=200,
                    base_difficulty=0.8,
                    attack_dialogue="* Line Walker charges back and forth!",
                ),
                EnemyAttackPattern(
                    id="ping_pong",
                    name="Ping Pong",
                    duration=4.0,
                    pattern_type="ping_pong",  # New 1D pattern
                    wave_count=3,
                    bullet_speed=150,
                    base_difficulty=0.9,
                    attack_dialogue="* Line Walker bounces with confusion!",
                ),
            ],
            xp_reward=5,
            gold_reward=3,
            spare_gold_reward=5,
            spare_threshold=75,
        ),
    }


def _create_advanced_enemies() -> Dict[str, CombatEnemy]:
    """Advanced 1D enemies."""
    return {
        "forward_sentinel": CombatEnemy(
            id="forward_sentinel",
            name="Forward Sentinel",
            stats=CombatStats(hp=25, max_hp=25, attack=8, defense=6),
            personality=EnemyPersonality.AGGRESSIVE,
            dimension="1d",
            color=(255, 100, 100),
            encounter_text="* Forward Sentinel blocks the path!\n* \"NONE SHALL PASS... BACKWARD!\"",
            check_text="* FORWARD SENTINEL - ATK 8 DEF 6\n* Believes backward is sin.\n* Guards the Forward Path zealously.\n* Has never looked behind.",
            idle_dialogues=[
                "* \"FORWARD! ALWAYS FORWARD!\"",
                "* Forward Sentinel refuses to acknowledge behind.",
                "* \"The past is poison! Only the future matters!\"",
                "* It strains eternally ahead.",
            ],
            hurt_dialogues=[
                "* \"You struck from... NO! I won't look!\"",
                "* Forward Sentinel flinches but doesn't turn.",
            ],
            spare_dialogue="* Forward Sentinel steps aside.\n* \"Perhaps... some paths fork.\"",
            kill_dialogue="* Forward Sentinel falls... forward.",
            act_options=[
                check_act(),
                ACTOption(
                    id="praise_forward",
                    name="Praise Forward",
                    description="Praise the virtue of moving forward.",
                    mood_change=30,
                    success_dialogue="* You praise the forward direction.\n* \"YES! You understand! FORWARD!\"",
                ),
                ACTOption(
                    id="show_sideways",
                    name="Show Sideways",
                    description="Demonstrate sideways movement.",
                    mood_change=40,
                    success_dialogue="* You move sideways.\n* \"That's not... backward? A NEW forward?!\"",
                ),
                ACTOption(
                    id="discuss_time",
                    name="Discuss Time",
                    description="Discuss how time only moves forward.",
                    mood_change=35,
                    success_dialogue="* You mention time's forward flow.\n* \"Even in your dimensions... forward is sacred!\"",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="forward_charge",
                    name="Forward Charge",
                    duration=3.5,
                    pattern_type="segment_wave",  # 1D pattern
                    bullet_count=8,
                    bullet_speed=280,
                    base_difficulty=1.1,
                    attack_dialogue="* \"FORWARD MEANS THROUGH YOU!\"",
                ),
                EnemyAttackPattern(
                    id="guardian_rush",
                    name="Guardian Rush",
                    duration=4.0,
                    pattern_type="guardian_barrage",  # Boss-like attack
                    bullet_count=10,
                    bullet_speed=250,
                    base_difficulty=1.2,
                    attack_dialogue="* \"NONE SHALL PASS BACKWARD!\"",
                ),
                EnemyAttackPattern(
                    id="sentinel_split",
                    name="Sentinel Split",
                    duration=4.5,
                    pattern_type="sentinel_multiply",  # New: splits into two points
                    bullet_count=12,
                    bullet_speed=200,
                    base_difficulty=1.3,
                    attack_dialogue="* \"I AM NOT ALONE IN MY CONVICTION!\"",
                ),
                EnemyAttackPattern(
                    id="line_formation",
                    name="Line Formation",
                    duration=5.0,
                    pattern_type="force_line",  # New: forms a line, constrains player
                    bullet_count=15,
                    bullet_speed=180,
                    base_difficulty=1.4,
                    attack_dialogue="* \"YOU WILL WALK MY PATH!\"",
                ),
            ],
            xp_reward=12,
            gold_reward=8,
            spare_threshold=100,
        ),
        
        "void_echo": CombatEnemy(
            id="void_echo",
            name="Void Echo",
            stats=CombatStats(hp=20, max_hp=20, attack=7, defense=3),
            personality=EnemyPersonality.PHILOSOPHICAL,
            dimension="1d",
            color=(80, 80, 120),
            encounter_text="* Something resonates from the Backward Void...\n* Void Echo manifests from nothingness!",
            check_text="* VOID ECHO - ATK 7 DEF 3\n* An echo of what came before.\n* Remembers the time before the Line.\n* Speaks in riddles and paradoxes.",
            idle_dialogues=[
                "* \"Before forward... was there backward?\"",
                "* \"I am the memory of nothing.\"",
                "* Void Echo phases in and out.",
                "* \"What exists behind the origin?\"",
            ],
            spare_dialogue="* Void Echo fades back into the void.\n* \"Perhaps nothing... is something after all.\"",
            kill_dialogue="* Void Echo dissipates into true silence.",
            act_options=[
                check_act(),
                ACTOption(
                    id="philosophize",
                    name="Philosophize",
                    description="Discuss the nature of nothingness.",
                    mood_change=45,
                    success_dialogue="* You discuss void and existence.\n* \"You understand! Nothing is the canvas!\"",
                ),
                ACTOption(
                    id="listen",
                    name="Listen",
                    description="Simply listen to its echoes.",
                    mood_change=35,
                    success_dialogue="* You listen to the void's whispers.\n* The Echo feels heard for the first time.",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="void_pulse",
                    name="Void Pulse",
                    duration=4.0,
                    pattern_type="void_pulse",  # New 1D pattern
                    bullet_count=6,
                    bullet_speed=120,
                    base_difficulty=1.0,
                    attack_dialogue="* Reality inverts around the Echo!",
                ),
                EnemyAttackPattern(
                    id="echo_spiral",
                    name="Echo Spiral",
                    duration=3.5,
                    pattern_type="echo_spiral",  # New 1D pattern
                    bullet_count=8,
                    bullet_speed=100,
                    base_difficulty=0.9,
                    attack_dialogue="* The void echoes with strange patterns!",
                ),
            ],
            xp_reward=10,
            gold_reward=5,
            spare_gold_reward=15,
            spare_threshold=80,
        ),
        
        "toll_collector": CombatEnemy(
            id="toll_collector",
            name="Toll Collector",
            stats=CombatStats(hp=18, max_hp=18, attack=6, defense=4),
            personality=EnemyPersonality.PLAYFUL,
            dimension="1d",
            color=(200, 180, 100),
            encounter_text="* Toll Collector blocks the Midpoint Station!\n* \"Toll for passage! One riddle or one fight!\"",
            check_text="* TOLL COLLECTOR - ATK 6 DEF 4\n* Collects tolls at the Midpoint.\n* Prefers riddles to violence.\n* Has heard every excuse.",
            idle_dialogues=[
                "* \"Everyone pays eventually~\"",
                "* Toll Collector jangles invisible coins.",
                "* \"Riddle? Fight? Or... other payment?\"",
            ],
            spare_dialogue="* Toll Collector lets you pass.\n* \"Pleasure doing business~\"",
            kill_dialogue="* Toll Collector's coins scatter into the void.",
            act_options=[
                check_act(),
                ACTOption(
                    id="pay_toll",
                    name="Pay Toll",
                    description="Offer payment (lose 10G).",
                    mood_change=100,  # Instant spare
                    success_dialogue="* You pay the toll.\n* \"Exact change! My favorite customer!\"",
                ),
                ACTOption(
                    id="riddle",
                    name="Answer Riddle",
                    description="Attempt to answer a riddle.",
                    mood_change=50,
                    success_dialogue="* \"What has one direction but two ways?\"\n* \"...A line segment!\" you answer.\n* \"Correct! Pass freely!\"",
                ),
                ACTOption(
                    id="bargain",
                    name="Bargain",
                    description="Try to haggle.",
                    mood_change=25,
                    success_dialogue="* You haggle the price down.\n* \"Ugh, fine. Half-toll for the clever one.\"",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="coin_barrage",
                    name="Coin Barrage",
                    duration=3.0,
                    pattern_type="converging_points",  # 1D pattern
                    bullet_count=8,
                    bullet_speed=180,
                    base_difficulty=0.8,
                    attack_dialogue="* \"Payment in PAIN then!\"",
                ),
            ],
            xp_reward=8,
            gold_reward=15,
            spare_threshold=50,
        ),
    }


def _create_boss_enemies() -> Dict[str, CombatEnemy]:
    """Boss enemies for 1D."""
    return {
        "segment_guardian": CombatEnemy(
            id="segment_guardian",
            name="Segment Guardian",
            stats=CombatStats(hp=40, max_hp=40, attack=12, defense=8),
            personality=EnemyPersonality.PROUD,
            dimension="1d",
            color=(255, 200, 100),
            is_boss=True,
            encounter_text="* The Segment Guardian bars the way to 2D!\n* \"Only the worthy may perceive WIDTH!\"",
            check_text="* SEGMENT GUARDIAN - ATK 12 DEF 8\n* Guardian of the Endpoint.\n* Proud of its clearly defined endpoints.\n* Has protected this boundary for eons.",
            idle_dialogues=[
                "* Segment Guardian measures you carefully.",
                "* \"My length is EXACTLY optimal.\"",
                "* Segment Guardian flexes its endpoints.",
                "* \"Many have sought to pass. Few have earned it.\"",
            ],
            hurt_dialogues=[
                "* \"A strong strike! But strength alone won't open 2D!\"",
                "* One endpoint flickers but holds.",
            ],
            low_hp_dialogues=[
                "* \"You are... worthy. But prove your understanding!\"",
                "* The Guardian's form wavers at the boundary.",
            ],
            spare_dialogue="* Segment Guardian extends to let you pass.\n* \"Go forth, and learn what WIDTH truly means.\"\n* The way to 2D opens before you!",
            kill_dialogue="* The Segment Guardian collapses.\n* The boundary weakens... but at what cost?",
            act_options=[
                check_act(),
                ACTOption(
                    id="compliment",
                    name="Compliment",
                    description="Praise its well-defined endpoints.",
                    mood_change=25,
                    success_dialogue="* You compliment its precise boundaries.\n* \"Ah, one who appreciates DEFINITION!\"",
                ),
                ACTOption(
                    id="measure",
                    name="Measure",
                    description="Respectfully measure its length.",
                    mood_change=30,
                    success_dialogue="* You measure carefully and nod approvingly.\n* \"Precise measurement! The foundation of geometry!\"",
                ),
                ACTOption(
                    id="discuss_2d",
                    name="Discuss 2D",
                    description="Discuss what lies beyond.",
                    mood_change=35,
                    success_dialogue="* You speak of planes and width.\n* \"You know of what I guard! Good!\"",
                ),
                ACTOption(
                    id="prove_worthy",
                    name="Prove Worthy",
                    description="Demonstrate understanding of dimensions.",
                    mood_change=50,
                    requires_turn=2,
                    success_dialogue="* You demonstrate dimensional awareness!\n* \"YES! You SEE beyond the line!\"\n* \"You may pass!\"",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="endpoint_thrust",
                    name="Endpoint Thrust",
                    duration=3.5,
                    pattern_type="segment_wave",  # 1D boss pattern
                    bullet_speed=250,
                    base_difficulty=1.2,
                    attack_dialogue="* The Guardian strikes with both endpoints!",
                ),
                EnemyAttackPattern(
                    id="boundary_sweep",
                    name="Boundary Sweep",
                    duration=4.0,
                    pattern_type="guardian_barrage",  # Boss pattern with gaps
                    bullet_count=12,
                    bullet_speed=220,
                    base_difficulty=1.3,
                    attack_dialogue="* \"The boundary shall test you!\"",
                ),
                EnemyAttackPattern(
                    id="dimensional_seal",
                    name="Dimensional Seal",
                    duration=5.0,
                    pattern_type="point_collapse",  # Collapse then expand
                    bullet_count=16,
                    bullet_speed=180,
                    base_difficulty=1.5,
                    attack_dialogue="* \"Feel the weight of dimensional transition!\"",
                ),
                EnemyAttackPattern(
                    id="final_judgment",
                    name="Final Judgment",
                    duration=6.0,
                    pattern_type="guardian_barrage",  # Intense final attack
                    bullet_count=20,
                    bullet_speed=200,
                    base_difficulty=1.8,
                    attack_dialogue="* \"PROVE YOUR WORTH TO ENTER THE SECOND DIMENSION!\"",
                ),
            ],
            xp_reward=30,
            gold_reward=20,
            spare_gold_reward=40,
            spare_threshold=120,
            can_flee=False,
        ),
    }


# Pre-built enemy dict for quick access
ENEMIES_1D = create_1d_enemies()
