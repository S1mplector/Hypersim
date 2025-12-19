"""Dimensional combat system for HyperSim.

A unique take on turn-based bullet-hell combat with dimensional mechanics.

UNIQUE FEATURES (differentiating from Undertale):
- Dimensional Shift: Change perception during combat (0D-4D)
- Perception Attacks: Enemies manipulate your dimensional awareness
- Reality Warping: Battle box changes shape and properties
- Geometric Resonance: Build resonance with geometric forms
- Transcendence Gauge: Build up to temporary 4D perception
- Grazing System: Near-misses reward transcendence
- Realm-based encounters: Each realm has unique modifiers

CORE FEATURES:
- Turn-based combat with bullet-hell dodge sequences
- FIGHT / ACT / ITEM / MERCY menu system
- Player "soul" that dodges enemy attacks in a battle box
- Enemy attack patterns with projectiles, waves, and geometric shapes
- Spare system based on ACT choices and mercy
- Rich dialogue and lore for every enemy and NPC
"""

from .core import (
    CombatState, CombatPhase, CombatResult,
    PlayerSoul, SoulMode,
    CombatStats, CombatAction,
    InventoryItem, DEFAULT_ITEMS
)
from .enemies import (
    CombatEnemy, EnemyPersonality, EnemyMood,
    ACTOption, EnemyAttackPattern,
    CombatStats as EnemyCombatStats,
    get_enemy, get_all_enemies, get_enemies_for_dimension,
    get_bosses, get_enemy_ids_for_dimension,
    create_1d_enemies, create_2d_enemies,
    create_3d_enemies, create_4d_enemies,
    ENEMIES_1D, ENEMIES_2D, ENEMIES_3D, ENEMIES_4D,
)
# Backwards-compatible aliases
from .enemies_expanded import (
    get_expanded_enemy, get_all_expanded_enemies,
    create_expanded_1d_enemies, create_expanded_2d_enemies,
    create_expanded_3d_enemies, create_expanded_4d_enemies,
)
from .attacks import (
    Bullet, BulletPattern, BulletType,
    AttackWave, AttackSequence,
    PatternGenerator, build_attack_from_pattern
)
from .battle import BattleSystem, BattleBox
from .ui import CombatUI
from .dimensional_mechanics import (
    PerceptionLevel, RealityWarpType,
    DimensionalShiftState, RealityWarpEffect,
    GeometricResonance, GrazingSystem,
    DimensionalCombatState, PerceptionAttack,
    DIMENSIONAL_ACT_EFFECTS
)
from .realms import (
    Realm, RealmType, RealmModifier,
    get_realm, get_realms_for_dimension,
    get_starting_realm, get_border_realm,
    ALL_REALMS, REALMS_1D, REALMS_2D, REALMS_3D, REALMS_4D
)
from .npcs import (
    NPC, NPCRole, NPCDialogue, DialogueLine,
    get_npc, get_npcs_for_realm, get_npcs_for_dimension,
    ALL_NPCS
)
from .integration import (
    CombatIntegration, EncounterType, EncounterConfig,
    EncounterTable, create_combat_integration
)

__all__ = [
    # Core
    "CombatState",
    "CombatPhase",
    "CombatResult",
    "PlayerSoul",
    "SoulMode",
    "CombatStats",
    "CombatAction",
    "InventoryItem",
    "DEFAULT_ITEMS",
    # Enemies
    "CombatEnemy",
    "EnemyPersonality",
    "EnemyMood",
    "ACTOption",
    "EnemyAttackPattern",
    "get_enemy",
    "get_all_enemies",
    "get_enemies_for_dimension",
    "get_bosses",
    "get_enemy_ids_for_dimension",
    "create_1d_enemies",
    "create_2d_enemies",
    "create_3d_enemies",
    "create_4d_enemies",
    "ENEMIES_1D",
    "ENEMIES_2D",
    "ENEMIES_3D",
    "ENEMIES_4D",
    # Backwards-compatible aliases
    "get_expanded_enemy",
    "get_all_expanded_enemies",
    "create_expanded_1d_enemies",
    "create_expanded_2d_enemies",
    "create_expanded_3d_enemies",
    "create_expanded_4d_enemies",
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
    # Dimensional Mechanics
    "PerceptionLevel",
    "RealityWarpType",
    "DimensionalShiftState",
    "RealityWarpEffect",
    "GeometricResonance",
    "GrazingSystem",
    "DimensionalCombatState",
    "PerceptionAttack",
    "DIMENSIONAL_ACT_EFFECTS",
    # Realms
    "Realm",
    "RealmType",
    "RealmModifier",
    "get_realm",
    "get_realms_for_dimension",
    "get_starting_realm",
    "get_border_realm",
    "ALL_REALMS",
    # NPCs
    "NPC",
    "NPCRole",
    "NPCDialogue",
    "get_npc",
    "get_npcs_for_realm",
    "get_npcs_for_dimension",
    "ALL_NPCS",
    # Integration
    "CombatIntegration",
    "EncounterType",
    "EncounterConfig",
    "EncounterTable",
    "create_combat_integration",
]


def run_combat_demo():
    """Run the standalone combat demo."""
    from .demo import run_demo
    run_demo()
