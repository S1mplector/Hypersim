"""Multiplayer session management."""
from __future__ import annotations

import socket
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

from .protocol import (
    MessageType, NetworkMessage,
    serialize_message, deserialize_message,
    msg_handshake, msg_player_input,
)
from .state_sync import StateSynchronizer, WorldState

if TYPE_CHECKING:
    from hypersim.game.ecs.world import World


class SessionMode(Enum):
    """Multiplayer session modes."""
    SINGLE_PLAYER = "single"
    LOCAL_COOP = "local"      # Split-screen
    LAN_HOST = "lan_host"     # Host a LAN game
    LAN_CLIENT = "lan_client" # Join a LAN game
    ONLINE_HOST = "online_host"
    ONLINE_CLIENT = "online_client"


class PlayerState(Enum):
    """State of a player in the session."""
    CONNECTING = "connecting"
    LOBBY = "lobby"
    READY = "ready"
    PLAYING = "playing"
    DISCONNECTED = "disconnected"


@dataclass
class PlayerSlot:
    """A player slot in the multiplayer session."""
    slot_id: int
    player_id: int = 0
    name: str = ""
    state: PlayerState = PlayerState.CONNECTING
    entity_id: Optional[str] = None
    dimension: str = "1d"
    
    # Network info (for remote players)
    address: Optional[tuple] = None
    last_ping: float = 0.0
    latency_ms: float = 0.0
    
    # Local info
    is_local: bool = True
    input_device: int = 0  # 0=keyboard, 1-4=controllers


@dataclass
class LobbyState:
    """State of the multiplayer lobby."""
    host_name: str = ""
    game_name: str = "HyperSim Game"
    max_players: int = 4
    players: Dict[int, PlayerSlot] = field(default_factory=dict)
    settings: Dict[str, str] = field(default_factory=dict)
    
    @property
    def player_count(self) -> int:
        return len(self.players)
    
    @property
    def is_full(self) -> bool:
        return self.player_count >= self.max_players
    
    def all_ready(self) -> bool:
        return all(p.state == PlayerState.READY for p in self.players.values())


