"""Gameplay scaffolding for HyperSim.

This package introduces dimension descriptors, progression, and session
management primitives to evolve HyperSim toward a game engine. The APIs
are intentionally lightweight so they can wrap existing rendering and
simulation pieces without forcing a specific gameplay loop.

New in this version:
- ECS (Entity Component System) for cross-dimensional gameplay
- Dimension-specific controllers (1D line, 2D plane)
- Game systems (input, physics, collision, damage, AI)
- Dimension-specific renderers
- Main game loop with progression integration
"""

from .abilities import AbilityState
from .dimensions import DimensionSpec, DimensionTrack, DEFAULT_DIMENSIONS
from .progression import CampaignNode, CampaignState, ProgressionState
from .session import GameSession
from .objectives import (
    ObjectiveSpec,
    ObjectiveType,
    MissionState,
    MissionTracker,
)

__all__ = [
    # Core game types
    "AbilityState",
    "DimensionSpec",
    "DimensionTrack",
    "DEFAULT_DIMENSIONS",
    "CampaignNode",
    "CampaignState",
    "ProgressionState",
    "GameSession",
    "ObjectiveSpec",
    "ObjectiveType",
    "MissionState",
    "MissionTracker",
]


def run_game():
    """Launch the playable game with default settings."""
    from .loop import run_game as _run
    _run()
