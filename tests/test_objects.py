"""Unit tests for hypersim.objects module."""
import numpy as np
import pytest

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
)


class TestHypercube:
    """Tests for Hypercube (Tesseract)."""

    def test_vertex_count(self):
        """Tesseract has 16 vertices."""
        cube = Hypercube(size=1.0)
        assert cube.vertex_count == 16

    def test_edge_count(self):
        """Tesseract has 32 edges."""
        cube = Hypercube(size=1.0)
        assert cube.edge_count == 32

    def test_edges_valid(self):
        """All edge indices should be valid."""
        cube = Hypercube(size=1.0)
        for a, b in cube.edges:
            assert 0 <= a < cube.vertex_count
            assert 0 <= b < cube.vertex_count

    def test_size_scaling(self):
        """Test that size parameter affects vertex positions."""
        cube1 = Hypercube(size=1.0)
        cube2 = Hypercube(size=2.0)
        v1 = np.array(cube1.vertices)
        v2 = np.array(cube2.vertices)
        # cube2 should have vertices twice as far from origin
        assert np.allclose(np.abs(v2), np.abs(v1) * 2)


class TestSimplex4D:
    """Tests for 4D Simplex (5-cell)."""

    def test_vertex_count(self):
        """5-cell has 5 vertices."""
        simplex = Simplex4D(size=1.0)
        assert simplex.vertex_count == 5

    def test_edge_count(self):
        """5-cell has 10 edges (fully connected)."""
        simplex = Simplex4D(size=1.0)
        assert simplex.edge_count == 10

    def test_fully_connected(self):
        """All vertices should be connected to all others."""
        simplex = Simplex4D(size=1.0)
        # 5 choose 2 = 10 edges
        assert simplex.edge_count == 5 * 4 // 2


class TestSixteenCell:
    """Tests for 16-cell (Hyperoctahedron)."""

    def test_vertex_count(self):
        """16-cell has 8 vertices."""
        cell = SixteenCell(size=1.0)
        assert cell.vertex_count == 8

    def test_edge_count(self):
        """16-cell has 24 edges."""
        cell = SixteenCell(size=1.0)
        assert cell.edge_count == 24

    def test_vertices_on_axes(self):
        """Vertices should be on coordinate axes."""
        cell = SixteenCell(size=1.0)
        for v in cell.vertices:
            # Each vertex has exactly one non-zero coordinate
            non_zero = np.count_nonzero(v)
            assert non_zero == 1


class TestTwentyFourCell:
    """Tests for 24-cell."""

    def test_vertex_count(self):
        """24-cell has 24 vertices."""
        cell = TwentyFourCell(size=1.0)
        assert cell.vertex_count == 24

    def test_edge_count(self):
        """24-cell has 96 edges."""
        cell = TwentyFourCell(size=1.0)
        assert cell.edge_count == 96


class TestDuoprism:
    """Tests for Duoprism."""

    def test_vertex_count_3x4(self):
        """3x4 duoprism has 12 vertices."""
        duo = Duoprism(m=3, n=4, size=1.0)
        assert duo.vertex_count == 12

    def test_vertex_count_5x5(self):
        """5x5 duoprism has 25 vertices."""
        duo = Duoprism(m=5, n=5, size=1.0)
        assert duo.vertex_count == 25


class TestHypercubeGrid:
    """Tests for HypercubeGrid."""

    def test_vertex_count_2(self):
        """2x2x2x2 grid has 16 vertices."""
        grid = HypercubeGrid(divisions=2, size=1.0)
        assert grid.vertex_count == 16

    def test_vertex_count_3(self):
        """3x3x3x3 grid has 81 vertices."""
        grid = HypercubeGrid(divisions=3, size=1.0)
        assert grid.vertex_count == 81


class TestCliffordTorus:
    """Tests for Clifford Torus."""

    def test_vertices_on_unit_sphere(self):
        """Clifford torus vertices should lie on S3."""
        torus = CliffordTorus(segments_u=10, segments_v=10, size=1.0)
        for v in torus.vertices:
            # Should have length 1 (on S3)
            length = np.linalg.norm(v)
            assert np.isclose(length, 1.0, rtol=0.1)


class TestSixHundredCell:
    """Tests for 600-cell."""

    def test_vertex_count(self):
        """600-cell has 120 vertices."""
        cell = SixHundredCell(size=1.0)
        assert cell.vertex_count == 120

    def test_edge_count(self):
        """600-cell has 720 edges."""
        cell = SixHundredCell(size=1.0)
        assert cell.edge_count == 720


class TestPrisms:
    """Tests for various prism objects."""

    def test_simplex_prism(self):
        """SimplexPrism should have 10 vertices."""
        prism = SimplexPrism(size=1.0, height=1.0)
        assert prism.vertex_count == 10

    def test_cube_prism(self):
        """CubePrism should have 16 vertices."""
        prism = CubePrism(size=1.0, height=1.0)
        assert prism.vertex_count == 16

    def test_tetra_prism(self):
        """TetraPrism should have 8 vertices."""
        prism = TetraPrism(size=1.0, height=1.0)
        assert prism.vertex_count == 8

    def test_octa_prism(self):
        """OctaPrism should have 12 vertices."""
        prism = OctaPrism(size=1.0, height=1.0)
        assert prism.vertex_count == 12


class TestManifolds:
    """Tests for manifold objects."""

    def test_spherinder_has_vertices(self):
        """Spherinder should have vertices."""
        sph = Spherinder(radius=1.0, height=1.0, segments=12, stacks=6)
        assert sph.vertex_count > 0

    def test_mobius_has_vertices(self):
        """Mobius4D should have vertices."""
        mob = Mobius4D(radius=1.0, width=0.5, segments_u=20, segments_v=5)
        assert mob.vertex_count > 0

    def test_torus_knot_has_vertices(self):
        """TorusKnot4D should have vertices."""
        knot = TorusKnot4D(p=2, q=3, segments=50, radius=1.0)
        assert knot.vertex_count > 0

    def test_hopf_link_has_vertices(self):
        """HopfLink4D should have vertices."""
        link = HopfLink4D(radius=1.0, segments=50)
        assert link.vertex_count > 0


class TestEdgeValidity:
    """Test that all objects have valid edge indices."""

    @pytest.mark.parametrize("obj_class,kwargs", [
        (Hypercube, {"size": 1.0}),
        (Simplex4D, {"size": 1.0}),
        (SixteenCell, {"size": 1.0}),
        (TwentyFourCell, {"size": 1.0}),
        (Duoprism, {"m": 3, "n": 4, "size": 1.0}),
        (HypercubeGrid, {"divisions": 2, "size": 1.0}),
        (CliffordTorus, {"segments_u": 8, "segments_v": 8, "size": 1.0}),
        (SimplexPrism, {"size": 1.0, "height": 1.0}),
        (RectifiedTesseract, {"size": 1.0}),
        (CubePrism, {"size": 1.0, "height": 1.0}),
        (Spherinder, {"radius": 1.0, "height": 1.0, "segments": 8, "stacks": 4}),
        (TetraPrism, {"size": 1.0, "height": 1.0}),
        (OctaPrism, {"size": 1.0, "height": 1.0}),
    ])
    def test_edge_indices_valid(self, obj_class, kwargs):
        """All edge indices should reference valid vertices."""
        obj = obj_class(**kwargs)
        for a, b in obj.edges:
            assert 0 <= a < obj.vertex_count, f"Invalid edge start {a}"
            assert 0 <= b < obj.vertex_count, f"Invalid edge end {b}"
