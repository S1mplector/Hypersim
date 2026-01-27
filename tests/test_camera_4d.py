"""Unit tests for the Camera4D projection pipeline."""
import numpy as np

from hypersim.visualization.renderers.pygame.camera_4d import Camera4D


def test_project_origin_center_default():
    """Origin should project to the screen center with default camera settings."""
    camera = Camera4D(screen_width=800, screen_height=600)
    x, y, _ = camera.project_4d_to_2d(np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32))
    assert abs(x - 400) <= 1
    assert abs(y - 300) <= 1


def test_target_stays_center_when_camera_moves():
    """Looking at the target should keep it centered after moving the camera."""
    camera = Camera4D(screen_width=800, screen_height=600)
    camera.set_position(5.0, 0.0, 0.0, 0.0)
    x, y, _ = camera.project_4d_to_2d(np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32))
    assert abs(x - 400) <= 1
    assert abs(y - 300) <= 1


def test_batch_projection_matches_single_projection():
    """Batch projection should match per-point projection results."""
    camera = Camera4D(screen_width=640, screen_height=480)
    camera.set_position(1.5, -0.5, -3.0, 0.2)
    points = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, -1.0, 0.5],
        [-1.0, -0.5, 0.75, -0.25],
    ], dtype=np.float32)

    screen_coords, depths = camera.batch_project_4d_to_2d(points)
    for idx, point in enumerate(points):
        x, y, depth = camera.project_4d_to_2d(point)
        assert screen_coords[idx, 0] == x
        assert screen_coords[idx, 1] == y
        assert np.isclose(depths[idx], depth)
