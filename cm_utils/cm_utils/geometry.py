from mathutils import Matrix


def vectors_to_matrix_4x4(x_column, y_column, z_column, translation):
    matrix = Matrix()
    matrix.col[0][0:3] = x_column
    matrix.col[1][0:3] = y_column
    matrix.col[2][0:3] = z_column
    matrix.col[3][0:3] = translation
    return matrix
