#!/usr/bin/env python3
"""Play HyperSim - Cross-Dimensional Adventure.

This is the main entry point for playing the game. It launches
the full game loop with progression, dimension transitions, and
save/load support.

Controls:
    - A/D or Left/Right: Move (1D)
    - WASD: Move (2D)
    - E: Interact (use portals)
    - Space: Use ability
    - P: Pause
    - R: Restart level
    - ESC: Quit

Run with:
    python examples/play_game.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hypersim.game import (
    GameSession,
    DimensionTrack,
    DEFAULT_DIMENSIONS,
    CampaignNode,
    CampaignState,
    ObjectiveSpec,
    ObjectiveType,
)
from hypersim.game.save import load_progression, save_progression, DEFAULT_SAVE_PATH
from hypersim.game.loop import GameLoop


def build_campaign(track: DimensionTrack) -> CampaignState:
    """Build the game campaign with missions for each dimension."""
    nodes = [
        # 1D Missions
        CampaignNode(
            id="awakening-1d",
            dimension_id="1d",
            title="Awakening on the Line",
            description="You exist as a point on an infinite line. Learn to move and sense your surroundings.",
            objectives=[
                ObjectiveSpec(
                    id="reach-1d",
                    type=ObjectiveType.REACH_DIMENSION,
                    description="Begin your existence on the line.",
                    params={"dimension_id": "1d"},
                ),
            ],
            rewards=["xp:50", "ability:ping_neighbors"],
        ),
        CampaignNode(
            id="collect-energy-1d",
            dimension_id="1d",
            title="Gather Energy",
            description="Collect energy orbs scattered along the line.",
            prerequisites=["awakening-1d"],
            objectives=[
                ObjectiveSpec(
                    id="collect-3-energy",
                    type=ObjectiveType.COLLECT,
                    target=3,
                    description="Collect 3 energy orbs.",
                    params={"item": "energy"},
                ),
            ],
            rewards=["xp:75"],
        ),
        CampaignNode(
            id="reach-portal-1d",
            dimension_id="1d",
            title="The Gateway",
            description="A strange portal pulses at the edge of your world. Reach it to ascend.",
            prerequisites=["collect-energy-1d"],
            objectives=[
                ObjectiveSpec(
                    id="reach-2d",
                    type=ObjectiveType.REACH_DIMENSION,
                    description="Enter the portal to 2D.",
                    params={"dimension_id": "2d"},
                ),
            ],
            rewards=["xp:100", "ability:fold_line"],
        ),
        
        # 2D Missions
        CampaignNode(
            id="explore-plane",
            dimension_id="2d",
            title="A Whole New Dimension",
            description="You can now move in two directions! Explore the plane.",
            prerequisites=["reach-portal-1d"],
            objectives=[
                ObjectiveSpec(
                    id="travel-plane",
                    type=ObjectiveType.TRAVEL,
                    target=50.0,
                    description="Travel 50 units in the plane.",
                ),
            ],
            rewards=["xp:100"],
        ),
        CampaignNode(
            id="collect-energy-2d",
            dimension_id="2d",
            title="Planar Harvest",
            description="Energy is scattered across the plane. Gather it.",
            prerequisites=["explore-plane"],
            objectives=[
                ObjectiveSpec(
                    id="collect-4-energy-2d",
                    type=ObjectiveType.COLLECT,
                    target=4,
                    description="Collect 4 energy orbs.",
                    params={"item": "energy"},
                ),
            ],
            rewards=["xp:125", "ability:sketch_path"],
        ),
        CampaignNode(
            id="reach-portal-2d",
            dimension_id="2d",
            title="Into Volume",
            description="A portal to 3D space awaits. Are you ready?",
            prerequisites=["collect-energy-2d"],
            objectives=[
                ObjectiveSpec(
                    id="reach-3d",
                    type=ObjectiveType.REACH_DIMENSION,
                    description="Enter the portal to 3D.",
                    params={"dimension_id": "3d"},
                ),
            ],
            rewards=["xp:150", "ability:slice_plane"],
        ),
        
        # 3D/4D Missions (placeholders)
        CampaignNode(
            id="volume-explorer",
            dimension_id="3d",
            title="Spatial Freedom",
            description="Experience true volume. Move in three dimensions.",
            prerequisites=["reach-portal-2d"],
            objectives=[
                ObjectiveSpec(
                    id="reach-3d-confirm",
                    type=ObjectiveType.REACH_DIMENSION,
                    description="Establish yourself in 3D space.",
                    params={"dimension_id": "3d"},
                ),
            ],
            rewards=["xp:200", "ability:carry_line"],
        ),
        CampaignNode(
            id="hyper-ascension",
            dimension_id="4d",
            title="Hyper Being",
            description="Transcend into the fourth dimension.",
            prerequisites=["volume-explorer"],
            objectives=[
                ObjectiveSpec(
                    id="reach-4d",
                    type=ObjectiveType.REACH_DIMENSION,
                    description="Enter hyperspace.",
                    params={"dimension_id": "4d"},
                ),
            ],
            rewards=["xp:300", "ability:rotate_hyperplanes"],
        ),
    ]
    return CampaignState(nodes=nodes, track=track)


def main() -> None:
    """Main entry point."""
    print("=" * 50)
    print("  HyperSim - Cross-Dimensional Adventure")
    print("=" * 50)
    print()
    print("Controls:")
    print("  A/D or Arrows: Move left/right (1D)")
    print("  WASD: Move in plane (2D)")
    print("  E: Interact with portals")
    print("  P: Pause game")
    print("  R: Restart current level")
    print("  ESC: Quit")
    print()
    
    # Load or create progression
    track = DimensionTrack(DEFAULT_DIMENSIONS)
    campaign = build_campaign(track)
    
    save_path = Path(DEFAULT_SAVE_PATH)
    progression = load_progression(save_path)
    
    if progression:
        print(f"Loaded save: {progression.profile_name}")
        print(f"  Dimension: {progression.current_dimension}")
        print(f"  XP: {progression.xp}")
        print(f"  Completed: {len(progression.completed_nodes)} missions")
    else:
        print("Starting new game...")
    
    print()
    print("Starting game...")
    print()
    
    # Create session and game
    session = GameSession(
        dimensions=track,
        campaign=campaign,
        progression=progression,
    )
    
    game = GameLoop(
        session,
        width=1024,
        height=768,
        title="HyperSim - Cross-Dimensional Adventure"
    )
    
    try:
        game.run()
    finally:
        # Save on exit
        print()
        print("Saving progress...")
        save_progression(session.progression, save_path)
        print(f"Saved to {save_path}")
        print()
        print("Final stats:")
        print(f"  Dimension: {session.progression.current_dimension}")
        print(f"  XP: {session.progression.xp}")
        print(f"  Abilities: {session.abilities.unlocked}")


if __name__ == "__main__":
    main()
