import argparse
import json
import os
import subprocess
import sys

import wandb


def run_wandb():
    with wandb.init(project="cloth-manipulation", entity="victorlouis") as run:
        height = wandb.config["height"]

        dir = os.path.dirname(os.path.abspath(__file__))
        wandb_dir = os.path.join(dir, "output", run.name)
        os.makedirs(wandb_dir)

        subdir = os.path.join(wandb_dir, f"height: {height:.4f}")
        os.makedirs(subdir)

        log = {"height": height}

        runCommand = f"blender scene.blend -b -P run_experiment.py -- -ht {height} -d '{subdir}'"
        subprocess.run([runCommand], shell=True, stdout=subprocess.DEVNULL)

        with open(os.path.join(subdir, "losses.json")) as f:
            losses = json.load(f)

        log = log | losses
        wandb.log(log)


if __name__ == "__main__":
    if "--" in sys.argv:
        arg_start = sys.argv.index("--") + 1
        argv = sys.argv[arg_start:]
        parser = argparse.ArgumentParser()
        parser.add_argument("-s", "--sweep_id", dest="sweep_id")
        args = parser.parse_known_args(argv)[0]
        wandb.agent(args.sweep_id, project="cloth-manipulation", function=run_wandb)
