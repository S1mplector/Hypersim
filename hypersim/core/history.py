"""Undo/Redo history system for 4D object manipulation.

Provides command pattern implementation for tracking and
reversing transformations on 4D objects.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, TYPE_CHECKING
import numpy as np
from copy import deepcopy

if TYPE_CHECKING:
    from .shape_4d import Shape4D


class Command(ABC):
    """Abstract base class for undoable commands."""
    
    @abstractmethod
    def execute(self) -> None:
        """Execute the command."""
        pass
    
    @abstractmethod
    def undo(self) -> None:
        """Undo the command."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of this command."""
        pass


@dataclass
class TransformCommand(Command):
    """Command for object transformations (position, rotation, scale)."""
    
    target: "Shape4D"
    transform_type: str  # "position", "rotation", "scale"
    old_value: Any
    new_value: Any
    
    def execute(self) -> None:
        if self.transform_type == "position":
            self.target.set_position(self.new_value)
        elif self.transform_type == "rotation":
            self.target.rotation = dict(self.new_value)
            self.target.invalidate_cache()
        elif self.transform_type == "scale":
            self.target.set_scale(self.new_value)
    
    def undo(self) -> None:
        if self.transform_type == "position":
            self.target.set_position(self.old_value)
        elif self.transform_type == "rotation":
            self.target.rotation = dict(self.old_value)
            self.target.invalidate_cache()
        elif self.transform_type == "scale":
            self.target.set_scale(self.old_value)
    
    @property
    def description(self) -> str:
        return f"Change {self.transform_type}"


@dataclass
class RotationCommand(Command):
    """Command for incremental rotation."""
    
    target: "Shape4D"
    angles: Dict[str, float]  # xy, xz, xw, yz, yw, zw
    
    def execute(self) -> None:
        self.target.rotate(**self.angles)
    
    def undo(self) -> None:
        # Reverse rotation
        reversed_angles = {k: -v for k, v in self.angles.items()}
        self.target.rotate(**reversed_angles)
    
    @property
    def description(self) -> str:
        planes = [k for k, v in self.angles.items() if v != 0]
        return f"Rotate in {', '.join(planes)}"


@dataclass  
class PropertyCommand(Command):
    """Command for changing object properties."""
    
    target: Any
    property_name: str
    old_value: Any
    new_value: Any
    
    def execute(self) -> None:
        setattr(self.target, self.property_name, self.new_value)
    
    def undo(self) -> None:
        setattr(self.target, self.property_name, self.old_value)
    
    @property
    def description(self) -> str:
        return f"Change {self.property_name}"


@dataclass
class CompositeCommand(Command):
    """Command that groups multiple commands."""
    
    commands: List[Command] = field(default_factory=list)
    _description: str = "Multiple changes"
    
    def add(self, command: Command) -> None:
        self.commands.append(command)
    
    def execute(self) -> None:
        for cmd in self.commands:
            cmd.execute()
    
    def undo(self) -> None:
        for cmd in reversed(self.commands):
            cmd.undo()
    
    @property
    def description(self) -> str:
        return self._description


