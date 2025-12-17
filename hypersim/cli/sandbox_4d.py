"""Immersive 4D Sandbox - Explore 4D space as a 4D being.

4D MATH OVERVIEW
================

In 4D space, we have 4 perpendicular axes: X, Y, Z, W.
- X: left/right
- Y: up/down  
- Z: forward/backward
- W: ana/kata (the 4th dimension - perpendicular to all 3D directions)

ROTATIONS IN 4D
---------------
In 3D, rotation happens around an axis (a line).
In 4D, rotation happens in a PLANE. There are 6 rotation planes:
- XY plane: rotation in the familiar horizontal plane
- XZ plane: yaw (looking left/right)
- YZ plane: pitch (looking up/down)
- XW plane: rotating between X and W (4D yaw)
- YW plane: rotating between Y and W (4D pitch)
- ZW plane: rotating between Z and W (4D roll)

4D PERSPECTIVE PROJECTION
-------------------------
Just as 3D->2D projection divides by Z (depth), 4D->3D projection divides by W.
Points with larger W appear smaller (further away in 4D).
This is how a 4D being would "see" - with W as the depth axis.

CONTROLS
--------
- WASD/Arrows: Move horizontally (X) and forward/back (Z)
- Space/Shift: Move up/down (Y)
- Q/E: Move in W dimension (ana/kata - the 4th dimension!)
- Mouse: Look around (XZ and YZ rotation - like a normal FPS)
- Scroll: Adjust W position smoothly
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any

import numpy as np
import pygame

from hypersim.objects import (
    Hypercube, SixteenCell, TwentyFourCell, Duoprism,
    Pentachoron, OneHundredTwentyCell, SixHundredCell, GrandAntiprism,
    CliffordTorus,
)


# =============================================================================
# 4D ROTATION MATRICES
# =============================================================================

def rotation_matrix_4d(plane: str, angle: float) -> np.ndarray:
    """Create a 4D rotation matrix for rotation in a given plane.
    
    In 4D, rotation occurs in a 2D plane, not around an axis.
    There are 6 possible rotation planes: XY, XZ, XW, YZ, YW, ZW.
    
    Args:
        plane: One of 'xy', 'xz', 'xw', 'yz', 'yw', 'zw'
        angle: Rotation angle in radians
    
    Returns:
        4x4 rotation matrix
    """
    c, s = np.cos(angle), np.sin(angle)
    m = np.eye(4, dtype=np.float64)
    
    # Map plane to axis indices
    plane_map = {
        'xy': (0, 1), 'xz': (0, 2), 'xw': (0, 3),
        'yz': (1, 2), 'yw': (1, 3), 'zw': (2, 3)
    }
    
    if plane in plane_map:
        i, j = plane_map[plane]
        m[i, i] = c
        m[i, j] = -s
        m[j, i] = s
        m[j, j] = c
    
    return m


# =============================================================================
# 4D CAMERA
# =============================================================================

@dataclass
class Camera4D:
    """A first-person camera in 4D space.
    
    The camera uses two angles for 3D-style mouse look (yaw/pitch),
    plus additional angles for 4D rotation when needed.
    
    Coordinate system:
    - Looking along +Z by default
    - Y is up
    - X is right
    - W is the 4th dimension (ana/kata)
    """
    # Position in 4D
    position: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0, -10.0, 0.0]))
    
    # Standard FPS angles (in radians)
    yaw: float = 0.0    # Rotation around Y axis (left/right look)
    pitch: float = 0.0  # Rotation around X axis (up/down look)
    
    # 4D rotation angles
    roll_4d: float = 0.0   # XW rotation (4D left/right)
    pitch_4d: float = 0.0  # YW rotation (4D up/down)
    
    # Settings
    move_speed: float = 5.0
    look_sensitivity: float = 0.002
    fov: float = 2.0  # Field of view for 4D projection
    
    def get_view_matrix(self) -> np.ndarray:
        """Get the combined view rotation matrix."""
        # Apply rotations: first yaw (XZ), then pitch (YZ), then 4D rotations
        m = np.eye(4, dtype=np.float64)
        m = m @ rotation_matrix_4d('xz', self.yaw)
        m = m @ rotation_matrix_4d('yz', self.pitch)
        m = m @ rotation_matrix_4d('xw', self.roll_4d)
        m = m @ rotation_matrix_4d('yw', self.pitch_4d)
        return m
    
    def get_forward(self) -> np.ndarray:
        """Get the forward direction vector (where camera is looking in XYZ)."""
        # Forward is +Z, rotated by yaw and pitch
        forward = np.array([0.0, 0.0, 1.0, 0.0])
        m = rotation_matrix_4d('xz', self.yaw) @ rotation_matrix_4d('yz', self.pitch)
        return m @ forward
    
    def get_right(self) -> np.ndarray:
        """Get the right direction vector."""
        right = np.array([1.0, 0.0, 0.0, 0.0])
        m = rotation_matrix_4d('xz', self.yaw)
        return m @ right
    
    def get_up(self) -> np.ndarray:
        """Get the up direction vector."""
        return np.array([0.0, 1.0, 0.0, 0.0])
    
    def get_ana(self) -> np.ndarray:
        """Get the ana direction (into 4D, +W direction in camera space)."""
        ana = np.array([0.0, 0.0, 0.0, 1.0])
        m = rotation_matrix_4d('xw', self.roll_4d) @ rotation_matrix_4d('yw', self.pitch_4d)
        return m @ ana
    
    def move(self, forward: float, right: float, up: float, ana: float, dt: float) -> None:
        """Move the camera relative to its orientation."""
        velocity = np.zeros(4)
        
        if forward != 0:
            velocity += self.get_forward() * forward
        if right != 0:
            velocity += self.get_right() * right
        if up != 0:
            velocity += self.get_up() * up
        if ana != 0:
            velocity += self.get_ana() * ana
        
        if np.any(velocity != 0):
            # Normalize to prevent faster diagonal movement
            velocity = velocity / np.linalg.norm(velocity)
            self.position += velocity * self.move_speed * dt
    
    def look(self, dx: float, dy: float) -> None:
        """Rotate the camera based on mouse movement."""
        self.yaw -= dx * self.look_sensitivity
        self.pitch -= dy * self.look_sensitivity
        
        # Clamp pitch to avoid gimbal lock
        self.pitch = np.clip(self.pitch, -np.pi/2 + 0.1, np.pi/2 - 0.1)
    
    def project_point(self, point: np.ndarray, screen_w: int, screen_h: int) -> Optional[Tuple[int, int, float]]:
        """Project a 4D point to 2D screen coordinates.
        
        This implements true 4D perspective projection:
        1. Transform point to camera space
        2. Apply 4D perspective (divide by W)
        3. Apply 3D perspective (divide by Z)
        4. Map to screen coordinates
        
        Returns (screen_x, screen_y, depth) or None if behind camera.
        """
        # Transform to camera space
        relative = point - self.position
        view_matrix = self.get_view_matrix().T  # Inverse rotation
        cam_point = view_matrix @ relative
        
        x, y, z, w = cam_point
        
        # 4D perspective: divide by W (with offset to avoid division by zero)
        # Objects at W=0 (same W as camera) appear at natural size
        # Objects at W>0 appear smaller (further in 4D)
        w_depth = w + 3.0  # Offset so W=0 maps to reasonable depth
        if w_depth < 0.1:
            return None  # Behind camera in 4D
        
        scale_4d = self.fov / w_depth
        x3d = x * scale_4d
        y3d = y * scale_4d
        z3d = z * scale_4d
        
        # 3D perspective: divide by Z
        z_depth = z3d + 5.0  # Offset for 3D depth
        if z_depth < 0.1:
            return None  # Behind camera in 3D
        
        scale_3d = self.fov / z_depth
        x2d = x3d * scale_3d
        y2d = y3d * scale_3d
        
        # Map to screen (Y is flipped, centered)
        screen_x = int(screen_w / 2 + x2d * 200)
        screen_y = int(screen_h / 2 - y2d * 200)
        
        # Combined depth for sorting
        depth = w_depth + z_depth * 0.1
        
        return (screen_x, screen_y, depth)


# =============================================================================
# 3D OBJECTS (embedded in 4D)
# =============================================================================

class Object3D:
    """A 3D object embedded in 4D space at a fixed W coordinate."""
    
    def __init__(self, vertices: List[List[float]], edges: List[Tuple[int, int]]):
        self.vertices_3d = np.array(vertices, dtype=np.float64)
        self.edges = edges
        self.position = np.zeros(4, dtype=np.float64)
        self.scale = 1.0
        self.color = (200, 200, 200)
    
    def get_vertices_4d(self) -> np.ndarray:
        """Get vertices as 4D points (W = position[3])."""
        n = len(self.vertices_3d)
        verts = np.zeros((n, 4), dtype=np.float64)
        verts[:, :3] = self.vertices_3d * self.scale
        verts += self.position
        return verts


def make_cube_3d(size: float = 1.0) -> Object3D:
    """Create a 3D cube."""
    s = size / 2
    verts = [
        [-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s],
        [-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s],
    ]
    edges = [
        (0,1), (1,2), (2,3), (3,0),
        (4,5), (5,6), (6,7), (7,4),
        (0,4), (1,5), (2,6), (3,7),
    ]
    return Object3D(verts, edges)


def make_tetrahedron_3d(size: float = 1.0) -> Object3D:
    """Create a 3D tetrahedron."""
    s = size * 0.6
    verts = [[s,s,s], [s,-s,-s], [-s,s,-s], [-s,-s,s]]
    edges = [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3)]
    return Object3D(verts, edges)


def make_octahedron_3d(size: float = 1.0) -> Object3D:
    """Create a 3D octahedron."""
    s = size
    verts = [[s,0,0], [-s,0,0], [0,s,0], [0,-s,0], [0,0,s], [0,0,-s]]
    edges = [
        (0,2), (0,3), (0,4), (0,5),
        (1,2), (1,3), (1,4), (1,5),
        (2,4), (2,5), (3,4), (3,5),
    ]
    return Object3D(verts, edges)


# =============================================================================
# WORLD OBJECT WRAPPER
# =============================================================================

@dataclass
class WorldObject:
    """An object in the sandbox world."""
    obj: Any
    is_3d: bool = False
    color: Tuple[int, int, int] = (100, 200, 255)
    position: np.ndarray = field(default_factory=lambda: np.zeros(4))
    
    def get_vertices(self) -> np.ndarray:
        if self.is_3d:
            return self.obj.get_vertices_4d()
        else:
            verts = np.array(self.obj.get_transformed_vertices(), dtype=np.float64)
            return verts + self.position
    
    def get_edges(self) -> List[Tuple[int, int]]:
        return list(self.obj.edges)


# =============================================================================
# SANDBOX APPLICATION
# =============================================================================

class Sandbox4D:
    """The immersive 4D sandbox."""
    
    def __init__(self, width: int = 1400, height: int = 900):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("HyperSim 4D Sandbox")
        self.clock = pygame.time.Clock()
        
        # Camera
        self.camera = Camera4D()
        self.camera.position = np.array([0.0, 0.0, -8.0, 0.0])
        
        # World
        self.objects: List[WorldObject] = []
        self.spawn_distance = 5.0
        self.spawn_size = 1.0
        
        # Input
        self.keys_held: Dict[int, bool] = {}
        self.mouse_captured = False
        
        # UI
        self.show_help = True
        self.show_hud = True
        self.show_grid = True
        
        # Fonts
        self.font = pygame.font.SysFont("Arial", 16)
        self.font_large = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 14)
        
        # Colors
        self.colors_4d = [
            (100, 180, 255), (255, 150, 100), (150, 255, 150),
            (255, 200, 100), (200, 150, 255), (255, 150, 200),
        ]
        self.colors_3d = [
            (255, 100, 100), (100, 255, 100), (100, 100, 255),
        ]
        
        # Spawn default scene
        self._spawn_defaults()
    
    def _init_from_app(self) -> None:
        """Initialize when launched from master app."""
        pygame.display.set_caption("HyperSim 4D Sandbox")
        
        self.camera = Camera4D()
        self.camera.position = np.array([0.0, 0.0, -8.0, 0.0])
        
        self.objects = []
        self.spawn_distance = 5.0
        self.spawn_size = 1.0
        
        self.keys_held = {}
        self.mouse_captured = False
        
        self.show_help = True
        self.show_hud = True
        self.show_grid = True
        
        self.font = pygame.font.SysFont("Arial", 16)
        self.font_large = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 14)
        
        self.colors_4d = [
            (100, 180, 255), (255, 150, 100), (150, 255, 150),
            (255, 200, 100), (200, 150, 255), (255, 150, 200),
        ]
        self.colors_3d = [
            (255, 100, 100), (100, 255, 100), (100, 100, 255),
        ]
        
        self._spawn_defaults()
    
    def _spawn_defaults(self) -> None:
        """Spawn default objects."""
        # Tesseract at origin
        cube = Hypercube(size=1.5)
        self.objects.append(WorldObject(
            obj=cube, is_3d=False,
            color=(100, 180, 255),
            position=np.array([0.0, 0.0, 0.0, 0.0])
        ))
        
        # 3D cube offset in X (to show difference)
        cube_3d = make_cube_3d(1.0)
        cube_3d.position = np.array([4.0, 0.0, 0.0, 0.0])
        cube_3d.color = (255, 150, 100)
        self.objects.append(WorldObject(
            obj=cube_3d, is_3d=True,
            color=(255, 150, 100),
            position=np.array([4.0, 0.0, 0.0, 0.0])
        ))
    
    def spawn_4d(self, name: str) -> None:
        """Spawn a 4D object in front of camera."""
        pos = self.camera.position + self.camera.get_forward() * self.spawn_distance
        
        factories = {
            "tesseract": lambda: Hypercube(size=self.spawn_size),
            "16cell": lambda: SixteenCell(size=self.spawn_size),
            "24cell": lambda: TwentyFourCell(size=self.spawn_size * 0.8),
            "5cell": lambda: Pentachoron(size=self.spawn_size * 1.2),
            "600cell": lambda: SixHundredCell(size=self.spawn_size * 0.5),
            "duoprism": lambda: Duoprism(m=4, n=5, size=self.spawn_size),
            "clifford": lambda: CliffordTorus(size=self.spawn_size),
        }
        
        if name in factories:
            obj = factories[name]()
            self.objects.append(WorldObject(
                obj=obj, is_3d=False,
                color=random.choice(self.colors_4d),
                position=pos.copy()
            ))
    
    def spawn_3d(self, name: str) -> None:
        """Spawn a 3D object in front of camera."""
        pos = self.camera.position + self.camera.get_forward() * self.spawn_distance
        
        factories = {
            "cube": lambda: make_cube_3d(self.spawn_size),
            "tetra": lambda: make_tetrahedron_3d(self.spawn_size),
            "octa": lambda: make_octahedron_3d(self.spawn_size),
        }
        
        if name in factories:
            obj = factories[name]()
            obj.position = pos.copy()
            obj.color = random.choice(self.colors_3d)
            self.objects.append(WorldObject(
                obj=obj, is_3d=True,
                color=obj.color,
                position=pos.copy()
            ))
    
    def handle_input(self, dt: float) -> bool:
        """Handle input. Returns False to quit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                self.keys_held[event.key] = True
                
                if event.key == pygame.K_ESCAPE:
                    if self.mouse_captured:
                        self._release_mouse()
                    else:
                        return False
                
                # Toggle mouse capture
                elif event.key == pygame.K_TAB:
                    if self.mouse_captured:
                        self._release_mouse()
                    else:
                        self._capture_mouse()
                
                # UI toggles
                elif event.key == pygame.K_h:
                    self.show_help = not self.show_help
                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid
                
                # Object management
                elif event.key == pygame.K_BACKSPACE:
                    if self.objects:
                        self.objects.pop()
                elif event.key == pygame.K_DELETE:
                    self.objects.clear()
                
                # Spawn 4D (number keys)
                elif event.key == pygame.K_1:
                    self.spawn_4d("tesseract")
                elif event.key == pygame.K_2:
                    self.spawn_4d("16cell")
                elif event.key == pygame.K_3:
                    self.spawn_4d("24cell")
                elif event.key == pygame.K_4:
                    self.spawn_4d("5cell")
                elif event.key == pygame.K_5:
                    self.spawn_4d("600cell")
                elif event.key == pygame.K_6:
                    self.spawn_4d("duoprism")
                elif event.key == pygame.K_7:
                    self.spawn_4d("clifford")
                
                # Spawn 3D (F keys)
                elif event.key == pygame.K_F1:
                    self.spawn_3d("cube")
                elif event.key == pygame.K_F2:
                    self.spawn_3d("tetra")
                elif event.key == pygame.K_F3:
                    self.spawn_3d("octa")
                
                # Size
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                    self.spawn_size = min(3.0, self.spawn_size + 0.2)
                elif event.key == pygame.K_MINUS:
                    self.spawn_size = max(0.2, self.spawn_size - 0.2)
            
            elif event.type == pygame.KEYUP:
                self.keys_held[event.key] = False
            
            elif event.type == pygame.MOUSEMOTION:
                if self.mouse_captured:
                    dx = event.pos[0] - self.width // 2
                    dy = event.pos[1] - self.height // 2
                    if dx != 0 or dy != 0:
                        self.camera.look(dx, dy)
                        pygame.mouse.set_pos(self.width // 2, self.height // 2)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not self.mouse_captured:
                    self._capture_mouse()
            
            elif event.type == pygame.MOUSEWHEEL:
                # Scroll to move in W
                self.camera.position[3] += event.y * 0.5
        
        # Continuous movement
        forward = right = up = ana = 0.0
        
        # WASD or Arrows for XZ movement
        if self.keys_held.get(pygame.K_w) or self.keys_held.get(pygame.K_UP):
            forward += 1
        if self.keys_held.get(pygame.K_s) or self.keys_held.get(pygame.K_DOWN):
            forward -= 1
        if self.keys_held.get(pygame.K_a) or self.keys_held.get(pygame.K_LEFT):
            right -= 1
        if self.keys_held.get(pygame.K_d) or self.keys_held.get(pygame.K_RIGHT):
            right += 1
        
        # Space/Shift for Y
        if self.keys_held.get(pygame.K_SPACE):
            up += 1
        if self.keys_held.get(pygame.K_LSHIFT) or self.keys_held.get(pygame.K_RSHIFT):
            up -= 1
        
        # Q/E for W (the 4th dimension!)
        if self.keys_held.get(pygame.K_q):
            ana -= 1  # Ana (negative W)
        if self.keys_held.get(pygame.K_e):
            ana += 1  # Kata (positive W)
        
        self.camera.move(forward, right, up, ana, dt)
        
        return True
    
    def _capture_mouse(self) -> None:
        self.mouse_captured = True
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        pygame.mouse.set_pos(self.width // 2, self.height // 2)
    
    def _release_mouse(self) -> None:
        self.mouse_captured = False
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
    
    def render(self) -> None:
        """Render the scene."""
        self.screen.fill((10, 12, 20))
        
        # Draw grid
        if self.show_grid:
            self._draw_grid()
        
        # Draw objects
        self._draw_objects()
        
        # Draw UI
        self._draw_crosshair()
        self._draw_hud()
        if self.show_help:
            self._draw_help()
        
        pygame.display.flip()
    
    def _draw_grid(self) -> None:
        """Draw reference grid at Y=0, W=0."""
        color = (30, 35, 50)
        size = 10
        spacing = 2.0
        
        for i in range(-size, size + 1):
            # X lines
            p1 = np.array([i * spacing, 0, -size * spacing, 0.0])
            p2 = np.array([i * spacing, 0, size * spacing, 0.0])
            self._draw_line_4d(p1, p2, color)
            
            # Z lines  
            p1 = np.array([-size * spacing, 0, i * spacing, 0.0])
            p2 = np.array([size * spacing, 0, i * spacing, 0.0])
            self._draw_line_4d(p1, p2, color)
        
        # W axis indicator (gold line along W at origin)
        p1 = np.array([0.0, 0.0, 0.0, -3.0])
        p2 = np.array([0.0, 0.0, 0.0, 3.0])
        self._draw_line_4d(p1, p2, (255, 200, 80), width=2)
    
    def _draw_line_4d(self, p1: np.ndarray, p2: np.ndarray, 
                      color: Tuple[int, int, int], width: int = 1) -> None:
        """Draw a line between two 4D points."""
        proj1 = self.camera.project_point(p1, self.width, self.height)
        proj2 = self.camera.project_point(p2, self.width, self.height)
        
        if proj1 and proj2:
            # Fade by depth
            avg_depth = (proj1[2] + proj2[2]) / 2
            alpha = max(0.2, min(1.0, 3.0 / (1 + avg_depth * 0.2)))
            faded = tuple(int(c * alpha) for c in color)
            pygame.draw.line(self.screen, faded, (proj1[0], proj1[1]), (proj2[0], proj2[1]), width)
    
    def _draw_objects(self) -> None:
        """Draw all world objects with depth sorting."""
        all_edges = []
        
        for world_obj in self.objects:
            verts = world_obj.get_vertices()
            edges = world_obj.get_edges()
            color = world_obj.color
            
            projected = [self.camera.project_point(v, self.width, self.height) for v in verts]
            
            for a, b in edges:
                if a < len(projected) and b < len(projected):
                    p1, p2 = projected[a], projected[b]
                    if p1 and p2:
                        depth = (p1[2] + p2[2]) / 2
                        all_edges.append((depth, p1, p2, color, world_obj.is_3d))
        
        # Sort back to front
        all_edges.sort(key=lambda x: -x[0])
        
        for depth, p1, p2, color, is_3d in all_edges:
            alpha = max(0.3, min(1.0, 4.0 / (1 + depth * 0.2)))
            faded = tuple(int(c * alpha) for c in color)
            width = 1 if is_3d else 2
            pygame.draw.line(self.screen, faded, (p1[0], p1[1]), (p2[0], p2[1]), width)
    
    def _draw_crosshair(self) -> None:
        """Draw center crosshair."""
        cx, cy = self.width // 2, self.height // 2
        color = (100, 100, 100) if self.mouse_captured else (60, 60, 60)
        size, gap = 12, 4
        
        pygame.draw.line(self.screen, color, (cx - size, cy), (cx - gap, cy), 2)
        pygame.draw.line(self.screen, color, (cx + gap, cy), (cx + size, cy), 2)
        pygame.draw.line(self.screen, color, (cx, cy - size), (cx, cy - gap), 2)
        pygame.draw.line(self.screen, color, (cx, cy + gap), (cx, cy + size), 2)
    
    def _draw_hud(self) -> None:
        """Draw heads-up display."""
        pos = self.camera.position
        
        # Position
        pos_text = f"X:{pos[0]:+.1f}  Y:{pos[1]:+.1f}  Z:{pos[2]:+.1f}  W:{pos[3]:+.1f}"
        surf = self.font.render(pos_text, True, (150, 150, 170))
        self.screen.blit(surf, (15, self.height - 55))
        
        # W indicator (the 4th dimension!)
        w_text = f"4th Dimension (W): {pos[3]:+.2f}"
        w_color = (255, 200, 80) if abs(pos[3]) > 0.1 else (150, 150, 170)
        surf = self.font.render(w_text, True, w_color)
        self.screen.blit(surf, (15, self.height - 30))
        
        # Objects
        n4d = sum(1 for o in self.objects if not o.is_3d)
        n3d = sum(1 for o in self.objects if o.is_3d)
        obj_text = f"Objects: {n4d} 4D, {n3d} 3D"
        surf = self.font_small.render(obj_text, True, (120, 120, 140))
        self.screen.blit(surf, (self.width - 150, self.height - 30))
        
        # Mouse hint
        if not self.mouse_captured:
            hint = "Click to capture mouse"
            surf = self.font.render(hint, True, (200, 180, 100))
            self.screen.blit(surf, (self.width//2 - surf.get_width()//2, 20))
    
    def _draw_help(self) -> None:
        """Draw help panel."""
        panel_w, panel_h = 320, 340
        panel_x, panel_y = 15, 15
        
        # Background
        surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        surf.fill((15, 18, 28, 230))
        self.screen.blit(surf, (panel_x, panel_y))
        pygame.draw.rect(self.screen, (50, 55, 70), (panel_x, panel_y, panel_w, panel_h), 1, 8)
        
        # Title
        title = self.font_large.render("4D Sandbox Controls", True, (220, 220, 240))
        self.screen.blit(title, (panel_x + 15, panel_y + 10))
        
        y = panel_y + 50
        sections = [
            ("Movement", [
                ("WASD / Arrows", "Move horizontally"),
                ("Space / Shift", "Move up / down"),
                ("Q / E", "Move in W (4th dim!)"),
                ("Scroll", "Adjust W position"),
            ]),
            ("View", [
                ("Mouse", "Look around"),
                ("Tab / Click", "Capture mouse"),
                ("Esc", "Release / Quit"),
            ]),
            ("Spawn", [
                ("1-7", "Spawn 4D objects"),
                ("F1-F3", "Spawn 3D objects"),
                ("+/-", "Adjust size"),
                ("Backspace", "Remove last"),
            ]),
        ]
        
        for section, items in sections:
            # Section header
            surf = self.font.render(section, True, (100, 180, 255))
            self.screen.blit(surf, (panel_x + 15, y))
            y += 22
            
            for key, desc in items:
                key_surf = self.font_small.render(key, True, (200, 200, 120))
                desc_surf = self.font_small.render(desc, True, (150, 150, 170))
                self.screen.blit(key_surf, (panel_x + 25, y))
                self.screen.blit(desc_surf, (panel_x + 130, y))
                y += 18
            y += 8
        
        # Toggle hint
        hint = self.font_small.render("H to hide help | G to toggle grid", True, (100, 100, 120))
        self.screen.blit(hint, (panel_x + 15, panel_y + panel_h - 25))
    
    def run(self) -> None:
        """Main loop."""
        last_time = pygame.time.get_ticks() / 1000.0
        
        while True:
            now = pygame.time.get_ticks() / 1000.0
            dt = min(now - last_time, 0.1)
            last_time = now
            
            if not self.handle_input(dt):
                break
            
            self.render()
            self.clock.tick(60)
        
        pygame.quit()


def run_sandbox_4d() -> None:
    """Launch the 4D sandbox."""
    sandbox = Sandbox4D()
    sandbox.run()


if __name__ == "__main__":
    run_sandbox_4d()
