import numpy as np
from scipy.spatial.transform import Rotation
from mathutils import Vector, Matrix


def rotate_point(point, rotation_origin, rotation_axis, angle):
    unit_axis = rotation_axis / np.linalg.norm(rotation_axis)
    rotation = Rotation.from_rotvec(angle * unit_axis)
    point_new = rotation.as_matrix() @ (point - rotation_origin) + rotation_origin
    return point_new


def vectors_to_matrix_4x4(x_column, y_column, z_column, translation):
    matrix = Matrix()
    matrix.col[0][0:3] = x_column
    matrix.col[1][0:3] = y_column
    matrix.col[2][0:3] = z_column
    matrix.col[3][0:3] = translation
    return matrix


def update_4x4_with_3x3(matrix4x4, matrix3x3):
    matrix4x4.col[0][0:3] = matrix3x3[:, 0]
    matrix4x4.col[1][0:3] = matrix3x3[:, 1]
    matrix4x4.col[2][0:3] = matrix3x3[:, 2]
