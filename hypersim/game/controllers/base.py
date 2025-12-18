"""Base controller and input handling infrastructure."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

import pygame
import numpy as np
from numpy.typing import NDArray


@dataclass
class InputMapping:
    """Maps keyboard/mouse inputs to game actions for a dimension."""
    
    dimension_id: str
    move_positive: Dict[str, int] = field(default_factory=dict)  # axis -> key
    move_negative: Dict[str, int] = field(default_factory=dict)  # axis -> key
    actions: Dict[str, int] = field(default_factory=dict)  # action -> key
    mouse_look: bool = False
    mouse_sensitivity: float = 0.002


# Default input mappings per dimension
DEFAULT_MAPPINGS: Dict[str, InputMapping] = {
    "1d": InputMapping(
        dimension_id="1d",
        move_positive={"x": pygame.K_d, "x_alt": pygame.K_RIGHT},
        move_negative={"x": pygame.K_a, "x_alt": pygame.K_LEFT},
        actions={
            "ability1": pygame.K_SPACE,
            "interact": pygame.K_e,
        },
    ),
    "2d": InputMapping(
        dimension_id="2d",
        move_positive={"x": pygame.K_d, "y": pygame.K_w},
        move_negative={"x": pygame.K_a, "y": pygame.K_s},
        actions={
            "ability1": pygame.K_SPACE,
            "ability2": pygame.K_q,
            "interact": pygame.K_e,
        },
    ),
    "3d": InputMapping(
        dimension_id="3d",
        move_positive={"x": pygame.K_d, "z": pygame.K_w},
        move_negative={"x": pygame.K_a, "z": pygame.K_s},
        actions={
            "jump": pygame.K_SPACE,
            "crouch": pygame.K_LCTRL,
            "ability1": pygame.K_q,
            "interact": pygame.K_e,
        },
        mouse_look=True,
    ),
    "4d": InputMapping(
        dimension_id="4d",
        move_positive={"x": pygame.K_d, "z": pygame.K_w, "w": pygame.K_e},
        move_negative={"x": pygame.K_a, "z": pygame.K_s, "w": pygame.K_q},
        actions={
            "jump": pygame.K_SPACE,
            "crouch": pygame.K_LCTRL,
            "ability1": pygame.K_1,
            "ability2": pygame.K_2,
            "interact": pygame.K_f,
        },
        mouse_look=True,
    ),
}


class InputHandler:
    """Processes raw input events and maintains input state."""
    
    def __init__(self):
        self._keys_held: Set[int] = set()
        self._keys_pressed: Set[int] = set()  # Just pressed this frame
        self._keys_released: Set[int] = set()  # Just released this frame
        self._mouse_delta: List[int] = [0, 0]
        self._mouse_buttons: Set[int] = set()
        self._action_states: Dict[str, bool] = {}
    
    def process_event(self, event: pygame.event.Event) -> None:
        """Process a single pygame event."""
        if event.type == pygame.KEYDOWN:
            self._keys_held.add(event.key)
            self._keys_pressed.add(event.key)
        elif event.type == pygame.KEYUP:
            self._keys_held.discard(event.key)
            self._keys_released.add(event.key)
        elif event.type == pygame.MOUSEMOTION:
            self._mouse_delta[0] += event.rel[0]
            self._mouse_delta[1] += event.rel[1]
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._mouse_buttons.add(event.button)
        elif event.type == pygame.MOUSEBUTTONUP:
            self._mouse_buttons.discard(event.button)
    
    def end_frame(self) -> None:
        """Clear per-frame state. Call at end of each update cycle."""
        self._keys_pressed.clear()
        self._keys_released.clear()
        self._mouse_delta = [0, 0]
    
    def is_held(self, key: int) -> bool:
        """Check if a key is currently held down."""
        return key in self._keys_held
    
    def is_pressed(self, key: int) -> bool:
        """Check if a key was just pressed this frame."""
        return key in self._keys_pressed
    
    def is_released(self, key: int) -> bool:
        """Check if a key was just released this frame."""
        return key in self._keys_released
    
    def get_axis(self, positive_key: int, negative_key: int) -> float:
        """Get axis value from two keys (-1, 0, or 1)."""
        value = 0.0
        if self.is_held(positive_key):
            value += 1.0
        if self.is_held(negative_key):
            value -= 1.0
        return value
    
    def get_mouse_delta(self) -> tuple[int, int]:
        """Get mouse movement since last frame."""
        return tuple(self._mouse_delta)
    
    def is_mouse_button_held(self, button: int) -> bool:
        """Check if a mouse button is held."""
        return button in self._mouse_buttons


class BaseController(ABC):
    """Base class for dimension-specific controllers."""
    
    dimension_id: str = "base"
    axes_count: int = 1
    
    def __init__(self, mapping: Optional[InputMapping] = None):
        self.mapping = mapping or DEFAULT_MAPPINGS.get(self.dimension_id, InputMapping(self.dimension_id))
        self.enabled = True
    
    @abstractmethod
    def compute_movement(self, input_handler: InputHandler) -> NDArray:
        """Compute movement vector from current input state.
        
        Returns:
            NDArray of shape (4,) with movement intent per axis
        """
        pass
    
    def get_action(self, action_name: str, input_handler: InputHandler) -> bool:
        """Check if an action key was just pressed."""
        key = self.mapping.actions.get(action_name)
        if key is None:
            return False
        return input_handler.is_pressed(key)
    
    def get_action_held(self, action_name: str, input_handler: InputHandler) -> bool:
        """Check if an action key is held."""
        key = self.mapping.actions.get(action_name)
        if key is None:
            return False
        return input_handler.is_held(key)
    
    def _get_axis_value(self, axis: str, input_handler: InputHandler) -> float:
        """Get input value for an axis (checks main key and alt key)."""
        pos_key = self.mapping.move_positive.get(axis)
        neg_key = self.mapping.move_negative.get(axis)
        pos_alt = self.mapping.move_positive.get(f"{axis}_alt")
        neg_alt = self.mapping.move_negative.get(f"{axis}_alt")
        
        value = 0.0
        if pos_key and input_handler.is_held(pos_key):
            value += 1.0
        if neg_key and input_handler.is_held(neg_key):
            value -= 1.0
        if pos_alt and input_handler.is_held(pos_alt):
            value += 1.0
        if neg_alt and input_handler.is_held(neg_alt):
            value -= 1.0
        
        return np.clip(value, -1.0, 1.0)
