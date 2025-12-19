"""4D Evolution system - player evolves through regular 4-polytopes.

The six convex regular 4-polytopes in order of complexity:
1. 5-cell (Pentachoron/4-simplex) - 5 vertices, 5 tetrahedral cells
2. 16-cell (Hexadecachoron/4-orthoplex) - 8 vertices, 16 tetrahedral cells  
3. 8-cell (Tesseract/4-cube) - 16 vertices, 8 cubic cells
4. 24-cell (Icositetrachoron) - 24 vertices, 24 octahedral cells [UNIQUE TO 4D!]
5. 120-cell (Hecatonicosachoron) - 600 vertices, 120 dodecahedral cells
6. 600-cell (Hexacosichoron) - 120 vertices, 600 tetrahedral cells

Each form grants different stats and abilities, representing growth as a 4D being.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from hypersim.game.session import GameSession


class PolytopeForm(IntEnum):
    """The six regular 4-polytopes in evolution order."""
    SIMPLEX_5 = 0      # 5-cell: Simplest, newborn 4D being
    CROSS_16 = 1       # 16-cell: Cross-polytope
    TESSERACT_8 = 2    # 8-cell: The iconic hypercube
    ICOSITETRACHORON = 3  # 24-cell: Unique to 4D!
    HECATONICOSACHORON = 4  # 120-cell: Complex dodecahedral
    HEXACOSICHORON = 5     # 600-cell: Ultimate form


@dataclass
class PolytopeStats:
    """Stats granted by a polytope form."""
    health_bonus: float = 0.0        # Added to base health
    speed_bonus: float = 0.0         # Added to base speed
    w_perception: float = 1.0        # How far player can see in W axis
    damage_reduction: float = 0.0    # Percentage damage reduction
    ability_cooldown_mult: float = 1.0  # Multiplier on ability cooldowns
    xp_multiplier: float = 1.0       # XP gain multiplier


@dataclass
class PolytopeFormDef:
    """Complete definition of a polytope evolution form."""
    form: PolytopeForm
    name: str
    short_name: str
    description: str
    vertices: int
    edges: int
    faces: int
    cells: int
    cell_type: str  # What 3D shape makes up the cells
    stats: PolytopeStats
    xp_required: int  # XP needed to evolve TO this form (0 for first)
    abilities_granted: List[str] = field(default_factory=list)
    color: Tuple[int, int, int] = (80, 200, 255)
    glow_intensity: float = 0.5


# Define all polytope forms with their geometric properties and game stats
POLYTOPE_FORMS: Dict[PolytopeForm, PolytopeFormDef] = {
    PolytopeForm.SIMPLEX_5: PolytopeFormDef(
        form=PolytopeForm.SIMPLEX_5,
        name="Pentachoron",
        short_name="5-Cell",
        description="The simplest regular 4D form. A 4D tetrahedron - humble but pure.",
        vertices=5,
        edges=10,
        faces=10,
        cells=5,
        cell_type="tetrahedron",
        stats=PolytopeStats(
            health_bonus=0,
            speed_bonus=2.0,  # Fast but fragile
            w_perception=1.0,
            damage_reduction=0.0,
            ability_cooldown_mult=1.2,
            xp_multiplier=1.0,
        ),
        xp_required=0,  # Starting form
        abilities_granted=["ping_neighbors"],
        color=(100, 200, 255),
        glow_intensity=0.4,
    ),
    
    PolytopeForm.CROSS_16: PolytopeFormDef(
        form=PolytopeForm.CROSS_16,
        name="Hexadecachoron",
        short_name="16-Cell",
        description="The 4D cross-polytope. Sharp and precise, like dual axes crossing.",
        vertices=8,
        edges=24,
        faces=32,
        cells=16,
        cell_type="tetrahedron",
        stats=PolytopeStats(
            health_bonus=20,
            speed_bonus=1.5,
            w_perception=1.5,
            damage_reduction=0.05,
            ability_cooldown_mult=1.1,
            xp_multiplier=1.1,
        ),
        xp_required=100,
        abilities_granted=["dash"],
        color=(120, 180, 255),
        glow_intensity=0.5,
    ),
    
    PolytopeForm.TESSERACT_8: PolytopeFormDef(
        form=PolytopeForm.TESSERACT_8,
        name="Tesseract",
        short_name="8-Cell",
        description="The legendary hypercube. Balanced and iconic - the archetypal 4D form.",
        vertices=16,
        edges=32,
        faces=24,
        cells=8,
        cell_type="cube",
        stats=PolytopeStats(
            health_bonus=50,
            speed_bonus=1.0,
            w_perception=2.0,
            damage_reduction=0.10,
            ability_cooldown_mult=1.0,
            xp_multiplier=1.2,
        ),
        xp_required=300,
        abilities_granted=["rotate_hyperplanes"],
        color=(150, 150, 255),
        glow_intensity=0.6,
    ),
    
    PolytopeForm.ICOSITETRACHORON: PolytopeFormDef(
        form=PolytopeForm.ICOSITETRACHORON,
        name="Icositetrachoron",
        short_name="24-Cell",
        description="The mysterious 24-cell - EXISTS ONLY IN 4D! Self-dual and perfect.",
        vertices=24,
        edges=96,
        faces=96,
        cells=24,
        cell_type="octahedron",
        stats=PolytopeStats(
            health_bonus=80,
            speed_bonus=1.2,
            w_perception=3.0,
            damage_reduction=0.15,
            ability_cooldown_mult=0.9,
            xp_multiplier=1.3,
        ),
        xp_required=600,
        abilities_granted=["stabilize_lower", "spawn_slices"],
        color=(180, 120, 255),
        glow_intensity=0.7,
    ),
    
    PolytopeForm.HECATONICOSACHORON: PolytopeFormDef(
        form=PolytopeForm.HECATONICOSACHORON,
        name="Hecatonicosachoron",
        short_name="120-Cell",
        description="An immense structure of 120 dodecahedral cells. Approaching perfection.",
        vertices=600,
        edges=1200,
        faces=720,
        cells=120,
        cell_type="dodecahedron",
        stats=PolytopeStats(
            health_bonus=120,
            speed_bonus=0.8,  # Slower but powerful
            w_perception=4.0,
            damage_reduction=0.20,
            ability_cooldown_mult=0.8,
            xp_multiplier=1.5,
        ),
        xp_required=1200,
        abilities_granted=["fold_line", "carry_line"],
        color=(200, 100, 255),
        glow_intensity=0.85,
    ),
    
    PolytopeForm.HEXACOSICHORON: PolytopeFormDef(
        form=PolytopeForm.HEXACOSICHORON,
        name="Hexacosichoron",
        short_name="600-Cell",
        description="The ultimate form - 600 tetrahedral cells in perfect harmony. Transcendence achieved.",
        vertices=120,
        edges=720,
        faces=1200,
        cells=600,
        cell_type="tetrahedron",
        stats=PolytopeStats(
            health_bonus=150,
            speed_bonus=1.5,  # Speed returns at mastery
            w_perception=5.0,  # See across all W
            damage_reduction=0.25,
            ability_cooldown_mult=0.7,
            xp_multiplier=2.0,
        ),
        xp_required=2500,
        abilities_granted=[],  # Has all abilities already
        color=(255, 150, 255),
        glow_intensity=1.0,
    ),
}


@dataclass
class EvolutionState:
    """Tracks player's evolution progress."""
    current_form: PolytopeForm = PolytopeForm.SIMPLEX_5
    evolution_xp: int = 0  # XP toward next evolution
    total_evolutions: int = 0  # Times evolved
    forms_unlocked: List[PolytopeForm] = field(default_factory=lambda: [PolytopeForm.SIMPLEX_5])
    
    @property
    def current_form_def(self) -> PolytopeFormDef:
        return POLYTOPE_FORMS[self.current_form]
    
    @property
    def next_form(self) -> Optional[PolytopeForm]:
        """Get the next form in evolution order, if any."""
        next_val = self.current_form.value + 1
        if next_val <= PolytopeForm.HEXACOSICHORON.value:
            return PolytopeForm(next_val)
        return None
    
    @property
    def next_form_def(self) -> Optional[PolytopeFormDef]:
        """Get definition of next form."""
        nf = self.next_form
        return POLYTOPE_FORMS[nf] if nf else None
    
    @property
    def xp_to_next(self) -> int:
        """XP remaining to reach next form."""
        nf = self.next_form_def
        if not nf:
            return 0
        return max(0, nf.xp_required - self.evolution_xp)
    
    @property
    def evolution_progress(self) -> float:
        """Progress to next form as 0-1 fraction."""
        nf = self.next_form_def
        if not nf or nf.xp_required == 0:
            return 1.0
        current_req = self.current_form_def.xp_required
        next_req = nf.xp_required
        range_xp = next_req - current_req
        if range_xp <= 0:
            return 1.0
        progress_xp = self.evolution_xp - current_req
        return min(1.0, max(0.0, progress_xp / range_xp))
    
    def can_evolve(self) -> bool:
        """Check if player has enough XP to evolve."""
        nf = self.next_form_def
        if not nf:
            return False
        return self.evolution_xp >= nf.xp_required
    
    def add_xp(self, amount: int) -> Tuple[int, bool]:
        """Add evolution XP. Returns (actual_added, can_now_evolve)."""
        multiplier = self.current_form_def.stats.xp_multiplier
        actual = int(amount * multiplier)
        self.evolution_xp += actual
        return actual, self.can_evolve()
    
    def evolve(self) -> Optional[PolytopeFormDef]:
        """Attempt to evolve to next form. Returns new form def if successful."""
        if not self.can_evolve():
            return None
        
        nf = self.next_form
        if not nf:
            return None
        
        self.current_form = nf
        self.total_evolutions += 1
        
        if nf not in self.forms_unlocked:
            self.forms_unlocked.append(nf)
        
        return POLYTOPE_FORMS[nf]
    
    def set_form(self, form: PolytopeForm) -> bool:
        """Set form directly (for testing or special cases)."""
        if form not in self.forms_unlocked:
            return False
        self.current_form = form
        return True


