"""Export functionality for HyperSim objects.

This module provides utilities to export 4D objects to various 3D formats
by projecting them or taking cross-sections.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple
import numpy as np

if TYPE_CHECKING:
    from hypersim.core.shape_4d import Shape4D

from hypersim.core.math_4d import perspective_projection_4d_to_3d


def export_to_obj(
    obj: "Shape4D",
    path: str | Path,
    projection_distance: float = 5.0,
    include_faces: bool = True,
    comment: Optional[str] = None,
) -> None:
    """Export a 4D object to Wavefront OBJ format.
    
    The 4D object is projected to 3D using perspective projection,
    then saved as an OBJ file.
    
    Args:
        obj: The 4D object to export
        path: Path to save the OBJ file
        projection_distance: Distance for 4D to 3D projection
        include_faces: Whether to include faces (if available)
        comment: Optional comment to include in the file header
    """
    path = Path(path)
    
    # Get transformed vertices and project to 3D
    vertices_4d = np.array(obj.get_transformed_vertices())
    vertices_3d = perspective_projection_4d_to_3d(vertices_4d, projection_distance)
    
    edges = obj.edges
    faces = obj.faces if include_faces and hasattr(obj, 'faces') else []
    
    with open(path, "w") as f:
        # Header
        f.write(f"# HyperSim OBJ Export\n")
        f.write(f"# Object: {obj.__class__.__name__}\n")
        if comment:
            f.write(f"# {comment}\n")
        f.write(f"# Vertices: {len(vertices_3d)}\n")
        f.write(f"# Edges: {len(edges)}\n")
        f.write(f"# Faces: {len(faces)}\n")
        f.write("\n")
        
        # Vertices
        for v in vertices_3d:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        f.write("\n")
        
        # Faces (if available)
        if faces:
            for face in faces:
                # OBJ uses 1-based indexing
                indices = " ".join(str(i + 1) for i in face)
                f.write(f"f {indices}\n")
            f.write("\n")
        
        # Edges as line elements
        for a, b in edges:
            f.write(f"l {a + 1} {b + 1}\n")


def export_to_ply(
    obj: "Shape4D",
    path: str | Path,
    projection_distance: float = 5.0,
    include_colors: bool = True,
) -> None:
    """Export a 4D object to PLY format.
    
    Args:
        obj: The 4D object to export
        path: Path to save the PLY file
        projection_distance: Distance for 4D to 3D projection
        include_colors: Whether to include vertex colors
    """
    path = Path(path)
    
    # Get transformed vertices and project to 3D
    vertices_4d = np.array(obj.get_transformed_vertices())
    vertices_3d = perspective_projection_4d_to_3d(vertices_4d, projection_distance)
    
    edges = obj.edges
    
    # Get color
    color = getattr(obj, "color", (255, 255, 255))
    if len(color) == 3:
        color = (*color, 255)
    
    with open(path, "w") as f:
        # Header
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"comment HyperSim PLY Export - {obj.__class__.__name__}\n")
        f.write(f"element vertex {len(vertices_3d)}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        if include_colors:
            f.write("property uchar red\n")
            f.write("property uchar green\n")
            f.write("property uchar blue\n")
        f.write(f"element edge {len(edges)}\n")
        f.write("property int vertex1\n")
        f.write("property int vertex2\n")
        f.write("end_header\n")
        
        # Vertices
        for v in vertices_3d:
            if include_colors:
                f.write(f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f} {color[0]} {color[1]} {color[2]}\n")
            else:
                f.write(f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        
        # Edges
        for a, b in edges:
            f.write(f"{a} {b}\n")


def export_to_stl(
    obj: "Shape4D",
    path: str | Path,
    projection_distance: float = 5.0,
) -> None:
    """Export a 4D object to STL format (ASCII).
    
    Note: STL only supports triangular faces, so this will only work
    properly for objects with triangular faces or faces that can be
    triangulated.
    
    Args:
        obj: The 4D object to export
        path: Path to save the STL file
        projection_distance: Distance for 4D to 3D projection
    """
    path = Path(path)
    
    # Get transformed vertices and project to 3D
    vertices_4d = np.array(obj.get_transformed_vertices())
    vertices_3d = perspective_projection_4d_to_3d(vertices_4d, projection_distance)
    
    faces = obj.faces if hasattr(obj, 'faces') else []
    
    def compute_normal(v1, v2, v3):
        """Compute face normal from three vertices."""
        edge1 = v2 - v1
        edge2 = v3 - v1
        normal = np.cross(edge1, edge2)
        norm = np.linalg.norm(normal)
        if norm > 0:
            normal = normal / norm
        return normal
    
    def triangulate_face(face_indices):
        """Convert a polygon face to triangles using fan triangulation."""
        triangles = []
        for i in range(1, len(face_indices) - 1):
            triangles.append((face_indices[0], face_indices[i], face_indices[i + 1]))
        return triangles
    
    with open(path, "w") as f:
        f.write(f"solid {obj.__class__.__name__}\n")
        
        for face in faces:
            triangles = triangulate_face(face)
            for tri in triangles:
                v1 = vertices_3d[tri[0]]
                v2 = vertices_3d[tri[1]]
                v3 = vertices_3d[tri[2]]
                normal = compute_normal(v1, v2, v3)
                
                f.write(f"  facet normal {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}\n")
                f.write("    outer loop\n")
                f.write(f"      vertex {v1[0]:.6f} {v1[1]:.6f} {v1[2]:.6f}\n")
                f.write(f"      vertex {v2[0]:.6f} {v2[1]:.6f} {v2[2]:.6f}\n")
                f.write(f"      vertex {v3[0]:.6f} {v3[1]:.6f} {v3[2]:.6f}\n")
                f.write("    endloop\n")
                f.write("  endfacet\n")
        
        f.write(f"endsolid {obj.__class__.__name__}\n")


def export_vertices_csv(
    obj: "Shape4D",
    path: str | Path,
    include_4d: bool = True,
    projection_distance: float = 5.0,
) -> None:
    """Export object vertices to CSV format.
    
    Args:
        obj: The 4D object to export
        path: Path to save the CSV file
        include_4d: Whether to include original 4D coordinates
        projection_distance: Distance for 4D to 3D projection
    """
    path = Path(path)
    
    vertices_4d = np.array(obj.get_transformed_vertices())
    vertices_3d = perspective_projection_4d_to_3d(vertices_4d, projection_distance)
    
    with open(path, "w") as f:
        if include_4d:
            f.write("index,x4d,y4d,z4d,w4d,x3d,y3d,z3d\n")
            for i, (v4, v3) in enumerate(zip(vertices_4d, vertices_3d)):
                f.write(f"{i},{v4[0]:.6f},{v4[1]:.6f},{v4[2]:.6f},{v4[3]:.6f},")
                f.write(f"{v3[0]:.6f},{v3[1]:.6f},{v3[2]:.6f}\n")
        else:
            f.write("index,x,y,z\n")
            for i, v in enumerate(vertices_3d):
                f.write(f"{i},{v[0]:.6f},{v[1]:.6f},{v[2]:.6f}\n")


def export_edges_csv(
    obj: "Shape4D",
    path: str | Path,
) -> None:
    """Export object edges to CSV format.
    
    Args:
        obj: The 4D object to export
        path: Path to save the CSV file
    """
    path = Path(path)
    
    with open(path, "w") as f:
        f.write("index,vertex1,vertex2\n")
        for i, (a, b) in enumerate(obj.edges):
            f.write(f"{i},{a},{b}\n")
