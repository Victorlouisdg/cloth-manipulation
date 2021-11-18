import bpy
import argparse
import sys

def export_as_obj(name, filepath):
    objects = bpy.data.objects
    object = objects[name]

    for o in objects:
        o.select_set(False)

    object.select_set(True)
    bpy.ops.export_scene.obj(filepath=filepath, use_selection=True, use_materials=False)


# ground = objects["Ground Plane"]

# cloth.select_set(True)


# dir = "/home/idlab185/Codim-IPC/Projects/FEMShell/input/victor/"

# bpy.ops.export_scene.obj(filepath=dir + "cloth.obj", use_selection=True, use_materials=False)

# cloth.select_set(False)
# ground.select_set(True)

# bpy.ops.export_scene.obj(filepath=dir +"ground.obj", use_selection=True, use_materials=False)

if __name__ == "__main__":
    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--') + 1:]
        parser = argparse.ArgumentParser()
        parser.add_argument('object_name')
        parser.add_argument('-o', '--output', dest='output_dir', metavar='OUTPUT_FILEPATH')
        args = parser.parse_known_args(argv)[0]
        print('height: ', args.height)
        height = args.height