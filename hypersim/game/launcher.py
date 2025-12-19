"""Tessera Game Launcher - Wires everything together."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional
from enum import Enum, auto

import pygame

from hypersim.game.ui.splash_screen import create_tessera_splash_sequence
from hypersim.game.ui.fancy_menu import FancyMainMenu, MenuState
from hypersim.game.ui.save_load_menu import SaveLoadMenu, SaveLoadMode
from hypersim.game.ui.pause_menu import PauseMenu
from hypersim.game.save_system import SaveManager, GameSaveData, get_save_manager
from hypersim.game.loop import GameLoop
from hypersim.game.session import GameSession
from hypersim.game.progression import ProgressionState


class LauncherState(Enum):
    """States of the game launcher."""
    SPLASH = auto()
    MAIN_MENU = auto()
    SAVE_LOAD = auto()
    LOADING = auto()
    IN_GAME = auto()
    PAUSED = auto()


class TesseraLauncher:
    """Main game launcher that manages all game states."""
    
    def __init__(self, width: int = 1280, height: int = 720, fullscreen: bool = False):
        pygame.init()
        pygame.mixer.init()
        
        # Display setup
        self.width = width
        self.height = height
        flags = pygame.FULLSCREEN if fullscreen else 0
        self.screen = pygame.display.set_mode((width, height), flags)
        pygame.display.set_caption("Tessera")
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = LauncherState.SPLASH
        
        # Systems
        self.save_manager = get_save_manager()
        
        # UI Components
        self.splash = create_tessera_splash_sequence(self.screen)
        self.main_menu = FancyMainMenu(self.screen)
        self.save_load_menu = SaveLoadMenu(self.screen)
        self.pause_menu = PauseMenu(self.screen)
        
        # Game
        self.game_loop: Optional[GameLoop] = None
        self.current_save: Optional[GameSaveData] = None
        
        # Wire up callbacks
        self._setup_callbacks()
    
    def _setup_callbacks(self) -> None:
        """Setup all UI callbacks."""
        # Main menu
        self.main_menu.on_start_game = self._on_menu_action
        self.main_menu.on_quit = self._quit
        
        # Save/Load menu
        self.save_load_menu.on_load = self._on_load_save
        self.save_load_menu.on_save = self._on_save_complete
        self.save_load_menu.on_close = self._on_save_load_close
        
        # Pause menu
        self.pause_menu.on_resume = self._on_pause_resume
        self.pause_menu.on_save = self._on_pause_save
        self.pause_menu.on_load = self._on_pause_load
        self.pause_menu.on_settings = self._on_pause_settings
        self.pause_menu.on_main_menu = self._return_to_menu
        self.pause_menu.on_quit = self._quit
    
    def _on_menu_action(self, action: str) -> None:
        """Handle main menu action."""
        if action == "campaign":
            self._show_campaign_menu()
        elif action == "quickplay":
            self._start_quick_play()
        elif action == "multiplayer":
            self._show_multiplayer_menu()
    
    def _show_campaign_menu(self) -> None:
        """Show campaign options (new game / continue / load)."""
        # Check for existing saves
        if self.save_manager.has_any_saves():
            # Show load menu
            self.save_load_menu.show(SaveLoadMode.LOAD)
            self.state = LauncherState.SAVE_LOAD
        else:
            # Start new game directly
            self._start_new_game()
    
    def _start_new_game(self) -> None:
        """Start a new campaign game."""
        self.current_save = self.save_manager.create_new_game()
        self.current_save.metadata.save_name = "New Campaign"
        self._launch_game()
    
    def _start_quick_play(self) -> None:
        """Start quick play - jump into action."""
        # Create temporary save for quick play
        self.current_save = self.save_manager.create_new_game()
        self.current_save.player.dimension = "2d"  # Start in 2D for quick action
        self.current_save.world.unlocked_dimensions = ["1d", "2d"]
        self._launch_game()
    
    def _show_multiplayer_menu(self) -> None:
        """Show multiplayer lobby."""
        # For now, show a placeholder message
        # TODO: Implement full multiplayer UI
        print("Multiplayer coming soon!")
    
    def _on_load_save(self, save_data: GameSaveData) -> None:
        """Handle save file loaded."""
        self.current_save = save_data
        self.save_load_menu.hide()
        self._launch_game()
    
    def _on_save_complete(self, slot_id: int, name: str) -> None:
        """Handle save completed."""
        print(f"Game saved to slot {slot_id}: {name}")
    
    def _on_save_load_close(self) -> None:
        """Handle save/load menu closed."""
        if self.game_loop:
            self.state = LauncherState.PAUSED
        else:
            self.state = LauncherState.MAIN_MENU
    
    def _on_pause_resume(self) -> None:
        """Resume game from pause."""
        self.pause_menu.hide()
        self.state = LauncherState.IN_GAME
        pygame.mouse.set_visible(False)
    
    def _on_pause_save(self) -> None:
        """Open save menu from pause."""
        self._update_save_from_game()
        self.save_load_menu.show(SaveLoadMode.SAVE, self.current_save)
        self.state = LauncherState.SAVE_LOAD
    
    def _on_pause_load(self) -> None:
        """Open load menu from pause."""
        self.save_load_menu.show(SaveLoadMode.LOAD)
        self.state = LauncherState.SAVE_LOAD
    
    def _on_pause_settings(self) -> None:
        """Open settings from pause."""
        # TODO: Implement in-game settings
        pass
    
    def _update_save_from_game(self) -> None:
        """Update current save data from game state."""
        if not self.game_loop or not self.current_save:
            return
        
        player = self.game_loop.world.find_player()
        if player:
            from hypersim.game.ecs.component import Transform, Health
            transform = player.get(Transform)
            if transform:
                self.current_save.player.position = transform.position.tolist()
            
            health = player.get(Health)
            if health:
                self.current_save.player.health = health.current
                self.current_save.player.max_health = health.max
        
        self.current_save.player.dimension = self.game_loop.session.active_dimension.id
        self.current_save.player.xp = self.game_loop.session.progression.xp
        self.current_save.player.level = self.current_save.player.xp // 100 + 1
    
    def _launch_game(self) -> None:
        """Launch the game with current save data."""
        self.main_menu.stop_music()
        self.state = LauncherState.LOADING
        
        # Create progression state from save
        progression = self._save_to_progression(self.current_save)
        
        # Create game session
        session = GameSession(progression=progression)
        session.set_dimension(self.current_save.player.dimension)
        
        # Create game loop
        self.game_loop = GameLoop(
            screen=self.screen,
            session=session,
        )
        
        # Set player position from save
        self._apply_save_to_game()
        
        self.state = LauncherState.IN_GAME
    
    def _save_to_progression(self, save: GameSaveData) -> ProgressionState:
        """Convert save data to progression state."""
        return ProgressionState(
            current_dimension=save.player.dimension,
            unlocked_dimensions=save.world.unlocked_dimensions,
            completed_nodes=set(save.world.completed_missions),
            xp=save.player.xp,
            profile_name=save.metadata.save_name,
            unlocked_abilities=set(save.player.unlocked_abilities),
            evolution_form=0,  # Will be set from dimension-specific evolution
            evolution_xp=save.player.evolution_xp_4d,
            evolution_forms_unlocked=[0],  # Default
        )
    
    def _apply_save_to_game(self) -> None:
        """Apply save data to running game."""
        if not self.game_loop or not self.current_save:
            return
        
        # Set player position
        player = self.game_loop.world.find_player()
        if player:
            from hypersim.game.ecs.component import Transform, Health
            transform = player.get(Transform)
            if transform:
                transform.position[:] = self.current_save.player.position
            
            health = player.get(Health)
            if health:
                health.current = self.current_save.player.health
                health.max = self.current_save.player.max_health
    
    def _save_current_game(self) -> None:
        """Save current game state."""
        if not self.game_loop or not self.current_save:
            return
        
        # Update save from game state
        player = self.game_loop.world.find_player()
        if player:
            from hypersim.game.ecs.component import Transform, Health
            transform = player.get(Transform)
            if transform:
                self.current_save.player.position = transform.position.tolist()
            
            health = player.get(Health)
            if health:
                self.current_save.player.health = health.current
                self.current_save.player.max_health = health.max
        
        # Update dimension and progression
        self.current_save.player.dimension = self.game_loop.session.active_dimension.id
        self.current_save.player.level = self.game_loop.session.progression.xp // 100 + 1
        self.current_save.player.xp = self.game_loop.session.progression.xp
        
        # Show save menu
        self.save_load_menu.show(SaveLoadMode.SAVE, self.current_save)
        self.state = LauncherState.SAVE_LOAD
    
    def _return_to_menu(self) -> None:
        """Return to main menu from game."""
        # Auto-save before returning
        if self.current_save:
            self.save_manager.auto_save(self.current_save, force=True)
        
        self.game_loop = None
        self.state = LauncherState.MAIN_MENU
        self.main_menu.start_music()
    
    def _quit(self) -> None:
        """Quit the game."""
        # Auto-save if in game
        if self.state == LauncherState.IN_GAME and self.current_save:
            self.save_manager.auto_save(self.current_save, force=True)
        
        self.running = False
    
    def run(self) -> None:
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()
                    continue
                
                self._handle_event(event)
            
            # Update
            self._update(dt)
            
            # Render
            self._render()
            
            pygame.display.flip()
        
        pygame.quit()
    
    def _handle_event(self, event: pygame.event.Event) -> None:
        """Handle input event based on current state."""
        if self.state == LauncherState.SPLASH:
            self.splash.handle_event(event)
        
        elif self.state == LauncherState.MAIN_MENU:
            self.main_menu.handle_event(event)
        
        elif self.state == LauncherState.SAVE_LOAD:
            self.save_load_menu.handle_event(event)
        
        elif self.state == LauncherState.PAUSED:
            self.pause_menu.handle_event(event)
        
        elif self.state == LauncherState.IN_GAME:
            # Check for pause
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._update_save_from_game()
                    self.pause_menu.show()
                    self.state = LauncherState.PAUSED
                    return
                elif event.key == pygame.K_F5:
                    # Quick save
                    self._update_save_from_game()
                    if self.current_save:
                        self.save_manager.quicksave(self.current_save)
                        print("Quick saved!")
                    return
                elif event.key == pygame.K_F9:
                    # Quick load
                    loaded = self.save_manager.quickload()
                    if loaded:
                        self.current_save = loaded
                        self._launch_game()
                        print("Quick loaded!")
                    return
                elif event.key == pygame.K_F6:
                    # Open save menu
                    self._update_save_from_game()
                    self._on_pause_save()
                    return
            
            # Pass to game loop
            if self.game_loop:
                self.game_loop._input.process_event(event)
    
    def _update(self, dt: float) -> None:
        """Update based on current state."""
        if self.state == LauncherState.SPLASH:
            if self.splash.update(dt):
                self.state = LauncherState.MAIN_MENU
                self.main_menu.start_music()
        
        elif self.state == LauncherState.MAIN_MENU:
            self.main_menu.update(dt)
        
        elif self.state == LauncherState.SAVE_LOAD:
            self.save_load_menu.update(dt)
        
        elif self.state == LauncherState.PAUSED:
            self.pause_menu.update(dt)
        
        elif self.state == LauncherState.IN_GAME:
            if self.game_loop:
                # Run one frame of game loop
                self.game_loop._update(dt)
                
                # Check for auto-save
                if self.current_save:
                    self.save_manager.check_auto_save(self.current_save)
    
    def _render(self) -> None:
        """Render based on current state."""
        if self.state == LauncherState.SPLASH:
            self.splash.draw()
        
        elif self.state == LauncherState.MAIN_MENU:
            self.main_menu.draw()
        
        elif self.state == LauncherState.SAVE_LOAD:
            # Draw menu behind save/load
            self.main_menu.draw()
            self.save_load_menu.draw()
        
        elif self.state == LauncherState.LOADING:
            self.screen.fill((5, 8, 15))
            font = pygame.font.Font(None, 48)
            text = font.render("Loading...", True, (150, 180, 220))
            rect = text.get_rect(center=(self.width // 2, self.height // 2))
            self.screen.blit(text, rect)
        
        elif self.state == LauncherState.PAUSED:
            # Draw game behind pause menu
            if self.game_loop:
                self.game_loop._render()
            self.pause_menu.draw()
        
        elif self.state == LauncherState.IN_GAME:
            if self.game_loop:
                self.game_loop._render()
                
                # Draw in-game HUD hints
                self._draw_game_hud()
    
    def _draw_game_hud(self) -> None:
        """Draw additional game HUD elements."""
        font = pygame.font.Font(None, 20)
        hints = "F5: Quick Save | F6: Save Menu | F9: Quick Load | ESC: Menu"
        hint_text = font.render(hints, True, (80, 80, 100))
        self.screen.blit(hint_text, (10, 10))


def main():
    """Entry point for Tessera."""
    launcher = TesseraLauncher()
    launcher.run()


if __name__ == "__main__":
    main()