class EvolutionSystem:
    """Manages player evolution through polytope forms."""
    
    def __init__(self):
        self._states: Dict[str, EvolutionState] = {}  # entity_id -> state
    
    def get_state(self, entity_id: str) -> EvolutionState:
        """Get or create evolution state for an entity."""
        if entity_id not in self._states:
            self._states[entity_id] = EvolutionState()
        return self._states[entity_id]
    
    def add_xp(self, entity_id: str, amount: int) -> Tuple[int, bool]:
        """Add evolution XP to an entity."""
        state = self.get_state(entity_id)
        return state.add_xp(amount)
    
    def try_evolve(self, entity_id: str) -> Optional[PolytopeFormDef]:
        """Try to evolve an entity. Returns new form if successful."""
        state = self.get_state(entity_id)
        return state.evolve()
    
    def get_form(self, entity_id: str) -> PolytopeFormDef:
        """Get current form definition for an entity."""
        return self.get_state(entity_id).current_form_def
    
    def apply_stats(self, entity_id: str, base_health: float, base_speed: float) -> Tuple[float, float]:
        """Apply evolution stats to base values. Returns (health, speed)."""
        stats = self.get_form(entity_id).stats
        return (
            base_health + stats.health_bonus,
            base_speed + stats.speed_bonus,
        )
    
    def get_damage_reduction(self, entity_id: str) -> float:
        """Get damage reduction multiplier (0-1)."""
        return self.get_form(entity_id).stats.damage_reduction
    
    def get_w_perception(self, entity_id: str) -> float:
        """Get W-axis perception range."""
        return self.get_form(entity_id).stats.w_perception
    
    def get_cooldown_multiplier(self, entity_id: str) -> float:
        """Get ability cooldown multiplier."""
        return self.get_form(entity_id).stats.ability_cooldown_mult


