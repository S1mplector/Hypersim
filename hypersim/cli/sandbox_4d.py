"""Immersive 4D Sandbox - Explore 4D space as a 4D being.

This sandbox provides a true 4D exploration experience where you can:
- Move freely in all 4 dimensions (X, Y, Z, W)
- Rotate your view in all 6 rotation planes (XY, XZ, XW, YZ, YW, ZW)
- Spawn 4D polytopes and see them from your 4D perspective
- Spawn 3D objects to understand how a 4D being perceives lower dimensions
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Tuple, Optional, Callable, Any

import numpy as np
import pygame

from hypersim.objects import (
    Hypercube, Simplex4D, SixteenCell, TwentyFourCell, Duoprism,
    Pentachoron, OneHundredTwentyCell, SixHundredCell, GrandAntiprism,
    CliffordTorus, CubePrism, TetraPrism, OctaPrism,
)


# =============================================================================
# 4D Camera System
# =============================================================================

@dataclass
class Camera4D:
    """A camera that exists in 4D space.
    
    The camera has a position in 4D and orientation defined by
    rotation angles in all 6 rotation planes.
    """
    # Position in 4D space
    position: np.ndarray = field(default_factory=lambda: np.array([0, 0, 0, 5], dtype=np.float64))
    
    # Rotation angles for all 6 planes (in radians)
    rotation_xy: float = 0.0
    rotation_xz: float = 0.0
    rotation_xw: float = 0.0
    rotation_yz: float = 0.0
    rotation_yw: float = 0.0
    rotation_zw: float = 0.0
    
    # Movement speed
    move_speed: float = 3.0
    rotate_speed: float = 1.5
    
    # Projection parameters
    fov: float = 1.5  # Field of view factor
    near_clip: float = 0.1
    
    def get_rotation_matrix(self) -> np.ndarray:
        """Get the combined 4D rotation matrix."""
        # Build rotation matrices for each plane
        def rot_matrix(plane: str, angle: float) -> np.ndarray:
            c, s = np.cos(angle), np.sin(angle)
            m = np.eye(4, dtype=np.float64)
            if plane == 'xy':
                m[0, 0], m[0, 1], m[1, 0], m[1, 1] = c, -s, s, c
            elif plane == 'xz':
                m[0, 0], m[0, 2], m[2, 0], m[2, 2] = c, -s, s, c
            elif plane == 'xw':
                m[0, 0], m[0, 3], m[3, 0], m[3, 3] = c, -s, s, c
            elif plane == 'yz':
                m[1, 1], m[1, 2], m[2, 1], m[2, 2] = c, -s, s, c
            elif plane == 'yw':
                m[1, 1], m[1, 3], m[3, 1], m[3, 3] = c, -s, s, c
            elif plane == 'zw':
                m[2, 2], m[2, 3], m[3, 2], m[3, 3] = c, -s, s, c
            return m
        
        # Combine rotations
        result = np.eye(4, dtype=np.float64)
        result = result @ rot_matrix('xy', self.rotation_xy)
        result = result @ rot_matrix('xz', self.rotation_xz)
        result = result @ rot_matrix('xw', self.rotation_xw)
        result = result @ rot_matrix('yz', self.rotation_yz)
        result = result @ rot_matrix('yw', self.rotation_yw)
        result = result @ rot_matrix('zw', self.rotation_zw)
        return result
    
    def get_forward_vectors(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Get the 4 basis vectors in camera space (right, up, forward, ana)."""
        rot = self.get_rotation_matrix()
        # Camera looks along -W by default
        right = rot[:, 0]    # X axis
        up = rot[:, 1]       # Y axis
        forward = rot[:, 2]  # Z axis
        ana = rot[:, 3]      # W axis (4th dimension direction)
        return right, up, forward, ana
    
    def move(self, direction: np.ndarray, dt: float) -> None:
        """Move the camera in a direction (in camera space)."""
        rot = self.get_rotation_matrix()
        world_direction = rot @ direction
        self.position += world_direction * self.move_speed * dt
    
    def move_world(self, direction: np.ndarray, dt: float) -> None:
        """Move the camera in world space."""
        self.position += direction * self.move_speed * dt
    
    def rotate(self, plane: str, angle: float) -> None:
        """Rotate the camera in a specific plane."""
        if plane == 'xy':
            self.rotation_xy += angle
        elif plane == 'xz':
            self.rotation_xz += angle
        elif plane == 'xw':
            self.rotation_xw += angle
        elif plane == 'yz':
            self.rotation_yz += angle
        elif plane == 'yw':
            self.rotation_yw += angle
        elif plane == 'zw':
            self.rotation_zw += angle
    
    def transform_point(self, point: np.ndarray) -> np.ndarray:
        """Transform a world point to camera space."""
        # Translate to camera position
        relative = point - self.position
        # Apply inverse rotation
        inv_rot = self.get_rotation_matrix().T
        return inv_rot @ relative
    
    def project_to_3d(self, point_4d: np.ndarray) -> Optional[Tuple[float, float, float, float]]:
        """Project a 4D point to 3D using perspective projection.
        
        Returns (x, y, z, w_depth) or None if behind camera.
        """
        # Transform to camera space
        cam_point = self.transform_point(point_4d)
        
        # W is the depth in 4D (like Z in 3D)
        w = cam_point[3]
        
        # Clip points behind camera
        if w < self.near_clip:
            return None
        
        # 4D perspective projection (W -> 3D)
        scale = self.fov / w
        x = cam_point[0] * scale
        y = cam_point[1] * scale
        z = cam_point[2] * scale
        
        return (x, y, z, w)
    
    def project_to_2d(self, point_4d: np.ndarray, screen_width: int, screen_height: int) -> Optional[Tuple[int, int, float]]:
        """Project a 4D point directly to 2D screen coordinates.
        
        Returns (screen_x, screen_y, depth) or None if not visible.
        """
        proj_3d = self.project_to_3d(point_4d)
        if proj_3d is None:
            return None
        
        x, y, z, w_depth = proj_3d
        
        # Secondary projection: 3D to 2D (using Z as secondary depth)
        # For simplicity, use orthographic for the 3D->2D step
        # with slight Z-based scaling for depth cue
        z_scale = 1.0 / (1.0 + abs(z) * 0.2)
        
        screen_x = int(screen_width / 2 + x * 150 * z_scale)
        screen_y = int(screen_height / 2 - y * 150 * z_scale)
        
        # Combined depth for sorting
        depth = w_depth + z * 0.1
        
        return (screen_x, screen_y, depth)


