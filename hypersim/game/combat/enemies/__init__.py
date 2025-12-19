"""Enemy definitions organized by dimension.

Structure:
- base.py: Core enemy classes and shared utilities
- enemies_1d.py: 1D dimension enemies (Line Walker, Point Spirit, etc.)
- enemies_2d.py: 2D dimension enemies (Triangle Scout, Square Citizen, etc.)
- enemies_3d.py: 3D dimension enemies (Cube Guard, Sphere Wanderer, etc.)
- enemies_4d.py: 4D dimension enemies (Tesseract Guardian, Hypersphere Wanderer, etc.)
"""
from typing import Dict, List, Optional
import copy

from .base import (
    CombatEnemy, EnemyPersonality, EnemyMood,
    ACTOption, EnemyAttackPattern, CombatStats, SoulMode
)
from .enemies_1d import ENEMIES_1D, create_1d_enemies
from .enemies_2d import ENEMIES_2D, create_2d_enemies
from .enemies_3d import ENEMIES_3D, create_3d_enemies
from .enemies_4d import ENEMIES_4D, create_4d_enemies


# Combined registry of all enemies
_ALL_ENEMIES: Dict[str, CombatEnemy] = {}


def _build_registry() -> Dict[str, CombatEnemy]:
    """Build the complete enemy registry."""
    global _ALL_ENEMIES
    if not _ALL_ENEMIES:
        _ALL_ENEMIES.update(create_1d_enemies())
        _ALL_ENEMIES.update(create_2d_enemies())
        _ALL_ENEMIES.update(create_3d_enemies())
        _ALL_ENEMIES.update(create_4d_enemies())
    return _ALL_ENEMIES


def get_all_enemies() -> Dict[str, CombatEnemy]:
    """Get all enemies as fresh copies."""
    registry = _build_registry()
    return {k: copy.deepcopy(v) for k, v in registry.items()}


def get_enemy(enemy_id: str) -> Optional[CombatEnemy]:
    """Get a fresh copy of an enemy by ID."""
    registry = _build_registry()
    enemy = registry.get(enemy_id)
    return copy.deepcopy(enemy) if enemy else None


def get_enemies_for_dimension(dimension: str) -> List[CombatEnemy]:
    """Get all enemies for a specific dimension."""
    registry = _build_registry()
    return [copy.deepcopy(e) for e in registry.values() if e.dimension == dimension]


def get_bosses() -> List[CombatEnemy]:
    """Get all boss enemies."""
    registry = _build_registry()
    return [copy.deepcopy(e) for e in registry.values() if e.is_boss]


def get_enemy_ids_for_dimension(dimension: str) -> List[str]:
    """Get enemy IDs for a dimension (without creating copies)."""
    registry = _build_registry()
    return [eid for eid, e in registry.items() if e.dimension == dimension]


__all__ = [
    # Classes
    "CombatEnemy",
    "EnemyPersonality", 
    "EnemyMood",
    "ACTOption",
    "EnemyAttackPattern",
    "CombatStats",
    "SoulMode",
    # Functions
    "get_all_enemies",
    "get_enemy",
    "get_enemies_for_dimension",
    "get_bosses",
    "get_enemy_ids_for_dimension",
    # Dimension-specific
    "create_1d_enemies",
    "create_2d_enemies", 
    "create_3d_enemies",
    "create_4d_enemies",
    "ENEMIES_1D",
    "ENEMIES_2D",
    "ENEMIES_3D",
    "ENEMIES_4D",
]
