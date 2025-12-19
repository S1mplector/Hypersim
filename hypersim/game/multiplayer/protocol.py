"""Network protocol for multiplayer communication."""
from __future__ import annotations

import json
import struct
import zlib
from dataclasses import dataclass, field, asdict
from enum import IntEnum
from typing import Any, Dict, List, Optional, Union

import numpy as np


class MessageType(IntEnum):
    """Types of network messages."""
    # Connection
    HANDSHAKE = 1
    HANDSHAKE_ACK = 2
    DISCONNECT = 3
    PING = 4
    PONG = 5
    
    # Lobby
    LOBBY_JOIN = 10
    LOBBY_LEAVE = 11
    LOBBY_STATE = 12
    LOBBY_READY = 13
    LOBBY_START = 14
    LOBBY_CHAT = 15
    
    # Game state
    WORLD_STATE = 20
    ENTITY_SPAWN = 21
    ENTITY_DESTROY = 22
    ENTITY_UPDATE = 23
    
    # Player actions
    PLAYER_INPUT = 30
    PLAYER_ACTION = 31
    PLAYER_ABILITY = 32
    
    # Events
    GAME_EVENT = 40
    DIMENSION_CHANGE = 41
    EVOLUTION_UPDATE = 42
    
    # Sync
    FULL_SYNC_REQUEST = 50
    FULL_SYNC_RESPONSE = 51
    DELTA_SYNC = 52


@dataclass
class NetworkMessage:
    """A network message with type and payload."""
    type: MessageType
    payload: Dict[str, Any] = field(default_factory=dict)
    sender_id: int = 0
    sequence: int = 0
    timestamp: float = 0.0
    reliable: bool = True  # If True, requires acknowledgment


# Protocol version for compatibility checking
PROTOCOL_VERSION = 1
MAGIC_HEADER = b"HYPR"


def serialize_message(msg: NetworkMessage, compress: bool = True) -> bytes:
    """Serialize a message to bytes for network transmission.
    
    Format:
    - 4 bytes: Magic header "HYPR"
    - 1 byte: Protocol version
    - 1 byte: Flags (compressed, reliable)
    - 2 bytes: Message type
    - 4 bytes: Sequence number
    - 4 bytes: Sender ID
    - 4 bytes: Payload length
    - N bytes: Payload (JSON, optionally compressed)
    """
    # Prepare payload
    payload_json = json.dumps(msg.payload, cls=NumpyEncoder).encode('utf-8')
    
    if compress and len(payload_json) > 100:
        payload_data = zlib.compress(payload_json)
        flags = 0b00000011 if msg.reliable else 0b00000001  # compressed + reliable
    else:
        payload_data = payload_json
        flags = 0b00000010 if msg.reliable else 0b00000000  # reliable only
    
    # Build header
    header = struct.pack(
        '>4sBBHIII',
        MAGIC_HEADER,
        PROTOCOL_VERSION,
        flags,
        msg.type.value,
        msg.sequence,
        msg.sender_id,
        len(payload_data)
    )
    
    return header + payload_data


def deserialize_message(data: bytes) -> Optional[NetworkMessage]:
    """Deserialize bytes to a NetworkMessage."""
    if len(data) < 20:  # Minimum header size
        return None
    
    try:
        # Parse header
        magic, version, flags, msg_type, sequence, sender_id, payload_len = struct.unpack(
            '>4sBBHIII', data[:20]
        )
        
        if magic != MAGIC_HEADER:
            return None
        
        if version != PROTOCOL_VERSION:
            print(f"Warning: Protocol version mismatch: {version} != {PROTOCOL_VERSION}")
        
        # Extract payload
        payload_data = data[20:20 + payload_len]
        
        # Decompress if needed
        is_compressed = flags & 0b00000001
        if is_compressed:
            payload_data = zlib.decompress(payload_data)
        
        payload = json.loads(payload_data.decode('utf-8'))
        
        return NetworkMessage(
            type=MessageType(msg_type),
            payload=payload,
            sender_id=sender_id,
            sequence=sequence,
            reliable=bool(flags & 0b00000010),
        )
    
    except Exception as e:
        print(f"Failed to deserialize message: {e}")
        return None


class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types."""
    
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return {"__ndarray__": True, "data": obj.tolist(), "dtype": str(obj.dtype)}
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return super().default(obj)


def numpy_decoder(dct: Dict) -> Any:
    """JSON decoder hook for numpy arrays."""
    if "__ndarray__" in dct:
        return np.array(dct["data"], dtype=dct["dtype"])
    return dct


# Message builders for common operations
def msg_handshake(player_name: str, client_version: str) -> NetworkMessage:
    """Create a handshake message."""
    return NetworkMessage(
        type=MessageType.HANDSHAKE,
        payload={
            "player_name": player_name,
            "client_version": client_version,
            "protocol_version": PROTOCOL_VERSION,
        }
    )


def msg_player_input(input_state: Dict[str, Any]) -> NetworkMessage:
    """Create a player input message."""
    return NetworkMessage(
        type=MessageType.PLAYER_INPUT,
        payload=input_state,
        reliable=False,  # Input can be dropped
    )


def msg_entity_update(entity_id: str, position: np.ndarray, velocity: np.ndarray) -> NetworkMessage:
    """Create an entity update message."""
    return NetworkMessage(
        type=MessageType.ENTITY_UPDATE,
        payload={
            "entity_id": entity_id,
            "position": position.tolist(),
            "velocity": velocity.tolist(),
        },
        reliable=False,
    )


def msg_game_event(event_type: str, **data) -> NetworkMessage:
    """Create a game event message."""
    return NetworkMessage(
        type=MessageType.GAME_EVENT,
        payload={
            "event_type": event_type,
            **data,
        }
    )


def msg_dimension_change(player_id: str, new_dimension: str) -> NetworkMessage:
    """Create a dimension change message."""
    return NetworkMessage(
        type=MessageType.DIMENSION_CHANGE,
        payload={
            "player_id": player_id,
            "dimension": new_dimension,
        }
    )