def generate_polytope_vertices(form: PolytopeForm, scale: float = 1.0) -> NDArray:
    """Generate 4D vertices for a polytope form.
    
    Returns array of shape (N, 4) with vertex coordinates.
    """
    if form == PolytopeForm.SIMPLEX_5:
        # 5-cell: vertices of a regular 4-simplex
        # One simple construction: 5 points equally spaced
        phi = (1 + np.sqrt(5)) / 2  # Golden ratio
        vertices = np.array([
            [1, 1, 1, -1/np.sqrt(5)],
            [1, -1, -1, -1/np.sqrt(5)],
            [-1, 1, -1, -1/np.sqrt(5)],
            [-1, -1, 1, -1/np.sqrt(5)],
            [0, 0, 0, np.sqrt(5) - 1/np.sqrt(5)],
        ]) * scale * 0.6
        
    elif form == PolytopeForm.CROSS_16:
        # 16-cell: ±1 on each axis
        vertices = np.array([
            [1, 0, 0, 0], [-1, 0, 0, 0],
            [0, 1, 0, 0], [0, -1, 0, 0],
            [0, 0, 1, 0], [0, 0, -1, 0],
            [0, 0, 0, 1], [0, 0, 0, -1],
        ]) * scale
        
    elif form == PolytopeForm.TESSERACT_8:
        # 8-cell (tesseract): all combinations of ±1
        vertices = []
        for w in [-1, 1]:
            for z in [-1, 1]:
                for y in [-1, 1]:
                    for x in [-1, 1]:
                        vertices.append([x, y, z, w])
        vertices = np.array(vertices) * scale * 0.5
        
    elif form == PolytopeForm.ICOSITETRACHORON:
        # 24-cell: permutations of (±1, ±1, 0, 0)
        vertices = []
        # All permutations of (±1, ±1, 0, 0)
        for i in range(4):
            for j in range(i+1, 4):
                for si in [-1, 1]:
                    for sj in [-1, 1]:
                        v = [0, 0, 0, 0]
                        v[i] = si
                        v[j] = sj
                        vertices.append(v)
        vertices = np.array(vertices) * scale * 0.7
        
    elif form == PolytopeForm.HECATONICOSACHORON:
        # 120-cell: Complex construction - using simplified version
        # Full 120-cell has 600 vertices, we'll use a subset for rendering
        phi = (1 + np.sqrt(5)) / 2
        vertices = []
        # Start with 24-cell vertices scaled
        for i in range(4):
            for j in range(i+1, 4):
                for si in [-1, 1]:
                    for sj in [-1, 1]:
                        v = [0, 0, 0, 0]
                        v[i] = si * phi
                        v[j] = sj * phi
                        vertices.append(v)
        # Add more vertices for richer structure
        for signs in [[-1,-1,-1,-1], [1,1,1,1], [1,-1,-1,1], [-1,1,1,-1]]:
            for perm in [[0,1,2,3], [1,2,3,0], [2,3,0,1], [3,0,1,2]]:
                v = [signs[perm[i]] * (1 if i < 2 else phi) for i in range(4)]
                vertices.append(v)
        vertices = np.array(vertices) * scale * 0.4
        
    elif form == PolytopeForm.HEXACOSICHORON:
        # 600-cell: 120 vertices - using icosahedral construction
        phi = (1 + np.sqrt(5)) / 2
        vertices = []
        # 16-cell vertices
        for i in range(4):
            for s in [-1, 1]:
                v = [0, 0, 0, 0]
                v[i] = s * 2
                vertices.append(v)
        # 8-cell vertices  
        for w in [-1, 1]:
            for z in [-1, 1]:
                for y in [-1, 1]:
                    for x in [-1, 1]:
                        vertices.append([x, y, z, w])
        # Even permutations with golden ratio
        base = [phi, 1, 1/phi, 0]
        for _ in range(4):  # Cyclic permutations
            for signs in [[1,1,1,1], [1,1,-1,-1], [1,-1,1,-1], [1,-1,-1,1],
                         [-1,1,1,-1], [-1,1,-1,1], [-1,-1,1,1], [-1,-1,-1,-1]]:
                vertices.append([base[i] * signs[i] for i in range(4)])
            base = [base[1], base[2], base[3], base[0]]
        
        vertices = np.array(vertices) * scale * 0.4
    
    else:
        # Fallback to simplex
        vertices = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
            [-0.5, -0.5, -0.5, -0.5],
        ]) * scale
    
    return vertices


