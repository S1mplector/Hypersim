"""Interactive object browser CLI.

Provides a command-line interface for browsing and exploring
4D objects without launching a graphical window.
"""
from __future__ import annotations

import sys
from typing import Dict, List, Optional, Type, Any

from hypersim.core.shape_4d import Shape4D
from hypersim.objects import (
    Hypercube,
    Simplex4D,
    SixteenCell,
    TwentyFourCell,
    Duoprism,
    HypercubeGrid,
    CliffordTorus,
    SimplexPrism,
    RectifiedTesseract,
    CubePrism,
    Spherinder,
    Mobius4D,
    IcosaPrism,
    PenteractFrame,
    DodecaPrism,
    SixHundredCell,
    TetraPrism,
    OctaPrism,
    TorusKnot4D,
    HopfLink4D,
    OneHundredTwentyCell,
    GrandAntiprism,
    RuncinatedTesseract,
    TruncatedTesseract,
)


# Registry of all available objects
OBJECT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "hypercube": {
        "class": Hypercube,
        "category": "Regular Polytopes",
        "description": "4D hypercube (tesseract) with 16 vertices, 32 edges",
        "params": {"size": 1.0},
    },
    "simplex": {
        "class": Simplex4D,
        "category": "Regular Polytopes",
        "description": "4D simplex (5-cell) with 5 vertices, 10 edges",
        "params": {"size": 1.0},
    },
    "16cell": {
        "class": SixteenCell,
        "category": "Regular Polytopes",
        "description": "16-cell (hyperoctahedron) with 8 vertices, 24 edges",
        "params": {"size": 1.0},
    },
    "24cell": {
        "class": TwentyFourCell,
        "category": "Regular Polytopes",
        "description": "Self-dual 24-cell with 24 vertices, 96 edges",
        "params": {"size": 1.0},
    },
    "600cell": {
        "class": SixHundredCell,
        "category": "Regular Polytopes",
        "description": "600-cell with 120 vertices, 720 edges",
        "params": {"size": 1.0},
    },
    "120cell": {
        "class": OneHundredTwentyCell,
        "category": "Regular Polytopes",
        "description": "120-cell with 600 vertices, 1200 edges",
        "params": {"size": 1.0},
    },
    "duoprism": {
        "class": Duoprism,
        "category": "Products",
        "description": "Cartesian product of two polygons",
        "params": {"m": 3, "n": 4, "size": 1.0},
    },
    "cube_prism": {
        "class": CubePrism,
        "category": "Prisms",
        "description": "3D cube extruded in W direction",
        "params": {"size": 1.0, "height": 1.0},
    },
    "tetra_prism": {
        "class": TetraPrism,
        "category": "Prisms",
        "description": "Tetrahedron extruded in W direction",
        "params": {"size": 1.0, "height": 1.0},
    },
    "octa_prism": {
        "class": OctaPrism,
        "category": "Prisms",
        "description": "Octahedron extruded in W direction",
        "params": {"size": 1.0, "height": 1.0},
    },
    "simplex_prism": {
        "class": SimplexPrism,
        "category": "Prisms",
        "description": "4D simplex extruded in W direction",
        "params": {"size": 1.0, "height": 1.0},
    },
    "icosa_prism": {
        "class": IcosaPrism,
        "category": "Prisms",
        "description": "Icosahedron extruded in W direction",
        "params": {"size": 1.0, "height": 1.0},
    },
    "dodeca_prism": {
        "class": DodecaPrism,
        "category": "Prisms",
        "description": "Dodecahedron extruded in W direction",
        "params": {"size": 1.0, "height": 1.0},
    },
    "clifford_torus": {
        "class": CliffordTorus,
        "category": "Manifolds",
        "description": "Flat torus embedded in S³",
        "params": {"segments_u": 20, "segments_v": 20, "size": 1.0},
    },
    "spherinder": {
        "class": Spherinder,
        "category": "Manifolds",
        "description": "Sphere × interval (spherical cylinder)",
        "params": {"radius": 1.0, "height": 1.0, "segments": 16, "stacks": 8},
    },
    "mobius_4d": {
        "class": Mobius4D,
        "category": "Manifolds",
        "description": "Möbius strip embedded in 4D",
        "params": {"radius": 1.0, "width": 0.5, "segments_u": 40, "segments_v": 10},
    },
    "torus_knot": {
        "class": TorusKnot4D,
        "category": "Manifolds",
        "description": "Torus knot on Clifford torus",
        "params": {"p": 3, "q": 5, "segments": 100, "radius": 1.0},
    },
    "hopf_link": {
        "class": HopfLink4D,
        "category": "Manifolds",
        "description": "Two linked circles in 4D",
        "params": {"radius": 1.0, "segments": 60},
    },
    "hypercube_grid": {
        "class": HypercubeGrid,
        "category": "Lattices",
        "description": "Regular 4D lattice grid",
        "params": {"divisions": 3, "size": 1.0},
    },
    "rectified_tesseract": {
        "class": RectifiedTesseract,
        "category": "Uniform Polytopes",
        "description": "Rectified hypercube with 24 vertices",
        "params": {"size": 1.0},
    },
    "penteract_frame": {
        "class": PenteractFrame,
        "category": "Higher Dimensional",
        "description": "5D hypercube projected to 4D",
        "params": {"size": 1.0},
    },
    "grand_antiprism": {
        "class": GrandAntiprism,
        "category": "Uniform Polytopes",
        "description": "Grand antiprism with 100 vertices",
        "params": {"size": 1.0},
    },
    "runcinated_tesseract": {
        "class": RuncinatedTesseract,
        "category": "Uniform Polytopes",
        "description": "Runcinated hypercube with 64 vertices",
        "params": {"size": 1.0},
    },
    "truncated_tesseract": {
        "class": TruncatedTesseract,
        "category": "Uniform Polytopes",
        "description": "Truncated hypercube with 64 vertices",
        "params": {"size": 1.0},
    },
}


