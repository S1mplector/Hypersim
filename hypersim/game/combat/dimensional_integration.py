"""Dimensional Combat Integration - Connects dimensional battle system to game loop.

This module provides the integration layer between the new dimensional combat
system and the main game loop, handling:
- Combat transitions and state management
- Story/route tracking integration
- Progression system hooks
- Realm-based encounter configuration
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

import pygame

from .core import CombatResult, CombatStats, CombatPhase
from .dimensional_combat import CombatDimension, PerceptionState, get_dimension_from_enemy
from .dimensional_battle_system import DimensionalBattleSystem, create_dimensional_battle_system
from .combat_effects import get_effects_manager
from .enemies import get_enemy, CombatEnemy

if TYPE_CHECKING:
    from hypersim.game.session import GameSession


class TransitionState(Enum):
    """Combat transition states."""
    NONE = auto()
    ENTERING = auto()
    IN_COMBAT = auto()
    EXITING = auto()


@dataclass
class DimensionalEncounterConfig:
    """Configuration for a dimensional combat encounter."""
    enemy_id: str
    dimension: CombatDimension = CombatDimension.TWO_D
    
    # Encounter settings
    can_flee: bool = True
    is_boss: bool = False
    is_scripted: bool = False  # Part of story progression
    
    # Story hooks
    pre_battle_dialogue: Optional[str] = None
    victory_dialogue: Optional[str] = None
    spare_dialogue: Optional[str] = None
    defeat_dialogue: Optional[str] = None
    
    # Rewards
    xp_bonus: int = 0
    gold_bonus: int = 0
    
    # Unlock conditions
    unlocks_next_area: bool = False
    unlocks_dimension: Optional[str] = None


@dataclass
class RealmEncounterTable:
    """Encounter table for a specific realm."""
    realm_id: str
    dimension: CombatDimension
    
    # Encounter rates and enemies
    enemies: List[Tuple[str, float]] = field(default_factory=list)  # (enemy_id, weight)
    encounter_rate: float = 0.05  # Base chance per step
    
    # Realm modifiers
    difficulty_modifier: float = 1.0
    perception_modifier: Optional[PerceptionState] = None  # Forced starting perception


class DimensionalCombatIntegration:
    """Integrates the dimensional combat system with the game loop."""
    
    def __init__(self, screen: pygame.Surface, session: Optional["GameSession"] = None):
        self.screen = screen
        self.session = session
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Battle system (includes its own UI)
        self.battle_system = create_dimensional_battle_system(self.width, self.height)
        
        # State
        self.in_combat = False
        self.transitioning = False
        self.transition_state = TransitionState.NONE
        self.transition_progress = 0.0
        self.transition_speed = 2.0
        
        # Current encounter
        self.current_config: Optional[DimensionalEncounterConfig] = None
        self.current_enemy_id: Optional[str] = None
        
        # Player stats (persisted across battles)
        self.player_stats = CombatStats(hp=20, max_hp=20, attack=10, defense=10)
        
        # Realm encounter tables
        self.encounter_tables: Dict[str, RealmEncounterTable] = {}
        self._build_encounter_tables()
        
        # Callbacks
        self.on_combat_end: Optional[Callable[[CombatResult, int, int, str], None]] = None
        self.on_boss_defeated: Optional[Callable[[str], None]] = None
        self.on_dimension_unlock: Optional[Callable[[str], None]] = None
        
        # Wire up battle system callback
        self.battle_system.on_battle_end = self._handle_battle_end
    
    def _build_encounter_tables(self) -> None:
        """Build encounter tables for all realms."""
        # === 1D REALMS ===
        self.encounter_tables["origin_point"] = RealmEncounterTable(
            realm_id="origin_point",
            dimension=CombatDimension.ONE_D,
            enemies=[("point_spirit", 1.0)],
            encounter_rate=0.03,
            difficulty_modifier=0.8,
        )
        
        self.encounter_tables["forward_path"] = RealmEncounterTable(
            realm_id="forward_path",
            dimension=CombatDimension.ONE_D,
            enemies=[
                ("line_walker", 0.5),
                ("forward_sentinel", 0.3),
                ("point_spirit", 0.2),
            ],
            encounter_rate=0.05,
            difficulty_modifier=1.0,
        )
        
        self.encounter_tables["backward_void"] = RealmEncounterTable(
            realm_id="backward_void",
            dimension=CombatDimension.ONE_D,
            enemies=[
                ("void_echo", 0.6),
                ("point_spirit", 0.4),
            ],
            encounter_rate=0.04,
            difficulty_modifier=1.1,
        )
        
        self.encounter_tables["midpoint_station"] = RealmEncounterTable(
            realm_id="midpoint_station",
            dimension=CombatDimension.ONE_D,
            enemies=[("toll_collector", 1.0)],
            encounter_rate=0.02,  # Lower rate - it's a rest area
            difficulty_modifier=0.9,
        )
        
        self.encounter_tables["the_endpoint"] = RealmEncounterTable(
            realm_id="the_endpoint",
            dimension=CombatDimension.ONE_D,
            enemies=[
                ("forward_sentinel", 0.5),
                ("line_walker", 0.3),
                ("void_echo", 0.2),
            ],
            encounter_rate=0.06,
            difficulty_modifier=1.2,
        )
        
        # === 2D REALMS (placeholder for expansion) ===
        self.encounter_tables["flat_plains"] = RealmEncounterTable(
            realm_id="flat_plains",
            dimension=CombatDimension.TWO_D,
            enemies=[
                ("triangle_scout", 0.4),
                ("square_guard", 0.3),
                ("circle_spinner", 0.3),
            ],
            encounter_rate=0.05,
            difficulty_modifier=1.0,
        )
        
        # === 3D REALMS (placeholder) ===
        self.encounter_tables["depth_caves"] = RealmEncounterTable(
            realm_id="depth_caves",
            dimension=CombatDimension.THREE_D,
            enemies=[
                ("sphere_wanderer", 0.4),
                ("cube_guardian", 0.3),
                ("depth_stalker", 0.3),
            ],
            encounter_rate=0.05,
            difficulty_modifier=1.0,
        )
        
        # === 4D REALMS (placeholder) ===
        self.encounter_tables["temporal_nexus"] = RealmEncounterTable(
            realm_id="temporal_nexus",
            dimension=CombatDimension.FOUR_D,
            enemies=[
                ("tesseract_citizen", 0.4),
                ("hypercube_sentinel", 0.3),
                ("time_weaver", 0.3),
            ],
            encounter_rate=0.05,
            difficulty_modifier=1.0,
        )
    
    def check_random_encounter(self, realm_id: str) -> Optional[str]:
        """Check for a random encounter in the given realm.
        
        Returns enemy_id if encounter triggered, None otherwise.
        """
        table = self.encounter_tables.get(realm_id)
        if not table:
            return None
        
        # Roll for encounter
        if random.random() > table.encounter_rate:
            return None
        
        # Select enemy based on weights
        total_weight = sum(w for _, w in table.enemies)
        roll = random.random() * total_weight
        
        cumulative = 0.0
        for enemy_id, weight in table.enemies:
            cumulative += weight
            if roll <= cumulative:
                return enemy_id
        
        return table.enemies[0][0] if table.enemies else None
    
    def start_encounter(self, config: DimensionalEncounterConfig) -> bool:
        """Start a dimensional combat encounter."""
        if self.in_combat or self.transitioning:
            return False
        
        enemy = get_enemy(config.enemy_id)
        if not enemy:
            return False
        
        self.current_config = config
        self.current_enemy_id = config.enemy_id
        
        # Start transition
        self.transitioning = True
        self.transition_state = TransitionState.ENTERING
        self.transition_progress = 0.0
        
        return True
    
    def start_random_encounter(self, enemy_id: str, realm_id: Optional[str] = None) -> bool:
        """Start a random encounter with the given enemy."""
        enemy = get_enemy(enemy_id)
        if not enemy:
            return False
        
        # Get dimension from enemy or realm
        dimension = get_dimension_from_enemy(getattr(enemy, 'dimension', '2d'))
        
        # Check if it's a boss
        is_boss = getattr(enemy, 'is_boss', False)
        
        config = DimensionalEncounterConfig(
            enemy_id=enemy_id,
            dimension=dimension,
            can_flee=not is_boss,
            is_boss=is_boss,
        )
        
        return self.start_encounter(config)
    
    def update(self, dt: float) -> None:
        """Update combat system."""
        # Handle transitions
        if self.transitioning:
            self._update_transition(dt)
            return
        
        # Update battle (includes UI update)
        if self.in_combat:
            self.battle_system.update(dt)
            
            # Update battle system's UI
            if self.battle_system.state and self.battle_system.enemy:
                self.battle_system.ui.update(
                    dt,
                    self.battle_system.state.player_stats,
                    self.battle_system.enemy.stats,
                    self.battle_system.rules
                )
    
    def _update_transition(self, dt: float) -> None:
        """Update combat transition animation."""
        self.transition_progress += self.transition_speed * dt
        
        if self.transition_state == TransitionState.ENTERING:
            if self.transition_progress >= 1.0:
                # Start actual battle
                self._start_battle()
                self.transition_state = TransitionState.IN_COMBAT
                self.transitioning = False
                self.in_combat = True
        
        elif self.transition_state == TransitionState.EXITING:
            if self.transition_progress >= 1.0:
                self.transition_state = TransitionState.NONE
                self.transitioning = False
                self.in_combat = False
    
    def _start_battle(self) -> None:
        """Actually start the battle after transition."""
        if not self.current_config:
            return
        
        # Start battle with current player stats
        self.battle_system.start_battle(
            self.current_config.enemy_id,
            self.player_stats
        )
    
    def _handle_battle_end(self, result: CombatResult, xp: int, gold: int) -> None:
        """Handle battle ending."""
        # Apply config bonuses
        if self.current_config:
            xp += self.current_config.xp_bonus
            gold += self.current_config.gold_bonus
        
        # Update player stats from battle
        if self.battle_system.state:
            self.player_stats = self.battle_system.state.player_stats
        
        # Start exit transition
        self.transition_state = TransitionState.EXITING
        self.transition_progress = 0.0
        self.transitioning = True
        
        # Handle boss defeat
        if self.current_config and self.current_config.is_boss:
            if result == CombatResult.VICTORY or result == CombatResult.SPARE:
                if self.on_boss_defeated:
                    self.on_boss_defeated(self.current_config.enemy_id)
                
                # Check for dimension unlock
                if self.current_config.unlocks_dimension:
                    if self.on_dimension_unlock:
                        self.on_dimension_unlock(self.current_config.unlocks_dimension)
        
        # Trigger callback
        if self.on_combat_end:
            self.on_combat_end(result, xp, gold, self.current_enemy_id or "")
        
        # Clear current encounter
        self.current_config = None
        self.current_enemy_id = None
    
    def handle_input(self, event: pygame.event.Event) -> bool:
        """Handle input events. Returns True if consumed."""
        if not self.in_combat:
            return False
        
        return self.battle_system.handle_input(event)
    
    def draw(self) -> None:
        """Draw combat (including transitions)."""
        if self.transitioning:
            self._draw_transition()
            return
        
        if self.in_combat:
            self._draw_battle()
    
    def _draw_transition(self) -> None:
        """Draw combat transition effect."""
        # Fade effect
        alpha = int(255 * self.transition_progress) if self.transition_state == TransitionState.ENTERING else int(255 * (1 - self.transition_progress))
        
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))
        
        # Show encounter text during enter transition
        if self.transition_state == TransitionState.ENTERING and self.transition_progress > 0.3:
            font = pygame.font.Font(None, 48)
            
            if self.current_config and self.current_config.is_boss:
                text = "★ BOSS BATTLE ★"
                color = (255, 100, 100)
            else:
                text = "⚔ ENCOUNTER ⚔"
                color = (255, 255, 255)
            
            text_surf = font.render(text, True, color)
            text_x = (self.width - text_surf.get_width()) // 2
            text_y = (self.height - text_surf.get_height()) // 2
            self.screen.blit(text_surf, (text_x, text_y))
    
    def _draw_battle(self) -> None:
        """Draw the battle."""
        # Clear screen
        self.screen.fill((0, 0, 0))
        
        # Draw battle system (includes unified UI)
        self.battle_system.draw(self.screen)


def create_dimensional_combat_integration(
    screen: pygame.Surface,
    session: Optional["GameSession"] = None
) -> DimensionalCombatIntegration:
    """Create a new dimensional combat integration."""
    return DimensionalCombatIntegration(screen, session)
