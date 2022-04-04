import os

import airo_blender_toolkit as abt
import blenderproc as bproc
import bpy
import numpy as np


def setup_ground():
    ground = bproc.object.create_primitive("PLANE", size=5.0)
    ground.blender_obj.name = "Ground"
    ground_material = ground.new_material("Ground")
    ground_material.set_principled_shader_value("Base Color", abt.colors.light_blue)
    ground_material.blender_obj.diffuse_color = abt.colors.light_blue
    return ground


def setup_shirt_material(shirt):
    shirt_material = shirt.new_material("Shirt")
    shirt_material.set_principled_shader_value("Sheen", 1.0)
    shirt_material.set_principled_shader_value("Roughness", 1.0)
    shirt_material.set_principled_shader_value("Base Color", abt.colors.dark_green)
    shirt_material.blender_obj.diffuse_color = abt.colors.dark_green
    return shirt_material


def setup_camera_perspective():
    scene = bpy.context.scene
    camera = scene.camera
    camera.location = 0.936188, -1.19851, 0.919974
    camera.rotation_euler = np.deg2rad(59.2), 0, np.deg2rad(32.8)

    scene.render.resolution_x = 1024
    scene.render.resolution_y = 512
    scene.view_settings.look = "High Contrast"


def setup_camera_topdown():
    scene = bpy.context.scene
    camera = scene.camera
    camera.data.display_size = 0.2
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.5
    camera.location = (0, 0, 1)
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 512
    scene.view_settings.look = "High Contrast"


def setup_enviroment_texture():
    hdri_name = "aviation_museum"
    assets_path = os.path.join(os.path.expanduser("~"), "assets")
    hdri_path = abt.download_hdri(hdri_name, assets_path, res="1k")
    abt.load_hdri(hdri_path)
