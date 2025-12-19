"""2D Dimension Enemies - The Plane.

Enemies that exist in two-dimensional space:
- Triangle Scout: Aggressive polygon
- Square Citizen: Timid tessellator
- Circle Mystic: Philosophical curve
- Fractal Entity: Infinitely complex
- Membrane Warper: BOSS - Guards passage to 3D
"""
from typing import Dict

from ..core import CombatStats, SoulMode
from .base import (
    CombatEnemy, EnemyPersonality, EnemyMood,
    ACTOption, EnemyAttackPattern, check_act
)


def create_2d_enemies() -> Dict[str, CombatEnemy]:
    """Create all 2D enemies."""
    return {
        **_create_basic_enemies(),
        **_create_advanced_enemies(),
        **_create_boss_enemies(),
    }


def _create_basic_enemies() -> Dict[str, CombatEnemy]:
    """Basic 2D enemies."""
    return {
        "triangle_scout": CombatEnemy(
            id="triangle_scout",
            name="Triangle Scout",
            stats=CombatStats(hp=20, max_hp=20, attack=7, defense=3),
            personality=EnemyPersonality.AGGRESSIVE,
            dimension="2d",
            color=(255, 100, 100),
            encounter_text="* Triangle Scout points at you threateningly!\n* Its vertices gleam with hostile intent.",
            check_text="* TRIANGLE SCOUT - ATK 7 DEF 3\n* The simplest polygon. Three sides, three angles.\n* Very pointy. Very aggressive.\n* Believes triangles are the superior shape.",
            idle_dialogues=[
                "* Triangle Scout rotates menacingly.",
                "* \"THREE SIDES! THREE CORNERS! PERFECT!\"",
                "* Triangle Scout's vertices gleam.",
                "* \"Circles are just LAZY triangles!\"",
            ],
            hurt_dialogues=[
                "* One of Triangle Scout's corners chips.",
                "* \"MY ANGLES! You'll pay for that!\"",
            ],
            spare_dialogue="* Triangle Scout rolls away, satisfied.\n* \"Maybe you're not so bad... for a non-triangle.\"",
            kill_dialogue="* Triangle Scout shatters into three lines.",
            act_options=[
                check_act(),
                ACTOption(
                    id="discuss_angles",
                    name="Angles",
                    description="Discuss interior angles.",
                    mood_change=30,
                    success_dialogue="* You discuss the beauty of 60° angles.\n* Triangle Scout nods rapidly!\n* \"180° total! Perfection!\"",
                ),
                ACTOption(
                    id="admire_vertices",
                    name="Admire",
                    description="Admire its sharp vertices.",
                    mood_change=35,
                    success_dialogue="* You comment on its sharp vertices.\n* Triangle Scout puffs with pride!",
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
                    attack_dialogue="* Triangle Scout spins its vertices at you!",
                ),
                EnemyAttackPattern(
                    id="corner_shot",
                    name="Corner Shot",
                    duration=3.0,
                    pattern_type="aimed_triangles",
                    bullet_count=9,
                    bullet_speed=220,
                    attack_dialogue="* \"Take THIS!\"",
                ),
            ],
            xp_reward=10,
            gold_reward=8,
            spare_threshold=80,
        ),
        
        "square_citizen": CombatEnemy(
            id="square_citizen",
            name="Square Citizen",
            stats=CombatStats(hp=30, max_hp=30, attack=6, defense=8),
            personality=EnemyPersonality.TIMID,
            dimension="2d",
            color=(100, 150, 255),
            encounter_text="* Square Citizen nervously approaches!\n* It seems reluctant to fight.",
            check_text="* SQUARE CITIZEN - ATK 6 DEF 8\n* A law-abiding rectangle (technically).\n* Seems uncomfortable with conflict.\n* Just wants to tile peacefully.",
            idle_dialogues=[
                "* Square Citizen adjusts its right angles.",
                "* \"I-I'm just trying to tile peacefully...\"",
                "* Square Citizen looks for an exit.",
                "* \"Why can't everyone just tessellate?\"",
            ],
            hurt_dialogues=[
                "* \"Please! I have a family of rectangles!\"",
                "* Square Citizen's corners droop sadly.",
            ],
            spare_dialogue="* Square Citizen tiles away in relief.\n* \"Thank you for understanding!\"",
            kill_dialogue="* Square Citizen crumbles into four lines.",
            act_options=[
                check_act(),
                ACTOption(
                    id="reassure",
                    name="Reassure",
                    description="Tell them everything's okay.",
                    mood_change=40,
                    success_dialogue="* You speak calmly.\n* Square Citizen relaxes slightly.\n* \"R-really? You're not going to rotate me?\"",
                ),
                ACTOption(
                    id="compliment_angles",
                    name="Right Angles",
                    description="Compliment their perfect right angles.",
                    mood_change=35,
                    success_dialogue="* \"R-really? You think they're nice?\"\n* Square Citizen blushes somehow.\n* \"90 degrees is so... reliable.\"",
                ),
                ACTOption(
                    id="discuss_tiling",
                    name="Tiling",
                    description="Discuss the art of tessellation.",
                    mood_change=45,
                    success_dialogue="* You discuss tessellation patterns.\n* \"Oh! You understand the beauty of perfect fit!\"",
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
                    attack_dialogue="* Square Citizen panics and tiles everywhere!",
                ),
            ],
            xp_reward=8,
            gold_reward=12,
            spare_gold_reward=10,
            spare_threshold=80,
        ),
    }


