import pprint

import numpy as np
import wandb

values = []

for height_ratio in np.linspace(0.1, 1.0, 14):
    for angle in np.linspace(30.0, 90.0, max(2, int(18 * height_ratio))):
        tilt_angle = 90.0 - angle
        values.append(f"{height_ratio}-{tilt_angle}")


sweep_config = {
    "entity": "victorlouis",
    "name": "sweep0",
    "method": "grid",
    "metric": {"goal": "minimize", "name": "mean_distance"},
    "parameters": {
        "height_ratio-tilt_angle": {"values": values},
    },
    "project": "fold_sleeve_default_1s",
}

sweep_id = wandb.sweep(sweep_config, project=sweep_config["project"])
print(sweep_id)
print("Combinations:", len(values))
pprint.pprint(sweep_config)
print(sweep_id)
