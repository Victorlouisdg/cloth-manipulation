"""Trajectory Height experiment.

   This file will take as input a height and return a loss value.

   1) Export the objs and trajectory.
   2) Setup and run IPC
   3) Import first IPC output and last back into blender.
   4) Calculate loss.
"""
import bpy
import os
import sys
import argparse
import datetime

from cm_utils import export_as_obj, import_cipc_outputs, render
from cm_utils import get_grasped_verts_trajectories, calcucate_velocities

sys.path.insert(0, os.path.dirname(__file__))
from cipc import simulate


def create_output_dir(height):
    dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.datetime.now()
    run_name = f"height={height:.4f} ({timestamp})"
    output_dir = os.path.join(dir, "output", run_name)
    os.makedirs(output_dir)
    return output_dir


def run(height):
    print("Running Trajectory Height experiment with height: ", height)
    output_dir = create_output_dir(height)

    # Selecting the relevant objects
    objects = bpy.data.objects
    cloth = objects["cloth_simple"]
    gripper = objects["gripper"]
    ground = objects["ground"]

    # TODO EDIT THE GRIPPER HEIGHT!

    # Exporting to obj for CIPC
    cloth_path = export_as_obj(cloth, output_dir)
    ground_path = export_as_obj(ground, output_dir)

    # Evaluating controlled vertices' velocities for all frames
    trajs, times = get_grasped_verts_trajectories(cloth, gripper)
    velocities = calcucate_velocities(trajs, times)

    # Simulating with CIPC and importing the results
    cipc_output_dir = os.path.join(output_dir, "cipc")
    os.makedirs(cipc_output_dir)
    simulate(cloth_path, ground_path, cipc_output_dir, velocities)
    import_cipc_outputs(cipc_output_dir)

    # Calculating losses
    # 1) make_fold_target
    # 5) loss: MSE  by iterating over mesh in blender
    # 5.1) later: import objs with libigl, iterate there for losses
    # coords0 = bpy.data.objects[""]

    # Saving the visualizations
    new_blend_path = os.path.join(output_dir, f"scene_with_results.blend")
    bpy.ops.wm.save_as_mainfile(filepath=new_blend_path)

    renders_dir = os.path.join(output_dir, "renders")
    render(renders_dir, resolution_percentage=50)


if __name__ == "__main__":
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1 :]
        parser = argparse.ArgumentParser()
        parser.add_argument("-ht", "--height", dest="height", type=float)
        args = parser.parse_known_args(argv)[0]
        print("height: ", args.height)
        height = args.height

        run(height)
    else:
        print(f"Please rerun with arguments.")
