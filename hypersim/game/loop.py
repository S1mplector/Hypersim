"""Main game loop integrating ECS, rendering, and session management."""
from __future__ import annotations

import math
from typing import Dict, List, Optional, TYPE_CHECKING

import pygame
import numpy as np

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

# Cinematic system for Chapter 1 First Point intro
from hypersim.game.story.cinematics import FirstPointCinematic

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
        
        # === CINEMATIC SYSTEM ===
        self.first_point_cinematic = FirstPointCinematic(self.screen)
        self._chapter_1_cinematic_played = False
        self._line_world_beats_seen: set[str] = set()
        self._line_trial_state: str = "inactive"  # inactive -> to_midpoint -> return_origin -> complete
        self._line_birth_state: str = "inactive"  # inactive -> cohere -> direction -> complete
        self._line_birth_hold_active = False
        self._line_birth_charge = 0.0
        self._line_birth_time = 0.0
        self._line_birth_flash = 0.0
        self._line_birth_intro_shown = False
        self._line_birth_music_active = False
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

        if dim_id == "1d" and self._is_line_birth_active() and not self._line_birth_intro_shown and not self.first_point_cinematic.is_active:
            self._start_line_birth_ritual()

        # 1D-specific onboarding
        if dim_id != "1d" and self._line_trial_state != "complete":
            # Trial only runs in 1D; cancel if player leaves early.
            self._line_trial_state = "inactive"
        if dim_id != "1d":
            self._line_birth_state = "inactive"
            self._line_birth_hold_active = False
            self._line_birth_intro_shown = False
            self._line_strain_axis = 0.0
            self._line_strain_bend = 0.0
            self._line_strain_flash = 0.0
            self._line_strain_shake = 0.0
            self._line_violation_meter = 0.0
            self._line_guardian_active = False
            self._line_guardian_reset_pending = False
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
    
    def _trigger_dimension_intro(self, dim_id: str) -> None:
        """Trigger intro dialogue for a dimension (first time only)."""
        if dim_id in self._dimension_intros_shown:
            return
        
        self._dimension_intros_shown.add(dim_id)
        self.session.progression.shown_dimension_vignettes.add(dim_id)
        
        # Special cinematic for Chapter 1 (1D) - First Point introduction
        if dim_id == "1d" and not self._chapter_1_cinematic_played:
            if self.current_world_id == "tutorial_1d" and self.session.progression.lineage_ritual_state != "complete":
                self._start_line_birth_ritual()
            else:
                self._start_first_point_cinematic()
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
        if self.session.progression.shift_tutorial_done or self.dialogue.is_active or self.first_point_cinematic.is_active:
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
        if self.session.progression.terminus_seen or self.dialogue.is_active or self.first_point_cinematic.is_active:
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
        return self._line_birth_state in {"cohere", "direction"}

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
            return

        ritual_state = (self.session.progression.lineage_ritual_state or "complete").lower()
        if ritual_state not in {"cohere", "direction", "complete"}:
            ritual_state = "complete"

        self._line_birth_state = ritual_state
        self._line_birth_hold_active = False
        self._line_birth_charge = 1.0 if ritual_state != "cohere" else 0.0
        self._line_birth_time = 0.0
        self._line_birth_flash = 0.0
        self._line_birth_intro_shown = False

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

        if self._line_birth_state == "cohere":
            lines = [
                {"speaker": "The Voice", "text": "Not yet."},
                {"speaker": "The Voice", "text": "The Line does not receive a thing that has not agreed to exist."},
                {"speaker": "System", "text": "Hold SPACE or ENTER to gather yourself into a point."},
            ]
            self._play_sequence_inline("line_birth_cohere", lines, pause=True)
        elif self._line_birth_state == "direction":
            lines = [
                {"speaker": "The Voice", "text": "Good. You can be found now."},
                {"speaker": "The Voice", "text": "One choice remains: decide which side of nothing will become ahead."},
                {"speaker": "System", "text": "Press A/LEFT for backward or D/RIGHT for forward."},
            ]
            self._play_sequence_inline("line_birth_direction", lines, pause=True)

    def _advance_line_birth_to_direction(self) -> None:
        """Promote the ritual from bare existence to choosing a first direction."""
        self._line_birth_state = "direction"
        self._line_birth_hold_active = False
        self._line_birth_charge = 1.0
        self._line_birth_flash = 1.0
        self._line_birth_time = 0.0
        self.session.progression.lineage_ritual_state = "direction"
        self.overlays.notify("Existence gained.", duration=2.4, color=(165, 220, 255))
        self._start_line_birth_ritual()

    def _complete_line_birth_ritual(self, direction: str) -> None:
        """Finish the rite and hand off into the First Point cinematic."""
        if direction not in {"forward", "backward"}:
            return

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
        self._set_player_control_enabled(True)

        label = "Forward" if direction == "forward" else "Backward"
        color = (225, 190, 120) if direction == "forward" else (170, 185, 245)
        self.overlays.notify(f"Direction claimed: {label}", duration=2.8, color=color)

        if not self._chapter_1_cinematic_played:
            self._start_first_point_cinematic()

    def _handle_line_birth_input(self, event: pygame.event.Event) -> bool:
        """Consume input for the line-birth ritual."""
        if not self._is_line_birth_active():
            return False

        if self._line_birth_state == "cohere":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self._line_birth_hold_active = True
                return True
            if event.type == pygame.KEYUP and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self._line_birth_hold_active = False
                return True

        if self._line_birth_state == "direction" and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_a, pygame.K_LEFT):
                self._complete_line_birth_ritual("backward")
                return True
            if event.key in (pygame.K_d, pygame.K_RIGHT):
                self._complete_line_birth_ritual("forward")
                return True

        return False

    def _update_line_birth_ritual(self, dt: float) -> None:
        """Advance ritual animation and existence-gain progress."""
        if not self._is_line_birth_active():
            return

        self._line_birth_time += dt
        self._line_birth_flash = max(0.0, self._line_birth_flash - dt * 1.5)

        if self.dialogue.is_active:
            return

        if self._line_birth_state == "cohere":
            if self._line_birth_hold_active:
                self._line_birth_charge = min(1.0, self._line_birth_charge + dt * 0.72)
            else:
                self._line_birth_charge = max(0.0, self._line_birth_charge - dt * 0.22)

            if self._line_birth_charge >= 1.0:
                self._advance_line_birth_to_direction()

    def _draw_line_birth_ritual(self) -> None:
        """Render the emergence ritual overlay on top of the 1D world."""
        if self.session.active_dimension.id != "1d":
            return

        renderer = self._renderers.get("1d")
        player = self.world.find_player()
        player_x = 0.0
        if player:
            transform = player.get(Transform)
            if transform:
                player_x = float(transform.position[0])

        if renderer and hasattr(renderer, "world_to_screen"):
            player_screen_x = renderer.world_to_screen(player_x, 0.0)[0]
            line_y = getattr(renderer, "line_y", self.height // 2)
        else:
            player_screen_x = self.width // 2
            line_y = self.height // 2

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((4, 7, 18, 92))
        self.screen.blit(overlay, (0, 0))

        title_font = pygame.font.Font(None, 44)
        subtitle_font = pygame.font.Font(None, 26)
        body_font = pygame.font.Font(None, 30)
        small_font = pygame.font.Font(None, 22)

        title = title_font.render("Rite of Emergence", True, (234, 236, 244))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 110)))

        pulse = 0.5 + 0.5 * np.sin(self._line_birth_time * 2.4)
        core_color = (170, 228, 255)
        ring_color = (225, 235, 255)

        for idx in range(10):
            orbit = self._line_birth_time * (0.7 + idx * 0.08) + idx * 0.63
            distance = 28 + idx * 7 - self._line_birth_charge * 14
            mote_x = player_screen_x + np.cos(orbit) * distance
            mote_y = line_y + np.sin(orbit) * (22 + idx * 3)
            radius = 2 + (idx % 3)
            fade = 0.78 - idx * 0.05
            pygame.draw.circle(
                self.screen,
                tuple(int(channel * fade) for channel in core_color),
                (int(mote_x), int(mote_y)),
                radius,
            )

        base_radius = 24 + 8 * self._line_birth_charge + 3 * pulse
        pygame.draw.circle(self.screen, (185, 225, 255), (int(player_screen_x), int(line_y)), int(base_radius))
        pygame.draw.circle(self.screen, (245, 250, 255), (int(player_screen_x), int(line_y)), 8)

        if self._line_birth_state == "cohere":
            ring_rect = pygame.Rect(0, 0, 132, 132)
            ring_rect.center = (player_screen_x, line_y)
            pygame.draw.circle(self.screen, (42, 54, 90), (int(player_screen_x), int(line_y)), 66, 2)
            pygame.draw.arc(
                self.screen,
                ring_color,
                ring_rect,
                -np.pi / 2,
                -np.pi / 2 + 2 * np.pi * self._line_birth_charge,
                5,
            )

            heading = subtitle_font.render("Gain Existence", True, (210, 220, 238))
            body = body_font.render("Hold SPACE or ENTER until absence loses you.", True, (236, 238, 245))
            meter_width = 280
            meter_rect = pygame.Rect(0, 0, meter_width, 10)
            meter_rect.center = (self.width // 2, line_y + 150)
            pygame.draw.rect(self.screen, (28, 34, 52), meter_rect, border_radius=5)
            fill_rect = meter_rect.copy()
            fill_rect.width = int(meter_width * self._line_birth_charge)
            pygame.draw.rect(self.screen, (172, 220, 255), fill_rect, border_radius=5)
            hint = small_font.render("Steady pressure makes you real.", True, (150, 165, 192))

            self.screen.blit(heading, heading.get_rect(center=(self.width // 2, line_y - 118)))
            self.screen.blit(body, body.get_rect(center=(self.width // 2, line_y + 118)))
            self.screen.blit(hint, hint.get_rect(center=(self.width // 2, line_y + 178)))
        elif self._line_birth_state == "direction":
            left_color = (150, 170, 245)
            right_color = (232, 196, 132)
            reach = 180 + 18 * pulse
            pygame.draw.line(
                self.screen,
                left_color,
                (int(player_screen_x - 22), int(line_y)),
                (int(player_screen_x - reach), int(line_y)),
                4,
            )
            pygame.draw.line(
                self.screen,
                right_color,
                (int(player_screen_x + 22), int(line_y)),
                (int(player_screen_x + reach), int(line_y)),
                4,
            )
            pygame.draw.polygon(
                self.screen,
                left_color,
                [
                    (int(player_screen_x - reach), int(line_y)),
                    (int(player_screen_x - reach + 22), int(line_y - 12)),
                    (int(player_screen_x - reach + 22), int(line_y + 12)),
                ],
            )
            pygame.draw.polygon(
                self.screen,
                right_color,
                [
                    (int(player_screen_x + reach), int(line_y)),
                    (int(player_screen_x + reach - 22), int(line_y - 12)),
                    (int(player_screen_x + reach - 22), int(line_y + 12)),
                ],
            )

            heading = subtitle_font.render("Choose The First Direction", True, (210, 220, 238))
            body = body_font.render("Press A/LEFT or D/RIGHT. Preference becomes geometry.", True, (236, 238, 245))
            left_label = small_font.render("Backward", True, left_color)
            right_label = small_font.render("Forward", True, right_color)
            hint = small_font.render("The Line remembers your first answer.", True, (150, 165, 192))

            self.screen.blit(heading, heading.get_rect(center=(self.width // 2, line_y - 118)))
            self.screen.blit(body, body.get_rect(center=(self.width // 2, line_y + 118)))
            self.screen.blit(left_label, left_label.get_rect(center=(player_screen_x - 180, line_y + 34)))
            self.screen.blit(right_label, right_label.get_rect(center=(player_screen_x + 180, line_y + 34)))
            self.screen.blit(hint, hint.get_rect(center=(self.width // 2, line_y + 176)))

        if self._line_birth_flash > 0.0:
            flash = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            flash.fill((215, 232, 255, int(86 * self._line_birth_flash)))
            self.screen.blit(flash, (0, 0))

    def _can_attempt_impossible_line_motion(self) -> bool:
        """Return whether the player can currently strain against the Line."""
        if self.session.active_dimension.id != "1d":
            return False
        if self.paused or self.dialogue.is_active or self.first_point_cinematic.is_active:
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

    def _trigger_line_guardian_intervention(self) -> None:
        """Summon a higher-dimensional guardian to reset reckless line-breaking."""
        if self._line_guardian_active:
            return

        from hypersim.game.ui.textbox import DialogueLine, DialogueSequence, TextBoxStyle

        self._line_guardian_active = True
        self._line_guardian_time = 0.0
        self._line_guardian_rotation = 0.0
        self._line_guardian_flash = 1.0
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
                text="So I will unmake you gently, until you remember that existence comes before ambition.",
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

    def _complete_line_guardian_intervention(self) -> None:
        """Strip the player back to pre-existence and restart the birth rite."""
        self._line_guardian_reset_pending = False
        self._line_guardian_active = False
        self._line_guardian_time = 0.0
        self._line_guardian_rotation = 0.0
        self._line_guardian_flash = 1.0
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

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((6, 7, 18, 150))
        self.screen.blit(overlay, (0, 0))

        center = (self.width // 2, self.height // 2 - 30)
        scale = 86.0 + 14.0 * math.sin(self._line_guardian_time * 1.7)
        vertices, edges = self._guardian_tesseract_geometry()
        projected = [self._project_guardian_vertex(self._rotate_guardian_vertex(v), center, scale) for v in vertices]

        glow = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for i, j in edges:
            p1, p2 = projected[i], projected[j]
            pygame.draw.line(glow, (235, 190, 120, 26), (p1[0], p1[1]), (p2[0], p2[1]), 6)
        self.screen.blit(glow, (0, 0))

        for i, j in edges:
            p1, p2 = projected[i], projected[j]
            depth = max(0.25, min(1.0, (p1[2] + p2[2] + 2.5) / 5.0))
            edge_color = (
                int(255 * depth),
                int(210 * depth),
                int(150 * depth),
            )
            pygame.draw.line(self.screen, edge_color, (p1[0], p1[1]), (p2[0], p2[1]), max(1, int(3 * depth)))

        for x, y, depth in projected:
            factor = max(0.35, min(1.0, (depth + 2.5) / 5.0))
            pygame.draw.circle(self.screen, (255, int(220 * factor), int(170 * factor)), (x, y), max(2, int(5 * factor)))

        renderer = self._renderers.get("1d")
        player = self.world.find_player()
        if renderer and player:
            transform = player.get(Transform)
            if transform:
                player_screen_x, player_screen_y = renderer.world_to_screen(float(transform.position[0]), 0.0)
                beam = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                pygame.draw.line(beam, (255, 220, 180, 120), center, (player_screen_x, player_screen_y), 3)
                pygame.draw.circle(beam, (255, 220, 180, 90), (player_screen_x, player_screen_y), 28)
                self.screen.blit(beam, (0, 0))

        if self._line_guardian_flash > 0.0:
            flash = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            flash.fill((255, 228, 190, int(80 * self._line_guardian_flash)))
            self.screen.blit(flash, (0, 0))
    
    def _start_first_point_cinematic(self) -> None:
        """Start the First Point cinematic for Chapter 1."""
        from hypersim.game.story.cinematics import get_first_point_dialogue
        from hypersim.game.ui.textbox import DialogueLine, DialogueSequence, TextBoxStyle

        def on_cinematic_complete():
            # Spawn the First Point as an interactable NPC after cinematic
            self._spawn_first_point_npc()

        self._chapter_1_cinematic_played = True
        intro_lines = []
        for item in get_first_point_dialogue(
            self.session.progression.intro_impulse or "",
            self.session.progression.lineage_direction or "",
        ):
            speaker = item.get("speaker", "")
            if speaker == "System":
                style = TextBoxStyle.TUTORIAL
                voice_id = item.get("voice_id") or "default"
                typing_speed = item.get("typing_speed", 30.0)
            elif speaker == "The First Point":
                style = TextBoxStyle.DIMENSION
                voice_id = item.get("voice_id") or "first_point"
                typing_speed = item.get("typing_speed", 24.0)
            else:
                style = TextBoxStyle.NARRATOR
                voice_id = item.get("voice_id") or "narrator"
                typing_speed = item.get("typing_speed", 28.0)

            intro_lines.append(
                DialogueLine(
                    speaker=speaker,
                    text=item.get("text", ""),
                    style=style,
                    voice_id=voice_id,
                    duration=item.get("duration", 1.2 if item.get("text") == "..." else 0.0),
                    typing_speed=typing_speed,
                    choices=item.get("choices", []),
                )
            )

        self.dialogue.register_sequence(
            DialogueSequence(
                id="chapter_1_first_point_intro",
                lines=intro_lines,
                pause_game=True,
                can_skip=False,
            )
        )
        self.first_point_cinematic.on_cinematic_complete = on_cinematic_complete
        self.first_point_cinematic.start(self.dialogue)
    
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
        cinematic_active = self.first_point_cinematic.is_active
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

        if cinematic_active:
            self.first_point_cinematic.update(dt)

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

        if self._line_guardian_reset_pending and not self.dialogue.is_active:
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
        # Check if First Point cinematic is active - render it on top of world
        if self.first_point_cinematic.is_active:
            # Render world underneath
            dim_id = self.session.active_dimension.id
            renderer = self._renderers.get(dim_id)
            if renderer:
                renderer.render(self.world, self.session.active_dimension)
            else:
                self.screen.fill((5, 5, 15))
            
            # Render cinematic overlay
            self.first_point_cinematic.draw()
            
            # Draw dialogue on top of cinematic
            self.dialogue.draw()
            return
        
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

        if self._line_guardian_active and dim_id == "1d":
            self._draw_line_guardian_judgment()
        if self._is_line_birth_active() and dim_id == "1d":
            self._draw_line_birth_ritual()
        
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
