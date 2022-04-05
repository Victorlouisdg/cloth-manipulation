import pprint

import numpy as np
import wandb

values = []

for height_ratio in np.linspace(0.3, 1.0, 5):
    for angle in np.linspace(30.0, 90.0, int(7 * height_ratio)):
        tilt_angle = 90.0 - angle
        values.append(f"{height_ratio}-{tilt_angle}")

sweep_config = {
    "entity": "victorlouis",
    "name": "my-sweep",
    "method": "grid",
    "metric": {"goal": "minimize", "name": "mean_distance"},
    "parameters": {
        "height_ratio-tilt_angle": {"values": values},
    },
    "project": "simfolds_20k",
}

sweep_id = wandb.sweep(sweep_config, project=sweep_config["project"])
print(sweep_id)
pprint.pprint(sweep_config)
