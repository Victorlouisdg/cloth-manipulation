import airo_blender_toolkit as abt
import blenderproc as bproc
import bpy
import numpy as np
from blenderproc.python.material import MaterialLoaderUtility
from cipc.materials.penava import materials_by_name

from cloth_manipulation.folds import BezierFoldTrajectory, SleeveFold
from cloth_manipulation.scene import setup_enviroment_texture, setup_ground, setup_shirt_material

bproc.init()
cloth_material = materials_by_name["cotton penava"]

# shirt = abt.PolygonalShirt()

shirt = abt.PolygonalShirt(
    bottom_width=0.75,
    neck_width=0.25,
    neck_depth=0.1,
    shoulder_width=0.68,
    shoulder_height=0.95,
    sleeve_width_start=0.3,
    sleeve_width_end=0.25,
    sleeve_length=0.22,
    sleeve_angle=5.0,
)

shirt_obj = shirt.blender_obj
abt.triangulate_blender_object(shirt_obj, minimum_triangle_density=20000)
shirt_obj.location.z = 2.0 * cloth_material.thickness  # ground offset + cloth offset
shirt.persist_transformation_into_mesh()
ground = setup_ground()
# setup_camera_topdown()

scene = bpy.context.scene
camera = scene.camera

camera.location = -0.708, -1.492, 1.027
camera.rotation_euler = np.deg2rad(60.8), 0, np.deg2rad(-21.6)
camera.data.lens = 50
scene.render.resolution_x = 2048
scene.render.resolution_y = 1024


setup_enviroment_texture()

# shirt.visualize_keypoints(radius=0.01)

shirt_material = setup_shirt_material(shirt)

keypoints = {name: coord[0] for name, coord in shirt.keypoints_3D.items()}
left_sleeve = SleeveFold(keypoints, "left")

# Visualizing the fold lines
fold_line_visualization_lengths = [
    (left_sleeve.fold_line(), 0.3, 0.1),
]
for fold_line, forward, backward in fold_line_visualization_lengths:
    abt.visualize_line(*fold_line, length_forward=forward, length_backward=backward, color=abt.colors.red)

fold = left_sleeve

scene = bpy.context.scene

# Setting up the animated grippers
grippers = []

height_ratio = 1.0
tilt_angle = 0.0

material = MaterialLoaderUtility.create("Material")
material.set_principled_shader_value("Base Color", (1.0, 1.0, 1.0, 1.0))
material.set_principled_shader_value("Alpha", 0.4)
material.blender_obj.diffuse_color = (1.0, 1.0, 1.0, 1.0)

# for height_ratio in np.linspace(0.1, 1.0, 14):
#     for angle in np.linspace(30.0, 90.0, max(2, int(18 * height_ratio))):
#         tilt_angle = 90.0 - angle
#         # values.append(f"{height_ratio}-{tilt_angle}")
#         angle = tilt_angle if fold.side == "right" else -1 * tilt_angle
#         fold_trajectory = BezierFoldTrajectory(fold, height_ratio, angle, end_height=0.05)
#         pose = fold_trajectory.pose(0.5)
#         sphere = bproc.object.create_primitive("SPHERE", location=pose.position, radius=0.015) # * 0.3)
#         sphere.add_material(material)
#         # sphere.blender_obj.name = category


end_height = 0.05

combos = [
    (1.0, 90.0),
]

for height_ratio, angle in combos:
    tilt_angle = 90.0 - angle
    angle = tilt_angle if fold.side == "right" else -1 * tilt_angle
    fold_trajectory = BezierFoldTrajectory(fold, height_ratio, angle, end_height=end_height)
    path, material = abt.visualize_path(fold_trajectory.path, color=abt.colors.orange, radius=0.005)
    material.set_principled_shader_value("Alpha", 0.3)
