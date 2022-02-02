import argparse
import os
import sys

import airo_blender_toolkit as abt
import bpy
from mathutils import Vector

from cm_utils.cipc_sim import SimulationCIPC
from cm_utils.dirs import ensure_output_paths
from cm_utils.materials.penava import materials_by_name

os.environ.setdefault("INSIDE_OF_THE_INTERNAL_BLENDER_PYTHON_ENVIRONMENT", "1")

import blenderproc as bproc


def make_square_cloth(size, subdivisions, location):
    cloth = bproc.object.create_primitive("PLANE", size=size, location=location)
    cloth.persist_transformation_into_mesh()
    cloth.edit_mode()
    for _ in range(subdivisions):
        bpy.ops.mesh.subdivide()
    bpy.ops.mesh.quads_convert_to_tris()
    cloth.object_mode()
    return cloth


def run_drape_simulation(sphere_radius, cloth_size, cloth_subdivisions, cloth_material):
    bproc.init()  # configures some settings and cleans up scene

    sphere = bproc.object.create_primitive("SPHERE", radius=sphere_radius)
    sphere.blender_obj.name = "sphere"

    cloth = make_square_cloth(cloth_size, cloth_subdivisions, (0, 0, 1.1 * sphere_radius))
    cloth.blender_obj.name = "cloth"

    paths = ensure_output_paths()

    simulation_steps = 10
    simulation = SimulationCIPC(paths, 25)
    simulation.add_collider(sphere.blender_obj, friction_coefficient=0.4)
    simulation.add_cloth(cloth.blender_obj, cloth_material)
    simulation.initialize_cipc()
    simulation.run(simulation_steps)

    for objs in simulation.blender_objects_output.values():
        for obj in objs:
            bproc_obj = bproc.python.types.MeshObjectUtility.MeshObject(obj)
            bproc_obj.set_shading_mode("smooth")

    # Setting up the render
    scene = bpy.context.scene
    camera = scene.camera
    camera.location = (sphere_radius * 5, 0, 0)
    abt.camera.look_at((0, 0, 0), camera)
    camera.location -= Vector((0, 0, sphere_radius / 2))

    scene.frame_start = 0
    scene.frame_end = simulation_steps
    scene.frame_set(simulation_steps)

    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.cycles.adaptive_threshold = 0.1

    # Render background transparent
    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = "RGBA"

    # Hiding the input objects
    sphere.blender_obj.hide_viewport = True
    sphere.blender_obj.hide_render = True
    cloth.blender_obj.hide_viewport = True
    cloth.blender_obj.hide_render = True

    hdri_name = "immenstadter_horn"
    hdri_path = abt.download_hdri(hdri_name, paths["run"], res="1k")
    abt.load_hdri(hdri_path)

    # Plane to prevent colored light from the HDRI floor
    bproc.object.create_primitive("PLANE", size=1, location=(0, 0, -1))

    bpy.ops.wm.save_as_mainfile(filepath=paths["blend"])

    scene.render.filepath = os.path.join(paths["run"], "result.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    if "--" in sys.argv:
        arg_start = sys.argv.index("--") + 1
        argv = sys.argv[arg_start:]
        parser = argparse.ArgumentParser()
        parser.add_argument("-sr", "--sphere_radius", dest="sphere_radius", type=float)
        parser.add_argument("-cs", "--cloth_size", dest="cloth_size", type=float)
        parser.add_argument("-csub", "--cloth_subdivisions", dest="cloth_subdivisions", type=int)
        parser.add_argument("-cm", "--cloth_material", dest="cloth_material")
        args = parser.parse_known_args(argv)[0]

        cloth_material = materials_by_name[f"{args.cloth_material} penava"]
        run_drape_simulation(args.sphere_radius, args.cloth_size, args.cloth_subdivisions, cloth_material)
    else:
        print("Please rerun with arguments after --")
