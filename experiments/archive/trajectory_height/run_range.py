import json
import os
import subprocess

import numpy as np
import wandb

height_min = 0.2
height_max = 0.6
steps = 40

run = wandb.init(project="cloth-manipulation", entity="victorlouis")
wandb.config = {"height_min": height_min, "height_max": height_max, "steps": steps}

dir = os.path.dirname(os.path.abspath(__file__))
wandb_dir = os.path.join(dir, "output", run.name)
os.makedirs(wandb_dir)

height_range = np.linspace(height_min, height_max, steps)

for height in height_range:
    subdir = os.path.join(wandb_dir, f"height: {height:.4f}")
    os.makedirs(subdir)

    log = {"height": height}

    runCommand = f"blender scene.blend -b -P run_experiment.py -- -ht {height} -d '{subdir}'"
    subprocess.run([runCommand], shell=True, stdout=subprocess.DEVNULL)

    with open(os.path.join(subdir, "losses.json")) as f:
        losses = json.load(f)

    log = log | losses
    wandb.log(log)

run.finish()
