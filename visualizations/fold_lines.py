import airo_blender_toolkit as abt
import blenderproc as bproc
import bpy
import numpy as np

from cloth_manipulation.folds import BezierFoldTrajectory, MiddleFold, SideFold, SleeveFold

bproc.init()


ground = bproc.object.create_primitive("PLANE", size=5.0)
ground.blender_obj.name = "Ground"
ground_material = ground.new_material("Ground")
ground_material.set_principled_shader_value("Base Color", abt.colors.light_blue)
ground_material.blender_obj.diffuse_color = abt.colors.light_blue

shirt = abt.PolygonalShirt()
shirt_material = shirt.new_material("Shirt")
shirt_material.set_principled_shader_value("Base Color", abt.colors.dark_green)
shirt_material.blender_obj.diffuse_color = abt.colors.dark_green
shirt.blender_obj.location.z = 0.003
shirt.persist_transformation_into_mesh()

shirt.visualize_keypoints(radius=0.01)

scene = bpy.context.scene
camera = scene.camera
camera.location = 0.936188, -1.19851, 0.919974
camera.rotation_euler = np.deg2rad(59.2), 0, np.deg2rad(32.8)

scene.render.resolution_x = 1024
scene.render.resolution_y = 512
scene.view_settings.look = "High Contrast"

# bpy.context.space_data.shading.light = 'FLAT'

hdri_name = "aviation_museum"  # studio_country_hall"# "monbachtal_riverbank"
hdri_path = abt.download_hdri(hdri_name, "/home/idlab185/assets", res="1k")
abt.load_hdri(hdri_path)

keypoints = {name: coord[0] for name, coord in shirt.keypoints_3D.items()}
left_sleeve = SleeveFold(keypoints, "left")
right_sleeve = SleeveFold(keypoints, "right")
left_side_top = SideFold(keypoints, "left", "top")
left_side_bottom = SideFold(keypoints, "left", "bottom")
right_side_top = SideFold(keypoints, "right", "top")
right_side_bottom = SideFold(keypoints, "right", "bottom")
middle_left = MiddleFold(keypoints, "left")
middle_right = MiddleFold(keypoints, "right")

fold_line_visualization_lengths = [
    (left_sleeve.fold_line(), 0.3, 0.1),
    # (right_sleeve.fold_line(), 0.1, 0.3),
    # (left_side_top.fold_line(), 0.7, 0.05),
    # (right_side_top.fold_line(), 0.05, 0.7),
    # (middle_left.fold_line(), 0.1, 0.5),
]

for fold_line, forward, backward in fold_line_visualization_lengths:
    abt.visualize_line(*fold_line, length_forward=forward, length_backward=backward, color=abt.colors.red)

import time

start = time.time()

trajectories = [
    BezierFoldTrajectory(left_sleeve, 0.6, -60),
    # BezierFoldTrajectory(right_sleeve, 0.6, 60),
    # BezierFoldTrajectory(left_side_top, 0.6, -20),
    # BezierFoldTrajectory(left_side_bottom, 0.6, 20),
    # BezierFoldTrajectory(right_side_top, 0.6, 20),
    # BezierFoldTrajectory(right_side_bottom, 0.6, -20),
    # BezierFoldTrajectory(middle_left, 0.6, -20),
    # BezierFoldTrajectory(middle_right, 0.6, 20),
]

print("Time", time.time() - start)


for trajectory in trajectories:
    abt.visualize_path(trajectory.path, color=abt.colors.orange)
    abt.visualize_transform(trajectory.start)
    abt.visualize_transform(trajectory.end)
