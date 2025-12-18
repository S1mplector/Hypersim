"""Gameplay scaffolding for HyperSim.

This package introduces dimension descriptors, progression, and session
management primitives to evolve HyperSim toward a game engine. The APIs
are intentionally lightweight so they can wrap existing rendering and
simulation pieces without forcing a specific gameplay loop.
"""

from .dimensions import DimensionSpec, DimensionTrack, DEFAULT_DIMENSIONS
from .progression import CampaignNode, CampaignState, ProgressionState
from .session import GameSession

__all__ = [
    "DimensionSpec",
    "DimensionTrack",
    "DEFAULT_DIMENSIONS",
    "CampaignNode",
    "CampaignState",
    "ProgressionState",
    "GameSession",
]