def generate_polytope_edges(form: PolytopeForm, vertices: NDArray) -> List[Tuple[int, int]]:
    """Generate edge connections for a polytope.
    
    Returns list of (vertex_idx_1, vertex_idx_2) tuples.
    """
    edges = []
    n = len(vertices)
    
    # Calculate edge length threshold based on polytope type
    if form == PolytopeForm.SIMPLEX_5:
        # All vertices connected in simplex
        for i in range(n):
            for j in range(i+1, n):
                edges.append((i, j))
    
    elif form == PolytopeForm.CROSS_16:
        # Connect non-opposite vertices
        for i in range(n):
            for j in range(i+1, n):
                # Opposite vertices are at indices differing by 1 (for pairs)
                if (i // 2) != (j // 2):
                    edges.append((i, j))
    
    elif form == PolytopeForm.TESSERACT_8:
        # Connect vertices differing in exactly one coordinate
        for i in range(n):
            for j in range(i+1, n):
                diff = bin(i ^ j).count('1')
                if diff == 1:
                    edges.append((i, j))
    
    else:
        # For complex polytopes, use distance threshold
        if n > 0:
            # Find minimum non-zero distance
            min_dist = float('inf')
            for i in range(min(n, 50)):  # Sample for performance
                for j in range(i+1, min(n, 50)):
                    d = np.linalg.norm(vertices[i] - vertices[j])
                    if d > 0.01 and d < min_dist:
                        min_dist = d
            
            threshold = min_dist * 1.1
            
            for i in range(n):
                for j in range(i+1, n):
                    d = np.linalg.norm(vertices[i] - vertices[j])
                    if d <= threshold:
                        edges.append((i, j))
    
    return edges


# Global evolution system instance
_evolution_system: Optional[EvolutionSystem] = None


def get_evolution_system() -> EvolutionSystem:
    """Get or create the global evolution system."""
    global _evolution_system
    if _evolution_system is None:
        _evolution_system = EvolutionSystem()
    return _evolution_system
