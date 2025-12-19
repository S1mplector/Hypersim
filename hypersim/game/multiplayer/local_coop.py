"""Local split-screen co-op support."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

import pygame
import numpy as np

if TYPE_CHECKING:
    from hypersim.game.ecs.world import World
    from hypersim.game.ecs.entity import Entity
    from hypersim.game.rendering.base_renderer import DimensionRenderer


class SplitMode(Enum):
    """Screen split modes for local co-op."""
    SINGLE = "single"           # No split (1 player)
    HORIZONTAL = "horizontal"   # Top/bottom split (2 players)
    VERTICAL = "vertical"       # Left/right split (2 players)
    QUAD = "quad"               # 4-way split (3-4 players)


@dataclass
class Viewport:
    """A viewport for rendering one player's view."""
    player_id: int
    rect: pygame.Rect
    surface: pygame.Surface = None
    
    # Camera state (for 3D/4D)
    camera_pos: np.ndarray = field(default_factory=lambda: np.zeros(4))
    camera_yaw: float = 0.0
    camera_pitch: float = 0.0
    
    def __post_init__(self):
        if self.surface is None:
            self.surface = pygame.Surface((self.rect.width, self.rect.height))


@dataclass 
class LocalPlayerConfig:
    """Configuration for a local player."""
    player_id: int
    name: str = "Player"
    input_device: int = 0  # 0=keyboard1, 1=keyboard2, 2-5=controllers
    color: Tuple[int, int, int] = (80, 200, 255)
    
    # Key bindings (for keyboard players)
    keys: Dict[str, int] = field(default_factory=dict)


# Default key bindings for two keyboard players
KEYBOARD_1_BINDINGS = {
    "up": pygame.K_w,
    "down": pygame.K_s,
    "left": pygame.K_a,
    "right": pygame.K_d,
    "action": pygame.K_e,
    "ability": pygame.K_SPACE,
    "jump": pygame.K_SPACE,
    "crouch": pygame.K_LCTRL,
}

KEYBOARD_2_BINDINGS = {
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "action": pygame.K_RETURN,
    "ability": pygame.K_RSHIFT,
    "jump": pygame.K_RSHIFT,
    "crouch": pygame.K_RCTRL,
}


