"""Example: Export 4D objects to various file formats.

This example demonstrates how to export 4D objects to OBJ, PLY,
STL, and CSV formats for use in other 3D software.
"""
import os
from pathlib import Path

from hypersim.objects import Hypercube, Simplex4D, SixteenCell
from hypersim.io import (
    export_to_obj,
    export_to_ply,
    export_vertices_csv,
    export_edges_csv,
    save_object,
)


def main():
    # Create output directory
    output_dir = Path("hypersim_exports")
    output_dir.mkdir(exist_ok=True)
    
    print("HyperSim Export Example")
    print("=" * 40)
    
    # Create and configure objects
    cube = Hypercube(size=1.5)
    cube.rotate(xy=0.3, xw=0.2, yw=0.15, zw=0.1)
    
    simplex = Simplex4D(size=1.5)
    simplex.rotate(xy=0.4, xw=0.25)
    
    cell16 = SixteenCell(size=1.2)
    cell16.rotate(xz=0.3, yw=0.2)
    
    objects = [
        ("hypercube", cube),
        ("simplex", simplex),
        ("16cell", cell16),
    ]
    
    for name, obj in objects:
        print(f"\nExporting {name}...")
        
        # Export to OBJ (widely supported 3D format)
        obj_path = output_dir / f"{name}.obj"
        export_to_obj(obj, obj_path, projection_distance=5.0)
        print(f"  - OBJ: {obj_path}")
        
        # Export to PLY (with colors)
        ply_path = output_dir / f"{name}.ply"
        export_to_ply(obj, ply_path, projection_distance=5.0)
        print(f"  - PLY: {ply_path}")
        
        # Export vertices to CSV
        csv_path = output_dir / f"{name}_vertices.csv"
        export_vertices_csv(obj, csv_path, include_4d=True)
        print(f"  - Vertices CSV: {csv_path}")
        
        # Export edges to CSV
        edges_path = output_dir / f"{name}_edges.csv"
        export_edges_csv(obj, edges_path)
        print(f"  - Edges CSV: {edges_path}")
        
        # Save object state (can be loaded back)
        state_path = output_dir / f"{name}_state.json"
        save_object(obj, state_path)
        print(f"  - State JSON: {state_path}")
    
    print("\n" + "=" * 40)
    print(f"All exports saved to: {output_dir.absolute()}")
    print("\nYou can import the OBJ/PLY files into Blender, MeshLab,")
    print("or other 3D software to view the projected 4D shapes.")


if __name__ == "__main__":
    main()
