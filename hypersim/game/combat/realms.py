"""Dimensional realms - distinct regions within each dimension with unique properties.

Each dimension contains multiple realms with their own:
- Visual themes and atmosphere
- Native inhabitants (enemies and NPCs)
- Combat modifiers
- Lore and story significance
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

from .dimensional_mechanics import RealityWarpType


class RealmType(Enum):
    """Categories of realms."""
    ORIGIN = auto()      # Starting areas
    SETTLEMENT = auto()  # Populated areas with NPCs
    WILDERNESS = auto()  # Dangerous exploration areas
    DUNGEON = auto()     # Combat-focused challenges
    SACRED = auto()      # Lore-rich, mystical areas
    BORDER = auto()      # Transition zones between dimensions
    VOID = auto()        # Empty, mysterious spaces
    CAPITAL = auto()     # Major cities/centers


@dataclass
class RealmModifier:
    """Combat modifiers active in a realm."""
    name: str
    description: str
    
    # Combat effects
    damage_multiplier: float = 1.0
    defense_multiplier: float = 1.0
    speed_multiplier: float = 1.0
    
    # Special effects
    default_warp: Optional[RealityWarpType] = None
    soul_mode_override: Optional[str] = None
    
    # Environmental hazards
    passive_damage: float = 0.0  # Per second
    healing_reduction: float = 0.0  # 0.0-1.0
    
    # Perception effects
    visibility_modifier: float = 1.0
    transcendence_rate: float = 1.0


@dataclass
class Realm:
    """A distinct region within a dimension."""
    id: str
    name: str
    dimension: str
    realm_type: RealmType
    
    # Description and lore
    description: str
    atmosphere: str  # Short mood description
    discovery_text: str  # Text when first entering
    
    # Visual theming
    primary_color: Tuple[int, int, int] = (100, 100, 100)
    secondary_color: Tuple[int, int, int] = (50, 50, 50)
    ambient_particles: bool = False
    
    # Combat properties
    modifier: RealmModifier = field(default_factory=lambda: RealmModifier("Default", ""))
    
    # Inhabitants
    native_enemy_ids: List[str] = field(default_factory=list)
    npc_ids: List[str] = field(default_factory=list)
    boss_id: Optional[str] = None
    
    # Connections
    connected_realms: List[str] = field(default_factory=list)
    portal_to_dimension: Optional[str] = None  # If this is a border realm
    
    # Progression
    requires_item: Optional[str] = None
    requires_boss_defeated: Optional[str] = None
    unlock_message: str = ""


# =============================================================================
# 1D REALMS - The Line
# =============================================================================

REALMS_1D: Dict[str, Realm] = {
    "origin_point": Realm(
        id="origin_point",
        name="The Origin Point",
        dimension="1d",
        realm_type=RealmType.ORIGIN,
        description="""Where all existence in 1D begins. A single point that 
        expanded into the first line. It pulses with primordial energy.""",
        atmosphere="Peaceful, contemplative, ancient",
        discovery_text="* You stand at the very beginning of linear existence.",
        primary_color=(200, 200, 255),
        secondary_color=(100, 100, 200),
        native_enemy_ids=["point_spirit", "nascent_line"],
        npc_ids=["elder_segment", "the_first_point"],
        connected_realms=["forward_path", "backward_void"],
    ),
    
    "forward_path": Realm(
        id="forward_path",
        name="The Forward Path",
        dimension="1d",
        realm_type=RealmType.WILDERNESS,
        description="""The eternal road ahead. Line Walkers patrol endlessly,
        believing that progress means only moving forward.""",
        atmosphere="Determined, relentless, hopeful",
        discovery_text="* The path stretches ahead, infinite and unwavering.",
        primary_color=(100, 200, 150),
        secondary_color=(50, 100, 75),
        modifier=RealmModifier(
            name="Forward Momentum",
            description="Everything pushes forward",
            speed_multiplier=1.2,
        ),
        native_enemy_ids=["line_walker", "forward_sentinel", "momentum_keeper"],
        npc_ids=["tired_traveler", "eternal_runner"],
        connected_realms=["origin_point", "the_endpoint", "midpoint_station"],
    ),
    
    "backward_void": Realm(
        id="backward_void",
        name="The Backward Void",
        dimension="1d",
        realm_type=RealmType.VOID,
        description="""The direction no one travels. Those who walk backward 
        are met with existential dread - for what lies behind the beginning?""",
        atmosphere="Eerie, lonely, philosophical",
        discovery_text="* Behind the origin... what could exist before existence?",
        primary_color=(50, 50, 80),
        secondary_color=(20, 20, 40),
        modifier=RealmModifier(
            name="Existential Reversal",
            description="Time and space feel inverted",
            default_warp=RealityWarpType.MIRROR,
            visibility_modifier=0.7,
        ),
        native_enemy_ids=["void_echo", "reverse_walker", "negation_spirit"],
        npc_ids=["the_philosopher", "lost_one"],
        connected_realms=["origin_point"],
    ),
    
    "midpoint_station": Realm(
        id="midpoint_station",
        name="Midpoint Station",
        dimension="1d",
        realm_type=RealmType.SETTLEMENT,
        description="""A rest stop exactly halfway along the Line. 
        Travelers gather here to share stories and trade.""",
        atmosphere="Warm, social, busy",
        discovery_text="* A haven of rest in the endless journey.",
        primary_color=(200, 180, 100),
        secondary_color=(150, 130, 50),
        native_enemy_ids=["toll_collector"],
        npc_ids=["innkeeper_segment", "merchant_ray", "storyteller"],
        connected_realms=["forward_path", "the_endpoint"],
    ),
    
    "the_endpoint": Realm(
        id="the_endpoint",
        name="The Endpoint",
        dimension="1d", 
        realm_type=RealmType.BORDER,
        description="""Where the 1D line meets the 2D plane. The Segment Guardian
        stands watch, allowing only those ready to perceive width to pass.""",
        atmosphere="Climactic, transformative, awe-inspiring",
        discovery_text="* The line... ends? No - it OPENS.",
        primary_color=(150, 100, 255),
        secondary_color=(100, 50, 200),
        modifier=RealmModifier(
            name="Dimensional Bleed",
            description="2D energy seeps through",
            transcendence_rate=1.5,
        ),
        native_enemy_ids=["segment_guardian", "border_patrol"],
        boss_id="segment_guardian",
        portal_to_dimension="2d",
        connected_realms=["forward_path", "midpoint_station"],
    ),
}

# =============================================================================
# 2D REALMS - The Plane
# =============================================================================

REALMS_2D: Dict[str, Realm] = {
    "flatland_commons": Realm(
        id="flatland_commons",
        name="Flatland Commons",
        dimension="2d",
        realm_type=RealmType.ORIGIN,
        description="""The central plaza of 2D existence. Polygons of all types
        gather here - triangles, squares, pentagons, and the revered circles.""",
        atmosphere="Bustling, hierarchical, geometric",
        discovery_text="* A world of shapes spreads before you in glorious flatness.",
        primary_color=(150, 200, 255),
        secondary_color=(100, 150, 200),
        native_enemy_ids=["triangle_scout", "square_citizen"],
        npc_ids=["mayor_hexagon", "elder_circle", "young_triangle"],
        connected_realms=["angular_heights", "curved_depths", "tessellation_district"],
    ),
    
    "angular_heights": Realm(
        id="angular_heights",
        name="The Angular Heights",
        dimension="2d",
        realm_type=RealmType.SETTLEMENT,
        description="""Where the polygons with few sides dwell. Triangles rule here,
        proud of their sharp vertices and perfect angles.""",
        atmosphere="Proud, martial, precise",
        discovery_text="* Sharp peaks rise in perfect triangular formation.",
        primary_color=(255, 150, 100),
        secondary_color=(200, 100, 50),
        modifier=RealmModifier(
            name="Angular Precision",
            description="Attacks are more precise",
            damage_multiplier=1.15,
        ),
        native_enemy_ids=["triangle_scout", "isoceles_warrior", "scalene_assassin", "equilateral_champion"],
        npc_ids=["general_triangle", "angle_sage"],
        boss_id="right_angle_king",
        connected_realms=["flatland_commons", "vertex_fortress"],
    ),
    
    "curved_depths": Realm(
        id="curved_depths",
        name="The Curved Depths",
        dimension="2d",
        realm_type=RealmType.SACRED,
        description="""Domain of the circles and ellipses. They contemplate infinity
        here, for a circle has infinite sides - or none at all.""",
        atmosphere="Mystical, philosophical, serene",
        discovery_text="* Perfect curves ripple outward like thoughts made manifest.",
        primary_color=(200, 100, 255),
        secondary_color=(150, 50, 200),
        modifier=RealmModifier(
            name="Infinite Contemplation",
            description="Time moves strangely here",
            speed_multiplier=0.85,
            transcendence_rate=1.3,
        ),
        native_enemy_ids=["circle_mystic", "ellipse_sage", "arc_phantom"],
        npc_ids=["high_priest_circle", "the_perfect_round"],
        connected_realms=["flatland_commons", "pi_sanctum"],
    ),
    
    "tessellation_district": Realm(
        id="tessellation_district",
        name="Tessellation District",
        dimension="2d",
        realm_type=RealmType.SETTLEMENT,
        description="""Where squares and hexagons tile perfectly, creating 
        neighborhoods of geometric precision. The middle class of Flatland.""",
        atmosphere="Orderly, comfortable, repetitive",
        discovery_text="* Perfect patterns repeat in every direction.",
        primary_color=(100, 150, 200),
        secondary_color=(50, 100, 150),
        native_enemy_ids=["square_citizen", "hexagon_worker", "tile_guardian"],
        npc_ids=["architect_square", "pattern_keeper"],
        connected_realms=["flatland_commons", "angular_heights", "fractal_frontier"],
    ),
    
    "fractal_frontier": Realm(
        id="fractal_frontier",
        name="The Fractal Frontier",
        dimension="2d",
        realm_type=RealmType.WILDERNESS,
        description="""At the edges of 2D, shapes become recursive, infinitely complex.
        Here dwell the irregular polygons, the fractals, the strange ones.""",
        atmosphere="Chaotic, beautiful, dangerous",
        discovery_text="* Infinite complexity unfolds within finite space.",
        primary_color=(100, 255, 200),
        secondary_color=(50, 200, 150),
        modifier=RealmModifier(
            name="Fractal Chaos",
            description="Reality recurses unpredictably",
            default_warp=RealityWarpType.OSCILLATE,
        ),
        native_enemy_ids=["fractal_entity", "irregular_terror", "mandelbrot_spawn"],
        npc_ids=["fractal_hermit"],
        connected_realms=["tessellation_district", "dimensional_membrane"],
    ),
    
    "dimensional_membrane": Realm(
        id="dimensional_membrane",
        name="The Dimensional Membrane",
        dimension="2d",
        realm_type=RealmType.BORDER,
        description="""The boundary where 2D meets 3D. The plane curves imperceptibly,
        hinting at a dimension of depth that Flatlanders cannot perceive.""",
        atmosphere="Liminal, transformative, vertiginous",
        discovery_text="* The world... bulges? There's something BEYOND the plane.",
        primary_color=(180, 150, 255),
        secondary_color=(130, 100, 200),
        modifier=RealmModifier(
            name="Depth Perception",
            description="You sense impossible thickness",
            transcendence_rate=2.0,
        ),
        native_enemy_ids=["membrane_warper", "depth_horror"],
        boss_id="membrane_warper",
        portal_to_dimension="3d",
        connected_realms=["fractal_frontier", "curved_depths"],
    ),
}

# =============================================================================
# 3D REALMS - The Volume
# =============================================================================

REALMS_3D: Dict[str, Realm] = {
    "geometric_citadel": Realm(
        id="geometric_citadel",
        name="The Geometric Citadel",
        dimension="3d",
        realm_type=RealmType.CAPITAL,
        description="""A magnificent city of polyhedra. Cube buildings, sphere domes,
        pyramid monuments - all coexisting in volumetric harmony.""",
        atmosphere="Grand, civilized, majestic",
        discovery_text="* Three dimensions of architecture soar around you.",
        primary_color=(200, 200, 255),
        secondary_color=(150, 150, 200),
        native_enemy_ids=["cube_guard", "pyramid_sentinel"],
        npc_ids=["king_dodecahedron", "sphere_oracle", "cube_architect"],
        connected_realms=["platonic_plains", "cavern_of_shadows", "crystalline_spires"],
    ),
    
    "platonic_plains": Realm(
        id="platonic_plains",
        name="The Platonic Plains",
        dimension="3d",
        realm_type=RealmType.WILDERNESS,
        description="""Rolling hills where the five Platonic solids roam free.
        Tetrahedra, cubes, octahedra, dodecahedra, and icosahedra graze peacefully.""",
        atmosphere="Pastoral, mathematical, pure",
        discovery_text="* Perfect forms move across a landscape of pure geometry.",
        primary_color=(150, 255, 150),
        secondary_color=(100, 200, 100),
        native_enemy_ids=["wild_tetrahedron", "roaming_octahedron", "feral_icosahedron"],
        npc_ids=["shepherd_of_solids", "platonic_philosopher"],
        connected_realms=["geometric_citadel", "sphere_sanctuary"],
    ),
    
    "cavern_of_shadows": Realm(
        id="cavern_of_shadows",
        name="Cavern of Shadows",
        dimension="3d",
        realm_type=RealmType.DUNGEON,
        description="""Deep caves where light creates shadows - the 2D projections
        of 3D objects. Some say the shadows remember being Flatlanders.""",
        atmosphere="Dark, philosophical, haunting",
        discovery_text="* Shadows dance on walls, echoes of lower dimensions.",
        primary_color=(80, 80, 100),
        secondary_color=(40, 40, 60),
        modifier=RealmModifier(
            name="Shadow Realm",
            description="2D shadows attack alongside 3D beings",
            visibility_modifier=0.6,
        ),
        native_enemy_ids=["shadow_cube", "cave_sphere", "darkness_tetrahedron"],
        npc_ids=["shadow_sage", "lost_flatlander"],
        connected_realms=["geometric_citadel", "void_between"],
    ),
    
    "crystalline_spires": Realm(
        id="crystalline_spires",
        name="The Crystalline Spires",
        dimension="3d",
        realm_type=RealmType.SACRED,
        description="""Towers of pure crystal that refract light into impossible colors.
        Here, geometric beings come to meditate on higher dimensions.""",
        atmosphere="Luminous, transcendent, sacred",
        discovery_text="* Light fragments into spectrums you've never seen.",
        primary_color=(255, 200, 255),
        secondary_color=(200, 150, 200),
        modifier=RealmModifier(
            name="Crystal Refraction",
            description="Light behaves strangely",
            transcendence_rate=1.5,
            healing_reduction=-0.2,  # Actually heals MORE
        ),
        native_enemy_ids=["crystal_guardian", "prism_elemental", "light_weaver"],
        npc_ids=["crystal_oracle", "light_keeper"],
        connected_realms=["geometric_citadel", "hyperborder"],
    ),
    
    "sphere_sanctuary": Realm(
        id="sphere_sanctuary",
        name="Sphere Sanctuary",
        dimension="3d",
        realm_type=RealmType.SETTLEMENT,
        description="""A peaceful place where spheres roll and bounce in endless play.
        The most social and friendly of 3D beings make their home here.""",
        atmosphere="Playful, warm, bouncy",
        discovery_text="* Spheres of all sizes bounce joyfully around you.",
        primary_color=(255, 200, 150),
        secondary_color=(200, 150, 100),
        modifier=RealmModifier(
            name="Bouncy Physics",
            description="Everything bounces",
        ),
        native_enemy_ids=["sphere_wanderer", "bouncing_ball", "rubber_sphere"],
        npc_ids=["sphere_elder", "bouncing_child", "roll_master"],
        connected_realms=["platonic_plains", "hyperborder"],
    ),
    
    "hyperborder": Realm(
        id="hyperborder",
        name="The Hyperborder",
        dimension="3d",
        realm_type=RealmType.BORDER,
        description="""Where 3D space curves into 4D hyperspace. Objects here cast
        shadows in directions that don't exist. The Tesseract Guardian watches.""",
        atmosphere="Mind-bending, awesome, terrifying",
        discovery_text="* Space folds in ways your mind struggles to comprehend.",
        primary_color=(255, 100, 255),
        secondary_color=(200, 50, 200),
        modifier=RealmModifier(
            name="Hyperspace Bleed",
            description="4D geometry intrudes",
            default_warp=RealityWarpType.TESSERACT,
            transcendence_rate=2.5,
        ),
        native_enemy_ids=["tesseract_fragment", "hypercube_shard", "w_axis_phantom"],
        boss_id="tesseract_guardian",
        portal_to_dimension="4d",
        connected_realms=["crystalline_spires", "sphere_sanctuary"],
    ),
}

