from scipy.spatial.transform import Rotation
from scipy.spatial.transform import Slerp
import numpy as np
from mathutils import Vector, Matrix


def rotate_point(point, rotation_origin, rotation_axis, angle):
    unit_axis = rotation_axis / np.linalg.norm(rotation_axis)
    rotation = Rotation.from_rotvec(angle * unit_axis)
    point_new = rotation.as_matrix() @ (point - rotation_origin) + rotation_origin
    return point_new


def get_sleeve_fold_plane(keypoints, left_or_right, angle):
    armpit = keypoints[f"{left_or_right}_armpit"]
    bottom = keypoints[f"bottom_{left_or_right}"]

    up = np.array([0, 0, 1.0])

    rotated = rotate_point(bottom, armpit, up, angle)

    fold_line = np.array(armpit) - rotated
    fold_plane_normal = np.cross(fold_line, up)

    return (armpit, fold_plane_normal), fold_line


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


def keyframe_sleeve_fold(
    gripper,
    keypoints,
    left_or_right,
    height_ratio,
    offset_ratio,
    start_frame,
    end_frame,
    angle=30,
):
    angle = np.deg2rad(angle)

    # Keyframe start pose
    sleeve_top = keypoints[f"{left_or_right}_sleeve_top"]
    sleeve_bottom = keypoints[f"{left_or_right}_sleeve_bottom"]

    shoulder = keypoints[f"{left_or_right}_shoulder"]
    armpit = keypoints[f"{left_or_right}_armpit"]

    sleeve_middle = (sleeve_top + sleeve_bottom) / 2
    shoulder_middle = (shoulder + armpit) / 2

    up = Vector([0, 0, 1])

    gripper_translation = sleeve_middle.to_4d()
    gripper_X = (shoulder_middle - sleeve_middle).normalized()
    gripper_Z = up
    gripper_Y = gripper_Z.cross(gripper_X)

    start_pose = vectors_to_matrix_4x4(
        gripper_X, gripper_Y, gripper_Z, gripper_translation
    )
    gripper.matrix_world = start_pose

    print(start_frame, end_frame)

    gripper.keyframe_insert(data_path="location", frame=start_frame)

    corner_bottom = keypoints[f"{left_or_right}_corner_bottom"]

    # For the left sleeve, we rotate the fold line clockwise
    if left_or_right == "left":
        angle = -angle

    rotated = Vector(rotate_point(corner_bottom, armpit, up, angle))
    vector_along_fold = (armpit - rotated).normalized()

    basis_X = vector_along_fold
    basis_Z = up
    basis_Y = basis_Z.cross(basis_X)
    new_basis = vectors_to_matrix_4x4(basis_X, basis_Y, basis_Z, armpit)

    # Keyframe end pose
    M = start_pose
    M = new_basis.inverted() @ M
    M = Matrix.Rotation(np.deg2rad(180), 4, "X") @ M
    M = new_basis @ M
    end_pose = M

    gripper.matrix_world = end_pose
    gripper.location.z = 0.05
    gripper.keyframe_insert(data_path="location", frame=end_frame)

    # Keyframe middle pose
    start_position = start_pose.translation
    end_position = end_pose.translation
    start_to_end_distance = (start_position - end_position).length

    middle_frame = (start_frame + end_frame) // 2

    mid_angle = np.deg2rad(90 if left_or_right is "left" else -90)

    M = start_pose
    M = new_basis.inverted() @ M
    M = Matrix.Rotation(mid_angle, 4, "X") @ M
    M = Matrix.Translation((offset_ratio * start_to_end_distance, 0, 0)) @ M
    M = new_basis @ M
    middle_pose = M

    gripper.matrix_world = middle_pose
    gripper.location.z = height_ratio * start_to_end_distance
    gripper.keyframe_insert(data_path="location", frame=middle_frame)

    # Keyframing the orientation of the gripper in all frames
    key_rots = Rotation.from_matrix(
        [start_pose.to_3x3(), middle_pose.to_3x3(), end_pose.to_3x3()]
    )
    key_times = [start_frame, middle_frame, end_frame]

    slerp = Slerp(key_times, key_rots)

    for i in range(start_frame, end_frame + 1):
        update_4x4_with_3x3(gripper.matrix_world, slerp(i).as_matrix())
        gripper.keyframe_insert(data_path="rotation_euler", frame=i)

    gripper.matrix_world = start_pose
