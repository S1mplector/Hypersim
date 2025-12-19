"""Mathematical advantages between 4D shapes.

Based on actual 4D geometry properties:
- Symmetry groups determine defensive capability
- Vertex/edge counts affect attack potential  
- Duality relationships create counter-matchups
- Cell types grant elemental-like advantages
- Topological properties enable unique abilities
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from hypersim.game.evolution_expanded import Shape4D, ShapeFamily, SHAPES_4D


class AdvantageType(Enum):
    """Types of mathematical advantages."""
    SYMMETRY = "symmetry"       # Higher symmetry = better defense
    VERTICES = "vertices"       # More vertices = more attack points
    DUALITY = "duality"         # Dual shapes counter each other
    CELLS = "cells"             # Cell type matchups
    TOPOLOGY = "topology"       # Topological properties
    DIMENSION = "dimension"     # Higher-dimensional glimpses


@dataclass
class ShapeAdvantage:
    """Calculated advantage between two shapes."""
    attacker: str
    defender: str
    damage_multiplier: float = 1.0
    accuracy_bonus: float = 0.0
    crit_chance: float = 0.0
    special_effects: List[str] = None
    explanation: str = ""
    
    def __post_init__(self):
        if self.special_effects is None:
            self.special_effects = []


# =============================================================================
# MATHEMATICAL PROPERTIES THAT AFFECT COMBAT
# =============================================================================

# Symmetry order (higher = more symmetric = better defense)
SYMMETRY_ORDER = {
    # Regular polytopes have highest symmetry
    "pentachoron": 120,        # 5! = 120
    "hexadecachoron": 384,     # 2^4 × 4! = 384
    "tesseract": 384,          # Same as 16-cell (dual)
    "icositetrachoron": 1152,  # Highest among regulars!
    "hecatonicosachoron": 14400,
    "hexacosichoron": 14400,   # Same as 120-cell (dual)
    
    # Uniform have good symmetry
    "rectified_tesseract": 384,
    "truncated_tesseract": 384,
    "cantellated_tesseract": 384,
    "bitruncated_tesseract": 384,
    "runcinated_tesseract": 384,
    "omnitruncated_tesseract": 384,
    
    # 24-cell family
    "snub_24_cell": 576,       # Chiral = half symmetry
    "rectified_24_cell": 1152,
    
    # Special
    "grand_antiprism": 400,
    "disphenoidal_288_cell": 1152,
    
    # Prisms have lower symmetry
    "tetrahedral_prism": 48,
    "cubic_prism": 96,
    "octahedral_prism": 96,
    "icosahedral_prism": 240,
    "dodecahedral_prism": 240,
    
    # Duoprisms
    "square_duoprism": 128,
    "hexagonal_duoprism": 288,
    
    # Exotic (varied)
    "clifford_torus": 0,       # Continuous symmetry (infinite)
    "spherinder": 0,
    "klein_bottle_4d": 0,
    "mobius_4d": 0,
    "hopf_link_4d": 0,
    "torus_knot_4d": 0,
    
    # Transcendent
    "penteract_frame": 3840,   # 5D symmetry!
}

# Dual pairs (these shapes counter each other)
DUAL_PAIRS = [
    ("tesseract", "hexadecachoron"),
    ("hecatonicosachoron", "hexacosichoron"),
    ("icositetrachoron", "icositetrachoron"),  # Self-dual!
    ("rectified_24_cell", "rectified_24_cell"),  # Self-dual
]

# Cell type advantages (like elemental matchups)
CELL_ADVANTAGES = {
    "tetrahedron": {
        "strong_vs": ["cube"],           # Sharp vs solid
        "weak_vs": ["dodecahedron"],     # Overwhelmed by complexity
    },
    "cube": {
        "strong_vs": ["octahedron"],     # Stability vs sharpness
        "weak_vs": ["tetrahedron"],
    },
    "octahedron": {
        "strong_vs": ["dodecahedron"],   # Precision vs complexity
        "weak_vs": ["cube"],
    },
    "dodecahedron": {
        "strong_vs": ["tetrahedron"],    # Complexity overwhelms simplicity
        "weak_vs": ["octahedron"],
    },
    "icosahedron": {
        "strong_vs": ["cube", "tetrahedron"],
        "weak_vs": [],
    },
}

# Shape to primary cell type
SHAPE_CELL_TYPE = {
    "pentachoron": "tetrahedron",
    "hexadecachoron": "tetrahedron",
    "tesseract": "cube",
    "icositetrachoron": "octahedron",
    "hecatonicosachoron": "dodecahedron",
    "hexacosichoron": "tetrahedron",
    "snub_24_cell": "icosahedron",
    "grand_antiprism": "tetrahedron",
}


def calculate_advantage(attacker_id: str, defender_id: str) -> ShapeAdvantage:
    """Calculate the mathematical advantage between two shapes."""
    attacker = SHAPES_4D.get(attacker_id)
    defender = SHAPES_4D.get(defender_id)
    
    if not attacker or not defender:
        return ShapeAdvantage(attacker_id, defender_id)
    
    damage_mult = 1.0
    accuracy = 0.0
    crit = 0.05  # Base 5%
    effects = []
    explanations = []
    
    # === VERTEX ADVANTAGE ===
    # More vertices = more attack angles
    vertex_ratio = attacker.vertices / max(1, defender.vertices)
    if vertex_ratio > 2.0:
        damage_mult *= 1.2
        explanations.append(f"Vertex superiority ({attacker.vertices} vs {defender.vertices})")
    elif vertex_ratio < 0.5:
        accuracy -= 0.1
        explanations.append("Fewer attack angles")
    
    # === SYMMETRY DEFENSE ===
    # Higher symmetry = better at deflecting
    att_sym = SYMMETRY_ORDER.get(attacker_id, 100)
    def_sym = SYMMETRY_ORDER.get(defender_id, 100)
    
    if def_sym > att_sym * 2:
        damage_mult *= 0.8
        explanations.append(f"Defender's superior symmetry")
    elif att_sym > def_sym * 2:
        crit += 0.1
        explanations.append("Symmetry advantage grants critical chance")
    
    # === DUALITY COUNTER ===
    # Dual shapes deal bonus damage to each other
    for pair in DUAL_PAIRS:
        if (attacker_id in pair and defender_id in pair):
            if attacker_id == defender_id:
                # Self-dual: bonus against everything
                damage_mult *= 1.1
                effects.append("self_dual_bonus")
                explanations.append("Self-dual resonance")
            else:
                # Dual pair: counter each other
                damage_mult *= 1.25
                effects.append("duality_counter")
                explanations.append("Duality counter!")
            break
    
    # === CELL TYPE MATCHUP ===
    att_cell = SHAPE_CELL_TYPE.get(attacker_id)
    def_cell = SHAPE_CELL_TYPE.get(defender_id)
    
    if att_cell and def_cell:
        cell_adv = CELL_ADVANTAGES.get(att_cell, {})
        if def_cell in cell_adv.get("strong_vs", []):
            damage_mult *= 1.15
            effects.append("cell_advantage")
            explanations.append(f"{att_cell} beats {def_cell}")
        elif def_cell in cell_adv.get("weak_vs", []):
            damage_mult *= 0.85
            explanations.append(f"{att_cell} weak to {def_cell}")
    
    # === FAMILY BONUSES ===
    # Exotic shapes have special properties
    if attacker.family == ShapeFamily.EXOTIC:
        if defender.family == ShapeFamily.REGULAR:
            effects.append("topology_confusion")
            accuracy += 0.15
            explanations.append("Topology confuses regular forms")
    
    # Transcendent shapes are powerful
    if attacker.family == ShapeFamily.TRANSCENDENT:
        damage_mult *= 1.3
        effects.append("dimensional_superiority")
        explanations.append("5D glimpse grants power")
    
    # === RARITY SCALING ===
    rarity_diff = attacker.rarity.value - defender.rarity.value
    if rarity_diff >= 2:
        damage_mult *= 1.0 + (rarity_diff * 0.05)
    
    return ShapeAdvantage(
        attacker=attacker_id,
        defender=defender_id,
        damage_multiplier=round(damage_mult, 2),
        accuracy_bonus=round(accuracy, 2),
        crit_chance=round(crit, 2),
        special_effects=effects,
        explanation=" | ".join(explanations) if explanations else "No special advantage"
    )


# =============================================================================
# SHAPE MATCHUP TABLE
# =============================================================================

# Pre-computed common matchups
SHAPE_MATCHUPS: Dict[Tuple[str, str], ShapeAdvantage] = {}

def _precompute_matchups():
    """Pre-compute common shape matchups."""
    common_shapes = [
        "pentachoron", "hexadecachoron", "tesseract", 
        "icositetrachoron", "hecatonicosachoron", "hexacosichoron"
    ]
    
    for att in common_shapes:
        for def_ in common_shapes:
            SHAPE_MATCHUPS[(att, def_)] = calculate_advantage(att, def_)

_precompute_matchups()


def get_matchup_summary(shape_id: str) -> Dict[str, str]:
    """Get a summary of a shape's matchups."""
    shape = SHAPES_4D.get(shape_id)
    if not shape:
        return {}
    
    summary = {
        "strong_against": [],
        "weak_against": [],
        "neutral": [],
    }
    
    for other_id in SHAPES_4D:
        if other_id == shape_id:
            continue
        
        adv = calculate_advantage(shape_id, other_id)
        if adv.damage_multiplier >= 1.15:
            summary["strong_against"].append(other_id)
        elif adv.damage_multiplier <= 0.85:
            summary["weak_against"].append(other_id)
        else:
            summary["neutral"].append(other_id)
    
    return summary
