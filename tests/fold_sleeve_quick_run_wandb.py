import argparse
import json
import os
import shutil
import subprocess
import sys
from functools import partial

import wandb


def run_wandb(keep_output=False):
    with wandb.init() as run:
        value = wandb.config["height_ratio-tilt_angle"]
        height_ratio, tilt_angle = value.split("-")
        height_ratio = float(height_ratio)
        tilt_angle = float(tilt_angle)

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

        if not keep_output:
            shutil.rmtree(subdir)


if __name__ == "__main__":
    if "--" in sys.argv:
        arg_start = sys.argv.index("--") + 1
        argv = sys.argv[arg_start:]
        parser = argparse.ArgumentParser()
        parser.add_argument("-s", "--sweep_id", dest="sweep_id")
        parser.add_argument("-c", "--count", dest="count", type=int)
        parser.add_argument("--keep_output", action=argparse.BooleanOptionalAction)

        args = parser.parse_known_args(argv)[0]
        print("keep_output =", args.keep_output)

        wandb_function = partial(run_wandb, keep_output=args.keep_output)
        wandb.agent(args.sweep_id, project="simfolds_test", function=wandb_function, count=args.count)
