"""Bootstrap a HyperSim game session with dimension progression.

Run with:
    python examples/game_session_bootstrap.py
"""
from __future__ import annotations

from pprint import pprint

from hypersim.game import (
    CampaignNode,
    CampaignState,
    DimensionTrack,
    GameSession,
    DEFAULT_DIMENSIONS,
)


def main() -> None:
    track = DimensionTrack(DEFAULT_DIMENSIONS)
    campaign = CampaignState(
        nodes=[
            CampaignNode(
                id="awakening-1d",
                dimension_id="1d",
                title="Awakening on the Line",
                description="Learn to move and sense neighbors as a 1D being.",
            ),
            CampaignNode(
                id="step-into-plane",
                dimension_id="2d",
                title="Step Into the Plane",
                description="Ascend to 2D and learn to fold the line.",
                prerequisites=["awakening-1d"],
            ),
        ],
        track=track,
    )

    session = GameSession(dimensions=track, campaign=campaign)
    print("Starting dimension:", session.active_dimension.name)
    print("Control scope:", session.control_scope())
    print("Available missions:", [n.id for n in campaign.available(session.progression)])

    # Complete the first mission and ascend
    campaign.complete("awakening-1d", session.progression)
    session.ascend_if_ready()
    print("\nAfter completing 'awakening-1d':")
    pprint(session.describe())
    print("Available missions:", [n.id for n in campaign.available(session.progression)])

    # Finish the second mission to unlock 3D
    campaign.complete("step-into-plane", session.progression)
    session.ascend_if_ready()
    print("\nAfter completing 'step-into-plane':")
    pprint(session.describe())


if __name__ == "__main__":
    main()
