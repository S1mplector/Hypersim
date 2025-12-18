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
    ObjectiveSpec,
    ObjectiveType,
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
                objectives=[
                    ObjectiveSpec(
                        id="reach-1d",
                        type=ObjectiveType.REACH_DIMENSION,
                        description="Exist on the line.",
                        params={"dimension_id": "1d"},
                    )
                ],
            ),
            CampaignNode(
                id="step-into-plane",
                dimension_id="2d",
                title="Step Into the Plane",
                description="Ascend to 2D and learn to fold the line.",
                prerequisites=["awakening-1d"],
                objectives=[
                    ObjectiveSpec(
                        id="reach-2d",
                        type=ObjectiveType.REACH_DIMENSION,
                        description="Enter the plane.",
                        params={"dimension_id": "2d"},
                    )
                ],
            ),
        ],
        track=track,
    )

    session = GameSession(dimensions=track, campaign=campaign)
    print("Starting dimension:", session.active_dimension.name)
    print("Abilities:", session.abilities.unlocked)
    print("Active mission:", session.progression.active_node_id)

    # Complete first mission by recording the starting dimension
    session.record_event("dimension_changed", dimension_id="1d")
    session.ascend_if_ready()
    print("\nAfter completing 'awakening-1d':")
    pprint(session.describe())
    print("Active mission:", session.progression.active_node_id)

    # Finish the second mission by ascending to 2D
    session.set_dimension("2d")
    session.ascend_if_ready()
    print("\nAfter completing 'step-into-plane':")
    pprint(session.describe())
    print("Active mission:", session.progression.active_node_id)


if __name__ == "__main__":
    main()
