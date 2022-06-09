import json
import os
import subprocess

import numpy as np
import wandb


def parse_parameters(run):
    value = run.config["height_ratio-tilt_angle"]
    height_ratio, tilt_angle = value.split("-")
    height_ratio = float(height_ratio)
    tilt_angle = float(tilt_angle)
    return height_ratio, tilt_angle


def make_output_dir(run_name, height_ratio, tilt_angle):
    dir = os.path.dirname(os.path.abspath(__file__))
    wandb_dir = os.path.join(dir, "output", run_name)
    subdir = os.path.join(wandb_dir, f"height_ratio {height_ratio:.4f} tilt_angle {tilt_angle}")
    os.makedirs(subdir)
    return subdir


def log_results(height_ratio, tilt_angle, output_dir):
    log = {"height_ratio": height_ratio, "tilt_angle": tilt_angle}
    with open(os.path.join(output_dir, "losses.json")) as f:
        losses = json.load(f)
    log = log | losses
    wandb.log(log)
    wandb.log({"result": wandb.Image(os.path.join(output_dir, "result.png"))})


def get_missing(project):
    api = wandb.Api()
    experiment = project

    all_radii = []
    all_thetas = []

    for height_ratio in np.linspace(0.1, 1.0, 14):
        for angle in np.linspace(30.0, 90.0, max(2, int(18 * height_ratio))):
            all_radii.append(height_ratio)
            all_thetas.append(np.deg2rad(angle))

    runs = api.runs(path=f"victorlouis/{experiment}")
    runs = [run for run in runs if len(run.summary._json_dict) and "mean_distance" in run.summary]

    thetas = []
    radii = []
    losses = []

    print("Amount of runs:", len(runs))
    for run in runs:
        s = run.summary
        radii.append(float(s["height_ratio"]))
        thetas.append(np.deg2rad(90.0 - s["tilt_angle"]))
        losses.append(s["mean_distance"])

    missing_thetas = []
    missing_radii = []

    for combo in zip(all_thetas, all_radii):
        if not np.any(
            [np.isclose(combo[0], combo2[0]) and np.isclose(combo[1], combo2[1]) for combo2 in zip(thetas, radii)]
        ):
            theta, radius = combo
            missing_thetas.append(theta)
            missing_radii.append(radius)

    return missing_thetas, missing_radii


def run_wandb(script, project, height_ratio, tilt_angle):
    with wandb.init(project=project, tags=["fix"]) as run:
        # height_ratio, tilt_angle = parse_parameters(run)
        output_dir = make_output_dir(run.name, height_ratio, tilt_angle)

        runCommand = (
            f"blender -b -P {script} -- -ht {height_ratio} -ta {tilt_angle} -d '{output_dir}' -cm 0 -sh 0 -fc 0.5"
        )

        print(runCommand)

        subprocess.run([runCommand], shell=True, stdout=subprocess.DEVNULL)

        log_results(height_ratio, tilt_angle, output_dir)


if __name__ == "__main__":
    project = "fold_sleeve_default"  # ENSURE PARAMS IN COMMAND ABOVE ARE CORRECT FOR PROJECT!
    script = "fold_sleeve.py"

    missing_thetas, missing_radii = get_missing(project)
    n_missings = len(missing_thetas)

    missing_angles = [90.0 - np.rad2deg(t) for t in missing_thetas]

    for i in range(n_missings):
        print(missing_angles[i], missing_radii[i])
        run_wandb(script, project, missing_radii[i], missing_angles[i])
