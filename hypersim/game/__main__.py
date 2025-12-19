"""Run HyperSim game with: python -m hypersim.game

This is the main entry point for the HyperSim dimensional adventure game.
Supports both the fancy launcher and direct gameplay modes.
"""
import pygame
import sys


def main():
    """Main entry point for the game."""
    # Check for command line args
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "--quick":
            # Skip menu, start immediately
            start_campaign("new_game")
            return
        elif arg == "--combat":
            # Run combat demo
            from hypersim.game.combat import run_combat_demo
            run_combat_demo()
            return
        elif arg == "--launcher":
            # Use the full launcher
            run_launcher()
            return
    
    # Default: run the fancy menu
    from hypersim.game.ui.fancy_menu import run_tessera_menu
    selected_mode = run_tessera_menu()
    
    if selected_mode:
        start_campaign(selected_mode)


def run_launcher():
    """Run the full Tessera launcher with all features."""
    from hypersim.game.launcher import TesseraLauncher
    launcher = TesseraLauncher(width=1280, height=720)
    launcher.run()


def start_campaign(mode: str):
    """Start the campaign with proper chapter system integration."""
    pygame.init()
    pygame.mixer.init()
    
    from hypersim.game.session import GameSession
    from hypersim.game.dimensions import DimensionTrack, DEFAULT_DIMENSIONS
    from hypersim.game.progression import ProgressionState
    from hypersim.game.save import load_progression, save_progression
    from hypersim.game.loop import GameLoop
    from hypersim.game.story.chapters import get_campaign_manager, reset_campaign
    
    # Set up dimension track
    track = DimensionTrack(DEFAULT_DIMENSIONS)
    
    # Handle mode
    if mode == "new_game":
        progression = ProgressionState()
        campaign = reset_campaign()  # Fresh campaign
        print("Starting new campaign...")
    elif mode == "load_save":
        progression = load_progression()
        if progression is None:
            print("No save found, starting new campaign...")
            progression = ProgressionState()
            campaign = reset_campaign()
        else:
            print("Loaded saved game!")
            campaign = get_campaign_manager()
    else:
        progression = ProgressionState()
        campaign = reset_campaign()
    
    # Create session
    session = GameSession(dimensions=track, progression=progression)
    
    # Create game loop with screen
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("HyperSim - Cross-Dimensional Adventure")
    
    game = GameLoop(
        session=session,
        screen=screen,
    )
    
    # Wire up campaign callbacks
    def on_chapter_start(chapter_id: str):
        chapter = campaign.chapters.get(chapter_id)
        if chapter and chapter.intro_dialogue_id:
            dialogue_lines = campaign.get_dialogue(chapter.intro_dialogue_id)
            if dialogue_lines:
                _play_dialogue(game, dialogue_lines)
    
    def on_chapter_complete(chapter_id: str):
        chapter = campaign.chapters.get(chapter_id)
        if chapter and chapter.outro_dialogue_id:
            dialogue_lines = campaign.get_dialogue(chapter.outro_dialogue_id)
            if dialogue_lines:
                _play_dialogue(game, dialogue_lines)
    
    def on_boss_defeated(boss_id: str):
        campaign.defeat_boss(boss_id)
        game.overlays.notify(f"★ {boss_id.replace('_', ' ').title()} Defeated! ★", 
                            duration=4.0, color=(255, 220, 100))
    
    campaign.on_chapter_start = on_chapter_start
    campaign.on_chapter_complete = on_chapter_complete
    
    # Hook boss defeated in combat integration
    if game.combat:
        original_boss_callback = game.combat.on_boss_defeated
        def combined_boss_callback(boss_id: str):
            on_boss_defeated(boss_id)
            if original_boss_callback:
                original_boss_callback(boss_id)
        game.combat.on_boss_defeated = combined_boss_callback
    
    # Start campaign for new game
    if mode == "new_game":
        # Start with prologue dialogue
        intro_id = campaign.start_new_game()
        if intro_id:
            dialogue_lines = campaign.get_dialogue(intro_id)
            if dialogue_lines:
                _queue_initial_dialogue(game, dialogue_lines)
        
        # Complete prologue and start chapter 1
        outro_id = campaign.complete_prologue()
        if outro_id:
            dialogue_lines = campaign.get_dialogue(outro_id)
            if dialogue_lines:
                _queue_dialogue(game, dialogue_lines, delay=True)
        
        # Start chapter 1
        campaign.start_chapter("chapter_1")
    
    # Run the game
    game.run()


