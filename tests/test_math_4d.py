"""Unit tests for hypersim.core.math_4d module."""
import numpy as np
import pytest
import math

from hypersim.core.math_4d import (
    create_vector_4d,
    create_translation_matrix_4d,
    create_scale_matrix_4d,
    create_rotation_matrix_4d,
    perspective_projection_4d_to_3d,
    normalize_vector,
    dot_product_4d,
    cross_product_4d,
    create_look_at_matrix,
)


class TestCreateVector4D:
    """Tests for create_vector_4d function."""

    def test_default_vector(self):
        """Test creating a default zero vector."""
        v = create_vector_4d()
        assert v.shape == (4,)
        assert np.allclose(v, [0.0, 0.0, 0.0, 0.0])

    def test_custom_vector(self):
        """Test creating a vector with custom values."""
        v = create_vector_4d(1.0, 2.0, 3.0, 4.0)
        assert np.allclose(v, [1.0, 2.0, 3.0, 4.0])

    def test_dtype(self):
        """Test that the vector has float32 dtype."""
        v = create_vector_4d(1, 2, 3, 4)
        assert v.dtype == np.float32


class TestCreateTranslationMatrix4D:
    """Tests for create_translation_matrix_4d function."""

    def test_identity_translation(self):
        """Test that zero translation gives identity-like matrix."""
        m = create_translation_matrix_4d()
        expected = np.eye(4, dtype=np.float32)
        assert np.allclose(m, expected)

    def test_translation_values(self):
        """Test that translation values are placed correctly."""
        m = create_translation_matrix_4d(1.0, 2.0, 3.0, 4.0)
        assert m[0, 3] == 1.0
        assert m[1, 3] == 2.0
        assert m[2, 3] == 3.0
        # Note: W translation is handled separately in Shape4D, not in this matrix
        assert m[3, 3] == 1.0  # Diagonal stays 1


class TestCreateScaleMatrix4D:
    """Tests for create_scale_matrix_4d function."""

    def test_identity_scale(self):
        """Test that unit scale gives identity matrix."""
        m = create_scale_matrix_4d()
        expected = np.eye(4, dtype=np.float32)
        assert np.allclose(m, expected)

    def test_uniform_scale(self):
        """Test uniform scaling."""
        m = create_scale_matrix_4d(2.0, 2.0, 2.0, 2.0)
        expected = np.diag([2.0, 2.0, 2.0, 2.0]).astype(np.float32)
        assert np.allclose(m, expected)

    def test_non_uniform_scale(self):
        """Test non-uniform scaling."""
        m = create_scale_matrix_4d(1.0, 2.0, 3.0, 4.0)
        v = np.array([1.0, 1.0, 1.0, 1.0])
        result = m @ v
        assert np.allclose(result, [1.0, 2.0, 3.0, 4.0])


class TestCreateRotationMatrix4D:
    """Tests for create_rotation_matrix_4d function."""

    def test_identity_rotation(self):
        """Test that zero angles give identity matrix."""
        m = create_rotation_matrix_4d()
        expected = np.eye(4, dtype=np.float32)
        assert np.allclose(m, expected)

    def test_rotation_xy_90(self):
        """Test 90-degree rotation in XY plane."""
        m = create_rotation_matrix_4d(angle_xy=math.pi / 2)
        v = np.array([1.0, 0.0, 0.0, 0.0])
        result = m @ v
        expected = np.array([0.0, 1.0, 0.0, 0.0])
        assert np.allclose(result, expected, atol=1e-6)

    def test_rotation_preserves_length(self):
        """Test that rotation preserves vector length."""
        m = create_rotation_matrix_4d(angle_xy=0.5, angle_xw=0.3, angle_zw=0.7)
        v = np.array([1.0, 2.0, 3.0, 4.0])
        result = m @ v
        assert np.isclose(np.linalg.norm(v), np.linalg.norm(result))

    def test_rotation_is_orthogonal(self):
        """Test that rotation matrix is orthogonal."""
        m = create_rotation_matrix_4d(angle_xy=0.5, angle_xz=0.3, angle_yw=0.7)
        identity = m @ m.T
        assert np.allclose(identity, np.eye(4), atol=1e-6)


