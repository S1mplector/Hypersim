"""Expanded enemy roster - re-exports from enemies/ submodule.

This file is kept for backwards compatibility.
All enemies are now organized in hypersim/game/combat/enemies/:
- base.py: Core classes and utilities
- enemies_1d.py: 1D dimension enemies
- enemies_2d.py: 2D dimension enemies  
- enemies_3d.py: 3D dimension enemies
- enemies_4d.py: 4D dimension enemies

Import from this file or directly from the submodule:
    from hypersim.game.combat.enemies_expanded import get_expanded_enemy
    # or
    from hypersim.game.combat.enemies import get_enemy
"""
from __future__ import annotations

from typing import Dict, List, Optional

# Re-export everything from the new organized submodule
from .enemies import (
    # Classes
    CombatEnemy,
    EnemyPersonality,
    EnemyMood,
    ACTOption,
    EnemyAttackPattern,
    CombatStats,
    SoulMode,
    # Functions
    get_all_enemies,
    get_enemy,
    get_enemies_for_dimension,
    get_bosses,
    get_enemy_ids_for_dimension,
    # Dimension-specific creators
    create_1d_enemies,
    create_2d_enemies,
    create_3d_enemies,
    create_4d_enemies,
    # Pre-built dicts
    ENEMIES_1D,
    ENEMIES_2D,
    ENEMIES_3D,
    ENEMIES_4D,
)

# Backwards-compatible aliases
get_all_expanded_enemies = get_all_enemies
get_expanded_enemy = get_enemy
create_expanded_1d_enemies = create_1d_enemies
create_expanded_2d_enemies = create_2d_enemies
create_expanded_3d_enemies = create_3d_enemies
create_expanded_4d_enemies = create_4d_enemies

__all__ = [
    # Classes
    "CombatEnemy",
    "EnemyPersonality",
    "EnemyMood",
    "ACTOption",
    "EnemyAttackPattern",
    "CombatStats",
    "SoulMode",
    # Functions (new names)
    "get_all_enemies",
    "get_enemy",
    "get_enemies_for_dimension",
    "get_bosses",
    "get_enemy_ids_for_dimension",
    # Functions (backwards-compatible names)
    "get_all_expanded_enemies",
    "get_expanded_enemy",
    # Creators (new names)
    "create_1d_enemies",
    "create_2d_enemies",
    "create_3d_enemies",
    "create_4d_enemies",
    # Creators (backwards-compatible names)
    "create_expanded_1d_enemies",
    "create_expanded_2d_enemies",
    "create_expanded_3d_enemies",
    "create_expanded_4d_enemies",
    # Pre-built dicts
    "ENEMIES_1D",
    "ENEMIES_2D",
    "ENEMIES_3D",
    "ENEMIES_4D",
]