class MultiplayerSession:
    """Manages a multiplayer game session."""
    
    def __init__(self, mode: SessionMode = SessionMode.SINGLE_PLAYER):
        self.mode = mode
        self.is_host = mode in (SessionMode.LOCAL_COOP, SessionMode.LAN_HOST, SessionMode.ONLINE_HOST)
        
        # Players
        self._local_player_id = 1
        self._players: Dict[int, PlayerSlot] = {}
        self._next_player_id = 1
        
        # Lobby
        self.lobby = LobbyState()
        self._in_lobby = True
        
        # State sync
        self.synchronizer = StateSynchronizer(is_authority=self.is_host)
        self.synchronizer.local_player_id = self._local_player_id
        
        # Networking
        self._socket: Optional[socket.socket] = None
        self._connections: Dict[int, tuple] = {}  # player_id -> (addr, port)
        self._running = False
        self._network_thread: Optional[threading.Thread] = None
        
        # Message handlers
        self._message_handlers: Dict[MessageType, Callable] = {}
        self._setup_handlers()
        
        # Callbacks
        self.on_player_join: Optional[Callable[[PlayerSlot], None]] = None
        self.on_player_leave: Optional[Callable[[int], None]] = None
        self.on_game_start: Optional[Callable[[], None]] = None
        self.on_message: Optional[Callable[[NetworkMessage], None]] = None
    
    def _setup_handlers(self) -> None:
        """Set up default message handlers."""
        self._message_handlers[MessageType.HANDSHAKE] = self._handle_handshake
        self._message_handlers[MessageType.DISCONNECT] = self._handle_disconnect
        self._message_handlers[MessageType.PING] = self._handle_ping
        self._message_handlers[MessageType.PONG] = self._handle_pong
        self._message_handlers[MessageType.PLAYER_INPUT] = self._handle_player_input
        self._message_handlers[MessageType.ENTITY_UPDATE] = self._handle_entity_update
        self._message_handlers[MessageType.LOBBY_READY] = self._handle_lobby_ready
        self._message_handlers[MessageType.LOBBY_START] = self._handle_lobby_start
    
    # =========================================================================
    # Player management
    # =========================================================================
    
    def add_local_player(self, name: str = "Player", input_device: int = 0) -> PlayerSlot:
        """Add a local player (for split-screen)."""
        player_id = self._next_player_id
        self._next_player_id += 1
        
        slot = PlayerSlot(
            slot_id=len(self._players),
            player_id=player_id,
            name=name,
            state=PlayerState.LOBBY,
            is_local=True,
            input_device=input_device,
        )
        
        self._players[player_id] = slot
        self.lobby.players[player_id] = slot
        
        if self.on_player_join:
            self.on_player_join(slot)
        
        return slot
    
    def remove_player(self, player_id: int) -> None:
        """Remove a player from the session."""
        if player_id in self._players:
            del self._players[player_id]
            self.lobby.players.pop(player_id, None)
            
            if self.on_player_leave:
                self.on_player_leave(player_id)
    
    def get_player(self, player_id: int) -> Optional[PlayerSlot]:
        """Get a player by ID."""
        return self._players.get(player_id)
    
    def get_local_players(self) -> List[PlayerSlot]:
        """Get all local players."""
        return [p for p in self._players.values() if p.is_local]
    
    def set_player_ready(self, player_id: int, ready: bool = True) -> None:
        """Set a player's ready state."""
        player = self._players.get(player_id)
        if player:
            player.state = PlayerState.READY if ready else PlayerState.LOBBY
    
    # =========================================================================
    # Lobby
    # =========================================================================
    
    def create_lobby(self, game_name: str, max_players: int = 4) -> None:
        """Create a new lobby."""
        self.lobby = LobbyState(
            host_name=self._players.get(self._local_player_id, PlayerSlot(0)).name,
            game_name=game_name,
            max_players=max_players,
        )
        self._in_lobby = True
    
    def start_game(self) -> bool:
        """Start the game from lobby."""
        if not self.lobby.all_ready() and len(self._players) > 1:
            return False
        
        self._in_lobby = False
        
        # Set all players to playing
        for player in self._players.values():
            player.state = PlayerState.PLAYING
        
        if self.on_game_start:
            self.on_game_start()
        
        # Broadcast game start
        if self.is_host:
            self.broadcast(NetworkMessage(type=MessageType.LOBBY_START))
        
        return True
    
    # =========================================================================
    # Networking
    # =========================================================================
    
    def host_game(self, port: int = 7777) -> bool:
        """Start hosting a networked game."""
        if self.mode not in (SessionMode.LAN_HOST, SessionMode.ONLINE_HOST):
            return False
        
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.bind(('0.0.0.0', port))
            self._socket.setblocking(False)
            
            self._running = True
            self._network_thread = threading.Thread(target=self._network_loop, daemon=True)
            self._network_thread.start()
            
            return True
        except Exception as e:
            print(f"Failed to host game: {e}")
            return False
    
    def join_game(self, host: str, port: int = 7777, player_name: str = "Player") -> bool:
        """Join a networked game."""
        if self.mode not in (SessionMode.LAN_CLIENT, SessionMode.ONLINE_CLIENT):
            return False
        
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setblocking(False)
            
            # Send handshake
            handshake = msg_handshake(player_name, "1.0.0")
            self._send_to((host, port), handshake)
            
            self._connections[0] = (host, port)  # Server is player 0
            
            self._running = True
            self._network_thread = threading.Thread(target=self._network_loop, daemon=True)
            self._network_thread.start()
            
            return True
        except Exception as e:
            print(f"Failed to join game: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the session."""
        self._running = False
        
        if self._socket:
            # Send disconnect message
            self.broadcast(NetworkMessage(type=MessageType.DISCONNECT))
            self._socket.close()
            self._socket = None
        
        if self._network_thread:
            self._network_thread.join(timeout=1.0)
            self._network_thread = None
    
    def _network_loop(self) -> None:
        """Background thread for network communication."""
        while self._running and self._socket:
            try:
                data, addr = self._socket.recvfrom(4096)
                msg = deserialize_message(data)
                if msg:
                    self._handle_message(msg, addr)
            except BlockingIOError:
                pass  # No data available
            except Exception as e:
                if self._running:
                    print(f"Network error: {e}")
            
            time.sleep(0.001)  # Prevent busy loop
    
    def _handle_message(self, msg: NetworkMessage, addr: tuple) -> None:
        """Handle an incoming network message."""
        handler = self._message_handlers.get(msg.type)
        if handler:
            handler(msg, addr)
        
        if self.on_message:
            self.on_message(msg)
    
    def _send_to(self, addr: tuple, msg: NetworkMessage) -> None:
        """Send a message to a specific address."""
        if self._socket:
            data = serialize_message(msg)
            self._socket.sendto(data, addr)
    
    def broadcast(self, msg: NetworkMessage, exclude: Optional[int] = None) -> None:
        """Broadcast a message to all connected players."""
        for player_id, addr in self._connections.items():
            if player_id != exclude:
                self._send_to(addr, msg)
    
    # =========================================================================
    # Message handlers
    # =========================================================================
    
    def _handle_handshake(self, msg: NetworkMessage, addr: tuple) -> None:
        """Handle handshake from new player."""
        if not self.is_host:
            return
        
        player_name = msg.payload.get("player_name", "Unknown")
        
        # Assign player ID
        player_id = self._next_player_id
        self._next_player_id += 1
        
        # Create player slot
        slot = PlayerSlot(
            slot_id=len(self._players),
            player_id=player_id,
            name=player_name,
            state=PlayerState.LOBBY,
            is_local=False,
            address=addr,
        )
        
        self._players[player_id] = slot
        self.lobby.players[player_id] = slot
        self._connections[player_id] = addr
        
        # Send acknowledgment
        ack = NetworkMessage(
            type=MessageType.HANDSHAKE_ACK,
            payload={
                "player_id": player_id,
                "lobby_state": {
                    "game_name": self.lobby.game_name,
                    "players": {
                        pid: {"name": p.name, "state": p.state.value}
                        for pid, p in self._players.items()
                    }
                }
            }
        )
        self._send_to(addr, ack)
        
        if self.on_player_join:
            self.on_player_join(slot)
    
    def _handle_disconnect(self, msg: NetworkMessage, addr: tuple) -> None:
        """Handle player disconnect."""
        player_id = msg.sender_id
        self.remove_player(player_id)
        self._connections.pop(player_id, None)
    
    def _handle_ping(self, msg: NetworkMessage, addr: tuple) -> None:
        """Handle ping request."""
        pong = NetworkMessage(
            type=MessageType.PONG,
            payload={"timestamp": msg.payload.get("timestamp", 0)}
        )
        self._send_to(addr, pong)
    
    def _handle_pong(self, msg: NetworkMessage, addr: tuple) -> None:
        """Handle pong response."""
        sent_time = msg.payload.get("timestamp", 0)
        latency = (time.time() - sent_time) * 1000  # ms
        
        # Update player latency
        for player in self._players.values():
            if player.address == addr:
                player.latency_ms = latency
                player.last_ping = time.time()
                break
    
    def _handle_player_input(self, msg: NetworkMessage, addr: tuple) -> None:
        """Handle input from remote player."""
        # Forward to game for processing
        pass
    
    def _handle_entity_update(self, msg: NetworkMessage, addr: tuple) -> None:
        """Handle entity state update."""
        self.synchronizer.receive_state_update(msg.payload)
    
    def _handle_lobby_ready(self, msg: NetworkMessage, addr: tuple) -> None:
        """Handle player ready state change."""
        player_id = msg.sender_id
        ready = msg.payload.get("ready", True)
        self.set_player_ready(player_id, ready)
    
    def _handle_lobby_start(self, msg: NetworkMessage, addr: tuple) -> None:
        """Handle game start signal."""
        if not self.is_host:
            self.start_game()
    
    # =========================================================================
    # Game integration
    # =========================================================================
    
    def update(self, dt: float, world: Optional["World"] = None) -> None:
        """Update multiplayer state."""
        if world and self.synchronizer.should_sync():
            # Update from world
            self.synchronizer.update_from_world(world)
            
            # Send dirty entities
            dirty = self.synchronizer.get_dirty_entities()
            if dirty:
                update_msg = NetworkMessage(
                    type=MessageType.ENTITY_UPDATE,
                    payload={
                        "entities": {e.entity_id: e.to_dict() for e in dirty}
                    },
                    reliable=False,
                )
                self.broadcast(update_msg)
            
            # Apply remote state
            self.synchronizer.apply_to_world(world)
    
    def send_input(self, input_state: Dict) -> None:
        """Send local input to server/host."""
        if not self.is_host and self._socket:
            seq = self.synchronizer.record_input(input_state)
            msg = msg_player_input({
                "sequence": seq,
                **input_state
            })
            self.broadcast(msg)
