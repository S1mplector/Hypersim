"""Gameplay scaffolding for HyperSim.

This package introduces dimension descriptors, progression, and session
management primitives to evolve HyperSim toward a game engine. The APIs
are intentionally lightweight so they can wrap existing rendering and
simulation pieces without forcing a specific gameplay loop.
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