def _play_dialogue(game, dialogue_lines, seq_id="campaign_dialogue"):
    """Play dialogue lines through the game's dialogue system."""
    from hypersim.game.ui.textbox import DialogueSequence, DialogueLine, TextBoxStyle
    
    lines = []
    for line in dialogue_lines:
        speaker = line.get("speaker", "")
        text = line.get("text", "")
        choices = line.get("choices", [])
        
        # Determine style based on speaker
        if speaker == "System":
            style = TextBoxStyle.SYSTEM
        elif speaker == "" or speaker == "Narrator":
            style = TextBoxStyle.NARRATOR
        elif "???" in speaker or "First Point" in speaker or "Voice" in speaker:
            style = TextBoxStyle.DIMENSION
        else:
            style = TextBoxStyle.CHARACTER
        
        lines.append(DialogueLine(
            speaker=speaker,
            text=text,
            style=style,
            choices=choices,
        ))
    
    if lines:
        seq = DialogueSequence(
            id=seq_id,
            lines=lines,
        )
        game.dialogue.register_sequence(seq)
        game.dialogue.start_sequence(seq_id)


def _queue_initial_dialogue(game, dialogue_lines):
    """Queue dialogue to play when game starts."""
    from hypersim.game.ui.textbox import DialogueSequence, DialogueLine, TextBoxStyle
    
    lines = []
    for line in dialogue_lines:
        speaker = line.get("speaker", "")
        text = line.get("text", "")
        choices = line.get("choices", [])
        
        # Determine style based on speaker
        if speaker == "System":
            style = TextBoxStyle.SYSTEM
        elif speaker == "" or speaker == "Narrator":
            style = TextBoxStyle.NARRATOR
        elif "???" in speaker or "First Point" in speaker or "Voice" in speaker:
            style = TextBoxStyle.DIMENSION
        else:
            style = TextBoxStyle.CHARACTER
        
        lines.append(DialogueLine(
            speaker=speaker,
            text=text,
            style=style,
            choices=choices,
        ))
    
    if lines:
        seq = DialogueSequence(
            id="initial_dialogue",
            lines=lines,
        )
        game.dialogue.register_sequence(seq)
        # Will be started when game loop begins
        game._initial_dialogue_id = "initial_dialogue"


def _queue_dialogue(game, dialogue_lines, delay=False):
    """Queue dialogue for later playback."""
    from hypersim.game.ui.textbox import DialogueSequence, DialogueLine, TextBoxStyle
    import random
    
    lines = []
    for line in dialogue_lines:
        speaker = line.get("speaker", "")
        text = line.get("text", "")
        choices = line.get("choices", [])
        
        # Determine style based on speaker
        if speaker == "System":
            style = TextBoxStyle.SYSTEM
        elif speaker == "" or speaker == "Narrator":
            style = TextBoxStyle.NARRATOR
        elif "???" in speaker or "First Point" in speaker or "Voice" in speaker:
            style = TextBoxStyle.DIMENSION
        else:
            style = TextBoxStyle.CHARACTER
        
        lines.append(DialogueLine(
            speaker=speaker,
            text=text,
            style=style,
            choices=choices,
        ))
    
    if lines:
        seq_id = f"queued_dialogue_{random.randint(1000, 9999)}"
        seq = DialogueSequence(id=seq_id, lines=lines)
        game.dialogue.register_sequence(seq)
        
        if not hasattr(game, '_queued_dialogues'):
            game._queued_dialogues = []
        game._queued_dialogues.append(seq_id)


if __name__ == "__main__":
    main()
