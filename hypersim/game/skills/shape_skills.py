"""Shape-specific skills based on 4D mathematical properties.

Each shape family has unique skills derived from their geometry:
- Regular: Classic attacks based on symmetry
- Uniform: Truncation-based effects
- 24-Cell: Self-dual and unique abilities
- Prism: Extension and projection skills
- Duoprism: Dual-ring attacks
- Exotic: Topological manipulation
- Transcendent: Higher-dimensional glimpses
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .skill_system import Skill, SkillType, SkillTarget, SkillEffect


# =============================================================================
# REGULAR POLYTOPE SKILLS
# =============================================================================

PENTACHORON_SKILLS = [
    Skill(
        id="simplex_pierce",
        name="Simplex Pierce",
        description="Strike with the sharp vertex of the simplest 4D form.",
        skill_type=SkillType.ATTACK,
        target=SkillTarget.SINGLE_ENEMY,
        cooldown=2.0,
        damage=25.0,
        range=8.0,
        effects=[SkillEffect.DAMAGE],
        color=(100, 200, 255),
        math_basis="The 5-cell has 5 vertices pointing in maximally separated directions - perfect for piercing attacks.",
    ),
    Skill(
        id="tetrahedral_shield",
        name="Tetrahedral Shield",
        description="Form a protective tetrahedron around yourself.",
        skill_type=SkillType.DEFENSE,
        target=SkillTarget.SELF,
        cooldown=8.0,
        duration=4.0,
        effects=[SkillEffect.SHIELD],
        damage=50.0,  # Shield amount
        color=(100, 200, 255),
        math_basis="Each cell of the 5-cell is a tetrahedron - the most stable 3D structure.",
    ),
]

HEXADECACHORON_SKILLS = [
    Skill(
        id="cross_slash",
        name="Cross Slash",
        description="Attack along all 4 axes simultaneously.",
        skill_type=SkillType.ATTACK,
        target=SkillTarget.AREA,
        cooldown=4.0,
        damage=35.0,
        area_radius=6.0,
        effects=[SkillEffect.DAMAGE],
        color=(120, 180, 255),
        math_basis="The 16-cell is the 4D cross-polytope - vertices at ±1 on each axis.",
    ),
    Skill(
        id="orthogonal_dodge",
        name="Orthogonal Dodge",
        description="Phase into a perpendicular dimension to avoid attacks.",
        skill_type=SkillType.MOVEMENT,
        target=SkillTarget.SELF,
        cooldown=3.0,
        duration=1.5,
        effects=[SkillEffect.PHASE],
        color=(120, 180, 255),
        math_basis="The 16-cell's vertices lie on coordinate axes - moving along one doesn't affect the others.",
    ),
]

TESSERACT_SKILLS = [
    Skill(
        id="cubic_crush",
        name="Cubic Crush",
        description="Compress space using all 8 cubic cells.",
        skill_type=SkillType.ATTACK,
        target=SkillTarget.SINGLE_ENEMY,
        cooldown=5.0,
        damage=50.0,
        range=10.0,
        effects=[SkillEffect.DAMAGE, SkillEffect.STUN],
        duration=1.0,
        color=(150, 150, 255),
        math_basis="The tesseract contains 8 cubes - compressing them crushes everything inside.",
    ),
    Skill(
        id="hypercube_barrier",
        name="Hypercube Barrier",
        description="Create an impenetrable cubic barrier in 4D.",
        skill_type=SkillType.DEFENSE,
        target=SkillTarget.SELF,
        cooldown=12.0,
        duration=5.0,
        effects=[SkillEffect.SHIELD],
        damage=100.0,
        color=(150, 150, 255),
        math_basis="The tesseract's 8 cells form a closed hypersurface - nothing can pass through.",
    ),
    Skill(
        id="vertex_warp",
        name="Vertex Warp",
        description="Teleport to any of the tesseract's 16 vertex positions.",
        skill_type=SkillType.MOVEMENT,
        target=SkillTarget.SELF,
        cooldown=6.0,
        range=15.0,
        effects=[SkillEffect.TELEPORT],
        color=(150, 150, 255),
        math_basis="The tesseract has 16 vertices at (±1,±1,±1,±1) - perfect teleport destinations.",
    ),
]

ICOSITETRACHORON_SKILLS = [
    Skill(
        id="self_dual_resonance",
        name="Self-Dual Resonance",
        description="Being self-dual, damage yourself to damage enemies more.",
        skill_type=SkillType.ATTACK,
        target=SkillTarget.ALL_ENEMIES,
        cooldown=10.0,
        damage=80.0,
        area_radius=12.0,
        effects=[SkillEffect.DAMAGE],
        color=(180, 120, 255),
        math_basis="The 24-cell is self-dual - it equals its own dual. This creates a resonance that amplifies all effects.",
    ),
    Skill(
        id="octahedral_reflection",
        name="Octahedral Reflection",
        description="Reflect incoming attacks using octahedral cells.",
        skill_type=SkillType.DEFENSE,
        target=SkillTarget.SELF,
        cooldown=5.0,
        duration=2.0,
        effects=[SkillEffect.SHIELD],
        damage=75.0,
        color=(180, 120, 255),
        math_basis="The 24-cell's 24 octahedral cells create a perfect reflective surface.",
    ),
    Skill(
        id="unique_existence",
        name="Unique Existence",
        description="As the only self-dual in 4D, become briefly invincible.",
        skill_type=SkillType.ULTIMATE,
        target=SkillTarget.SELF,
        cooldown=30.0,
        duration=3.0,
        effects=[SkillEffect.PHASE, SkillEffect.SHIELD],
        damage=200.0,
        color=(200, 150, 255),
        math_basis="The 24-cell exists ONLY in 4D with no analog elsewhere. This uniqueness grants temporary transcendence.",
    ),
]

HECATONICOSACHORON_SKILLS = [
    Skill(
        id="dodecahedral_storm",
        name="Dodecahedral Storm",
        description="Unleash 120 dodecahedral cells as projectiles.",
        skill_type=SkillType.ATTACK,
        target=SkillTarget.AREA,
        cooldown=8.0,
        damage=60.0,
        area_radius=15.0,
        effects=[SkillEffect.DAMAGE, SkillEffect.KNOCKBACK],
        color=(200, 100, 255),
        math_basis="The 120-cell has 120 dodecahedral cells - each can be launched independently.",
    ),
    Skill(
        id="golden_ratio_harmony",
        name="Golden Ratio Harmony",
        description="The φ ratio heals and strengthens.",
        skill_type=SkillType.UTILITY,
        target=SkillTarget.SELF,
        cooldown=15.0,
        heal=100.0,
        duration=10.0,
        effects=[SkillEffect.HEAL],
        color=(255, 200, 100),
        math_basis="The dodecahedron embodies the golden ratio φ - a proportion of perfect harmony.",
    ),
]

HEXACOSICHORON_SKILLS = [
    Skill(
        id="six_hundred_strike",
        name="Six Hundred Strike",
        description="Attack 600 times in rapid succession.",
        skill_type=SkillType.ATTACK,
        target=SkillTarget.SINGLE_ENEMY,
        cooldown=12.0,
        damage=150.0,  # Total damage
        range=8.0,
        effects=[SkillEffect.DAMAGE],
        color=(255, 150, 255),
        math_basis="The 600-cell has 600 tetrahedral cells - each one strikes.",
    ),
    Skill(
        id="vertex_constellation",
        name="Vertex Constellation",
        description="120 vertices create a constellation of damage points.",
        skill_type=SkillType.ATTACK,
        target=SkillTarget.AREA,
        cooldown=15.0,
        damage=100.0,
        area_radius=20.0,
        effects=[SkillEffect.DAMAGE],
        color=(255, 150, 255),
        math_basis="The 600-cell's 120 vertices form a 4D constellation of attack points.",
    ),
    Skill(
        id="geometric_perfection",
        name="Geometric Perfection",
        description="Achieve perfect form - massive stat boost.",
        skill_type=SkillType.ULTIMATE,
        target=SkillTarget.SELF,
        cooldown=45.0,
        duration=8.0,
        effects=[SkillEffect.SHIELD, SkillEffect.HEAL],
        damage=150.0,
        heal=100.0,
        color=(255, 200, 255),
        math_basis="The 600-cell represents the pinnacle of 4D regular geometry - perfect in every way.",
    ),
]

# =============================================================================
# UNIFORM POLYTOPE SKILLS (Tesseract Derivatives)
# =============================================================================

UNIFORM_SKILLS = [
    Skill(
        id="truncation_blast",
        name="Truncation Blast",
        description="Cut away enemy vertices with geometric precision.",
        skill_type=SkillType.ATTACK,
        target=SkillTarget.SINGLE_ENEMY,
        cooldown=4.0,
        damage=40.0,
        range=10.0,
        effects=[SkillEffect.DAMAGE, SkillEffect.SLOW],
        duration=2.0,
        color=(160, 160, 230),
        math_basis="Truncation removes vertices - applied to enemies, it removes their capabilities.",
    ),
    Skill(
        id="cantellation_expand",
        name="Cantellation Expand",
        description="Push enemies away by expanding your form.",
        skill_type=SkillType.DEFENSE,
        target=SkillTarget.AREA,
        cooldown=6.0,
        area_radius=8.0,
        effects=[SkillEffect.KNOCKBACK],
        color=(170, 140, 240),
        math_basis="Cantellation expands edges and faces outward - applied to space, it pushes everything away.",
    ),
    Skill(
        id="omnitruncation_ultimate",
        name="Omnitruncation",
        description="Apply every geometric operation at once.",
        skill_type=SkillType.ULTIMATE,
        target=SkillTarget.AREA,
        cooldown=25.0,
        damage=120.0,
        area_radius=15.0,
        effects=[SkillEffect.DAMAGE, SkillEffect.STUN, SkillEffect.KNOCKBACK],
        duration=2.0,
        color=(220, 120, 255),
        math_basis="Omnitruncation applies truncation, rectification, and cantellation simultaneously.",
    ),
]

# =============================================================================
# EXOTIC/TOPOLOGICAL SKILLS
# =============================================================================

EXOTIC_SKILLS = [
    Skill(
        id="klein_inversion",
        name="Klein Inversion",
        description="Turn enemies inside-out using non-orientable topology.",
        skill_type=SkillType.MANIPULATION,
        target=SkillTarget.SINGLE_ENEMY,
        cooldown=10.0,
        damage=60.0,
        effects=[SkillEffect.INVERT, SkillEffect.DAMAGE],
        color=(150, 100, 255),
        math_basis="The Klein bottle has no inside or outside - pass through it and you're inverted.",
    ),
    Skill(
        id="mobius_twist",
        name="Möbius Twist",
        description="Twist space so enemies face the wrong direction.",
        skill_type=SkillType.MANIPULATION,
        target=SkillTarget.AREA,
        cooldown=8.0,
        area_radius=10.0,
        effects=[SkillEffect.STUN, SkillEffect.ROTATE],
        duration=3.0,
        color=(255, 150, 100),
        math_basis="The Möbius strip reverses orientation after one loop - enemies become disoriented.",
    ),
    Skill(
        id="hopf_link_bind",
        name="Hopf Link Bind",
        description="Eternally link yourself to an enemy - share damage.",
        skill_type=SkillType.MANIPULATION,
        target=SkillTarget.SINGLE_ENEMY,
        cooldown=15.0,
        duration=10.0,
        effects=[SkillEffect.ABSORB],
        color=(255, 100, 255),
        math_basis="The Hopf link is two circles linked in 4D - inseparable without breaking one.",
    ),
    Skill(
        id="clifford_parallel",
        name="Clifford Parallel",
        description="Create parallel versions of yourself in different W-slices.",
        skill_type=SkillType.UTILITY,
        target=SkillTarget.SELF,
        cooldown=20.0,
        duration=8.0,
        effects=[SkillEffect.DUPLICATE],
        color=(100, 255, 200),
        math_basis="The Clifford torus exists in parallel W-slices - you can too.",
    ),
    Skill(
        id="torus_knot_trap",
        name="Torus Knot Trap",
        description="Trap enemies in an inescapable 4D knot.",
        skill_type=SkillType.MANIPULATION,
        target=SkillTarget.AREA,
        cooldown=12.0,
        area_radius=6.0,
        duration=5.0,
        effects=[SkillEffect.STUN, SkillEffect.DAMAGE],
        damage=30.0,
        color=(200, 255, 150),
        math_basis="A torus knot in 4D cannot be untied - enemies are trapped.",
    ),
]

# =============================================================================
# PRISM SKILLS
# =============================================================================

PRISM_SKILLS = [
    Skill(
        id="extrusion_lance",
        name="Extrusion Lance",
        description="Extend a 3D shape into 4D as a piercing lance.",
        skill_type=SkillType.ATTACK,
        target=SkillTarget.DIRECTION,
        cooldown=3.0,
        damage=30.0,
        range=15.0,
        effects=[SkillEffect.DAMAGE],
        color=(200, 150, 150),
        math_basis="Prisms are 3D shapes extruded along W - extend further to reach far enemies.",
    ),
    Skill(
        id="projection_collapse",
        name="Projection Collapse",
        description="Collapse your 4D form onto 3D, dealing damage as you compress.",
        skill_type=SkillType.ATTACK,
        target=SkillTarget.AREA,
        cooldown=7.0,
        damage=45.0,
        area_radius=8.0,
        effects=[SkillEffect.DAMAGE, SkillEffect.KNOCKBACK],
        color=(180, 180, 160),
        math_basis="Projecting a 4D object to 3D compresses it - enemies in the way are crushed.",
    ),
]

# =============================================================================
# TRANSCENDENT SKILLS (5D glimpse)
# =============================================================================

TRANSCENDENT_SKILLS = [
    Skill(
        id="fifth_dimension_glimpse",
        name="Fifth Dimension Glimpse",
        description="Briefly perceive 5D, seeing all possible futures.",
        skill_type=SkillType.UTILITY,
        target=SkillTarget.SELF,
        cooldown=30.0,
        duration=5.0,
        effects=[SkillEffect.PHASE],
        color=(255, 255, 200),
        math_basis="The penteract is a 5D hypercube - glimpsing it reveals paths through 4D.",
    ),
    Skill(
        id="dimensional_cascade",
        name="Dimensional Cascade",
        description="Attack through all dimensions simultaneously.",
        skill_type=SkillType.ULTIMATE,
        target=SkillTarget.DIMENSION,
        cooldown=60.0,
        damage=200.0,
        effects=[SkillEffect.DAMAGE, SkillEffect.SLICE],
        color=(255, 255, 255),
        math_basis="From 5D, all of 4D is visible. Attack everything at once.",
    ),
]


# =============================================================================
# SKILL REGISTRY
# =============================================================================

SHAPE_SKILLS: Dict[str, List[Skill]] = {
    # Regular
    "pentachoron": PENTACHORON_SKILLS,
    "hexadecachoron": HEXADECACHORON_SKILLS,
    "tesseract": TESSERACT_SKILLS,
    "icositetrachoron": ICOSITETRACHORON_SKILLS,
    "hecatonicosachoron": HECATONICOSACHORON_SKILLS,
    "hexacosichoron": HEXACOSICHORON_SKILLS,
    
    # Uniform
    "rectified_tesseract": UNIFORM_SKILLS,
    "truncated_tesseract": UNIFORM_SKILLS,
    "cantellated_tesseract": UNIFORM_SKILLS,
    "bitruncated_tesseract": UNIFORM_SKILLS,
    "runcinated_tesseract": UNIFORM_SKILLS,
    "omnitruncated_tesseract": UNIFORM_SKILLS,
    
    # Exotic
    "clifford_torus": EXOTIC_SKILLS,
    "klein_bottle_4d": EXOTIC_SKILLS,
    "mobius_4d": EXOTIC_SKILLS,
    "hopf_link_4d": EXOTIC_SKILLS,
    "torus_knot_4d": EXOTIC_SKILLS,
    "spherinder": EXOTIC_SKILLS,
    
    # Prism
    "tetrahedral_prism": PRISM_SKILLS,
    "cubic_prism": PRISM_SKILLS,
    "octahedral_prism": PRISM_SKILLS,
    "icosahedral_prism": PRISM_SKILLS,
    "dodecahedral_prism": PRISM_SKILLS,
    
    # Transcendent
    "penteract_frame": TRANSCENDENT_SKILLS,
}


def get_skills_for_shape(shape_id: str) -> List[Skill]:
    """Get all skills available for a shape."""
    return SHAPE_SKILLS.get(shape_id, [])


def get_skill_by_id(skill_id: str) -> Optional[Skill]:
    """Find a skill by its ID."""
    for skills in SHAPE_SKILLS.values():
        for skill in skills:
            if skill.id == skill_id:
                return skill
    return None


def get_all_skills() -> List[Skill]:
    """Get all unique skills."""
    seen = set()
    all_skills = []
    
    for skills in SHAPE_SKILLS.values():
        for skill in skills:
            if skill.id not in seen:
                seen.add(skill.id)
                all_skills.append(skill)
    
    return all_skills
