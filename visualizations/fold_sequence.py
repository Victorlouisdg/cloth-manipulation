import os

import airo_blender_toolkit as abt
import blenderproc as bproc
import bpy
from mathutils import Vector

from cloth_manipulation.cipc_sim import SimulationCIPC
from cloth_manipulation.dirs import ensure_output_filepaths
from cloth_manipulation.folds import BezierFoldTrajectory, MiddleFold, SideFold, SleeveFold
from cloth_manipulation.materials.penava import materials_by_name

# 1. Setting up the scene
bproc.init()

ground = bproc.object.create_primitive("PLANE", size=10.0)
ground.blender_obj.name = "Ground"
ground_material = ground.new_material("Ground")
ground_material.set_principled_shader_value("Base Color", abt.colors.light_blue)
ground_material.blender_obj.diffuse_color = abt.colors.light_blue

cloth_material = materials_by_name["cotton penava"]

shirt0 = abt.PolygonalShirt()
shirt0_obj = shirt0.blender_obj
abt.triangulate_blender_object(shirt0_obj, minimum_triangle_density=20000)
shirt0_obj.location.z = 2.0 * cloth_material.thickness
shirt0.persist_transformation_into_mesh()


shirt_material = shirt0.new_material(name=shirt0_obj.name)
shirt_material.set_principled_shader_value("Sheen", 1.0)
shirt_material.set_principled_shader_value("Roughness", 1.0)
shirt_material.set_principled_shader_value("Base Color", abt.colors.dark_green)
shirt_material.blender_obj.diffuse_color = abt.colors.dark_green

# abt.show_wireframes()
scene = bpy.context.scene
camera = scene.camera
camera.data.display_size = 0.2
camera.data.type = "ORTHO"
camera.data.ortho_scale = 3.5
camera.location = (1, 1, 5)
scene.render.resolution_x = 2000
scene.render.resolution_y = 500

scene.frame_start = 0

filepaths = ensure_output_filepaths()
hdri_name = "immenstadter_horn"
hdri_path = abt.download_hdri(hdri_name, filepaths["run"], res="1k")
abt.load_hdri(hdri_path)

# 2. Creating the target shape and fold trajectories
keypoints = {name: coord[0] for name, coord in shirt0.keypoints_3D.items()}

left_sleeve = SleeveFold(keypoints, "left")
right_sleeve = SleeveFold(keypoints, "right")
left_side_top = SideFold(keypoints, "left", "top")
left_side_bottom = SideFold(keypoints, "left", "bottom")
right_side_top = SideFold(keypoints, "right", "top")
right_side_bottom = SideFold(keypoints, "right", "bottom")
middle_left = MiddleFold(keypoints, "left")
middle_right = MiddleFold(keypoints, "right")

left_side = [left_side_top, left_side_bottom]
right_side = [right_side_top, right_side_bottom]
middle = [middle_left, middle_right]

fold_steps = [[left_sleeve], [right_sleeve], left_side, right_side, middle]


frames_per_fold_step = 50
frames_between_fold_steps = 5

simulation_steps = len(fold_steps) * (frames_per_fold_step + frames_between_fold_steps)

print(f"Simulating {simulation_steps} steps.")

scene.frame_end = simulation_steps

# empty = abt.visualize_transform(fold.gripper_start_pose(), 0.1)
# abt.visualize_line(*fold.fold_line(), length=1.5)

grippers = []

frame = scene.frame_start

for fold_step in fold_steps:
    for fold in fold_step:
        height_ratio = 0.8
        tilt_angle = 20 if fold.side == "right" else -20
        fold_trajectory = BezierFoldTrajectory(fold, height_ratio, tilt_angle, end_height=0.1)
        gripper_cube = bproc.object.create_primitive("CUBE", size=0.05).blender_obj
        abt.keyframe_trajectory(gripper_cube, fold_trajectory, frame, frame + frames_per_fold_step)
        bpy.ops.object.paths_range_update()
        bpy.ops.object.paths_calculate(start_frame=scene.frame_start, end_frame=scene.frame_end)
        gripper = abt.Gripper(gripper_cube)
        grippers.append(gripper)
    frame += frames_per_fold_step + frames_between_fold_steps


# # 3. Running the simulation
simulation = SimulationCIPC(filepaths, 25)
simulation.add_cloth(shirt0.blender_obj, cloth_material)
simulation.add_collider(ground.blender_obj, friction_coefficient=0.8)
simulation.initialize_cipc()

shirt_obj = shirt0_obj

for frame in range(scene.frame_start, scene.frame_end):
    scene.frame_set(frame)
    action = {}
    for gripper in grippers:
        action |= gripper.action(shirt_obj)

    simulation.step(action)
    shirt_obj = simulation.blender_objects_output[shirt0_obj.name][frame + 1]
    scene.frame_set(frame + 1)


# 5. Visualization
for shirt_obj in simulation.blender_objects_output[shirt0_obj.name].values():
    shirt_obj.data.materials.append(shirt_material.blender_obj)

scene.frame_set(simulation_steps)

objects_to_hide = [ground.blender_obj, shirt0.blender_obj]

for object in objects_to_hide:
    object.hide_viewport = True
    object.hide_render = True


# make visualisazation here
visualized_folds = {0: [left_sleeve, right_sleeve], 110: [left_side_top, right_side_top], 220: [middle_left], 275: []}

fold_line_visualizations = {
    0: [(left_sleeve.fold_line(), 0.3, 0.1), (right_sleeve.fold_line(), 0.1, 0.3)],
    110: [(left_side_top.fold_line(), 0.7, 0.05), (right_side_top.fold_line(), 0.05, 0.7)],
    220: [(middle_left.fold_line(), 0.1, 0.5)],
    275: [],
}

x = 0.0
i = 0
for frame, fold_lines in fold_line_visualizations.items():
    scene.frame_set(frame)
    shirt_obj = bpy.data.objects[f"Shirt_{frame}"]
    abt.select_only(shirt_obj)
    bpy.ops.object.duplicate_move(
        OBJECT_OT_duplicate={"linked": False, "mode": "TRANSLATION"}, TRANSFORM_OT_translate={"value": (x, 1, 0)}
    )
    shirt_copy = bpy.context.active_object
    shirt_copy.animation_data_clear()

    for fold_line, forward, backward in fold_lines:
        line = abt.visualize_line(
            *fold_line, length_forward=forward, length_backward=backward, color=abt.colors.red, thickness=0.006
        )
        line.blender_obj.location += Vector((x, 1, 0))

    # Ad-hoc shifts to the right
    if i == 0:
        x += 1.1
    else:
        x += 0.7
    i += 1


x = 0.0
i = 0
for fold_step in fold_steps:
    for fold in fold_step:
        # Ad-hoc shifts to the right
        height_ratio = 0.8
        tilt_angle = 20 if fold.side == "right" else -20
        trajectory = BezierFoldTrajectory(fold, height_ratio, tilt_angle, end_height=0.1)

        path = abt.visualize_path(trajectory.path, color=abt.colors.orange, radius=0.005)
        path.blender_obj.location += Vector((x, 1, 0))

        if i == 1:
            x += 1.1
        if i == 5:
            x += 0.7
        i += 1

bpy.ops.wm.save_as_mainfile(filepath=filepaths["blend"])

scene.render.filepath = os.path.join(filepaths["run"], "result.png")
bpy.ops.render.render(write_still=True)
