import airo_blender_toolkit as abt
import blenderproc as bproc
import bpy
from mathutils import Matrix

from cm_utils.cipc_sim import SimulationCIPC
from cm_utils.dirs import ensure_output_filepaths
from cm_utils.folds import BezierFoldTrajectory, SleeveFold
from cm_utils.materials.penava import materials_by_name

bproc.init()

shirt = abt.PolygonalShirt()
abt.triangulate_blender_object(shirt.blender_object, minimum_triangle_density=1000)
shirt.blender_obj.location.z = 0.6
shirt.persist_transformation_into_mesh()

# shirt.visualize_keypoints(radius=0.01)

airo_orange = [0.94, 0.60, 0.23, 1.0]
shirt_material = shirt.new_material(name=shirt.blender_obj.name)
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

keypoints = {name: coord[0] for name, coord in shirt.keypoints_3D.items()}


side = "left"
# sides = ["left", "right"]

# for side in sides:
fold = SleeveFold(keypoints, side)
# empty = abt.visualize_transform(fold.gripper_start_pose(), 0.1)
# abt.visualize_line(*fold.fold_line(), length=1.5)

height_ratio = 0.5
tilt_angle = 20 if side == "right" else -20
fold_trajectory = BezierFoldTrajectory(fold, height_ratio, tilt_angle)
# abt.visualize_path(fold_trajectory.path)

sphere = bproc.object.create_primitive("SPHERE", radius=0.5)
sphere.blender_obj.name = "sphere"

filepaths = ensure_output_filepaths()

cloth_material = materials_by_name["cotton penava"]

simulation_steps = 50

simulation = SimulationCIPC(filepaths, 25)
simulation.add_collider(sphere.blender_obj, friction_coefficient=0.4)
simulation.add_cloth(shirt.blender_obj, cloth_material)
simulation.initialize_cipc()

gripper = bproc.object.create_primitive("CUBE", size=0.05)
gripper.blender_obj.name = "Gripper"
gripper.blender_obj.matrix_world = Matrix(fold_trajectory.start)

# simulation.run(simulation_steps)

# for objs in simulation.blender_objects_output.values():
#     for obj in objs:
#         bproc_obj = bproc.python.types.MeshObjectUtility.MeshObject(obj)
#         bproc_obj.set_shading_mode("smooth")
#         if shirt.blender_obj.name in obj.name:
#             obj.data.materials.append(shirt_material.blender_obj)


# scene.frame_start = 0
# scene.frame_end = simulation_steps
# scene.frame_set(simulation_steps)

# # Hiding the input objects
# sphere.blender_obj.hide_viewport = True
# sphere.blender_obj.hide_render = True
# shirt.blender_obj.hide_viewport = True
# shirt.blender_obj.hide_render = True

# hdri_name = "immenstadter_horn"
# hdri_path = abt.download_hdri(hdri_name, filepaths["run"], res="1k")
# abt.load_hdri(hdri_path)

# bpy.ops.wm.save_as_mainfile(filepath=filepaths["blend"])

# scene.render.filepath = os.path.join(filepaths["run"], "result.png")
# bpy.ops.render.render(write_still=True)