class TestPerspectiveProjection4DTo3D:
    """Tests for perspective_projection_4d_to_3d function."""

    def test_single_point(self):
        """Test projecting a single point."""
        points = np.array([[1.0, 2.0, 3.0, 0.0]])
        result = perspective_projection_4d_to_3d(points, distance=5.0)
        assert result.shape == (1, 3)

    def test_origin_projection(self):
        """Test that origin projects to origin."""
        points = np.array([[0.0, 0.0, 0.0, 0.0]])
        result = perspective_projection_4d_to_3d(points, distance=5.0)
        assert np.allclose(result, [[0.0, 0.0, 0.0]])

    def test_multiple_points(self):
        """Test projecting multiple points."""
        points = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
        ])
        result = perspective_projection_4d_to_3d(points, distance=5.0)
        assert result.shape == (3, 3)

    def test_w_affects_scale(self):
        """Test that W coordinate affects projection scale."""
        p1 = np.array([[1.0, 0.0, 0.0, 0.0]])
        p2 = np.array([[1.0, 0.0, 0.0, 2.0]])
        r1 = perspective_projection_4d_to_3d(p1, distance=5.0)
        r2 = perspective_projection_4d_to_3d(p2, distance=5.0)
        # Point with larger W should be scaled differently
        assert not np.allclose(r1[0, 0], r2[0, 0])


class TestNormalizeVector:
    """Tests for normalize_vector function."""

    def test_unit_vector(self):
        """Test that a unit vector stays unit."""
        v = np.array([1.0, 0.0, 0.0, 0.0])
        result = normalize_vector(v)
        assert np.allclose(result, v)

    def test_normalize_to_unit(self):
        """Test normalization produces unit length."""
        v = np.array([3.0, 4.0, 0.0, 0.0])
        result = normalize_vector(v)
        assert np.isclose(np.linalg.norm(result), 1.0)

    def test_zero_vector(self):
        """Test that zero vector returns zero vector."""
        v = np.array([0.0, 0.0, 0.0, 0.0])
        result = normalize_vector(v)
        assert np.allclose(result, v)

    def test_4d_vector(self):
        """Test normalizing a 4D vector."""
        v = np.array([1.0, 1.0, 1.0, 1.0])
        result = normalize_vector(v)
        expected_length = 1.0
        assert np.isclose(np.linalg.norm(result), expected_length)


class TestDotProduct4D:
    """Tests for dot_product_4d function."""

    def test_orthogonal_vectors(self):
        """Test dot product of orthogonal vectors is zero."""
        v1 = np.array([1.0, 0.0, 0.0, 0.0])
        v2 = np.array([0.0, 1.0, 0.0, 0.0])
        assert dot_product_4d(v1, v2) == 0.0

    def test_parallel_vectors(self):
        """Test dot product of parallel vectors."""
        v1 = np.array([1.0, 0.0, 0.0, 0.0])
        v2 = np.array([2.0, 0.0, 0.0, 0.0])
        assert dot_product_4d(v1, v2) == 2.0

    def test_general_dot_product(self):
        """Test general dot product."""
        v1 = np.array([1.0, 2.0, 3.0, 4.0])
        v2 = np.array([5.0, 6.0, 7.0, 8.0])
        expected = 1*5 + 2*6 + 3*7 + 4*8
        assert dot_product_4d(v1, v2) == expected


class TestCrossProduct4D:
    """Tests for cross_product_4d function."""

    def test_orthogonal_result(self):
        """Test that result is orthogonal to all inputs."""
        a = np.array([1.0, 0.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0, 0.0])
        c = np.array([0.0, 0.0, 1.0, 0.0])
        result = cross_product_4d(a, b, c)
        assert np.isclose(np.dot(result, a), 0.0, atol=1e-6)
        assert np.isclose(np.dot(result, b), 0.0, atol=1e-6)
        assert np.isclose(np.dot(result, c), 0.0, atol=1e-6)

    def test_standard_basis(self):
        """Test cross product of standard basis vectors."""
        a = np.array([1.0, 0.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0, 0.0])
        c = np.array([0.0, 0.0, 1.0, 0.0])
        result = cross_product_4d(a, b, c)
        # Should point in W direction
        expected = np.array([0.0, 0.0, 0.0, -1.0])
        assert np.allclose(result, expected, atol=1e-6)


class TestCreateLookAtMatrix:
    """Tests for create_look_at_matrix function."""

    def test_basic_look_at(self):
        """Test basic look-at matrix creation."""
        eye = np.array([0.0, 0.0, -5.0, 0.0])
        target = np.array([0.0, 0.0, 0.0, 0.0])
        up = np.array([0.0, 1.0, 0.0, 0.0])
        m = create_look_at_matrix(eye, target, up)
        assert m.shape == (4, 4)

    def test_orthonormal_result(self):
        """Test that result is orthonormal."""
        eye = np.array([1.0, 2.0, 3.0, 0.5])
        target = np.array([0.0, 0.0, 0.0, 0.0])
        up = np.array([0.0, 1.0, 0.0, 0.0])
        m = create_look_at_matrix(eye, target, up)
        identity = m @ m.T
        assert np.allclose(identity, np.eye(4), atol=1e-5)
