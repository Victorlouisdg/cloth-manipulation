import os

import airo_blender_toolkit as abt
import blenderproc as bproc
import bpy

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
camera.location = 0, 0, 3.2
camera.rotation_euler = 0, 0, 0
camera.data.lens = 80

scene.render.resolution_x = 3840
scene.render.resolution_y = 2160

hdri_name = "immenstadter_horn"  # "aviation_museum"  # studio_country_hall"# "monbachtal_riverbank"
hdri_path = abt.download_hdri(hdri_name, os.path.join(os.path.expanduser("~"), "assets"), res="1k")
abt.load_hdri(hdri_path)
