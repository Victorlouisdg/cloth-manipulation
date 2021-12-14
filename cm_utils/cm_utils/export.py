import bpy
import argparse
import sys
import os


def export_as_obj(object, filepath):
    if filepath is None:
        filepath = os.path.join(os.getcwd(), f"{object.name}.obj")

    if os.path.isdir(filepath):
        filepath = os.path.join(filepath, f"{object.name}.obj")

    for o in bpy.data.objects:
        o.select_set(False)

    object.select_set(True)
    bpy.ops.export_scene.obj(filepath=filepath, use_selection=True, use_materials=False)
    return filepath


if __name__ == "__main__":
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1 :]
        parser = argparse.ArgumentParser()
        parser.add_argument("object_name")
        parser.add_argument(
            "-o", "--output", dest="output_dir", metavar="OUTPUT_FILEPATH"
        )
        args = parser.parse_known_args(argv)[0]
        export_as_obj(args.object_name, args.output_dir)