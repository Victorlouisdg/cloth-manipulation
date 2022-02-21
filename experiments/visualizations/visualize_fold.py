# read blender object
# turn into keypointed object
# calculate fold
# visualize fold

import airo_blender_toolkit as abt
import bpy

from cm_utils.folds import SleeveFold

keypoint_ids_cloth = {
    "left_shoulder": 1121,
    "left_sleeve_top": 57,
    "left_sleeve_bottom": 0,
    "left_armpit": 929,
    "left_corner_bottom": 369,
    "right_shoulder": 2583,
    "right_sleeve_top": 1492,
    "right_sleeve_bottom": 1435,
    "right_armpit": 2391,
    "right_corner_bottom": 1804,
}

# Selecting the relevant objects
objects = bpy.data.objects
cloth_name = "cloth"
cloth = objects[cloth_name]

cloth_keypointed = abt.KeypointedObject(cloth, keypoint_ids_cloth)
cloth_keypointed.visualize_keypoints(radius=0.02)


keypoints = {name: cloth.data.vertices[id].co for name, id in keypoint_ids_cloth.items()}

fold = SleeveFold(keypoints, 0.5, 0.5, "left")
# abt.visualize_transform(fold.fold_basis, 0.1)
# abt.visualize_transform(fold.gripper_start_pose, 0.1)
# abt.visualize_transform(fold.gripper_middle_pose, 0.1)
# abt.visualize_transform(fold.gripper_end_pose, 0.1)

# empty = abt.visualize_transform(fold.gripper_start_pose, 0.1)

# poses = {
#     0: fold.gripper_start_pose,
#     50: fold.gripper_middle_pose,
#     100: fold.gripper_end_pose,
# }

# keyframe_locations(empty, poses)

for i in range(0, 101, 10):
    pose = fold.gripper_pose(i / 100.0)
    abt.visualize_transform(pose, 0.1)
