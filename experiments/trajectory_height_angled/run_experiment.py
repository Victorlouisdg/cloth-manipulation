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

from cm_utils.folds import keyframe_sleeve_fold
from cm_utils import export_as_obj, import_cipc_outputs, render, encode_video
from cm_utils import (
    get_grasped_verts_trajectories,
    calculate_velocities,
    set_trajectory_height,
    make_gripper,
)
from cm_utils.grasp import visualize_trajectories
from cm_utils.cipc import Simulation
from cm_utils import ensure_output_paths, save_dict_as_json

keypoint_ids_cloth_simple = {
    "left_shoulder": 22,
    "left_sleeve_top": 2,
    "left_sleeve_bottom": 0,
    "left_armpit": 18,
    "left_corner_bottom": 8,
    "right_shoulder": 53,
    "right_sleeve_top": 29,
    "right_sleeve_bottom": 27,
    "right_armpit": 49,
    "right_corner_bottom": 35,
}


def run_experiment(height_ratio, offset_ratio, run_dir=None):
    config = {"height_ratio": height_ratio, "offset_ratio": offset_ratio}
    paths = ensure_output_paths(run_dir, config=config)
    save_dict_as_json(paths["config"], config)

    # Selecting the relevant objects
    objects = bpy.data.objects
    cloth_name = "cloth_simple"
    cloth = objects[cloth_name]
    ground = objects["ground"]

    keypoints = {
        name: cloth.data.vertices[id].co
        for name, id in keypoint_ids_cloth_simple.items()
    }

    scene = bpy.context.scene

    frames_per_fold = 100
    scene.frame_end = 227  # todo think about these frames in more detail
    scene.render.fps = 25

    cloth_path = export_as_obj(cloth, paths["run"])
    ground_path = export_as_obj(ground, paths["run"])

    simulation = Simulation(cloth_path, ground_path, paths["cipc"])

    for i, side in enumerate(["left", "right"]):
        gripper = make_gripper(f"gripper_{side}_sleeve")

        start_frame = i * (frames_per_fold + 1)
        end_frame = start_frame + frames_per_fold + 1

        keyframe_sleeve_fold(gripper, keypoints, side, height_ratio, offset_ratio, start_frame, end_frame)

        # TODO if i != 0, import final frame and get new grasped vertices
        trajs, times = get_grasped_verts_trajectories(
            cloth, gripper, start_frame, end_frame
        )

        velocities = calculate_velocities(trajs, times)
        simulation.advance(frames_per_fold + 1, velocities)


    simulation.advance(25, {})

    import_cipc_outputs(paths["cipc"])

    # Saving the visualizations
    bpy.ops.object.paths_update_visible()
    bpy.ops.wm.save_as_mainfile(filepath=paths["blend"])

    #  TODO update Calculating losses
    # no need to transform to world space because origins coincide
    # targets = np.array([v.co for v in objects[f"{cloth_name}_target"].data.vertices])
    # positions = np.array([v.co for v in objects["sim100"].data.vertices])

    # distances = np.linalg.norm(targets - positions, axis=1)
    # sq_distances = distances ** 2
    # mean_distance = distances.mean(axis=0)
    # mean_sq_distance = sq_distances.mean(axis=0)
    # rms_distance = np.sqrt(mean_sq_distance)

    losses = {}
    # losses = {
    #     "mean_distance": mean_distance,
    #     "mean_sq_distance": mean_sq_distance,
    #     "rms_distance": rms_distance,
    # }
    # save_dict_as_json(paths["losses"], losses)

    render(paths["renders"], resolution_percentage=50)
    encode_video(paths["renders"], paths["video"])

    return losses


if __name__ == "__main__":
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1 :]
        parser = argparse.ArgumentParser()
        parser.add_argument("-hr", "--height_ratio", dest="height_ratio", type=float)
        parser.add_argument("-or", "--offset_ratio", dest="offset_ratio", type=float)
        parser.add_argument("-d", "--dir", dest="run_dir", metavar="RUN_DIR")
        args = parser.parse_known_args(argv)[0]
        losses = run_experiment(args.height_ratio, args.offset_ratio, args.run_dir)

        print("LOSSES")
        for k, v in losses.items():
            print(f"{k} = {v}")
    else:
        print(f"Please rerun with arguments after --")
