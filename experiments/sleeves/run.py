import airo_blender_toolkit as abt
import blenderproc as bproc
import bpy

from cm_utils.folds import SleeveFold

bproc.init()

shirt = abt.PolygonalShirt()
shirt.visualize_keypoints(radius=0.01)

abt.triangulate_blender_object(shirt.blender_object, minimum_triangle_density=100)

abt.show_wireframes()
bpy.context.scene.camera.location.z += 2.0

bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080

keypoints = {name: coord[0] for name, coord in shirt.keypoints_3D.items()}

fold = SleeveFold(keypoints, "left")

empty = abt.visualize_transform(fold.gripper_start_pose(), 0.1)
abt.visualize_line(*fold.fold_line(), length=1.5)
