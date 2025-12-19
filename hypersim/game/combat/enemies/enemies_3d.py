"""3D Dimension Enemies - The Volume.

Enemies that exist in three-dimensional space:
- Cube Guard: Proud military polyhedron
- Sphere Wanderer: Lonely rolling friend
- Pyramid Sentinel: Ancient wisdom keeper
- Shadow Cube: Confused projection
- Crystal Guardian: Light-bending protector
"""
from typing import Dict

from ..core import CombatStats, SoulMode
from .base import (
    CombatEnemy, EnemyPersonality, EnemyMood,
    ACTOption, EnemyAttackPattern, check_act
)


def create_3d_enemies() -> Dict[str, CombatEnemy]:
    """Create all 3D enemies."""
    return {
        **_create_basic_enemies(),
        **_create_advanced_enemies(),
    }


def _create_basic_enemies() -> Dict[str, CombatEnemy]:
    """Basic 3D enemies."""
    return {
        "cube_guard": CombatEnemy(
            id="cube_guard",
            name="Cube Guard",
            stats=CombatStats(hp=45, max_hp=45, attack=10, defense=12),
            personality=EnemyPersonality.PROUD,
            dimension="3d",
            color=(150, 200, 255),
            encounter_text="* Cube Guard materializes in three dimensions!\n* \"Halt! State your business in volumetric space!\"",
            check_text="* CUBE GUARD - ATK 10 DEF 12\n* 6 faces, 12 edges, 8 vertices.\n* Takes its job very seriously.\n* Has guarded these volumes for centuries.",
            idle_dialogues=[
                "* Cube Guard stands at attention.",
                "* \"All six faces accounted for!\"",
                "* Cube Guard rotates to show all sides.",
                "* \"Order! Structure! Right angles!\"",
            ],
            hurt_dialogues=[
                "* One face dents slightly.",
                "* \"A hit! But my structure holds!\"",
            ],
            spare_dialogue="* Cube Guard salutes and rolls away.\n* \"Carry on, citizen of volume.\"",
            kill_dialogue="* Cube Guard unfolds into a flat cross.",
            act_options=[
                check_act(),
                ACTOption(
                    id="salute",
                    name="Salute",
                    description="Give a formal salute.",
                    mood_change=40,
                    success_dialogue="* You salute respectfully.\n* Cube Guard returns the gesture with precision!",
                ),
                ACTOption(
                    id="inspect",
                    name="Inspect",
                    description="Perform a formal inspection.",
                    mood_change=45,
                    success_dialogue="* \"Excellent form, soldier.\"\n* Cube Guard swells with pride!",
                ),
                ACTOption(
                    id="count_faces",
                    name="Count Faces",
                    description="Count all six faces approvingly.",
                    mood_change=35,
                    success_dialogue="* \"One, two, three, four, five, SIX!\"\n* \"Finally! Someone who appreciates proper counting!\"",
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
                    attack_dialogue="* All six faces attack in formation!",
                ),
            ],
            xp_reward=20,
            gold_reward=15,
            spare_threshold=100,
        ),
        
        "sphere_wanderer": CombatEnemy(
            id="sphere_wanderer",
            name="Sphere Wanderer",
            stats=CombatStats(hp=40, max_hp=40, attack=8, defense=6),
            personality=EnemyPersonality.LONELY,
            dimension="3d",
            color=(255, 180, 100),
            encounter_text="* Sphere Wanderer rolls towards you, seeking company.\n* It bounces hopefully.",
            check_text="* SPHERE WANDERER - ATK 8 DEF 6\n* Perfect in all directions. Equal in every way.\n* Seems to want a friend badly.\n* Has been rolling alone for too long.",
            idle_dialogues=[
                "* Sphere Wanderer bounces hopefully.",
                "* \"Will you... roll with me?\"",
                "* (It looks so lonely.)",
                "* \"Everyone else has corners to hold onto...\"",
            ],
            hurt_dialogues=[
                "* Sphere Wanderer deflates slightly.",
                "* \"Even you... won't play with me?\"",
            ],
            spare_dialogue="* Sphere Wanderer bounces away joyfully!\n* \"I have a FRIEND! I'll never forget you!\"",
            kill_dialogue="* Sphere Wanderer pops quietly.",
            act_options=[
                check_act(),
                ACTOption(
                    id="play",
                    name="Play",
                    description="Play catch with them.",
                    mood_change=50,
                    success_dialogue="* You play catch!\n* Sphere Wanderer is OVERJOYED!\n* \"Again! Again!\"",
                ),
                ACTOption(
                    id="befriend",
                    name="Befriend",
                    description="Offer genuine friendship.",
                    mood_change=60,
                    success_dialogue="* You offer to be friends.\n* Sphere Wanderer cries happy tears!\n* \"Really?! You mean it?!\"",
                ),
                ACTOption(
                    id="compliment_roundness",
                    name="Roundness",
                    description="Compliment their perfect roundness.",
                    mood_change=40,
                    success_dialogue="* \"You... you think I'm perfectly round?\"\n* Sphere Wanderer glows with happiness.",
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
                    attack_dialogue="* \"Play with me! Please!\"",
                ),
            ],
            xp_reward=15,
            gold_reward=12,
            spare_gold_reward=20,
            spare_threshold=100,
        ),
    }


