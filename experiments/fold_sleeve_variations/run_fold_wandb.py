import argparse
import json
import os
import shutil
import subprocess
import sys
from functools import partial

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


def run_wandb(script, keep_output=False):
    with wandb.init() as run:
        height_ratio, tilt_angle = parse_parameters(run)
        output_dir = make_output_dir(run.name, height_ratio, tilt_angle)

        runCommand = f"blender -b -P {script} -- -ht {height_ratio} -ta {tilt_angle} -d '{output_dir}' -cm 0 -sh 2"
        subprocess.run([runCommand], shell=True, stdout=subprocess.DEVNULL)

        log_results(height_ratio, tilt_angle, output_dir)

        if not keep_output:
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    if "--" in sys.argv:
        arg_start = sys.argv.index("--") + 1
        argv = sys.argv[arg_start:]
        parser = argparse.ArgumentParser()
        parser.add_argument("script", help="The python script of the experiment.")
        parser.add_argument("project", help="The project on wandb to log to.")
        parser.add_argument("sweep_id")
        parser.add_argument("-c", "--count", dest="count", type=int, help="Amount of runs for the wandb agent.")
        parser.add_argument(
            "--keep_output",
            action=argparse.BooleanOptionalAction,
            help="If not set all simulation output will be removed after the run to save memory.",
        )
        args = parser.parse_known_args(argv)[0]
        wandb_function = partial(run_wandb, script=args.script, keep_output=args.keep_output)
        wandb.agent(args.sweep_id, project=args.project, function=wandb_function, count=args.count)