class LocalCoopManager:
    """Manages local split-screen co-op."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        self._players: Dict[int, LocalPlayerConfig] = {}
        self._viewports: Dict[int, Viewport] = {}
        self._split_mode = SplitMode.SINGLE
        
        # Input state per player
        self._input_states: Dict[int, Dict[str, bool]] = {}
        
        # Controller support
        pygame.joystick.init()
        self._joysticks: List[pygame.joystick.Joystick] = []
        self._refresh_joysticks()
    
    def _refresh_joysticks(self) -> None:
        """Refresh connected joysticks/controllers."""
        self._joysticks = []
        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            joy.init()
            self._joysticks.append(joy)
    
    def add_player(
        self,
        player_id: int,
        name: str = "",
        input_device: int = 0,
        color: Optional[Tuple[int, int, int]] = None
    ) -> LocalPlayerConfig:
        """Add a local player."""
        if not name:
            name = f"Player {len(self._players) + 1}"
        
        # Assign color based on player number
        default_colors = [
            (80, 200, 255),   # Cyan
            (255, 100, 100),  # Red
            (100, 255, 100),  # Green
            (255, 200, 50),   # Yellow
        ]
        if color is None:
            color = default_colors[len(self._players) % len(default_colors)]
        
        # Set up key bindings
        keys = {}
        if input_device == 0:
            keys = KEYBOARD_1_BINDINGS.copy()
        elif input_device == 1:
            keys = KEYBOARD_2_BINDINGS.copy()
        
        config = LocalPlayerConfig(
            player_id=player_id,
            name=name,
            input_device=input_device,
            color=color,
            keys=keys,
        )
        
        self._players[player_id] = config
        self._input_states[player_id] = {}
        
        self._update_split_mode()
        self._create_viewports()
        
        return config
    
    def remove_player(self, player_id: int) -> None:
        """Remove a local player."""
        self._players.pop(player_id, None)
        self._viewports.pop(player_id, None)
        self._input_states.pop(player_id, None)
        
        self._update_split_mode()
        self._create_viewports()
    
    def _update_split_mode(self) -> None:
        """Update split mode based on player count."""
        count = len(self._players)
        if count <= 1:
            self._split_mode = SplitMode.SINGLE
        elif count == 2:
            # Prefer horizontal for widescreen
            if self.screen_width / self.screen_height > 1.5:
                self._split_mode = SplitMode.VERTICAL
            else:
                self._split_mode = SplitMode.HORIZONTAL
        else:
            self._split_mode = SplitMode.QUAD
    
    def _create_viewports(self) -> None:
        """Create viewports for all players."""
        self._viewports.clear()
        
        player_ids = list(self._players.keys())
        count = len(player_ids)
        
        if count == 0:
            return
        
        w, h = self.screen_width, self.screen_height
        
        if self._split_mode == SplitMode.SINGLE:
            self._viewports[player_ids[0]] = Viewport(
                player_id=player_ids[0],
                rect=pygame.Rect(0, 0, w, h)
            )
        
        elif self._split_mode == SplitMode.HORIZONTAL:
            # Top/bottom split
            half_h = h // 2
            self._viewports[player_ids[0]] = Viewport(
                player_id=player_ids[0],
                rect=pygame.Rect(0, 0, w, half_h)
            )
            if count > 1:
                self._viewports[player_ids[1]] = Viewport(
                    player_id=player_ids[1],
                    rect=pygame.Rect(0, half_h, w, half_h)
                )
        
        elif self._split_mode == SplitMode.VERTICAL:
            # Left/right split
            half_w = w // 2
            self._viewports[player_ids[0]] = Viewport(
                player_id=player_ids[0],
                rect=pygame.Rect(0, 0, half_w, h)
            )
            if count > 1:
                self._viewports[player_ids[1]] = Viewport(
                    player_id=player_ids[1],
                    rect=pygame.Rect(half_w, 0, half_w, h)
                )
        
        elif self._split_mode == SplitMode.QUAD:
            # 4-way split
            half_w, half_h = w // 2, h // 2
            positions = [
                (0, 0),           # Top-left
                (half_w, 0),      # Top-right
                (0, half_h),      # Bottom-left
                (half_w, half_h), # Bottom-right
            ]
            for i, pid in enumerate(player_ids[:4]):
                x, y = positions[i]
                self._viewports[pid] = Viewport(
                    player_id=pid,
                    rect=pygame.Rect(x, y, half_w, half_h)
                )
    
    def process_event(self, event: pygame.event.Event) -> None:
        """Process input events for all local players."""
        # Keyboard input
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            pressed = event.type == pygame.KEYDOWN
            
            for player_id, config in self._players.items():
                if config.input_device > 1:
                    continue  # Controller player
                
                for action, key in config.keys.items():
                    if event.key == key:
                        self._input_states[player_id][action] = pressed
        
        # Controller input
        elif event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP:
            pressed = event.type == pygame.JOYBUTTONDOWN
            joy_id = event.joy
            
            for player_id, config in self._players.items():
                if config.input_device == joy_id + 2:  # Controllers start at device 2
                    # Map controller buttons
                    button_map = {
                        0: "action",    # A/X
                        1: "ability",   # B/Circle
                        2: "jump",      # X/Square
                        3: "crouch",    # Y/Triangle
                    }
                    action = button_map.get(event.button)
                    if action:
                        self._input_states[player_id][action] = pressed
        
        elif event.type == pygame.JOYAXISMOTION:
            joy_id = event.joy
            
            for player_id, config in self._players.items():
                if config.input_device == joy_id + 2:
                    # Left stick
                    if event.axis == 0:  # X axis
                        self._input_states[player_id]["left"] = event.value < -0.5
                        self._input_states[player_id]["right"] = event.value > 0.5
                    elif event.axis == 1:  # Y axis
                        self._input_states[player_id]["up"] = event.value < -0.5
                        self._input_states[player_id]["down"] = event.value > 0.5
    
    def get_input(self, player_id: int) -> Dict[str, bool]:
        """Get current input state for a player."""
        return self._input_states.get(player_id, {})
    
    def get_movement_vector(self, player_id: int) -> np.ndarray:
        """Get movement vector from input state."""
        state = self._input_states.get(player_id, {})
        
        x = 0.0
        y = 0.0
        
        if state.get("left"):
            x -= 1.0
        if state.get("right"):
            x += 1.0
        if state.get("up"):
            y += 1.0
        if state.get("down"):
            y -= 1.0
        
        # Normalize
        length = np.sqrt(x*x + y*y)
        if length > 1.0:
            x /= length
            y /= length
        
        return np.array([x, y, 0.0, 0.0])
    
    def render_viewports(
        self,
        world: "World",
        renderers: Dict[str, "DimensionRenderer"],
        player_entities: Dict[int, "Entity"],
        dimension_specs: Dict[str, any],
    ) -> None:
        """Render all viewports."""
        for player_id, viewport in self._viewports.items():
            entity = player_entities.get(player_id)
            if not entity:
                continue
            
            # Get player's dimension
            from hypersim.game.ecs.component import DimensionAnchor
            anchor = entity.get(DimensionAnchor)
            dim_id = anchor.dimension_id if anchor else "1d"
            
            renderer = renderers.get(dim_id)
            if not renderer:
                continue
            
            # Update renderer for this player's view
            # (Would need to modify renderer to use viewport.surface)
            
            # For now, just render to main screen at viewport position
            # Full implementation would render to viewport.surface then blit
            
            # Draw viewport border
            border_color = self._players[player_id].color
            pygame.draw.rect(self.screen, border_color, viewport.rect, 2)
            
            # Draw player name
            font = pygame.font.Font(None, 20)
            name_text = font.render(
                self._players[player_id].name,
                True, border_color
            )
            self.screen.blit(name_text, (viewport.rect.x + 5, viewport.rect.y + 5))
    
    @property
    def player_count(self) -> int:
        return len(self._players)
    
    @property
    def split_mode(self) -> SplitMode:
        return self._split_mode
    
    def get_viewport(self, player_id: int) -> Optional[Viewport]:
        return self._viewports.get(player_id)