def _create_advanced_enemies() -> Dict[str, CombatEnemy]:
    """Advanced 3D enemies."""
    return {
        "pyramid_sentinel": CombatEnemy(
            id="pyramid_sentinel",
            name="Pyramid Sentinel",
            stats=CombatStats(hp=50, max_hp=50, attack=12, defense=10),
            personality=EnemyPersonality.PHILOSOPHICAL,
            dimension="3d",
            color=(200, 180, 100),
            encounter_text="* Pyramid Sentinel rises from the ground!\n* Ancient wisdom radiates from its apex.",
            check_text="* PYRAMID SENTINEL - ATK 12 DEF 10\n* Ancient guardian of volumetric secrets.\n* Its apex points toward higher dimensions.\n* Contains the wisdom of ages.",
            idle_dialogues=[
                "* The Sentinel hums with ancient power.",
                "* \"I have stood since the first volume was measured.\"",
                "* Its apex tracks something above.",
                "* \"Squares become cubes. Cubes become...?\"",
            ],
            spare_dialogue="* Pyramid Sentinel sinks back into the ground.\n* \"Seek the apex of all dimensions.\"",
            kill_dialogue="* Pyramid Sentinel crumbles to sand.",
            act_options=[
                check_act(),
                ACTOption(
                    id="seek_wisdom",
                    name="Seek Wisdom",
                    description="Ask for ancient knowledge.",
                    mood_change=40,
                    success_dialogue="* The Sentinel shares geometric truths.\n* \"A pyramid's shadow... is a 2D projection of 3D truth.\"",
                ),
                ACTOption(
                    id="respect_age",
                    name="Show Respect",
                    description="Bow to its ancient presence.",
                    mood_change=45,
                    success_dialogue="* You bow respectfully.\n* \"The young one shows proper deference.\"",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="apex_beam",
                    name="Apex Beam",
                    duration=4.5,
                    pattern_type="aimed_triangles",
                    bullet_count=12,
                    bullet_speed=200,
                    attack_dialogue="* Power gathers at the apex!",
                ),
            ],
            xp_reward=25,
            gold_reward=20,
            spare_threshold=100,
        ),
        
        "shadow_cube": CombatEnemy(
            id="shadow_cube",
            name="Shadow Cube",
            stats=CombatStats(hp=35, max_hp=35, attack=9, defense=5),
            personality=EnemyPersonality.CONFUSED,
            dimension="3d",
            color=(60, 60, 80),
            encounter_text="* A shadow detaches from the wall!\n* Shadow Cube remembers being 2D...",
            check_text="* SHADOW CUBE - ATK 9 DEF 5\n* A 2D projection that gained awareness.\n* Confused about its true dimensionality.\n* Flickers between flat and volumetric.",
            idle_dialogues=[
                "* \"Am I flat or thick? Both? Neither?\"",
                "* Shadow Cube flickers unstably.",
                "* \"I cast a shadow... but I AM a shadow...\"",
                "* The shadow stretches impossibly.",
            ],
            spare_dialogue="* Shadow Cube fades into peaceful darkness.\n* \"Maybe I am both. Maybe that's okay.\"",
            kill_dialogue="* Shadow Cube becomes truly flat.",
            act_options=[
                check_act(),
                ACTOption(
                    id="explain_projection",
                    name="Projection",
                    description="Explain 2D projections of 3D.",
                    mood_change=50,
                    success_dialogue="* You explain dimensional projection.\n* \"I'm a shadow OF something! Not just nothing!\"",
                ),
                ACTOption(
                    id="cast_shadow",
                    name="Cast Shadow",
                    description="Cast your own shadow alongside it.",
                    mood_change=40,
                    success_dialogue="* Your shadows touch.\n* \"We're both projections of something greater...\"",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="shadow_spread",
                    name="Shadow Spread",
                    duration=3.5,
                    pattern_type="grid",
                    bullet_count=12,
                    bullet_speed=140,
                    attack_dialogue="* Shadows spread across every surface!",
                ),
            ],
            xp_reward=12,
            gold_reward=10,
            spare_threshold=90,
        ),
        
        "crystal_guardian": CombatEnemy(
            id="crystal_guardian",
            name="Crystal Guardian",
            stats=CombatStats(hp=55, max_hp=55, attack=14, defense=8),
            personality=EnemyPersonality.PROUD,
            dimension="3d",
            color=(255, 200, 255),
            encounter_text="* Crystal Guardian refracts light into rainbows!\n* \"You stand in sacred chromatic space!\"",
            check_text="* CRYSTAL GUARDIAN - ATK 14 DEF 8\n* Made of pure crystalline geometry.\n* Refracts light into impossible colors.\n* Guards the path to higher understanding.",
            idle_dialogues=[
                "* Light shatters into spectrums around it.",
                "* \"Each facet holds a different truth.\"",
                "* Colors dance across the Guardian's form.",
                "* \"Clarity comes through proper angles.\"",
            ],
            spare_dialogue="* Crystal Guardian lets you pass.\n* \"May your perception refract into new spectrums.\"",
            kill_dialogue="* Crystal Guardian shatters into dull fragments.",
            act_options=[
                check_act(),
                ACTOption(
                    id="admire_facets",
                    name="Admire Facets",
                    description="Admire the crystal facets.",
                    mood_change=40,
                    success_dialogue="* You appreciate each geometric plane.\n* \"Yes! Each facet is a window to truth!\"",
                ),
                ACTOption(
                    id="discuss_light",
                    name="Light",
                    description="Discuss the nature of refracted light.",
                    mood_change=45,
                    success_dialogue="* You speak of spectrums and wavelengths.\n* \"One light, infinite colors! Dimensional metaphor!\"",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="prism_burst",
                    name="Prism Burst",
                    duration=4.0,
                    pattern_type="pulse",
                    bullet_count=24,
                    bullet_speed=170,
                    attack_dialogue="* Light refracts into weaponized rainbows!",
                ),
            ],
            xp_reward=30,
            gold_reward=25,
            spare_threshold=100,
        ),
    }


