from numpy.testing import assert_equal, assert_almost_equal
import numpy as np

from skimage.measure import profile_line

image = np.arange(100, dtype=np.float).reshape((10, 10))


def test_horizontal_rightward():
    prof = profile_line(image, (0, 2), (0, 8), order=0)
    expected_prof = np.arange(2, 9)
    assert_equal(prof, expected_prof)


def test_horizontal_leftward():
    prof = profile_line(image, (0, 8), (0, 2), order=0)
    expected_prof = np.arange(8, 1, -1)
    assert_equal(prof, expected_prof)


def test_vertical_downward():
    prof = profile_line(image, (2, 5), (8, 5), order=0)
    expected_prof = np.arange(25, 95, 10)
    assert_equal(prof, expected_prof)


def test_vertical_upward():
    prof = profile_line(image, (8, 5), (2, 5), order=0)
    expected_prof = np.arange(85, 15, -10)
    assert_equal(prof, expected_prof)


def test_45deg_right_downward():
    prof = profile_line(image, (2, 2), (8, 8), order=0)
    expected_prof = np.array([22, 33, 33, 44, 55, 55, 66, 77, 77, 88])
    # repeats are due to aliasing using nearest neighbor interpolation.
    # to see this, imagine a diagonal line with markers every unit of
    # length traversing a checkerboard pattern of squares also of unit
    # length. Because the line is diagonal, sometimes more than one
    # marker will fall on the same checkerboard box.
    assert_almost_equal(prof, expected_prof)


def test_45deg_right_downward_interpolated():
    prof = profile_line(image, (2, 2), (8, 8), order=1)
    expected_prof = np.linspace(22, 88, 10)
    assert_almost_equal(prof, expected_prof)


def test_45deg_right_upward():
    prof = profile_line(image, (8, 2), (2, 8), order=1)
    expected_prof = np.arange(82, 27, -6)
    assert_almost_equal(prof, expected_prof)


def test_45deg_left_upward():
    prof = profile_line(image, (8, 8), (2, 2), order=1)
    expected_prof = np.arange(88, 21, -22. / 3)
    assert_almost_equal(prof, expected_prof)


def test_45deg_left_downward():
    prof = profile_line(image, (2, 8), (8, 2), order=1)
    expected_prof = np.arange(28, 83, 6)
    assert_almost_equal(prof, expected_prof)


def test_pythagorean_triangle_right_downward():
    prof = profile_line(image, (1, 1), (7, 9), order=0)
    expected_prof = np.array([11, 22, 23, 33, 34, 45, 56, 57, 67, 68, 79])
    assert_equal(prof, expected_prof)


def test_pythagorean_triangle_right_downward_interpolated():
    prof = profile_line(image, (1, 1), (7, 9), order=1)
    expected_prof = np.linspace(11, 79, 11)
    assert_almost_equal(prof, expected_prof)


pyth_image = np.zeros((6, 7), np.float)
line = ((1, 2, 2, 3, 3, 4), (1, 2, 3, 3, 4, 5))
below = ((2, 2, 3, 4, 4, 5), (0, 1, 2, 3, 4, 4))
above = ((0, 1, 1, 2, 3, 3), (2, 2, 3, 4, 5, 6))
pyth_image[line] = 1.8
pyth_image[below] = 0.6
pyth_image[above] = 0.6


def test_pythagorean_triangle_right_downward_linewidth():
    prof = profile_line(pyth_image, (1, 1), (4, 5),
                        linewidth=3, order=0)
    expected_prof = np.ones(6)
    assert_almost_equal(prof, expected_prof)


def test_pythagorean_triangle_right_upward_linewidth():
    prof = profile_line(pyth_image[::-1, :], (4, 1), (1, 5),
                        linewidth=3, order=0)
    expected_prof = np.ones(6)
    assert_almost_equal(prof, expected_prof)


def test_pythagorean_triangle_transpose_left_down_linewidth():
    prof = profile_line(pyth_image.T[:, ::-1], (1, 4), (5, 1),
                        linewidth=3, order=0)
    expected_prof = np.ones(6)
    assert_almost_equal(prof, expected_prof)


first_color = np.array([0, 0, 255])
second_color = np.array([255, 255, 0])
rgb_image = np.array(([first_color, first_color], [second_color, second_color]), dtype=np.float)


def test_rgb_vertical_downward():
    prof = profile_line(rgb_image, (0, 0), (1, 0), order=0)
    expected_prof = np.array((first_color, second_color))
    assert_equal(prof, expected_prof)


plane = np.array([[1, 1, 1, 1, 1], [1, 1, 1, 1, 1], [1, 1, 0, 1, 1],
                  [1, 1, 1, 1, 1], [1, 1, 1, 1, 1]], dtype=np.float)
image3d = np.stack((plane, plane, plane, plane, plane))


def test_3d_vertical_downward():
    prof = profile_line(image3d, (0, 0, 0), (0, 1, 0), order=0, multichannel=False)
    expected_prof = np.array([1, 1])
    assert_equal(prof, expected_prof)


def test_3d_diagonal():
    prof = profile_line(image3d, (0, 0, 0), (4, 4, 4), order=0, multichannel=False)
    expected_prof = np.array([1, 1, 1, 0, 0, 1, 1, 1])
    assert_equal(prof, expected_prof)


def test_3d_diagonal_interpolated():
    prof = profile_line(image3d, (1, 1, 1), (3, 3, 3), order=1, multichannel=False)
    expected_prof = np.array([1, 0.75, 0, 0.75, 1])
    assert_equal(prof, expected_prof)

def test_3d_through_center_linewidth_1():
    prof = profile_line(image3d, (0, 2, 2), (4, 2, 2), order=1, linewidth=1, multichannel=False)
    expected_prof = np.repeat(0, 5)
    assert_equal(prof, expected_prof)


def test_3d_through_center_linewidth_3():
    prof = profile_line(image3d, (0, 2, 2), (4, 2, 2), order=1, linewidth=3, multichannel=False)
    expected_prof = np.repeat(0.731370849898, 5)
    assert_almost_equal(prof, expected_prof)


def test_3d_through_center_linewidth_5():
    prof = profile_line(image3d, (0, 2, 2), (4, 2, 2), order=1, linewidth=5, multichannel=False)
    expected_prof = np.repeat(0.877895840863, 5)
    assert_almost_equal(prof, expected_prof)


first_plane_color = np.array([0, 0, 255])
second_plane_color = np.array([255, 255, 0])
rgb_first_plane = np.array([[[first_plane_color], [first_plane_color]],
                            [[first_plane_color], [first_plane_color]]], dtype=np.float)
rgb_second_plane = np.array([[[second_plane_color], [second_plane_color]],
                             [[second_plane_color], [second_plane_color]]], dtype=np.float)
rgb_image3d = np.dstack((rgb_first_plane, rgb_second_plane))


def test_rgb_3d_diagonal():
    prof = profile_line(rgb_image3d, (0, 0, 0), (1, 1, 1), order=0, multichannel=True)
    expected_prof = np.array((first_plane_color, second_plane_color, second_plane_color))
    assert_equal(prof, expected_prof)

if __name__ == "__main__":
    from numpy.testing import run_module_suite
    run_module_suite()

