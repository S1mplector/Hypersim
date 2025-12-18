"""Campaign-style game mode that layers progression onto the sandbox."""
from __future__ import annotations

from pathlib import Path

from hypersim.cli.sandbox_4d import Sandbox4D
from hypersim.game import (
    CampaignNode,
    CampaignState,
    DimensionTrack,
    GameSession,
    DEFAULT_DIMENSIONS,
)
from hypersim.game.save import load_progression, save_progression, DEFAULT_SAVE_PATH


def _build_default_campaign(track: DimensionTrack) -> CampaignState:
    """Create a light, linear campaign over the default dimensions."""
    nodes = [
        CampaignNode(
            id="awakening-1d",
            dimension_id="1d",
            title="Awakening on the Line",
            description="Learn to move along the line and ping neighbors.",
        ),
        CampaignNode(
            id="step-into-plane",
            dimension_id="2d",
            title="Step Into the Plane",
            description="Ascend to 2D, fold space, and sketch a path.",
            prerequisites=["awakening-1d"],
        ),
        CampaignNode(
            id="stretch-into-space",
            dimension_id="3d",
            title="Stretch Into Space",
            description="Enter 3D space and manipulate 2D holograms.",
            prerequisites=["step-into-plane"],
        ),
        CampaignNode(
            id="hyper-sense",
            dimension_id="4d",
            title="Awaken as Hyper Being",
            description="Rotate hyperplanes and stabilize lower dimensions.",
            prerequisites=["stretch-into-space"],
        ),
    ]
    return CampaignState(nodes=nodes, track=track)


def run_game_mode() -> None:
    """Launch the progression-enabled sandbox experience."""
    track = DimensionTrack(DEFAULT_DIMENSIONS)
    campaign = _build_default_campaign(track)
    save_path = Path(DEFAULT_SAVE_PATH)
    progression = load_progression(save_path) or None
    session = GameSession(dimensions=track, campaign=campaign, progression=progression)
    app = Sandbox4D(session=session)
    try:
        app.run()
    finally:
        save_progression(session.progression, save_path)
