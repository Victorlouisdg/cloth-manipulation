import airo_blender_toolkit as abt
import bpy
import numpy as np

from cm_utils.folds import BezierFoldTrajectory, SleeveFold

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
keypoints = {name: np.array(cloth.data.vertices[id].co) for name, id in keypoint_ids_cloth.items()}

fold = SleeveFold(keypoints, "left")


configs = [
    (1.0, 0),
    (0.25, 0),
    (1.0, 60),
    (0.25, 60),
]


for height_ratio, tilt_angle in configs:
    fold_trajectory = BezierFoldTrajectory(fold, height_ratio, tilt_angle)

    for time_completion in np.linspace(0, 1, 100):
        pose = fold_trajectory.pose(time_completion)
        abt.visualize_transform(pose, 0.05)
