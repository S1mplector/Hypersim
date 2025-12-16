"""Basic 4D object editor for interactive manipulation.

Provides tools for editing 4D objects including:
- Transform gizmos (move, rotate, scale)
- Vertex editing
- Property panels
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, List, Optional, Tuple, Callable, Dict, Any
import numpy as np
import pygame

if TYPE_CHECKING:
    from hypersim.core.shape_4d import Shape4D

from hypersim.core.history import History, TransformCommand, RotationCommand


class EditMode(Enum):
    """Editor modes."""
    SELECT = auto()
    MOVE = auto()
    ROTATE = auto()
    SCALE = auto()
    VERTEX = auto()


class Axis(Enum):
    """Axes for constrained manipulation."""
    X = auto()
    Y = auto()
    Z = auto()
    W = auto()
    XY = auto()
    XZ = auto()
    XW = auto()
    YZ = auto()
    YW = auto()
    ZW = auto()
    FREE = auto()


@dataclass
class SelectionInfo:
    """Information about current selection."""
    objects: List["Shape4D"] = field(default_factory=list)
    vertices: List[int] = field(default_factory=list)  # Selected vertex indices
    
    @property
    def has_selection(self) -> bool:
        return len(self.objects) > 0
    
    @property
    def single_object(self) -> Optional["Shape4D"]:
        return self.objects[0] if len(self.objects) == 1 else None
    
    def clear(self) -> None:
        self.objects.clear()
        self.vertices.clear()
    
    def add_object(self, obj: "Shape4D") -> None:
        if obj not in self.objects:
            self.objects.append(obj)
    
    def remove_object(self, obj: "Shape4D") -> None:
        if obj in self.objects:
            self.objects.remove(obj)
    
    def toggle_object(self, obj: "Shape4D") -> None:
        if obj in self.objects:
            self.objects.remove(obj)
        else:
            self.objects.append(obj)


@dataclass
class GizmoConfig:
    """Configuration for transform gizmos."""
    size: float = 80.0
    line_width: int = 3
    hover_width: int = 5
    colors: Dict[str, Tuple[int, int, int]] = field(default_factory=lambda: {
        'x': (255, 80, 80),
        'y': (80, 255, 80),
        'z': (80, 80, 255),
        'w': (255, 200, 80),
        'hover': (255, 255, 100),
        'active': (255, 255, 255),
    })


class TransformGizmo:
    """Visual gizmo for object transformation."""
    
    def __init__(self, config: Optional[GizmoConfig] = None):
        self.config = config or GizmoConfig()
        self.visible = True
        self.mode = EditMode.MOVE
        self.active_axis: Optional[Axis] = None
        self.hovered_axis: Optional[Axis] = None
        
        self._drag_start: Optional[Tuple[int, int]] = None
        self._drag_start_value: Any = None
    
    def draw(
        self,
        surface: pygame.Surface,
        center: Tuple[int, int],
        scale: float = 1.0,
    ) -> None:
        """Draw the gizmo at a screen position."""
        if not self.visible:
            return
        
        cfg = self.config
        size = cfg.size * scale
        
        if self.mode == EditMode.MOVE:
            self._draw_move_gizmo(surface, center, size)
        elif self.mode == EditMode.ROTATE:
            self._draw_rotate_gizmo(surface, center, size)
        elif self.mode == EditMode.SCALE:
            self._draw_scale_gizmo(surface, center, size)
    
    def _draw_move_gizmo(
        self,
        surface: pygame.Surface,
        center: Tuple[int, int],
        size: float,
    ) -> None:
        """Draw translation arrows."""
        cfg = self.config
        cx, cy = center
        
        # Draw axes
        axes = [
            (Axis.X, (1, 0), cfg.colors['x']),
            (Axis.Y, (0, -1), cfg.colors['y']),
            (Axis.Z, (0.7, 0.7), cfg.colors['z']),
        ]
        
        for axis, (dx, dy), color in axes:
            end_x = cx + dx * size
            end_y = cy + dy * size
            
            width = cfg.hover_width if self.hovered_axis == axis else cfg.line_width
            if self.active_axis == axis:
                color = cfg.colors['active']
            elif self.hovered_axis == axis:
                color = cfg.colors['hover']
            
            # Line
            pygame.draw.line(surface, color, center, (end_x, end_y), width)
            
            # Arrow head
            arrow_size = 10
            pygame.draw.polygon(surface, color, [
                (end_x, end_y),
                (end_x - dx * arrow_size - dy * arrow_size * 0.5,
                 end_y - dy * arrow_size + dx * arrow_size * 0.5),
                (end_x - dx * arrow_size + dy * arrow_size * 0.5,
                 end_y - dy * arrow_size - dx * arrow_size * 0.5),
            ])
        
        # W axis (special - shown as circle)
        w_color = cfg.colors['w']
        if self.hovered_axis == Axis.W:
            w_color = cfg.colors['hover']
        pygame.draw.circle(surface, w_color, center, 12, 2)
    
    def _draw_rotate_gizmo(
        self,
        surface: pygame.Surface,
        center: Tuple[int, int],
        size: float,
    ) -> None:
        """Draw rotation circles."""
        cfg = self.config
        
        # Draw rotation rings for different planes
        planes = [
            (Axis.XY, cfg.colors['z'], 0),
            (Axis.XZ, cfg.colors['y'], 1),
            (Axis.YZ, cfg.colors['x'], 2),
        ]
        
        for axis, color, offset in planes:
            width = cfg.hover_width if self.hovered_axis == axis else cfg.line_width
            if self.active_axis == axis:
                color = cfg.colors['active']
            elif self.hovered_axis == axis:
                color = cfg.colors['hover']
            
            # Draw ellipse to suggest 3D
            rect = pygame.Rect(
                center[0] - size + offset * 5,
                center[1] - size * 0.3 + offset * 10,
                size * 2,
                size * 0.6,
            )
            pygame.draw.ellipse(surface, color, rect, width)
    
    def _draw_scale_gizmo(
        self,
        surface: pygame.Surface,
        center: Tuple[int, int],
        size: float,
    ) -> None:
        """Draw scale handles."""
        cfg = self.config
        cx, cy = center
        
        # Similar to move but with boxes at ends
        axes = [
            (Axis.X, (1, 0), cfg.colors['x']),
            (Axis.Y, (0, -1), cfg.colors['y']),
            (Axis.Z, (0.7, 0.7), cfg.colors['z']),
        ]
        
        for axis, (dx, dy), color in axes:
            end_x = cx + dx * size
            end_y = cy + dy * size
            
            width = cfg.hover_width if self.hovered_axis == axis else cfg.line_width
            if self.active_axis == axis:
                color = cfg.colors['active']
            elif self.hovered_axis == axis:
                color = cfg.colors['hover']
            
            # Line
            pygame.draw.line(surface, color, center, (end_x, end_y), width)
            
            # Box at end
            box_size = 8
            pygame.draw.rect(surface, color, (
                end_x - box_size // 2,
                end_y - box_size // 2,
                box_size, box_size,
            ))
        
        # Center cube for uniform scale
        center_color = cfg.colors['w'] if self.hovered_axis != Axis.FREE else cfg.colors['hover']
        pygame.draw.rect(surface, center_color, (cx - 6, cy - 6, 12, 12))
    
    def hit_test(
        self,
        pos: Tuple[int, int],
        center: Tuple[int, int],
        scale: float = 1.0,
    ) -> Optional[Axis]:
        """Test if a screen position hits any axis."""
        size = self.config.size * scale
        cx, cy = center
        px, py = pos
        
        # Check each axis
        threshold = 15
        
        if self.mode in (EditMode.MOVE, EditMode.SCALE):
            # X axis
            if cy - threshold < py < cy + threshold and cx < px < cx + size + threshold:
                return Axis.X
            # Y axis
            if cx - threshold < px < cx + threshold and cy - size - threshold < py < cy:
                return Axis.Y
            # Z axis (diagonal)
            dist_to_z = abs((px - cx) - (py - cy) * 0.7 / 0.7)
            if dist_to_z < threshold and px > cx and py > cy:
                return Axis.Z
            # W (center)
            if (px - cx) ** 2 + (py - cy) ** 2 < 20 ** 2:
                return Axis.W if self.mode == EditMode.MOVE else Axis.FREE
        
        elif self.mode == EditMode.ROTATE:
            # Check distance from center (ring hit test)
            dist = np.sqrt((px - cx) ** 2 + (py - cy) ** 2)
            if size * 0.8 < dist < size * 1.2:
                return Axis.XY  # Simplified - would need better ring detection
        
        return None
    
    def begin_drag(self, pos: Tuple[int, int], axis: Axis) -> None:
        """Start a drag operation."""
        self.active_axis = axis
        self._drag_start = pos
    
    def end_drag(self) -> None:
        """End a drag operation."""
        self.active_axis = None
        self._drag_start = None
        self._drag_start_value = None
    
    def get_drag_delta(
        self,
        current_pos: Tuple[int, int],
        sensitivity: float = 0.01,
    ) -> np.ndarray:
        """Get transformation delta from drag."""
        if self._drag_start is None or self.active_axis is None:
            return np.zeros(4)
        
        dx = current_pos[0] - self._drag_start[0]
        dy = current_pos[1] - self._drag_start[1]
        
        delta = np.zeros(4, dtype=np.float32)
        
        if self.active_axis == Axis.X:
            delta[0] = dx * sensitivity
        elif self.active_axis == Axis.Y:
            delta[1] = -dy * sensitivity
        elif self.active_axis == Axis.Z:
            delta[2] = (dx + dy) * sensitivity * 0.5
        elif self.active_axis == Axis.W:
            delta[3] = dy * sensitivity
        elif self.active_axis == Axis.FREE:
            # Uniform
            delta[:] = (dx - dy) * sensitivity * 0.5
        
        return delta


class ObjectEditor:
    """Main editor class for manipulating 4D objects."""
    
    def __init__(self):
        self.selection = SelectionInfo()
        self.gizmo = TransformGizmo()
        self.history = History()
        self.mode = EditMode.SELECT
        
        # Callbacks
        self.on_selection_changed: Optional[Callable[[SelectionInfo], None]] = None
        self.on_transform_changed: Optional[Callable[["Shape4D"], None]] = None
        
        # State
        self._is_dragging = False
        self._drag_start_pos: Optional[np.ndarray] = None
        self._snap_enabled = False
        self._snap_increment = 0.25
    
    def set_mode(self, mode: EditMode) -> None:
        """Set the current edit mode."""
        self.mode = mode
        self.gizmo.mode = mode
        self.gizmo.end_drag()
    
    def select(self, obj: "Shape4D", add: bool = False) -> None:
        """Select an object."""
        if not add:
            self.selection.clear()
        self.selection.add_object(obj)
        
        if self.on_selection_changed:
            self.on_selection_changed(self.selection)
    
    def deselect(self, obj: "Shape4D") -> None:
        """Deselect an object."""
        self.selection.remove_object(obj)
        
        if self.on_selection_changed:
            self.on_selection_changed(self.selection)
    
    def clear_selection(self) -> None:
        """Clear selection."""
        self.selection.clear()
        
        if self.on_selection_changed:
            self.on_selection_changed(self.selection)
    
    def handle_mouse_down(
        self,
        pos: Tuple[int, int],
        button: int,
        gizmo_center: Optional[Tuple[int, int]] = None,
    ) -> bool:
        """Handle mouse down event.
        
        Returns True if the event was handled.
        """
        if button != 1:  # Left click only
            return False
        
        # Check gizmo hit
        if gizmo_center and self.selection.has_selection:
            axis = self.gizmo.hit_test(pos, gizmo_center)
            if axis:
                self.gizmo.begin_drag(pos, axis)
                self._is_dragging = True
                
                # Store starting values for undo
                obj = self.selection.single_object
                if obj:
                    self._drag_start_pos = obj.position.copy()
                
                return True
        
        return False
    
    def handle_mouse_move(
        self,
        pos: Tuple[int, int],
        gizmo_center: Optional[Tuple[int, int]] = None,
    ) -> None:
        """Handle mouse move event."""
        # Update gizmo hover state
        if gizmo_center:
            self.gizmo.hovered_axis = self.gizmo.hit_test(pos, gizmo_center)
        
        # Handle drag
        if self._is_dragging and self.selection.single_object:
            obj = self.selection.single_object
            delta = self.gizmo.get_drag_delta(pos)
            
            if self.mode == EditMode.MOVE:
                new_pos = self._drag_start_pos + delta * 10  # Scale delta
                if self._snap_enabled:
                    new_pos = np.round(new_pos / self._snap_increment) * self._snap_increment
                obj.set_position(new_pos)
            
            elif self.mode == EditMode.ROTATE:
                rotation_delta = delta * 0.5  # Convert to rotation
                if self.gizmo.active_axis == Axis.XY:
                    obj.rotate(xy=rotation_delta[0])
                elif self.gizmo.active_axis == Axis.XZ:
                    obj.rotate(xz=rotation_delta[1])
                elif self.gizmo.active_axis == Axis.YZ:
                    obj.rotate(yz=rotation_delta[2])
            
            elif self.mode == EditMode.SCALE:
                scale_factor = 1.0 + delta[0]
                if self.gizmo.active_axis == Axis.FREE:
                    obj.set_scale(obj.scale * scale_factor)
            
            if self.on_transform_changed:
                self.on_transform_changed(obj)
    
    def handle_mouse_up(self, pos: Tuple[int, int], button: int) -> None:
        """Handle mouse up event."""
        if button == 1 and self._is_dragging:
            # Record change in history
            obj = self.selection.single_object
            if obj and self._drag_start_pos is not None:
                if self.mode == EditMode.MOVE:
                    cmd = TransformCommand(
                        target=obj,
                        transform_type="position",
                        old_value=self._drag_start_pos.copy(),
                        new_value=obj.position.copy(),
                    )
                    # Don't execute - already applied
                    self.history._undo_stack.append(cmd)
                    self.history._redo_stack.clear()
            
            self._is_dragging = False
            self._drag_start_pos = None
            self.gizmo.end_drag()
    
    def handle_key(self, key: int) -> bool:
        """Handle keyboard input.
        
        Returns True if the event was handled.
        """
        # Mode shortcuts
        if key == pygame.K_g:
            self.set_mode(EditMode.MOVE)
            return True
        elif key == pygame.K_r:
            self.set_mode(EditMode.ROTATE)
            return True
        elif key == pygame.K_s:
            self.set_mode(EditMode.SCALE)
            return True
        
        # Undo/Redo
        elif key == pygame.K_z:
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_CTRL:
                if mods & pygame.KMOD_SHIFT:
                    self.history.redo()
                else:
                    self.history.undo()
                return True
        elif key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.history.redo()
            return True
        
        # Delete selection
        elif key == pygame.K_DELETE or key == pygame.K_x:
            if self.selection.has_selection:
                self.selection.clear()
                return True
        
        # Snap toggle
        elif key == pygame.K_x:
            self._snap_enabled = not self._snap_enabled
            return True
        
        return False
    
    def draw_gizmo(
        self,
        surface: pygame.Surface,
        project_func: Callable[[np.ndarray], Tuple[int, int]],
    ) -> None:
        """Draw the transform gizmo for selected objects."""
        if not self.selection.has_selection:
            return
        
        obj = self.selection.single_object
        if obj is None:
            return
        
        # Get screen position of object center
        center_4d = obj.position
        center_2d = project_func(center_4d)
        
        self.gizmo.draw(surface, center_2d)
    
    def get_properties(self) -> Dict[str, Any]:
        """Get properties of selected object for display."""
        obj = self.selection.single_object
        if obj is None:
            return {}
        
        return {
            "Position": {
                "X": obj.position[0],
                "Y": obj.position[1],
                "Z": obj.position[2],
                "W": obj.position[3],
            },
            "Rotation": obj.rotation.copy(),
            "Scale": obj.scale,
            "Vertices": obj.vertex_count,
            "Edges": obj.edge_count,
        }
    
    def set_property(self, name: str, value: Any) -> None:
        """Set a property on the selected object."""
        obj = self.selection.single_object
        if obj is None:
            return
        
        if name == "scale":
            old = obj.scale
            obj.set_scale(value)
            cmd = TransformCommand(obj, "scale", old, value)
            self.history._undo_stack.append(cmd)
        
        if self.on_transform_changed:
            self.on_transform_changed(obj)
