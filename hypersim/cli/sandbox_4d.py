"""Immersive 4D Sandbox - Explore 4D space as a 4D being.

Controls:
- WASD/Arrows: Move horizontally (XZ plane)
- Space/Shift: Move up/down (Y)
- Q/E: Move in W (the 4th dimension!)
- Mouse: Look around
- Scroll: Adjust W position
- 1-7: Spawn 4D objects
- F1-F3: Spawn 3D objects
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Tuple, Any

import numpy as np
import pygame

from .base_app import BaseApp, Camera4D, THEME, Fonts
from .sandbox_features import (
    ObjectAnimator, AnimationConfig,
    SpawnGizmo, SpawnMode,
    Minimap, MinimapView,
    SandboxHUD,
    ObjectSelector,
)
from hypersim.objects import (
    Hypercube, SixteenCell, TwentyFourCell, Duoprism,
    Pentachoron, SixHundredCell, CliffordTorus,
)


# =============================================================================
# 3D OBJECTS (embedded in 4D)
# =============================================================================

class Object3D:
    """A 3D object embedded in 4D space."""
    
    def __init__(self, vertices: List[List[float]], edges: List[Tuple[int, int]]):
        self.vertices_3d = np.array(vertices, dtype=np.float64)
        self.edges = edges
        self.position = np.zeros(4, dtype=np.float64)
        self.scale = 1.0
        self.color = (200, 200, 200)
    
    def get_vertices_4d(self) -> np.ndarray:
        n = len(self.vertices_3d)
        verts = np.zeros((n, 4), dtype=np.float64)
        verts[:, :3] = self.vertices_3d * self.scale
        verts += self.position
        return verts


def make_cube_3d(size: float = 1.0) -> Object3D:
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
    s = size * 0.6
    verts = [[s,s,s], [s,-s,-s], [-s,s,-s], [-s,-s,s]]
    edges = [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3)]
    return Object3D(verts, edges)


def make_octahedron_3d(size: float = 1.0) -> Object3D:
    s = size
    verts = [[s,0,0], [-s,0,0], [0,s,0], [0,-s,0], [0,0,s], [0,0,-s]]
    edges = [
        (0,2), (0,3), (0,4), (0,5),
        (1,2), (1,3), (1,4), (1,5),
        (2,4), (2,5), (3,4), (3,5),
    ]
    return Object3D(verts, edges)


# =============================================================================
# WORLD OBJECT
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
        verts = np.array(self.obj.get_transformed_vertices(), dtype=np.float64)
        return verts + self.position
    
    def get_edges(self) -> List[Tuple[int, int]]:
        return list(self.obj.edges)


# =============================================================================
# SANDBOX APPLICATION
# =============================================================================

class Sandbox4D(BaseApp):
    """The immersive 4D sandbox with enhanced features."""
    
    def __init__(self, width: int = 1400, height: int = 900):
        super().__init__(width, height, "HyperSim 4D Sandbox")
        
        self.camera = Camera4D()
        self.objects: List[WorldObject] = []
        self.spawn_distance = 5.0
        self.spawn_size = 1.0
        
        self.show_help = True
        self.show_grid = True
        
        self.colors_4d = [
            (100, 180, 255), (255, 150, 100), (150, 255, 150),
            (255, 200, 100), (200, 150, 255), (255, 150, 200),
        ]
        self.colors_3d = [(255, 100, 100), (100, 255, 100), (100, 100, 255)]
        
        # Enhanced features
        self.animator = ObjectAnimator()
        self.spawn_gizmo = SpawnGizmo()
        self.minimap = Minimap(width - 170, 80, size=150)
        self.hud = SandboxHUD(width, height)
        self.selector = ObjectSelector()
        
        self._spawn_defaults()
    
    def _init_from_app(self) -> None:
        """Initialize when launched from master app."""
        pygame.display.set_caption(self.title)
        self.camera = Camera4D()
        self.objects = []
        self.spawn_distance = 5.0
        self.spawn_size = 1.0
        self.show_help = True
        self.show_grid = True
        self.running = True
        self.keys_held = {}
        self.mouse_captured = False
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
        self.colors_4d = [
            (100, 180, 255), (255, 150, 100), (150, 255, 150),
            (255, 200, 100), (200, 150, 255), (255, 150, 200),
        ]
        self.colors_3d = [(255, 100, 100), (100, 255, 100), (100, 100, 255)]
        
        # Enhanced features
        self.animator = ObjectAnimator()
        self.spawn_gizmo = SpawnGizmo()
        self.minimap = Minimap(self.width - 170, 80, size=150)
        self.hud = SandboxHUD(self.width, self.height)
        self.selector = ObjectSelector()
        
        self._spawn_defaults()
    
    def _spawn_defaults(self) -> None:
        """Spawn default objects."""
        cube = Hypercube(size=1.5)
        self.objects.append(WorldObject(cube, False, (100, 180, 255), np.zeros(4)))
        self.animator.register(0)  # Register for animation
        
        cube_3d = make_cube_3d(1.0)
        cube_3d.position = np.array([4.0, 0.0, 0.0, 0.0])
        cube_3d.color = (255, 150, 100)
        self.objects.append(WorldObject(cube_3d, True, (255, 150, 100), cube_3d.position.copy()))
    
    def spawn_4d(self, name: str) -> None:
        """Spawn a 4D object."""
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
            idx = len(self.objects)
            self.objects.append(WorldObject(obj, False, random.choice(self.colors_4d), pos.copy()))
            self.animator.register(idx)  # Auto-animate new objects
    
    def spawn_3d(self, name: str) -> None:
        """Spawn a 3D object."""
        pos = self.camera.position + self.camera.get_forward() * self.spawn_distance
        factories = {
            "cube": lambda: make_cube_3d(self.spawn_size),
            "tetra": lambda: make_tetrahedron_3d(self.spawn_size),
            "octa": lambda: make_octahedron_3d(self.spawn_size),
        }
        if name in factories:
            obj = factories[name]()
            obj.position = pos.copy()
            color = random.choice(self.colors_3d)
            obj.color = color
            self.objects.append(WorldObject(obj, True, color, pos.copy()))
    
    def handle_events(self) -> bool:
        """Handle input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                self.keys_held[event.key] = True
                
                if event.key == pygame.K_ESCAPE:
                    if self.mouse_captured:
                        self.release_mouse()
                    else:
                        return False
                elif event.key == pygame.K_TAB:
                    if self.mouse_captured:
                        self.release_mouse()
                    else:
                        self.capture_mouse()
                elif event.key == pygame.K_h:
                    self.show_help = not self.show_help
                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid
                elif event.key == pygame.K_m:
                    self.minimap.visible = not self.minimap.visible
                elif event.key == pygame.K_n:
                    self.minimap.cycle_view()
                elif event.key == pygame.K_p:
                    self.animator.toggle_pause()
                elif event.key == pygame.K_COMMA:
                    self.animator.set_speed(self.animator.global_speed - 0.25)
                elif event.key == pygame.K_PERIOD:
                    self.animator.set_speed(self.animator.global_speed + 0.25)
                elif event.key == pygame.K_BACKSPACE and self.objects:
                    self.animator.unregister(len(self.objects) - 1)
                    self.objects.pop()
                elif event.key == pygame.K_DELETE:
                    self.objects.clear()
                    self.animator.animations.clear()
                # Spawn 4D (using gizmo selection or direct)
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
                # Spawn 3D
                elif event.key == pygame.K_F1:
                    self.spawn_3d("cube")
                elif event.key == pygame.K_F2:
                    self.spawn_3d("tetra")
                elif event.key == pygame.K_F3:
                    self.spawn_3d("octa")
                # Spawn gizmo controls
                elif event.key == pygame.K_LEFTBRACKET:
                    self.spawn_gizmo.prev_type()
                elif event.key == pygame.K_RIGHTBRACKET:
                    self.spawn_gizmo.next_type()
                elif event.key == pygame.K_t:
                    self.spawn_gizmo.toggle_dimension()
                # Size
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                    self.spawn_size = min(3.0, self.spawn_size + 0.2)
                    self.spawn_gizmo.adjust_scale(0.2)
                elif event.key == pygame.K_MINUS:
                    self.spawn_size = max(0.2, self.spawn_size - 0.2)
                    self.spawn_gizmo.adjust_scale(-0.2)
            
            elif event.type == pygame.KEYUP:
                self.keys_held[event.key] = False
            
            elif event.type == pygame.MOUSEMOTION:
                if self.mouse_captured:
                    dx = event.pos[0] - self.width // 2
                    dy = event.pos[1] - self.height // 2
                    if dx != 0 or dy != 0:
                        self.camera.look(dx, dy)
                        pygame.mouse.set_pos(self.width // 2, self.height // 2)
                else:
                    # Update selector hover
                    self.selector.update(event.pos, self.camera, self.objects, 
                                        self.width, self.height)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if not self.mouse_captured:
                        # Try to select object first
                        if self.selector.hover_index is not None:
                            self.selector.click()
                        else:
                            self.capture_mouse()
                elif event.button == 3:  # Right click to deselect
                    self.selector.deselect()
            
            elif event.type == pygame.MOUSEWHEEL:
                self.camera.position[3] += event.y * 0.5
                self.spawn_gizmo.adjust_distance(event.y * 0.5)
        
        return True
    
    def update(self, dt: float) -> None:
        """Update camera movement and animations."""
        forward = right = up = ana = 0.0
        
        if self.keys_held.get(pygame.K_w) or self.keys_held.get(pygame.K_UP):
            forward += 1
        if self.keys_held.get(pygame.K_s) or self.keys_held.get(pygame.K_DOWN):
            forward -= 1
        if self.keys_held.get(pygame.K_a) or self.keys_held.get(pygame.K_LEFT):
            right -= 1
        if self.keys_held.get(pygame.K_d) or self.keys_held.get(pygame.K_RIGHT):
            right += 1
        if self.keys_held.get(pygame.K_SPACE):
            up += 1
        if self.keys_held.get(pygame.K_LSHIFT) or self.keys_held.get(pygame.K_RSHIFT):
            up -= 1
        if self.keys_held.get(pygame.K_q):
            ana -= 1
        if self.keys_held.get(pygame.K_e):
            ana += 1
        
        self.camera.move(forward, right, up, ana, dt)
        
        # Update object animations
        self.animator.update(dt, self.objects)
        
        # Update spawn gizmo preview
        self.spawn_gizmo.update_preview(self.camera)
        
        # Update HUD stats
        fps = self.clock.get_fps() if self.clock else 60
        self.hud.update_stats(fps, dt)
    
    def render(self) -> None:
        """Render the scene."""
        self.screen.fill(THEME.bg_dark)
        
        if self.show_grid:
            self._draw_grid()
        
        self._draw_objects()
        
        # Draw selection highlights
        self.selector.draw(self.screen, self.camera, self.objects, self.width, self.height)
        
        # Draw spawn gizmo
        self.spawn_gizmo.draw(self.screen, self.camera, self.width, self.height)
        
        self.draw_crosshair()
        
        # Draw enhanced HUD
        self.hud.draw(self.screen, self.camera, self.objects, self.animator)
        
        # Draw minimap
        self.minimap.draw(self.screen, self.camera, self.objects)
        
        if self.show_help:
            self._draw_help()
    
    def _draw_grid(self) -> None:
        """Draw reference grid."""
        color = (30, 35, 50)
        size, spacing = 10, 2.0
        
        for i in range(-size, size + 1):
            p1 = np.array([i * spacing, 0, -size * spacing, 0.0])
            p2 = np.array([i * spacing, 0, size * spacing, 0.0])
            self.draw_line_4d(self.camera, p1, p2, color)
            
            p1 = np.array([-size * spacing, 0, i * spacing, 0.0])
            p2 = np.array([size * spacing, 0, i * spacing, 0.0])
            self.draw_line_4d(self.camera, p1, p2, color)
        
        # W axis indicator
        self.draw_line_4d(self.camera, 
                         np.array([0., 0., 0., -3.]), 
                         np.array([0., 0., 0., 3.]), 
                         (255, 200, 80), width=2)
    
    def _draw_objects(self) -> None:
        """Draw all objects with depth sorting."""
        all_edges = []
        
        for world_obj in self.objects:
            verts = world_obj.get_vertices()
            edges = world_obj.get_edges()
            color = world_obj.color
            
            projected = [self.camera.project(v, self.width, self.height) for v in verts]
            
            for a, b in edges:
                if a < len(projected) and b < len(projected):
                    p1, p2 = projected[a], projected[b]
                    if p1 and p2:
                        depth = (p1[2] + p2[2]) / 2
                        all_edges.append((depth, p1, p2, color, world_obj.is_3d))
        
        all_edges.sort(key=lambda x: -x[0])
        
        for depth, p1, p2, color, is_3d in all_edges:
            alpha = max(0.3, min(1.0, 4.0 / (1 + depth * 0.2)))
            faded = tuple(int(c * alpha) for c in color)
            width = 1 if is_3d else 2
            pygame.draw.line(self.screen, faded, (p1[0], p1[1]), (p2[0], p2[1]), width)
    
    def _draw_hud(self) -> None:
        """Draw HUD."""
        pos = self.camera.position
        fonts = Fonts.get()
        
        pos_text = f"X:{pos[0]:+.1f}  Y:{pos[1]:+.1f}  Z:{pos[2]:+.1f}  W:{pos[3]:+.1f}"
        self.draw_text(pos_text, (15, self.height - 55), THEME.text_secondary, fonts.body)
        
        w_color = (255, 200, 80) if abs(pos[3]) > 0.1 else THEME.text_secondary
        self.draw_text(f"4th Dimension (W): {pos[3]:+.2f}", (15, self.height - 30), w_color, fonts.body)
        
        n4d = sum(1 for o in self.objects if not o.is_3d)
        n3d = sum(1 for o in self.objects if o.is_3d)
        self.draw_text(f"Objects: {n4d} 4D, {n3d} 3D", (self.width - 150, self.height - 30), 
                      THEME.text_muted, fonts.small)
        
        if not self.mouse_captured:
            hint = fonts.body.render("Click to capture mouse", True, (200, 180, 100))
            self.screen.blit(hint, (self.width//2 - hint.get_width()//2, 20))
    
    def _draw_help(self) -> None:
        """Draw help panel."""
        fonts = Fonts.get()
        panel_w, panel_h = 340, 380
        
        self.draw_panel(pygame.Rect(15, 15, panel_w, panel_h), 
                       alpha=230, border_color=THEME.border)
        
        self.draw_text("4D Sandbox Controls", (30, 25), THEME.text_primary, fonts.title)
        
        y = 55
        sections = [
            ("Movement", [("WASD/Arrows", "Move XZ"), ("Space/Shift", "Up/Down"), 
                         ("Q/E", "W axis (4D!)"), ("Scroll", "Adjust W")]),
            ("View", [("Mouse", "Look"), ("Tab/Click", "Capture"), 
                     ("M/N", "Minimap on/cycle"), ("Esc", "Release/Quit")]),
            ("Spawn", [("1-7", "4D objects"), ("F1-F3", "3D objects"), 
                      ("[ / ]", "Cycle type"), ("T", "Toggle 4D/3D"), ("+/-", "Size")]),
            ("Animation", [("P", "Pause/Resume"), (",/.", "Speed -/+")]),
            ("Select", [("Click", "Select object"), ("R-Click", "Deselect")]),
        ]
        
        for section, items in sections:
            self.draw_text(section, (30, y), THEME.accent_blue, fonts.body)
            y += 20
            for key, desc in items:
                self.draw_text(key, (40, y), (200, 200, 120), fonts.small)
                self.draw_text(desc, (145, y), THEME.text_muted, fonts.small)
                y += 16
            y += 6
        
        self.draw_text("H: help | G: grid | Objects auto-animate!", (30, panel_h - 12), 
                      THEME.text_muted, fonts.small)


def run_sandbox_4d() -> None:
    """Launch the 4D sandbox."""
    sandbox = Sandbox4D()
    sandbox.run()


if __name__ == "__main__":
    run_sandbox_4d()