class History:
    """Manages undo/redo history.
    
    Maintains a stack of commands that can be undone and redone.
    """
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self._callbacks: Dict[str, List[Callable]] = {
            'change': [],
            'undo': [],
            'redo': [],
        }
    
    def execute(self, command: Command) -> None:
        """Execute a command and add it to history.
        
        Args:
            command: The command to execute
        """
        command.execute()
        self._undo_stack.append(command)
        self._redo_stack.clear()  # Clear redo stack on new command
        
        # Trim history if too long
        while len(self._undo_stack) > self.max_history:
            self._undo_stack.pop(0)
        
        self._trigger_callbacks('change')
    
    def undo(self) -> bool:
        """Undo the last command.
        
        Returns:
            True if a command was undone
        """
        if not self._undo_stack:
            return False
        
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        
        self._trigger_callbacks('undo')
        self._trigger_callbacks('change')
        
        return True
    
    def redo(self) -> bool:
        """Redo the last undone command.
        
        Returns:
            True if a command was redone
        """
        if not self._redo_stack:
            return False
        
        command = self._redo_stack.pop()
        command.execute()
        self._undo_stack.append(command)
        
        self._trigger_callbacks('redo')
        self._trigger_callbacks('change')
        
        return True
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0
    
    @property
    def undo_description(self) -> Optional[str]:
        """Get description of command that would be undone."""
        if self._undo_stack:
            return self._undo_stack[-1].description
        return None
    
    @property
    def redo_description(self) -> Optional[str]:
        """Get description of command that would be redone."""
        if self._redo_stack:
            return self._redo_stack[-1].description
        return None
    
    def clear(self) -> None:
        """Clear all history."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._trigger_callbacks('change')
    
    def on(self, event: str, callback: Callable) -> None:
        """Register a callback for history events.
        
        Args:
            event: Event name ('change', 'undo', 'redo')
            callback: Function to call
        """
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def off(self, event: str, callback: Callable) -> None:
        """Remove a callback."""
        if event in self._callbacks and callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)
    
    def _trigger_callbacks(self, event: str) -> None:
        """Trigger callbacks for an event."""
        for callback in self._callbacks.get(event, []):
            try:
                callback()
            except Exception:
                pass
    
    @property
    def undo_count(self) -> int:
        """Number of undoable commands."""
        return len(self._undo_stack)
    
    @property
    def redo_count(self) -> int:
        """Number of redoable commands."""
        return len(self._redo_stack)
    
    def get_history_list(self, max_items: int = 10) -> List[str]:
        """Get a list of recent command descriptions.
        
        Args:
            max_items: Maximum number of items to return
            
        Returns:
            List of command descriptions (most recent first)
        """
        items = []
        for cmd in reversed(self._undo_stack[-max_items:]):
            items.append(cmd.description)
        return items


class TransactionContext:
    """Context manager for grouping commands into a transaction.
    
    Usage:
        with TransactionContext(history, "Move and rotate") as tx:
            history.execute(move_cmd)
            history.execute(rotate_cmd)
    
    All commands within the context are grouped as one undoable action.
    """
    
    def __init__(self, history: History, description: str = "Transaction"):
        self.history = history
        self.description = description
        self._commands: List[Command] = []
        self._original_execute = None
    
    def __enter__(self) -> "TransactionContext":
        # Temporarily replace execute to capture commands
        self._original_execute = self.history.execute
        self.history.execute = self._capture_command
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # Restore original execute
        self.history.execute = self._original_execute
        
        # If no exception, create composite command
        if exc_type is None and self._commands:
            composite = CompositeCommand(
                commands=self._commands,
                _description=self.description,
            )
            self._original_execute(composite)
        
        return False
    
    def _capture_command(self, command: Command) -> None:
        """Capture a command without adding to history."""
        command.execute()
        self._commands.append(command)


# Convenience functions for common operations

def record_position_change(
    history: History,
    target: "Shape4D",
    old_pos: np.ndarray,
    new_pos: np.ndarray,
) -> None:
    """Record a position change in history."""
    cmd = TransformCommand(
        target=target,
        transform_type="position",
        old_value=old_pos.copy(),
        new_value=new_pos.copy(),
    )
    history.execute(cmd)


def record_rotation(
    history: History,
    target: "Shape4D",
    **angles: float,
) -> None:
    """Record a rotation in history."""
    cmd = RotationCommand(target=target, angles=angles)
    history.execute(cmd)


def record_scale_change(
    history: History,
    target: "Shape4D",
    old_scale: float,
    new_scale: float,
) -> None:
    """Record a scale change in history."""
    cmd = TransformCommand(
        target=target,
        transform_type="scale",
        old_value=old_scale,
        new_value=new_scale,
    )
    history.execute(cmd)
