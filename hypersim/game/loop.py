"""Main game loop integrating ECS, rendering, and session management."""
from __future__ import annotations

from typing import Dict, Optional, TYPE_CHECKING

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

# New integrated systems
from hypersim.game.ui.textbox import DialogueSystem, DialogueLine, TextBoxStyle, create_campaign_dialogues
from hypersim.game.ui.overlay import OverlayManager
from hypersim.game.audio import AudioSystem, GameAudioHandler, get_audio_system
from hypersim.game.evolution import EvolutionState, PolytopeForm, get_evolution_system
from hypersim.game.story.campaign import Campaign
from hypersim.game.story.npc import NPCManager
from hypersim.game.story.lore import Codex

# Combat system
from hypersim.game.combat import (
    CombatIntegration, CombatResult, CombatStats,
    create_combat_integration, get_realms_for_dimension,
    get_starting_realm, EncounterConfig, EncounterType
)

# Story/Narrative system
from hypersim.game.story.narrative import StoryManager, StoryRoute, StoryChapter, ENDINGS

if TYPE_CHECKING:
    from hypersim.game.session import GameSession


class GameLoop:
    """Main game loop that orchestrates all systems."""
    
    def __init__(
        self,
        session: "GameSession",
        width: int = 1024,
        height: int = 768,
        title: str = "HyperSim"
    ):
        self.session = session
        self.width = width
        self.height = height
        self.title = title
        
        # Initialize pygame
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        
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
        self._dimension_intros_shown: set = set()
        
        # === COMBAT SYSTEM ===
        self.combat: Optional[CombatIntegration] = None
        self._current_realm_id: Optional[str] = None
        self._steps_in_realm: int = 0
        
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
            
            # Player colliding with enemy
            if entity_a.has_tag("player") and entity_b.has_tag("enemy"):
                self.damage_system.queue_damage(entity_a.id, 10.0)
            elif entity_b.has_tag("player") and entity_a.has_tag("enemy"):
                self.damage_system.queue_damage(entity_b.id, 10.0)
            
            # Player colliding with pickup
            if entity_a.has_tag("player") and entity_b.get(Pickup):
                self._collect_pickup(entity_a, entity_b)
            elif entity_b.has_tag("player") and entity_a.get(Pickup):
                self._collect_pickup(entity_b, entity_a)
        
        def on_interact(event):
            player = self.world.get(event.source_entity_id)
            if not player:
                return
            
            player_transform = player.get(Transform)
            if not player_transform:
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
                    self._use_portal(portal)
                    break
        
        self.world.on_event("collision", on_collision)
        self.world.on_event("player_interact", on_interact)
    
    def _collect_pickup(self, player: Entity, pickup_entity: Entity) -> None:
        """Handle player collecting a pickup."""
        pickup = pickup_entity.get(Pickup)
        if pickup.collected:
            return
        
        pickup.collected = True
        pickup_entity.active = False
        
        self.session.record_event("collect", item=pickup.item_type, count=pickup.value)
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
        if portal.target_dimension:
            # Dimension transition
            self.session.set_dimension(portal.target_dimension)
            self._reload_dimension()
    
    def _reload_dimension(self) -> None:
        """Reload the world for the current dimension."""
        # Clear existing entities
        self.world.clear()
        
        # Spawn player and entities for new dimension
        dim_id = self.session.active_dimension.id
        self._spawn_default_level(dim_id)
        
        # Update input system
        self.input_system.set_dimension(dim_id)
        
        # Trigger dimension intro dialogue (first time only)
        self._trigger_dimension_intro(dim_id)
        
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
        
        # Map dimensions to dialogue sequences
        intro_map = {
            "1d": "intro_1d",
            "2d": "intro_2d",
            "3d": "intro_3d",
            "4d": "intro_4d",
        }
        
        seq_id = intro_map.get(dim_id)
        if seq_id:
            self.dialogue.start_sequence(seq_id)
    
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
        player.add(Health(current=100, max=100))
        player.add(Controller(controller_type=controller_type, speed=8.0))
        player.add(DimensionAnchor(dimension_id=dimension_id))
        player.tag("player", "controllable")
        
        self.world.spawn(player)
        return player
    
    def _spawn_1d_level(self) -> None:
        """Spawn a basic 1D tutorial level."""
        # Set world bounds
        self.physics_system.set_bounds("1d", 0, -45.0, 45.0)
        
        # Spawn player at origin
        self._spawn_player("1d", np.array([0.0, 0.0, 0.0, 0.0]))
        
        # Spawn some enemies
        enemy_positions = [-15.0, 10.0, 25.0]
        for i, x in enumerate(enemy_positions):
            enemy = Entity(id=f"enemy_{i}")
            enemy.add(Transform(position=np.array([x, 0.0, 0.0, 0.0])))
            enemy.add(Velocity())
            enemy.add(Renderable(color=(200, 50, 50)))
            enemy.add(Collider(shape=ColliderShape.SEGMENT, size=np.array([0.8])))
            enemy.add(Health(current=30, max=30))
            enemy.add(AIBrain(
                behavior="oscillate",
                state={"center": x, "amplitude": 3.0, "speed": 2.0, "direction": 1}
            ))
            enemy.add(DimensionAnchor(dimension_id="1d"))
            enemy.tag("enemy")
            self.world.spawn(enemy)
        
        # Spawn pickups
        pickup_positions = [-8.0, 5.0, 18.0]
        for i, x in enumerate(pickup_positions):
            pickup = Entity(id=f"pickup_{i}")
            pickup.add(Transform(position=np.array([x, 0.0, 0.0, 0.0])))
            pickup.add(Renderable(color=(255, 220, 50)))
            pickup.add(Collider(shape=ColliderShape.SEGMENT, size=np.array([0.3]), is_trigger=True))
            pickup.add(Pickup(item_type="energy", value=1))
            pickup.add(DimensionAnchor(dimension_id="1d"))
            pickup.tag("pickup")
            self.world.spawn(pickup)
        
        # Spawn portal to 2D at the end
        portal = Entity(id="portal_2d")
        portal.add(Transform(position=np.array([40.0, 0.0, 0.0, 0.0])))
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
    
    def run(self) -> None:
        """Run the main game loop."""
        self.running = True
        
        # Initialize combat system
        self.combat = create_combat_integration(self.screen, self.session)
        self.combat.on_combat_end = self._on_combat_end
        self.combat.on_boss_defeated = self._on_boss_defeated
        
        # Initialize first dimension
        self._reload_dimension()
        
        while self.running:
            dt = self.clock.tick(self.target_fps) / 1000.0
            
            # Process events
            self._process_events()
            
            # Check if dialogue, combat, or overlay should pause game
            dialogue_active = self.dialogue.should_pause_game
            combat_active = self.combat and self.combat.in_combat
            
            if combat_active:
                # Update combat system
                self.combat.update(dt)
            elif not self.paused and not dialogue_active:
                # Update systems
                self.world.update(dt)
                
                # Process game events for session/objectives
                for event in self.world.drain_events():
                    self.session.record_event(event.event_type, **event.data)
                
                # Check for random encounters
                self._check_random_encounter()
            
            # Update dialogue and overlays (always)
            self.dialogue.update(dt)
            self.overlays.update(dt)
            
            # Render
            self._render()
            
            # End frame
            self.input_handler.end_frame()
            pygame.display.flip()
        
        # Save progression on exit
        from hypersim.game.save import save_progression
        save_progression(self.session.progression)
        
        pygame.quit()
    
    def _check_random_encounter(self) -> None:
        """Check for random combat encounters based on player movement."""
        if not self.combat or self.combat.in_combat:
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
        if not self.combat:
            return
        
        # Release mouse capture for combat
        if self._mouse_captured:
            self._set_mouse_capture(False)
        
        # Start encounter
        if self.combat.start_random_encounter(enemy_id):
            self.audio.play("encounter")
            self.overlays.notify("⚔️ ENCOUNTER!", duration=1.5, color=(255, 100, 100))
    
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
        
        # Check current route and notify player of major shifts
        route = self.story.get_current_route()
        self._check_route_notification(route)
        
        # Re-capture mouse if in 3D/4D
        dim_id = self.session.active_dimension.id
        if dim_id in ("3d", "4d"):
            self._set_mouse_capture(True)
    
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
    
    def _process_events(self) -> None:
        """Process pygame events."""
        for event in pygame.event.get():
            # Let combat system handle input first if active
            if self.combat and self.combat.in_combat:
                if self.combat.handle_input(event):
                    continue
            
            # Let dialogue system handle input
            if self.dialogue.handle_input(event):
                continue
            
            # Let overlay manager handle input
            if self.overlays.handle_event(event):
                continue
            
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.dialogue.is_active:
                        # Close dialogue first
                        self.dialogue.stop()
                    elif self._mouse_captured:
                        # Release mouse first
                        self._set_mouse_capture(False)
                    else:
                        self.running = False
                elif event.key == pygame.K_p:
                    if not self.dialogue.is_active:
                        self.paused = not self.paused
                elif event.key == pygame.K_r:
                    # Reload level
                    if not self.dialogue.is_active:
                        self._reload_dimension()
                elif event.key == pygame.K_TAB:
                    # Toggle mouse capture in 3D/4D
                    dim = self.session.active_dimension.id
                    if dim in ("3d", "4d") and not self.dialogue.is_active:
                        self._set_mouse_capture(not self._mouse_captured)
                elif event.key == pygame.K_v:
                    # Try to evolve (in 4D)
                    if self.session.active_dimension.id == "4d":
                        self._try_evolve()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Click to capture mouse in 3D/4D
                dim = self.session.active_dimension.id
                if dim in ("3d", "4d") and not self._mouse_captured and not self.dialogue.is_active:
                    self._set_mouse_capture(True)
            
            # Forward to input handler
            self.input_handler.process_event(event)
        
        # Process mouse look for 3D/4D controllers
        if self._mouse_captured and not self.paused and not self.dialogue.is_active:
            self._volume_controller.process_mouse(self.input_handler)
            self._hyper_controller.process_mouse(self.input_handler)
    
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
        # Check if combat is active - render combat instead of world
        if self.combat and self.combat.in_combat:
            self.combat.draw()
            # Draw overlays on top of combat
            self.overlays.draw()
            return
        
        dim_id = self.session.active_dimension.id
        renderer = self._renderers.get(dim_id)
        
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
        font = pygame.font.Font(None, 20)
        dim_id = self.session.active_dimension.id
        
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
        elif self.session.progression.active_node_id:
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