def _create_advanced_enemies() -> Dict[str, CombatEnemy]:
    """Advanced 2D enemies."""
    return {
        "circle_mystic": CombatEnemy(
            id="circle_mystic",
            name="Circle Mystic",
            stats=CombatStats(hp=35, max_hp=35, attack=9, defense=4),
            personality=EnemyPersonality.PHILOSOPHICAL,
            dimension="2d",
            color=(200, 100, 255),
            encounter_text="* Circle Mystic rolls into view, contemplating infinity.\n* \"Ah... another point on the cosmic circumference.\"",
            check_text="* CIRCLE MYSTIC - ATK 9 DEF 4\n* Has infinite sides, or zero?\n* Ponders the nature of π.\n* Considers all polygons to be incomplete circles.",
            idle_dialogues=[
                "* \"Is my circumference truly endless?\"",
                "* Circle Mystic contemplates its center.",
                "* \"We are all just points rotating around meaning...\"",
                "* \"π never ends. Neither does existence.\"",
            ],
            spare_dialogue="* Circle Mystic rolls away, at peace.\n* \"May your radius extend forever.\"",
            kill_dialogue="* Circle Mystic's circumference unwinds into nothing.",
            act_options=[
                check_act(),
                ACTOption(
                    id="discuss_pi",
                    name="Discuss π",
                    description="Engage in mathematical philosophy.",
                    mood_change=45,
                    success_dialogue="* You discuss the transcendence of π.\n* \"Yes! An irrational truth! Infinite precision!\"\n* Circle Mystic is deeply moved!",
                ),
                ACTOption(
                    id="meditate",
                    name="Meditate",
                    description="Meditate on circular nature.",
                    mood_change=50,
                    success_dialogue="* You both contemplate infinity.\n* A profound connection forms.\n* \"You understand the endless cycle.\"",
                ),
                ACTOption(
                    id="roll_together",
                    name="Roll",
                    description="Roll alongside the Circle.",
                    mood_change=35,
                    success_dialogue="* You roll in harmony.\n* \"The path curves, but never ends!\"",
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
                EnemyAttackPattern(
                    id="infinite_loop",
                    name="Infinite Loop",
                    duration=4.0,
                    pattern_type="pulse",
                    bullet_count=12,
                    bullet_speed=140,
                    attack_dialogue="* \"Round and round, forever...\"",
                ),
            ],
            xp_reward=15,
            gold_reward=10,
            spare_threshold=100,
        ),
        
        "fractal_entity": CombatEnemy(
            id="fractal_entity",
            name="Fractal Entity",
            stats=CombatStats(hp=45, max_hp=45, attack=11, defense=5),
            personality=EnemyPersonality.GEOMETRIC,
            dimension="2d",
            color=(100, 255, 200),
            encounter_text="* A shape within shapes within shapes appears!\n* Fractal Entity unfolds infinitely!",
            check_text="* FRACTAL ENTITY - ATK 11 DEF 5\n* Infinite complexity in finite space.\n* Contains copies of itself at every scale.\n* Its true form cannot be fully perceived.",
            idle_dialogues=[
                "* The Entity reveals another layer of detail.",
                "* \"Zoom in. I am still here. Zoom more. Still here.\"",
                "* Patterns repeat within patterns.",
                "* \"I am the coastline that never measures true.\"",
            ],
            spare_dialogue="* Fractal Entity recedes into infinite detail.\n* \"We will meet again... at every scale.\"",
            kill_dialogue="* Fractal Entity simplifies into mundane geometry.",
            act_options=[
                check_act(),
                ACTOption(
                    id="zoom_in",
                    name="Zoom In",
                    description="Focus on smaller details.",
                    mood_change=30,
                    success_dialogue="* You peer closer.\n* \"Ah, you see my children! And their children!\"",
                ),
                ACTOption(
                    id="zoom_out",
                    name="Zoom Out",
                    description="See the larger pattern.",
                    mood_change=30,
                    success_dialogue="* You step back.\n* \"Yes! The great pattern! I am but a piece!\"",
                ),
                ACTOption(
                    id="appreciate_recursion",
                    name="Recursion",
                    description="Appreciate the recursive nature.",
                    mood_change=50,
                    success_dialogue="* You speak of self-similarity.\n* \"FINALLY! One who UNDERSTANDS!\"\n* The Entity glows with joy.",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="recursive_burst",
                    name="Recursive Burst",
                    duration=4.5,
                    pattern_type="pulse",
                    bullet_count=32,
                    bullet_speed=130,
                    attack_dialogue="* \"Each piece contains the whole!\"",
                ),
            ],
            xp_reward=20,
            gold_reward=15,
            spare_threshold=90,
        ),
    }


def _create_boss_enemies() -> Dict[str, CombatEnemy]:
    """Boss enemies for 2D."""
    return {
        "membrane_warper": CombatEnemy(
            id="membrane_warper",
            name="Membrane Warper",
            stats=CombatStats(hp=60, max_hp=60, attack=13, defense=10),
            personality=EnemyPersonality.PHILOSOPHICAL,
            dimension="2d",
            color=(180, 150, 255),
            is_boss=True,
            encounter_text="* The Dimensional Membrane bulges!\n* Membrane Warper emerges, half in 2D, half... elsewhere!",
            check_text="* MEMBRANE WARPER - ATK 13 DEF 10\n* Guardian of the 2D/3D boundary.\n* Exists partially in both dimensions.\n* Can bend the plane itself.",
            idle_dialogues=[
                "* Reality ripples around the Warper.",
                "* \"Do you feel it? The thickness pressing in?\"",
                "* \"I remember when I was flat. Before I saw... depth.\"",
                "* The Warper's form bulges impossibly.",
            ],
            hurt_dialogues=[
                "* Part of the Warper phases into 3D briefly.",
                "* \"You strike at what you cannot see!\"",
            ],
            low_hp_dialogues=[
                "* \"You have... potential. For depth.\"",
                "* The membrane between dimensions thins.",
            ],
            spare_dialogue="* Membrane Warper parts the dimensional veil.\n* \"Go. Learn what DEPTH truly means.\"\n* The way to 3D opens!",
            kill_dialogue="* Membrane Warper flattens completely.\n* The boundary tears open violently.",
            act_options=[
                check_act(),
                ACTOption(
                    id="perceive_depth",
                    name="Perceive Depth",
                    description="Try to perceive the third dimension.",
                    mood_change=35,
                    success_dialogue="* You strain to see... THICKNESS.\n* \"Yes! You feel it! The Z-axis!\"",
                ),
                ACTOption(
                    id="discuss_flatland",
                    name="Discuss Flatland",
                    description="Discuss the limits of 2D perception.",
                    mood_change=40,
                    success_dialogue="* You speak of dimensional blindness.\n* \"You understand our limitation!\"",
                ),
                ACTOption(
                    id="embrace_expansion",
                    name="Embrace",
                    description="Embrace the coming expansion.",
                    mood_change=50,
                    requires_turn=2,
                    success_dialogue="* You open yourself to new perception.\n* \"YES! You are ready to see MORE!\"",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="dimension_warp",
                    name="Dimension Warp",
                    duration=4.0,
                    pattern_type="tesseract",
                    bullet_count=16,
                    bullet_speed=160,
                    attack_dialogue="* Reality BENDS around the Warper!",
                ),
                EnemyAttackPattern(
                    id="depth_crush",
                    name="Depth Crush",
                    duration=5.0,
                    pattern_type="pulse",
                    bullet_count=20,
                    bullet_speed=180,
                    soul_mode=SoulMode.BLUE,
                    attack_dialogue="* \"Feel the WEIGHT of the third dimension!\"",
                ),
            ],
            xp_reward=40,
            gold_reward=30,
            spare_gold_reward=50,
            spare_threshold=130,
            can_flee=False,
        ),
    }


# Pre-built enemy dict for quick access
ENEMIES_2D = create_2d_enemies()
