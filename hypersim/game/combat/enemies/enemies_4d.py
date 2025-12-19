"""4D Dimension Enemies - Hyperspace.

Enemies that exist in four-dimensional space:
- Tesseract Guardian: BOSS - Guards entry to hyperspace
- Hypersphere Wanderer: Lonely 4D sphere
- Memory Specter: Echo from W- depths
- Threshold Guardian: FINAL BOSS - Guards transcendence
"""
from typing import Dict

from ..core import CombatStats, SoulMode
from .base import (
    CombatEnemy, EnemyPersonality, EnemyMood,
    ACTOption, EnemyAttackPattern, check_act
)


def create_4d_enemies() -> Dict[str, CombatEnemy]:
    """Create all 4D enemies."""
    return {
        **_create_basic_enemies(),
        **_create_boss_enemies(),
    }


def _create_basic_enemies() -> Dict[str, CombatEnemy]:
    """Basic 4D enemies."""
    return {
        "hypersphere_wanderer": CombatEnemy(
            id="hypersphere_wanderer",
            name="Hypersphere Wanderer",
            stats=CombatStats(hp=60, max_hp=60, attack=12, defense=8),
            personality=EnemyPersonality.LONELY,
            dimension="4d",
            color=(255, 200, 150),
            encounter_text="* A sphere passes THROUGH space!\n* Hypersphere Wanderer emerges from impossible direction!",
            check_text="* HYPERSPHERE WANDERER - ATK 12 DEF 8\n* A 4D sphere - infinite in every direction.\n* Crosses through 3D as a growing/shrinking sphere.\n* Wanders the lonely corridors of hyperspace.",
            idle_dialogues=[
                "* The Wanderer's 3D cross-section expands and contracts.",
                "* \"In 4D, even touching is complicated.\"",
                "* \"I pass through your space... but never IN it.\"",
                "* \"Everything is 'nearby' in hyperspace. Yet so far.\"",
            ],
            hurt_dialogues=[
                "* Part of the Wanderer phases out of perception.",
                "* \"You... reached me? In W-space?\"",
            ],
            spare_dialogue="* Hypersphere Wanderer recedes into W-space.\n* \"Perhaps in higher dimensions... we'll meet again.\"",
            kill_dialogue="* Hypersphere Wanderer collapses into a 3D sphere, then a circle, then a point.",
            act_options=[
                check_act(),
                ACTOption(
                    id="reach_through",
                    name="Reach Through",
                    description="Try to reach into the W direction.",
                    mood_change=50,
                    success_dialogue="* You extend in a direction you can barely perceive.\n* \"You... touched me! Truly touched me!\"",
                ),
                ACTOption(
                    id="share_loneliness",
                    name="Share",
                    description="Share in the loneliness of dimensions.",
                    mood_change=45,
                    success_dialogue="* You speak of dimensional isolation.\n* \"You understand... we're all alone in our perceptions.\"",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="cross_section",
                    name="Cross Section",
                    duration=4.0,
                    pattern_type="pulse",
                    bullet_count=16,
                    bullet_speed=160,
                    attack_dialogue="* The Wanderer passes through 3D space!",
                ),
            ],
            xp_reward=40,
            gold_reward=30,
            spare_threshold=100,
        ),
        
        "memory_specter": CombatEnemy(
            id="memory_specter",
            name="Memory Specter",
            stats=CombatStats(hp=50, max_hp=50, attack=15, defense=5),
            personality=EnemyPersonality.PHILOSOPHICAL,
            dimension="4d",
            color=(100, 100, 150),
            encounter_text="* A figure from your past appears!\n* Memory Specter wears a familiar face...",
            check_text="* MEMORY SPECTER - ATK 15 DEF 5\n* An echo from the W- depths.\n* Takes the form of forgotten things.\n* Speaks truths you'd rather not hear.",
            idle_dialogues=[
                "* \"Do you remember? I do. I remember everything.\"",
                "* The Specter shifts between faces.",
                "* \"The past doesn't die in 4D. It waits.\"",
                "* \"You left so many things behind...\"",
            ],
            hurt_dialogues=[
                "* The memory wavers but doesn't fade.",
                "* \"You cannot destroy what has already happened.\"",
            ],
            spare_dialogue="* Memory Specter fades into the past.\n* \"Remember... but don't be trapped.\"",
            kill_dialogue="* Memory Specter is forgotten. Was it ever real?",
            act_options=[
                check_act(),
                ACTOption(
                    id="acknowledge_past",
                    name="Acknowledge",
                    description="Acknowledge the memories.",
                    mood_change=45,
                    success_dialogue="* You face the memories directly.\n* \"You accept what was... good.\"",
                ),
                ACTOption(
                    id="let_go",
                    name="Let Go",
                    description="Choose to let go of the past.",
                    mood_change=50,
                    success_dialogue="* You release your grip on what was.\n* \"Freedom... true dimensional freedom.\"",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="past_echoes",
                    name="Past Echoes",
                    duration=4.5,
                    pattern_type="spiral",
                    bullet_count=20,
                    bullet_speed=140,
                    attack_dialogue="* \"Remember THIS?!\"",
                ),
            ],
            xp_reward=35,
            gold_reward=20,
            spare_threshold=95,
        ),
        
        "tesseract_citizen": CombatEnemy(
            id="tesseract_citizen",
            name="Tesseract Citizen",
            stats=CombatStats(hp=55, max_hp=55, attack=11, defense=9),
            personality=EnemyPersonality.GEOMETRIC,
            dimension="4d",
            color=(200, 150, 255),
            encounter_text="* A shape of impossible angles approaches!\n* Tesseract Citizen rotates through dimensions!",
            check_text="* TESSERACT CITIZEN - ATK 11 DEF 9\n* An ordinary resident of hyperspace.\n* Finds 3D beings quaint.\n* Can see inside closed 3D objects.",
            idle_dialogues=[
                "* The Citizen rotates, revealing more faces than should exist.",
                "* \"Your insides are showing, you know.\"",
                "* \"Why do you only have three directions?\"",
                "* It examines you from angles you can't perceive.",
            ],
            spare_dialogue="* Tesseract Citizen phases away.\n* \"Come back when you've grown more sides.\"",
            kill_dialogue="* Tesseract Citizen unfolds into eight cubes, then 24 squares.",
            act_options=[
                check_act(),
                ACTOption(
                    id="ask_about_4d",
                    name="Ask About 4D",
                    description="Ask what 4D is like.",
                    mood_change=35,
                    success_dialogue="* \"Imagine a direction you can't point in.\"\n* \"Now move that way. Simple!\"",
                ),
                ACTOption(
                    id="show_respect",
                    name="Show Respect",
                    description="Acknowledge your lower dimensionality.",
                    mood_change=45,
                    success_dialogue="* You admit you can't fully perceive them.\n* \"Finally! Humility! So rare in 3D beings.\"",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="hypercube_spin",
                    name="Hypercube Spin",
                    duration=4.0,
                    pattern_type="tesseract",
                    bullet_count=12,
                    bullet_speed=170,
                    attack_dialogue="* The Citizen rotates through W!",
                ),
            ],
            xp_reward=30,
            gold_reward=25,
            spare_threshold=90,
        ),
    }


