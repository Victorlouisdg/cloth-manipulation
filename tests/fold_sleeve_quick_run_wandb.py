import json
import os
import subprocess

import wandb


def run_wandb():
    with wandb.init(project="simfolds_test", entity="victorlouis") as run:
        height_ratio = 0.6
        tilt_angle = 30

        dir = os.path.dirname(os.path.abspath(__file__))
        wandb_dir = os.path.join(dir, "output", run.name)
        os.makedirs(wandb_dir)

        subdir = os.path.join(wandb_dir, f"height_ratio: {height_ratio:.4f} tilt_angle: {tilt_angle}")
        os.makedirs(subdir)

        log = {"height_ratio": height_ratio, "tilt_angle": tilt_angle}  # , "height_ratio-tilt_angle": value}

        runCommand = f"blender -b -P fold_sleeve_quick.py -- -ht {height_ratio} -ta {tilt_angle} -d '{subdir}'"
        subprocess.run([runCommand], shell=True, stdout=subprocess.DEVNULL)

        with open(os.path.join(subdir, "losses.json")) as f:
            losses = json.load(f)

        log = log | losses
        wandb.log(log)
        wandb.log({"result": wandb.Image(os.path.join(subdir, "result.png"))})


if __name__ == "__main__":
    run_wandb()