# =============================================================================
# 4D REALMS - Hyperspace
# =============================================================================

REALMS_4D: Dict[str, Realm] = {
    "hyperspace_nexus": Realm(
        id="hyperspace_nexus",
        name="Hyperspace Nexus",
        dimension="4d",
        realm_type=RealmType.CAPITAL,
        description="""The central hub of 4D existence. Tesseracts and hyperspheres
        drift through space that connects to itself in impossible ways.""",
        atmosphere="Impossible, magnificent, overwhelming",
        discovery_text="* You perceive... everything? Inside, outside, all at once.",
        primary_color=(255, 150, 255),
        secondary_color=(200, 100, 200),
        native_enemy_ids=["tesseract_citizen", "hypersphere_wanderer"],
        npc_ids=["tesseract_sage", "hypersphere_oracle", "w_axis_guide"],
        connected_realms=["w_positive_reach", "w_negative_depths", "ana_kata_corridor"],
    ),
    
    "w_positive_reach": Realm(
        id="w_positive_reach",
        name="The W+ Reach",
        dimension="4d",
        realm_type=RealmType.WILDERNESS,
        description="""The positive W-axis extends into realms of pure possibility.
        Here, potential becomes actual, and future echoes back to present.""",
        atmosphere="Hopeful, bright, expanding",
        discovery_text="* Forward in a direction that has no name in lower dimensions.",
        primary_color=(255, 255, 150),
        secondary_color=(200, 200, 100),
        modifier=RealmModifier(
            name="Positive Potential",
            description="Everything leans toward growth",
            healing_reduction=-0.3,
            transcendence_rate=1.2,
        ),
        native_enemy_ids=["possibility_entity", "future_echo", "potential_guardian"],
        npc_ids=["seer_of_futures", "hope_keeper"],
        connected_realms=["hyperspace_nexus", "probability_gardens"],
    ),
    
    "w_negative_depths": Realm(
        id="w_negative_depths",
        name="The W- Depths",
        dimension="4d",
        realm_type=RealmType.DUNGEON,
        description="""The negative W-axis descends into realms of memory and loss.
        Here, what was echoes eternally, and the past refuses to release its grip.""",
        atmosphere="Melancholic, heavy, nostalgic",
        discovery_text="* Backward in a direction that remembers everything.",
        primary_color=(100, 100, 150),
        secondary_color=(50, 50, 100),
        modifier=RealmModifier(
            name="Negative Memory",
            description="The past weighs heavily",
            speed_multiplier=0.9,
            passive_damage=0.5,
        ),
        native_enemy_ids=["memory_specter", "regret_manifestation", "past_self"],
        npc_ids=["keeper_of_memories", "the_forgotten"],
        connected_realms=["hyperspace_nexus", "entropy_well"],
    ),
    
    "ana_kata_corridor": Realm(
        id="ana_kata_corridor",
        name="Ana-Kata Corridor",
        dimension="4d",
        realm_type=RealmType.SACRED,
        description="""A passage that moves ana (4D-up) and kata (4D-down).
        Here, the nature of dimensional existence itself is contemplated.""",
        atmosphere="Transcendent, holy, infinite",
        discovery_text="* Up and down in a direction perpendicular to up and down.",
        primary_color=(200, 255, 255),
        secondary_color=(150, 200, 200),
        modifier=RealmModifier(
            name="Ana-Kata Flow",
            description="Movement through W is enhanced",
            transcendence_rate=2.0,
        ),
        native_enemy_ids=["ana_guardian", "kata_guardian", "corridor_keeper"],
        npc_ids=["dimension_monk", "transcendence_guide"],
        connected_realms=["hyperspace_nexus", "beyond_threshold"],
    ),
    
    "probability_gardens": Realm(
        id="probability_gardens",
        name="The Probability Gardens",
        dimension="4d",
        realm_type=RealmType.SETTLEMENT,
        description="""A place where all possible outcomes bloom like flowers.
        Every choice spawns a new branch, and the gardens tend them all.""",
        atmosphere="Surreal, beautiful, paradoxical",
        discovery_text="* Every possibility exists here, simultaneously.",
        primary_color=(255, 200, 255),
        secondary_color=(200, 150, 200),
        native_enemy_ids=["probability_beast", "quantum_flower", "choice_echo"],
        npc_ids=["gardener_of_possibilities", "probability_sage"],
        connected_realms=["w_positive_reach", "beyond_threshold"],
    ),
    
    "entropy_well": Realm(
        id="entropy_well",
        name="The Entropy Well",
        dimension="4d",
        realm_type=RealmType.VOID,
        description="""Where dimensional energy drains away. The lowest point in 
        all of hyperspace, where things go to be forgotten.""",
        atmosphere="Draining, silent, final",
        discovery_text="* Everything flows downward here, toward forgetting.",
        primary_color=(50, 50, 50),
        secondary_color=(20, 20, 20),
        modifier=RealmModifier(
            name="Entropic Drain",
            description="Energy constantly depletes",
            passive_damage=1.0,
            healing_reduction=0.5,
            transcendence_rate=0.5,
        ),
        native_enemy_ids=["entropy_beast", "void_consumer", "forgetting_spirit"],
        npc_ids=["last_witness"],
        connected_realms=["w_negative_depths"],
    ),
    
    "beyond_threshold": Realm(
        id="beyond_threshold",
        name="The Beyond Threshold",
        dimension="4d",
        realm_type=RealmType.BORDER,
        description="""The edge of 4D existence. Beyond lies 5D, 6D, infinity...
        or perhaps nothing at all. None who have crossed have returned to tell.""",
        atmosphere="Ultimate, unknowable, transcendent",
        discovery_text="* The final boundary. Beyond this... what?",
        primary_color=(255, 255, 255),
        secondary_color=(200, 200, 200),
        modifier=RealmModifier(
            name="Transcendence Threshold",
            description="The boundary of all boundaries",
            transcendence_rate=3.0,
        ),
        native_enemy_ids=["threshold_guardian", "infinity_fragment"],
        boss_id="threshold_guardian",
        npc_ids=["the_transcended"],
        connected_realms=["ana_kata_corridor", "probability_gardens"],
    ),
}

# Combined realm registry
ALL_REALMS: Dict[str, Realm] = {}
ALL_REALMS.update(REALMS_1D)
ALL_REALMS.update(REALMS_2D)
ALL_REALMS.update(REALMS_3D)
ALL_REALMS.update(REALMS_4D)


def get_realm(realm_id: str) -> Optional[Realm]:
    """Get a realm by ID."""
    return ALL_REALMS.get(realm_id)


def get_realms_for_dimension(dimension: str) -> List[Realm]:
    """Get all realms for a dimension."""
    return [r for r in ALL_REALMS.values() if r.dimension == dimension]


def get_starting_realm(dimension: str) -> Optional[Realm]:
    """Get the starting realm for a dimension."""
    for realm in get_realms_for_dimension(dimension):
        if realm.realm_type == RealmType.ORIGIN:
            return realm
        if realm.realm_type == RealmType.CAPITAL:
            return realm
    realms = get_realms_for_dimension(dimension)
    return realms[0] if realms else None


def get_border_realm(dimension: str) -> Optional[Realm]:
    """Get the border realm for a dimension (leads to next dimension)."""
    for realm in get_realms_for_dimension(dimension):
        if realm.realm_type == RealmType.BORDER and realm.portal_to_dimension:
            return realm
    return None
