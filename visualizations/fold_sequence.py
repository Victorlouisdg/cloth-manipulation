import airo_blender_toolkit as abt
import blenderproc as bproc
import bpy

from cloth_manipulation.cipc_sim import SimulationCIPC
from cloth_manipulation.dirs import ensure_output_filepaths
from cloth_manipulation.folds import BezierFoldTrajectory, MiddleFold, SideFold, SleeveFold
from cloth_manipulation.materials.penava import materials_by_name

# 1. Setting up the scene
bproc.init()

ground = bproc.object.create_primitive("PLANE", size=5.0)
ground.blender_obj.name = "ground"
ground_material = ground.new_material("Ground")
ground_material.set_principled_shader_value("Base Color", abt.colors.light_blue)
ground_material.blender_obj.diffuse_color = abt.colors.light_blue

cloth_material = materials_by_name["cotton penava"]

shirt0 = abt.PolygonalShirt()
shirt0_obj = shirt0.blender_obj
abt.triangulate_blender_object(shirt0_obj, minimum_triangle_density=10000)
shirt0_obj.location.z = 2.0 * cloth_material.thickness
shirt0.persist_transformation_into_mesh()


shirt_material = shirt0.new_material(name=shirt0_obj.name)
shirt_material.set_principled_shader_value("Sheen", 1.0)
shirt_material.set_principled_shader_value("Roughness", 1.0)
shirt_material.set_principled_shader_value("Base Color", abt.colors.dark_green)
shirt_material.blender_obj.diffuse_color = abt.colors.dark_green

# abt.show_wireframes()
scene = bpy.context.scene
scene.camera.data.display_size = 0.2
scene.camera.location.z += 2.0
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

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


frames_per_fold_step = 25
frames_between_fold_steps = 5

simulation_steps = len(fold_steps) * (frames_per_fold_step + frames_between_fold_steps)

scene.frame_end = simulation_steps


# empty = abt.visualize_transform(fold.gripper_start_pose(), 0.1)
# abt.visualize_line(*fold.fold_line(), length=1.5)

grippers = []

frame = scene.frame_start

for fold_step in fold_steps:
    for fold in fold_step:
        height_ratio = 0.8
        tilt_angle = 20 if fold.side == "right" else -20
        fold_trajectory = BezierFoldTrajectory(fold, height_ratio, tilt_angle)
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


for frame in range(scene.frame_start, scene.frame_end):
    scene.frame_set(frame)
    action = {}
    for gripper in grippers:
        action |= gripper.action(shirt0_obj)

    simulation.step(action)
    shirt0_obj = simulation.blender_objects_output[frame + 1][0]
    scene.frame_set(frame + 1)


# 5. Visualization
for objs in simulation.blender_objects_output.values():
    for obj in objs:
        bproc_obj = bproc.python.types.MeshObjectUtility.MeshObject(obj)
        bproc_obj.set_shading_mode("smooth")
        if shirt0.blender_obj.name in obj.name:
            obj.data.materials.append(shirt_material.blender_obj)

scene.frame_set(simulation_steps)

objects_to_hide = [ground.blender_obj, shirt0.blender_obj]

for object in objects_to_hide:
    object.hide_viewport = True
    object.hide_render = True


# make visualisazation here
# visualized_folds = {0: [left_sleeve, right_sleeve], 50: [left_side_top]}

# x = 0.0

# for frame, folds in visualized_folds.items():
#     scene.frame_set(frame)
#     shirt_obj = bpy.data.objects[f"Shirt_{frame}"]
#     abt.select_only(shirt_obj)
#     bpy.ops.object.duplicate_move(
#         OBJECT_OT_duplicate={"linked": False, "mode": "TRANSLATION"}, TRANSFORM_OT_translate={"value": (x, 1, 0)}
#     )

#     shirt_copy = bpy.context.active_object
#     shirt_copy.animation_data_clear()
#     x += 1.0

bpy.ops.wm.save_as_mainfile(filepath=filepaths["blend"])

# scene.render.filepath = os.path.join(filepaths["run"], "result.png")
# bpy.ops.render.render(write_still=True)
