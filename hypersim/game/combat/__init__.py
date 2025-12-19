"""Undertale-inspired combat system for Tessera.

Features:
- Turn-based combat with bullet-hell dodge sequences
- FIGHT / ACT / ITEM / MERCY menu system
- Player "soul" that dodges enemy attacks in a battle box
- Enemy attack patterns with projectiles, waves, and geometric shapes
- Spare system based on ACT choices and mercy
- Dimensional twist: attacks and patterns vary by dimension
"""

from .core import (
    CombatState, CombatPhase, CombatResult,
    PlayerSoul, SoulMode,
    CombatStats, CombatAction
)
from .enemies import (
    CombatEnemy, EnemyPersonality, EnemyMood,
    ACTOption, EnemyAttackPattern
)
from .attacks import (
    Bullet, BulletPattern, BulletType,
    AttackWave, AttackSequence,
    PatternGenerator, build_attack_from_pattern
)
from .battle import BattleSystem, BattleBox
from .ui import CombatUI

__all__ = [
    # Core
    "CombatState",
    "CombatPhase",
    "CombatResult",
    "PlayerSoul",
    "SoulMode",
    "CombatStats",
    "CombatAction",
    # Enemies
    "CombatEnemy",
    "EnemyPersonality",
    "EnemyMood",
    "ACTOption",
    "EnemyAttackPattern",
    # Attacks
    "Bullet",
    "BulletPattern",
    "BulletType",
    "AttackWave",
    "AttackSequence",
    "PatternGenerator",
    "build_attack_from_pattern",
    # Battle
    "BattleSystem",
    "BattleBox",
    # UI
    "CombatUI",
]
