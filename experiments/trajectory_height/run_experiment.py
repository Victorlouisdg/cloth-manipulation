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
import numpy as np
import json

from cm_utils import export_as_obj, import_cipc_outputs, render
from cm_utils import get_grasped_verts_trajectories, calcucate_velocities

# This allows import from this dir even when running with blender
sys.path.insert(0, os.path.dirname(__file__))
from cipc import simulate


def create_output_dir(height):
    dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.datetime.now()
    run_name = f"height={height:.4f} ({timestamp})"
    output_dir = os.path.join(dir, "output", run_name)
    os.makedirs(output_dir)
    return output_dir


def set_trajectory_height(gripper, height):
    action = gripper.animation_data.action
    zcurve = action.fcurves[2]
    z1_key = zcurve.keyframe_points[1]
    z1_key.co[1] = height
    z1_key.handle_left[1] = height
    z1_key.handle_right[1] = height


def run_experiment(height, output_dir=None):

    if output_dir is None:
        output_dir = create_output_dir(height)

    print("Running Trajectory Height experiment with height: ", height)

    # Selecting the relevant objects
    objects = bpy.data.objects
    cloth_name = "cloth"
    cloth = objects[cloth_name]
    gripper = objects["gripper"]
    ground = objects["ground"]

    # Editing the gripper height
    set_trajectory_height(gripper, height)

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
    # no need to transform to world space because origins coincide
    targets = np.array([v.co for v in objects[f"{cloth_name}_target"].data.vertices])
    positions = np.array([v.co for v in objects["sim100"].data.vertices])

    distances = np.linalg.norm(targets - positions, axis=1)
    sq_distances = distances ** 2
    mean_distance = distances.mean(axis=0)
    mean_sq_distance = sq_distances.mean(axis=0)
    rms_distance = np.sqrt(mean_sq_distance)

    # Saving the visualizations
    new_blend_path = os.path.join(output_dir, f"scene_with_results.blend")
    bpy.ops.wm.save_as_mainfile(filepath=new_blend_path)

    renders_dir = os.path.join(output_dir, "renders")
    render(renders_dir, resolution_percentage=50)

    losses = {
        "mean_distance": mean_distance,
        "mean_sq_distance": mean_sq_distance,
        "rms_distance": rms_distance,
    }

    print(losses)

    with open(os.path.join(output_dir, "losses.json"), "w") as f:
        json.dump(losses, f)

    return losses


if __name__ == "__main__":
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1 :]
        parser = argparse.ArgumentParser()
        parser.add_argument("-ht", "--height", dest="height", type=float)
        parser.add_argument(
            "-o", "--output", dest="output_dir", metavar="OUTPUT_DIR"
        )
        args = parser.parse_known_args(argv)[0]
        print("height: ", args.height)

        losses = run_experiment(args.height, args.output_dir)

        print("LOSSES")
        for k, v in losses.items():
            print(f"{k} = {v}")
    else:
        print(f"Please rerun with arguments.")
