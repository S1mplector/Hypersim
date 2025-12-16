"""Unit tests for hypersim.core.shape_4d module."""
import numpy as np
import pytest

from hypersim.core.shape_4d import Shape4D
from hypersim.objects import Hypercube, Simplex4D, SixteenCell


class TestShape4DTransformations:
    """Tests for Shape4D transformation methods."""

    def test_default_position(self):
        """Test that default position is origin."""
        cube = Hypercube(size=1.0)
        assert np.allclose(cube.position, [0.0, 0.0, 0.0, 0.0])

    def test_set_position_array(self):
        """Test setting position with array."""
        cube = Hypercube(size=1.0)
        cube.set_position([1.0, 2.0, 3.0, 4.0])
        assert np.allclose(cube.position, [1.0, 2.0, 3.0, 4.0])

    def test_set_position_kwargs(self):
        """Test setting position with keyword arguments."""
        cube = Hypercube(size=1.0)
        cube.set_position(x=1.0, y=2.0)
        assert cube.position[0] == 1.0
        assert cube.position[1] == 2.0

    def test_translate(self):
        """Test translation."""
        cube = Hypercube(size=1.0)
        cube.set_position([0.0, 0.0, 0.0, 0.0])
        cube.translate(1.0, 2.0, 3.0, 4.0)
        assert np.allclose(cube.position, [1.0, 2.0, 3.0, 4.0])

    def test_rotate(self):
        """Test rotation accumulation."""
        cube = Hypercube(size=1.0)
        initial_xy = cube.rotation['xy']
        cube.rotate(xy=0.5)
        assert np.isclose(cube.rotation['xy'], (initial_xy + 0.5) % (2 * np.pi))

    def test_set_rotation(self):
        """Test setting rotation directly."""
        cube = Hypercube(size=1.0)
        cube.set_rotation(xy=1.0, xw=0.5)
        assert np.isclose(cube.rotation['xy'], 1.0)
        assert np.isclose(cube.rotation['xw'], 0.5)

    def test_set_scale(self):
        """Test setting scale."""
        cube = Hypercube(size=1.0)
        cube.set_scale(2.0)
        assert cube.scale == 2.0

    def test_transform_matrix_updates(self):
        """Test that transform matrix is marked dirty on changes."""
        cube = Hypercube(size=1.0)
        cube._transform_dirty = False
        cube.rotate(xy=0.1)
        assert cube._transform_dirty


class TestShape4DBoundingBox:
    """Tests for Shape4D bounding box."""

    def test_hypercube_bounding_box(self):
        """Test hypercube bounding box at origin."""
        cube = Hypercube(size=2.0)
        min_corner, max_corner = cube.get_bounding_box()
        # Size 2.0 means vertices at ±1
        assert np.all(min_corner <= -0.9)
        assert np.all(max_corner >= 0.9)

    def test_translated_bounding_box(self):
        """Test bounding box after translation."""
        cube = Hypercube(size=2.0)
        cube.set_position([10.0, 0.0, 0.0, 0.0])
        min_corner, max_corner = cube.get_bounding_box()
        assert min_corner[0] > 8.0
        assert max_corner[0] < 12.0


class TestShape4DVertexTransform:
    """Tests for Shape4D vertex transformation."""

    def test_transformed_vertices_count(self):
        """Test that transformed vertices count matches original."""
        cube = Hypercube(size=1.0)
        transformed = cube.get_transformed_vertices()
        assert len(transformed) == len(cube.vertices)

    def test_translation_applied(self):
        """Test that translation is applied to vertices."""
        cube = Hypercube(size=1.0)
        cube.set_position([100.0, 0.0, 0.0, 0.0])
        transformed = cube.get_transformed_vertices()
        # All x coordinates should be around 100
        for v in transformed:
            assert v[0] > 99.0

    def test_scale_applied(self):
        """Test that scale is applied to vertices."""
        cube = Hypercube(size=1.0)
        original = cube.get_transformed_vertices()
        cube.set_scale(2.0)
        scaled = cube.get_transformed_vertices()
        # Vertices should be further from origin
        orig_dist = np.linalg.norm(original[0])
        scaled_dist = np.linalg.norm(scaled[0])
        assert np.isclose(scaled_dist, orig_dist * 2.0, rtol=0.1)


class TestShape4DProperties:
    """Tests for Shape4D property methods."""

    def test_vertex_count(self):
        """Test vertex_count property."""
        cube = Hypercube(size=1.0)
        assert cube.vertex_count == 16

    def test_edge_count(self):
        """Test edge_count property."""
        cube = Hypercube(size=1.0)
        assert cube.edge_count == 32

    def test_get_methods(self):
        """Test get_* method aliases."""
        cube = Hypercube(size=1.0)
        assert cube.get_vertex_count() == cube.vertex_count
        assert cube.get_edge_count() == cube.edge_count
        assert cube.get_face_count() == cube.face_count
        assert cube.get_cell_count() == cube.cell_count


class TestShape4DVisibility:
    """Tests for Shape4D visibility checking."""

    def test_visible_by_default(self):
        """Test that shapes are visible by default."""
        cube = Hypercube(size=1.0)
        assert cube.visible

    def test_is_visible_method(self):
        """Test is_visible method."""
        cube = Hypercube(size=1.0)
        # Camera close enough to see the object (within FOV distance)
        camera_pos = np.array([0.0, 0.0, -2.0, 0.0])
        assert cube.is_visible(camera_pos)

    def test_hidden_shape(self):
        """Test that hidden shapes report not visible."""
        cube = Hypercube(size=1.0)
        cube.visible = False
        camera_pos = np.array([0.0, 0.0, -10.0, 0.0])
        assert not cube.is_visible(camera_pos)