def _create_boss_enemies() -> Dict[str, CombatEnemy]:
    """Boss enemies for 3D."""
    return {
        "hyperborder_sentinel": CombatEnemy(
            id="hyperborder_sentinel",
            name="Hyperborder Sentinel",
            stats=CombatStats(hp=80, max_hp=80, attack=16, defense=12),
            personality=EnemyPersonality.GEOMETRIC,
            dimension="3d",
            color=(200, 100, 255),
            is_boss=True,
            encounter_text="* At the edge of 3D, something guards the border!\n* Hyperborder Sentinel manifests from impossible angles!",
            check_text="* HYPERBORDER SENTINEL - ATK 16 DEF 12\n* Guards the passage to 4D.\n* Has glimpsed the fourth dimension.\n* Warns travelers of what lies beyond.",
            idle_dialogues=[
                "* \"Beyond me lies... MORE. Are you ready for more?\"",
                "* The Sentinel's form flickers with extra angles.",
                "* \"I have seen what 4D does to the unprepared.\"",
                "* \"Width, height, depth... and then WHAT?\"",
            ],
            hurt_dialogues=[
                "* \"You strike at dimensions you cannot see!\"",
                "* Part of the Sentinel phases into hyperspace.",
            ],
            low_hp_dialogues=[
                "* \"Perhaps... you ARE ready for what lies beyond.\"",
                "* The border between dimensions thins.",
            ],
            spare_dialogue="* Hyperborder Sentinel steps aside.\n* \"Go. May you survive what I could not become.\"\n* The way to 4D opens!",
            kill_dialogue="* The Sentinel collapses.\n* The border tears. Reality screams briefly.",
            act_options=[
                check_act(),
                ACTOption(
                    id="ask_about_4d",
                    name="Ask About 4D",
                    description="Ask what lies beyond.",
                    mood_change=30,
                    success_dialogue="* \"Imagine seeing inside closed boxes.\"\n* \"Imagine your secrets laid bare.\"\n* \"That is 4D.\"",
                ),
                ACTOption(
                    id="prove_readiness",
                    name="Prove Ready",
                    description="Demonstrate you understand the cost.",
                    mood_change=45,
                    requires_turn=2,
                    success_dialogue="* You speak of dissolution and growth.\n* \"You understand the price. Good.\"",
                ),
                ACTOption(
                    id="empathize",
                    name="Empathize",
                    description="Acknowledge its lonely vigil.",
                    mood_change=40,
                    success_dialogue="* \"You see my burden. Few do.\"\n* \"Guarding a door you dare not enter...\"",
                ),
            ],
            attack_patterns=[
                EnemyAttackPattern(
                    id="dimensional_tear",
                    name="Dimensional Tear",
                    duration=4.5,
                    pattern_type="tesseract",
                    bullet_count=20,
                    bullet_speed=180,
                    attack_dialogue="* Reality TEARS at the border!",
                ),
                EnemyAttackPattern(
                    id="hyperspace_glimpse",
                    name="Hyperspace Glimpse",
                    duration=5.0,
                    pattern_type="pulse",
                    bullet_count=24,
                    bullet_speed=160,
                    soul_mode=SoulMode.BLUE,
                    attack_dialogue="* \"See what awaits!\"",
                ),
            ],
            xp_reward=60,
            gold_reward=40,
            spare_gold_reward=70,
            spare_threshold=120,
            can_flee=False,
        ),
    }


def create_3d_enemies() -> Dict[str, CombatEnemy]:
    """Create all 3D enemies."""
    return {
        **_create_basic_enemies(),
        **_create_advanced_enemies(),
        **_create_boss_enemies(),
    }


# Pre-built enemy dict for quick access
ENEMIES_3D = create_3d_enemies()
