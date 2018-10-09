import math
import numpy as np
from scipy import ndimage as ndi, constants

from ._linalg import get_any_perpendicular_vector_3d, rotation_matrix, affine_transform


def profile_line(image, src, dst, linewidth=1,
                 order=1, mode='constant', cval=0.0, multichannel=True,
                 endpoint=True, num_sample_points=4):
    """Return the intensity profile of an image measured along a scan line.

    Parameters
    ----------
    image : numeric array, shape (M, N[, C])
        The image, either grayscale (2D or 3D array) or multichannel
        (3D array, for a RBG 2D image where the final axis contains the channel
        information).
    src : 2-tuple of numeric scalar (float or int)
        The start point of the scan line.
    dst : 2-tuple of numeric scalar (float or int)
        The end point of the scan line. The destination point is *included*
        in the profile, in contrast to standard numpy indexing.
    linewidth : int, optional
        Width of the scan, perpendicular to the line
    order : int in {0, 1, 2, 3, 4, 5}, optional
        The order of the spline interpolation to compute image values at
        non-integer coordinates. 0 means nearest-neighbor interpolation.
    mode : {'constant', 'nearest', 'reflect', 'mirror', 'wrap'}, optional
        How to compute any values falling outside of the image.
    cval : float, optional
        If `mode` is 'constant', what constant value to use outside the image.
    multichannel : bool, optional
        Whether the last axis of the image is to be interpreted as RGB
        channels or another spatial dimension.
    endpoint : bool, optional
        If True, returns the intensity value at dst. Otherwise, it is not included.
        Default is True.
    num_sample_points : int, optional
        The number of sample points for 3d profile lines. generates angles afters.

    Returns
    -------
    return_value : array
        The intensity profile along the scan line. The length of the profile
        is the ceil of the computed length of the scan line.

    Examples
    --------
    >>> x = np.array([[1, 1, 1, 2, 2, 2]])
    >>> img = np.vstack([np.zeros_like(x), x, x, x, np.zeros_like(x)])
    >>> img
    array([[0, 0, 0, 0, 0, 0],
           [1, 1, 1, 2, 2, 2],
           [1, 1, 1, 2, 2, 2],
           [1, 1, 1, 2, 2, 2],
           [0, 0, 0, 0, 0, 0]])
    >>> profile_line(img, (2, 1), (2, 4))
    array([ 1.,  1.,  2.,  2.])
    >>> profile_line(img, (1, 0), (1, 6), cval=4)
    array([ 1.,  1.,  1.,  2.,  2.,  2.,  4.])

    The destination point is included in the profile, in contrast to
    standard numpy indexing.
    For example:

    >>> profile_line(img, (1, 0), (1, 6))  # The final point is out of bounds
    array([ 1.,  1.,  1.,  2.,  2.,  2.,  0.])
    >>> profile_line(img, (1, 0), (1, 5))  # This accesses the full first row
    array([ 1.,  1.,  1.,  2.,  2.,  2.])
    """
    if image.ndim not in [2, 3, 4]:
        raise ValueError('profile_line is not implemented for images of dimension {0}'.format(image.shape))

    perp_lines = _line_profile_coordinates(src, dst, linewidth=linewidth, endpoint=endpoint, num_sample_points=num_sample_points)
    if image.ndim == 4 or (image.ndim == 3 and multichannel):
        # 2D or 3D multichannel
        pixels = [ndi.map_coordinates(image[..., i], perp_lines, order=order,
                                      mode=mode, cval=cval) for i in range(image.shape[image.ndim - 1])]
        pixels = np.transpose(np.asarray(pixels), (1, 2, 0))
    else:
        # 2D or 3D grayscale
        pixels = ndi.map_coordinates(image, perp_lines, order=order, mode=mode, cval=cval)

    intensities = pixels.mean(axis=1)
    return intensities