# =============================================================================
# 3D Objects (for demonstrating 4D perspective on lower dimensions)
# =============================================================================

class Object3D:
    """A 3D object embedded in 4D space (at W=0 by default)."""
    
    def __init__(self, vertices_3d: np.ndarray, edges: List[Tuple[int, int]], 
                 position: np.ndarray = None, w_position: float = 0.0):
        self.vertices_3d = np.array(vertices_3d, dtype=np.float64)
        self.edges = edges
        self.position = position if position is not None else np.zeros(4, dtype=np.float64)
        self.position[3] = w_position
        self.color = (200, 200, 200)
        self.scale = 1.0
    
    def get_vertices_4d(self) -> np.ndarray:
        """Get vertices as 4D points."""
        n = len(self.vertices_3d)
        vertices_4d = np.zeros((n, 4), dtype=np.float64)
        vertices_4d[:, :3] = self.vertices_3d * self.scale
        vertices_4d += self.position
        return vertices_4d


def create_cube_3d(size: float = 1.0) -> Object3D:
    """Create a 3D cube."""
    s = size / 2
    vertices = [
        [-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s],
        [-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s],
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
    ]
    return Object3D(np.array(vertices), edges)


def create_tetrahedron_3d(size: float = 1.0) -> Object3D:
    """Create a 3D tetrahedron."""
    s = size
    vertices = [
        [s, s, s], [s, -s, -s], [-s, s, -s], [-s, -s, s]
    ]
    edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    return Object3D(np.array(vertices) * 0.5, edges)


def create_octahedron_3d(size: float = 1.0) -> Object3D:
    """Create a 3D octahedron."""
    s = size
    vertices = [
        [s, 0, 0], [-s, 0, 0], [0, s, 0], [0, -s, 0], [0, 0, s], [0, 0, -s]
    ]
    edges = [
        (0, 2), (0, 3), (0, 4), (0, 5),
        (1, 2), (1, 3), (1, 4), (1, 5),
        (2, 4), (2, 5), (3, 4), (3, 5),
    ]
    return Object3D(np.array(vertices), edges)


