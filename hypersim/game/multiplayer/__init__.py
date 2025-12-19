"""Multiplayer networking for HyperSim.

Supports:
- Local split-screen co-op
- LAN peer-to-peer
- Client-server architecture for online play
"""

from .protocol import (
    MessageType,
    NetworkMessage,
    serialize_message,
    deserialize_message,
)
from .state_sync import (
    NetworkEntity,
    WorldState,
    StateSynchronizer,
)
from .session import (
    PlayerSlot,
    MultiplayerSession,
    SessionMode,
)

__all__ = [
    # Protocol
    "MessageType",
    "NetworkMessage",
    "serialize_message",
    "deserialize_message",
    # State sync
    "NetworkEntity",
    "WorldState",
    "StateSynchronizer",
    # Session
    "PlayerSlot",
    "MultiplayerSession",
    "SessionMode",
]