def _line_profile_coordinates(src, dst, linewidth=1, endpoint=True, num_sample_points=4):
    """Return the coordinates of the profile of an image along a scan line.

    Parameters
    ----------
    src : 2 or 3-tuple of numeric scalar (float or int)
        The start point of the scan line.
    dst : 2 or 3-tuple of numeric scalar (float or int)
        The end point of the scan line.
    linewidth : int, optional
        Width of the scan, perpendicular to the line. In 3D, this value is the
        diameter of a 3d cylinder along the scan line.

    Returns
    -------
    perp_array : array, shape (2 or 3, N, C), float
        The coordinates of the profile along the scan line. The length of the
        profile is the ceil of the computed length of the scan line.

    Notes
    -----
    This is a utility method meant to be used internally by skimage functions.
    The destination point is included in the profile, in contrast to
    standard numpy indexing.
    """
    src = np.asarray(src, dtype=float)
    dst = np.asarray(dst, dtype=float)
    length = math.ceil(np.linalg.norm(dst - src))
    unit_dir = (dst - src) / length

    # when endpoint is true add 1 to length to include the last point in the profile.
    # (in contrast to standard numpy indexing)
    num = length + 1 if endpoint else length

    if len(src) == 2:
        line_row = np.linspace(src[0], dst[0], num, endpoint=endpoint)
        line_col = np.linspace(src[1], dst[1], num, endpoint=endpoint)
        d_row, d_col = unit_dir
        # we subtract 1 from linewidth to change from pixel-counting
        # (make this line 3 pixels wide) to point distances (the
        # distance between pixel centers)
        row_width = (linewidth - 1) * d_col / 2
        col_width = (linewidth - 1) * -d_row / 2
        perp_rows = [np.linspace(row_i - row_width, row_i + row_width, linewidth) for row_i in line_row]
        perp_cols = [np.linspace(col_i - col_width, col_i + col_width, linewidth) for col_i in line_col]
        return np.array([perp_rows, perp_cols])

    elif len(src) == 3:
        line_pln = np.linspace(src[0], dst[0], num, endpoint=endpoint)
        line_row = np.linspace(src[1], dst[1], num, endpoint=endpoint)
        line_col = np.linspace(src[2], dst[2], num, endpoint=endpoint)
        d_pln, d_row, d_col = unit_dir
        perp_vector = np.asarray(get_any_perpendicular_vector_3d([d_pln, d_row, d_col]))
        pln_width, row_width, col_width,  = (linewidth - 1) * perp_vector / 2

        if linewidth == 1:
            perp_pln = np.expand_dims(line_pln, axis=1)
            perp_rows = np.expand_dims(line_row, axis=1)
            perp_cols = np.expand_dims(line_col, axis=1)
            return np.array([perp_pln, perp_rows, perp_cols])

        if linewidth > 1:
            # separate the points to only get the outside ones (without the center points)
            perp_pln = [np.linspace(pln_i - pln_width, pln_i + pln_width, linewidth) for pln_i in line_pln]
            #perp_pln = np.array_split(np.asarray(perp_pln), 2, axis=1)[-1]
            perp_pln = np.array_split(np.asarray(perp_pln), 2, axis=1)[0]
            perp_rows = [np.linspace(row_i - row_width, row_i + row_width, linewidth) for row_i in line_row]
            #perp_rows = np.array_split(np.asarray(perp_rows), 2, axis=1)[-1]
            perp_rows = np.array_split(np.asarray(perp_rows), 2, axis=1)[0]
            perp_cols = [np.linspace(col_i - col_width, col_i + col_width, linewidth) for col_i in line_col]
            #perp_cols = np.array_split(np.asarray(perp_cols), 2, axis=1)[-1]
            perp_cols = np.array_split(np.asarray(perp_cols), 2, axis=1)[0]
            perp_array = np.array([perp_pln, perp_rows, perp_cols])

            # create a rotated array of sample points around the direction axis
            points = perp_array.T.reshape(-1, 3)


            # split number of samples into even angles to cover 360 degrees
            # without using the first (0) and the last (2π)
            rot_angles = np.linspace(0, 2 * constants.pi, num_sample_points, endpoint=False)[1:]
            # rot_angles = [constants.pi / 2]  # one rot angle for now

            points_array = [points]
            for angle in rot_angles:
                rot_matrix = rotation_matrix(angle, unit_dir, dst)
                transformed_points = affine_transform(rot_matrix, points)
                #rot_points = np.dot(rot_matrix[:-1, :-1], points.T).T
                points_array += [transformed_points]

            # remove duplicate elements - from the center
            points_array = np.unique(points_array, axis=0)

            # add centers to points

            # put back in shape of perp_array
            # rot_points = rot_points.reshape(linewidth, length + 1, 3).T
            # array = np.dstack([array, rot_points])

            #np.asarray(points_array).reshape(3, int(np.floor(linewidth / 2)), -1)


            points_array = np.asarray(points_array).reshape((linewidth / 2) * num_sample_points, length + 1, 3).T
            #points_array = points.reshape((linewidth - 1) * num_sample_points, length + 1, 3).T


            #points_array = points_array.reshape(linewidth, length + 1, 3).T
            #array = np.dstack([array, rot_points])

            # if linewidth is odd, add center elements
            # if linewidth % 2:
            #     centers_pln = np.expand_dims(line_pln, axis=1)
            #     centers_rows = np.expand_dims(line_row, axis=1)
            #     centers_cols = np.expand_dims(line_col, axis=1)
            #     np.array([centers_pln, centers_rows, centers_cols])
            #     array = np.dstack([perp_array, array])

            return points_array
