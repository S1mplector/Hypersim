"""Configurable input handling system.

Provides a flexible keybinding system that can be configured
via config files or at runtime.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Set, Any
import pygame


class InputAction(Enum):
    """Standard input actions."""
    # Camera movement
    CAMERA_FORWARD = auto()
    CAMERA_BACKWARD = auto()
    CAMERA_LEFT = auto()
    CAMERA_RIGHT = auto()
    CAMERA_UP = auto()
    CAMERA_DOWN = auto()
    CAMERA_W_POSITIVE = auto()
    CAMERA_W_NEGATIVE = auto()
    
    # View controls
    ZOOM_IN = auto()
    ZOOM_OUT = auto()
    RESET_VIEW = auto()
    
    # Object controls
    TOGGLE_SPIN = auto()
    NEXT_OBJECT = auto()
    PREV_OBJECT = auto()
    
    # Display modes
    TOGGLE_WIREFRAME = auto()
    TOGGLE_FACES = auto()
    TOGGLE_STEREO = auto()
    TOGGLE_INFO = auto()
    
    # Playback
    PLAY_PAUSE = auto()
    STOP = auto()
    
    # Application
    QUIT = auto()
    SCREENSHOT = auto()


# Default key bindings
DEFAULT_KEYBINDINGS: Dict[int, InputAction] = {
    pygame.K_w: InputAction.CAMERA_FORWARD,
    pygame.K_s: InputAction.CAMERA_BACKWARD,
    pygame.K_a: InputAction.CAMERA_LEFT,
    pygame.K_d: InputAction.CAMERA_RIGHT,
    pygame.K_q: InputAction.CAMERA_UP,
    pygame.K_e: InputAction.CAMERA_DOWN,
    pygame.K_z: InputAction.CAMERA_W_POSITIVE,
    pygame.K_x: InputAction.CAMERA_W_NEGATIVE,
    pygame.K_EQUALS: InputAction.ZOOM_IN,
    pygame.K_PLUS: InputAction.ZOOM_IN,
    pygame.K_MINUS: InputAction.ZOOM_OUT,
    pygame.K_r: InputAction.RESET_VIEW,
    pygame.K_t: InputAction.TOGGLE_SPIN,
    pygame.K_RIGHT: InputAction.NEXT_OBJECT,
    pygame.K_LEFT: InputAction.PREV_OBJECT,
    pygame.K_f: InputAction.TOGGLE_FACES,
    pygame.K_3: InputAction.TOGGLE_STEREO,
    pygame.K_i: InputAction.TOGGLE_INFO,
    pygame.K_SPACE: InputAction.PLAY_PAUSE,
    pygame.K_ESCAPE: InputAction.QUIT,
    pygame.K_F12: InputAction.SCREENSHOT,
}


@dataclass
class InputState:
    """Current state of input devices."""
    keys_pressed: Set[int] = field(default_factory=set)
    keys_just_pressed: Set[int] = field(default_factory=set)
    keys_just_released: Set[int] = field(default_factory=set)
    mouse_pos: tuple = (0, 0)
    mouse_delta: tuple = (0, 0)
    mouse_buttons: tuple = (False, False, False)
    mouse_just_pressed: Set[int] = field(default_factory=set)
    mouse_just_released: Set[int] = field(default_factory=set)
    mouse_wheel: int = 0


class InputManager:
    """Manages input handling with configurable keybindings.
    
    Supports:
    - Configurable key bindings
    - Action-based input (decouple keys from actions)
    - Callback registration for actions
    - Continuous and one-shot input detection
    """
    
    def __init__(self, keybindings: Optional[Dict[int, InputAction]] = None):
        """Initialize the input manager.
        
        Args:
            keybindings: Optional custom keybindings, uses defaults if None
        """
        self.keybindings = dict(keybindings or DEFAULT_KEYBINDINGS)
        self._action_callbacks: Dict[InputAction, List[Callable[[], None]]] = {}
        self._continuous_callbacks: Dict[InputAction, List[Callable[[float], None]]] = {}
        self._state = InputState()
        self._prev_keys: Set[int] = set()
        self._prev_mouse: tuple = (False, False, False)
    
    def bind_key(self, key: int, action: InputAction) -> None:
        """Bind a key to an action.
        
        Args:
            key: Pygame key constant
            action: Action to trigger
        """
        self.keybindings[key] = action
    
    def unbind_key(self, key: int) -> None:
        """Remove a key binding.
        
        Args:
            key: Pygame key constant
        """
        self.keybindings.pop(key, None)
    
    def get_binding(self, action: InputAction) -> Optional[int]:
        """Get the key bound to an action.
        
        Args:
            action: The action to look up
            
        Returns:
            Key constant or None
        """
        for key, act in self.keybindings.items():
            if act == action:
                return key
        return None
    
    def on_action(self, action: InputAction, callback: Callable[[], None]) -> None:
        """Register a callback for when an action is triggered.
        
        Args:
            action: Action to listen for
            callback: Function to call (no arguments)
        """
        if action not in self._action_callbacks:
            self._action_callbacks[action] = []
        self._action_callbacks[action].append(callback)
    
    def on_continuous(self, action: InputAction, callback: Callable[[float], None]) -> None:
        """Register a callback for continuous action (called every frame while held).
        
        Args:
            action: Action to listen for
            callback: Function to call with delta time
        """
        if action not in self._continuous_callbacks:
            self._continuous_callbacks[action] = []
        self._continuous_callbacks[action].append(callback)
    
    def remove_callback(self, action: InputAction, callback: Callable) -> None:
        """Remove a callback.
        
        Args:
            action: Action the callback was registered for
            callback: The callback to remove
        """
        if action in self._action_callbacks:
            try:
                self._action_callbacks[action].remove(callback)
            except ValueError:
                pass
        if action in self._continuous_callbacks:
            try:
                self._continuous_callbacks[action].remove(callback)
            except ValueError:
                pass
    
    def update(self, dt: float) -> None:
        """Update input state and trigger callbacks.
        
        Args:
            dt: Delta time since last update
        """
        # Update key state
        current_keys = set()
        pressed_keys = pygame.key.get_pressed()
        for key in range(len(pressed_keys)):
            if pressed_keys[key]:
                current_keys.add(key)
        
        self._state.keys_just_pressed = current_keys - self._prev_keys
        self._state.keys_just_released = self._prev_keys - current_keys
        self._state.keys_pressed = current_keys
        
        # Update mouse state
        mouse_pos = pygame.mouse.get_pos()
        self._state.mouse_delta = (
            mouse_pos[0] - self._state.mouse_pos[0],
            mouse_pos[1] - self._state.mouse_pos[1],
        )
        self._state.mouse_pos = mouse_pos
        
        mouse_buttons = pygame.mouse.get_pressed()
        self._state.mouse_just_pressed = set()
        self._state.mouse_just_released = set()
        for i in range(3):
            if mouse_buttons[i] and not self._prev_mouse[i]:
                self._state.mouse_just_pressed.add(i)
            elif not mouse_buttons[i] and self._prev_mouse[i]:
                self._state.mouse_just_released.add(i)
        self._state.mouse_buttons = mouse_buttons
        
        # Trigger one-shot callbacks for just-pressed keys
        for key in self._state.keys_just_pressed:
            if key in self.keybindings:
                action = self.keybindings[key]
                for callback in self._action_callbacks.get(action, []):
                    callback()
        
        # Trigger continuous callbacks for held keys
        for key in self._state.keys_pressed:
            if key in self.keybindings:
                action = self.keybindings[key]
                for callback in self._continuous_callbacks.get(action, []):
                    callback(dt)
        
        # Store previous state
        self._prev_keys = current_keys
        self._prev_mouse = mouse_buttons
    
    def is_action_pressed(self, action: InputAction) -> bool:
        """Check if an action's key is currently pressed.
        
        Args:
            action: Action to check
            
        Returns:
            True if pressed
        """
        for key, act in self.keybindings.items():
            if act == action and key in self._state.keys_pressed:
                return True
        return False
    
    def is_action_just_pressed(self, action: InputAction) -> bool:
        """Check if an action was just triggered this frame.
        
        Args:
            action: Action to check
            
        Returns:
            True if just pressed
        """
        for key, act in self.keybindings.items():
            if act == action and key in self._state.keys_just_pressed:
                return True
        return False
    
    def get_mouse_delta(self) -> tuple:
        """Get mouse movement since last frame."""
        return self._state.mouse_delta
    
    def is_mouse_button_pressed(self, button: int) -> bool:
        """Check if a mouse button is pressed (0=left, 1=middle, 2=right)."""
        return self._state.mouse_buttons[button]
    
    def is_mouse_dragging(self, button: int = 0) -> bool:
        """Check if mouse is being dragged with button held."""
        return (
            self._state.mouse_buttons[button] and 
            (self._state.mouse_delta[0] != 0 or self._state.mouse_delta[1] != 0)
        )
    
    def get_keybindings_text(self) -> List[str]:
        """Get human-readable keybindings list.
        
        Returns:
            List of "Key: Action" strings
        """
        lines = []
        for key, action in sorted(self.keybindings.items(), key=lambda x: x[1].name):
            key_name = pygame.key.name(key).upper()
            action_name = action.name.replace("_", " ").title()
            lines.append(f"{key_name}: {action_name}")
        return lines
    
    def load_from_config(self, config: Dict[str, str]) -> None:
        """Load keybindings from a config dictionary.
        
        Args:
            config: Dict mapping action names to key names
        """
        for action_name, key_name in config.items():
            try:
                action = InputAction[action_name.upper()]
                key = getattr(pygame, f"K_{key_name.lower()}", None)
                if key is not None:
                    self.bind_key(key, action)
            except (KeyError, AttributeError):
                pass
    
    def save_to_config(self) -> Dict[str, str]:
        """Save keybindings to a config dictionary.
        
        Returns:
            Dict mapping action names to key names
        """
        config = {}
        for key, action in self.keybindings.items():
            key_name = pygame.key.name(key)
            config[action.name] = key_name
        return config