def get_categories() -> Dict[str, List[str]]:
    """Get objects organized by category."""
    categories: Dict[str, List[str]] = {}
    for name, info in OBJECT_REGISTRY.items():
        cat = info["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(name)
    return categories


def create_object(name: str, **kwargs) -> Optional[Shape4D]:
    """Create an object by name with optional parameter overrides."""
    if name not in OBJECT_REGISTRY:
        return None
    
    info = OBJECT_REGISTRY[name]
    params = dict(info["params"])
    params.update(kwargs)
    
    return info["class"](**params)


def print_object_info(name: str, obj: Shape4D) -> None:
    """Print detailed information about an object."""
    info = OBJECT_REGISTRY.get(name, {})
    
    print(f"\n{'=' * 50}")
    print(f"  {name.upper()}")
    print(f"{'=' * 50}")
    print(f"Category:    {info.get('category', 'Unknown')}")
    print(f"Description: {info.get('description', 'N/A')}")
    print(f"\nGeometry:")
    print(f"  Vertices: {obj.vertex_count}")
    print(f"  Edges:    {obj.edge_count}")
    print(f"  Faces:    {obj.face_count}")
    print(f"  Cells:    {obj.cell_count}")
    
    # Bounding box
    min_corner, max_corner = obj.get_bounding_box()
    print(f"\nBounding Box:")
    print(f"  Min: ({min_corner[0]:.3f}, {min_corner[1]:.3f}, {min_corner[2]:.3f}, {min_corner[3]:.3f})")
    print(f"  Max: ({max_corner[0]:.3f}, {max_corner[1]:.3f}, {max_corner[2]:.3f}, {max_corner[3]:.3f})")
    
    # Parameters
    print(f"\nDefault Parameters:")
    for key, val in info.get("params", {}).items():
        print(f"  {key}: {val}")


def print_help() -> None:
    """Print help information."""
    print("""
HyperSim Object Browser
=======================

Commands:
  list              List all available objects
  list <category>   List objects in a category
  info <name>       Show detailed info about an object
  create <name>     Create an object and show its stats
  compare <n1> <n2> Compare two objects
  export <name> <f> Export object to file
  help              Show this help
  quit              Exit the browser

Examples:
  list Regular Polytopes
  info hypercube
  create duoprism m=5 n=6
  compare hypercube 16cell
""")


def run_browser() -> None:
    """Run the interactive object browser."""
    print("\nHyperSim Interactive Object Browser")
    print("Type 'help' for commands, 'quit' to exit\n")
    
    while True:
        try:
            line = input("hypersim> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if not line:
            continue
        
        parts = line.split()
        cmd = parts[0].lower()
        args = parts[1:]
        
        if cmd == "quit" or cmd == "exit":
            print("Goodbye!")
            break
        
        elif cmd == "help":
            print_help()
        
        elif cmd == "list":
            if args:
                # List specific category
                cat_name = " ".join(args)
                categories = get_categories()
                found = False
                for cat, names in categories.items():
                    if cat.lower() == cat_name.lower():
                        print(f"\n{cat}:")
                        for name in sorted(names):
                            desc = OBJECT_REGISTRY[name]["description"]
                            print(f"  {name:20} - {desc}")
                        found = True
                        break
                if not found:
                    print(f"Unknown category: {cat_name}")
                    print("Available categories:", ", ".join(get_categories().keys()))
            else:
                # List all
                categories = get_categories()
                for cat in sorted(categories.keys()):
                    print(f"\n{cat}:")
                    for name in sorted(categories[cat]):
                        desc = OBJECT_REGISTRY[name]["description"]
                        print(f"  {name:20} - {desc}")
        
        elif cmd == "info":
            if not args:
                print("Usage: info <object_name>")
                continue
            name = args[0].lower()
            if name not in OBJECT_REGISTRY:
                print(f"Unknown object: {name}")
                print("Use 'list' to see available objects")
                continue
            obj = create_object(name)
            print_object_info(name, obj)
        
        elif cmd == "create":
            if not args:
                print("Usage: create <object_name> [param=value ...]")
                continue
            name = args[0].lower()
            if name not in OBJECT_REGISTRY:
                print(f"Unknown object: {name}")
                continue
            
            # Parse parameters
            params = {}
            for arg in args[1:]:
                if "=" in arg:
                    key, val = arg.split("=", 1)
                    try:
                        params[key] = float(val) if "." in val else int(val)
                    except ValueError:
                        params[key] = val
            
            obj = create_object(name, **params)
            if obj:
                print_object_info(name, obj)
        
        elif cmd == "compare":
            if len(args) < 2:
                print("Usage: compare <object1> <object2>")
                continue
            
            name1, name2 = args[0].lower(), args[1].lower()
            obj1 = create_object(name1)
            obj2 = create_object(name2)
            
            if not obj1:
                print(f"Unknown object: {name1}")
                continue
            if not obj2:
                print(f"Unknown object: {name2}")
                continue
            
            print(f"\n{'Property':<15} {name1:>15} {name2:>15}")
            print("-" * 47)
            print(f"{'Vertices':<15} {obj1.vertex_count:>15} {obj2.vertex_count:>15}")
            print(f"{'Edges':<15} {obj1.edge_count:>15} {obj2.edge_count:>15}")
            print(f"{'Faces':<15} {obj1.face_count:>15} {obj2.face_count:>15}")
            print(f"{'Cells':<15} {obj1.cell_count:>15} {obj2.cell_count:>15}")
        
        elif cmd == "export":
            if len(args) < 2:
                print("Usage: export <object_name> <filename>")
                continue
            
            name = args[0].lower()
            filename = args[1]
            
            obj = create_object(name)
            if not obj:
                print(f"Unknown object: {name}")
                continue
            
            try:
                if filename.endswith(".obj"):
                    from hypersim.io import export_to_obj
                    export_to_obj(obj, filename)
                elif filename.endswith(".ply"):
                    from hypersim.io import export_to_ply
                    export_to_ply(obj, filename)
                elif filename.endswith(".json"):
                    from hypersim.io import save_object
                    save_object(obj, filename)
                else:
                    print("Supported formats: .obj, .ply, .json")
                    continue
                print(f"Exported to {filename}")
            except Exception as e:
                print(f"Export failed: {e}")
        
        else:
            print(f"Unknown command: {cmd}")
            print("Type 'help' for available commands")


if __name__ == "__main__":
    run_browser()