def create_icosahedron_3d(size: float = 1.0) -> Object3D:
    """Create a 3D icosahedron."""
    phi = (1 + math.sqrt(5)) / 2
    s = size / 2
    vertices = [
        [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
        [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
        [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1],
    ]
    edges = [
        (0, 1), (0, 5), (0, 7), (0, 10), (0, 11),
        (1, 5), (1, 7), (1, 8), (1, 9),
        (2, 3), (2, 4), (2, 6), (2, 10), (2, 11),
        (3, 4), (3, 6), (3, 8), (3, 9),
        (4, 5), (4, 9), (4, 11),
        (5, 9), (5, 11),
        (6, 7), (6, 8), (6, 10),
        (7, 8), (7, 10),
        (8, 9), (10, 11),
    ]
    return Object3D(np.array(vertices) * s, edges)


def create_sphere_3d(radius: float = 1.0, segments: int = 16) -> Object3D:
    """Create a 3D sphere wireframe."""
    vertices = []
    edges = []
    
    # Generate latitude/longitude grid
    for i in range(segments + 1):
        lat = math.pi * i / segments - math.pi / 2
        for j in range(segments):
            lon = 2 * math.pi * j / segments
            x = radius * math.cos(lat) * math.cos(lon)
            y = radius * math.sin(lat)
            z = radius * math.cos(lat) * math.sin(lon)
            vertices.append([x, y, z])
    
    # Connect vertices
    for i in range(segments):
        for j in range(segments):
            curr = i * segments + j
            next_j = i * segments + (j + 1) % segments
            next_i = (i + 1) * segments + j
            edges.append((curr, next_j))
            if i < segments:
                edges.append((curr, next_i))
    
    return Object3D(np.array(vertices), edges)


# =============================================================================
# Sandbox World Object
# =============================================================================

@dataclass
class WorldObject:
    """An object in the sandbox world."""
    obj: Any  # Either a 4D shape or Object3D
    is_3d: bool = False
    color: Tuple[int, int, int] = (100, 200, 255)
    position: np.ndarray = field(default_factory=lambda: np.zeros(4, dtype=np.float64))
    
    def get_vertices(self) -> np.ndarray:
        """Get 4D vertices of the object."""
        if self.is_3d:
            return self.obj.get_vertices_4d()
        else:
            verts = np.array(self.obj.get_transformed_vertices(), dtype=np.float64)
            return verts + self.position
    
    def get_edges(self) -> List[Tuple[int, int]]:
        """Get edges of the object."""
        if self.is_3d:
            return self.obj.edges
        else:
            return list(self.obj.edges)


# =============================================================================
# Main Sandbox Application
# =============================================================================

class Sandbox4D:
    """The main 4D sandbox application."""
    
    def __init__(self, width: int = 1400, height: int = 900):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("HyperSim 4D Sandbox - Explore the Fourth Dimension")
        self.clock = pygame.time.Clock()
        
        # Camera
        self.camera = Camera4D()
        self.camera.position = np.array([0, 0, 0, 8], dtype=np.float64)
        
        # World objects
        self.objects: List[WorldObject] = []
        
        # Spawn settings
        self.spawn_distance = 5.0
        self.spawn_size = 1.0
        
        # UI state
        self.show_help = True
        self.show_minimap = True
        self.show_crosshair = True
        self.paused = False
        
        # Input state
        self.keys_held: Dict[int, bool] = {}
        self.mouse_captured = False
        self.last_mouse_pos = (width // 2, height // 2)
        
        # Fonts
        self.font = pygame.font.SysFont("Arial", 16)
        self.font_title = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 14)
        
        # Colors palette
        self.colors_4d = [
            (100, 200, 255), (255, 150, 100), (150, 255, 150),
            (255, 200, 100), (200, 150, 255), (255, 150, 200),
            (100, 255, 200), (255, 255, 150),
        ]
        self.colors_3d = [
            (255, 100, 100), (100, 255, 100), (100, 100, 255),
            (255, 255, 100), (255, 100, 255), (100, 255, 255),
        ]
        
        # Reference grid
        self.show_grid = True
        self.grid_size = 20
        self.grid_spacing = 2.0
        
        # Spawn a few default objects
        self._spawn_default_scene()
    
    def _init_from_app(self) -> None:
        """Initialize when launched from the master app (screen already set)."""
        pygame.display.set_caption("HyperSim 4D Sandbox - Explore the Fourth Dimension")
        
        # Camera
        self.camera = Camera4D()
        self.camera.position = np.array([0, 0, 0, 8], dtype=np.float64)
        
        # World objects
        self.objects: List[WorldObject] = []
        
        # Spawn settings
        self.spawn_distance = 5.0
        self.spawn_size = 1.0
        
        # UI state
        self.show_help = True
        self.show_minimap = True
        self.show_crosshair = True
        self.paused = False
        
        # Input state
        self.keys_held: Dict[int, bool] = {}
        self.mouse_captured = False
        self.last_mouse_pos = (self.width // 2, self.height // 2)
        
        # Fonts
        self.font = pygame.font.SysFont("Arial", 16)
        self.font_title = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 14)
        
        # Colors palette
        self.colors_4d = [
            (100, 200, 255), (255, 150, 100), (150, 255, 150),
            (255, 200, 100), (200, 150, 255), (255, 150, 200),
            (100, 255, 200), (255, 255, 150),
        ]
        self.colors_3d = [
            (255, 100, 100), (100, 255, 100), (100, 100, 255),
            (255, 255, 100), (255, 100, 255), (100, 255, 255),
        ]
        
        # Reference grid
        self.show_grid = True
        self.grid_size = 20
        self.grid_spacing = 2.0
        
        # Spawn default scene
        self._spawn_default_scene()
    
    def _spawn_default_scene(self) -> None:
        """Spawn some default objects to start with."""
        # A tesseract at the origin
        cube = Hypercube(size=1.5)
        self.objects.append(WorldObject(
            obj=cube, is_3d=False,
            color=(100, 200, 255),
            position=np.array([0, 0, 0, 0], dtype=np.float64)
        ))
        
        # A 3D cube to show what 3D looks like from 4D
        cube_3d = create_cube_3d(1.0)
        cube_3d.color = (255, 150, 100)
        self.objects.append(WorldObject(
            obj=cube_3d, is_3d=True,
            color=(255, 150, 100),
            position=np.array([4, 0, 0, 0], dtype=np.float64)
        ))
    
    def spawn_4d_object(self, obj_type: str) -> None:
        """Spawn a 4D object in front of the camera."""
        # Calculate spawn position (in front of camera in W direction)
        _, _, _, ana = self.camera.get_forward_vectors()
        spawn_pos = self.camera.position - ana * self.spawn_distance
        
        obj = None
        if obj_type == "tesseract":
            obj = Hypercube(size=self.spawn_size)
        elif obj_type == "16cell":
            obj = SixteenCell(size=self.spawn_size)
        elif obj_type == "24cell":
            obj = TwentyFourCell(size=self.spawn_size * 0.8)
        elif obj_type == "5cell":
            obj = Pentachoron(size=self.spawn_size * 1.2)
        elif obj_type == "600cell":
            obj = SixHundredCell(size=self.spawn_size * 0.6)
        elif obj_type == "120cell":
            obj = OneHundredTwentyCell(size=self.spawn_size * 0.5)
        elif obj_type == "duoprism":
            obj = Duoprism(m=4, n=5, size=self.spawn_size)
        elif obj_type == "clifford":
            obj = CliffordTorus(size=self.spawn_size)
        elif obj_type == "grand":
            obj = GrandAntiprism(size=self.spawn_size * 0.7)
        
        if obj:
            color = random.choice(self.colors_4d)
            self.objects.append(WorldObject(
                obj=obj, is_3d=False,
                color=color,
                position=spawn_pos.copy()
            ))
    
    def spawn_3d_object(self, obj_type: str) -> None:
        """Spawn a 3D object (embedded in 4D at W=spawn position)."""
        _, _, _, ana = self.camera.get_forward_vectors()
        spawn_pos = self.camera.position - ana * self.spawn_distance
        
        obj = None
        if obj_type == "cube":
            obj = create_cube_3d(self.spawn_size)
        elif obj_type == "tetrahedron":
            obj = create_tetrahedron_3d(self.spawn_size)
        elif obj_type == "octahedron":
            obj = create_octahedron_3d(self.spawn_size)
        elif obj_type == "icosahedron":
            obj = create_icosahedron_3d(self.spawn_size * 0.8)
        elif obj_type == "sphere":
            obj = create_sphere_3d(self.spawn_size * 0.5, segments=12)
        
        if obj:
            obj.position = spawn_pos.copy()
            color = random.choice(self.colors_3d)
            obj.color = color
            self.objects.append(WorldObject(
                obj=obj, is_3d=True,
                color=color,
                position=spawn_pos.copy()
            ))
    
    def handle_input(self, dt: float) -> bool:
        """Handle input events. Returns False if should quit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                self.keys_held[event.key] = True
                
                if event.key == pygame.K_ESCAPE:
                    if self.mouse_captured:
                        self.mouse_captured = False
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                    else:
                        return False
                
                elif event.key == pygame.K_TAB:
                    self.mouse_captured = not self.mouse_captured
                    pygame.mouse.set_visible(not self.mouse_captured)
                    pygame.event.set_grab(self.mouse_captured)
                    if self.mouse_captured:
                        pygame.mouse.set_pos(self.width // 2, self.height // 2)
                
                elif event.key == pygame.K_h:
                    self.show_help = not self.show_help
                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid
                elif event.key == pygame.K_m:
                    self.show_minimap = not self.show_minimap
                elif event.key == pygame.K_c:
                    self.show_crosshair = not self.show_crosshair
                elif event.key == pygame.K_BACKSPACE:
                    if self.objects:
                        self.objects.pop()
                elif event.key == pygame.K_DELETE:
                    self.objects.clear()
                
                # 4D Object spawning (number keys)
                elif event.key == pygame.K_1:
                    self.spawn_4d_object("tesseract")
                elif event.key == pygame.K_2:
                    self.spawn_4d_object("16cell")
                elif event.key == pygame.K_3:
                    self.spawn_4d_object("24cell")
                elif event.key == pygame.K_4:
                    self.spawn_4d_object("5cell")
                elif event.key == pygame.K_5:
                    self.spawn_4d_object("600cell")
                elif event.key == pygame.K_6:
                    self.spawn_4d_object("duoprism")
                elif event.key == pygame.K_7:
                    self.spawn_4d_object("clifford")
                elif event.key == pygame.K_8:
                    self.spawn_4d_object("grand")
                
                # 3D Object spawning (F keys)
                elif event.key == pygame.K_F1:
                    self.spawn_3d_object("cube")
                elif event.key == pygame.K_F2:
                    self.spawn_3d_object("tetrahedron")
                elif event.key == pygame.K_F3:
                    self.spawn_3d_object("octahedron")
                elif event.key == pygame.K_F4:
                    self.spawn_3d_object("icosahedron")
                elif event.key == pygame.K_F5:
                    self.spawn_3d_object("sphere")
                
                # Size adjustment
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
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
                        # Mouse controls XZ and YZ rotation (like looking around)
                        self.camera.rotate('xz', -dx * 0.003)
                        self.camera.rotate('yz', -dy * 0.003)
                        pygame.mouse.set_pos(self.width // 2, self.height // 2)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not self.mouse_captured and event.button == 1:
                    self.mouse_captured = True
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                    pygame.mouse.set_pos(self.width // 2, self.height // 2)
        
        # Continuous movement
        move_dir = np.zeros(4, dtype=np.float64)
        
        # WASD for XY movement
        if self.keys_held.get(pygame.K_w):
            move_dir[1] += 1  # Up
        if self.keys_held.get(pygame.K_s):
            move_dir[1] -= 1  # Down
        if self.keys_held.get(pygame.K_a):
            move_dir[0] -= 1  # Left
        if self.keys_held.get(pygame.K_d):
            move_dir[0] += 1  # Right
        
        # QE for Z movement
        if self.keys_held.get(pygame.K_q):
            move_dir[2] -= 1  # Backward in Z
        if self.keys_held.get(pygame.K_e):
            move_dir[2] += 1  # Forward in Z
        
        # RF for W movement (the 4th dimension!)
        if self.keys_held.get(pygame.K_r):
            move_dir[3] -= 1  # Ana (into 4D)
        if self.keys_held.get(pygame.K_f):
            move_dir[3] += 1  # Kata (out of 4D)
        
        # Arrow keys for 4D rotation
        if self.keys_held.get(pygame.K_LEFT):
            self.camera.rotate('xw', dt * self.camera.rotate_speed)
        if self.keys_held.get(pygame.K_RIGHT):
            self.camera.rotate('xw', -dt * self.camera.rotate_speed)
        if self.keys_held.get(pygame.K_UP):
            self.camera.rotate('yw', dt * self.camera.rotate_speed)
        if self.keys_held.get(pygame.K_DOWN):
            self.camera.rotate('yw', -dt * self.camera.rotate_speed)
        
        # ZX for ZW rotation
        if self.keys_held.get(pygame.K_z):
            self.camera.rotate('zw', dt * self.camera.rotate_speed)
        if self.keys_held.get(pygame.K_x):
            self.camera.rotate('zw', -dt * self.camera.rotate_speed)
        
        # Apply movement
        if np.any(move_dir != 0):
            norm = np.linalg.norm(move_dir)
            if norm > 0:
                move_dir /= norm
            self.camera.move(move_dir, dt)
        
        return True
    
    def render_grid(self) -> None:
        """Render a 4D reference grid."""
        if not self.show_grid:
            return
        
        grid_color = (40, 45, 60)
        half = self.grid_size // 2
        
        # Draw grid lines in XY plane at Z=0, W=0
        for i in range(-half, half + 1):
            pos = i * self.grid_spacing
            
            # X lines
            start = np.array([pos, -half * self.grid_spacing, 0, 0], dtype=np.float64)
            end = np.array([pos, half * self.grid_spacing, 0, 0], dtype=np.float64)
            self._draw_line_4d(start, end, grid_color)
            
            # Y lines
            start = np.array([-half * self.grid_spacing, pos, 0, 0], dtype=np.float64)
            end = np.array([half * self.grid_spacing, pos, 0, 0], dtype=np.float64)
            self._draw_line_4d(start, end, grid_color)
        
        # Draw W axis indicator
        origin = np.array([0, 0, 0, 0], dtype=np.float64)
        w_end = np.array([0, 0, 0, 5], dtype=np.float64)
        self._draw_line_4d(origin, w_end, (255, 200, 100), width=2)
    
    def _draw_line_4d(self, start: np.ndarray, end: np.ndarray, 
                      color: Tuple[int, int, int], width: int = 1) -> None:
        """Draw a line in 4D space."""
        p1 = self.camera.project_to_2d(start, self.width, self.height)
        p2 = self.camera.project_to_2d(end, self.width, self.height)
        
        if p1 is not None and p2 is not None:
            # Depth-based alpha
            avg_depth = (p1[2] + p2[2]) / 2
            alpha = max(0.2, min(1.0, 2.0 / (1 + avg_depth * 0.1)))
            faded_color = tuple(int(c * alpha) for c in color)
            pygame.draw.line(self.screen, faded_color, (p1[0], p1[1]), (p2[0], p2[1]), width)
    
    def render_objects(self) -> None:
        """Render all objects in the scene."""
        # Collect all edges with depth for sorting
        all_edges = []
        
        for world_obj in self.objects:
            vertices = world_obj.get_vertices()
            edges = world_obj.get_edges()
            color = world_obj.color
            
            # Project all vertices
            projected = []
            for v in vertices:
                p = self.camera.project_to_2d(v, self.width, self.height)
                projected.append(p)
            
            # Collect edges
            for a, b in edges:
                if a < len(projected) and b < len(projected):
                    p1, p2 = projected[a], projected[b]
                    if p1 is not None and p2 is not None:
                        avg_depth = (p1[2] + p2[2]) / 2
                        all_edges.append((avg_depth, p1, p2, color, world_obj.is_3d))
        
        # Sort by depth (far to near)
        all_edges.sort(key=lambda x: -x[0])
        
        # Draw edges
        for depth, p1, p2, color, is_3d in all_edges:
            # Depth-based color fading
            alpha = max(0.3, min(1.0, 3.0 / (1 + depth * 0.15)))
            faded_color = tuple(int(c * alpha) for c in color)
            
            width = 1 if is_3d else 2
            pygame.draw.line(self.screen, faded_color, (p1[0], p1[1]), (p2[0], p2[1]), width)
    
    def render_crosshair(self) -> None:
        """Render a crosshair in the center."""
        if not self.show_crosshair:
            return
        
        cx, cy = self.width // 2, self.height // 2
        color = (150, 150, 150)
        size = 15
        gap = 5
        
        pygame.draw.line(self.screen, color, (cx - size, cy), (cx - gap, cy), 2)
        pygame.draw.line(self.screen, color, (cx + gap, cy), (cx + size, cy), 2)
        pygame.draw.line(self.screen, color, (cx, cy - size), (cx, cy - gap), 2)
        pygame.draw.line(self.screen, color, (cx, cy + gap), (cx, cy + size), 2)
    
    def render_minimap(self) -> None:
        """Render a minimap showing position in 4D."""
        if not self.show_minimap:
            return
        
        # Draw minimap background
        map_size = 150
        margin = 15
        map_x = self.width - map_size - margin
        map_y = margin
        
        pygame.draw.rect(self.screen, (20, 25, 35), (map_x, map_y, map_size, map_size), border_radius=8)
        pygame.draw.rect(self.screen, (50, 55, 70), (map_x, map_y, map_size, map_size), width=1, border_radius=8)
        
        # Draw XW view (top-down in X and W)
        center_x = map_x + map_size // 2
        center_y = map_y + map_size // 2
        scale = 5.0
        
        # Draw axes
        pygame.draw.line(self.screen, (60, 60, 80), (map_x + 10, center_y), (map_x + map_size - 10, center_y), 1)
        pygame.draw.line(self.screen, (60, 60, 80), (center_x, map_y + 10), (center_x, map_y + map_size - 10), 1)
        
        # Draw objects on minimap
        for obj in self.objects:
            pos = obj.position
            mx = int(center_x + pos[0] * scale)
            mw = int(center_y - pos[3] * scale)  # W is vertical on minimap
            
            if map_x + 5 < mx < map_x + map_size - 5 and map_y + 5 < mw < map_y + map_size - 5:
                color = obj.color if not obj.is_3d else (255, 100, 100)
                pygame.draw.circle(self.screen, color, (mx, mw), 3)
        
        # Draw camera position
        cam_x = int(center_x + self.camera.position[0] * scale)
        cam_w = int(center_y - self.camera.position[3] * scale)
        pygame.draw.circle(self.screen, (255, 255, 100), (cam_x, cam_w), 5)
        
        # Draw camera direction
        _, _, _, ana = self.camera.get_forward_vectors()
        dir_x = int(cam_x - ana[0] * 15)
        dir_w = int(cam_w + ana[3] * 15)
        pygame.draw.line(self.screen, (255, 255, 100), (cam_x, cam_w), (dir_x, dir_w), 2)
        
        # Labels
        label_x = self.font_small.render("X", True, (100, 100, 120))
        label_w = self.font_small.render("W", True, (100, 100, 120))
        self.screen.blit(label_x, (map_x + map_size - 20, center_y + 5))
        self.screen.blit(label_w, (center_x + 5, map_y + 5))
    
    def render_hud(self) -> None:
        """Render the heads-up display."""
        # Position info
        pos = self.camera.position
        pos_text = f"Position: X={pos[0]:.1f} Y={pos[1]:.1f} Z={pos[2]:.1f} W={pos[3]:.1f}"
        pos_surf = self.font.render(pos_text, True, (180, 180, 200))
        self.screen.blit(pos_surf, (15, self.height - 60))
        
        # Object count
        count_4d = sum(1 for o in self.objects if not o.is_3d)
        count_3d = sum(1 for o in self.objects if o.is_3d)
        count_text = f"Objects: {count_4d} 4D, {count_3d} 3D | Size: {self.spawn_size:.1f}"
        count_surf = self.font.render(count_text, True, (180, 180, 200))
        self.screen.blit(count_surf, (15, self.height - 35))
        
        # FPS
        fps = self.clock.get_fps()
        fps_surf = self.font_small.render(f"FPS: {fps:.0f}", True, (120, 120, 140))
        self.screen.blit(fps_surf, (self.width - 70, self.height - 30))
        
        # Mouse capture hint
        if not self.mouse_captured:
            hint = "Click or TAB to capture mouse"
            hint_surf = self.font.render(hint, True, (200, 200, 100))
            self.screen.blit(hint_surf, (self.width // 2 - hint_surf.get_width() // 2, 20))
    
    def render_help(self) -> None:
        """Render help overlay."""
        if not self.show_help:
            return
        
        # Help panel
        panel_width = 380
        panel_height = 420
        panel_x = 15
        panel_y = 15
        
        # Background
        surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        surf.fill((15, 18, 28, 220))
        self.screen.blit(surf, (panel_x, panel_y))
        pygame.draw.rect(self.screen, (60, 65, 80), (panel_x, panel_y, panel_width, panel_height), 
                        width=1, border_radius=8)
        
        # Title
        title = self.font_title.render("4D Sandbox Controls", True, (230, 230, 250))
        self.screen.blit(title, (panel_x + 15, panel_y + 12))
        
        y = panel_y + 50
        sections = [
            ("Movement (Camera Space)", [
                ("W/A/S/D", "Move up/left/down/right"),
                ("Q/E", "Move backward/forward (Z)"),
                ("R/F", "Move ana/kata (W - 4th dim!)"),
            ]),
            ("Rotation", [
                ("Mouse", "Look around (XZ/YZ planes)"),
                ("←/→", "Rotate in XW plane"),
                ("↑/↓", "Rotate in YW plane"),
                ("Z/X", "Rotate in ZW plane"),
            ]),
            ("Spawn 4D Objects (1-8)", [
                ("1", "Tesseract"),
                ("2", "16-cell"),
                ("3", "24-cell"),
                ("4", "5-cell"),
                ("5", "600-cell"),
                ("6", "Duoprism"),
                ("7", "Clifford Torus"),
                ("8", "Grand Antiprism"),
            ]),
            ("Spawn 3D Objects (F1-F5)", [
                ("F1-F5", "Cube/Tetra/Octa/Icosa/Sphere"),
            ]),
            ("Other", [
                ("+/-", "Adjust spawn size"),
                ("Backspace", "Remove last object"),
                ("Delete", "Clear all"),
                ("H/G/M/C", "Toggle help/grid/minimap/crosshair"),
                ("Tab/Esc", "Toggle mouse capture"),
            ]),
        ]
        
        for section_title, items in sections:
            # Section title
            sect_surf = self.font.render(section_title, True, (150, 200, 255))
            self.screen.blit(sect_surf, (panel_x + 15, y))
            y += 22
            
            for key, desc in items:
                key_surf = self.font_small.render(key, True, (200, 200, 100))
                desc_surf = self.font_small.render(desc, True, (160, 160, 180))
                self.screen.blit(key_surf, (panel_x + 25, y))
                self.screen.blit(desc_surf, (panel_x + 100, y))
                y += 18
            y += 5
    
    def render(self) -> None:
        """Render the entire scene."""
        # Clear screen
        self.screen.fill((8, 10, 18))
        
        # Render world
        self.render_grid()
        self.render_objects()
        
        # Render UI
        self.render_crosshair()
        self.render_minimap()
        self.render_hud()
        self.render_help()
        
        pygame.display.flip()
    
    def run(self) -> None:
        """Main loop."""
        running = True
        last_time = pygame.time.get_ticks() / 1000.0
        
        while running:
            now = pygame.time.get_ticks() / 1000.0
            dt = min(now - last_time, 0.1)
            last_time = now
            
            running = self.handle_input(dt)
            self.render()
            
            self.clock.tick(60)
        
        pygame.quit()


def run_sandbox_4d() -> None:
    """Launch the 4D sandbox."""
    sandbox = Sandbox4D()
    sandbox.run()


if __name__ == "__main__":
    run_sandbox_4d()
