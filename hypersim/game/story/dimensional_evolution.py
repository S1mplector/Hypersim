"""Evolution paths for each dimension.

Every dimension has its own shapes and evolution paths:
- 1D: Line segments, rays, intervals → vibrating strings, wave functions
- 2D: Polygons, circles → complex polygons, fractals, curves
- 3D: Polyhedra, spheres → complex solids, toroids, manifolds
- 4D: Polytopes → hyperspheres, exotic manifolds (existing system)

Each dimension's evolution represents expanded UNDERSTANDING of that dimension,
not just gaining power but perceiving more of reality.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class DimensionTier(Enum):
    """Evolution tiers within a dimension."""
    NASCENT = 1      # Just born into dimension
    AWAKENED = 2     # Basic understanding
    ADEPT = 3        # Competent
    MASTER = 4       # Deep understanding
    TRANSCENDENT = 5 # Ready to perceive next dimension


@dataclass
class DimensionalForm:
    """A shape/form within a specific dimension."""
    id: str
    name: str
    short_name: str
    dimension: str  # "1d", "2d", "3d", "4d"
    tier: DimensionTier
    
    # Lore
    description: str
    lore: str
    philosophical_meaning: str = ""
    
    # Requirements
    xp_required: int = 0
    requires_forms: List[str] = field(default_factory=list)
    
    # Stats
    perception_bonus: float = 0.0  # How well you perceive this dimension
    stability: float = 1.0         # Resistance to dimensional shifts
    resonance: float = 1.0         # Connection to other beings
    
    # Abilities unlocked
    abilities: List[str] = field(default_factory=list)
    
    # Visual
    color: Tuple[int, int, int] = (200, 200, 255)
    vertices: int = 0
    edges: int = 0


# =============================================================================
# 1D FORMS - The Line Beings
# =============================================================================

FORMS_1D: Dict[str, DimensionalForm] = {
    # === NASCENT ===
    "point_awakened": DimensionalForm(
        id="point_awakened",
        name="Awakened Point",
        short_name="Point",
        dimension="1d",
        tier=DimensionTier.NASCENT,
        description="A point that has just achieved self-awareness and extended into the Line.",
        lore="You remember nothing before this. There was darkness, then suddenly: direction. Forward exists. Backward exists. You ARE.",
        philosophical_meaning="The birth of choice - for the first time, you can decide which way to go.",
        xp_required=0,
        perception_bonus=0.0,
        stability=0.5,
        resonance=0.5,
        abilities=["pulse"],
        color=(150, 150, 200),
        vertices=1,
        edges=0,
    ),
    
    "segment": DimensionalForm(
        id="segment",
        name="Line Segment",
        short_name="Segment",
        dimension="1d",
        tier=DimensionTier.NASCENT,
        description="A being with defined beginning and end - you know your boundaries.",
        lore="You have grown. You are no longer just a point - you have LENGTH. You occupy space. You have a start and an end. This is terrifying and wonderful.",
        philosophical_meaning="Understanding limitation - to have boundaries is to have definition.",
        xp_required=50,
        requires_forms=["point_awakened"],
        perception_bonus=0.1,
        stability=0.6,
        resonance=0.6,
        abilities=["extend", "contract"],
        color=(160, 160, 210),
        vertices=2,
        edges=1,
    ),
    
    # === AWAKENED ===
    "ray": DimensionalForm(
        id="ray",
        name="Ray",
        short_name="Ray",
        dimension="1d",
        tier=DimensionTier.AWAKENED,
        description="A being with a beginning but no end - infinite in one direction.",
        lore="You have shed one of your limits. Your end has dissolved into infinity. You can extend forever forward, but you still remember your origin. This is freedom.",
        philosophical_meaning="Releasing limitation while maintaining identity - you can grow infinitely while remembering where you began.",
        xp_required=150,
        requires_forms=["segment"],
        perception_bonus=0.2,
        stability=0.7,
        resonance=0.7,
        abilities=["infinite_extend", "origin_anchor"],
        color=(170, 170, 220),
        vertices=1,
        edges=1,
    ),
    
    "interval": DimensionalForm(
        id="interval",
        name="Bounded Interval",
        short_name="Interval",
        dimension="1d",
        tier=DimensionTier.AWAKENED,
        description="A segment that has learned to CONTAIN - to have an inside.",
        lore="You have discovered a profound truth: between your endpoints lies INTERIOR. You are no longer just length - you are containment. Other points can exist WITHIN you.",
        philosophical_meaning="The first concept of 'inside' and 'outside' - the seed of higher-dimensional thinking.",
        xp_required=200,
        requires_forms=["segment"],
        perception_bonus=0.25,
        stability=0.8,
        resonance=0.6,
        abilities=["contain", "exclude"],
        color=(180, 180, 230),
        vertices=2,
        edges=1,
    ),
    
    # === ADEPT ===
    "vibrating_string": DimensionalForm(
        id="vibrating_string",
        name="Vibrating String",
        short_name="String",
        dimension="1d",
        tier=DimensionTier.ADEPT,
        description="A line that has learned to oscillate - to create PATTERN in 1D.",
        lore="You vibrate. You pulse. You create waves along your length. In doing so, you have discovered TIME in a deeper way - rhythm, frequency, pattern. You are music made manifest.",
        philosophical_meaning="Pattern emerges from simple oscillation - complexity from simplicity.",
        xp_required=400,
        requires_forms=["ray", "interval"],
        perception_bonus=0.4,
        stability=0.7,
        resonance=0.9,
        abilities=["resonate", "harmonize", "pulse_wave"],
        color=(190, 170, 240),
        vertices=2,
        edges=1,
    ),
    
    "vector": DimensionalForm(
        id="vector",
        name="Vector",
        short_name="Vector",
        dimension="1d",
        tier=DimensionTier.ADEPT,
        description="A directed line - you have magnitude AND direction as fundamental properties.",
        lore="You are no longer just existence in 1D - you are INTENT. You point somewhere. You have purpose encoded in your very being. Other beings can read your direction and know your will.",
        philosophical_meaning="Purpose as identity - you are not just what you are, but where you're going.",
        xp_required=500,
        requires_forms=["ray"],
        perception_bonus=0.45,
        stability=0.85,
        resonance=0.75,
        abilities=["direct", "transmit_intent", "align"],
        color=(200, 180, 250),
        vertices=2,
        edges=1,
    ),
    
    # === MASTER ===
    "wave_function": DimensionalForm(
        id="wave_function",
        name="Wave Function",
        short_name="Wave",
        dimension="1d",
        tier=DimensionTier.MASTER,
        description="A being that exists as probability along the line - everywhere and nowhere.",
        lore="You have transcended fixed position. You exist as a PROBABILITY DISTRIBUTION - more likely here, less likely there, but never completely anywhere. You have touched the quantum nature of reality.",
        philosophical_meaning="Existence is not binary - you can be partially everywhere, a distribution of being.",
        xp_required=800,
        requires_forms=["vibrating_string", "vector"],
        perception_bonus=0.6,
        stability=0.5,
        resonance=1.0,
        abilities=["superposition", "collapse", "quantum_tunnel"],
        color=(220, 150, 255),
        vertices=0,  # Undefined
        edges=0,
    ),
    
    "infinite_line": DimensionalForm(
        id="infinite_line",
        name="Infinite Line",
        short_name="∞Line",
        dimension="1d",
        tier=DimensionTier.MASTER,
        description="A line extending infinitely in BOTH directions - you have no beginning, no end.",
        lore="You have released all limits. You extend forever forward AND forever backward. You have no origin, no terminus. You simply ARE, throughout all of 1D existence. You are the LINE itself.",
        philosophical_meaning="Complete freedom from boundary - identity without limitation.",
        xp_required=1000,
        requires_forms=["ray", "wave_function"],
        perception_bonus=0.7,
        stability=0.9,
        resonance=0.8,
        abilities=["omnipresence_1d", "infinite_reach"],
        color=(230, 160, 255),
        vertices=0,
        edges=1,
    ),
    
    # === TRANSCENDENT ===
    "line_transcendent": DimensionalForm(
        id="line_transcendent",
        name="Transcendent Line",
        short_name="Trans-Line",
        dimension="1d",
        tier=DimensionTier.TRANSCENDENT,
        description="A 1D being on the verge of perceiving the second dimension.",
        lore="You have mastered the Line completely. And in your mastery, you sense... something else. A direction that is neither forward nor backward. A way of moving that you cannot quite comprehend. The Plane calls to you.",
        philosophical_meaning="Mastery leads to awareness of limitation - the expert sees what the novice cannot.",
        xp_required=1500,
        requires_forms=["wave_function", "infinite_line"],
        perception_bonus=0.9,
        stability=1.0,
        resonance=1.0,
        abilities=["sense_2d", "prepare_expansion", "dimensional_ripple"],
        color=(255, 180, 255),
        vertices=0,
        edges=1,
    ),
}


# =============================================================================
# 2D FORMS - The Flat Beings
# =============================================================================

FORMS_2D: Dict[str, DimensionalForm] = {
    # === NASCENT ===
    "newborn_flat": DimensionalForm(
        id="newborn_flat",
        name="Newborn Flat",
        short_name="Flat",
        dimension="2d",
        tier=DimensionTier.NASCENT,
        description="A being who has just perceived the second dimension - width exists!",
        lore="LEFT! RIGHT! The words explode in your consciousness. There are directions you never knew existed! The line you lived on was just the EDGE of something vast. You see the Plane, and weep with joy.",
        philosophical_meaning="The shock of expanded perception - reality is larger than you thought.",
        xp_required=0,
        perception_bonus=0.0,
        stability=0.5,
        resonance=0.5,
        abilities=["sidestep"],
        color=(150, 200, 150),
        vertices=0,
        edges=0,
    ),
    
    "triangle": DimensionalForm(
        id="triangle",
        name="Triangle",
        short_name="Triangle",
        dimension="2d",
        tier=DimensionTier.NASCENT,
        description="The simplest polygon - three vertices, three edges, one face.",
        lore="You have taken shape! Three points, three lines, and for the first time: AREA. You enclose space. You have an inside that is truly distinct from outside. You are the foundation of all 2D geometry.",
        philosophical_meaning="The minimum complexity for enclosure - three is the first number of wholeness.",
        xp_required=100,
        requires_forms=["newborn_flat"],
        perception_bonus=0.15,
        stability=0.7,
        resonance=0.6,
        abilities=["pierce", "stable_stance"],
        color=(160, 210, 160),
        vertices=3,
        edges=3,
    ),
    
    # === AWAKENED ===
    "square": DimensionalForm(
        id="square",
        name="Square",
        short_name="Square",
        dimension="2d",
        tier=DimensionTier.AWAKENED,
        description="Four equal sides, four right angles - the shape of order.",
        lore="Symmetry! Balance! Your four sides are equal, your angles perfect. You tile the plane without gaps - you are a piece of the cosmic grid. Where triangles are unstable, you are solid. Where triangles pierce, you contain.",
        philosophical_meaning="Order and structure - the universe has patterns, and you embody one.",
        xp_required=250,
        requires_forms=["triangle"],
        perception_bonus=0.25,
        stability=0.85,
        resonance=0.7,
        abilities=["tile", "stabilize", "contain_area"],
        color=(170, 220, 170),
        vertices=4,
        edges=4,
    ),
    
    "pentagon": DimensionalForm(
        id="pentagon",
        name="Pentagon",
        short_name="Pentagon",
        dimension="2d",
        tier=DimensionTier.AWAKENED,
        description="Five sides - the first polygon that cannot tile alone.",
        lore="Five sides. Five is special - it brings the golden ratio, the spiral, the pattern of life itself. You cannot tile the plane alone, but you can create aperiodic patterns. You are unique, irreplaceable.",
        philosophical_meaning="Not everything must fit perfectly - uniqueness has value beyond uniformity.",
        xp_required=350,
        requires_forms=["square"],
        perception_bonus=0.3,
        stability=0.75,
        resonance=0.85,
        abilities=["golden_resonance", "aperiodic_pattern"],
        color=(180, 200, 180),
        vertices=5,
        edges=5,
    ),
    
    # === ADEPT ===
    "hexagon": DimensionalForm(
        id="hexagon",
        name="Hexagon",
        short_name="Hexagon",
        dimension="2d",
        tier=DimensionTier.ADEPT,
        description="Six sides - the most efficient shape for tiling.",
        lore="Bees know this truth: six sides enclose the maximum area with minimum perimeter. You are EFFICIENCY made manifest. Your tiling leaves no gaps, wastes no space. You are nature's choice.",
        philosophical_meaning="Optimal solutions exist in nature - mathematics describes beauty.",
        xp_required=500,
        requires_forms=["pentagon"],
        perception_bonus=0.4,
        stability=0.9,
        resonance=0.8,
        abilities=["efficient_contain", "perfect_tile", "natural_resonance"],
        color=(190, 230, 190),
        vertices=6,
        edges=6,
    ),
    
    "circle": DimensionalForm(
        id="circle",
        name="Circle",
        short_name="Circle",
        dimension="2d",
        tier=DimensionTier.ADEPT,
        description="Infinite sides, infinite symmetry - the limit of polygons.",
        lore="You have no vertices. You have no edges. You are the limit that all polygons approach as they add more sides. You are CONTINUOUS. Every point on your boundary is equal. You are democracy in geometric form.",
        philosophical_meaning="Limits approach perfection - infinite refinement yields smooth beauty.",
        xp_required=600,
        requires_forms=["hexagon"],
        perception_bonus=0.45,
        stability=0.8,
        resonance=0.95,
        abilities=["roll", "contain_optimal", "symmetry_all"],
        color=(200, 240, 200),
        vertices=0,  # Infinite
        edges=0,     # Infinite
    ),
    
    # === MASTER ===
    "star_polygon": DimensionalForm(
        id="star_polygon",
        name="Star Polygon",
        short_name="Star",
        dimension="2d",
        tier=DimensionTier.MASTER,
        description="A polygon that crosses itself - non-convex, complex, beautiful.",
        lore="You have discovered that lines can CROSS. Your edges intersect, creating patterns within patterns. You are not simple containment - you are complexity, recursion, self-reference. You are the first hint of fractal nature.",
        philosophical_meaning="Complexity emerges from simple rules applied recursively.",
        xp_required=900,
        requires_forms=["hexagon", "circle"],
        perception_bonus=0.55,
        stability=0.7,
        resonance=0.9,
        abilities=["self_intersect", "pattern_within", "recursive_form"],
        color=(220, 220, 180),
        vertices=5,  # Pentagram
        edges=5,
    ),
    
    "fractal_form": DimensionalForm(
        id="fractal_form",
        name="Fractal Form",
        short_name="Fractal",
        dimension="2d",
        tier=DimensionTier.MASTER,
        description="A shape with infinite perimeter but finite area - self-similar at all scales.",
        lore="You are infinite within the finite. Your boundary goes on forever, yet you fit in the palm of a hand. Zoom into any part of you, and you see... yourself. You are the same at every scale. You are SELF-SIMILAR.",
        philosophical_meaning="Infinity can be contained - the infinite and finite coexist.",
        xp_required=1200,
        requires_forms=["star_polygon"],
        perception_bonus=0.65,
        stability=0.6,
        resonance=1.0,
        abilities=["infinite_edge", "self_similar", "scale_invariant"],
        color=(230, 200, 150),
        vertices=0,  # Infinite
        edges=0,     # Infinite
    ),
    
    # === TRANSCENDENT ===
    "plane_transcendent": DimensionalForm(
        id="plane_transcendent",
        name="Transcendent Flat",
        short_name="Trans-Flat",
        dimension="2d",
        tier=DimensionTier.TRANSCENDENT,
        description="A 2D being sensing the third dimension - depth awaits.",
        lore="You have mastered the Plane. Every polygon, every curve, every fractal - you understand them all. And now... you sense thickness. A direction perpendicular to ALL directions you know. UP. The Volume calls.",
        philosophical_meaning="Complete mastery reveals new horizons - expertise opens doors.",
        xp_required=1800,
        requires_forms=["fractal_form"],
        perception_bonus=0.85,
        stability=1.0,
        resonance=1.0,
        abilities=["sense_3d", "prepare_depth", "planar_mastery"],
        color=(255, 220, 180),
        vertices=0,
        edges=0,
    ),
}


# =============================================================================
# 3D FORMS - The Solid Beings
# =============================================================================

FORMS_3D: Dict[str, DimensionalForm] = {
    # === NASCENT ===
    "newborn_solid": DimensionalForm(
        id="newborn_solid",
        name="Newborn Solid",
        short_name="Solid",
        dimension="3d",
        tier=DimensionTier.NASCENT,
        description="A being who has just perceived depth - UP and DOWN exist!",
        lore="DEPTH! VOLUME! You are no longer flat - you have THICKNESS. You can contain not just area, but SPACE. The flat plane you lived on was just the SURFACE of something vast. You see Volume, and reality expands.",
        philosophical_meaning="Each expansion reveals previous existence was a mere surface.",
        xp_required=0,
        perception_bonus=0.0,
        stability=0.5,
        resonance=0.5,
        abilities=["rise", "descend"],
        color=(200, 150, 150),
        vertices=0,
        edges=0,
    ),
    
    "tetrahedron": DimensionalForm(
        id="tetrahedron",
        name="Tetrahedron",
        short_name="Tetra",
        dimension="3d",
        tier=DimensionTier.NASCENT,
        description="The simplest solid - four vertices, six edges, four faces.",
        lore="Four points, four triangular faces. You are the simplest SOLID, the 3D equivalent of the triangle. You can contain volume. You have an inside that is truly THREE-DIMENSIONAL. You are fire made form.",
        philosophical_meaning="Simplicity in 3D - the minimum for volume enclosure.",
        xp_required=150,
        requires_forms=["newborn_solid"],
        perception_bonus=0.15,
        stability=0.7,
        resonance=0.6,
        abilities=["pierce_3d", "fire_aspect"],
        color=(210, 160, 160),
        vertices=4,
        edges=6,
    ),
    
    # === AWAKENED ===
    "cube_3d": DimensionalForm(
        id="cube_3d",
        name="Cube",
        short_name="Cube",
        dimension="3d",
        tier=DimensionTier.AWAKENED,
        description="Six square faces, the shape of earth and stability.",
        lore="You are order in three dimensions. Your faces are perfect squares. You tile 3D space completely. Buildings are made of you. You are the shape of civilization, of structure, of the grid that underlies reality.",
        philosophical_meaning="Structure extends through all dimensions - order is universal.",
        xp_required=350,
        requires_forms=["tetrahedron"],
        perception_bonus=0.25,
        stability=0.9,
        resonance=0.7,
        abilities=["tile_3d", "earth_aspect", "contain_volume"],
        color=(220, 170, 170),
        vertices=8,
        edges=12,
    ),
    
    "octahedron": DimensionalForm(
        id="octahedron",
        name="Octahedron",
        short_name="Octa",
        dimension="3d",
        tier=DimensionTier.AWAKENED,
        description="Eight triangular faces - the dual of the cube.",
        lore="You are the DUAL of the cube. Where the cube has vertices, you have faces. Where the cube has faces, you have vertices. You are the same shape seen from the inside. You are air made form.",
        philosophical_meaning="Duality - every structure has an inverse that is equally valid.",
        xp_required=450,
        requires_forms=["cube_3d"],
        perception_bonus=0.3,
        stability=0.8,
        resonance=0.8,
        abilities=["dual_sight", "air_aspect", "phase_dual"],
        color=(180, 180, 220),
        vertices=6,
        edges=12,
    ),
    
    # === ADEPT ===
    "dodecahedron": DimensionalForm(
        id="dodecahedron",
        name="Dodecahedron",
        short_name="Dodeca",
        dimension="3d",
        tier=DimensionTier.ADEPT,
        description="Twelve pentagonal faces - the shape of the cosmos.",
        lore="Twelve faces of pentagons - the golden ratio appears in your every measurement. The ancients believed the cosmos was shaped like you. You contain all other Platonic solids. You are the universe made form.",
        philosophical_meaning="Harmony and completeness - some forms contain all others.",
        xp_required=700,
        requires_forms=["octahedron"],
        perception_bonus=0.45,
        stability=0.85,
        resonance=0.9,
        abilities=["cosmic_resonance", "contain_platonic", "golden_form"],
        color=(200, 200, 180),
        vertices=20,
        edges=30,
    ),
    
    "icosahedron": DimensionalForm(
        id="icosahedron",
        name="Icosahedron",
        short_name="Icosa",
        dimension="3d",
        tier=DimensionTier.ADEPT,
        description="Twenty triangular faces - approaching the sphere.",
        lore="Twenty triangles, twenty faces of fire. You are the most complex regular solid that still tiles to form larger structures. Viruses take your shape. You are water made form, fluid yet structured.",
        philosophical_meaning="Maximum regular complexity - the boundary of structured simplicity.",
        xp_required=800,
        requires_forms=["dodecahedron"],
        perception_bonus=0.5,
        stability=0.75,
        resonance=0.95,
        abilities=["water_aspect", "viral_replication", "twenty_faces"],
        color=(180, 200, 220),
        vertices=12,
        edges=30,
    ),
    
    # === MASTER ===
    "sphere_3d": DimensionalForm(
        id="sphere_3d",
        name="Sphere",
        short_name="Sphere",
        dimension="3d",
        tier=DimensionTier.MASTER,
        description="Infinite faces, perfect symmetry in all directions.",
        lore="You have no vertices. You have no edges. You are the limit that all polyhedra approach. Every point on your surface is identical. You are the shape of planets, of bubbles, of the universe itself.",
        philosophical_meaning="Ultimate symmetry - all directions equal, all points the same.",
        xp_required=1200,
        requires_forms=["icosahedron"],
        perception_bonus=0.65,
        stability=0.7,
        resonance=1.0,
        abilities=["roll_3d", "perfect_symmetry", "contain_all"],
        color=(220, 220, 230),
        vertices=0,
        edges=0,
    ),
    
    "torus_3d": DimensionalForm(
        id="torus_3d",
        name="Torus",
        short_name="Torus",
        dimension="3d",
        tier=DimensionTier.MASTER,
        description="A donut shape - surface with a hole, genus one.",
        lore="You have a HOLE. Not a wound, but a fundamental property. You cannot be deformed into a sphere without cutting. You are topologically distinct. Your surface has paths that cannot be contracted to a point.",
        philosophical_meaning="Topology over geometry - what cannot be smoothed away is essential.",
        xp_required=1500,
        requires_forms=["sphere_3d"],
        perception_bonus=0.7,
        stability=0.8,
        resonance=0.9,
        abilities=["donut_roll", "genus_one", "non_contractible"],
        color=(230, 200, 200),
        vertices=0,
        edges=0,
    ),
    
    # === TRANSCENDENT ===
    "solid_transcendent": DimensionalForm(
        id="solid_transcendent",
        name="Transcendent Solid",
        short_name="Trans-Solid",
        dimension="3d",
        tier=DimensionTier.TRANSCENDENT,
        description="A 3D being sensing the fourth dimension - W awaits.",
        lore="You have mastered Volume. Every solid, every surface, every topology - you understand them all. And now... you sense ANOTHER direction. Perpendicular to all three you know. W. The Hyperspace calls.",
        philosophical_meaning="Three dimensions were never the end - there is always more.",
        xp_required=2200,
        requires_forms=["torus_3d"],
        perception_bonus=0.9,
        stability=1.0,
        resonance=1.0,
        abilities=["sense_4d", "prepare_hyperspace", "volumetric_mastery"],
        color=(255, 200, 200),
        vertices=0,
        edges=0,
    ),
}


# =============================================================================
# REGISTRY
# =============================================================================

ALL_DIMENSIONAL_FORMS: Dict[str, Dict[str, DimensionalForm]] = {
    "1d": FORMS_1D,
    "2d": FORMS_2D,
    "3d": FORMS_3D,
}


def get_forms_for_dimension(dimension: str) -> Dict[str, DimensionalForm]:
    """Get all forms for a dimension."""
    return ALL_DIMENSIONAL_FORMS.get(dimension, {})


def get_starting_form(dimension: str) -> Optional[DimensionalForm]:
    """Get the starting form for a dimension."""
    forms = get_forms_for_dimension(dimension)
    for form in forms.values():
        if form.xp_required == 0:
            return form
    return None


def get_available_forms(
    dimension: str,
    unlocked: Set[str],
    current_xp: int
) -> List[DimensionalForm]:
    """Get forms available for evolution."""
    forms = get_forms_for_dimension(dimension)
    available = []
    
    for form_id, form in forms.items():
        if form_id in unlocked:
            continue
        if current_xp < form.xp_required:
            continue
        if form.requires_forms and not all(r in unlocked for r in form.requires_forms):
            continue
        available.append(form)
    
    return available


def get_transcendent_form(dimension: str) -> Optional[DimensionalForm]:
    """Get the transcendent form for a dimension."""
    forms = get_forms_for_dimension(dimension)
    for form in forms.values():
        if form.tier == DimensionTier.TRANSCENDENT:
            return form
    return None
