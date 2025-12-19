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

# New Dimensional Combat System
from .dimensional_combat import (
    CombatDimension, PerceptionState,
    DimensionalMovementRules, PerceptionAbilities,
    DepthLayer, DEPTH_LAYERS,
    TemporalBulletState, DimensionalBullet,
    DimensionalCombatRules, DimensionalPatternGenerator,
    get_dimension_from_enemy, get_recommended_perception
)
from .dimensional_battlebox import (
    DimensionalBattleBox, BoxTransformState,
    create_dimensional_battlebox
)
from .perception_system import (
    PerceptionShiftResult, PerceptionMeter,
    TranscendenceMeter, PerceptionHUD,
    PerceptionController, DimensionalResonance,
    ResonanceMeter, RESONANCE_ACTIONS
)
from .dimensional_battle_system import (
    DimensionalSoul, DimensionalBattleSystem,
    create_dimensional_battle_system
)
from .combat_effects import (
    CombatEffectsManager, Particle, TextPopup,
    ScreenShake, ScreenFlash, RingEffect,
    get_effects_manager
)
from .dimensional_enemy_ai import (
    DimensionalEnemyAI, EnemyAIType, PerceptionAttackType,
    PerceptionAttack, get_enemy_ai, create_ai_for_enemy,
    ENEMY_AI_PRESETS
)
from .dimensional_ui import (
    DimensionalCombatUI, AnimatedBar, CombatMenuItem
)
from .dimensional_integration import (
    DimensionalCombatIntegration, DimensionalEncounterConfig,
    RealmEncounterTable, TransitionState,
    create_dimensional_combat_integration
)
from .story_encounters import (
    StoryEncounter, StoryEncounterType, StoryEncounterManager,
    ENCOUNTERS_1D, get_encounter_manager
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
    # New Dimensional Combat System
    "CombatDimension",
    "PerceptionState",
    "DimensionalMovementRules",
    "PerceptionAbilities",
    "DepthLayer",
    "DEPTH_LAYERS",
    "TemporalBulletState",
    "DimensionalBullet",
    "DimensionalCombatRules",
    "DimensionalPatternGenerator",
    "get_dimension_from_enemy",
    "get_recommended_perception",
    "DimensionalBattleBox",
    "BoxTransformState",
    "create_dimensional_battlebox",
    "PerceptionShiftResult",
    "PerceptionMeter",
    "TranscendenceMeter",
    "PerceptionHUD",
    "PerceptionController",
    "DimensionalResonance",
    "ResonanceMeter",
    "RESONANCE_ACTIONS",
    "DimensionalSoul",
    "DimensionalBattleSystem",
    "create_dimensional_battle_system",
    # Combat Effects
    "CombatEffectsManager",
    "Particle",
    "TextPopup",
    "ScreenShake",
    "ScreenFlash",
    "RingEffect",
    "get_effects_manager",
    # Enemy AI
    "DimensionalEnemyAI",
    "EnemyAIType",
    "PerceptionAttackType",
    "PerceptionAttack",
    "get_enemy_ai",
    "create_ai_for_enemy",
    "ENEMY_AI_PRESETS",
    # Dimensional UI
    "DimensionalCombatUI",
    "AnimatedBar",
    "CombatMenuItem",
    # Dimensional Integration
    "DimensionalCombatIntegration",
    "DimensionalEncounterConfig",
    "RealmEncounterTable",
    "TransitionState",
    "create_dimensional_combat_integration",
    # Story Encounters
    "StoryEncounter",
    "StoryEncounterType",
    "StoryEncounterManager",
    "ENCOUNTERS_1D",
    "get_encounter_manager",
]


def run_combat_demo():
    """Run the standalone combat demo."""
    from .demo import run_demo
    run_demo()


def run_dimensional_combat_demo():
    """Run the new dimensional combat demo."""
    import pygame
    from .dimensional_battle_system import create_dimensional_battle_system
    from .enemies import get_enemy
    
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption("Dimensional Combat Demo")
    clock = pygame.time.Clock()
    
    # Create battle system
    battle = create_dimensional_battle_system(640, 480)
    
    # Start with a 4D enemy to showcase all features
    battle.start_battle("tesseract_citizen")
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    direction = -1 if event.key == pygame.K_LEFT else 1
                    battle.move_menu(direction)
            
            battle.handle_input(event)
        
        battle.update(dt)
        
        screen.fill((0, 0, 0))
        battle.draw(screen)
        pygame.display.flip()
        
        # End battle check
        if battle.state and battle.state.result != CombatResult.ONGOING:
            if battle.state.phase in (CombatPhase.VICTORY, CombatPhase.SPARE, 
                                      CombatPhase.DEFEAT, CombatPhase.FLEE):
                pass  # Let ending animation play
    
    pygame.quit()