def _create_boss_enemies() -> Dict[str, CombatEnemy]:
    """Boss enemies for 4D."""
    return {
        "tesseract_guardian": CombatEnemy(
            id="tesseract_guardian",
            name="Tesseract Guardian",
            stats=CombatStats(hp=100, max_hp=100, attack=18, defense=15),
            personality=EnemyPersonality.GEOMETRIC,
            dimension="4d",
            color=(255, 100, 255),
            is_boss=True,
            encounter_text="* The Tesseract Guardian unfolds before you!\n* Impossible angles connect impossible faces!",
            check_text="* TESSERACT GUARDIAN - ATK 18 DEF 15\n* 8 cells, 24 faces, 32 edges, 16 vertices.\n* Guards the secrets of hyperspace.\n* Can see inside everything you consider 'closed'.",
            idle_dialogues=[
                "* The Guardian rotates through dimensions you can barely perceive.",
                "* \"You see only my shadow...\"",
                "* Reality warps around its form.",
                "* \"In 4D, there are no secrets. No 'inside'. Only existence.\"",
            ],
            hurt_dialogues=[
                "* A corner phases out of existence briefly.",
                "* \"Impossible... you struck my W-axis!\"",
            ],
            low_hp_dialogues=[
                "* The Guardian's form flickers between states.",
                "* \"Perhaps... you ARE worthy of hyperspace...\"",
            ],
            spare_dialogue="* The Tesseract Guardian acknowledges you.\n* \"You have earned the right to perceive.\"\n* Hyperspace unfolds before you!",
            kill_dialogue="* The Guardian collapses into 3D.\n* Something essential is lost forever.",
            act_options=[
                check_act(),
                ACTOption(
                    id="perceive",
                    name="Perceive",
                    description="Try to perceive all 4 dimensions.",
                    mood_change=30,
                    success_dialogue="* You strain to see the W-axis.\n* \"Ah! You TRY! Most cannot even imagine!\"",
                ),
                ACTOption(
                    id="rotate_self",
                    name="4D Rotate",
                    description="Rotate yourself in 4D.",
                    mood_change=50,
                    requires_turn=2,
                    success_dialogue="* You rotate through the W-axis!\n* \"IMPOSSIBLE! You... you SEE!\"\n* The Guardian is deeply impressed!",
                ),
                ACTOption(
                    id="acknowledge",
                    name="Acknowledge",
                    description="Acknowledge its higher nature.",
                    mood_change=40,
                    success_dialogue="* \"At last... a being who understands.\"\n* The Guardian's hostility fades.",
                ),
                ACTOption(
                    id="discuss_transcendence",
                    name="Transcendence",
                    description="Discuss dimensional transcendence.",
                    mood_change=45,
                    success_dialogue="* You speak of ascending beyond 4D.\n* \"Yes... even we are shadows of something greater.\"",
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
            can_flee=False,
        ),
        
        "threshold_guardian": CombatEnemy(
            id="threshold_guardian",
            name="Threshold Guardian",
            stats=CombatStats(hp=150, max_hp=150, attack=25, defense=20),
            personality=EnemyPersonality.GEOMETRIC,
            dimension="4d",
            color=(255, 255, 255),
            is_boss=True,
            encounter_text="* At the edge of 4D, something watches!\n* The Threshold Guardian bars the way to the Beyond!",
            check_text="* THRESHOLD GUARDIAN - ATK 25 DEF 20\n* The final guardian before transcendence.\n* Its form cannot be described in any language.\n* Has watched dimensions fold and unfold since the beginning.",
            idle_dialogues=[
                "* \"Beyond me lies... beyond.\"",
                "* The Guardian's form hurts to perceive.",
                "* \"Are you ready to stop being what you are?\"",
                "* \"Transcendence is not achievement. It is dissolution.\"",
            ],
            hurt_dialogues=[
                "* Something shifts in directions you cannot name.",
                "* \"You wound what cannot be wounded.\"",
            ],
            low_hp_dialogues=[
                "* \"You have earned... consideration.\"",
                "* The threshold flickers. Something waits beyond.",
            ],
            spare_dialogue="* The Threshold Guardian steps aside.\n* \"Go then. Become something we cannot follow.\"\n* The threshold opens. Beyond lies...",
            kill_dialogue="* The Threshold Guardian falls.\n* The barrier shatters. Reality screams.",
            act_options=[
                check_act(),
                ACTOption(
                    id="prove_understanding",
                    name="Prove",
                    description="Demonstrate understanding of all dimensions.",
                    mood_change=40,
                    success_dialogue="* You recite the truth of each dimension.\n* \"You have learned. But learning is not being.\"",
                ),
                ACTOption(
                    id="accept_dissolution",
                    name="Accept",
                    description="Accept that transcendence means changing.",
                    mood_change=50,
                    success_dialogue="* You accept the loss of your current form.\n* \"Ah... you understand the price.\"",
                ),
                ACTOption(
                    id="ask_purpose",
                    name="Purpose",
                    description="Ask why the Guardian guards.",
                    mood_change=35,
                    success_dialogue="* \"I guard not to keep you out...\n* ...but to ensure only the ready pass.\"\n* \"Many have been lost to premature transcendence.\"",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="all_dimensions",
                    name="All Dimensions",
                    duration=6.0,
                    pattern_type="tesseract",
                    bullet_count=64,
                    bullet_speed=180,
                    attack_dialogue="* \"Face the truth of ALL dimensions!\"",
                ),
                EnemyAttackPattern(
                    id="transcendence_test",
                    name="Transcendence Test",
                    duration=8.0,
                    pattern_type="pulse",
                    bullet_count=48,
                    bullet_speed=200,
                    soul_mode=SoulMode.PURPLE,
                    attack_dialogue="* \"Your perception will be TESTED!\"",
                ),
            ],
            xp_reward=200,
            gold_reward=100,
            spare_gold_reward=200,
            spare_threshold=200,
            can_flee=False,
        ),
    }


# Pre-built enemy dict for quick access
ENEMIES_4D = create_4d_enemies()
