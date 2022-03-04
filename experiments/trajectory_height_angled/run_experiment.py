"""Trajectory Height experiment.

   This file will take as input a height and return a loss value.

   1) Export the objs and trajectory.
   2) Setup and run IPC
   3) Import first IPC output and last back into blender.
   4) Calculate loss.
"""
import argparse
import sys

import bpy
import numpy as np

from cm_utils import (
    encode_video,
    ensure_output_filepaths,
    export_as_obj,
    import_cipc_output,
    render,
    save_dict_as_json,
)
from cm_utils.cipc import Simulation, cipc_action
from cm_utils.folds_old import MiddleFold, SideFold, SleeveFold
from cm_utils.grasp import update_active_grippers

# Currently the vertex ids of the keypoints in the meshes are hardcoded.
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

keypoint_ids = {
    "cloth": keypoint_ids_cloth,
    "cloth_simple": keypoint_ids_cloth_simple,
}


def run_experiment(height_ratio, offset_ratio, run_dir=None):
    config = {"height_ratio": height_ratio, "offset_ratio": offset_ratio}
    paths = ensure_output_filepaths(run_dir, config=config)
    save_dict_as_json(paths["config"], config)

    # Selecting the relevant objects
    objects = bpy.data.objects
    cloth_name = "cloth"
    cloth = objects[cloth_name]
    ground = objects["ground"]

    keypoints = {name: cloth.data.vertices[id].co for name, id in keypoint_ids[cloth_name].items()}

    scene = bpy.context.scene

    scene.frame_start = 0
    scene.frame_end = 600
    scene.render.fps = 25

    cloth_path = export_as_obj(cloth, paths["run"])
    ground_path = export_as_obj(ground, paths["run"])

    fold_sequence = [
        ((0, 100), SleeveFold(keypoints, height_ratio, offset_ratio, "left")),
        ((100, 200), SleeveFold(keypoints, height_ratio, offset_ratio, "right")),
        ((200, 300), SideFold(keypoints, 0.7, 0.0, "left", "top")),
        ((200, 300), SideFold(keypoints, 0.7, 0.0, "left", "bottom")),
        ((300, 400), SideFold(keypoints, 0.7, 0.0, "right", "top")),
        ((300, 400), SideFold(keypoints, 0.7, 0.0, "right", "bottom")),
        ((400, 500), MiddleFold(keypoints, 0.5, 0.0, "left")),
        ((400, 500), MiddleFold(keypoints, 0.5, 0.0, "right")),
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
    simulation = Simulation(cloth_path, ground_path, paths["cipc"])
    cloth = import_cipc_output(paths["cipc"], 0)

    active_grippers = {}
    for frame in range(scene.frame_end):
        action = {}
        update_active_grippers(grippers, active_grippers, cloth, frame)

        for gripper, grasped in active_grippers.items():
            gripper_action = cipc_action(gripper, cloth, grasped, frame)
            action = action | gripper_action

        simulation.step(action)
        cloth = import_cipc_output(paths["cipc"], frame + 1)
        return

    scene.frame_set(scene.frame_start)

    # Saving the visualizations
    bpy.ops.object.paths_update_visible()
    bpy.ops.wm.save_as_mainfile(filepath=paths["blend"])

    # no need to transform to world space because origins coincide
    targets = np.array([v.co for v in cloth_target.data.vertices])
    final_positions = np.array([v.co for v in objects[f"sim{scene.frame_end}"].data.vertices])

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

    render(paths["renders"], resolution_percentage=50)
    encode_video(paths["renders"], paths["video"])

    return losses


if __name__ == "__main__":
    if "--" in sys.argv:
        arg_start = sys.argv.index("--") + 1
        argv = sys.argv[arg_start:]
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
        print("Please rerun with arguments after --")
