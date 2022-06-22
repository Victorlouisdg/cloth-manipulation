import argparse
import os
import sys

import airo_blender_toolkit as abt
import blenderproc as bproc
import bpy
import numpy as np
from cipc.dirs import ensure_output_filepaths, save_dict_as_json
from cipc.materials.penava import materials_by_name
from cipc.simulator import SimulationCIPC

from cloth_manipulation.folds import BezierFoldTrajectory, SleeveFold
from cloth_manipulation.losses import mean_distance
from cloth_manipulation.scene import setup_camera_topdown, setup_enviroment_texture, setup_ground, setup_shirt_material


def fold_sleeves(height_ratio=0.8, tilt_angle=20, run_dir=None):
    # 1. Setting up the scene
    bproc.init()

    ground = setup_ground()
    setup_camera_topdown()
    setup_enviroment_texture()

    cloth_material = materials_by_name["cotton penava"]

    shirt = abt.PolygonalShirt()
    shirt_obj = shirt.blender_obj
    abt.triangulate_blender_object(shirt_obj, minimum_triangle_density=20000)
    shirt_obj.location.z = 2.0 * cloth_material.thickness  # ground offset + cloth offset
    shirt.persist_transformation_into_mesh()
    # shirt.visualize_keypoints(radius=0.01)

    shirt_material = setup_shirt_material(shirt)

    keypoints = {name: coord[0] for name, coord in shirt.keypoints_3D.items()}
    left_sleeve = SleeveFold(keypoints, "left")
    right_sleeve = SleeveFold(keypoints, "right")

    # Visualizing the fold lines
    fold_line_visualization_lengths = [
        (left_sleeve.fold_line(), 0.3, 0.1),
        (right_sleeve.fold_line(), 0.1, 0.3),
    ]
    for fold_line, forward, backward in fold_line_visualization_lengths:
        abt.visualize_line(*fold_line, length_forward=forward, length_backward=backward, color=abt.colors.red)

    # The 2.0 below is because C-IPC offsets this thickness on both side, might need to halve this later.
    left_target = left_sleeve.make_target_mesh(shirt.blender_obj, cloth_thickness=2.0 * cloth_material.thickness)
    target = right_sleeve.make_target_mesh(left_target, cloth_thickness=2.0 * cloth_material.thickness)

    fold_steps = [[left_sleeve], [right_sleeve]]

    frames_per_fold_step = 100
    frames_between_fold_steps = 5
    simulation_steps = len(fold_steps) * (frames_per_fold_step + frames_between_fold_steps)

    scene = bpy.context.scene
    scene.frame_end = simulation_steps

    print(f"Simulating {simulation_steps} steps.")

    # Setting up the animated grippers
    grippers = []
    frame = scene.frame_start

    for fold_step in fold_steps:
        for fold in fold_step:
            angle = tilt_angle if fold.side == "right" else -1 * tilt_angle
            fold_trajectory = BezierFoldTrajectory(fold, height_ratio, angle, end_height=0.05)
            gripper = abt.BlockGripper()
            abt.keyframe_trajectory(gripper.gripper_obj, fold_trajectory, frame, frame + frames_per_fold_step)
            bpy.ops.object.paths_range_update()
            bpy.ops.object.paths_calculate(start_frame=scene.frame_start, end_frame=scene.frame_end)
            grippers.append(gripper)
            abt.visualize_path(fold_trajectory.path, color=abt.colors.orange, radius=0.005)
            # abt.visualize_transform(fold_trajectory.pose(0.0))
        frame += frames_per_fold_step + frames_between_fold_steps

    config = {"height_ratio": height_ratio, "tilt_angle": tilt_angle}
    filepaths = ensure_output_filepaths(run_dir, config=config)

    # Running the simulation
    simulation = SimulationCIPC(filepaths, 25)
    simulation.friction_coefficient = 0.5
    simulation.add_cloth(shirt.blender_obj, cloth_material)
    simulation.add_collider(ground.blender_obj, friction_coefficient=0.8)
    simulation.initialize_cipc()

    simulated_shirt = shirt.blender_obj

    for frame in range(scene.frame_start, scene.frame_end):
        scene.frame_set(frame)
        action = {}
        for gripper in grippers:
            action |= gripper.action(simulated_shirt)
        simulation.step(action)
        simulated_shirt = simulation.blender_objects_output[shirt_obj.name][frame + 1]
        scene.frame_set(frame + 1)

    # 4. Calculating the loss
    print(target.name)
    print(simulated_shirt.name)
    print(shirt.blender_obj.name)

    targets = np.array([target.matrix_world @ v.co for v in target.data.vertices])
    simulated_positions = np.array([simulated_shirt.matrix_world @ v.co for v in simulated_shirt.data.vertices])
    initial_positions = np.array([shirt.blender_obj.matrix_world @ v.co for v in shirt.blender_obj.data.vertices])

    losses = {
        "mean_distance": mean_distance(targets, simulated_positions),
    }

    mean_distance_initial = mean_distance(targets, initial_positions)

    print("Mean distance (initial):", mean_distance_initial)
    print("Mean distance (result):", losses["mean_distance"])

    save_dict_as_json(filepaths["losses"], losses)

    # 5. Visualization
    for shirt_obj in simulation.blender_objects_output[shirt.blender_obj.name].values():
        shirt_obj.data.materials.append(shirt_material.blender_obj)

    scene.frame_set(simulation_steps)
    objects_to_hide = [ground.blender_obj, shirt.blender_obj, left_target, target]

    for object in objects_to_hide:
        object.hide_viewport = True
        object.hide_render = True

    scene.cycles.adaptive_threshold = 0.1
    scene.render.filepath = os.path.join(filepaths["run"], "result.png")

    bpy.ops.wm.save_as_mainfile(filepath=filepaths["blend"])
    bpy.ops.render.render(write_still=True)

    return losses


if __name__ == "__main__":
    if "--" in sys.argv:
        arg_start = sys.argv.index("--") + 1
        argv = sys.argv[arg_start:]
        parser = argparse.ArgumentParser()
        parser.add_argument("-ht", "--height_ratio", dest="height_ratio", type=float)
        parser.add_argument("-ta", "--tilt_angle", dest="tilt_angle", type=float)
        parser.add_argument("-d", "--dir", dest="run_dir", metavar="RUN_DIR")
        args = parser.parse_known_args(argv)[0]

        print(args.run_dir)
        fold_sleeves(args.height_ratio, args.tilt_angle, args.run_dir)
    else:
        print("Please rerun with arguments.")
