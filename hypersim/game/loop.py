"""Main game loop integrating ECS, rendering, and session management."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

import pygame
import numpy as np

try:
    from PIL import Image, ImageSequence
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from hypersim.game.ecs.world import World
from hypersim.game.ecs.entity import Entity
from hypersim.game.ecs.component import (
    Transform, Velocity, Renderable, Collider, ColliderShape,
    Health, Controller, AIBrain, DimensionAnchor, Pickup, Portal
)
from hypersim.game.controllers.base import InputHandler
from hypersim.game.systems.input_system import InputSystem
from hypersim.game.systems.physics_system import PhysicsSystem
from hypersim.game.systems.collision_system import CollisionSystem
from hypersim.game.systems.damage_system import DamageSystem
from hypersim.game.systems.ai_system import AISystem
from hypersim.game.rendering.base_renderer import DimensionRenderer
from hypersim.game.rendering.line_renderer import LineRenderer
from hypersim.game.rendering.plane_renderer import PlaneRenderer
from hypersim.game.rendering.volume_renderer import VolumeRenderer
from hypersim.game.rendering.hyper_renderer import HyperRenderer
from hypersim.game.controllers.volume_controller import VolumeController
from hypersim.game.controllers.hyper_controller import HyperController
from hypersim.game.objectives import ObjectiveState

try:
    from hypersim.game.content import WorldLoader
except ImportError:
    WorldLoader = None

# New integrated systems
from hypersim.game.ui.textbox import DialogueSystem, DialogueLine, TextBoxStyle, create_campaign_dialogues
from hypersim.game.ui.overlay import OverlayManager
from hypersim.game.audio import AudioSystem, GameAudioHandler, get_audio_system
from hypersim.game.evolution import EvolutionState, PolytopeForm, get_evolution_system
from hypersim.game.story.campaign import Campaign
from hypersim.game.story.npc import NPCManager
from hypersim.game.story.lore import Codex
from hypersim.game.story.lore_expanded import discover_lore

# Combat system (old)
from hypersim.game.combat import (
    CombatIntegration, CombatResult, CombatStats,
    create_combat_integration, get_realms_for_dimension,
    get_starting_realm, EncounterConfig, EncounterType
)

# NEW Dimensional Combat System
from hypersim.game.combat import (
    DimensionalCombatIntegration, DimensionalEncounterConfig,
    create_dimensional_combat_integration, CombatDimension,
    get_encounter_manager, StoryEncounterManager
)

# Story/Narrative system
from hypersim.game.story.narrative import StoryManager, StoryRoute, StoryChapter, ENDINGS

if TYPE_CHECKING:
    from hypersim.game.content import WorldDefinition
    from hypersim.game.session import GameSession


class GameLoop:
    """Main game loop that orchestrates all systems."""
    
    def __init__(
        self,
        session: "GameSession",
        width: int = 1024,
        height: int = 768,
        title: str = "HyperSim",
        screen: Optional[pygame.Surface] = None,
        starting_world_id: Optional[str] = None,
    ):
        self.session = session
        self.title = title
        
        # Initialize pygame if needed
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        
        # Use provided screen or create new one
        if screen is not None:
            self.screen = screen
            self.width = screen.get_width()
            self.height = screen.get_height()
        else:
            self.width = width
            self.height = height
            self.screen = pygame.display.set_mode((width, height))
            pygame.display.set_caption(title)
        
        self.clock = pygame.time.Clock()
        
        # Campaign/dialogue queues
        self._initial_dialogue_id: Optional[str] = None
        self._queued_dialogues: List[str] = []
        self._initial_dialogue_played = False
        
        # Create world and systems
        self.world = World()
        self.input_handler = InputHandler()
        
        # Initialize systems
        self.input_system = InputSystem(self.input_handler)
        self.ai_system = AISystem()
        self.physics_system = PhysicsSystem()
        self.collision_system = CollisionSystem()
        self.damage_system = DamageSystem()
        
        self.world.add_system(self.input_system)
        self.world.add_system(self.ai_system)
        self.world.add_system(self.physics_system)
        self.world.add_system(self.collision_system)
        self.world.add_system(self.damage_system)
        
        # Initialize renderers per dimension
        self._renderers: Dict[str, DimensionRenderer] = {
            "1d": LineRenderer(self.screen),
            "2d": PlaneRenderer(self.screen),
            "3d": VolumeRenderer(self.screen),
            "4d": HyperRenderer(self.screen),
        }
        
        # Register 3D/4D controllers
        self._volume_controller = VolumeController()
        self._hyper_controller = HyperController()
        self.input_system.register_controller("volume", self._volume_controller)
        self.input_system.register_controller("3d", self._volume_controller)
        self.input_system.register_controller("hyper", self._hyper_controller)
        self.input_system.register_controller("4d", self._hyper_controller)
        
        # Mouse capture state for 3D/4D
        self._mouse_captured = False
        
        # Game state
        self.running = False
        self.paused = False
        self.target_fps = 60
        self._runtime_initialized = False

        # Authored content/world state
        self._world_loader = WorldLoader() if WorldLoader else None
        self._default_world_ids = {
            "1d": "tutorial_1d",
            "2d": "tutorial_2d",
            "3d": "tutorial_3d",
            "4d": "tutorial_4d",
        }
        self.current_world_id = starting_world_id or session.progression.current_world_id or ""
        self._current_world_def: Optional["WorldDefinition"] = None
        self._world_objectives: List[ObjectiveState] = []
        self._pending_spawn_position: Optional[np.ndarray] = None
        
        # === NEW INTEGRATED SYSTEMS ===
        
        # Dialogue system
        self.dialogue = DialogueSystem(self.screen)
        for seq in create_campaign_dialogues():
            self.dialogue.register_sequence(seq)
        
        # Overlay manager (notifications, etc.)
        self.overlays = OverlayManager(self.screen)
        
        # Audio system
        self.audio = get_audio_system()
        self._audio_handler = GameAudioHandler(self.audio, self.world)
        
        # Evolution system (for 4D)
        self.evolution = get_evolution_system()
        self._evolution_state = EvolutionState()
        
        # Story/Campaign system
        self.campaign = Campaign()
        self.npc_manager = NPCManager()
        self.codex = Codex()
        
        # === NARRATIVE SYSTEM ===
        self.story = StoryManager()
        
        # Track dimension intro dialogues shown
        self._dimension_intros_shown: set = set(session.progression.shown_dimension_vignettes)
        
        # === COMBAT SYSTEM ===
        self.combat: Optional[CombatIntegration] = None
        self.dimensional_combat: Optional[DimensionalCombatIntegration] = None
        self.story_encounters: Optional[StoryEncounterManager] = None
        self._current_realm_id: Optional[str] = None
        self._steps_in_realm: int = 0
        self._current_encounter_entity: Optional[Entity] = None
        self._encounter_prompt_entity: Optional[Entity] = None
        self._use_dimensional_combat: bool = True  # Use new system by default
        
        # === 1D ONBOARDING / BIRTH RITUAL ===
        self._chapter_1_cinematic_played = False
        self._line_world_beats_seen: set[str] = set()
        self._line_trial_state: str = "inactive"  # inactive -> to_midpoint -> return_origin -> complete
        self._line_birth_state: str = "inactive"  # inactive -> cohere -> complete
        self._line_birth_hold_active = False
        self._line_birth_charge = 0.0
        self._line_birth_time = 0.0
        self._line_birth_flash = 0.0
        self._line_birth_intro_shown = False
        self._line_birth_music_active = False
        self._line_birth_trial_phase = "pulse"  # pulse -> gather -> endure -> stabilize -> weave -> seal
        self._line_birth_pulse_timer = 0.0
        self._line_birth_pulse_hits = 0
        self._line_birth_gather_collected = 0
        self._line_birth_gather_cursor = np.zeros(2, dtype=float)
        self._line_birth_endure_progress = 0.0
        self._line_birth_balance = 0.0
        self._line_birth_balance_velocity = 0.0
        self._line_birth_stability = 0.0
        self._line_birth_weave_progress = 0.0
        self._line_birth_weave_expected = 1
        self._line_birth_direction_bias = 0.0
        self._line_birth_seal_rotation = 0.0
        self._line_birth_seal_hits = 0
        self._line_birth_interstitial_active = False
        self._line_birth_interstitial_phase = ""
        self._line_birth_interstitial_timer = 0.0
        self._line_birth_interstitial_duration = 0.0
        self._line_birth_interstitial_dismissing = False
        self._line_birth_interstitial_dismiss_timer = 0.0
        self._line_birth_interstitial_seen: set[str] = set()
        self._line_birth_left_active = False
        self._line_birth_right_active = False
        self._line_birth_up_active = False
        self._line_birth_down_active = False
        self._line_birth_fail_flash = 0.0
        self._line_strain_axis = 0.0
        self._line_strain_bend = 0.0
        self._line_strain_flash = 0.0
        self._line_strain_shake = 0.0
        self._line_violation_meter = 0.0
        self._line_guardian_active = False
        self._line_guardian_time = 0.0
        self._line_guardian_rotation = 0.0
        self._line_guardian_flash = 0.0
        self._line_guardian_reset_pending = False
        self._line_guardian_music_active = False
        self._line_guardian_strikes = 0
        self._line_guardian_attack_timer = 0.0
        self._line_guardian_last_dialogue_index = -1
        self._line_guardian_transition_progress = 0.0
        self._guardian_nebula_frames: List[pygame.Surface] = []
        self._guardian_nebula_durations: List[float] = []
        self._guardian_nebula_frame_index = 0
        self._guardian_nebula_frame_timer = 0.0
        self._guardian_nebula_loaded = False
        
        # Input handler reference for launcher integration
        self._input = self.input_handler
        
        # Wire up event handlers
        self._setup_event_handlers()
    
    def _setup_event_handlers(self) -> None:
        """Set up event handlers for game events."""
        
        def on_collision(event):
            # Check for damage-dealing collisions
            entity_a = self.world.get(event.data.get("entity_a"))
            entity_b = self.world.get(event.data.get("entity_b"))
            
            if not entity_a or not entity_b:
                return
            
            # Determine which is player and which is other
            player = None
            other = None
            if entity_a.has_tag("player"):
                player = entity_a
                other = entity_b
            elif entity_b.has_tag("player"):
                player = entity_b
                other = entity_a
            
            if player and other:
                # Player colliding with encounter trigger - prompt or start combat.
                if other.has_tag("encounter_trigger"):
                    ai_brain = other.get(AIBrain)
                    if ai_brain and ai_brain.state.get("enemy_id"):
                        enemy_id = ai_brain.state["enemy_id"]
                        self._handle_encounter_contact(other, enemy_id)
                        return  # Don't deal damage if starting combat
                
                # Player colliding with regular enemy (no encounter system)
                if other.has_tag("enemy") and not other.has_tag("encounter_trigger"):
                    self.damage_system.queue_damage(player.id, 10.0)
                
                # Player colliding with pickup
                if other.get(Pickup):
                    self._collect_pickup(player, other)
        
        def on_interact(event):
            player = self.world.get(event.source_entity_id)
            if not player:
                return
            
            player_transform = player.get(Transform)
            if not player_transform:
                return
            
            # Check for nearby NPCs first (including The First Point)
            for entity in self.world.entities.values():
                if not entity.has_tag("interactable") and not entity.has_tag("npc"):
                    continue
                
                entity_transform = entity.get(Transform)
                if not entity_transform:
                    continue
                
                # Check distance (use 1D distance for 1D, 2D for others)
                dim_id = self.session.active_dimension.id
                if dim_id == "1d":
                    dist = abs(player_transform.position[0] - entity_transform.position[0])
                else:
                    dist = np.linalg.norm(
                        player_transform.position[:2] - entity_transform.position[:2]
                    )
                
                if dist < 3.0:
                    self._interact_with_npc(entity)
                    return
            
            # Check for nearby portals
            for entity in self.world.entities.values():
                portal = entity.get(Portal)
                if not portal or not portal.active:
                    continue
                
                entity_transform = entity.get(Transform)
                if not entity_transform:
                    continue
                
                # Check distance
                dist = np.linalg.norm(
                    player_transform.position[:2] - entity_transform.position[:2]
                )
                if dist < 2.0:
                    self._use_portal_entity(entity, portal)
                    break
        
        self.world.on_event("collision", on_collision)
        self.world.on_event("player_interact", on_interact)
        
        # Shared events for the encounter choice prompt.
        self.dialogue.register_event("encounter_choice_talk", self._on_encounter_choice_talk)
        self.dialogue.register_event("encounter_choice_ignore", self._on_encounter_choice_ignore)
        self.dialogue.register_event("encounter_choice_fight", self._on_encounter_choice_fight)
    
    def _collect_pickup(self, player: Entity, pickup_entity: Entity) -> None:
        """Handle player collecting a pickup."""
        pickup = pickup_entity.get(Pickup)
        if pickup.collected:
            return
        
        pickup.collected = True
        pickup_entity.active = False
        
        self.session.record_event("collect", item=pickup.item_type, count=pickup.value)
        self._record_world_event("collect", item=pickup.item_type, count=pickup.value)
        self.world.emit("pickup_collected", item=pickup.item_type, entity_id=pickup_entity.id)
        
        # Grant evolution XP in 4D
        dim_id = self.session.active_dimension.id
        if dim_id == "4d":
            xp_value = pickup.value * 10  # 10 XP per pickup value
            actual_xp, can_evolve = self._evolution_state.add_xp(xp_value)
            self.overlays.notify(f"+{actual_xp} Evolution XP", color=(200, 150, 255))
            
            if can_evolve:
                self.overlays.notify("★ EVOLUTION READY! ★", duration=5.0, color=(255, 220, 100))
        
        # Notification
        self.overlays.notify(f"Collected {pickup.item_type}!", color=(255, 220, 50))
    
    def _use_portal(self, portal: Portal) -> None:
        """Handle player entering a portal."""
        self._use_portal_entity(None, portal)

    def _use_portal_entity(self, portal_entity: Optional[Entity], portal: Portal) -> None:
        """Handle player entering a portal entity."""
        target_world_id = portal.target_world or ""
        target_dimension = portal.target_dimension or ""

        if target_world_id and not target_dimension and self._world_loader:
            try:
                target_dimension = self._world_loader.load(target_world_id).dimension
            except FileNotFoundError:
                target_dimension = ""

        if not target_world_id and target_dimension:
            target_world_id = self._get_default_world_id(target_dimension)

        if portal_entity is not None:
            self._record_world_event("interact", target=self._get_interaction_target(portal_entity))

        if target_dimension:
            self._record_world_event("dimension_changed", dimension_id=target_dimension)

        if target_world_id:
            self.current_world_id = target_world_id
            self.session.progression.advance_to_world(target_world_id)

        if portal.target_position is not None:
            self._pending_spawn_position = np.asarray(portal.target_position, dtype=np.float64).copy()

        if target_dimension:
            if target_dimension != self.session.active_dimension.id:
                self.session.set_dimension(target_dimension)
            self._reload_dimension()

    def _get_default_world_id(self, dimension_id: str) -> str:
        """Return the authored tutorial world for a dimension."""
        return self._default_world_ids.get(dimension_id, "")

    def _resolve_world_id_for_dimension(self, dimension_id: str) -> str:
        """Choose the best world id for the current dimension."""
        candidate = self.current_world_id or self.session.progression.current_world_id
        if candidate and self._world_loader:
            try:
                world_def = self._world_loader.load(candidate)
            except FileNotFoundError:
                pass
            else:
                if world_def.dimension == dimension_id:
                    return world_def.id
        return self._get_default_world_id(dimension_id)

    def _clear_dimension_bounds(self, dimension_id: str) -> None:
        """Clear any previously configured bounds for a dimension."""
        prefix = f"{dimension_id}_"
        for key in [key for key in self.physics_system.bounds if key.startswith(prefix)]:
            del self.physics_system.bounds[key]

    def _apply_world_bounds(self, world_def: "WorldDefinition") -> None:
        """Apply authored bounds to the physics system."""
        axis_map = {"x": 0, "y": 1, "z": 2, "w": 3}
        self._clear_dimension_bounds(world_def.dimension)
        for axis_name, bounds in world_def.bounds.items():
            axis_index = axis_map.get(axis_name)
            if axis_index is None:
                continue
            self.physics_system.set_bounds(world_def.dimension, axis_index, bounds[0], bounds[1])

    def _load_world_objectives(self, world_def: "WorldDefinition") -> None:
        """Restore authored objective progress for the active world."""
        snapshot = self.session.progression.world_objective_progress.get(world_def.id, {})
        self._world_objectives = []

        for spec in world_def.objectives:
            progress = min(spec.target, float(snapshot.get(spec.id, 0.0)))
            self._world_objectives.append(
                ObjectiveState(
                    spec=spec,
                    progress=progress,
                    completed=progress >= spec.target,
                )
            )

        if self._world_objectives and all(state.completed for state in self._world_objectives):
            self.session.progression.record_world_completion(world_def.id)
            if world_def.next_world:
                self.session.progression.unlock_world(world_def.next_world)

    def _persist_world_objectives(self) -> None:
        """Persist current world objective progress into progression state."""
        if not self.current_world_id or not self._world_objectives:
            return
        self.session.progression.world_objective_progress[self.current_world_id] = {
            state.spec.id: state.progress for state in self._world_objectives
        }

    def _record_world_event(self, event_type: str, **data) -> None:
        """Apply a gameplay event to the current authored world objectives."""
        if not self._world_objectives:
            return

        changed = False
        completed_labels: List[str] = []
        for state in self._world_objectives:
            was_completed = state.completed
            if state.apply_event(event_type, data):
                changed = True
                if not was_completed and state.completed:
                    completed_labels.append(state.spec.description or state.spec.id.replace("_", " ").title())

        if not changed:
            return

        self._persist_world_objectives()

        for label in completed_labels:
            self.overlays.notify(f"Objective complete: {label}", duration=2.4, color=(140, 220, 170))

        if self._current_world_def and all(state.completed for state in self._world_objectives):
            if self._current_world_def.next_world:
                self.session.progression.unlock_world(self._current_world_def.next_world)
            if self.session.progression.record_world_completion(self._current_world_def.id):
                self.overlays.notify(
                    f"World complete: {self._current_world_def.name}",
                    duration=3.0,
                    color=(120, 220, 170),
                )

    def _apply_pending_spawn_position(self) -> None:
        """Move the spawned player to a portal-defined destination if set."""
        if self._pending_spawn_position is None:
            return

        player = self.world.find_player()
        if player:
            transform = player.get(Transform)
            if transform:
                count = min(len(transform.position), len(self._pending_spawn_position))
                transform.position[:count] = self._pending_spawn_position[:count]

        self._pending_spawn_position = None

    def _get_interaction_target(self, entity: Entity) -> str:
        """Resolve a stable target id for authored interaction objectives."""
        ignored_tags = {"portal", "npc", "interactable", "friendly", "trigger"}
        named_tags = sorted(tag for tag in entity.tags if tag not in ignored_tags)
        if named_tags:
            return named_tags[0]
        return entity.id

    def _load_authored_world(self, dimension_id: str) -> bool:
        """Load the authored world for the active dimension if available."""
        if not self._world_loader:
            return False

        world_id = self._resolve_world_id_for_dimension(dimension_id)
        if not world_id:
            return False

        try:
            world_def = self._world_loader.load(world_id)
        except FileNotFoundError:
            return False

        if world_def.dimension != dimension_id:
            return False

        self._apply_world_bounds(world_def)
        self._current_world_def = world_def
        self.current_world_id = world_def.id
        self.session.progression.advance_to_world(world_def.id)
        self._world_loader.spawn_world(world_def, self.world)
        self._load_world_objectives(world_def)
        self._apply_pending_spawn_position()
        return True
    
    def _reload_dimension(self) -> None:
        """Reload the world for the current dimension."""
        # Clear existing entities
        self.world.clear()
        
        # Spawn player and entities for new dimension
        dim_id = self.session.active_dimension.id
        self._steps_in_realm = 0
        self._current_realm_id = None
        self._current_world_def = None
        self._world_objectives = []

        if not self._load_authored_world(dim_id):
            fallback_world_id = self._get_default_world_id(dim_id)
            if fallback_world_id:
                self.current_world_id = fallback_world_id
                self.session.progression.advance_to_world(fallback_world_id)
            self._spawn_default_level(dim_id)
            self._apply_pending_spawn_position()
        
        # Update input system
        self.input_system.set_dimension(dim_id)
        self._sync_line_birth_state()
        
        # Trigger dimension intro dialogue (first time only)
        self._trigger_dimension_intro(dim_id)

        if dim_id == "1d" and self._is_line_birth_active() and not self._line_birth_intro_shown:
            self._start_line_birth_ritual()

        # 1D-specific onboarding
        if dim_id != "1d" and self._line_trial_state != "complete":
            # Trial only runs in 1D; cancel if player leaves early.
            self._line_trial_state = "inactive"
        if dim_id != "1d":
            self._line_birth_state = "inactive"
            self._line_birth_hold_active = False
            self._line_birth_intro_shown = False
            self._line_birth_trial_phase = "pulse"
            self._line_birth_pulse_timer = 0.0
            self._line_birth_pulse_hits = 0
            self._line_birth_endure_progress = 0.0
            self._line_birth_balance = 0.0
            self._line_birth_balance_velocity = 0.0
            self._line_birth_stability = 0.0
            self._line_birth_left_active = False
            self._line_birth_right_active = False
            self._line_birth_fail_flash = 0.0
            self._line_strain_axis = 0.0
            self._line_strain_bend = 0.0
            self._line_strain_flash = 0.0
            self._line_strain_shake = 0.0
            self._line_violation_meter = 0.0
            self._line_guardian_active = False
            self._line_guardian_reset_pending = False
            self._line_guardian_strikes = 0
            self._line_guardian_attack_timer = 0.0
            self._line_guardian_last_dialogue_index = -1
            self._line_guardian_transition_progress = 0.0
            self._sync_line_birth_music()
            self._stop_line_guardian_music()
        
        # Set evolution state for 4D renderer
        if dim_id == "4d":
            renderer = self._renderers.get("4d")
            if renderer and hasattr(renderer, "set_evolution_state"):
                renderer.set_evolution_state(self._evolution_state)
        
        # Notify dimension change
        dim_name = self.session.active_dimension.name
        self.overlays.notify(f"Entered {dim_name}", duration=3.0, color=(150, 200, 255))
        self.audio.play("dimension_shift")

    def _finish_line_birth_onboarding(self) -> None:
        """Silently transition from birth into normal 1D play."""
        self._chapter_1_cinematic_played = True
        if self.current_world_id == "tutorial_1d":
            self._spawn_first_point_npc()
        self.overlays.notify("The Line admits you.", duration=2.6, color=(180, 230, 255))
    
    def _trigger_dimension_intro(self, dim_id: str) -> None:
        """Trigger intro dialogue for a dimension (first time only)."""
        if dim_id in self._dimension_intros_shown:
            return
        
        self._dimension_intros_shown.add(dim_id)
        self.session.progression.shown_dimension_vignettes.add(dim_id)
        
        # The 1D opening is now entirely handled by the birth ritual.
        if dim_id == "1d" and not self._chapter_1_cinematic_played:
            if self.current_world_id == "tutorial_1d" and self.session.progression.lineage_ritual_state != "complete":
                self._start_line_birth_ritual()
            else:
                self._finish_line_birth_onboarding()
            return
        
        # Map dimensions to dialogue sequences
        if dim_id in ("2d", "3d", "4d"):
            self._play_dimension_vignette(dim_id)

        # Outsider vignette when returning to a lower dimension after ascension
        highest_order = self.session.progression.highest_unlocked_order(self.session.dimensions)
        current_order = self.session.dimensions.get(dim_id).order
        if highest_order > current_order and not self.session.progression.outsider_cutscene_played:
            self._play_outsider_cutscene()

    def _play_dimension_vignette(self, dim_id: str) -> None:
        """Dimension entry vignette with philosophical framing."""
        from hypersim.game.ui.textbox import TextBoxStyle
        impulse = self.session.progression.intro_impulse or "lean"
        impulse_phrase = {
            "lean": "You lead with motion.",
            "listen": "You lead with patience.",
            "hesitate": "You measure before moving.",
        }.get(impulse, "You carry the question of how to act.")
        
        base_lines = [
            {"text": "...", "style": TextBoxStyle.DIMENSION, "duration": 0.8},
            {"text": impulse_phrase, "style": TextBoxStyle.NARRATOR},
        ]
        
        if dim_id == "2d":
            lines = base_lines + [
                {"text": "A sideways axis tears open. Up and down invent privacy.", "speaker": "The Voice", "style": TextBoxStyle.DIMENSION},
                {"text": "Welcome to the SECOND DIMENSION.", "speaker": "The Voice", "style": TextBoxStyle.DIMENSION},
                {"text": "Move freely with WASD. Corners now matter; edges can enclose you.", "style": TextBoxStyle.TUTORIAL},
            ]
        elif dim_id == "3d":
            lines = base_lines + [
                {"text": "Depth unfolds. Shadows become volumes. You feel weight behind every surface.", "speaker": "The Voice", "style": TextBoxStyle.DIMENSION},
                {"text": "Welcome to the THIRD DIMENSION.", "speaker": "The Voice", "style": TextBoxStyle.DIMENSION},
                {"text": "Move with WASD, look with the mouse. Space to rise, Ctrl to descend.", "style": TextBoxStyle.TUTORIAL},
            ]
        else:  # 4d
            lines = base_lines + [
                {"text": "Time and space braid together. You sense insides and futures at once.", "speaker": "The Voice", "style": TextBoxStyle.DIMENSION},
                {"text": "Welcome to the FOURTH DIMENSION.", "speaker": "The Voice", "style": TextBoxStyle.DIMENSION},
                {"text": "Use Q and E to move along the W axis. Your polytope form will evolve.", "style": TextBoxStyle.TUTORIAL},
            ]
        
        self._play_sequence_inline(f"vignette_{dim_id}", lines, pause=True)

    def _play_outsider_cutscene(self) -> None:
        """Show how lower dimensions perceive you after ascension."""
        from hypersim.game.ui.textbox import TextBoxStyle
        self.session.progression.outsider_cutscene_played = True
        lines = [
            {"text": "...", "style": TextBoxStyle.DIMENSION, "duration": 1.0},
            {"text": "You return as a fracture in their sky.", "style": TextBoxStyle.NARRATOR},
            {"text": "Voices overlap. Shapes flicker. Cause and effect blur.", "style": TextBoxStyle.NARRATOR},
            {"text": "To them, you are a rumor of a higher place.", "speaker": "The Voice", "style": TextBoxStyle.DIMENSION},
            {"text": "Move gently. You carry axes they cannot name.", "speaker": "The Voice", "style": TextBoxStyle.DIMENSION},
        ]
        self._play_sequence_inline("outsider_return", lines, pause=True)

    def _maybe_trigger_shift_tutorial(self) -> None:
        """Fire the 1D shift tutorial once."""
        from hypersim.game.ui.textbox import TextBoxStyle
        if self.session.progression.shift_tutorial_done or self.dialogue.is_active:
            return
        self.session.progression.shift_tutorial_done = True
        lines = [
            {"text": "...", "style": TextBoxStyle.DIMENSION, "duration": 0.6},
            {"text": "Instinct whispers: you can vanish for a heartbeat.", "speaker": "The Voice", "style": TextBoxStyle.DIMENSION},
            {"text": "Tap Shift to slip aside and let collisions pass through.", "style": TextBoxStyle.TUTORIAL},
            {"text": "This is the first muscle of ascent. It will cost focus; use it with intent.", "speaker": "The Voice", "style": TextBoxStyle.DIMENSION},
        ]
        self._play_sequence_inline("shift_tutorial_1d", lines, pause=True)

    def _maybe_trigger_terminus_cutscene(self) -> None:
        """Show the 1D Terminus cutscene with ascend/stay choice."""
        from hypersim.game.ui.textbox import DialogueSequence, DialogueLine, TextBoxStyle
        if self.session.progression.terminus_seen or self.dialogue.is_active:
            return
        self.session.progression.terminus_seen = True
        # Unlock related lore
        discover_lore("tessera_prologue")
        discover_lore("monodia_sparks")
        discover_lore("monodia_terminus")

        seq_id = "terminus_cutscene"
        lines = [
            DialogueLine(text="The Line thins. Vibrations fade. You feel a pull sideways.", style=TextBoxStyle.NARRATOR),
            DialogueLine(text="This is the Terminus.", speaker="The Voice", style=TextBoxStyle.DIMENSION),
            DialogueLine(text="To step is to lose your home, to gain a width you cannot explain.", speaker="The Voice", style=TextBoxStyle.DIMENSION),
            DialogueLine(
                text="Do you ascend now?",
                speaker="The Voice",
                style=TextBoxStyle.DIMENSION,
                choices=[
                    ("Step into width.", "terminus_ascend"),
                    ("Stay on the Line for now.", "terminus_stay"),
                ],
            ),
        ]
        seq = DialogueSequence(
            id=seq_id,
            lines=lines,
            pause_game=True,
        )
        self.dialogue.register_sequence(seq)
        self.dialogue.register_event("terminus_ascend", self._handle_terminus_ascend)
        self.dialogue.register_event("terminus_stay", self._handle_terminus_stay)
        self.dialogue.start_sequence(seq_id)

    def _handle_terminus_ascend(self) -> None:
        """Handle immediate ascension from the Terminus cutscene."""
        self.dialogue.stop()
        next_dim = self.session.dimensions.next(self.session.active_dimension.id)
        if not next_dim:
            return

        self._record_world_event("dimension_changed", dimension_id=next_dim.id)
        next_world_id = self._get_default_world_id(next_dim.id)
        if next_world_id:
            self.current_world_id = next_world_id
            self.session.progression.advance_to_world(next_world_id)

        if self.session.ascend():
            self._reload_dimension()

    def _handle_terminus_stay(self) -> None:
        """Handle choosing to stay on the Line."""
        self.dialogue.stop()
        self.overlays.notify("You remain on the Line—for now.", duration=2.5, color=(200, 180, 255))

    def _play_sequence_inline(self, seq_id: str, lines: list, pause: bool = True) -> None:
        """Register and start a one-off dialogue sequence."""
        from hypersim.game.ui.textbox import DialogueSequence, DialogueLine, TextBoxStyle
        if self.dialogue.is_active:
            return
        dl_lines = []
        for item in lines:
            dl_lines.append(DialogueLine(
                speaker=item.get("speaker", ""),
                text=item.get("text", ""),
                style=item.get("style", TextBoxStyle.NARRATOR),
                choices=item.get("choices", []),
                duration=item.get("duration", 0.0),
                typing_speed=item.get("typing_speed", 30.0),
            ))
        seq = DialogueSequence(
            id=seq_id,
            lines=dl_lines,
            pause_game=pause,
        )
        self.dialogue.register_sequence(seq)
        self.dialogue.start_sequence(seq_id)

    def _is_line_birth_active(self) -> bool:
        """Return whether the emergence ritual is blocking normal gameplay."""
        return self._line_birth_state == "cohere"

    def _sync_line_birth_music(self) -> None:
        """Keep the 0D birthing music aligned with the emergence ritual."""
        should_play = (
            self.session.active_dimension.id == "1d"
            and self.current_world_id == "tutorial_1d"
            and self._is_line_birth_active()
        )
        if should_play:
            if not self._line_birth_music_active and self.audio.play_music("darkrumble0d.mp3"):
                self._line_birth_music_active = True
            return

        if self._line_birth_music_active:
            if pygame.mixer.get_init():
                try:
                    pygame.mixer.music.fadeout(900)
                except pygame.error:
                    self.audio.stop_music()
            else:
                self.audio.stop_music()
            self._line_birth_music_active = False

    def _start_line_guardian_music(self) -> None:
        """Start the guardian confrontation track."""
        if self._line_guardian_music_active:
            return
        if self.audio.play_music("guardianconfront.mp3"):
            self._line_birth_music_active = False
            self._line_guardian_music_active = True

    def _stop_line_guardian_music(self) -> None:
        """Stop the guardian confrontation track."""
        if not self._line_guardian_music_active:
            return
        if pygame.mixer.get_init():
            try:
                pygame.mixer.music.fadeout(1200)
            except pygame.error:
                self.audio.stop_music()
        else:
            self.audio.stop_music()
        self._line_guardian_music_active = False

    def _set_player_control_enabled(self, enabled: bool) -> None:
        """Enable or disable direct player control."""
        player = self.world.find_player()
        if not player:
            return

        controller = player.get(Controller)
        if controller:
            controller.enabled = enabled
            if not enabled:
                controller.clear_input()

        velocity = player.get(Velocity)
        if velocity is not None and not enabled:
            velocity.linear[:] = 0.0

    def _sync_line_birth_state(self) -> None:
        """Apply persisted ritual state to the freshly loaded 1D runtime."""
        if self.session.active_dimension.id != "1d" or self.current_world_id != "tutorial_1d":
            self._line_birth_state = "inactive"
            self._line_birth_hold_active = False
            self._line_birth_intro_shown = False
            self._line_birth_trial_phase = "pulse"
            self._line_birth_pulse_timer = 0.0
            self._line_birth_pulse_hits = 0
            self._line_birth_gather_collected = 0
            self._line_birth_gather_cursor[:] = 0.0
            self._line_birth_endure_progress = 0.0
            self._line_birth_balance = 0.0
            self._line_birth_balance_velocity = 0.0
            self._line_birth_stability = 0.0
            self._line_birth_weave_progress = 0.0
            self._line_birth_weave_expected = 1
            self._line_birth_direction_bias = 0.0
            self._line_birth_seal_rotation = 0.0
            self._line_birth_seal_hits = 0
            self._line_birth_interstitial_active = False
            self._line_birth_interstitial_phase = ""
            self._line_birth_interstitial_timer = 0.0
            self._line_birth_interstitial_duration = 0.0
            self._line_birth_interstitial_dismissing = False
            self._line_birth_interstitial_dismiss_timer = 0.0
            self._line_birth_interstitial_seen.clear()
            self._line_birth_left_active = False
            self._line_birth_right_active = False
            self._line_birth_up_active = False
            self._line_birth_down_active = False
            self._line_birth_fail_flash = 0.0
            return

        ritual_state = (self.session.progression.lineage_ritual_state or "complete").lower()
        if ritual_state == "direction":
            ritual_state = "cohere"
        if ritual_state not in {"cohere", "complete"}:
            ritual_state = "complete"

        self._line_birth_state = ritual_state
        self._line_birth_hold_active = False
        self._line_birth_charge = 1.0 if ritual_state != "cohere" else 0.0
        self._line_birth_time = 0.0
        self._line_birth_flash = 0.0
        self._line_birth_intro_shown = False
        self._line_birth_trial_phase = "pulse"
        self._line_birth_pulse_timer = 0.0
        self._line_birth_pulse_hits = 0
        self._line_birth_gather_collected = 0
        self._line_birth_gather_cursor[:] = 0.0
        self._line_birth_endure_progress = 0.0
        self._line_birth_balance = 0.0
        self._line_birth_balance_velocity = 0.0
        self._line_birth_stability = 0.0
        self._line_birth_weave_progress = 0.0
        self._line_birth_weave_expected = 1
        self._line_birth_direction_bias = 0.0
        self._line_birth_seal_rotation = 0.0
        self._line_birth_seal_hits = 0
        self._line_birth_interstitial_active = False
        self._line_birth_interstitial_phase = ""
        self._line_birth_interstitial_timer = 0.0
        self._line_birth_interstitial_duration = 0.0
        self._line_birth_interstitial_dismissing = False
        self._line_birth_interstitial_dismiss_timer = 0.0
        self._line_birth_interstitial_seen.clear()
        self._line_birth_left_active = False
        self._line_birth_right_active = False
        self._line_birth_up_active = False
        self._line_birth_down_active = False
        self._line_birth_fail_flash = 0.0

        player = self.world.find_player()
        if player:
            transform = player.get(Transform)
            if transform and ritual_state != "complete":
                transform.position[0] = 0.0
            velocity = player.get(Velocity)
            if velocity is not None and ritual_state != "complete":
                velocity.linear[:] = 0.0

        self._set_player_control_enabled(ritual_state == "complete")

    def _start_line_birth_ritual(self) -> None:
        """Begin the playable rite that lets the player become a point."""
        self._sync_line_birth_state()
        if not self._is_line_birth_active():
            return

        self._line_birth_intro_shown = True
        self._line_birth_time = 0.0
        self._set_player_control_enabled(False)
        if self._line_birth_state == "cohere" and self._line_birth_trial_phase == "pulse":
            self._start_line_birth_interstitial("pulse")

    def _line_birth_interstitial_lines(self, phase: str) -> list[str]:
        """Return the ritual lore fragments shown before each birth trial."""
        cards = {
            "pulse": [
                "You are not born yet.",
                "You are heat without shape.",
                "Strike the silence.",
                "Make the Line notice.",
            ],
            "gather": [
                "A spark arrives in pieces.",
                "The dark keeps what hesitates.",
                "Take the missing parts back.",
            ],
            "endure": [
                "Now keep them.",
                "The void will pull at the seams.",
                "Stay in the halo.",
                "Do not let yourself come apart again.",
            ],
            "stabilize": [
                "A spark is easy.",
                "A self is harder.",
                "Hold center.",
                "Do not shake loose.",
            ],
            "weave": [
                "Direction is repetition.",
                "Left. Right. Left. Right.",
                "Teach the world your pattern.",
            ],
            "seal": [
                "The opening is narrow.",
            ],
        }
        return cards.get(phase, [])

    def _start_line_birth_interstitial(self, phase: str) -> None:
        """Pause the ritual briefly to show a suspenseful lore card."""
        if phase in self._line_birth_interstitial_seen:
            return

        lines = self._line_birth_interstitial_lines(phase)
        if not lines:
            return

        char_count = sum(len(line) for line in lines)
        self._line_birth_interstitial_seen.add(phase)
        self._line_birth_interstitial_active = True
        self._line_birth_interstitial_phase = phase
        self._line_birth_interstitial_timer = 0.0
        self._line_birth_interstitial_duration = max(4.9, min(7.2, 2.3 + char_count / 26.0))
        self._line_birth_interstitial_dismissing = False
        self._line_birth_interstitial_dismiss_timer = 0.0

    def _begin_line_birth_interstitial_dismissal(self) -> None:
        """Start fading the ritual card back into the active minigame."""
        if not self._line_birth_interstitial_active or self._line_birth_interstitial_dismissing:
            return
        self._line_birth_interstitial_dismissing = True
        self._line_birth_interstitial_dismiss_timer = 0.0

    def _finish_line_birth_interstitial(self) -> None:
        """Dismiss the current ritual card and return control to the active trial."""
        self._line_birth_interstitial_active = False
        self._line_birth_interstitial_phase = ""
        self._line_birth_interstitial_timer = 0.0
        self._line_birth_interstitial_duration = 0.0
        self._line_birth_interstitial_dismissing = False
        self._line_birth_interstitial_dismiss_timer = 0.0
        self._line_birth_flash = max(self._line_birth_flash, 0.28)

    def _line_birth_pulse_radius(self) -> float:
        """Return the current collapse-ring radius for the first trial."""
        cycle_duration = 1.04
        progress = min(1.0, self._line_birth_pulse_timer / cycle_duration)
        return 214.0 - 182.0 * progress

    def _line_birth_pulse_precision(self) -> float:
        """Return how close the current pulse ring is to ideal convergence."""
        radius = self._line_birth_pulse_radius()
        ideal_radius = 46.0
        return max(0.0, 1.0 - abs(radius - ideal_radius) / 12.0)

    def _line_birth_gather_target_pos(self) -> np.ndarray:
        """Return the current gather-shard position in ritual-local space."""
        target_angle = self._line_birth_time * (1.28 + self._line_birth_gather_collected * 0.08) + self._line_birth_gather_collected * 1.17
        return np.array([
            math.cos(target_angle) * (118.0 + 10.0 * math.sin(self._line_birth_time * 1.2 + self._line_birth_gather_collected)),
            math.sin(target_angle * 1.18) * (88.0 + 8.0 * math.cos(self._line_birth_time * 0.9 + self._line_birth_gather_collected * 0.7)),
        ])

    def _line_birth_endure_radius(self) -> float:
        """Return the current safe radius for the endure phase."""
        return 34.0 + math.sin(self._line_birth_time * 3.4) * 6.0 + math.cos(self._line_birth_time * 1.8) * 2.0

    def _line_birth_stabilize_safe_limit(self) -> float:
        """Return the breathing center threshold for the stabilize phase."""
        return 0.12 + (0.5 + 0.5 * math.sin(self._line_birth_time * 2.8 + 0.7)) * 0.08

    def _line_birth_weave_beat_strength(self) -> float:
        """Return beat emphasis for the weave phase."""
        return 0.5 + 0.5 * math.sin(self._line_birth_time * 8.6)

    def _line_birth_seal_gate_span(self) -> float:
        """Return the current angular window for the seal phase."""
        return 0.17 + (0.5 + 0.5 * math.sin(self._line_birth_time * 2.2 + self._line_birth_seal_hits * 0.6)) * 0.08

    def _line_birth_scene_offset(self) -> tuple[int, int]:
        """Return a small camera offset for ritual impacts and instability."""
        intensity = self._line_birth_flash * 1.4 + self._line_birth_fail_flash * 2.2
        offset_x = int(math.sin(self._line_birth_time * 31.0) * intensity * 5.0 + math.cos(self._line_birth_time * 17.0) * self._line_birth_fail_flash * 3.0)
        offset_y = int(math.cos(self._line_birth_time * 27.0 + 0.7) * intensity * 4.0)
        return offset_x, offset_y

    def _attempt_line_birth_pulse(self) -> None:
        """Resolve a timing attempt during the first birth trial."""
        radius = self._line_birth_pulse_radius()
        precision = self._line_birth_pulse_precision()
        in_window = precision > 0.0
        self._line_birth_flash = 1.0
        self._line_birth_pulse_timer = 0.0

        if in_window:
            self._line_birth_pulse_hits = min(6, self._line_birth_pulse_hits + 1)
            self._line_birth_charge = min(0.5, self._line_birth_pulse_hits / 12.0 + precision * 0.035)
            self.audio.play("ability", volume_override=0.28)
            if self._line_birth_pulse_hits >= 6:
                self._line_birth_trial_phase = "gather"
                self._line_birth_gather_collected = 0
                self._line_birth_gather_cursor[:] = 0.0
                self._line_birth_fail_flash = 0.0
                self._start_line_birth_interstitial("gather")
        else:
            self._line_birth_pulse_hits = max(0, self._line_birth_pulse_hits - 1)
            self._line_birth_charge = max(0.0, self._line_birth_charge - 0.08)
            self._line_birth_fail_flash = 1.0
            self.audio.play("damage", volume_override=0.22)

    def _advance_line_birth_to_stabilize(self) -> None:
        """Move the ritual from scattered fragments into a coherent self."""
        self._line_birth_trial_phase = "stabilize"
        self._line_birth_balance = 0.0
        self._line_birth_balance_velocity = 0.0
        self._line_birth_stability = 0.0
        self._line_birth_fail_flash = 0.0
        self._line_birth_charge = max(self._line_birth_charge, 0.54)
        self._start_line_birth_interstitial("stabilize")

    def _advance_line_birth_to_endure(self) -> None:
        """Move the ritual into a survival phase where the spark must hold together."""
        self._line_birth_trial_phase = "endure"
        self._line_birth_endure_progress = 0.0
        self._line_birth_gather_cursor[:] = 0.0
        self._line_birth_fail_flash = 0.0
        self._line_birth_charge = max(self._line_birth_charge, 0.62)
        self._start_line_birth_interstitial("endure")

    def _advance_line_birth_to_weave(self) -> None:
        """Move the ritual into a rhythm-trial that hardens the spark into being."""
        self._line_birth_trial_phase = "weave"
        self._line_birth_weave_progress = 0.0
        self._line_birth_weave_expected = 1 if self._line_birth_direction_bias >= 0.0 else -1
        self._line_birth_fail_flash = 0.0
        self._line_birth_charge = max(self._line_birth_charge, 0.72)
        self._start_line_birth_interstitial("weave")

    def _attempt_line_birth_weave(self, direction_sign: int) -> None:
        """Resolve an alternating weave input during the fourth birth trial."""
        direction_sign = 1 if direction_sign >= 0 else -1
        beat_strength = self._line_birth_weave_beat_strength()
        on_beat = beat_strength >= 0.72
        self._line_birth_flash = 1.0
        self._line_birth_direction_bias += 0.12 * direction_sign

        if direction_sign == self._line_birth_weave_expected:
            gain = 0.24 if on_beat else 0.14
            self._line_birth_weave_progress = min(1.0, self._line_birth_weave_progress + gain)
            self._line_birth_charge = min(1.0, max(self._line_birth_charge, 0.74 + self._line_birth_weave_progress * 0.18))
            self._line_birth_weave_expected *= -1
            if not on_beat:
                self._line_birth_fail_flash = max(self._line_birth_fail_flash, 0.16)
            self.audio.play("ability", volume_override=0.28)
            if self._line_birth_weave_progress >= 1.0:
                self._advance_line_birth_to_seal()
        else:
            penalty = 0.22 if on_beat else 0.14
            self._line_birth_weave_progress = max(0.0, self._line_birth_weave_progress - penalty)
            self._line_birth_charge = max(0.62, self._line_birth_charge - 0.05)
            self._line_birth_fail_flash = 1.0
            self.audio.play("damage", volume_override=0.2)

    def _advance_line_birth_to_seal(self) -> None:
        """Move the ritual into its final convergence trial before direction exists."""
        self._line_birth_trial_phase = "seal"
        self._line_birth_seal_rotation = math.pi
        self._line_birth_seal_hits = 0
        self._line_birth_flash = 1.0
        self._line_birth_fail_flash = 0.0
        self._line_birth_charge = max(self._line_birth_charge, 0.76)
        self._start_line_birth_interstitial("seal")

    def _attempt_line_birth_seal(self) -> None:
        """Resolve the final convergence strike around the spark."""
        gate_angle = math.pi * 1.5
        angle = self._line_birth_seal_rotation % math.tau
        delta = abs((angle - gate_angle + math.pi) % math.tau - math.pi)
        in_window = delta <= self._line_birth_seal_gate_span()
        self._line_birth_flash = 1.0

        if in_window:
            self._line_birth_seal_hits = min(3, self._line_birth_seal_hits + 1)
            self._line_birth_charge = min(1.0, 0.78 + self._line_birth_seal_hits * 0.07)
            self._line_birth_seal_rotation = (self._line_birth_seal_rotation + 0.42) % math.tau
            self.audio.play("ability", volume_override=0.28)
            if self._line_birth_seal_hits >= 3:
                self._complete_line_birth_ritual()
        else:
            self._line_birth_seal_hits = max(0, self._line_birth_seal_hits - 1)
            self._line_birth_charge = max(0.58, self._line_birth_charge - 0.08)
            self._line_birth_fail_flash = 1.0
            self.audio.play("damage", volume_override=0.22)

    def _resolve_lineage_direction(self) -> str:
        """Derive a first direction from the birth ritual instead of a final menu choice."""
        return "forward" if self._line_birth_direction_bias >= 0.0 else "backward"

    def _line_birth_move_vector(self) -> np.ndarray:
        """Return current ritual movement input as a normalized 2D vector."""
        move_x = 0.0
        move_y = 0.0
        if self._line_birth_left_active:
            move_x -= 1.0
        if self._line_birth_right_active:
            move_x += 1.0
        if self._line_birth_up_active:
            move_y -= 1.0
        if self._line_birth_down_active:
            move_y += 1.0

        move = np.array([move_x, move_y], dtype=float)
        norm = float(np.linalg.norm(move))
        if norm > 1.0:
            move /= norm
        return move

    def _line_birth_endure_target(self) -> np.ndarray:
        """Return the moving sanctuary offset used by the endure phase."""
        return np.array(
            [
                math.sin(self._line_birth_time * 1.16) * 118.0 + math.cos(self._line_birth_time * 0.53) * 24.0,
                math.cos(self._line_birth_time * 1.42 + 0.5) * 76.0 + math.sin(self._line_birth_time * 0.84) * 18.0,
            ],
            dtype=float,
        )

    def _complete_line_birth_ritual(self) -> None:
        """Finish the rite and hand off into normal 1D play."""
        direction = self._resolve_lineage_direction()

        player = self.world.find_player()
        if player:
            transform = player.get(Transform)
            if transform:
                transform.position[0] = 0.8 if direction == "forward" else -0.8
            velocity = player.get(Velocity)
            if velocity is not None:
                velocity.linear[:] = 0.0

        self.session.progression.lineage_direction = direction
        self.session.progression.lineage_ritual_state = "complete"
        self._line_birth_state = "complete"
        self._line_birth_hold_active = False
        self._line_birth_flash = 1.0
        self._line_birth_time = 0.0
        self._line_birth_left_active = False
        self._line_birth_right_active = False
        self._line_birth_up_active = False
        self._line_birth_down_active = False
        self._line_birth_interstitial_active = False
        self._set_player_control_enabled(True)

        label = "Forward" if direction == "forward" else "Backward"
        color = (225, 190, 120) if direction == "forward" else (170, 185, 245)
        self.overlays.notify(f"The Line assigns: {label}", duration=2.8, color=color)
        self._finish_line_birth_onboarding()

    def _handle_line_birth_input(self, event: pygame.event.Event) -> bool:
        """Consume input for the line-birth ritual."""
        if not self._is_line_birth_active():
            return False
        phase = self._line_birth_trial_phase

        if self._line_birth_interstitial_active:
            if (
                event.type == pygame.KEYDOWN
                and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE)
                and self._line_birth_interstitial_timer >= 0.8
            ):
                self._begin_line_birth_interstitial_dismissal()
                return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self._line_birth_interstitial_timer >= 0.8:
                self._begin_line_birth_interstitial_dismissal()
                return True
            if event.type in (pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                return True

        if self._line_birth_state == "cohere":
            if phase == "pulse":
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._attempt_line_birth_pulse()
                    return True
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._attempt_line_birth_pulse()
                    return True
            elif self._line_birth_trial_phase in {"gather", "endure"}:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_a, pygame.K_LEFT):
                        self._line_birth_left_active = True
                        return True
                    if event.key in (pygame.K_d, pygame.K_RIGHT):
                        self._line_birth_right_active = True
                        return True
                    if event.key in (pygame.K_w, pygame.K_UP):
                        self._line_birth_up_active = True
                        return True
                    if event.key in (pygame.K_s, pygame.K_DOWN):
                        self._line_birth_down_active = True
                        return True
                if event.type == pygame.KEYUP:
                    if event.key in (pygame.K_a, pygame.K_LEFT):
                        self._line_birth_left_active = False
                        return True
                    if event.key in (pygame.K_d, pygame.K_RIGHT):
                        self._line_birth_right_active = False
                        return True
                    if event.key in (pygame.K_w, pygame.K_UP):
                        self._line_birth_up_active = False
                        return True
                    if event.key in (pygame.K_s, pygame.K_DOWN):
                        self._line_birth_down_active = False
                        return True
            elif self._line_birth_trial_phase == "weave":
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_a, pygame.K_LEFT):
                        self._attempt_line_birth_weave(-1)
                        return True
                    if event.key in (pygame.K_d, pygame.K_RIGHT):
                        self._attempt_line_birth_weave(1)
                        return True
            elif self._line_birth_trial_phase == "seal":
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._attempt_line_birth_seal()
                    return True
            elif self._line_birth_trial_phase == "stabilize":
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_a, pygame.K_LEFT):
                        self._line_birth_left_active = True
                        self._line_birth_direction_bias -= 0.02
                        return True
                    if event.key in (pygame.K_d, pygame.K_RIGHT):
                        self._line_birth_right_active = True
                        self._line_birth_direction_bias += 0.02
                        return True
                if event.type == pygame.KEYUP:
                    if event.key in (pygame.K_a, pygame.K_LEFT):
                        self._line_birth_left_active = False
                        return True
                    if event.key in (pygame.K_d, pygame.K_RIGHT):
                        self._line_birth_right_active = False
                        return True

        return False

    def _update_line_birth_ritual(self, dt: float) -> None:
        """Advance ritual animation and existence-gain progress."""
        if not self._is_line_birth_active():
            return

        self._line_birth_time += dt
        self._line_birth_flash = max(0.0, self._line_birth_flash - dt * 1.5)
        self._line_birth_fail_flash = max(0.0, self._line_birth_fail_flash - dt * 1.8)

        if self._line_birth_interstitial_active:
            self._line_birth_interstitial_timer += dt
            if self._line_birth_interstitial_dismissing:
                self._line_birth_interstitial_dismiss_timer += dt
            if self._line_birth_interstitial_dismissing and self._line_birth_interstitial_dismiss_timer >= 0.55:
                self._finish_line_birth_interstitial()
            return

        if self.dialogue.is_active:
            return

        if self._line_birth_state == "cohere":
            if self._line_birth_trial_phase == "pulse":
                cycle_duration = 1.04
                self._line_birth_pulse_timer += dt
                if self._line_birth_pulse_timer >= cycle_duration:
                    self._line_birth_pulse_timer -= cycle_duration
                    self._line_birth_pulse_hits = max(0, self._line_birth_pulse_hits - 1)
                    self._line_birth_charge = max(0.0, self._line_birth_charge - 0.06)
                    self._line_birth_fail_flash = max(self._line_birth_fail_flash, 0.58)
            elif self._line_birth_trial_phase == "gather":
                speed = 228.0
                move = self._line_birth_move_vector()
                flow = np.array([
                    math.sin(self._line_birth_time * 1.7 + self._line_birth_gather_cursor[1] * 0.02 + self._line_birth_gather_collected),
                    math.cos(self._line_birth_time * 1.35 + self._line_birth_gather_cursor[0] * 0.018 - self._line_birth_gather_collected * 0.6),
                ]) * 18.0
                self._line_birth_gather_cursor += move * speed * dt
                self._line_birth_gather_cursor += flow * dt
                self._line_birth_gather_cursor[0] = float(np.clip(self._line_birth_gather_cursor[0], -170.0, 170.0))
                self._line_birth_gather_cursor[1] = float(np.clip(self._line_birth_gather_cursor[1], -140.0, 140.0))

                target_pos = self._line_birth_gather_target_pos()
                if np.linalg.norm(self._line_birth_gather_cursor - target_pos) <= 26.0:
                    self._line_birth_gather_collected += 1
                    self._line_birth_charge = min(0.64, 0.5 + self._line_birth_gather_collected * 0.023)
                    self._line_birth_flash = 1.0
                    self._line_birth_gather_cursor *= 0.72
                    self.audio.play("ability", volume_override=0.24)
                    if self._line_birth_gather_collected >= 6:
                        self._advance_line_birth_to_endure()
            elif self._line_birth_trial_phase == "endure":
                speed = 204.0
                move = self._line_birth_move_vector()
                flow = np.array([
                    math.sin(self._line_birth_time * 3.6 + self._line_birth_gather_cursor[1] * 0.012),
                    math.cos(self._line_birth_time * 3.1 + self._line_birth_gather_cursor[0] * 0.014),
                ]) * 10.0
                self._line_birth_gather_cursor += move * speed * dt
                self._line_birth_gather_cursor += flow * dt
                self._line_birth_gather_cursor[0] = float(np.clip(self._line_birth_gather_cursor[0], -178.0, 178.0))
                self._line_birth_gather_cursor[1] = float(np.clip(self._line_birth_gather_cursor[1], -148.0, 148.0))

                target_pos = self._line_birth_endure_target()
                distance = float(np.linalg.norm(self._line_birth_gather_cursor - target_pos))
                safe_radius = self._line_birth_endure_radius()
                if distance <= safe_radius:
                    self._line_birth_endure_progress = min(1.0, self._line_birth_endure_progress + dt * 0.42)
                    self._line_birth_charge = min(0.76, max(self._line_birth_charge, 0.62 + self._line_birth_endure_progress * 0.14))
                else:
                    decay = 0.2 + max(0.0, distance - safe_radius) * 0.004
                    self._line_birth_endure_progress = max(0.0, self._line_birth_endure_progress - dt * decay)
                    if distance > 82.0:
                        self._line_birth_fail_flash = max(self._line_birth_fail_flash, 0.48)

                if self._line_birth_endure_progress >= 1.0:
                    self.audio.play("ability", volume_override=0.3)
                    self._advance_line_birth_to_stabilize()
            elif self._line_birth_trial_phase == "stabilize":
                drift = math.sin(self._line_birth_time * 2.35) * 0.68 + math.cos(self._line_birth_time * 1.28) * 0.26
                steer = 0.0
                if self._line_birth_left_active:
                    steer -= 1.0
                if self._line_birth_right_active:
                    steer += 1.0

                self._line_birth_balance_velocity += (drift + steer * 1.28 - self._line_birth_balance * 1.08) * dt
                self._line_birth_balance_velocity *= max(0.0, 1.0 - dt * 1.9)
                self._line_birth_balance += self._line_birth_balance_velocity * dt
                self._line_birth_balance = float(np.clip(self._line_birth_balance, -1.35, 1.35))

                safe_limit = self._line_birth_stabilize_safe_limit()
                centered = abs(self._line_birth_balance) < safe_limit
                if centered:
                    self._line_birth_stability = min(1.0, self._line_birth_stability + dt * 0.26)
                else:
                    penalty = 0.36 + max(0.0, abs(self._line_birth_balance) - safe_limit) * 0.52
                    self._line_birth_stability = max(0.0, self._line_birth_stability - dt * penalty)
                    if abs(self._line_birth_balance) > 0.74:
                        self._line_birth_fail_flash = max(self._line_birth_fail_flash, 0.72)

                self._line_birth_charge = min(1.0, 0.5 + self._line_birth_stability * 0.5)
                if self._line_birth_stability >= 1.0:
                    self._advance_line_birth_to_weave()
            elif self._line_birth_trial_phase == "weave":
                beat_strength = self._line_birth_weave_beat_strength()
                decay = 0.06 + 0.06 * (1.0 - beat_strength) + 0.05 * (1.0 - self._line_birth_weave_progress)
                self._line_birth_weave_progress = max(0.0, self._line_birth_weave_progress - dt * decay)
                self._line_birth_charge = max(0.68, 0.76 + self._line_birth_weave_progress * 0.18 - dt * 0.04)
            else:
                speed = 2.28 + self._line_birth_seal_hits * 0.48 + 0.24 * math.sin(self._line_birth_time * 1.6) + 0.12 * math.cos(self._line_birth_time * 3.0)
                self._line_birth_seal_rotation = (self._line_birth_seal_rotation + dt * speed) % math.tau
                self._line_birth_charge = min(
                    0.96,
                    max(
                        self._line_birth_charge,
                        0.72 + self._line_birth_seal_hits * 0.08 + (0.5 + 0.5 * math.sin(self._line_birth_time * 3.2)) * 0.03,
                    ),
                )

    def _draw_void_hint(self, text: str, center_y: int) -> None:
        """Draw a restrained hint for fullscreen ritual scenes."""
        font = getattr(self, "_void_hint_font", None)
        if font is None:
            font = pygame.font.Font(None, 26)
            self._void_hint_font = font

        text_surface = font.render(text, True, (170, 190, 204))
        pad_x = 16
        pad_y = 10
        panel = pygame.Surface((text_surface.get_width() + pad_x * 2, text_surface.get_height() + pad_y * 2), pygame.SRCALPHA)
        pygame.draw.rect(panel, (10, 14, 20, 132), panel.get_rect(), border_radius=14)
        pygame.draw.rect(panel, (42, 56, 72, 138), panel.get_rect(), width=1, border_radius=14)
        panel.blit(text_surface, (pad_x, pad_y))
        rect = panel.get_rect(center=(self.width // 2, center_y))
        self.screen.blit(panel, rect)

    def _load_guardian_nebula_frames(self) -> None:
        """Lazily load the interior guardian nebula animation."""
        if self._guardian_nebula_loaded:
            return

        self._guardian_nebula_loaded = True
        if not PIL_AVAILABLE:
            return

        nebula_path = Path(__file__).parent / "assets" / "gifs" / "nebula.gif"
        if not nebula_path.exists():
            return

        try:
            with Image.open(nebula_path) as gif:
                default_duration = gif.info.get("duration", 90)
                for frame in ImageSequence.Iterator(gif):
                    rgba = frame.convert("RGBA")
                    surface = pygame.image.fromstring(rgba.tobytes(), rgba.size, "RGBA").convert_alpha()
                    self._guardian_nebula_frames.append(surface)
                    duration_ms = frame.info.get("duration", default_duration)
                    self._guardian_nebula_durations.append(max(0.04, float(duration_ms) / 1000.0))
        except Exception:
            self._guardian_nebula_frames.clear()
            self._guardian_nebula_durations.clear()

    def _convex_hull_2d(self, points: list[tuple[int, int]]) -> list[tuple[int, int]]:
        """Return the monotonic-chain hull for a projected 2D point set."""
        unique = sorted(set(points))
        if len(unique) <= 2:
            return unique

        def cross(origin: tuple[int, int], a: tuple[int, int], b: tuple[int, int]) -> int:
            return (a[0] - origin[0]) * (b[1] - origin[1]) - (a[1] - origin[1]) * (b[0] - origin[0])

        lower: list[tuple[int, int]] = []
        for point in unique:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
                lower.pop()
            lower.append(point)

        upper: list[tuple[int, int]] = []
        for point in reversed(unique):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
                upper.pop()
            upper.append(point)

        return lower[:-1] + upper[:-1]

    def _draw_guardian_nebula(self, center: tuple[int, int], projected: list[tuple[int, int, float]]) -> None:
        """Render the animated nebula so it reads as interior depth inside the guardian."""
        self._load_guardian_nebula_frames()
        if not self._guardian_nebula_frames:
            return

        hull = self._convex_hull_2d([(x, y) for x, y, _depth in projected])
        if len(hull) < 3:
            return

        min_x = min(x for x, _y in hull)
        max_x = max(x for x, _y in hull)
        min_y = min(y for _x, y in hull)
        max_y = max(y for _x, y in hull)
        hull_w = max(64, max_x - min_x)
        hull_h = max(64, max_y - min_y)

        frame = self._guardian_nebula_frames[self._guardian_nebula_frame_index]
        scaled_w = int(hull_w * 1.7)
        scaled_h = int(hull_h * 1.7)
        nebula = pygame.transform.smoothscale(frame, (scaled_w, scaled_h))

        offset_x = int(math.sin(self._line_guardian_time * 0.44) * hull_w * 0.12)
        offset_y = int(math.cos(self._line_guardian_time * 0.37) * hull_h * 0.1)
        nebula_pos = (
            center[0] - scaled_w // 2 + offset_x,
            center[1] - scaled_h // 2 + offset_y,
        )

        interior_fill = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.polygon(interior_fill, (8, 24, 30, 120), hull)
        self.screen.blit(interior_fill, (0, 0))

        nebula_layer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        nebula_layer.blit(nebula, nebula_pos)

        cyan_tint = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        cyan_tint.fill((34, 214, 255, 26))
        nebula_layer.blit(cyan_tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        mask = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255, 255), hull)
        nebula_layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.screen.blit(nebula_layer, (0, 0))

        inner_glow = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.polygon(inner_glow, (86, 244, 255, 26), hull)
        pygame.draw.polygon(inner_glow, (146, 252, 255, 30), hull, width=4)
        self.screen.blit(inner_glow, (0, 0))

    def _draw_glow_circle_scene(
        self,
        center: tuple[int, int],
        radius: int,
        color: tuple[int, int, int],
        alpha: int,
    ) -> None:
        """Draw a soft glow circle for ritual/guardian fullscreen scenes."""
        radius = max(1, radius)
        surf = pygame.Surface((radius * 2 + 8, radius * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*color, max(0, min(255, alpha))), (radius + 4, radius + 4), radius)
        self.screen.blit(surf, (center[0] - radius - 4, center[1] - radius - 4))

    def _measure_pixel_text_line(self, text: str, font: pygame.font.Font, scale: int) -> int:
        """Measure a line for the ritual interstitial text renderer."""
        width = 0
        for char in text:
            width += max(6, font.size(char)[0] * scale)
        return width

    def _draw_shaky_pixel_text_block(self, lines: list[str], alpha: int) -> None:
        """Draw white pixel-text with per-letter shake for the ritual cards."""
        font = getattr(self, "_line_birth_interstitial_font", None)
        if font is None:
            font = pygame.font.Font(None, 16)
            self._line_birth_interstitial_font = font

        scale = 2
        line_height = font.get_height() * scale + 18
        total_height = len(lines) * line_height - 12
        start_y = self.height // 2 - total_height // 2
        visible_chars = int(max(0.0, self._line_birth_interstitial_timer - 0.18) * 34.0)
        global_char_index = 0

        for line_index, line in enumerate(lines):
            x = self.width // 2 - self._measure_pixel_text_line(line, font, scale) // 2
            y = start_y + line_index * line_height
            for char in line:
                char_width = max(6, font.size(char)[0] * scale)
                if visible_chars > 0 and char != " ":
                    glyph = font.render(char, False, (255, 255, 255))
                    glyph = pygame.transform.scale(glyph, (glyph.get_width() * scale, glyph.get_height() * scale))
                    glyph.set_alpha(alpha)
                    shake_tick = int(self._line_birth_interstitial_timer * 12.0)
                    noise_seed = global_char_index * 12.9898 + shake_tick * 78.233
                    noise_x = math.sin(noise_seed) * 43758.5453
                    noise_y = math.sin(noise_seed + 19.19) * 24634.6345
                    jitter_x = int(round(((noise_x - math.floor(noise_x)) - 0.5) * 1.6))
                    jitter_y = int(round(((noise_y - math.floor(noise_y)) - 0.5) * 1.8))
                    self.screen.blit(glyph, (x + jitter_x, y + jitter_y))
                if visible_chars > 0:
                    visible_chars -= 1
                global_char_index += 1
                x += char_width

    def _draw_line_birth_interstitial(self) -> None:
        """Draw the suspenseful lore card that precedes each ritual challenge."""
        self._draw_line_birth_challenge_scene(show_hint=False)

        fade_window = 0.55
        if self._line_birth_interstitial_dismissing:
            fade_out = max(0.0, 1.0 - self._line_birth_interstitial_dismiss_timer / fade_window)
            overlay_alpha = int(255 * fade_out)
            text_alpha = int(255 * min(1.0, self._line_birth_interstitial_timer / 0.4) * fade_out)
        else:
            overlay_alpha = 255
            text_alpha = int(255 * min(1.0, self._line_birth_interstitial_timer / 0.4))
        blackout = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        blackout.fill((0, 0, 0, max(0, min(255, overlay_alpha))))
        self.screen.blit(blackout, (0, 0))

        self._draw_shaky_pixel_text_block(self._line_birth_interstitial_lines(self._line_birth_interstitial_phase), text_alpha)
        if not self._line_birth_interstitial_dismissing and self._line_birth_interstitial_timer >= 0.8:
            self._draw_void_hint("CLICK / ENTER", self.height - 56)

    def _draw_line_birth_challenge_scene(self, show_hint: bool = True) -> None:
        """Render the playable emergence ritual scene."""
        if self.session.active_dimension.id != "1d":
            return

        self.screen.fill((0, 0, 0))

        center_x = self.width // 2
        center_y = self.height // 2 - 12
        phase = self._line_birth_trial_phase
        scene_offset_x, scene_offset_y = self._line_birth_scene_offset()
        center_x += scene_offset_x
        center_y += scene_offset_y

        pulse = 0.5 + 0.5 * np.sin(self._line_birth_time * 2.4)
        core_color = (164, 238, 255)
        ring_color = (215, 248, 255)

        spark_x = center_x
        spark_y = center_y
        if self._line_birth_state == "cohere" and phase in {"gather", "endure"}:
            spark_x += int(self._line_birth_gather_cursor[0])
            spark_y += int(self._line_birth_gather_cursor[1])
        elif self._line_birth_state == "cohere" and phase == "stabilize":
            spark_x += int(self._line_birth_balance * 170.0)

        ritual_move = self._line_birth_move_vector()

        dust = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for idx in range(32):
            seed = idx * 1.713
            drift = self._line_birth_time * (0.08 + idx * 0.002)
            dust_x = center_x + math.sin(seed + drift * 1.3) * (210 + idx * 13) + math.cos(drift + seed * 0.5) * 24
            dust_y = center_y + math.cos(seed * 1.9 + drift) * (138 + idx * 8)
            alpha = 10 + (idx % 6) * 5
            radius = 1 + (idx % 3)
            pygame.draw.circle(dust, (56, 76, 96, alpha), (int(dust_x), int(dust_y)), radius)
        self.screen.blit(dust, (0, 0))

        vignette = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for idx in range(6, 0, -1):
            radius = int(74 + idx * 48 + pulse * 10)
            alpha = int(8 + idx * 4 + self._line_birth_charge * 6)
            pygame.draw.circle(vignette, (8, 20, 28, alpha), (spark_x, spark_y), radius)
        self.screen.blit(vignette, (0, 0))

        void_arcs = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for idx in range(3):
            size = 220 + idx * 84
            rect = pygame.Rect(0, 0, size, size)
            rect.center = (center_x, center_y)
            arc_start = self._line_birth_time * (0.18 + idx * 0.05) + idx * 1.6
            arc_end = arc_start + math.pi * (0.76 + idx * 0.08)
            pygame.draw.arc(void_arcs, (18, 32, 44, 34 - idx * 6), rect, arc_start, arc_end, 2)
        self.screen.blit(void_arcs, (0, 0))

        for idx in range(12):
            orbit = self._line_birth_time * (0.9 + idx * 0.05) + idx * 0.56
            distance = 22 + idx * 8 - self._line_birth_charge * 14
            mote_x = spark_x + np.cos(orbit) * distance
            mote_y = spark_y + np.sin(orbit) * (18 + idx * 2.2)
            radius = 1 + (idx % 3)
            fade = 0.82 - idx * 0.05
            pygame.draw.circle(
                self.screen,
                tuple(int(channel * fade) for channel in core_color),
                (int(mote_x), int(mote_y)),
                radius,
            )

        orb_layer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        orb_count = 10
        for idx in range(orb_count):
            angle = self._line_birth_time * (0.74 + idx * 0.04) + idx * 0.63
            radius_x = 34 + idx * 10 - self._line_birth_charge * 8
            radius_y = 24 + idx * 6
            orb_x = spark_x + math.cos(angle) * radius_x
            orb_y = spark_y + math.sin(angle) * radius_y
            orb_radius = max(2, 4 - idx // 4)
            alpha = max(22, int(88 - idx * 5 + self._line_birth_charge * 24))
            orb = pygame.Surface((orb_radius * 2 + 6, orb_radius * 2 + 6), pygame.SRCALPHA)
            pygame.draw.circle(orb, (140, 228, 252, alpha), (orb_radius + 3, orb_radius + 3), orb_radius)
            orb_layer.blit(orb, (int(orb_x) - orb_radius - 3, int(orb_y) - orb_radius - 3))
        self.screen.blit(orb_layer, (0, 0))

        if phase in {"gather", "endure"} and float(np.linalg.norm(ritual_move)) > 0.0:
            trail_layer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            for idx in range(1, 5):
                falloff = 1.0 - idx / 5.0
                ghost_x = spark_x - ritual_move[0] * idx * 18.0
                ghost_y = spark_y - ritual_move[1] * idx * 18.0
                pygame.draw.circle(trail_layer, (136, 224, 248, int(42 * falloff)), (int(ghost_x), int(ghost_y)), max(2, int(5 * falloff)))
            self.screen.blit(trail_layer, (0, 0))

        base_radius = 10 + 12 * self._line_birth_charge + 4 * pulse
        self._draw_glow_circle_scene((spark_x, spark_y), int(base_radius * 2.4), (92, 212, 255), 32)
        self._draw_glow_circle_scene((spark_x, spark_y), int(base_radius * 1.5), (164, 238, 255), 74)
        pygame.draw.circle(self.screen, (214, 248, 255), (spark_x, spark_y), int(base_radius))
        pygame.draw.circle(self.screen, (255, 255, 255), (spark_x, spark_y), 3)

        if self._line_birth_state == "cohere":
            if self._line_birth_trial_phase == "pulse":
                ring_radius = int(self._line_birth_pulse_radius())
                target_radius = 46
                pulse_precision = self._line_birth_pulse_precision()
                pygame.draw.circle(self.screen, (34, 44, 68), (spark_x, spark_y), 96, 1)
                pygame.draw.circle(self.screen, (86, 116, 146), (spark_x, spark_y), target_radius, 1)
                pygame.draw.circle(self.screen, (176, 236, 255), (spark_x, spark_y), target_radius, 2 if pulse_precision > 0.55 else 1)
                pygame.draw.circle(self.screen, ring_color, (spark_x, spark_y), max(16, ring_radius), 3)
                for idx in range(3):
                    echo_radius = ring_radius + 28 + idx * 18
                    if echo_radius < 224:
                        pygame.draw.circle(
                            self.screen,
                            (58, 86, 112),
                            (spark_x, spark_y),
                            max(18, echo_radius),
                            1,
                        )
                for idx in range(4):
                    angle = self._line_birth_time * 1.8 + idx * (math.tau / 4.0)
                    inner = (
                        int(spark_x + math.cos(angle) * 26),
                        int(spark_y + math.sin(angle) * 26),
                    )
                    outer = (
                        int(spark_x + math.cos(angle) * (64 + pulse_precision * 12)),
                        int(spark_y + math.sin(angle) * (64 + pulse_precision * 12)),
                    )
                    pygame.draw.line(self.screen, (74, 108, 134), inner, outer, 2)

                for idx in range(6):
                    marker_x = center_x - 140 + idx * 56
                    marker_y = spark_y - 152
                    active = idx < self._line_birth_pulse_hits
                    color = (168, 230, 255) if active else (46, 54, 72)
                    pygame.draw.polygon(
                        self.screen,
                        color,
                        [
                            (marker_x, marker_y - 8),
                            (marker_x + 8, marker_y),
                            (marker_x, marker_y + 8),
                            (marker_x - 8, marker_y),
                        ],
                    )
            elif phase == "gather":
                target_pos = self._line_birth_gather_target_pos()
                target_x = center_x + target_pos[0]
                target_y = center_y + target_pos[1]
                gather_angle = self._line_birth_time * (1.28 + self._line_birth_gather_collected * 0.08) + self._line_birth_gather_collected * 1.17
                trail = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                for idx in range(1, 5):
                    trail_angle = gather_angle - idx * 0.28
                    trail_x = center_x + math.cos(trail_angle) * (118.0 + 10.0 * math.sin(self._line_birth_time * 1.2 + self._line_birth_gather_collected))
                    trail_y = center_y + math.sin(trail_angle * 1.18) * (88.0 + 8.0 * math.cos(self._line_birth_time * 0.9 + self._line_birth_gather_collected * 0.7))
                    pygame.draw.circle(trail, (124, 218, 244, max(18, 64 - idx * 12)), (int(trail_x), int(trail_y)), max(3, 7 - idx))
                self.screen.blit(trail, (0, 0))
                self._draw_glow_circle_scene((int(target_x), int(target_y)), 26, (98, 228, 255), 32)
                pygame.draw.circle(self.screen, (188, 246, 255), (int(target_x), int(target_y)), 10, 2)
                pygame.draw.circle(self.screen, (236, 252, 255), (int(target_x), int(target_y)), 4)
                tether = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                pygame.draw.line(tether, (70, 120, 148, 58), (spark_x, spark_y), (int(target_x), int(target_y)), 1)
                self.screen.blit(tether, (0, 0))
                for sign in (-1, 1):
                    phantom_x = center_x + math.cos(gather_angle + sign * 1.7) * 142.0
                    phantom_y = center_y + math.sin((gather_angle + sign * 1.4) * 1.08) * 96.0
                    pygame.draw.circle(self.screen, (54, 78, 98), (int(phantom_x), int(phantom_y)), 6, 1)

                for idx in range(6):
                    marker_x = center_x - 140 + idx * 56
                    marker_y = spark_y - 152
                    active = idx < self._line_birth_gather_collected
                    radius = 7 if active else 5
                    color = (164, 238, 255) if active else (42, 50, 66)
                    pygame.draw.circle(self.screen, color, (marker_x, marker_y), radius)
            elif phase == "endure":
                target = self._line_birth_endure_target()
                target_x = center_x + int(target[0])
                target_y = center_y + int(target[1])
                safe_radius = self._line_birth_endure_radius()
                halo_layer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                for radius, alpha in ((88, 18), (56, 26), (int(safe_radius), 54)):
                    pygame.draw.circle(halo_layer, (124, 232, 255, alpha), (target_x, target_y), radius, 1 if radius > safe_radius + 2 else 0)
                pygame.draw.circle(halo_layer, (222, 250, 255, 120), (target_x, target_y), 10)
                self.screen.blit(halo_layer, (0, 0))
                pygame.draw.line(self.screen, (72, 110, 136), (spark_x, spark_y), (target_x, target_y), 1)

                tendrils = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                for idx in range(4):
                    points = []
                    side = -1 if idx % 2 == 0 else 1
                    anchor_y = center_y - 170 + idx * 116
                    for step in range(8):
                        progress = step / 7.0
                        x = center_x + side * (220 - progress * 120) + math.sin(self._line_birth_time * 2.2 + idx * 0.8 + progress * 5.0) * 18
                        y = anchor_y + progress * 92 + math.cos(self._line_birth_time * 1.6 + idx + progress * 4.4) * 12
                        points.append((int(x), int(y)))
                    pygame.draw.lines(tendrils, (28, 46, 60, 74), False, points, 3)
                self.screen.blit(tendrils, (0, 0))
                for idx in range(6):
                    arc_rect = pygame.Rect(0, 0, int(safe_radius * 2) + idx * 16, int(safe_radius * 2) + idx * 16)
                    arc_rect.center = (target_x, target_y)
                    start = self._line_birth_time * (0.7 + idx * 0.08) + idx * 0.9
                    pygame.draw.arc(self.screen, (38, 64, 82), arc_rect, start, start + math.pi * 0.6, 1)

                meter_width = 320
                meter_rect = pygame.Rect(0, 0, meter_width, 12)
                meter_rect.center = (center_x, spark_y + 118)
                pygame.draw.rect(self.screen, (18, 22, 34), meter_rect, border_radius=6)
                fill_rect = meter_rect.copy()
                fill_rect.width = int(meter_width * self._line_birth_endure_progress)
                pygame.draw.rect(self.screen, (164, 238, 255), fill_rect, border_radius=6)
            elif phase == "stabilize":
                safe_limit = self._line_birth_stabilize_safe_limit()
                guide_rect = pygame.Rect(0, 0, 168, 246)
                guide_rect.center = (center_x, spark_y)
                pygame.draw.rect(self.screen, (18, 26, 40), guide_rect, border_radius=24)
                pygame.draw.rect(self.screen, (60, 88, 112), guide_rect, width=1, border_radius=24)
                safe_width = int(42 + safe_limit * 130.0)
                safe_rect = pygame.Rect(0, 0, safe_width, 214)
                safe_rect.center = (center_x, spark_y)
                pygame.draw.rect(self.screen, (20, 58, 78), safe_rect, border_radius=18)
                pygame.draw.rect(self.screen, (118, 198, 220), safe_rect, width=1, border_radius=18)

                trail_count = 4
                for idx in range(trail_count):
                    lag = (idx + 1) / trail_count
                    ghost_x = int(spark_x - self._line_birth_balance_velocity * 120.0 * lag)
                    ghost_alpha = max(18, int(54 * (1.0 - lag)))
                    self._draw_glow_circle_scene((ghost_x, spark_y), int(10 * (1.0 - lag * 0.4)), (112, 218, 255), ghost_alpha)

                meter_width = 320
                meter_rect = pygame.Rect(0, 0, meter_width, 12)
                meter_rect.center = (center_x, spark_y + 116)
                pygame.draw.rect(self.screen, (18, 22, 34), meter_rect, border_radius=6)
                fill_rect = meter_rect.copy()
                fill_rect.width = int(meter_width * self._line_birth_stability)
                pygame.draw.rect(self.screen, (164, 238, 255), fill_rect, border_radius=6)
                current_layer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                for side in (-1, 1):
                    points = []
                    for idx in range(7):
                        progress = idx / 6.0
                        wave = math.sin(self._line_birth_time * 2.2 + progress * 3.6 + side * 0.8)
                        x = center_x + side * (118 + progress * 64 + wave * 16)
                        y = spark_y - 122 + progress * 244
                        points.append((int(x), int(y)))
                    pygame.draw.lines(current_layer, (86, 166, 190, 46), False, points, 2)
                self.screen.blit(current_layer, (0, 0))
            elif phase == "weave":
                beat_strength = self._line_birth_weave_beat_strength()
                braid_layer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                for side in (-1, 1):
                    points = []
                    for idx in range(10):
                        progress = idx / 9.0
                        sway = math.sin(self._line_birth_time * 6.4 + progress * 4.8 + side * 0.6) * 18.0
                        x = center_x + side * (132 - progress * 96) + sway * side * 0.28
                        y = center_y - 124 + progress * 248
                        points.append((int(x), int(y)))
                    pygame.draw.lines(
                        braid_layer,
                        (136, 228, 252, 84 if (side == self._line_birth_weave_expected) else 48),
                        False,
                        points,
                        3,
                    )
                self.screen.blit(braid_layer, (0, 0))
                beam_layer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                beam_alpha = int(24 + beat_strength * 84)
                pygame.draw.line(beam_layer, (120, 220, 248, beam_alpha), (center_x - 128, center_y), (center_x + 128, center_y), 2)
                self.screen.blit(beam_layer, (0, 0))

                meter_width = 320
                meter_rect = pygame.Rect(0, 0, meter_width, 12)
                meter_rect.center = (center_x, spark_y + 118)
                pygame.draw.rect(self.screen, (18, 22, 34), meter_rect, border_radius=6)
                fill_rect = meter_rect.copy()
                fill_rect.width = int(meter_width * self._line_birth_weave_progress)
                pygame.draw.rect(self.screen, (164, 238, 255), fill_rect, border_radius=6)
                for side, color in ((-1, (150, 170, 245)), (1, (232, 196, 132))):
                    node_x = center_x + side * 128
                    node_y = center_y
                    radius = 12 + (8 if side == self._line_birth_weave_expected else 0) + int(beat_strength * (5 if side == self._line_birth_weave_expected else 2))
                    pygame.draw.circle(self.screen, color, (node_x, node_y), radius, 2)
                    pygame.draw.circle(self.screen, color, (node_x, node_y), 3)
                    if side == self._line_birth_weave_expected:
                        self._draw_glow_circle_scene((node_x, node_y), int(18 + beat_strength * 14), color, int(28 + beat_strength * 42))
            else:
                seal_radius = 124
                gate_angle = math.pi * 1.5
                gate_span = self._line_birth_seal_gate_span()
                ring_rect = pygame.Rect(0, 0, seal_radius * 2, seal_radius * 2)
                ring_rect.center = (spark_x, spark_y)
                pygame.draw.arc(
                    self.screen,
                    (56, 78, 96),
                    ring_rect,
                    gate_angle + gate_span,
                    gate_angle + math.tau - gate_span,
                    3,
                )
                gate_inner = (
                    int(spark_x + math.cos(gate_angle) * (seal_radius - 8)),
                    int(spark_y + math.sin(gate_angle) * (seal_radius - 8)),
                )
                gate_outer = (
                    int(spark_x + math.cos(gate_angle) * (seal_radius + 16)),
                    int(spark_y + math.sin(gate_angle) * (seal_radius + 16)),
                )
                pygame.draw.line(self.screen, (212, 248, 255), gate_inner, gate_outer, 4)

                for idx in range(3):
                    lag = idx * 0.18
                    angle = self._line_birth_seal_rotation - lag
                    orb_x = spark_x + math.cos(angle) * seal_radius
                    orb_y = spark_y + math.sin(angle) * seal_radius
                    alpha = max(28, 88 - idx * 22)
                    radius = max(4, 8 - idx * 2)
                    orb = pygame.Surface((radius * 2 + 6, radius * 2 + 6), pygame.SRCALPHA)
                    pygame.draw.circle(orb, (150, 238, 255, alpha), (radius + 3, radius + 3), radius)
                    self.screen.blit(orb, (int(orb_x) - radius - 3, int(orb_y) - radius - 3))
                for idx in range(2):
                    angle = -self._line_birth_seal_rotation * (0.8 + idx * 0.18) + idx * 1.2
                    inner_radius = seal_radius - 38 - idx * 16
                    orb_x = spark_x + math.cos(angle) * inner_radius
                    orb_y = spark_y + math.sin(angle) * inner_radius
                    pygame.draw.circle(self.screen, (110, 212, 244), (int(orb_x), int(orb_y)), 5 - idx)
                inner_ring = pygame.Rect(0, 0, (seal_radius - 34) * 2, (seal_radius - 34) * 2)
                inner_ring.center = (spark_x, spark_y)
                pygame.draw.arc(self.screen, (70, 108, 132), inner_ring, self._line_birth_time * 1.2, self._line_birth_time * 1.2 + math.pi * 1.1, 2)

                for idx in range(3):
                    marker_x = center_x - 56 + idx * 56
                    marker_y = spark_y - 162
                    active = idx < self._line_birth_seal_hits
                    color = (170, 236, 255) if active else (42, 52, 68)
                    pygame.draw.circle(self.screen, color, (marker_x, marker_y), 8)
        meter_width = 320
        meter_rect = pygame.Rect(0, 0, meter_width, 10)
        meter_rect.center = (center_x, self.height - 94)
        pygame.draw.rect(self.screen, (18, 22, 34), meter_rect, border_radius=5)
        fill_rect = meter_rect.copy()
        fill_rect.width = int(meter_width * self._line_birth_charge)
        pygame.draw.rect(self.screen, (118, 210, 244), fill_rect, border_radius=5)

        if self._line_birth_fail_flash > 0.0:
            fail = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            fail.fill((120, 10, 10, int(56 * self._line_birth_fail_flash)))
            self.screen.blit(fail, (0, 0))

        if self._line_birth_flash > 0.0:
            flash = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            flash.fill((215, 232, 255, int(72 * self._line_birth_flash)))
            self.screen.blit(flash, (0, 0))

        if show_hint:
            if self._line_birth_state == "cohere":
                if phase == "pulse":
                    self._draw_void_hint("SPACE AT CONVERGENCE", self.height - 56)
                elif phase == "gather":
                    self._draw_void_hint("WASD GATHER SHARDS", self.height - 56)
                elif phase == "endure":
                    self._draw_void_hint("WASD STAY IN THE HALO", self.height - 56)
                elif phase == "stabilize":
                    self._draw_void_hint("A / D HOLD CENTER", self.height - 56)
                elif phase == "weave":
                    self._draw_void_hint("A / D ALTERNATE", self.height - 56)
                else:
                    self._draw_void_hint("SPACE THROUGH THE SLIT", self.height - 56)

    def _draw_line_birth_ritual(self) -> None:
        """Route birth rendering between lore interstitials and active challenges."""
        if self._line_birth_interstitial_active:
            self._draw_line_birth_interstitial()
            return
        self._draw_line_birth_challenge_scene(show_hint=True)

    def _can_attempt_impossible_line_motion(self) -> bool:
        """Return whether the player can currently strain against the Line."""
        if self.session.active_dimension.id != "1d":
            return False
        if self.paused or self.dialogue.is_active:
            return False
        if self._is_line_birth_active() or self._line_guardian_active:
            return False
        if self.combat and (self.combat.in_combat or self.combat.transitioning):
            return False
        if self.dimensional_combat and (self.dimensional_combat.in_combat or self.dimensional_combat.transitioning):
            return False
        return True

    def _attempt_impossible_line_motion(self, axis: float) -> None:
        """Let the player briefly strain toward a forbidden axis in 1D."""
        if not self._can_attempt_impossible_line_motion():
            return

        axis = -1.0 if axis < 0 else 1.0
        self._line_strain_axis = axis
        self._line_strain_bend = min(1.0, self._line_strain_bend * 0.45 + 1.0)
        self._line_strain_flash = 1.0
        self._line_strain_shake = max(self._line_strain_shake, 1.0)

        if not self.audio.play("line_strain", volume_override=0.95):
            self.audio.play("damage", volume_override=0.55)

        affected = self._confuse_nearby_line_entities(axis)
        self._line_violation_meter = min(7.0, self._line_violation_meter + 1.0 + affected * 0.28)
        self.world.emit("line_strain_attempt", axis="up" if axis < 0 else "down", affected=affected)

        if self._line_violation_meter >= 4.6:
            self._trigger_line_guardian_intervention()

    def _confuse_nearby_line_entities(self, axis: float) -> int:
        """Make nearby 1D entities visibly uncertain after witnessing impossible motion."""
        player = self.world.find_player()
        if not player:
            return 0

        player_transform = player.get(Transform)
        if not player_transform:
            return 0

        player_x = float(player_transform.position[0])
        affected = 0
        for entity in self.world.in_dimension("1d"):
            if not entity.active or entity.id == player.id:
                continue
            if entity.has_tag("marker") or entity.has_tag("the_first_point") or entity.get(Portal):
                continue

            brain = entity.get(AIBrain)
            transform = entity.get(Transform)
            if not brain or not transform:
                continue

            distance = abs(float(transform.position[0]) - player_x)
            if distance > 12.0:
                continue

            intensity = max(0.2, 1.0 - distance / 12.0)
            existing_timer = float(brain.get_state("confused_timer", 0.0))
            existing_level = float(brain.get_state("confusion_level", 0.0))
            brain.set_state("confused_timer", max(existing_timer, 1.0 + intensity * 1.6))
            brain.set_state("confusion_level", min(3.5, existing_level + 0.45 + intensity * 0.9))
            brain.set_state("confusion_axis", axis)
            if float(brain.get_state("confusion_phase", 0.0)) == 0.0:
                brain.set_state("confusion_phase", float(np.random.uniform(0.0, math.tau)))
            affected += 1

        return affected

    def _update_line_strain(self, dt: float) -> None:
        """Decay the forbidden-axis strain and guardian punishment animation."""
        self._line_strain_bend = max(0.0, self._line_strain_bend - dt * 2.6)
        self._line_strain_flash = max(0.0, self._line_strain_flash - dt * 3.5)
        self._line_strain_shake = max(0.0, self._line_strain_shake - dt * 4.4)
        self._line_violation_meter = max(0.0, self._line_violation_meter - dt * 0.14)

        if self._line_guardian_active:
            self._line_guardian_time += dt
            self._line_guardian_rotation += dt * 0.85
            self._line_guardian_flash = max(0.0, self._line_guardian_flash - dt * 0.8)

    def _trigger_line_guardian_strike(self, final: bool = False) -> None:
        """Advance the guardian execution animation by one strike."""
        self._line_guardian_strikes = min(4, self._line_guardian_strikes + 1)
        self._line_guardian_attack_timer = 1.0
        self._line_guardian_flash = 1.0 if final else max(self._line_guardian_flash, 0.7)
        self._line_strain_shake = max(self._line_strain_shake, 1.1 if final else 0.85)
        self.audio.play("guardian_judgment", volume_override=0.22 if final else 0.14)

    def _update_line_guardian_scene(self, dt: float) -> None:
        """Drive guardian strikes and the collapse transition."""
        if not self._line_guardian_active:
            return

        self._line_guardian_attack_timer = max(0.0, self._line_guardian_attack_timer - dt * 2.7)
        self._load_guardian_nebula_frames()
        if self._guardian_nebula_frames:
            self._guardian_nebula_frame_timer += dt
            frame_duration = self._guardian_nebula_durations[self._guardian_nebula_frame_index]
            while self._guardian_nebula_frame_timer >= frame_duration:
                self._guardian_nebula_frame_timer -= frame_duration
                self._guardian_nebula_frame_index = (self._guardian_nebula_frame_index + 1) % len(self._guardian_nebula_frames)
                frame_duration = self._guardian_nebula_durations[self._guardian_nebula_frame_index]
        current_sequence = getattr(self.dialogue, "_current_sequence", None)
        current_index = getattr(self.dialogue, "_current_line_index", 0)

        if current_sequence and current_sequence.id == "line_guardian_intervention":
            if self._line_guardian_last_dialogue_index < 0:
                self._line_guardian_last_dialogue_index = current_index
            elif current_index != self._line_guardian_last_dialogue_index:
                for idx in range(self._line_guardian_last_dialogue_index + 1, current_index + 1):
                    if idx >= 2 and self._line_guardian_strikes < 3:
                        self._trigger_line_guardian_strike()
                self._line_guardian_last_dialogue_index = current_index

        if self._line_guardian_reset_pending and not self.dialogue.is_active:
            if self._line_guardian_transition_progress <= 0.0 and self._line_guardian_strikes < 4:
                self._trigger_line_guardian_strike(final=True)
            self._line_guardian_transition_progress = min(1.0, self._line_guardian_transition_progress + dt * 0.72)

    def _trigger_line_guardian_intervention(self) -> None:
        """Summon a higher-dimensional guardian to reset reckless line-breaking."""
        if self._line_guardian_active:
            return

        from hypersim.game.ui.textbox import DialogueLine, DialogueSequence, TextBoxStyle

        self._line_guardian_active = True
        self._line_guardian_time = 0.0
        self._line_guardian_rotation = 0.0
        self._line_guardian_flash = 1.0
        self._line_guardian_strikes = 0
        self._line_guardian_attack_timer = 0.0
        self._line_guardian_last_dialogue_index = 0
        self._line_guardian_transition_progress = 0.0
        self._guardian_nebula_frame_index = 0
        self._guardian_nebula_frame_timer = 0.0
        self._line_strain_bend = max(self._line_strain_bend, 0.9)
        self._line_strain_shake = max(self._line_strain_shake, 1.2)
        self._line_strain_flash = 1.0
        self._set_player_control_enabled(False)
        self.audio.play("guardian_judgment", volume_override=1.0)
        self._start_line_guardian_music()

        seq_id = "line_guardian_intervention"
        lines = [
            DialogueLine(
                text="The Line screams. A shape with too many edges forces itself through the wound.",
                style=TextBoxStyle.NARRATOR,
                duration=1.2,
            ),
            DialogueLine(
                speaker="The Tesseract Guardian",
                text="Enough.",
                style=TextBoxStyle.DIMENSION,
                voice_id="tesseract_guardian",
            ),
            DialogueLine(
                speaker="The Tesseract Guardian",
                text="Curiosity is not your crime. Contempt is.",
                style=TextBoxStyle.DIMENSION,
                voice_id="tesseract_guardian",
            ),
            DialogueLine(
                speaker="The Tesseract Guardian",
                text="You were given one honest axis and answered it by trying to tear a second through frightened minds.",
                style=TextBoxStyle.DIMENSION,
                voice_id="tesseract_guardian",
            ),
            DialogueLine(
                speaker="The Tesseract Guardian",
                text="So I will tear you apart gently, dimension by dimension, until even your spark remembers gratitude.",
                style=TextBoxStyle.DIMENSION,
                voice_id="tesseract_guardian",
            ),
        ]
        self.dialogue.register_event("line_guardian_reset", self._queue_line_guardian_reset)
        self.dialogue.register_sequence(
            DialogueSequence(
                id=seq_id,
                lines=lines,
                pause_game=True,
                can_skip=False,
                on_end="line_guardian_reset",
            )
        )
        self.dialogue.start_sequence(seq_id)

    def _queue_line_guardian_reset(self) -> None:
        """Defer the actual reset until after the punishment dialogue fully closes."""
        self._line_guardian_reset_pending = True
        self._line_guardian_transition_progress = 0.0

    def _complete_line_guardian_intervention(self) -> None:
        """Strip the player back to pre-existence and restart the birth rite."""
        self._line_guardian_reset_pending = False
        self._line_guardian_active = False
        self._line_guardian_time = 0.0
        self._line_guardian_rotation = 0.0
        self._line_guardian_flash = 1.0
        self._line_guardian_strikes = 0
        self._line_guardian_attack_timer = 0.0
        self._line_guardian_last_dialogue_index = -1
        self._line_guardian_transition_progress = 0.0
        self._line_strain_axis = 0.0
        self._line_strain_bend = 0.0
        self._line_strain_flash = 1.0
        self._line_strain_shake = 0.8
        self._line_violation_meter = 0.0
        self._stop_line_guardian_music()

        self.session.progression.lineage_ritual_state = "cohere"
        self.session.progression.lineage_direction = ""
        self._chapter_1_cinematic_played = False

        if self.current_world_id != "tutorial_1d":
            self.current_world_id = "tutorial_1d"
            self.session.progression.advance_to_world("tutorial_1d")
            self._reload_dimension()
            return

        player = self.world.find_player()
        if player:
            transform = player.get(Transform)
            if transform:
                transform.position[0] = 0.0
            velocity = player.get(Velocity)
            if velocity is not None:
                velocity.linear[:] = 0.0

        for entity in list(self.world.entities.values()):
            if entity.id == "the_first_point":
                self.world.despawn(entity.id)
                continue
            brain = entity.get(AIBrain)
            if brain:
                brain.set_state("confused_timer", 0.0)
                brain.set_state("confusion_level", 0.0)

        self._start_line_birth_ritual()

    def _guardian_tesseract_geometry(self) -> tuple[list[np.ndarray], list[tuple[int, int]]]:
        """Return cached 4D hypercube geometry for the punitive guardian overlay."""
        if hasattr(self, "_line_guardian_vertices") and hasattr(self, "_line_guardian_edges"):
            return self._line_guardian_vertices, self._line_guardian_edges

        vertices = []
        for w in (-1.0, 1.0):
            for z in (-1.0, 1.0):
                for y in (-1.0, 1.0):
                    for x in (-1.0, 1.0):
                        vertices.append(np.array([x, y, z, w], dtype=float))
        edges = []
        for i in range(16):
            for j in range(i + 1, 16):
                if bin(i ^ j).count("1") == 1:
                    edges.append((i, j))

        self._line_guardian_vertices = vertices
        self._line_guardian_edges = edges
        return vertices, edges

    def _rotate_guardian_vertex(self, vertex: np.ndarray) -> np.ndarray:
        """Rotate guardian geometry through a few 4D planes."""
        x, y, z, w = vertex
        a = self._line_guardian_rotation

        cos_xw, sin_xw = math.cos(a), math.sin(a)
        x, w = x * cos_xw - w * sin_xw, x * sin_xw + w * cos_xw

        cos_yw, sin_yw = math.cos(a * 0.77), math.sin(a * 0.77)
        y, w = y * cos_yw - w * sin_yw, y * sin_yw + w * cos_yw

        cos_zw, sin_zw = math.cos(a * 0.53), math.sin(a * 0.53)
        z, w = z * cos_zw - w * sin_zw, z * sin_zw + w * cos_zw

        cos_xy, sin_xy = math.cos(a * 0.31), math.sin(a * 0.31)
        x, y = x * cos_xy - y * sin_xy, x * sin_xy + y * cos_xy
        return np.array([x, y, z, w], dtype=float)

    def _project_guardian_vertex(self, vertex: np.ndarray, center: tuple[int, int], scale: float) -> tuple[int, int, float]:
        """Project a 4D guardian vertex to the 2D screen."""
        x, y, z, w = vertex
        factor_4d = 2.8 / max(0.25, 2.8 - w)
        x3 = x * factor_4d
        y3 = y * factor_4d
        z3 = z * factor_4d
        factor_3d = 3.6 / max(0.35, 3.6 - z3)
        return (
            int(center[0] + x3 * factor_3d * scale),
            int(center[1] - y3 * factor_3d * scale),
            w + z3,
        )

    def _draw_line_guardian_judgment(self) -> None:
        """Draw the higher-dimensional guardian that punishes repeated overreach."""
        if not self._line_guardian_active:
            return

        self.screen.fill((0, 0, 0))

        center = (self.width // 2, self.height // 2 - 150)
        victim = (self.width // 2, self.height - 128)
        scale = 96.0 + 18.0 * math.sin(self._line_guardian_time * 1.7)
        vertices, edges = self._guardian_tesseract_geometry()
        projected = [self._project_guardian_vertex(self._rotate_guardian_vertex(v), center, scale) for v in vertices]

        self._draw_guardian_nebula(center, projected)

        guardian_center_vec = np.array(center, dtype=float)
        umbra = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        glow = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        edge_energy = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for i, j in edges:
            p1, p2 = projected[i], projected[j]
            p1_vec = np.array([p1[0], p1[1]], dtype=float)
            p2_vec = np.array([p2[0], p2[1]], dtype=float)
            mid = (p1_vec + p2_vec) * 0.5
            outward = mid - guardian_center_vec
            outward_norm = max(1.0, np.linalg.norm(outward))
            outward /= outward_norm
            tangent = p2_vec - p1_vec
            tangent_norm = max(1.0, np.linalg.norm(tangent))
            tangent /= tangent_norm
            depth = max(0.25, min(1.0, (p1[2] + p2[2] + 2.5) / 5.0))
            offset = outward * (2.0 + depth * 3.4)

            shadow_start = tuple((p1_vec + offset * 0.65).astype(int))
            shadow_end = tuple((p2_vec + offset * 0.65).astype(int))
            pygame.draw.line(umbra, (0, 0, 0, int(156 * depth)), shadow_start, shadow_end, max(8, int(14 * depth)))
            pygame.draw.line(umbra, (4, 10, 14, int(110 * depth)), (p1[0], p1[1]), (p2[0], p2[1]), max(6, int(10 * depth)))

            pygame.draw.line(glow, (34, 214, 255, int(42 * depth)), (p1[0], p1[1]), (p2[0], p2[1]), max(10, int(16 * depth)))

            for marker_idx, marker_t in enumerate((0.22, 0.5, 0.78)):
                emit = p1_vec * (1.0 - marker_t) + p2_vec * marker_t
                wave = math.sin(self._line_guardian_time * 3.1 + i * 0.41 + j * 0.27 + marker_idx * 1.9)
                ray_dir = outward * (0.88 + 0.08 * wave) + tangent * (0.22 * wave)
                ray_dir /= max(1.0, np.linalg.norm(ray_dir))
                ray_start = emit + outward * 3.0
                ray_end = ray_start + ray_dir * (12.0 + depth * 20.0 + abs(wave) * 10.0)
                alpha = int(26 + depth * 40.0 - marker_idx * 5)
                pygame.draw.line(
                    edge_energy,
                    (72, 238, 255, alpha),
                    tuple(ray_start.astype(int)),
                    tuple(ray_end.astype(int)),
                    1,
                )
                ember_radius = 1 + marker_idx // 2
                pygame.draw.circle(edge_energy, (126, 248, 255, alpha + 12), tuple(ray_start.astype(int)), ember_radius)
        self.screen.blit(umbra, (0, 0))
        self.screen.blit(glow, (0, 0))
        self.screen.blit(edge_energy, (0, 0))

        for i, j in edges:
            p1, p2 = projected[i], projected[j]
            depth = max(0.25, min(1.0, (p1[2] + p2[2] + 2.5) / 5.0))
            edge_color = (
                int(8 + 12 * depth),
                int(16 + 20 * depth),
                int(24 + 26 * depth),
            )
            pygame.draw.line(self.screen, edge_color, (p1[0], p1[1]), (p2[0], p2[1]), max(2, int(5 * depth)))
            highlight_color = (
                int(68 * depth),
                int(228 * depth),
                int(255 * depth),
            )
            pygame.draw.line(self.screen, highlight_color, (p1[0], p1[1]), (p2[0], p2[1]), max(1, int(2 * depth)))

        for x, y, depth in projected:
            factor = max(0.35, min(1.0, (depth + 2.5) / 5.0))
            self._draw_glow_circle_scene((x, y), max(5, int(8 * factor)), (8, 16, 20), int(36 * factor))
            pygame.draw.circle(self.screen, (6, 14, 18), (x, y), max(3, int(6 * factor)))
            pygame.draw.circle(self.screen, (132, int(245 * factor), 255), (x, y), max(1, int(2 * factor)))

        attack_phase = 1.0 - self._line_guardian_attack_timer
        attack_phase = max(0.0, min(1.0, attack_phase))
        thrust = 0.0
        if self._line_guardian_attack_timer > 0.0:
            thrust = math.sin(attack_phase * math.pi) ** 0.85
        if self._line_guardian_transition_progress > 0.0:
            thrust = max(thrust, 0.84 + self._line_guardian_transition_progress * 0.16)

        direction = np.array([victim[0] - center[0], victim[1] - center[1]], dtype=float)
        direction /= max(1.0, np.linalg.norm(direction))
        perpendicular = np.array([-direction[1], direction[0]], dtype=float)
        weapon_length = 208.0
        idle_origin = (
            np.array(center, dtype=float)
            + perpendicular * (166.0 + 18.0 * math.sin(self._line_guardian_time * 1.3))
            - direction * (54.0 - 12.0 * math.cos(self._line_guardian_time * 1.1))
        )
        strike_origin = np.array(victim, dtype=float) - direction * (weapon_length - 24.0)
        base = idle_origin * (1.0 - thrust) + strike_origin * thrust
        tip = base + direction * weapon_length
        tail = base - direction * 34.0
        shaft_half = 8.6 + (1.0 - thrust) * 2.6
        weapon_core = base + direction * 98.0
        shaft_points = [
            tuple((base + perpendicular * shaft_half * 1.05).astype(int)),
            tuple((weapon_core + perpendicular * shaft_half * 0.94).astype(int)),
            tuple((tip + perpendicular * shaft_half * 0.26).astype(int)),
            tuple((tip - perpendicular * shaft_half * 0.26).astype(int)),
            tuple((weapon_core - perpendicular * shaft_half * 0.94).astype(int)),
            tuple((base - perpendicular * shaft_half * 1.05).astype(int)),
        ]
        inner_shaft_points = [
            tuple((base + perpendicular * shaft_half * 0.34).astype(int)),
            tuple((weapon_core + perpendicular * shaft_half * 0.28).astype(int)),
            tuple((tip + perpendicular * shaft_half * 0.08).astype(int)),
            tuple((tip - perpendicular * shaft_half * 0.08).astype(int)),
            tuple((weapon_core - perpendicular * shaft_half * 0.28).astype(int)),
            tuple((base - perpendicular * shaft_half * 0.34).astype(int)),
        ]
        head_base = tip - direction * 38.0
        head_wing = tip - direction * 64.0
        spear_head = [
            tuple(tip.astype(int)),
            tuple((head_base + perpendicular * 11.0).astype(int)),
            tuple((head_wing + perpendicular * 28.0).astype(int)),
            tuple((head_wing - perpendicular * 28.0).astype(int)),
            tuple((head_base - perpendicular * 11.0).astype(int)),
        ]
        upper_prong = [
            tuple((head_base + perpendicular * 8.0).astype(int)),
            tuple((head_base + perpendicular * 30.0 - direction * 24.0).astype(int)),
            tuple((tip + perpendicular * 16.0 - direction * 10.0).astype(int)),
        ]
        lower_prong = [
            tuple((head_base - perpendicular * 8.0).astype(int)),
            tuple((head_base - perpendicular * 30.0 - direction * 24.0).astype(int)),
            tuple((tip - perpendicular * 16.0 - direction * 10.0).astype(int)),
        ]
        tail_head = [
            tuple(tail.astype(int)),
            tuple((tail + perpendicular * 18.0 + direction * 8.0).astype(int)),
            tuple((tail - perpendicular * 18.0 + direction * 8.0).astype(int)),
        ]
        fin_center = base + direction * 70.0
        fin_a = [
            tuple((fin_center + perpendicular * 26.0).astype(int)),
            tuple((fin_center - direction * 26.0 + perpendicular * 6.0).astype(int)),
            tuple((fin_center - direction * 10.0 - perpendicular * 6.0).astype(int)),
            tuple((fin_center + direction * 6.0 + perpendicular * 10.0).astype(int)),
        ]
        fin_b = [
            tuple((fin_center - perpendicular * 26.0).astype(int)),
            tuple((fin_center - direction * 26.0 - perpendicular * 6.0).astype(int)),
            tuple((fin_center - direction * 10.0 + perpendicular * 6.0).astype(int)),
            tuple((fin_center + direction * 6.0 - perpendicular * 10.0).astype(int)),
        ]
        rear_barb_center = base + direction * 22.0
        rear_barb_a = [
            tuple((rear_barb_center + perpendicular * 20.0).astype(int)),
            tuple((rear_barb_center + direction * 24.0 + perpendicular * 5.0).astype(int)),
            tuple((rear_barb_center + direction * 6.0 - perpendicular * 4.0).astype(int)),
        ]
        rear_barb_b = [
            tuple((rear_barb_center - perpendicular * 20.0).astype(int)),
            tuple((rear_barb_center + direction * 24.0 - perpendicular * 5.0).astype(int)),
            tuple((rear_barb_center + direction * 6.0 + perpendicular * 4.0).astype(int)),
        ]
        core_diamond = [
            tuple((weapon_core + perpendicular * 12.0).astype(int)),
            tuple((weapon_core + direction * 16.0).astype(int)),
            tuple((weapon_core - perpendicular * 12.0).astype(int)),
            tuple((weapon_core - direction * 16.0).astype(int)),
        ]
        core_cage = [
            tuple((weapon_core + perpendicular * 22.0).astype(int)),
            tuple((weapon_core + direction * 26.0).astype(int)),
            tuple((weapon_core - perpendicular * 22.0).astype(int)),
            tuple((weapon_core - direction * 26.0).astype(int)),
        ]

        spear_glow = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for trail_idx in range(5):
            lag = (trail_idx + 1) / 5.0
            ghost_progress = max(0.0, thrust - lag * 0.16)
            ghost_base = idle_origin * (1.0 - ghost_progress) + strike_origin * ghost_progress
            ghost_tip = ghost_base + direction * weapon_length
            ghost_core = ghost_base + direction * 98.0
            ghost_half = shaft_half * (1.0 - lag * 0.18)
            ghost_points = [
                tuple((ghost_base + perpendicular * ghost_half * 1.05).astype(int)),
                tuple((ghost_core + perpendicular * ghost_half * 0.94).astype(int)),
                tuple((ghost_tip + perpendicular * ghost_half * 0.26).astype(int)),
                tuple((ghost_tip - perpendicular * ghost_half * 0.26).astype(int)),
                tuple((ghost_core - perpendicular * ghost_half * 0.94).astype(int)),
                tuple((ghost_base - perpendicular * ghost_half * 1.05).astype(int)),
            ]
            pygame.draw.polygon(spear_glow, (86, 246, 255, max(0, 54 - trail_idx * 9)), ghost_points)
        pygame.draw.polygon(spear_glow, (62, 196, 218, 54), shaft_points)
        pygame.draw.polygon(spear_glow, (128, 255, 255, 96), spear_head)
        pygame.draw.polygon(spear_glow, (116, 252, 255, 74), upper_prong)
        pygame.draw.polygon(spear_glow, (116, 252, 255, 74), lower_prong)
        pygame.draw.polygon(spear_glow, (96, 240, 255, 56), fin_a)
        pygame.draw.polygon(spear_glow, (96, 240, 255, 56), fin_b)
        pygame.draw.polygon(spear_glow, (82, 228, 246, 44), rear_barb_a)
        pygame.draw.polygon(spear_glow, (82, 228, 246, 44), rear_barb_b)
        pygame.draw.polygon(spear_glow, (132, 250, 255, 44), core_cage, width=2)
        pygame.draw.circle(spear_glow, (96, 242, 255, 40), tuple(weapon_core.astype(int)), 26, 1)
        self.screen.blit(spear_glow, (0, 0))
        pygame.draw.polygon(self.screen, (40, 122, 142), shaft_points)
        pygame.draw.polygon(self.screen, (118, 230, 244), inner_shaft_points)
        pygame.draw.polygon(self.screen, (234, 255, 255), spear_head)
        pygame.draw.polygon(self.screen, (190, 252, 255), upper_prong)
        pygame.draw.polygon(self.screen, (190, 252, 255), lower_prong)
        pygame.draw.polygon(self.screen, (54, 188, 208), tail_head)
        pygame.draw.polygon(self.screen, (90, 226, 242), fin_a)
        pygame.draw.polygon(self.screen, (90, 226, 242), fin_b)
        pygame.draw.polygon(self.screen, (74, 214, 236), rear_barb_a)
        pygame.draw.polygon(self.screen, (74, 214, 236), rear_barb_b)
        pygame.draw.polygon(self.screen, (14, 24, 30), core_diamond)
        pygame.draw.polygon(self.screen, (154, 248, 255), core_cage, width=2)
        pygame.draw.circle(self.screen, (224, 255, 255), tuple((weapon_core + direction * 2.0).astype(int)), 4)

        if thrust < 0.2:
            hover_glow = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.circle(
                hover_glow,
                (72, 236, 255, 28),
                tuple(idle_origin.astype(int)),
                28,
                1,
            )
            pygame.draw.circle(
                hover_glow,
                (126, 248, 255, 44),
                tuple(idle_origin.astype(int)),
                8,
            )
            pygame.draw.circle(
                hover_glow,
                (96, 242, 255, 32),
                tuple(weapon_core.astype(int)),
                30,
                1,
            )
            pygame.draw.polygon(hover_glow, (132, 250, 255, 42), core_cage, width=1)
            self.screen.blit(hover_glow, (0, 0))

        point_glow = max(0.0, 1.0 - self._line_guardian_strikes * 0.28)
        point_glow *= max(0.08, 1.0 - self._line_guardian_transition_progress * 0.9)
        spark_scale = max(0.12, 1.0 - self._line_guardian_transition_progress * 0.82)

        if point_glow > 0.02:
            self._draw_glow_circle_scene(victim, int(48 * point_glow * spark_scale), (72, 232, 255), 44)
            self._draw_glow_circle_scene(victim, int(28 * max(0.2, point_glow) * spark_scale), (214, 252, 255), 86)
        pygame.draw.circle(self.screen, (188, 246, 255), victim, max(2, int(8 * spark_scale)))
        if point_glow > 0.1:
            pygame.draw.circle(self.screen, (255, 255, 255), victim, max(2, int(4 * spark_scale)))

        for idx in range(8):
            orbit = self._line_guardian_time * (1.6 + idx * 0.12) + idx * 0.8
            distance = 18 + idx * 7 + self._line_guardian_transition_progress * 26
            shard_x = victim[0] + math.cos(orbit) * distance
            shard_y = victim[1] + math.sin(orbit) * (8 + idx * 1.8) - self._line_guardian_transition_progress * 24
            alpha = max(24, int(90 * (1.0 - idx / 10.0) * max(0.18, 1.0 - self._line_guardian_transition_progress)))
            shard_radius = max(1, 3 - idx // 3)
            shard = pygame.Surface((shard_radius * 2 + 4, shard_radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(shard, (150, 238, 255, alpha), (shard_radius + 2, shard_radius + 2), shard_radius)
            self.screen.blit(shard, (int(shard_x) - shard_radius - 2, int(shard_y) - shard_radius - 2))

        if thrust > 0.52:
            impact = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            impact_alpha = int(120 * thrust)
            for idx in range(6):
                angle = idx * (math.tau / 6.0) + self._line_guardian_time * 0.8
                ray_start = (
                    int(victim[0] + math.cos(angle) * 8),
                    int(victim[1] + math.sin(angle) * 8),
                )
                ray_end = (
                    int(victim[0] + math.cos(angle) * (28 + thrust * 22)),
                    int(victim[1] + math.sin(angle) * (28 + thrust * 22)),
                )
                pygame.draw.line(impact, (188, 250, 255, impact_alpha), ray_start, ray_end, 2)
            pygame.draw.circle(impact, (214, 255, 255, impact_alpha), victim, int(14 + thrust * 8), 1)
            self.screen.blit(impact, (0, 0))

        if self._line_guardian_flash > 0.0:
            flash = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            flash.fill((196, 252, 255, int(92 * self._line_guardian_flash)))
            self.screen.blit(flash, (0, 0))
    
    def _spawn_first_point_npc(self) -> None:
        """Spawn the First Point as an interactable NPC entity."""
        # Check if already spawned
        if self.world.get("the_first_point"):
            return
        
        first_point = Entity(id="the_first_point")
        first_point.add(Transform(position=np.array([-3.0, 0.0, 0.0, 0.0])))
        first_point.add(Velocity())
        first_point.add(Renderable(color=(180, 100, 255), glow=2.0))  # Purple with strong glow
        first_point.add(Collider(shape=ColliderShape.SEGMENT, size=np.array([1.0]), is_trigger=True))
        first_point.add(AIBrain(
            behavior="stationary",
            state={"npc_id": "the_first_point", "is_friendly": True}
        ))
        first_point.add(DimensionAnchor(dimension_id="1d"))
        first_point.tag("npc", "friendly", "the_first_point", "interactable")
        self.world.spawn(first_point)
    
    def _interact_with_npc(self, npc_entity: Entity) -> None:
        """Handle player interacting with an NPC."""
        from hypersim.game.story.cinematics import get_first_point_interaction_dialogue
        from hypersim.game.ui.textbox import DialogueSequence, DialogueLine, TextBoxStyle
        
        # Don't start dialogue if already in dialogue or combat
        if self.dialogue.is_active:
            return
        if self.combat and self.combat.in_combat:
            return
        if self.dimensional_combat and self.dimensional_combat.in_combat:
            return

        self._record_world_event("interact", target=self._get_interaction_target(npc_entity))
        
        # Handle The First Point specifically
        if npc_entity.has_tag("the_first_point"):
            self._start_first_point_interaction()
            return
        
        # Handle other NPCs through their AI state
        ai_brain = npc_entity.get(AIBrain)
        if ai_brain and ai_brain.state.get("npc_id"):
            npc_id = ai_brain.state["npc_id"]
            # Could load dialogue from npcs.py here
            self.overlays.notify(f"Talked to {npc_id}", duration=2.0, color=(150, 200, 255))
    
    def _start_first_point_interaction(self) -> None:
        """Start dialogue interaction with The First Point."""
        from hypersim.game.story.cinematics import get_first_point_interaction_dialogue
        from hypersim.game.ui.textbox import DialogueSequence, DialogueLine, TextBoxStyle
        
        # Create dialogue sequence dynamically
        dialogue_data = get_first_point_interaction_dialogue("greeting")
        lines = []
        
        for item in dialogue_data:
            speaker = item.get("speaker", "")
            text = item.get("text", "")
            choices = item.get("choices", [])
            
            style = TextBoxStyle.DIMENSION if speaker == "The First Point" else TextBoxStyle.NARRATOR
            
            lines.append(DialogueLine(
                speaker=speaker,
                text=text,
                style=style,
                choices=choices,
            ))
        
        if lines:
            seq = DialogueSequence(
                id="first_point_interaction",
                lines=lines,
                pause_game=True,
            )
            self.dialogue.register_sequence(seq)
            
            # Register choice callbacks
            self._register_first_point_choices()
            
            self.dialogue.start_sequence("first_point_interaction")
    
    def _register_first_point_choices(self) -> None:
        """Register callbacks for First Point dialogue choices."""
        from hypersim.game.story.cinematics import (
            FIRST_POINT_INTERACTION_DIALOGUES,
            get_first_point_interaction_dialogue,
        )
        from hypersim.game.ui.textbox import DialogueSequence, DialogueLine, TextBoxStyle
        
        def create_choice_handler(choice_key: str):
            def handler():
                # Get the follow-up dialogue
                dialogue_data = get_first_point_interaction_dialogue(choice_key)
                lines = []
                
                for item in dialogue_data:
                    speaker = item.get("speaker", "")
                    text = item.get("text", "")
                    choices = item.get("choices", [])
                    
                    style = TextBoxStyle.DIMENSION if speaker == "The First Point" else TextBoxStyle.NARRATOR
                    
                    lines.append(DialogueLine(
                        speaker=speaker,
                        text=text,
                        style=style,
                        choices=choices,
                    ))
                
                if lines:
                    seq = DialogueSequence(
                        id=f"first_point_{choice_key}",
                        lines=lines,
                        pause_game=True,
                    )
                    self.dialogue.register_sequence(seq)
                    self.dialogue.start_sequence(f"first_point_{choice_key}")
            return handler
        
        # Register handlers for all defined First Point dialogue branches.
        for key in FIRST_POINT_INTERACTION_DIALOGUES.keys():
            self.dialogue.register_event(key, create_choice_handler(key))
        
        # Special branch that starts a gameplay challenge.
        self.dialogue.register_event("start_line_trial", self._start_line_trial)
    
    def _start_line_trial(self) -> None:
        """Start the First Point's optional movement trial in 1D."""
        self.dialogue.stop()
        
        if self.session.active_dimension.id != "1d":
            self.overlays.notify("The trial can only be taken on the Line.", duration=2.2, color=(200, 170, 130))
            return
        
        if self._line_trial_state == "complete":
            self.overlays.notify("Line Trial already completed.", duration=2.2, color=(120, 210, 170))
            return
        
        if self._line_trial_state in ("to_midpoint", "return_origin"):
            self.overlays.notify("Line Trial in progress.", duration=2.2, color=(210, 190, 120))
            return
        
        self._line_trial_state = "to_midpoint"
        self.overlays.notify("Line Trial: Reach Midpoint Station, then return to the Origin.", duration=4.0, color=(210, 190, 120))

    def _update_1d_world_beats(self) -> None:
        """Add short pacing beats to make early 1D traversal feel more alive."""
        if self.session.active_dimension.id != "1d":
            return
        
        player = self.world.get("player")
        if not player:
            return
        transform = player.get(Transform)
        if not transform:
            return
        
        x = float(transform.position[0])
        if not self.session.progression.shift_tutorial_done and abs(x) >= 1.2:
            self._maybe_trigger_shift_tutorial()
        if not self.session.progression.terminus_seen and x >= 40.0:
            self._maybe_trigger_terminus_cutscene()

        beats = [
            ("line_departure", x >= 2.0, "The Line hums. Every step draws you farther from origin."),
            ("line_forward", x >= 10.0, "Forward Path: doctrine ahead, patrols nearby."),
            ("line_void", x <= -12.0, "Backward Void: echoes answer questions no sentinel asks."),
            ("line_midpoint", x >= 21.0, "Midpoint Station: temporary peace between ideologies."),
            ("line_endpoint", x >= 31.0, "Endpoint ahead. Reality feels thin here."),
        ]
        
        for beat_id, condition, message in beats:
            if condition and beat_id not in self._line_world_beats_seen:
                self._line_world_beats_seen.add(beat_id)
                self.overlays.notify(message, duration=2.6, color=(170, 185, 215))
        
        # Optional First Point trial progression.
        if self._line_trial_state == "to_midpoint" and x >= 22.0:
            self._line_trial_state = "return_origin"
            self.overlays.notify("Trial step complete. Return to the Origin Point.", duration=3.0, color=(220, 195, 120))
        elif self._line_trial_state == "return_origin" and x <= 1.5:
            self._line_trial_state = "complete"
            self.session.progression.xp += 10
            discover_lore("monodia_sparks")
            self.overlays.notify("Line Trial complete. +10 XP", duration=3.0, color=(130, 220, 170))
    
    def _spawn_default_level(self, dimension_id: str) -> None:
        """Spawn default entities for a dimension."""
        if dimension_id == "1d":
            self._spawn_1d_level()
        elif dimension_id == "2d":
            self._spawn_2d_level()
        elif dimension_id == "3d":
            self._spawn_3d_level()
        elif dimension_id == "4d":
            self._spawn_4d_level()
        else:
            # Default: just spawn player
            self._spawn_player(dimension_id, np.zeros(4))
        
        # Handle mouse capture for 3D/4D
        if dimension_id in ("3d", "4d"):
            self._set_mouse_capture(True)
        else:
            self._set_mouse_capture(False)
    
    def _spawn_player(self, dimension_id: str, position: np.ndarray) -> Entity:
        """Spawn the player entity."""
        controller_map = {
            "1d": "line",
            "2d": "plane",
            "3d": "volume",
            "4d": "hyper",
        }
        controller_type = controller_map.get(dimension_id, "plane")
        
        collider_map = {
            "1d": ColliderShape.SEGMENT,
            "2d": ColliderShape.CIRCLE,
            "3d": ColliderShape.SPHERE,
            "4d": ColliderShape.SPHERE,
        }
        collider_shape = collider_map.get(dimension_id, ColliderShape.CIRCLE)
        
        player = Entity(id="player")
        player.add(Transform(position=position.copy()))
        player.add(Velocity())
        player.add(Renderable(color=(80, 200, 255), glow=1.0))
        player.add(Collider(
            shape=collider_shape,
            size=np.array([0.5]),
        ))
        player.add(Health(current=20, max=20))
        player.add(Controller(controller_type=controller_type, speed=8.0))
        player.add(DimensionAnchor(dimension_id=dimension_id))
        player.tag("player", "controllable")
        
        self.world.spawn(player)
        return player
    
    def _spawn_1d_level(self) -> None:
        """Spawn a 1D level with diverse entities representing different realms.
        
        The Line is divided into realms:
        - Origin Point (-10 to 0): Safe starting area with Point Spirits
        - Forward Path (0 to 20): Forward Sentinels patrol here
        - Backward Void (-40 to -10): Void Echoes dwell here
        - Midpoint Station (20): Toll Collector (friendly NPC area)
        - The Endpoint (30 to 45): Boss area with Segment Guardian
        """
        # Set world bounds - The Line stretches from -45 to +45
        self.physics_system.set_bounds("1d", 0, -45.0, 45.0)
        
        # Spawn player at origin
        self._spawn_player("1d", np.array([0.0, 0.0, 0.0, 0.0]))
        
        # Set starting realm
        self._current_realm_id = "origin_point"
        
        # === ORIGIN POINT REALM (-10 to 0) ===
        # Point Spirits - one gentle introduction encounter near the origin.
        point_spirit_positions = [-6.0]
        for i, x in enumerate(point_spirit_positions):
            spirit = Entity(id=f"point_spirit_{i}")
            spirit.add(Transform(position=np.array([x, 0.0, 0.0, 0.0])))
            spirit.add(Velocity())
            spirit.add(Renderable(color=(255, 255, 200)))  # Pale yellow glow
            spirit.add(Collider(shape=ColliderShape.SEGMENT, size=np.array([0.4]), is_trigger=True))
            spirit.add(Health(current=8, max=8))
            spirit.add(AIBrain(
                behavior="oscillate",
                state={"center": x, "amplitude": 1.0, "speed": 0.5, "direction": 1,
                       "enemy_id": "point_spirit", "realm": "origin_point"}
            ))
            spirit.add(DimensionAnchor(dimension_id="1d"))
            spirit.tag("encounter_trigger", "point_spirit")
            self.world.spawn(spirit)
        
        # === FORWARD PATH REALM (5 to 20) ===
        # Line Walkers - confused but not hostile (blue)
        line_walker = Entity(id="line_walker_0")
        line_walker.add(Transform(position=np.array([8.0, 0.0, 0.0, 0.0])))
        line_walker.add(Velocity())
        line_walker.add(Renderable(color=(100, 200, 255)))  # Blue
        line_walker.add(Collider(shape=ColliderShape.SEGMENT, size=np.array([0.6]), is_trigger=True))
        line_walker.add(Health(current=15, max=15))
        line_walker.add(AIBrain(
            behavior="oscillate",
            state={"center": 8.0, "amplitude": 2.5, "speed": 1.2, "direction": 1,
                   "enemy_id": "line_walker", "realm": "forward_path"}
        ))
        line_walker.add(DimensionAnchor(dimension_id="1d"))
        line_walker.tag("encounter_trigger", "line_walker")
        self.world.spawn(line_walker)
        
        # Forward Sentinel - aggressive guardian (red)
        sentinel = Entity(id="forward_sentinel_0")
        sentinel.add(Transform(position=np.array([15.0, 0.0, 0.0, 0.0])))
        sentinel.add(Velocity())
        sentinel.add(Renderable(color=(255, 100, 100)))  # Red
        sentinel.add(Collider(shape=ColliderShape.SEGMENT, size=np.array([0.8]), is_trigger=True))
        sentinel.add(Health(current=25, max=25))
        sentinel.add(AIBrain(
            behavior="oscillate",
            state={"center": 15.0, "amplitude": 2.0, "speed": 1.0, "direction": 1,
                   "enemy_id": "forward_sentinel", "realm": "forward_path"}
        ))
        sentinel.add(DimensionAnchor(dimension_id="1d"))
        sentinel.tag("encounter_trigger", "forward_sentinel")
        self.world.spawn(sentinel)
        
        # === BACKWARD VOID REALM (-40 to -10) ===
        # Void Echoes - philosophical beings from the void (dark purple)
        void_echo_positions = [-24.0]
        for i, x in enumerate(void_echo_positions):
            echo = Entity(id=f"void_echo_{i}")
            echo.add(Transform(position=np.array([x, 0.0, 0.0, 0.0])))
            echo.add(Velocity())
            echo.add(Renderable(color=(80, 80, 120)))  # Dark purple
            echo.add(Collider(shape=ColliderShape.SEGMENT, size=np.array([0.7]), is_trigger=True))
            echo.add(Health(current=20, max=20))
            echo.add(AIBrain(
                behavior="oscillate",
                state={"center": x, "amplitude": 1.5, "speed": 0.8, "direction": -1,
                       "enemy_id": "void_echo", "realm": "backward_void"}
            ))
            echo.add(DimensionAnchor(dimension_id="1d"))
            echo.tag("encounter_trigger", "void_echo")
            self.world.spawn(echo)
        
        # === MIDPOINT STATION (around x=22) ===
        # Toll Collector - playful gatekeeper (gold)
        toll_collector = Entity(id="toll_collector_0")
        toll_collector.add(Transform(position=np.array([22.0, 0.0, 0.0, 0.0])))
        toll_collector.add(Velocity())
        toll_collector.add(Renderable(color=(200, 180, 100)))  # Gold
        toll_collector.add(Collider(shape=ColliderShape.SEGMENT, size=np.array([0.6]), is_trigger=True))
        toll_collector.add(Health(current=18, max=18))
        toll_collector.add(AIBrain(
            behavior="stationary",
            state={"enemy_id": "toll_collector", "realm": "midpoint_station"}
        ))
        toll_collector.add(DimensionAnchor(dimension_id="1d"))
        toll_collector.tag("encounter_trigger", "toll_collector")
        self.world.spawn(toll_collector)
        
        # === THE ENDPOINT (30 to 45) ===
        # Segment Guardian - BOSS (orange-gold, larger)
        guardian = Entity(id="segment_guardian")
        guardian.add(Transform(position=np.array([35.0, 0.0, 0.0, 0.0])))
        guardian.add(Velocity())
        guardian.add(Renderable(color=(255, 200, 100)))  # Orange-gold
        guardian.add(Collider(shape=ColliderShape.SEGMENT, size=np.array([1.2]), is_trigger=True))
        guardian.add(Health(current=40, max=40))
        guardian.add(AIBrain(
            behavior="oscillate",
            state={"center": 35.0, "amplitude": 1.5, "speed": 0.8, "direction": 1,
                   "enemy_id": "segment_guardian", "realm": "the_endpoint", "is_boss": True}
        ))
        guardian.add(DimensionAnchor(dimension_id="1d"))
        guardian.tag("encounter_trigger", "segment_guardian", "boss")
        self.world.spawn(guardian)
        
        # === PICKUPS (energy orbs) ===
        pickup_positions = [-3.0, 5.0, 12.0, 25.0]
        for i, x in enumerate(pickup_positions):
            pickup = Entity(id=f"pickup_{i}")
            pickup.add(Transform(position=np.array([x, 0.0, 0.0, 0.0])))
            pickup.add(Renderable(color=(255, 220, 50)))
            pickup.add(Collider(shape=ColliderShape.SEGMENT, size=np.array([0.3]), is_trigger=True))
            pickup.add(Pickup(item_type="energy", value=1))
            pickup.add(DimensionAnchor(dimension_id="1d"))
            pickup.tag("pickup")
            self.world.spawn(pickup)
        
        # === REALM MARKERS (visual indicators) ===
        # These are non-collidable visual markers showing realm boundaries
        realm_markers = [
            (-10.0, (60, 60, 80)),   # Origin->Backward Void boundary
            (5.0, (60, 80, 100)),    # Origin->Forward Path boundary  
            (20.0, (80, 70, 50)),    # Forward Path->Midpoint boundary
            (30.0, (100, 80, 60)),   # Midpoint->Endpoint boundary
        ]
        for i, (x, color) in enumerate(realm_markers):
            marker = Entity(id=f"realm_marker_{i}")
            marker.add(Transform(position=np.array([x, 0.0, 0.0, 0.0])))
            marker.add(Renderable(color=color))
            marker.add(DimensionAnchor(dimension_id="1d"))
            marker.tag("marker")
            self.world.spawn(marker)
        
        # === PORTAL TO 2D (after defeating boss) ===
        portal = Entity(id="portal_2d")
        portal.add(Transform(position=np.array([42.0, 0.0, 0.0, 0.0])))
        portal.add(Renderable(color=(150, 50, 255)))
        portal.add(Collider(shape=ColliderShape.SEGMENT, size=np.array([1.0]), is_trigger=True))
        portal.add(Portal(target_dimension="2d", active=True))
        portal.add(DimensionAnchor(dimension_id="1d"))
        portal.tag("portal")
        self.world.spawn(portal)
    
    def _spawn_2d_level(self) -> None:
        """Spawn a basic 2D level."""
        # Set world bounds
        self.physics_system.set_bounds("2d", 0, -40.0, 40.0)
        self.physics_system.set_bounds("2d", 1, -30.0, 30.0)
        
        # Spawn player
        self._spawn_player("2d", np.array([0.0, 0.0, 0.0, 0.0]))
        
        # Spawn enemies
        enemy_configs = [
            ((-10.0, 5.0), "patrol", [np.array([-10.0, 5.0]), np.array([-10.0, -5.0])]),
            ((10.0, -5.0), "patrol", [np.array([10.0, -5.0]), np.array([10.0, 5.0])]),
            ((0.0, 15.0), "chase", []),
        ]
        
        for i, (pos, behavior, patrol) in enumerate(enemy_configs):
            enemy = Entity(id=f"enemy_{i}")
            enemy.add(Transform(position=np.array([pos[0], pos[1], 0.0, 0.0])))
            enemy.add(Velocity())
            enemy.add(Renderable(color=(200, 50, 50)))
            enemy.add(Collider(shape=ColliderShape.CIRCLE, size=np.array([0.6])))
            enemy.add(Health(current=50, max=50))
            enemy.add(AIBrain(
                behavior=behavior,
                patrol_points=patrol,
                detect_range=12.0,
                attack_range=1.5,
                state={"speed": 3.5}
            ))
            enemy.add(DimensionAnchor(dimension_id="2d"))
            enemy.tag("enemy")
            self.world.spawn(enemy)
        
        # Spawn pickups
        pickup_positions = [(5.0, 5.0), (-5.0, -5.0), (15.0, 10.0), (-15.0, -10.0)]
        for i, pos in enumerate(pickup_positions):
            pickup = Entity(id=f"pickup_{i}")
            pickup.add(Transform(position=np.array([pos[0], pos[1], 0.0, 0.0])))
            pickup.add(Renderable(color=(255, 220, 50)))
            pickup.add(Collider(shape=ColliderShape.CIRCLE, size=np.array([0.4]), is_trigger=True))
            pickup.add(Pickup(item_type="energy", value=1))
            pickup.add(DimensionAnchor(dimension_id="2d"))
            pickup.tag("pickup")
            self.world.spawn(pickup)
        
        # Portal to 3D
        portal = Entity(id="portal_3d")
        portal.add(Transform(position=np.array([30.0, 20.0, 0.0, 0.0])))
        portal.add(Renderable(color=(150, 50, 255)))
        portal.add(Collider(shape=ColliderShape.CIRCLE, size=np.array([1.2]), is_trigger=True))
        portal.add(Portal(target_dimension="3d", active=True))
        portal.add(DimensionAnchor(dimension_id="2d"))
        portal.tag("portal")
        self.world.spawn(portal)
    
    def _spawn_3d_level(self) -> None:
        """Spawn a 3D volume level."""
        # Set world bounds
        self.physics_system.set_bounds("3d", 0, -50.0, 50.0)
        self.physics_system.set_bounds("3d", 1, -5.0, 50.0)  # Y is up
        self.physics_system.set_bounds("3d", 2, -50.0, 50.0)
        
        # Spawn player
        self._spawn_player("3d", np.array([0.0, 1.0, 0.0, 0.0]))
        
        # Spawn 3D enemies
        enemy_configs = [
            ((10.0, 1.0, 10.0), "patrol", [np.array([10.0, 1.0, 10.0]), np.array([10.0, 1.0, -10.0])]),
            ((-10.0, 1.0, -5.0), "patrol", [np.array([-10.0, 1.0, -5.0]), np.array([-10.0, 1.0, 15.0])]),
            ((0.0, 1.0, 20.0), "chase", []),
            ((15.0, 1.0, -15.0), "chase", []),
        ]
        
        for i, (pos, behavior, patrol) in enumerate(enemy_configs):
            enemy = Entity(id=f"enemy_{i}")
            enemy.add(Transform(position=np.array([pos[0], pos[1], pos[2], 0.0])))
            enemy.add(Velocity())
            enemy.add(Renderable(color=(200, 50, 50)))
            enemy.add(Collider(shape=ColliderShape.SPHERE, size=np.array([0.8])))
            enemy.add(Health(current=75, max=75))
            enemy.add(AIBrain(
                behavior=behavior,
                patrol_points=patrol,
                detect_range=15.0,
                attack_range=2.0,
                state={"speed": 4.0}
            ))
            enemy.add(DimensionAnchor(dimension_id="3d"))
            enemy.tag("enemy")
            self.world.spawn(enemy)
        
        # Spawn pickups in 3D space
        pickup_positions = [
            (5.0, 1.0, 5.0), (-5.0, 1.0, -5.0), 
            (15.0, 1.0, 10.0), (-15.0, 1.0, -10.0),
            (0.0, 3.0, 0.0), (20.0, 1.0, 0.0),
        ]
        for i, pos in enumerate(pickup_positions):
            pickup = Entity(id=f"pickup_{i}")
            pickup.add(Transform(position=np.array([pos[0], pos[1], pos[2], 0.0])))
            pickup.add(Renderable(color=(255, 220, 50)))
            pickup.add(Collider(shape=ColliderShape.SPHERE, size=np.array([0.5]), is_trigger=True))
            pickup.add(Pickup(item_type="energy", value=1))
            pickup.add(DimensionAnchor(dimension_id="3d"))
            pickup.tag("pickup")
            self.world.spawn(pickup)
        
        # Portal to 4D
        portal = Entity(id="portal_4d")
        portal.add(Transform(position=np.array([40.0, 1.0, 40.0, 0.0])))
        portal.add(Renderable(color=(180, 100, 255)))
        portal.add(Collider(shape=ColliderShape.SPHERE, size=np.array([1.5]), is_trigger=True))
        portal.add(Portal(target_dimension="4d", active=True))
        portal.add(DimensionAnchor(dimension_id="3d"))
        portal.tag("portal")
        self.world.spawn(portal)
    
    def _spawn_4d_level(self) -> None:
        """Spawn a 4D hyperspace level."""
        # Set world bounds
        self.physics_system.set_bounds("4d", 0, -50.0, 50.0)
        self.physics_system.set_bounds("4d", 1, -5.0, 50.0)
        self.physics_system.set_bounds("4d", 2, -50.0, 50.0)
        # W bounds handled implicitly
        
        # Spawn player
        self._spawn_player("4d", np.array([0.0, 1.0, 0.0, 0.0]))
        
        # Spawn 4D enemies (positioned in hyperspace)
        enemy_configs = [
            ((10.0, 1.0, 10.0, 0.0), "patrol"),
            ((-10.0, 1.0, -5.0, 0.5), "chase"),
            ((0.0, 1.0, 20.0, -0.5), "chase"),
            ((15.0, 1.0, -15.0, 1.0), "patrol"),
            ((5.0, 1.0, 5.0, -1.0), "chase"),  # In different W slice
        ]
        
        for i, (pos, behavior) in enumerate(enemy_configs):
            enemy = Entity(id=f"enemy_{i}")
            enemy.add(Transform(position=np.array([pos[0], pos[1], pos[2], pos[3]])))
            enemy.add(Velocity())
            enemy.add(Renderable(color=(200, 50, 50)))
            enemy.add(Collider(shape=ColliderShape.SPHERE, size=np.array([0.8])))
            enemy.add(Health(current=100, max=100))
            enemy.add(AIBrain(
                behavior=behavior,
                detect_range=12.0,
                attack_range=2.0,
                state={"speed": 3.5}
            ))
            enemy.add(DimensionAnchor(dimension_id="4d"))
            enemy.tag("enemy")
            self.world.spawn(enemy)
        
        # Spawn pickups across W slices
        pickup_positions = [
            (5.0, 1.0, 5.0, 0.0), (-5.0, 1.0, -5.0, 0.0),
            (15.0, 1.0, 10.0, 0.5), (-15.0, 1.0, -10.0, -0.5),
            (0.0, 2.0, 0.0, 1.0), (20.0, 1.0, 0.0, -1.0),
        ]
        for i, pos in enumerate(pickup_positions):
            pickup = Entity(id=f"pickup_{i}")
            pickup.add(Transform(position=np.array([pos[0], pos[1], pos[2], pos[3]])))
            pickup.add(Renderable(color=(255, 220, 50)))
            pickup.add(Collider(shape=ColliderShape.SPHERE, size=np.array([0.5]), is_trigger=True))
            pickup.add(Pickup(item_type="hypercrystal", value=2))
            pickup.add(DimensionAnchor(dimension_id="4d"))
            pickup.tag("pickup")
            self.world.spawn(pickup)
        
        # Victory portal (back to start or end game)
        portal = Entity(id="portal_victory")
        portal.add(Transform(position=np.array([0.0, 1.0, 50.0, 0.0])))
        portal.add(Renderable(color=(255, 200, 100)))
        portal.add(Collider(shape=ColliderShape.SPHERE, size=np.array([2.0]), is_trigger=True))
        portal.add(Portal(target_dimension="1d", active=True))  # Loop back
        portal.add(DimensionAnchor(dimension_id="4d"))
        portal.tag("portal", "victory")
        self.world.spawn(portal)
    
    def _set_mouse_capture(self, capture: bool) -> None:
        """Enable or disable mouse capture for FPS-style control."""
        self._mouse_captured = capture
        pygame.mouse.set_visible(not capture)
        pygame.event.set_grab(capture)
        
        # Update controllers
        self._volume_controller.mouse_captured = capture
        self._hyper_controller.mouse_captured = capture

    def initialize_runtime(self) -> None:
        """Initialize runtime systems shared by direct run and launcher mode."""
        if self._runtime_initialized:
            return

        # Initialize old combat system (fallback)
        self.combat = create_combat_integration(self.screen, self.session)
        self.combat.on_combat_end = self._on_combat_end
        self.combat.on_boss_defeated = self._on_boss_defeated

        # Initialize NEW dimensional combat system
        self.dimensional_combat = create_dimensional_combat_integration(self.screen, self.session)
        self.dimensional_combat.on_combat_end = self._on_combat_end
        self.dimensional_combat.on_boss_defeated = self._on_boss_defeated
        self.dimensional_combat.on_dimension_unlock = self._on_dimension_unlock

        # Initialize story encounter manager
        self.story_encounters = get_encounter_manager()

        # Initialize first dimension
        self._reload_dimension()

        # Play initial campaign dialogue if set
        if self._initial_dialogue_id and not self._initial_dialogue_played:
            self._initial_dialogue_played = True
            self.dialogue.start_sequence(self._initial_dialogue_id)

        self._runtime_initialized = True
    
    def run(self) -> None:
        """Run the main game loop."""
        self.running = True
        self.initialize_runtime()
        
        while self.running:
            dt = self.clock.tick(self.target_fps) / 1000.0
            
            # Process events
            self._process_events()
            self._update(dt)
            
            # Render
            self._render()
            
            # End frame
            self.end_frame()
            pygame.display.flip()
        
        # Save progression on exit
        from hypersim.game.save import save_progression
        save_progression(self.session.progression)
        
        pygame.quit()

    def _update(self, dt: float) -> None:
        """Advance the game by a single frame."""
        self.initialize_runtime()

        # Keep mouse-look responsive in both standalone and launcher modes.
        if self._mouse_captured and not self.paused and not self.dialogue.is_active:
            self._volume_controller.process_mouse(self.input_handler)
            self._hyper_controller.process_mouse(self.input_handler)

        dialogue_active = self.dialogue.should_pause_game
        line_birth_active = self._is_line_birth_active()
        guardian_active = self._line_guardian_active
        old_combat_active = self.combat and (self.combat.in_combat or self.combat.transitioning)
        dim_combat_active = self.dimensional_combat and (
            self.dimensional_combat.in_combat or self.dimensional_combat.transitioning
        )

        self._sync_line_birth_music()
        self._update_line_strain(dt)

        if line_birth_active:
            self._update_line_birth_ritual(dt)

        if dim_combat_active:
            self.dimensional_combat.update(dt)
        elif old_combat_active:
            self.combat.update(dt)
        elif guardian_active:
            pass
        elif line_birth_active:
            pass
        elif not self.paused and not dialogue_active:
            self.world.update(dt)
            self._update_1d_world_beats()

            for event in self.world.drain_events():
                self.session.record_event(event.event_type, **event.data)
                self._record_world_event(event.event_type, **event.data)

            self._check_random_encounter()

        self.dialogue.update(dt)
        self.overlays.update(dt)

        if self._line_guardian_active or self._line_guardian_reset_pending:
            self._update_line_guardian_scene(dt)

        if (
            self._line_guardian_reset_pending
            and not self.dialogue.is_active
            and self._line_guardian_transition_progress >= 1.0
        ):
            self._complete_line_guardian_intervention()

        if not self.dialogue.is_active and self._queued_dialogues:
            next_dialogue = self._queued_dialogues.pop(0)
            self.dialogue.start_sequence(next_dialogue)
    
    def _check_random_encounter(self) -> None:
        """Check for random combat encounters based on player movement."""
        if not self.combat or self.combat.in_combat:
            return
        
        # 1D already has curated encounter entities; random battles feel repetitive here.
        if self.session.active_dimension.id == "1d":
            return
        
        # Only check encounters when player moves
        player = self.world.get("player")
        if not player:
            return
        
        velocity = player.get(Velocity)
        if not velocity:
            return
        
        # Check if player is moving
        speed = np.linalg.norm(velocity.linear[:2])
        if speed < 0.1:
            return
        
        # Increment steps
        self._steps_in_realm += 1
        
        # Check for encounter every ~60 frames (1 second) of movement
        if self._steps_in_realm % 60 != 0:
            return
        
        # Get current realm (default to dimension's starting realm)
        if not self._current_realm_id:
            dim_id = self.session.active_dimension.id
            starting_realm = get_starting_realm(dim_id)
            self._current_realm_id = starting_realm.id if starting_realm else None
        
        if not self._current_realm_id:
            return
        
        # Check for random encounter
        enemy_id = self.combat.check_random_encounter(self._current_realm_id)
        if enemy_id:
            self._start_combat_encounter(enemy_id)
    
    def _start_combat_encounter(self, enemy_id: str) -> None:
        """Start a combat encounter with the given enemy."""
        # Release mouse capture for combat
        if self._mouse_captured:
            self._set_mouse_capture(False)
        
        # Get enemy to determine dimension
        from hypersim.game.combat.enemies import get_enemy
        enemy = get_enemy(enemy_id)
        enemy_name = enemy.name if enemy else enemy_id.replace("_", " ").title()
        enemy_dimension = getattr(enemy, 'dimension', '2d') if enemy else '2d'
        
        # Use dimensional combat for non-2D enemies
        if self._use_dimensional_combat and self.dimensional_combat and enemy_dimension != '2d':
            config = DimensionalEncounterConfig(
                enemy_id=enemy_id,
                dimension=CombatDimension.ONE_D if enemy_dimension == '1d' else (
                    CombatDimension.THREE_D if enemy_dimension == '3d' else CombatDimension.FOUR_D
                ),
                can_flee=True,
                is_boss=getattr(enemy, 'is_boss', False) if enemy else False,
            )
            
            if self.dimensional_combat.start_encounter(config):
                self.audio.play("encounter")
                self.overlays.notify(f"⚔️ {enemy_name} appears!", duration=1.5, color=(255, 100, 100))
        elif self.combat:
            # Use old combat system for 2D
            if self.combat.start_random_encounter(enemy_id):
                self.audio.play("encounter")
                self.overlays.notify("⚔️ ENCOUNTER!", duration=1.5, color=(255, 100, 100))
    
    def _is_entity_on_encounter_cooldown(self, entity: Entity) -> bool:
        """Return True if this entity should not re-trigger encounter logic yet."""
        cooldown_until = getattr(entity, "_encounter_cooldown_until_ms", 0)
        return pygame.time.get_ticks() < cooldown_until
    
    def _set_entity_encounter_cooldown(self, entity: Entity, seconds: float) -> None:
        """Set an encounter cooldown on the entity."""
        entity._encounter_cooldown_until_ms = pygame.time.get_ticks() + int(max(0.0, seconds) * 1000)
    
    def _handle_encounter_contact(self, entity: Entity, enemy_id: str) -> None:
        """Handle contact with an encounter entity."""
        # Check if any combat system is already active.
        old_combat_busy = self.combat and (self.combat.in_combat or self.combat.transitioning)
        dim_combat_busy = self.dimensional_combat and (self.dimensional_combat.in_combat or self.dimensional_combat.transitioning)
        if old_combat_busy or dim_combat_busy:
            return
        
        if not entity.active or entity.has_tag("friendly"):
            return
        
        if self._is_entity_on_encounter_cooldown(entity):
            return
        
        # In 1D we offer a choice prompt instead of instant aggression.
        if self.session.active_dimension.id == "1d":
            if self.dialogue.is_active:
                return
            self._show_encounter_prompt(entity, enemy_id)
            return
        
        self._trigger_encounter(enemy_id, entity)
    
    def _show_encounter_prompt(self, entity: Entity, enemy_id: str) -> None:
        """Show Talk / Ignore / Fight prompt for a nearby encounter entity."""
        from hypersim.game.ui.textbox import DialogueSequence, DialogueLine, TextBoxStyle
        from hypersim.game.combat.enemies import get_enemy
        
        if self.dialogue.is_active:
            return
        
        enemy = get_enemy(enemy_id)
        enemy_name = enemy.name if enemy else enemy_id.replace("_", " ").title()
        seq_id = f"encounter_prompt_{entity.id}"
        
        self._encounter_prompt_entity = entity
        
        seq = DialogueSequence(
            id=seq_id,
            lines=[
                DialogueLine(
                    speaker=enemy_name,
                    text="A nearby presence notices you. How do you respond?",
                    style=TextBoxStyle.CHARACTER,
                    choices=[
                        ("Talk first.", "encounter_choice_talk"),
                        ("Ignore and move on.", "encounter_choice_ignore"),
                        ("Fight.", "encounter_choice_fight"),
                    ],
                )
            ],
            pause_game=True,
            can_skip=False,
        )
        self.dialogue.register_sequence(seq)
        self.dialogue.start_sequence(seq_id)
    
    def _get_pending_encounter_prompt(self) -> tuple[Optional[Entity], str]:
        """Get currently prompted encounter entity and enemy id."""
        entity = self._encounter_prompt_entity
        if not entity or not entity.active:
            self._encounter_prompt_entity = None
            return None, ""
        
        ai_brain = entity.get(AIBrain)
        enemy_id = ai_brain.state.get("enemy_id", "") if ai_brain else ""
        if not enemy_id:
            self._encounter_prompt_entity = None
            return None, ""
        return entity, enemy_id
    
    def _can_talk_pacify(self, enemy_id: str) -> bool:
        """Return whether this enemy can be permanently calmed by dialogue."""
        return enemy_id in {"point_spirit", "line_walker", "void_echo", "toll_collector"}
    
    def _get_talk_response(self, enemy_id: str) -> str:
        """Contextual one-line response for talk-first encounters."""
        responses = {
            "point_spirit": "\"I only wanted to be seen.\"",
            "line_walker": "\"You move strangely... but not with malice.\"",
            "forward_sentinel": "\"State your direction. I will watch your next step.\"",
            "void_echo": "\"Even silence can be a truce.\"",
            "toll_collector": "\"A polite traveler! No toll for kindness today.\"",
            "segment_guardian": "\"Understanding before violence. Good.\"",
        }
        return responses.get(enemy_id, "The being studies you, then eases back.")
    
    def _on_encounter_choice_talk(self) -> None:
        """Handle choosing to talk first at an encounter prompt."""
        from hypersim.game.combat.enemies import get_enemy
        
        entity, enemy_id = self._get_pending_encounter_prompt()
        self.dialogue.stop()
        self._encounter_prompt_entity = None
        
        if not entity or not enemy_id:
            return
        
        enemy = get_enemy(enemy_id)
        enemy_name = enemy.name if enemy else enemy_id.replace("_", " ").title()
        
        # Give breathing room to prevent immediate re-prompting.
        self._set_entity_encounter_cooldown(entity, 6.0)
        
        if self._can_talk_pacify(enemy_id):
            entity.untag("encounter_trigger")
            entity.tag("friendly")
            renderable = entity.get(Renderable)
            if renderable:
                renderable.color = (100, 230, 160)
            self.overlays.notify(f"{enemy_name} stands down.", duration=2.0, color=(100, 230, 160))
        else:
            self.overlays.notify(f"{enemy_name} remains wary.", duration=2.0, color=(220, 180, 120))
        
        self._play_sequence_inline(
            f"encounter_talk_{entity.id}",
            [
                {
                    "speaker": enemy_name,
                    "text": self._get_talk_response(enemy_id),
                    "style": TextBoxStyle.CHARACTER,
                }
            ],
            pause=True,
        )
    
    def _on_encounter_choice_ignore(self) -> None:
        """Handle choosing to ignore an encounter."""
        entity, _ = self._get_pending_encounter_prompt()
        self.dialogue.stop()
        self._encounter_prompt_entity = None
        
        if entity:
            self._set_entity_encounter_cooldown(entity, 8.0)
        self.overlays.notify("You keep your distance.", duration=1.8, color=(170, 170, 190))
    
    def _on_encounter_choice_fight(self) -> None:
        """Handle choosing to fight from the encounter prompt."""
        entity, enemy_id = self._get_pending_encounter_prompt()
        self.dialogue.stop()
        self._encounter_prompt_entity = None
        
        if entity and enemy_id:
            self._trigger_encounter(enemy_id, entity)
    
    def _trigger_encounter(self, enemy_id: str, entity: Entity) -> None:
        """Trigger a combat encounter from touching an entity in the world.
        
        Args:
            enemy_id: The combat enemy ID to fight
            entity: The world entity that triggered the encounter
        """
        # Check if any combat system is already active
        old_combat_busy = self.combat and (self.combat.in_combat or self.combat.transitioning)
        dim_combat_busy = self.dimensional_combat and (self.dimensional_combat.in_combat or self.dimensional_combat.transitioning)
        
        if old_combat_busy or dim_combat_busy:
            return
        
        # Don't re-trigger recently fought / prompted entities.
        if self._is_entity_on_encounter_cooldown(entity):
            return
        
        # Get enemy info from AI brain
        ai_brain = entity.get(AIBrain)
        is_boss = ai_brain.state.get("is_boss", False) if ai_brain else False
        realm = ai_brain.state.get("realm", self._current_realm_id) if ai_brain else self._current_realm_id
        
        # Update current realm based on entity
        if realm:
            self._current_realm_id = realm
        
        # Release mouse capture for combat
        if self._mouse_captured:
            self._set_mouse_capture(False)
        
        # Determine dimension from entity's anchor first, then enemy definition
        entity_anchor = entity.get(DimensionAnchor)
        entity_dimension = entity_anchor.dimension_id if entity_anchor else None
        
        # Get enemy to determine dimension (fallback)
        from hypersim.game.combat.enemies import get_enemy
        enemy = get_enemy(enemy_id)
        enemy_name = enemy.name if enemy else enemy_id.replace("_", " ").title()
        enemy_dimension = entity_dimension or (getattr(enemy, 'dimension', '2d') if enemy else '2d')
        
        # Use NEW dimensional combat for 1D, 3D, 4D enemies (always use for non-2D)
        if self._use_dimensional_combat and self.dimensional_combat and enemy_dimension != '2d':
            config = DimensionalEncounterConfig(
                enemy_id=enemy_id,
                dimension=CombatDimension.ONE_D if enemy_dimension == '1d' else (
                    CombatDimension.THREE_D if enemy_dimension == '3d' else CombatDimension.FOUR_D
                ),
                can_flee=not is_boss,
                is_boss=is_boss,
            )
            
            if self.dimensional_combat.start_encounter(config):
                self._current_encounter_entity = entity
                self.audio.play("encounter")
                
                if is_boss:
                    self.overlays.notify(f"⚔️ BOSS: {enemy_name}!", duration=2.0, color=(255, 50, 50))
                else:
                    self.overlays.notify(f"⚔️ {enemy_name} appears!", duration=1.5, color=(255, 100, 100))
        else:
            # Use old combat system for 2D or if dimensional combat disabled
            from hypersim.game.combat import EncounterConfig, EncounterType
            
            config = EncounterConfig(
                enemy_id=enemy_id,
                encounter_type=EncounterType.BOSS if is_boss else EncounterType.RANDOM,
                can_flee=not is_boss,
            )
            
            if self.combat and self.combat.start_encounter(config):
                self._current_encounter_entity = entity
                self.audio.play("encounter")
                
                if is_boss:
                    self.overlays.notify(f"⚔️ BOSS: {enemy_name}!", duration=2.0, color=(255, 50, 50))
                else:
                    self.overlays.notify(f"⚔️ {enemy_name} appears!", duration=1.5, color=(255, 100, 100))
    
    def _on_combat_end(self, result: CombatResult, xp: int, gold: int, enemy_id: str = "") -> None:
        """Handle combat ending."""
        # Update session
        self.session.progression.xp += xp
        self.session.progression.gold = getattr(self.session.progression, 'gold', 0) + gold
        
        # Track in story system for route determination
        if result == CombatResult.VICTORY:
            self.story.record_kill(enemy_id)
            self.overlays.notify(f"Victory! +{xp} XP, +{gold}G", color=(255, 255, 100))
            self.audio.play("victory")
        elif result == CombatResult.SPARE:
            self.story.record_spare(enemy_id)
            self.overlays.notify(f"Spared! +{gold}G", color=(255, 255, 100))
            self.audio.play("spare")
        elif result == CombatResult.FLEE:
            self.story.record_flee()
            self.overlays.notify("Escaped!", color=(200, 200, 200))
        elif result == CombatResult.DEFEAT:
            self.overlays.notify("Defeated...", color=(255, 100, 100))
            # Respawn player with reduced HP
            if self.combat:
                self.combat.player_stats.hp = self.combat.player_stats.max_hp // 2
        
        # Handle the world entity that triggered the encounter
        if hasattr(self, '_current_encounter_entity') and self._current_encounter_entity:
            entity = self._current_encounter_entity
            if result == CombatResult.VICTORY:
                # Trigger death animation before removing
                self._trigger_entity_death_animation(entity)
                # Remove defeated enemy from world
                entity.active = False
                self.world.despawn(entity.id)
            elif result == CombatResult.SPARE:
                # Spared enemies become friendly (remove encounter trigger)
                entity.untag("encounter_trigger")
                entity.tag("friendly")
                self._set_entity_encounter_cooldown(entity, 10.0)
                # Change color to indicate friendliness
                renderable = entity.get(Renderable)
                if renderable:
                    renderable.color = (100, 255, 150)  # Greenish
            elif result == CombatResult.FLEE:
                self._set_entity_encounter_cooldown(entity, 8.0)
                # Move player away from enemy to prevent immediate re-encounter
                player = self.world.get("player")
                if player:
                    player_transform = player.get(Transform)
                    entity_transform = entity.get(Transform)
                    if player_transform and entity_transform:
                        # Move player 5 units away in opposite direction
                        diff = player_transform.position - entity_transform.position
                        if np.linalg.norm(diff) > 0:
                            diff = diff / np.linalg.norm(diff) * 5.0
                            player_transform.position = player_transform.position + diff
            
            self._current_encounter_entity = None
        
        # Check current route and notify player of major shifts
        route = self.story.get_current_route()
        self._check_route_notification(route)
        
        # Re-capture mouse if in 3D/4D
        dim_id = self.session.active_dimension.id
        if dim_id in ("3d", "4d"):
            self._set_mouse_capture(True)
    
    def _trigger_entity_death_animation(self, entity: Entity) -> None:
        """Trigger death/explosion animation for a 1D entity."""
        dim_id = self.session.active_dimension.id
        if dim_id != "1d":
            return  # Only for 1D entities for now
        
        # Get the LineRenderer to access the particle system
        renderer = self._renderers.get("1d")
        if not renderer or not hasattr(renderer, 'particle_system'):
            return
        
        # Get entity position and color
        transform = entity.get(Transform)
        renderable = entity.get(Renderable)
        if not transform:
            return
        
        # Calculate screen position
        player = self.world.find_player()
        player_x = 0.0
        if player:
            player_transform = player.get(Transform)
            if player_transform:
                player_x = player_transform.position[0]
        
        screen_x = renderer.world_to_screen(transform.position[0], 0)[0]
        color = renderable.color if renderable else (255, 255, 255)
        
        # Trigger death animation
        renderer.particle_system.trigger_death(entity.id, screen_x, color, 30)
    
    def _check_route_notification(self, route: StoryRoute) -> None:
        """Notify player if they've shifted to a specific route."""
        state = self.story.route_state
        
        # Ascension hints
        if route == StoryRoute.ASCENSION and state.enemies_spared == 5:
            self.overlays.notify("♥ Path of Mercy...", duration=3.0, color=(255, 200, 255))
        
        # Conquest warnings
        if route == StoryRoute.CONQUEST and state.enemies_killed == 5:
            self.overlays.notify("⚔ Path of Conquest...", duration=3.0, color=(255, 100, 100))
    
    def _on_boss_defeated(self, boss_id: str) -> None:
        """Handle boss being defeated."""
        self.overlays.notify(f"★ BOSS DEFEATED: {boss_id} ★", duration=5.0, color=(255, 220, 100))
        self.audio.play("boss_defeated")
        
        # Unlock next dimension if this was a border boss
        dim_id = self.session.active_dimension.id
        next_dims = {"1d": "2d", "2d": "3d", "3d": "4d"}
        if dim_id in next_dims:
            # Could trigger dimension unlock dialogue here
            self.dialogue.start_sequence(f"unlock_{next_dims[dim_id]}")
    
    def _on_dimension_unlock(self, dimension_id: str) -> None:
        """Handle dimension being unlocked by combat."""
        self.session.progression.unlock_dimension(dimension_id)
        self.overlays.notify(f"★ {dimension_id.upper()} UNLOCKED! ★", duration=4.0, color=(150, 200, 255))
        
        # Trigger unlock dialogue
        self.dialogue.start_sequence(f"unlock_{dimension_id}")
    
    def _process_events(self) -> None:
        """Process pygame events."""
        for event in pygame.event.get():
            self.handle_event(event)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle a single event in both standalone and launcher modes."""
        if self.dimensional_combat and self.dimensional_combat.in_combat:
            if self.dimensional_combat.handle_input(event):
                return True

        if self.combat and self.combat.in_combat:
            if self.combat.handle_input(event):
                return True

        if self.dialogue.handle_input(event):
            return True

        if self.overlays.handle_event(event):
            return True

        if event.type == pygame.QUIT:
            self.running = False
            return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.dialogue.is_active:
                    self.dialogue.stop()
                elif self._mouse_captured:
                    self._set_mouse_capture(False)
                else:
                    self.running = False
                return True
            if event.key == pygame.K_p:
                if not self.dialogue.is_active:
                    self.paused = not self.paused
                return True
            if event.key == pygame.K_r:
                if not self.dialogue.is_active:
                    self._reload_dimension()
                return True
            if event.key == pygame.K_TAB:
                dim = self.session.active_dimension.id
                if dim in ("3d", "4d") and not self.dialogue.is_active:
                    self._set_mouse_capture(not self._mouse_captured)
                return True
            if event.key == pygame.K_v:
                if self.session.active_dimension.id == "4d":
                    self._try_evolve()
                return True
            if event.key == pygame.K_w and self._can_attempt_impossible_line_motion():
                self._attempt_impossible_line_motion(-1.0)
                return True
            if event.key == pygame.K_s and self._can_attempt_impossible_line_motion():
                self._attempt_impossible_line_motion(1.0)
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            dim = self.session.active_dimension.id
            if dim in ("3d", "4d") and not self._mouse_captured and not self.dialogue.is_active:
                self._set_mouse_capture(True)

        if self._line_guardian_active:
            return True

        if self._is_line_birth_active() and not self.dialogue.is_active:
            if self._handle_line_birth_input(event):
                return True

        self.input_handler.process_event(event)
        return False

    def end_frame(self) -> None:
        """Clear per-frame input state."""
        self.input_handler.end_frame()
    
    def _try_evolve(self) -> None:
        """Attempt to evolve to the next polytope form."""
        if not self._evolution_state.can_evolve():
            self.overlays.notify("Not enough XP to evolve", color=(200, 100, 100))
            return
        
        new_form = self._evolution_state.evolve()
        if new_form:
            self.audio.play("ability")
            self.overlays.notify(
                f"★ EVOLVED to {new_form.short_name}! ★",
                duration=5.0,
                color=(255, 220, 100)
            )
            
            # Show evolution dialogue
            if not hasattr(self, '_evolution_dialogue_shown'):
                self._evolution_dialogue_shown = True
                self.dialogue.start_sequence("evolution_unlocked")
    
    def _render(self) -> None:
        """Render the current frame."""
        # Check if NEW dimensional combat is active - render it instead of world
        if self.dimensional_combat and (self.dimensional_combat.in_combat or self.dimensional_combat.transitioning):
            self.dimensional_combat.draw()
            # Draw overlays on top of combat
            self.overlays.draw()
            return
        
        # Check if OLD combat is active or transitioning - render combat instead of world
        if self.combat and (self.combat.in_combat or self.combat.transitioning):
            self.combat.draw()
            # Draw overlays on top of combat
            self.overlays.draw()
            return

        dim_id = self.session.active_dimension.id
        if self._line_guardian_active and dim_id == "1d":
            self._draw_line_guardian_judgment()
            self.dialogue.draw()
            return
        if self._is_line_birth_active() and dim_id == "1d":
            self._draw_line_birth_ritual()
            self.dialogue.draw()
            return

        renderer = self._renderers.get(dim_id)
        
        # Pass delta time to LineRenderer for particle updates
        if dim_id == "1d" and hasattr(renderer, 'set_delta_time'):
            renderer.set_delta_time(self.clock.get_time() / 1000.0)
        if dim_id == "1d" and hasattr(renderer, 'set_dimensional_strain'):
            renderer.set_dimensional_strain(
                self._line_strain_bend if not self._line_guardian_active else max(self._line_strain_bend, 0.75),
                self._line_strain_axis if not self._line_guardian_active else (self._line_strain_axis or 1.0),
                max(self._line_strain_flash, self._line_guardian_flash),
                self._line_strain_shake + (0.4 if self._line_guardian_active else 0.0),
            )
        
        # Update camera orientation for 3D/4D renderers from controllers
        if dim_id == "3d" and hasattr(renderer, 'set_camera_orientation'):
            renderer.set_camera_orientation(
                self._volume_controller.yaw,
                self._volume_controller.pitch
            )
        elif dim_id == "4d" and hasattr(renderer, 'set_camera_orientation'):
            renderer.set_camera_orientation(
                self._hyper_controller.yaw,
                self._hyper_controller.pitch
            )
        
        if renderer:
            renderer.render(self.world, self.session.active_dimension)
        else:
            # Fallback: clear screen
            self.screen.fill((20, 20, 30))
        
        # Draw overlays (notifications, etc.)
        self.overlays.draw()
        
        # Draw dialogue (on top of everything except pause)
        self.dialogue.draw()
        
        # Draw pause overlay
        if self.paused:
            self._draw_pause_overlay()
        
        # Draw session info
        self._draw_session_info()
    
    def _draw_pause_overlay(self) -> None:
        """Draw pause screen overlay."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 72)
        text = font.render("PAUSED", True, (255, 255, 255))
        rect = text.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(text, rect)
        
        small_font = pygame.font.Font(None, 32)
        hint = small_font.render("Press P to resume, ESC to quit", True, (180, 180, 180))
        hint_rect = hint.get_rect(center=(self.width // 2, self.height // 2 + 50))
        self.screen.blit(hint, hint_rect)
    
    def _draw_session_info(self) -> None:
        """Draw session/progression info."""
        if self._is_line_birth_active() or self._line_guardian_active:
            return

        font = pygame.font.Font(None, 20)
        dim_id = self.session.active_dimension.id
        left_y = 36

        if self._current_world_def:
            world_text = font.render(f"World: {self._current_world_def.name}", True, (140, 170, 210))
            self.screen.blit(world_text, (10, left_y))
            left_y += 18

        if self._world_objectives:
            for state in self._world_objectives[:3]:
                label = state.spec.description or state.spec.id.replace("_", " ").title()
                if state.spec.target > 1:
                    current = int(state.progress) if state.progress.is_integer() else round(state.progress, 1)
                    target = int(state.spec.target) if float(state.spec.target).is_integer() else round(state.spec.target, 1)
                    label = f"{label} ({current}/{target})"
                prefix = "[x]" if state.completed else "[ ]"
                color = (120, 220, 170) if state.completed else (190, 190, 210)
                objective_text = font.render(f"{prefix} {label}", True, color)
                self.screen.blit(objective_text, (10, left_y))
                left_y += 18
        
        # XP
        xp_text = font.render(f"XP: {self.session.progression.xp}", True, (180, 180, 100))
        self.screen.blit(xp_text, (self.width - 80, 10))
        
        # Evolution XP in 4D
        if dim_id == "4d":
            evo_xp = self._evolution_state.evolution_xp
            form_name = self._evolution_state.current_form_def.short_name
            evo_text = font.render(f"Form: {form_name} | Evo XP: {evo_xp}", True, (200, 150, 255))
            self.screen.blit(evo_text, (self.width - 200, 30))
            
            if self._evolution_state.can_evolve():
                evolve_hint = font.render("Press V to EVOLVE!", True, (255, 220, 100))
                self.screen.blit(evolve_hint, (self.width - 150, 50))
        
        # Active mission
        elif self.session.progression.active_node_id and not self._world_objectives:
            mission_text = font.render(
                f"Mission: {self.session.progression.active_node_id}",
                True, (150, 150, 200)
            )
            self.screen.blit(mission_text, (self.width - 200, 30))
        
        # Controls hint (dimension-specific)
        if dim_id in ("3d", "4d"):
            if dim_id == "4d":
                controls = "WASD: Move | Mouse: Look | Q/E: W-axis | V: Evolve | SPACE/ENTER: Dialogue"
            else:
                controls = "WASD: Move | Mouse: Look | Space/Ctrl: Up/Down | SPACE/ENTER: Dialogue"
        elif dim_id == "1d":
            controls = "A/D: Move | W/S: Strain the Line | SHIFT: Phase | E: Interact"
        else:
            controls = "WASD/Arrows: Move | E: Interact | SPACE/ENTER: Dialogue"
        
        controls_text = font.render(controls, True, (100, 100, 120))
        self.screen.blit(controls_text, (10, self.height - 20))


def run_game(session: Optional["GameSession"] = None) -> None:
    """Convenience function to run the game."""
    from hypersim.game import GameSession, DimensionTrack, DEFAULT_DIMENSIONS
    from hypersim.game.save import load_progression
    
    if session is None:
        track = DimensionTrack(DEFAULT_DIMENSIONS)
        progression = load_progression()
        session = GameSession(dimensions=track, progression=progression)
    
    game = GameLoop(session, title="HyperSim - Cross-Dimensional Adventure")
    game.run()
