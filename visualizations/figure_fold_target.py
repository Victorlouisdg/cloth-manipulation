import airo_blender_toolkit as abt
import blenderproc as bproc

from cloth_manipulation.folds import SleeveFold
from cloth_manipulation.scene import setup_ground

bproc.init()


setup_ground()

shirt = abt.PolygonalShirt()
abt.triangulate_blender_object(shirt.blender_obj, minimum_triangle_density=20000)

shirt_material = shirt.new_material("Shirt")
shirt_material.set_principled_shader_value("Base Color", abt.colors.dark_green)
shirt_material.blender_obj.diffuse_color = abt.colors.dark_green
shirt.blender_obj.location.z = 0.003
shirt.persist_transformation_into_mesh()

# shirt.visualize_keypoints(radius=0.01)

# setup_camera_topdown()
import bpy

scene = bpy.context.scene
camera = scene.camera
camera.data.display_size = 0.2
camera.data.type = "ORTHO"
camera.data.ortho_scale = 1.2
camera.location = (0.186, 0, 1)
scene.render.resolution_x = 2000
scene.render.resolution_y = 1200

# camera = scene.camera
# camera.location = 0.936188, -1.19851, 0.919974
# camera.rotation_euler = np.deg2rad(59.2), 0, np.deg2rad(32.8)

# scene.render.resolution_x = 1024
# scene.render.resolution_y = 512

# bpy.context.space_data.shading.light = 'FLAT'

hdri_name = "aviation_museum"
hdri_path = abt.download_hdri(hdri_name, "/home/idlab185/assets", res="1k")
abt.load_hdri(hdri_path)

keypoints = {name: coord[0] for name, coord in shirt.keypoints_3D.items()}
left_sleeve = SleeveFold(keypoints, "left", angle=30)

fold_line_visualization_lengths = [
    (left_sleeve.fold_line(), 0.3, 0.1),
]

for fold_line, forward, backward in fold_line_visualization_lengths:
    abt.visualize_line(*fold_line, length_forward=forward, length_backward=backward, color=abt.colors.red)

target = left_sleeve.make_target_mesh(shirt.blender_obj, cloth_thickness=0.005)

objects_to_hide = [shirt.blender_obj]

for object in objects_to_hide:
    object.hide_viewport = True
    object.hide_render = True
