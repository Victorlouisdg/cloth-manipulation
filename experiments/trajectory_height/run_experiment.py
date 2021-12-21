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

from cm_utils import export_as_obj, import_cipc_outputs, render, encode_video
from cm_utils import (
    get_grasped_verts_trajectories,
    calcucate_velocities,
    set_trajectory_height,
)
from cm_utils.cipc import simulate
from cm_utils import ensure_output_paths, save_dict_as_json


def run_experiment(height, run_dir=None):
    config = {"height": height}
    paths = ensure_output_paths(run_dir, config=config)
    save_dict_as_json(paths["config"], config)

    # Selecting the relevant objects
    objects = bpy.data.objects
    cloth_name = "cloth_simple"
    cloth = objects[cloth_name]
    gripper = objects["gripper"]
    ground = objects["ground"]

    # Editing the gripper height
    set_trajectory_height(gripper, height)

    # Exporting to obj for CIPC
    cloth_path = export_as_obj(cloth, paths["run"])
    ground_path = export_as_obj(ground, paths["run"])

    # Evaluating controlled vertices' velocities for all frames
    trajs, times = get_grasped_verts_trajectories(cloth, gripper)
    velocities = calcucate_velocities(trajs, times)

    # Simulating with CIPC and importing the results
    simulate(cloth_path, ground_path, paths["cipc"], velocities)
    import_cipc_outputs(paths["cipc"])

    # Saving the visualizations
    bpy.ops.object.paths_update_visible()
    bpy.ops.wm.save_as_mainfile(filepath=paths["blend"])

    # Calculating losses
    # no need to transform to world space because origins coincide
    targets = np.array([v.co for v in objects[f"{cloth_name}_target"].data.vertices])
    positions = np.array([v.co for v in objects["sim100"].data.vertices])

    distances = np.linalg.norm(targets - positions, axis=1)
    sq_distances = distances ** 2
    mean_distance = distances.mean(axis=0)
    mean_sq_distance = sq_distances.mean(axis=0)
    rms_distance = np.sqrt(mean_sq_distance)

    losses = {
        "mean_distance": mean_distance,
        "mean_sq_distance": mean_sq_distance,
        "rms_distance": rms_distance,
    }
    save_dict_as_json(paths["losses"], losses)

    render(paths["renders"], resolution_percentage=50)
    encode_video(paths["renders"], paths["video"])

    return losses


if __name__ == "__main__":
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1 :]
        parser = argparse.ArgumentParser()
        parser.add_argument("-ht", "--height", dest="height", type=float)
        parser.add_argument("-d", "--dir", dest="run_dir", metavar="RUN_DIR")
        args = parser.parse_known_args(argv)[0]
        print("HEIGHT: ", args.height)
        losses = run_experiment(args.height, args.run_dir)

        print("LOSSES")
        for k, v in losses.items():
            print(f"{k} = {v}")
    else:
        print(f"Please rerun with arguments.")
