"""Expanded 4D Evolution system with multiple shape families.

HyperSim has 30+ 4D shapes organized into families:
- Regular Polytopes (the classic 6)
- Uniform/Tesseract derivatives  
- 24-Cell family
- Prisms (3D shape extruded into 4D)
- Duoprisms (2D × 2D products)
- Exotic/Topological (non-convex, self-intersecting)
- Special constructions

Players can choose evolution paths and unlock different families!
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    pass


class ShapeFamily(Enum):
    """Families of 4D shapes."""
    REGULAR = "regular"           # The 6 convex regular polytopes
    UNIFORM = "uniform"           # Uniform polytopes (tesseract derivatives)
    CELL_24 = "cell_24"           # 24-cell family
    PRISM = "prism"               # 3D prisms extruded to 4D
    DUOPRISM = "duoprism"         # Products of 2D polygons
    EXOTIC = "exotic"             # Topological oddities
    SPECIAL = "special"           # Unique constructions
    TRANSCENDENT = "transcendent" # Beyond normal 4D


class ShapeRarity(Enum):
    """Rarity/power tier of shapes."""
    COMMON = 1
    UNCOMMON = 2
    RARE = 3
    EPIC = 4
    LEGENDARY = 5
    MYTHIC = 6


@dataclass
class Shape4D:
    """Definition of a 4D shape for evolution."""
    id: str
    name: str
    short_name: str
    family: ShapeFamily
    rarity: ShapeRarity
    
    # Geometry
    vertices: int
    edges: int
    faces: int
    cells: int
    cell_type: str = "mixed"
    
    # Description
    description: str = ""
    lore: str = ""
    
    # Requirements
    xp_required: int = 0
    requires_shapes: List[str] = field(default_factory=list)  # Must have evolved through these
    requires_dimension_mastery: int = 0  # Dimension order (0=1D, 3=4D)
    
    # Stats
    health_bonus: float = 0.0
    speed_bonus: float = 0.0
    w_perception: float = 1.0
    damage_reduction: float = 0.0
    ability_power: float = 1.0
    
    # Special abilities unlocked
    abilities: List[str] = field(default_factory=list)
    
    # Visual
    color: Tuple[int, int, int] = (200, 200, 255)
    glow: float = 0.5
    
    # Reference to HyperSim class
    hypersim_class: Optional[str] = None


# =============================================================================
# SHAPE DEFINITIONS - All 4D shapes from HyperSim
# =============================================================================

SHAPES_4D: Dict[str, Shape4D] = {
    # =========================================================================
    # REGULAR POLYTOPES - The Classic Six
    # =========================================================================
    "pentachoron": Shape4D(
        id="pentachoron",
        name="Pentachoron",
        short_name="5-Cell",
        family=ShapeFamily.REGULAR,
        rarity=ShapeRarity.COMMON,
        vertices=5, edges=10, faces=10, cells=5,
        cell_type="tetrahedron",
        description="The simplest regular 4D polytope. A 4D tetrahedron.",
        lore="In the beginning, there was the point. Then came the line, the triangle, the tetrahedron... and finally, the pentachoron. The first shape to truly exist in 4D.",
        xp_required=0,
        health_bonus=0, speed_bonus=2.0, w_perception=1.0,
        abilities=["ping_neighbors"],
        color=(100, 200, 255), glow=0.4,
        hypersim_class="Pentachoron",
    ),
    
    "hexadecachoron": Shape4D(
        id="hexadecachoron",
        name="Hexadecachoron",
        short_name="16-Cell",
        family=ShapeFamily.REGULAR,
        rarity=ShapeRarity.COMMON,
        vertices=8, edges=24, faces=32, cells=16,
        cell_type="tetrahedron",
        description="The 4D cross-polytope. Sharp, precise, dual to the tesseract.",
        lore="Where the tesseract sprawls outward in cubic abundance, the hexadecachoron pierces inward with tetrahedral precision. They are two faces of the same 4D coin.",
        xp_required=100,
        requires_shapes=["pentachoron"],
        health_bonus=20, speed_bonus=1.5, w_perception=1.5,
        damage_reduction=0.05,
        abilities=["dash"],
        color=(120, 180, 255), glow=0.5,
        hypersim_class="SixteenCell",
    ),
    
    "tesseract": Shape4D(
        id="tesseract",
        name="Tesseract",
        short_name="8-Cell",
        family=ShapeFamily.REGULAR,
        rarity=ShapeRarity.UNCOMMON,
        vertices=16, edges=32, faces=24, cells=8,
        cell_type="cube",
        description="The legendary hypercube. Eight cubes folded through 4D space.",
        lore="The tesseract is perhaps the most famous 4D object. Its shadow confounds 3D minds - a cube within a cube, connected at impossible angles. Yet in 4D, it is as natural as breathing.",
        xp_required=300,
        requires_shapes=["hexadecachoron"],
        health_bonus=50, speed_bonus=1.0, w_perception=2.0,
        damage_reduction=0.10, ability_power=1.1,
        abilities=["rotate_hyperplanes"],
        color=(150, 150, 255), glow=0.6,
        hypersim_class="Hypercube",
    ),
    
    "icositetrachoron": Shape4D(
        id="icositetrachoron",
        name="Icositetrachoron",
        short_name="24-Cell",
        family=ShapeFamily.REGULAR,
        rarity=ShapeRarity.RARE,
        vertices=24, edges=96, faces=96, cells=24,
        cell_type="octahedron",
        description="The self-dual 24-cell. EXISTS ONLY IN 4D - no analog in any other dimension!",
        lore="The 24-cell is a miracle of geometry. Self-dual, perfectly symmetric, and utterly unique to four dimensions. Those who achieve this form report a strange sensation of being their own reflection.",
        xp_required=600,
        requires_shapes=["tesseract"],
        health_bonus=80, speed_bonus=1.2, w_perception=3.0,
        damage_reduction=0.15, ability_power=1.2,
        abilities=["stabilize_lower", "spawn_slices"],
        color=(180, 120, 255), glow=0.7,
        hypersim_class="TwentyFourCell",
    ),
    
    "hecatonicosachoron": Shape4D(
        id="hecatonicosachoron",
        name="Hecatonicosachoron",
        short_name="120-Cell",
        family=ShapeFamily.REGULAR,
        rarity=ShapeRarity.EPIC,
        vertices=600, edges=1200, faces=720, cells=120,
        cell_type="dodecahedron",
        description="An immense structure of 120 dodecahedral cells. Approaching geometric transcendence.",
        lore="The 120-cell is a cosmos unto itself. Each of its 120 dodecahedral chambers could contain a universe. Those who achieve this form speak of hearing music in the geometry.",
        xp_required=1200,
        requires_shapes=["icositetrachoron"],
        health_bonus=120, speed_bonus=0.8, w_perception=4.0,
        damage_reduction=0.20, ability_power=1.4,
        abilities=["fold_line", "carry_line"],
        color=(200, 100, 255), glow=0.85,
        hypersim_class="OneHundredTwentyCell",
    ),
    
    "hexacosichoron": Shape4D(
        id="hexacosichoron",
        name="Hexacosichoron",
        short_name="600-Cell",
        family=ShapeFamily.REGULAR,
        rarity=ShapeRarity.LEGENDARY,
        vertices=120, edges=720, faces=1200, cells=600,
        cell_type="tetrahedron",
        description="The ultimate regular polytope. 600 tetrahedra in perfect harmony.",
        lore="To become the 600-cell is to achieve perfect geometric enlightenment. Every vertex touches 20 others. Every edge is shared by 5 cells. The mathematics sing.",
        xp_required=2500,
        requires_shapes=["hecatonicosachoron"],
        health_bonus=150, speed_bonus=1.5, w_perception=5.0,
        damage_reduction=0.25, ability_power=1.6,
        abilities=[],  # Has all abilities
        color=(255, 150, 255), glow=1.0,
        hypersim_class="SixHundredCell",
    ),
    
    # =========================================================================
    # UNIFORM POLYTOPES - Tesseract Derivatives
    # =========================================================================
    "rectified_tesseract": Shape4D(
        id="rectified_tesseract",
        name="Rectified Tesseract",
        short_name="Rectified 8-Cell",
        family=ShapeFamily.UNIFORM,
        rarity=ShapeRarity.UNCOMMON,
        vertices=32, edges=96, faces=88, cells=24,
        cell_type="cuboctahedron/tetrahedron",
        description="The tesseract with vertices cut to edge midpoints. A bridge between forms.",
        lore="Rectification reveals hidden symmetries. The tesseract's harsh corners soften into something more fluid, more alive.",
        xp_required=400,
        requires_shapes=["tesseract"],
        health_bonus=40, speed_bonus=1.3, w_perception=2.2,
        damage_reduction=0.08, ability_power=1.15,
        abilities=["phase_shift"],
        color=(140, 180, 220), glow=0.55,
        hypersim_class="RectifiedTesseract",
    ),
    
    "truncated_tesseract": Shape4D(
        id="truncated_tesseract",
        name="Truncated Tesseract",
        short_name="Truncated 8-Cell",
        family=ShapeFamily.UNIFORM,
        rarity=ShapeRarity.UNCOMMON,
        vertices=64, edges=128, faces=88, cells=24,
        cell_type="truncated cube/tetrahedron",
        description="The tesseract with corners sliced away. Softer but still powerful.",
        lore="Truncation teaches humility. The perfect cube surrenders its vertices to become something gentler, yet no less beautiful.",
        xp_required=450,
        requires_shapes=["tesseract"],
        health_bonus=55, speed_bonus=1.1, w_perception=2.1,
        damage_reduction=0.12,
        abilities=["shield_burst"],
        color=(160, 160, 230), glow=0.58,
        hypersim_class="TruncatedTesseract",
    ),
    
    "cantellated_tesseract": Shape4D(
        id="cantellated_tesseract",
        name="Cantellated Tesseract",
        short_name="Cantellated 8-Cell",
        family=ShapeFamily.UNIFORM,
        rarity=ShapeRarity.RARE,
        vertices=96, edges=256, faces=216, cells=56,
        cell_type="rhombicuboctahedron/tetrahedron/cube",
        description="Edges and faces expanded outward. A complex, beautiful form.",
        lore="Cantellation stretches space itself. The tesseract blooms outward like a geometric flower.",
        xp_required=700,
        requires_shapes=["rectified_tesseract"],
        health_bonus=70, speed_bonus=0.9, w_perception=2.5,
        damage_reduction=0.14, ability_power=1.25,
        abilities=["gravity_well"],
        color=(170, 140, 240), glow=0.65,
        hypersim_class="CantellatedTesseract",
    ),
    
    "bitruncated_tesseract": Shape4D(
        id="bitruncated_tesseract",
        name="Bitruncated Tesseract",
        short_name="Bitruncated 8-Cell",
        family=ShapeFamily.UNIFORM,
        rarity=ShapeRarity.RARE,
        vertices=96, edges=192, faces=120, cells=24,
        cell_type="truncated octahedron",
        description="Truncated from both dual perspectives. Perfectly balanced.",
        lore="The bitruncated tesseract sees both the cube and its dual simultaneously. It exists in a state of geometric superposition.",
        xp_required=750,
        requires_shapes=["truncated_tesseract"],
        health_bonus=65, speed_bonus=1.0, w_perception=2.8,
        damage_reduction=0.13,
        abilities=["dual_vision"],
        color=(180, 130, 220), glow=0.68,
        hypersim_class="BitruncatedTesseract",
    ),
    
    "runcinated_tesseract": Shape4D(
        id="runcinated_tesseract",
        name="Runcinated Tesseract",
        short_name="Runcinated 8-Cell",
        family=ShapeFamily.UNIFORM,
        rarity=ShapeRarity.RARE,
        vertices=64, edges=192, faces=192, cells=80,
        cell_type="cube/tetrahedron/triangular prism",
        description="Cells pulled apart and connected by prisms. Expanded and intricate.",
        lore="Runcination pulls the tesseract's cells apart, revealing the spaces between. What was solid becomes porous, interconnected.",
        xp_required=800,
        requires_shapes=["tesseract"],
        health_bonus=75, speed_bonus=1.1, w_perception=2.6,
        damage_reduction=0.15,
        abilities=["cell_hop"],
        color=(190, 150, 210), glow=0.7,
        hypersim_class="RuncinatedTesseract",
    ),
    
    "omnitruncated_tesseract": Shape4D(
        id="omnitruncated_tesseract",
        name="Omnitruncated Tesseract",
        short_name="Omnitruncated 8-Cell",
        family=ShapeFamily.UNIFORM,
        rarity=ShapeRarity.EPIC,
        vertices=384, edges=768, faces=464, cells=80,
        cell_type="great rhombicuboctahedron/truncated tetrahedron/hexagonal prism/cube",
        description="Maximum truncation. Every possible cut applied. Geometric maximalism.",
        lore="The omnitruncated tesseract holds nothing back. Every symmetry operation has been applied. It is geometry without restraint.",
        xp_required=1500,
        requires_shapes=["cantellated_tesseract", "bitruncated_tesseract"],
        health_bonus=100, speed_bonus=0.7, w_perception=3.5,
        damage_reduction=0.22, ability_power=1.5,
        abilities=["omni_shield", "truncation_wave"],
        color=(220, 120, 255), glow=0.9,
        hypersim_class="OmnitruncatedTesseract",
    ),
    
    # =========================================================================
    # 24-CELL FAMILY
    # =========================================================================
    "snub_24_cell": Shape4D(
        id="snub_24_cell",
        name="Snub 24-Cell",
        short_name="Snub 24-Cell",
        family=ShapeFamily.CELL_24,
        rarity=ShapeRarity.EPIC,
        vertices=96, edges=432, faces=480, cells=144,
        cell_type="icosahedron/tetrahedron/triangular prism",
        description="The 24-cell twisted and snubbed. Chiral and beautiful.",
        lore="The snub 24-cell is the 24-cell given a twist - literally. It comes in left-handed and right-handed forms, mirror images that can never align.",
        xp_required=1100,
        requires_shapes=["icositetrachoron"],
        health_bonus=90, speed_bonus=1.4, w_perception=3.2,
        damage_reduction=0.16, ability_power=1.35,
        abilities=["chiral_shift", "mirror_form"],
        color=(150, 200, 255), glow=0.8,
        hypersim_class="Snub24Cell",
    ),
    
    "rectified_24_cell": Shape4D(
        id="rectified_24_cell",
        name="Rectified 24-Cell",
        short_name="Rectified 24-Cell",
        family=ShapeFamily.CELL_24,
        rarity=ShapeRarity.RARE,
        vertices=96, edges=288, faces=240, cells=48,
        cell_type="cube/cuboctahedron",
        description="Also called the Tesseractihexadecachoron. The 24-cell rectified.",
        lore="Rectifying the already-perfect 24-cell produces something unexpected: a form where cubes and cuboctahedra dance together in impossible harmony.",
        xp_required=900,
        requires_shapes=["icositetrachoron"],
        health_bonus=85, speed_bonus=1.0, w_perception=3.0,
        damage_reduction=0.14,
        abilities=["cubical_shield"],
        color=(160, 180, 250), glow=0.72,
        hypersim_class="Rectified24Cell",
    ),
    
    # =========================================================================
    # SPECIAL POLYTOPES
    # =========================================================================
    "grand_antiprism": Shape4D(
        id="grand_antiprism",
        name="Grand Antiprism",
        short_name="Grand Antiprism",
        family=ShapeFamily.SPECIAL,
        rarity=ShapeRarity.LEGENDARY,
        vertices=100, edges=500, faces=720, cells=320,
        cell_type="tetrahedron/pentagonal antiprism",
        description="A unique uniform polytope. Two rings of 10 antiprisms connected by 300 tetrahedra.",
        lore="The Grand Antiprism defies easy classification. It is uniform but not regular, beautiful but strange. Its dual rings spin through 4D space in eternal opposition.",
        xp_required=2000,
        requires_shapes=["snub_24_cell"],
        health_bonus=130, speed_bonus=1.3, w_perception=4.2,
        damage_reduction=0.23, ability_power=1.55,
        abilities=["ring_dance", "antiprism_spin"],
        color=(255, 180, 200), glow=0.95,
        hypersim_class="GrandAntiprism",
    ),
    
    "disphenoidal_288_cell": Shape4D(
        id="disphenoidal_288_cell",
        name="Disphenoidal 288-Cell",
        short_name="288-Cell",
        family=ShapeFamily.SPECIAL,
        rarity=ShapeRarity.MYTHIC,
        vertices=48, edges=336, faces=576, cells=288,
        cell_type="tetragonal disphenoid",
        description="The dual of the bitruncated 24-cell. 288 disphenoidal cells in perfect array.",
        lore="Few beings ever achieve the 288-cell form. Its cells are disphenoids - tetrahedra stretched and warped into something alien yet beautiful.",
        xp_required=3500,
        requires_shapes=["grand_antiprism", "hexacosichoron"],
        health_bonus=180, speed_bonus=1.0, w_perception=5.5,
        damage_reduction=0.30, ability_power=1.8,
        abilities=["disphenoid_storm", "cell_multiplication"],
        color=(255, 220, 150), glow=1.0,
        hypersim_class="Disphenoidal288Cell",
    ),
    
    # =========================================================================
    # PRISMS - 3D shapes extruded into 4D
    # =========================================================================
    "tetrahedral_prism": Shape4D(
        id="tetrahedral_prism",
        name="Tetrahedral Prism",
        short_name="Tetra Prism",
        family=ShapeFamily.PRISM,
        rarity=ShapeRarity.COMMON,
        vertices=8, edges=16, faces=14, cells=6,
        cell_type="tetrahedron/triangular prism",
        description="A tetrahedron extruded along the W axis. Simple but versatile.",
        lore="The prism forms are bridges between 3D and 4D. The tetrahedral prism remembers its simplex origins while reaching into the fourth dimension.",
        xp_required=150,
        requires_dimension_mastery=3,
        health_bonus=15, speed_bonus=1.8, w_perception=1.2,
        abilities=["extrude"],
        color=(200, 150, 150), glow=0.35,
        hypersim_class="TetraPrism",
    ),
    
    "cubic_prism": Shape4D(
        id="cubic_prism",
        name="Cubic Prism",
        short_name="Cube Prism",
        family=ShapeFamily.PRISM,
        rarity=ShapeRarity.COMMON,
        vertices=16, edges=32, faces=24, cells=8,
        cell_type="cube/square prism",
        description="A cube extruded into 4D. Halfway between cube and tesseract.",
        lore="The cubic prism is what you get when a cube dreams of becoming a tesseract. It reaches into W but hasn't fully committed.",
        xp_required=200,
        requires_dimension_mastery=3,
        health_bonus=25, speed_bonus=1.5, w_perception=1.4,
        abilities=["w_stretch"],
        color=(180, 180, 160), glow=0.4,
        hypersim_class="CubePrism",
    ),
    
    "octahedral_prism": Shape4D(
        id="octahedral_prism",
        name="Octahedral Prism",
        short_name="Octa Prism",
        family=ShapeFamily.PRISM,
        rarity=ShapeRarity.UNCOMMON,
        vertices=12, edges=28, faces=26, cells=10,
        cell_type="octahedron/triangular prism",
        description="An octahedron stretched through 4D space.",
        lore="Sharp and angular, the octahedral prism cuts through dimensions with its pointed vertices.",
        xp_required=250,
        requires_shapes=["tetrahedral_prism"],
        health_bonus=30, speed_bonus=1.6, w_perception=1.5,
        damage_reduction=0.05,
        abilities=["pierce"],
        color=(160, 200, 180), glow=0.45,
        hypersim_class="OctaPrism",
    ),
    
    "icosahedral_prism": Shape4D(
        id="icosahedral_prism",
        name="Icosahedral Prism",
        short_name="Icosa Prism",
        family=ShapeFamily.PRISM,
        rarity=ShapeRarity.RARE,
        vertices=24, edges=60, faces=62, cells=22,
        cell_type="icosahedron/pentagonal prism",
        description="An icosahedron extended into the fourth dimension.",
        lore="Twenty triangular faces become twenty triangular prisms, capped by icosahedra. The golden ratio echoes through 4D.",
        xp_required=500,
        requires_shapes=["octahedral_prism"],
        health_bonus=60, speed_bonus=1.2, w_perception=2.0,
        damage_reduction=0.10,
        abilities=["golden_resonance"],
        color=(220, 200, 100), glow=0.6,
        hypersim_class="IcosaPrism",
    ),
    
    "dodecahedral_prism": Shape4D(
        id="dodecahedral_prism",
        name="Dodecahedral Prism",
        short_name="Dodeca Prism",
        family=ShapeFamily.PRISM,
        rarity=ShapeRarity.RARE,
        vertices=40, edges=90, faces=64, cells=14,
        cell_type="dodecahedron/pentagonal prism",
        description="A dodecahedron reaching into the fourth dimension.",
        lore="Twelve pentagonal faces, each becoming a pentagonal prism. The dodecahedral prism whispers of the 120-cell to come.",
        xp_required=550,
        requires_shapes=["icosahedral_prism"],
        health_bonus=65, speed_bonus=1.0, w_perception=2.2,
        damage_reduction=0.11,
        abilities=["pentagonal_shield"],
        color=(200, 180, 220), glow=0.62,
        hypersim_class="DodecaPrism",
    ),
    
    # =========================================================================
    # DUOPRISMS - Products of 2D polygons
    # =========================================================================
    "square_duoprism": Shape4D(
        id="square_duoprism",
        name="Square Duoprism",
        short_name="4-4 Duoprism",
        family=ShapeFamily.DUOPRISM,
        rarity=ShapeRarity.UNCOMMON,
        vertices=16, edges=32, faces=24, cells=8,
        cell_type="square prism",
        description="A 4×4 duoprism. Two perpendicular rings of 4 cubes each.",
        lore="The duoprisms are products of lower-dimensional shapes. The square duoprism is four dimensions trying to be two dimensions twice.",
        xp_required=350,
        requires_dimension_mastery=3,
        health_bonus=35, speed_bonus=1.3, w_perception=1.8,
        abilities=["duo_spin"],
        color=(180, 200, 180), glow=0.5,
        hypersim_class="Duoprism",
    ),
    
    "hexagonal_duoprism": Shape4D(
        id="hexagonal_duoprism",
        name="Hexagonal Duoprism",
        short_name="6-6 Duoprism",
        family=ShapeFamily.DUOPRISM,
        rarity=ShapeRarity.RARE,
        vertices=36, edges=72, faces=48, cells=12,
        cell_type="hexagonal prism",
        description="A 6×6 duoprism. Two rings of 6 hexagonal prisms each.",
        lore="The hexagonal duoprism tiles space efficiently in two perpendicular planes. It is geometry's answer to multitasking.",
        xp_required=600,
        requires_shapes=["square_duoprism"],
        health_bonus=55, speed_bonus=1.1, w_perception=2.3,
        damage_reduction=0.08,
        abilities=["hex_field"],
        color=(200, 220, 160), glow=0.58,
        hypersim_class="Duoprism",
    ),
    
    # =========================================================================
    # EXOTIC SHAPES - Topological oddities
    # =========================================================================
    "clifford_torus": Shape4D(
        id="clifford_torus",
        name="Clifford Torus",
        short_name="Clifford Torus",
        family=ShapeFamily.EXOTIC,
        rarity=ShapeRarity.EPIC,
        vertices=0, edges=0, faces=0, cells=0,  # Continuous surface
        cell_type="surface",
        description="A flat torus embedded in 4D. Zero curvature despite being toroidal!",
        lore="The Clifford Torus is a mathematical miracle - a donut shape with no curvature. It lives on the 3-sphere, a place where parallel lines can meet.",
        xp_required=1400,
        requires_shapes=["icositetrachoron"],
        health_bonus=95, speed_bonus=1.5, w_perception=3.8,
        damage_reduction=0.18, ability_power=1.4,
        abilities=["flat_wrap", "torus_tunnel"],
        color=(100, 255, 200), glow=0.88,
        hypersim_class="CliffordTorus",
    ),
    
    "spherinder": Shape4D(
        id="spherinder",
        name="Spherinder",
        short_name="Spherinder",
        family=ShapeFamily.EXOTIC,
        rarity=ShapeRarity.RARE,
        vertices=0, edges=0, faces=0, cells=2,  # 2 spherical cells
        cell_type="sphere/curved",
        description="A sphere crossed with a line. The 4D equivalent of a cylinder.",
        lore="The spherinder is what happens when infinity meets roundness. Its two spherical caps are connected by an infinite curved surface.",
        xp_required=700,
        requires_dimension_mastery=3,
        health_bonus=60, speed_bonus=1.0, w_perception=2.5,
        damage_reduction=0.12,
        abilities=["roll_4d"],
        color=(255, 200, 200), glow=0.6,
        hypersim_class="Spherinder",
    ),
    
    "klein_bottle_4d": Shape4D(
        id="klein_bottle_4d",
        name="Klein Bottle",
        short_name="Klein Bottle",
        family=ShapeFamily.EXOTIC,
        rarity=ShapeRarity.LEGENDARY,
        vertices=0, edges=0, faces=0, cells=0,
        cell_type="non-orientable surface",
        description="A non-orientable surface that can only exist properly in 4D. Has no inside or outside.",
        lore="The Klein Bottle defies understanding. It passes through itself without intersection, having no boundary, no inside, no outside. It simply IS.",
        xp_required=2200,
        requires_shapes=["clifford_torus"],
        health_bonus=140, speed_bonus=1.2, w_perception=4.5,
        damage_reduction=0.24, ability_power=1.6,
        abilities=["non_orientable", "boundary_dissolve"],
        color=(150, 100, 255), glow=0.95,
        hypersim_class="KleinBottle4D",
    ),
    
    "mobius_4d": Shape4D(
        id="mobius_4d",
        name="4D Möbius Strip",
        short_name="Möbius 4D",
        family=ShapeFamily.EXOTIC,
        rarity=ShapeRarity.EPIC,
        vertices=0, edges=0, faces=0, cells=0,
        cell_type="non-orientable surface",
        description="The Möbius strip extended into 4D. Even stranger than its 3D cousin.",
        lore="In 4D, the Möbius strip gains new dimensions of strangeness. Walk along it and you return... but not quite where you started.",
        xp_required=1300,
        requires_shapes=["spherinder"],
        health_bonus=85, speed_bonus=1.4, w_perception=3.4,
        damage_reduction=0.17,
        abilities=["twist_space"],
        color=(255, 150, 100), glow=0.82,
        hypersim_class="Mobius4D",
    ),
    
    "hopf_link_4d": Shape4D(
        id="hopf_link_4d",
        name="Hopf Link",
        short_name="Hopf Link",
        family=ShapeFamily.EXOTIC,
        rarity=ShapeRarity.EPIC,
        vertices=0, edges=0, faces=0, cells=0,
        cell_type="linked circles",
        description="Two circles linked in 4D. They cannot be separated without breaking one.",
        lore="The Hopf Link is love made geometric - two circles eternally intertwined, unable to part, yet never truly touching.",
        xp_required=1350,
        requires_shapes=["clifford_torus"],
        health_bonus=88, speed_bonus=1.3, w_perception=3.5,
        damage_reduction=0.16,
        abilities=["link_bind", "circle_dance"],
        color=(255, 100, 255), glow=0.85,
        hypersim_class="HopfLink4D",
    ),
    
    "torus_knot_4d": Shape4D(
        id="torus_knot_4d",
        name="4D Torus Knot",
        short_name="Torus Knot",
        family=ShapeFamily.EXOTIC,
        rarity=ShapeRarity.LEGENDARY,
        vertices=0, edges=0, faces=0, cells=0,
        cell_type="knotted curve",
        description="A mathematical knot wound around a torus in 4D space.",
        lore="The 4D torus knot ties space itself into loops. It is mathematics becoming art, complexity becoming beauty.",
        xp_required=2400,
        requires_shapes=["hopf_link_4d", "mobius_4d"],
        health_bonus=145, speed_bonus=1.1, w_perception=4.8,
        damage_reduction=0.26, ability_power=1.65,
        abilities=["knot_trap", "torus_navigation"],
        color=(200, 255, 150), glow=0.98,
        hypersim_class="TorusKnot4D",
    ),
    
    # =========================================================================
    # TRANSCENDENT - Beyond normal 4D
    # =========================================================================
    "penteract_frame": Shape4D(
        id="penteract_frame",
        name="Penteract Frame",
        short_name="5D Frame",
        family=ShapeFamily.TRANSCENDENT,
        rarity=ShapeRarity.MYTHIC,
        vertices=32, edges=80, faces=0, cells=0,
        cell_type="5D wireframe",
        description="The wireframe of a 5D hypercube. A glimpse beyond 4D.",
        lore="The Penteract Frame is not truly a 4D shape - it is the shadow of a 5D shadow. Those who achieve this form touch the infinite.",
        xp_required=5000,
        requires_shapes=["hexacosichoron", "disphenoidal_288_cell", "torus_knot_4d"],
        health_bonus=200, speed_bonus=2.0, w_perception=10.0,
        damage_reduction=0.35, ability_power=2.0,
        abilities=["fifth_glimpse", "dimension_bridge", "infinite_recursion"],
        color=(255, 255, 255), glow=1.0,
        hypersim_class="PenteractFrame",
    ),
}


# =============================================================================
# EVOLUTION PATHS - Suggested routes through the shape families
# =============================================================================

EVOLUTION_PATHS = {
    "classic": {
        "name": "Classic Regular Path",
        "description": "The traditional journey through the 6 regular polytopes.",
        "shapes": ["pentachoron", "hexadecachoron", "tesseract", "icositetrachoron", "hecatonicosachoron", "hexacosichoron"],
    },
    "uniform": {
        "name": "Uniform Mastery",
        "description": "Master the tesseract and all its truncated forms.",
        "shapes": ["tesseract", "rectified_tesseract", "truncated_tesseract", "cantellated_tesseract", "bitruncated_tesseract", "runcinated_tesseract", "omnitruncated_tesseract"],
    },
    "exotic": {
        "name": "Exotic Topology",
        "description": "Explore non-orientable surfaces and strange topologies.",
        "shapes": ["spherinder", "clifford_torus", "mobius_4d", "hopf_link_4d", "klein_bottle_4d", "torus_knot_4d"],
    },
    "prism": {
        "name": "Prism Ascension",
        "description": "Start with prisms and build understanding of 4D extension.",
        "shapes": ["tetrahedral_prism", "cubic_prism", "octahedral_prism", "icosahedral_prism", "dodecahedral_prism"],
    },
    "ultimate": {
        "name": "Ultimate Transcendence",
        "description": "Achieve the most powerful forms across all families.",
        "shapes": ["hexacosichoron", "omnitruncated_tesseract", "grand_antiprism", "disphenoidal_288_cell", "torus_knot_4d", "penteract_frame"],
    },
}


def get_available_shapes(unlocked: Set[str], current_xp: int) -> List[Shape4D]:
    """Get shapes available for evolution based on current progress."""
    available = []
    for shape_id, shape in SHAPES_4D.items():
        if shape_id in unlocked:
            continue
        
        # Check XP
        if current_xp < shape.xp_required:
            continue
        
        # Check prerequisites
        if shape.requires_shapes:
            if not all(req in unlocked for req in shape.requires_shapes):
                continue
        
        available.append(shape)
    
    return available


def get_shapes_by_family(family: ShapeFamily) -> List[Shape4D]:
    """Get all shapes in a family."""
    return [s for s in SHAPES_4D.values() if s.family == family]


def get_shapes_by_rarity(rarity: ShapeRarity) -> List[Shape4D]:
    """Get all shapes of a rarity tier."""
    return [s for s in SHAPES_4D.values() if s.rarity == rarity]
