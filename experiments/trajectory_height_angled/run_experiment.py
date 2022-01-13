"""Trajectory Height experiment.

   This file will take as input a height and return a loss value.

   1) Export the objs and trajectory.
   2) Setup and run IPC
   3) Import first IPC output and last back into blender.
   4) Calculate loss.
"""
from cm_utils.grasp import find_grasped_vertices, update_active_grippers
import bpy
import sys
import argparse
import numpy as np

from cm_utils.folds import SleeveFold
from cm_utils import export_as_obj, import_cipc_output, render, encode_video
from cm_utils import (
    get_grasped_verts_trajectories,
    calculate_velocities,
)
from cm_utils.cipc import Simulation, cipc_action
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

keypoint_ids_cloth = {
    "left_shoulder": 1121,
    "left_sleeve_top": 57,
    "left_sleeve_bottom": 0,
    "left_armpit": 929,
    "left_corner_bottom": 369,
    "right_shoulder": 2583,
    "right_sleeve_top": 1492,
    "right_sleeve_bottom": 1435,
    "right_armpit": 2391,
    "right_corner_bottom": 1804,
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

    # frames_per_fold = 101
    scene.frame_start = 0
    scene.frame_end = 227  # todo think about these frames in more detail
    scene.render.fps = 25

    cloth_path = export_as_obj(cloth, paths["run"])
    ground_path = export_as_obj(ground, paths["run"])

    fold_sequence = [
        ((0, 100), SleeveFold(keypoints, height_ratio, offset_ratio, "left")),
        ((100, 200), SleeveFold(keypoints, height_ratio, offset_ratio, "right")),
        # SideFold("left", "top"),
        # SideFold("left", "bottom"),
        # SideFold(),
        # SideFold()
    ]

    # Keyframe the grippers for each fold
    grippers = []
    for (start_frame, end_frame), fold in fold_sequence:
        gripper = fold.make_keyframed_gripper(start_frame, end_frame)
        grippers.append(gripper)

    # Create the idealized cloth target shape
    cloth_target = cloth
    for _, fold in fold_sequence:
        cloth_target = fold.make_folded_cloth_target(cloth_target)

    scene.frame_set(scene.frame_start)

    # Simulate
    active_grippers = {}
    simulation = Simulation(cloth_path, ground_path, paths["cipc"])
    for frame in range(50): #range(scene.frame_end):
        action = {}

        update_active_grippers(grippers, active_grippers, cloth, frame)

        # TODO FIGURE OUT WHY CLOTH DOESNT MOVE PERFECTLY WITH GRIPPER
        for gripper, grasped in active_grippers.items():
            gripper_action = cipc_action(gripper, cloth, grasped, frame)
            action = action | gripper_action

        simulation.step(action)
        cloth = import_cipc_output(paths["cipc"], frame)

    scene.frame_set(scene.frame_start)

    # Saving the visualizations
    bpy.ops.object.paths_update_visible()
    bpy.ops.wm.save_as_mainfile(filepath=paths["blend"])

    # no need to transform to world space because origins coincide
    targets = np.array([v.co for v in cloth_target.data.vertices])
    final_positions = np.array(
        [v.co for v in objects[f"sim{scene.frame_end}"].data.vertices]
    )

    distances = np.linalg.norm(targets - final_positions, axis=1)
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

    # render(paths["renders"], resolution_percentage=50)
    # encode_video(paths["renders"], paths["video"])

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
