"""Run HyperSim game with: python -m hypersim.game"""
import pygame

from hypersim.game.ui.fancy_menu import run_tessera_menu


def main():
    """Main entry point for the game."""
    selected_mode = run_tessera_menu()
    
    if selected_mode:
        # Start the actual game
        start_game(selected_mode)


def start_game(mode: str):
    """Start the game with the selected mode."""
    # Re-initialize pygame (it was quit by menu)
    pygame.init()
    pygame.mixer.init()
    
    # Import game components
    from hypersim.game.session import GameSession
    from hypersim.game.dimensions import DimensionTrack, DEFAULT_DIMENSIONS
    from hypersim.game.progression import ProgressionState
    from hypersim.game.save import load_progression, save_progression
    from hypersim.game.loop import GameLoop
    
    # Set up dimension track
    track = DimensionTrack(DEFAULT_DIMENSIONS)
    
    # Handle mode
    if mode == "new_game":
        # Fresh start
        progression = ProgressionState()
        print("Starting new game...")
    elif mode == "load_save":
        # Load saved progress
        progression = load_progression()
        if progression is None:
            print("No save found, starting new game...")
            progression = ProgressionState()
        else:
            print("Loaded saved game!")
    else:
        progression = ProgressionState()
    
    # Create session and start game loop
    session = GameSession(dimensions=track, progression=progression)
    
    game = GameLoop(
        session, 
        width=1280, 
        height=720,
        title="HyperSim - Cross-Dimensional Adventure"
    )
    game.run()


if __name__ == "__main__":
    main()
