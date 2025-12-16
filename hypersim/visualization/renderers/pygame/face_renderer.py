"""Face rendering with depth sorting for solid 4D visualization.

Provides filled polygon rendering of 4D object faces with proper
depth ordering for correct occlusion.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple, Optional
import numpy as np
import pygame

if TYPE_CHECKING:
    from hypersim.core.shape_4d import Shape4D

from hypersim.core.math_4d import perspective_projection_4d_to_3d


class FaceRenderer:
    """Renders 4D object faces with depth sorting.
    
    Projects 4D faces to 2D and draws them with proper depth ordering
    so that front faces occlude back faces.
    """
    
    def __init__(
        self,
        screen: pygame.Surface,
        projection_distance: float = 5.0,
        projection_scale: float = 120.0,
        w_scale_factor: float = 0.3,
    ):
        """Initialize the face renderer.
        
        Args:
            screen: Pygame surface to render to
            projection_distance: 4D projection distance
            projection_scale: Scale factor for screen projection
            w_scale_factor: W coordinate influence on scale
        """
        self.screen = screen
        self.projection_distance = projection_distance
        self.projection_scale = projection_scale
        self.w_scale_factor = w_scale_factor
    
    def _project_vertex(self, v: np.ndarray) -> Tuple[int, int, float]:
        """Project a 4D vertex to 2D screen coordinates.
        
        Args:
            v: 4D vertex [x, y, z, w]
            
        Returns:
            Tuple of (screen_x, screen_y, depth)
        """
        x, y, z, w = v
        scale = 1.0 / (1.0 + abs(w) * self.w_scale_factor)
        
        width, height = self.screen.get_size()
        screen_x = int(x * scale * self.projection_scale + width // 2)
        screen_y = int(-y * scale * self.projection_scale + height // 2)
        depth = z * scale
        
        return screen_x, screen_y, depth
    
    def _compute_face_depth(
        self,
        vertices_4d: List[np.ndarray],
        face_indices: Tuple[int, ...],
    ) -> float:
        """Compute the average depth of a face for sorting.
        
        Args:
            vertices_4d: List of 4D vertices
            face_indices: Indices of vertices forming the face
            
        Returns:
            Average Z depth of the face
        """
        total_z = 0.0
        for idx in face_indices:
            v = vertices_4d[idx]
            w = v[3]
            scale = 1.0 / (1.0 + abs(w) * self.w_scale_factor)
            total_z += v[2] * scale
        return total_z / len(face_indices)
    
    def _compute_face_normal_2d(
        self,
        points: List[Tuple[int, int]],
    ) -> float:
        """Compute the 2D winding order of a face.
        
        Positive means counter-clockwise (front-facing),
        negative means clockwise (back-facing).
        
        Args:
            points: List of 2D points
            
        Returns:
            Signed area (positive = CCW)
        """
        area = 0.0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        return area / 2.0
    
    def render_faces(
        self,
        obj: "Shape4D",
        face_color: Tuple[int, int, int] = (60, 120, 180),
        edge_color: Tuple[int, int, int] = (255, 255, 255),
        alpha: int = 180,
        draw_edges: bool = True,
        edge_width: int = 1,
        backface_culling: bool = True,
        lighting: bool = True,
    ) -> None:
        """Render an object's faces with depth sorting.
        
        Args:
            obj: The Shape4D object to render
            face_color: Base color for faces (R, G, B)
            edge_color: Color for edges
            alpha: Face transparency (0-255)
            draw_edges: Whether to draw face edges
            edge_width: Width of edge lines
            backface_culling: Whether to cull back-facing faces
            lighting: Whether to apply simple lighting
        """
        if not hasattr(obj, 'faces') or not obj.faces:
            return
        
        vertices_4d = obj.get_transformed_vertices()
        
        # Compute face depths and project vertices
        face_data = []
        for face in obj.faces:
            depth = self._compute_face_depth(vertices_4d, face)
            
            # Project face vertices
            points_2d = []
            points_3d = []
            for idx in face:
                sx, sy, _ = self._project_vertex(vertices_4d[idx])
                points_2d.append((sx, sy))
                points_3d.append(vertices_4d[idx][:3])
            
            # Check winding order for backface culling
            winding = self._compute_face_normal_2d(points_2d)
            
            if backface_culling and winding < 0:
                continue
            
            # Compute lighting
            color = list(face_color)
            if lighting and len(points_3d) >= 3:
                # Simple lighting based on face normal
                v0 = np.array(points_3d[0])
                v1 = np.array(points_3d[1])
                v2 = np.array(points_3d[2])
                
                edge1 = v1 - v0
                edge2 = v2 - v0
                normal = np.cross(edge1, edge2)
                norm_len = np.linalg.norm(normal)
                
                if norm_len > 0:
                    normal = normal / norm_len
                    # Light from camera direction
                    light_dir = np.array([0, 0, -1])
                    intensity = max(0.3, abs(np.dot(normal, light_dir)))
                    color = [int(c * intensity) for c in face_color]
            
            face_data.append({
                'depth': depth,
                'points': points_2d,
                'color': tuple(color),
                'winding': winding,
            })
        
        # Sort faces by depth (back to front)
        face_data.sort(key=lambda f: f['depth'], reverse=True)
        
        # Draw faces
        for face in face_data:
            if len(face['points']) < 3:
                continue
            
            # Create surface with alpha
            if alpha < 255:
                # Draw with transparency
                surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
                color_with_alpha = (*face['color'], alpha)
                pygame.draw.polygon(surface, color_with_alpha, face['points'])
                self.screen.blit(surface, (0, 0))
            else:
                pygame.draw.polygon(self.screen, face['color'], face['points'])
            
            # Draw edges
            if draw_edges:
                pygame.draw.polygon(
                    self.screen, edge_color, face['points'], edge_width
                )
    
    def render_wireframe_with_depth(
        self,
        obj: "Shape4D",
        near_color: Tuple[int, int, int] = (255, 255, 255),
        far_color: Tuple[int, int, int] = (60, 60, 80),
        line_width: int = 2,
        depth_range: Tuple[float, float] = (-2.0, 2.0),
    ) -> None:
        """Render wireframe with depth-based coloring.
        
        Edges closer to the camera are brighter, farther edges are dimmer.
        
        Args:
            obj: The Shape4D object to render
            near_color: Color for near edges
            far_color: Color for far edges
            line_width: Edge line width
            depth_range: (min_depth, max_depth) for color interpolation
        """
        vertices_4d = obj.get_transformed_vertices()
        
        # Compute edge depths and project
        edge_data = []
        for a, b in obj.edges:
            v1 = vertices_4d[a]
            v2 = vertices_4d[b]
            
            p1 = self._project_vertex(v1)
            p2 = self._project_vertex(v2)
            
            # Average depth of edge
            avg_depth = (p1[2] + p2[2]) / 2
            
            edge_data.append({
                'p1': (p1[0], p1[1]),
                'p2': (p2[0], p2[1]),
                'depth': avg_depth,
            })
        
        # Sort edges by depth (back to front)
        edge_data.sort(key=lambda e: e['depth'], reverse=True)
        
        # Draw edges with depth-based color
        min_d, max_d = depth_range
        for edge in edge_data:
            # Normalize depth to 0-1
            t = (edge['depth'] - min_d) / (max_d - min_d)
            t = max(0.0, min(1.0, t))
            
            # Interpolate color
            color = tuple(
                int(far_color[i] + (near_color[i] - far_color[i]) * (1 - t))
                for i in range(3)
            )
            
            pygame.draw.line(
                self.screen,
                color,
                edge['p1'],
                edge['p2'],
                line_width,
            )
