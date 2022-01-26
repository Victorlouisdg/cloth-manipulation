from cm_utils import render
from cm_utils.dirs import ensure_output_paths
from cm_utils.materials.penava import materials
from cm_utils.cipc_sim import SimulationCIPC
import itertools
import numpy as np
import airo_blender_toolkit as abt
import bpy
from mathutils import Vector
import os

cloth_name = "cloth"
cloth = bpy.data.objects[cloth_name]
sphere = bpy.data.objects["sphere"]

# TODO make sphere and cloth here

cotton = materials[0]
friction_coefficient = 0.4

# SimulationCIPC is an adaptor between Blender and CIPC
paths = ensure_output_paths()

simulation_steps = 50

results_locations = [(1, 0, 1), (2, 0, 1), (1, 0, 0), (2, 0, 0)]


colors = [
    [0.800000, 0.040000, 0.040624, 1.000000],  # red
    [0.800000, 0.304412, 0.040000, 1.000000],  # yellow
    [0.800000, 0.186991, 0.040000, 1.000000], # orange
    #[0.040000, 0.800000, 0.090221, 1.000000],  # green
    [0.040000, 0.181768, 0.800000, 1.000000],  # blue
]


def set_blender_material(object, color):
    material = bpy.data.materials.new(name="cloth")
    material.diffuse_color = color
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.9
    object.data.materials.append(material)


for material, location, color in zip(materials, results_locations, colors):
    cloth.name = material.name
    simulation = SimulationCIPC(paths, 25)
    simulation.add_collider(sphere, friction_coefficient)
    simulation.add_cloth(cloth, material)
    simulation.initialize_cipc()
    simulation.run(simulation_steps)

    objects_flat = list(
        itertools.chain.from_iterable(simulation.blender_objects_output.values())
    )
    for obj in objects_flat:
        obj.location = location
        for f in obj.data.polygons:
            f.use_smooth = True

        if material.name in obj.name:
            set_blender_material(obj, color)

    break

results_middle = np.mean(results_locations, axis=0)
camera_location = results_middle + (0, -3, 0)

def look_at(point, camera):
    direction = Vector(point) - camera.location
    rot_quat = direction.to_track_quat("-Z", "Y")
    camera.rotation_euler = rot_quat.to_euler()


bpy.ops.object.camera_add(location=camera_location)
camera = bpy.context.active_object
#camera.data.lens = 50  # focal length in mm
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 2

look_at(results_middle, camera)
scene = bpy.context.scene
scene.camera = camera
scene.render.resolution_x = 1920
scene.render.resolution_y = 1920
scene.render.engine = "CYCLES"

hdri_name = "immenstadter_horn"
hdri_path = abt.download_hdri(hdri_name, paths["run"])
abt.load_hdri(hdri_path)

# Plane to prevent light from HDRI grass
bpy.ops.mesh.primitive_plane_add(location = (1.5, 0, -2))

scene.render.film_transparent = True
scene.cycles.adaptive_threshold = 0.1
scene.view_settings.exposure = 1
scene.view_settings.look = 'High Contrast'

cloth.hide_viewport = True
sphere.hide_viewport = True

scene.render.fps = 25
scene.frame_start = 0
scene.frame_end = simulation_steps

scene.frame_set(50)

bpy.ops.wm.save_as_mainfile(filepath=paths["blend"])

scene.render.resolution_percentage = 50
scene.render.filepath = os.path.join(paths["run"], "result.png")

bpy.ops.render.render(write_still=True)

