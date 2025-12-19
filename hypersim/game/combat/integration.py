"""Combat system integration with the main game loop.

This module handles:
- Encounter triggers (random, scripted, boss)
- Battle transitions (fade in/out, music changes)
- Combat state management within the game loop
- Reward distribution after battles
- Realm-based encounter tables
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

import pygame

from .core import CombatState, CombatPhase, CombatResult, CombatStats
from .battle import BattleSystem, BattleBox
from .ui import CombatUI
from .enemies import CombatEnemy, get_enemy
from .enemies_expanded import get_expanded_enemy, get_all_expanded_enemies
from .realms import Realm, get_realm, get_realms_for_dimension
from .dimensional_mechanics import (
    DimensionalCombatState, PerceptionLevel, RealityWarpType,
    DimensionalShiftState, GrazingSystem
)

if TYPE_CHECKING:
    from hypersim.game.session import GameSession


class EncounterType(Enum):
    """Types of combat encounters."""
    RANDOM = auto()       # Random overworld encounter
    SCRIPTED = auto()     # Story-triggered encounter
    BOSS = auto()         # Boss battle
    AMBUSH = auto()       # Surprise attack (no flee first turn)
    PEACEFUL = auto()     # Can avoid fight entirely


@dataclass
class EncounterConfig:
    """Configuration for an encounter."""
    enemy_id: str
    encounter_type: EncounterType = EncounterType.RANDOM
    
    # Intro customization
    custom_intro: Optional[str] = None
    
    # Rewards
    bonus_xp: int = 0
    bonus_gold: int = 0
    guaranteed_item: Optional[str] = None
    
    # Battle modifiers
    enemy_hp_modifier: float = 1.0
    enemy_atk_modifier: float = 1.0
    
    # Flags
    can_flee: bool = True
    can_spare: bool = True
    story_critical: bool = False


@dataclass
class EncounterTable:
    """Table of possible encounters for a realm."""
    realm_id: str
    encounters: List[Tuple[str, float]] = field(default_factory=list)  # (enemy_id, weight)
    
    # Encounter rate
    base_encounter_rate: float = 0.1  # 10% per step
    steps_since_encounter: int = 0
    
    # Boss encounters
    boss_id: Optional[str] = None
    boss_defeated: bool = False
    
    def roll_encounter(self) -> Optional[str]:
        """Roll for a random encounter. Returns enemy_id or None."""
        self.steps_since_encounter += 1
        
        # Increase rate with steps (pity system)
        current_rate = min(0.5, self.base_encounter_rate + self.steps_since_encounter * 0.02)
        
        if random.random() < current_rate:
            self.steps_since_encounter = 0
            return self._pick_enemy()
        
        return None
    
    def _pick_enemy(self) -> Optional[str]:
        """Pick an enemy from the weighted table."""
        if not self.encounters:
            return None
        
        total_weight = sum(weight for _, weight in self.encounters)
        roll = random.random() * total_weight
        
        cumulative = 0.0
        for enemy_id, weight in self.encounters:
            cumulative += weight
            if roll <= cumulative:
                return enemy_id
        
        return self.encounters[-1][0]


class CombatIntegration:
    """Integrates combat system with the main game loop."""
    
    def __init__(self, screen: pygame.Surface, session: "GameSession"):
        self.screen = screen
        self.session = session
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Combat systems
        self.battle_system = BattleSystem(self.width, self.height)
        self.combat_ui = CombatUI(screen)
        
        # Dimensional mechanics
        self.dimensional_state = DimensionalCombatState()
        
        # State
        self.in_combat = False
        self.current_encounter: Optional[EncounterConfig] = None
        self.current_enemy: Optional[CombatEnemy] = None
        
        # Encounter tables per realm
        self.encounter_tables: Dict[str, EncounterTable] = {}
        self._build_encounter_tables()
        
        # Transition effects
        self.transition_alpha = 0
        self.transitioning = False
        self.transition_callback: Optional[Callable] = None
        
        # Callbacks
        self.on_combat_end: Optional[Callable[[CombatResult, int, int], None]] = None
        self.on_boss_defeated: Optional[Callable[[str], None]] = None
        
        # Player stats (persisted across battles)
        self.player_stats = CombatStats(
            hp=20, max_hp=20, attack=10, defense=10
        )
    
    def _build_encounter_tables(self) -> None:
        """Build encounter tables for all realms."""
        # 1D Realms
        self.encounter_tables["origin_point"] = EncounterTable(
            realm_id="origin_point",
            encounters=[("point_spirit", 0.7), ("line_walker", 0.3)],
            base_encounter_rate=0.05,
        )
        self.encounter_tables["forward_path"] = EncounterTable(
            realm_id="forward_path",
            encounters=[
                ("line_walker", 0.5),
                ("forward_sentinel", 0.3),
                ("momentum_keeper", 0.2),
            ],
            base_encounter_rate=0.12,
        )
        self.encounter_tables["backward_void"] = EncounterTable(
            realm_id="backward_void",
            encounters=[
                ("void_echo", 0.5),
                ("reverse_walker", 0.3),
                ("negation_spirit", 0.2),
            ],
            base_encounter_rate=0.15,
        )
        self.encounter_tables["midpoint_station"] = EncounterTable(
            realm_id="midpoint_station",
            encounters=[("toll_collector", 1.0)],
            base_encounter_rate=0.03,  # Safe zone
        )
        self.encounter_tables["the_endpoint"] = EncounterTable(
            realm_id="the_endpoint",
            encounters=[("border_patrol", 0.7), ("segment_guardian", 0.3)],
            base_encounter_rate=0.1,
            boss_id="segment_guardian",
        )
        
        # 2D Realms
        self.encounter_tables["flatland_commons"] = EncounterTable(
            realm_id="flatland_commons",
            encounters=[
                ("triangle_scout", 0.4),
                ("square_citizen", 0.5),
                ("hexagon_worker", 0.1),
            ],
            base_encounter_rate=0.08,
        )
        self.encounter_tables["angular_heights"] = EncounterTable(
            realm_id="angular_heights",
            encounters=[
                ("triangle_scout", 0.3),
                ("isoceles_warrior", 0.3),
                ("scalene_assassin", 0.2),
                ("equilateral_champion", 0.2),
            ],
            base_encounter_rate=0.15,
            boss_id="right_angle_king",
        )
        self.encounter_tables["curved_depths"] = EncounterTable(
            realm_id="curved_depths",
            encounters=[
                ("circle_mystic", 0.5),
                ("ellipse_sage", 0.3),
                ("arc_phantom", 0.2),
            ],
            base_encounter_rate=0.1,
        )
        self.encounter_tables["fractal_frontier"] = EncounterTable(
            realm_id="fractal_frontier",
            encounters=[
                ("fractal_entity", 0.5),
                ("irregular_terror", 0.3),
                ("mandelbrot_spawn", 0.2),
            ],
            base_encounter_rate=0.18,
        )
        self.encounter_tables["dimensional_membrane"] = EncounterTable(
            realm_id="dimensional_membrane",
            encounters=[("depth_horror", 0.6), ("membrane_warper", 0.4)],
            base_encounter_rate=0.12,
            boss_id="membrane_warper",
        )
        
        # 3D Realms
        self.encounter_tables["geometric_citadel"] = EncounterTable(
            realm_id="geometric_citadel",
            encounters=[
                ("cube_guard", 0.4),
                ("pyramid_sentinel", 0.3),
                ("sphere_wanderer", 0.3),
            ],
            base_encounter_rate=0.08,
        )
        self.encounter_tables["platonic_plains"] = EncounterTable(
            realm_id="platonic_plains",
            encounters=[
                ("wild_tetrahedron", 0.3),
                ("roaming_octahedron", 0.3),
                ("feral_icosahedron", 0.2),
                ("sphere_wanderer", 0.2),
            ],
            base_encounter_rate=0.12,
        )
        self.encounter_tables["cavern_of_shadows"] = EncounterTable(
            realm_id="cavern_of_shadows",
            encounters=[
                ("shadow_cube", 0.4),
                ("cave_sphere", 0.3),
                ("darkness_tetrahedron", 0.3),
            ],
            base_encounter_rate=0.15,
        )
        self.encounter_tables["crystalline_spires"] = EncounterTable(
            realm_id="crystalline_spires",
            encounters=[
                ("crystal_guardian", 0.4),
                ("prism_elemental", 0.3),
                ("light_weaver", 0.3),
            ],
            base_encounter_rate=0.1,
        )
        self.encounter_tables["hyperborder"] = EncounterTable(
            realm_id="hyperborder",
            encounters=[
                ("tesseract_fragment", 0.4),
                ("hypercube_shard", 0.3),
                ("w_axis_phantom", 0.3),
            ],
            base_encounter_rate=0.12,
            boss_id="tesseract_guardian",
        )
        
        # 4D Realms
        self.encounter_tables["hyperspace_nexus"] = EncounterTable(
            realm_id="hyperspace_nexus",
            encounters=[
                ("tesseract_citizen", 0.4),
                ("hypersphere_wanderer", 0.4),
                ("ana_guardian", 0.2),
            ],
            base_encounter_rate=0.1,
        )
        self.encounter_tables["w_positive_reach"] = EncounterTable(
            realm_id="w_positive_reach",
            encounters=[
                ("possibility_entity", 0.4),
                ("future_echo", 0.3),
                ("potential_guardian", 0.3),
            ],
            base_encounter_rate=0.12,
        )
        self.encounter_tables["w_negative_depths"] = EncounterTable(
            realm_id="w_negative_depths",
            encounters=[
                ("memory_specter", 0.5),
                ("regret_manifestation", 0.3),
                ("past_self", 0.2),
            ],
            base_encounter_rate=0.15,
        )
        self.encounter_tables["beyond_threshold"] = EncounterTable(
            realm_id="beyond_threshold",
            encounters=[
                ("infinity_fragment", 0.6),
                ("threshold_guardian", 0.4),
            ],
            base_encounter_rate=0.1,
            boss_id="threshold_guardian",
        )
    
    def check_random_encounter(self, realm_id: str) -> Optional[str]:
        """Check for a random encounter in a realm. Returns enemy_id or None."""
        if self.in_combat:
            return None
        
        table = self.encounter_tables.get(realm_id)
        if not table:
            return None
        
        return table.roll_encounter()
    
    def start_encounter(self, config: EncounterConfig) -> bool:
        """Start a combat encounter."""
        if self.in_combat:
            return False
        
        # Try expanded enemies first, then fall back to original
        enemy = get_expanded_enemy(config.enemy_id)
        if not enemy:
            enemy = get_enemy(config.enemy_id)
        
        if not enemy:
            print(f"Warning: Enemy '{config.enemy_id}' not found")
            return False
        
        # Apply modifiers
        enemy.stats.max_hp = int(enemy.stats.max_hp * config.enemy_hp_modifier)
        enemy.stats.hp = enemy.stats.max_hp
        enemy.stats.attack = int(enemy.stats.attack * config.enemy_atk_modifier)
        
        if not config.can_flee:
            enemy.can_flee = False
        if not config.can_spare:
            enemy.can_spare = False
        
        # Store state
        self.current_encounter = config
        self.current_enemy = enemy
        
        # Start battle with transition
        self._start_battle_transition()
        
        return True
    
    def start_random_encounter(self, enemy_id: str) -> bool:
        """Start a random encounter with default config."""
        return self.start_encounter(EncounterConfig(
            enemy_id=enemy_id,
            encounter_type=EncounterType.RANDOM,
        ))
    
    def start_boss_encounter(self, enemy_id: str) -> bool:
        """Start a boss encounter."""
        return self.start_encounter(EncounterConfig(
            enemy_id=enemy_id,
            encounter_type=EncounterType.BOSS,
            can_flee=False,
            story_critical=True,
        ))
    
    def _start_battle_transition(self) -> None:
        """Start the transition into battle."""
        self.transitioning = True
        self.transition_alpha = 0
        self.transition_callback = self._begin_combat
    
    def _begin_combat(self) -> None:
        """Actually begin the combat after transition."""
        self.in_combat = True
        self.transitioning = False
        
        # Initialize battle system
        self.battle_system.start_battle(
            self.current_enemy.id,
            self.player_stats
        )
        self.battle_system.enemy = self.current_enemy
        
        # Reset dimensional state
        self.dimensional_state = DimensionalCombatState()
        
        # Set up end callback
        self.battle_system.on_battle_end = self._on_battle_end
    
    def _on_battle_end(self, result: CombatResult, xp: int, gold: int) -> None:
        """Handle battle end."""
        # Apply bonus rewards
        if self.current_encounter:
            xp += self.current_encounter.bonus_xp
            gold += self.current_encounter.bonus_gold
        
        # Update player stats from battle
        if self.battle_system.state:
            self.player_stats.hp = self.battle_system.state.player_stats.hp
        
        # Check boss defeat
        if (self.current_encounter and 
            self.current_encounter.encounter_type == EncounterType.BOSS and
            result == CombatResult.VICTORY):
            
            # Mark boss as defeated in encounter table
            for table in self.encounter_tables.values():
                if table.boss_id == self.current_enemy.id:
                    table.boss_defeated = True
            
            if self.on_boss_defeated:
                self.on_boss_defeated(self.current_enemy.id)
        
        # Transition out
        self._start_end_transition(result, xp, gold)
    
    def _start_end_transition(self, result: CombatResult, xp: int, gold: int) -> None:
        """Start transition out of battle."""
        self.transitioning = True
        self.transition_alpha = 255
        self.transition_callback = lambda: self._end_combat(result, xp, gold)
    
    def _end_combat(self, result: CombatResult, xp: int, gold: int) -> None:
        """Clean up after combat."""
        self.in_combat = False
        self.transitioning = False
        self.current_encounter = None
        self.current_enemy = None
        
        if self.on_combat_end:
            self.on_combat_end(result, xp, gold)
    
    def update(self, dt: float) -> None:
        """Update combat systems."""
        # Update transition
        if self.transitioning:
            if self.transition_callback == self._begin_combat:
                # Fading in
                self.transition_alpha = min(255, self.transition_alpha + 500 * dt)
                if self.transition_alpha >= 255:
                    self.transition_callback()
            else:
                # Fading out
                self.transition_alpha = max(0, self.transition_alpha - 500 * dt)
                if self.transition_alpha <= 0:
                    self.transition_callback()
        
        # Update combat
        if self.in_combat:
            self.battle_system.update(dt)
            self.dimensional_state.update(dt)
            self.combat_ui.update(dt)
            
            # Update grazing
            if self.battle_system.state and self.battle_system.state.phase == CombatPhase.ENEMY_ATTACK:
                self._check_grazing()
    
    def _check_grazing(self) -> None:
        """Check for grazing (near misses) and award bonuses."""
        if not self.battle_system.state:
            return
        
        soul = self.battle_system.state.player_soul
        
        for i, bullet in enumerate(self.battle_system.bullets):
            if self.dimensional_state.grazing.check_graze(
                soul.x, soul.y, i,
                bullet.x, bullet.y,
                bullet.radius, soul.radius
            ):
                # Award transcendence and resonance
                trans, res = self.dimensional_state.grazing.get_rewards()
                self.dimensional_state.shift_state.add_transcendence(trans)
                self.dimensional_state.resonance.add_resonance("plane", res)
    
    def handle_input(self, event: pygame.event.Event) -> bool:
        """Handle input during combat. Returns True if consumed."""
        if not self.in_combat:
            return False
        
        # Handle dimensional shift hotkeys
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                # Shift to Point (invulnerable freeze)
                if self.dimensional_state.shift_state.can_shift_to(PerceptionLevel.POINT):
                    self.dimensional_state.shift_state.shift_to(PerceptionLevel.POINT)
                    return True
            elif event.key == pygame.K_2:
                # Shift to Line (horizontal only)
                if self.dimensional_state.shift_state.can_shift_to(PerceptionLevel.LINE):
                    self.dimensional_state.shift_state.shift_to(PerceptionLevel.LINE)
                    return True
            elif event.key == pygame.K_3:
                # Return to Plane (default)
                self.dimensional_state.shift_state.current_perception = PerceptionLevel.PLANE
                return True
            elif event.key == pygame.K_4:
                # Shift to Volume (phase ability)
                if self.dimensional_state.shift_state.can_shift_to(PerceptionLevel.VOLUME):
                    self.dimensional_state.shift_state.shift_to(PerceptionLevel.VOLUME)
                    return True
            elif event.key == pygame.K_t:
                # Activate Transcendence
                if self.dimensional_state.shift_state.can_transcend():
                    self.dimensional_state.shift_state.activate_transcendence()
                    return True
            elif event.key == pygame.K_SPACE:
                # Phase dodge (if in Volume mode)
                if self.dimensional_state.try_phase():
                    return True
        
        # Pass to battle system
        return self.battle_system.handle_input(event)
    
    def draw(self) -> None:
        """Draw combat UI."""
        if self.in_combat:
            # Draw main combat
            self.combat_ui.draw(
                self.battle_system.state,
                self.battle_system.enemy,
                self.battle_system.battle_box,
                self.battle_system.bullets
            )
            
            # Draw dimensional UI elements
            self._draw_dimensional_ui()
        
        # Draw transition overlay
        if self.transitioning and self.transition_alpha > 0:
            overlay = pygame.Surface((self.width, self.height))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(int(self.transition_alpha))
            self.screen.blit(overlay, (0, 0))
    
    def _draw_dimensional_ui(self) -> None:
        """Draw dimensional combat UI elements."""
        font = pygame.font.Font(None, 20)
        
        # Shift energy bar
        shift_state = self.dimensional_state.shift_state
        bar_width = 150
        bar_height = 12
        bar_x = self.width - bar_width - 20
        bar_y = 20
        
        # Background
        pygame.draw.rect(self.screen, (40, 40, 60), 
                        (bar_x, bar_y, bar_width, bar_height))
        
        # Fill
        fill_width = int(bar_width * shift_state.shift_energy / shift_state.max_shift_energy)
        pygame.draw.rect(self.screen, (100, 200, 255),
                        (bar_x, bar_y, fill_width, bar_height))
        
        # Border
        pygame.draw.rect(self.screen, (150, 150, 200),
                        (bar_x, bar_y, bar_width, bar_height), 1)
        
        # Label
        label = font.render("SHIFT", True, (150, 150, 200))
        self.screen.blit(label, (bar_x - 45, bar_y))
        
        # Current perception
        perception_text = shift_state.current_perception.value.upper()
        perc_label = font.render(f"[{perception_text}]", True, (200, 200, 255))
        self.screen.blit(perc_label, (bar_x + bar_width + 5, bar_y))
        
        # Transcendence gauge
        trans_y = bar_y + 20
        trans_fill = int(bar_width * shift_state.transcendence_gauge / shift_state.transcendence_max)
        
        pygame.draw.rect(self.screen, (40, 40, 60),
                        (bar_x, trans_y, bar_width, bar_height))
        pygame.draw.rect(self.screen, (255, 200, 100),
                        (bar_x, trans_y, trans_fill, bar_height))
        pygame.draw.rect(self.screen, (200, 150, 100),
                        (bar_x, trans_y, bar_width, bar_height), 1)
        
        trans_label = font.render("TRANS", True, (200, 150, 100))
        self.screen.blit(trans_label, (bar_x - 45, trans_y))
        
        if shift_state.can_transcend():
            ready = font.render("[T] READY!", True, (255, 220, 100))
            self.screen.blit(ready, (bar_x + bar_width + 5, trans_y))
        
        # Graze counter
        graze_y = trans_y + 20
        graze_text = f"GRAZE: {self.dimensional_state.grazing.graze_count}"
        if self.dimensional_state.grazing.combo_count > 1:
            graze_text += f" (x{self.dimensional_state.grazing.combo_count})"
        graze_label = font.render(graze_text, True, (100, 255, 200))
        self.screen.blit(graze_label, (bar_x, graze_y))
        
        # Control hints
        hint_y = self.height - 60
        hints = [
            "[1-4] Shift Perception",
            "[T] Transcend",
            "[SPACE] Phase (3D mode)",
        ]
        for i, hint in enumerate(hints):
            hint_surf = font.render(hint, True, (100, 100, 120))
            self.screen.blit(hint_surf, (self.width - 180, hint_y + i * 15))


def create_combat_integration(screen: pygame.Surface, session: "GameSession") -> CombatIntegration:
    """Factory function to create combat integration."""
    return CombatIntegration(screen, session)
