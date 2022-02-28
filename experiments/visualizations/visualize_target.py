import airo_blender_toolkit as abt
import bpy
import numpy as np

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
keypoints = {name: np.array(cloth.data.vertices[id].co) for name, id in keypoint_ids_cloth.items()}

fold = SleeveFold(keypoints, "left")

fold.make_target_mesh(cloth, cloth_thickness=0.01)
