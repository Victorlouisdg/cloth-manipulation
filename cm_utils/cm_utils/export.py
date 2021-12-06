import bpy
import argparse
import sys
import os

def export_as_obj(name, filepath):
    if filepath is None:
        filepath = os.path.join(os.getcwd(), f"{name}.obj")

    if os.path.isdir(filepath):
        filepath = os.path.join(filepath, f"{name}.obj")

    objects = bpy.data.objects
    object = objects[name]

    for o in objects:
        o.select_set(False)

    object.select_set(True)
    bpy.ops.export_scene.obj(filepath=filepath, use_selection=True, use_materials=False)
    return filepath


def export_trajectory_as_velocities(name, filepath):

    scene = bpy.context.scene

    # animation in blender should go from 0 tot 100
    # -> this leads to 100 frames being simulated
    # -> set fps e.g. 25

    # 

    # for i in range(n_sim_frames + 1):
    #     scene.frame_set(i)
    #     locations.append(obj.location.copy())
    #     times.append(dt * i) 


if __name__ == "__main__":
    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--') + 1:]
        parser = argparse.ArgumentParser()
        parser.add_argument('object_name')
        parser.add_argument('-o', '--output', dest='output_dir', metavar='OUTPUT_FILEPATH')
        args = parser.parse_known_args(argv)[0]
        export_as_obj(args.object_name, args.output_dir)
