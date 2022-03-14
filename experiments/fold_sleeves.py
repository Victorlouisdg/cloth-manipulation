import airo_blender_toolkit as abt
import blenderproc as bproc
import bpy
import numpy as np

from cloth_manipulation.cipc_sim import SimulationCIPC
from cloth_manipulation.dirs import ensure_output_filepaths, save_dict_as_json
from cloth_manipulation.folds import BezierFoldTrajectory, SleeveFold
from cloth_manipulation.losses import mean_distance
from cloth_manipulation.materials.penava import materials_by_name

# 1. Setting up the scene
bproc.init()

ground = bproc.object.create_primitive("PLANE", size=5.0)
ground.blender_obj.name = "ground"

cloth_material = materials_by_name["cotton penava"]

shirt = abt.PolygonalShirt()
shirt_obj = shirt.blender_obj
abt.triangulate_blender_object(shirt_obj, minimum_triangle_density=1000)
shirt_obj.location.z = 2.0 * cloth_material.thickness
shirt.persist_transformation_into_mesh()
# shirt.visualize_keypoints(radius=0.01)

airo_orange = [0.94, 0.60, 0.23, 1.0]
shirt_material = shirt.new_material(name=shirt_obj.name)
shirt_material.set_principled_shader_value("Sheen", 1.0)
shirt_material.set_principled_shader_value("Roughness", 1.0)
shirt_material.set_principled_shader_value("Base Color", airo_orange)
shirt_material.blender_obj.diffuse_color = airo_orange

# abt.show_wireframes()
scene = bpy.context.scene
scene.camera.data.display_size = 0.2
scene.camera.location.z += 2.0
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

simulation_steps = 125  # 250
scene.frame_start = 0
scene.frame_end = simulation_steps

filepaths = ensure_output_filepaths()
hdri_name = "immenstadter_horn"
hdri_path = abt.download_hdri(hdri_name, filepaths["run"], res="1k")
abt.load_hdri(hdri_path)

# 2. Creating the target shape and fold trajectories
keypoints = {name: coord[0] for name, coord in shirt.keypoints_3D.items()}
fold_sequence = [((0, 100), SleeveFold(keypoints, "left"))]  # , ((100, 200), SleeveFold(keypoints, "right"))]

# empty = abt.visualize_transform(fold.gripper_start_pose(), 0.1)
# abt.visualize_line(*fold.fold_line(), length=1.5)

grippers = []
shirt_target = shirt_obj

for (start_frame, end_frame), fold in fold_sequence:
    shirt_target = fold.make_target_mesh(shirt_target, cloth_material.thickness)

    height_ratio = 0.8
    tilt_angle = 20 if fold.side == "right" else -20
    fold_trajectory = BezierFoldTrajectory(fold, height_ratio, tilt_angle)
    # abt.visualize_path(fold_trajectory.path)
    gripper_cube = bproc.object.create_primitive("CUBE", size=0.05).blender_obj
    abt.keyframe_trajectory(gripper_cube, fold_trajectory, start_frame, end_frame)
    bpy.ops.object.paths_range_update()
    bpy.ops.object.paths_calculate(start_frame=scene.frame_start, end_frame=scene.frame_end)
    gripper = abt.Gripper(gripper_cube)
    grippers.append(gripper)


# # 3. Running the simulation
simulation = SimulationCIPC(filepaths, 25)
simulation.add_cloth(shirt.blender_obj, cloth_material)
simulation.add_collider(ground.blender_obj, friction_coefficient=0.8)
simulation.initialize_cipc()


for frame in range(scene.frame_start, scene.frame_end + 1):
    scene.frame_set(frame)
    action = {}
    for gripper in grippers:
        action |= gripper.action(shirt_obj)

    simulation.step(action)
    shirt_obj = simulation.blender_objects_output[frame + 1][0]

# 4. Calculating the loss

print(shirt_target.name)
print(shirt_obj.name)
print(shirt.blender_obj.name)

targets = np.array([v.co for v in shirt_target.data.vertices])
final_positions = np.array([v.co for v in shirt_obj.data.vertices])
initial_positions = np.array([v.co for v in shirt.blender_obj.data.vertices])


losses = {
    "mean_distance": mean_distance(targets, final_positions),
    # "mean_sq_distance": mean_distance(targets, final_positions),
    # "rms_distance": mean_distance(targets, final_positions),
}

mean_distance_ref = mean_distance(targets, initial_positions)

print("Mean distance (reference):", mean_distance_ref)
print("Mean distance (result):", losses["mean_distance"])
# print(shirt.scale)
# print(mean_distance / shirt.scale)

save_dict_as_json(filepaths["losses"], losses)

# 5. Visualization
for objs in simulation.blender_objects_output.values():
    for obj in objs:
        bproc_obj = bproc.python.types.MeshObjectUtility.MeshObject(obj)
        bproc_obj.set_shading_mode("smooth")
        if shirt.blender_obj.name in obj.name:
            obj.data.materials.append(shirt_material.blender_obj)

scene.frame_set(simulation_steps)

objects_to_hide = [ground.blender_obj, shirt.blender_obj, shirt_target]

for object in objects_to_hide:
    object.hide_viewport = True
    object.hide_render = True


bpy.ops.wm.save_as_mainfile(filepath=filepaths["blend"])

# scene.render.filepath = os.path.join(filepaths["run"], "result.png")
# bpy.ops.render.render(write_still=True)
