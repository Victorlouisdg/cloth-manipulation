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
from cm_utils import test, export_as_obj, import_cipc_outputs, render
from cm_utils import get_grasped_verts_trajectories, calcucate_velocities

sys.path.insert(0, os.path.dirname(__file__))
from cipc import simulate


# CIPC_PATH = "/home/idlab185/Codim-IPC"
# CIPC_PYTHON_PATH = os.path.join(CIPC_PATH, "Python")
# CIPC_BUILD_PATH = os.path.join(CIPC_PATH, "build")

# sys.path.insert(0, CIPC_PYTHON_PATH)
# sys.path.insert(0, CIPC_BUILD_PATH)

# from JGSL import *
# import Drivers

#print("JGSL module location:", JGSL.__file__)

import os
import datetime

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

    objects = bpy.data.objects
    cloth = objects['cloth_simple']
    gripper = objects['gripper']

    cloth_path = export_as_obj('cloth_simple', output_dir)
    ground_path = export_as_obj('ground', output_dir)

    trajs, times = get_grasped_verts_trajectories(cloth, gripper)
    velocities = calcucate_velocities(trajs, times)

    cipc_output_dir = os.path.join(output_dir, "cipc")
    os.makedirs(cipc_output_dir)


    simulate(cloth_path, ground_path, cipc_output_dir, velocities)

    import_cipc_outputs(cipc_output_dir)

    new_blend_path = os.path.join(output_dir, f"scene_with_results.blend")
    bpy.ops.wm.save_as_mainfile(filepath=new_blend_path)

    renders_dir = os.path.join(output_dir, "renders")
    render(renders_dir)



    #simulate(cloth_path, ground_path, cipc_output_dir)

    # 1) make_fold_target
    # 2) TODO maybe export with origin at 0,0,0 so z-translation backed in
    # export cloth target -> not needed initially
    # export trajectory
    # 3) run IPC with cloth.obj and ground.obj
    # 4) import IPC results back into blender
    # 5) loss: MSE  by iterating over mesh in blender
    # 5.1) later: import objs with libigl, iterate there for losses 




# CIPC_PATH = /home/Codim-IPC/

if __name__ == "__main__":
    test.test_print()

    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--') + 1:]
        parser = argparse.ArgumentParser()
        parser.add_argument('-ht', '--height', dest='height', type=float)
        args = parser.parse_known_args(argv)[0]
        print('height: ', args.height)
        height = args.height

        run(height)
    else:
        print(f"Please rerun with arguments.")



