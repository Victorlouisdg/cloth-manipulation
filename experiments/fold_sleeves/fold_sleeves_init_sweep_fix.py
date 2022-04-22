import pprint

import wandb

# Missing values from previous sweep
values = [
    "0.6538461538461539-30.0",
    "0.6538461538461539-36.0",
    "0.6538461538461539-42.0",
    "0.7923076923076923-46.15384615384615",
]

sweep_name = "sweep0_fix"
project = "simfolds_20k_bigger"

sweep_config = {
    "entity": "victorlouis",
    "name": sweep_name,
    "method": "grid",
    "metric": {"goal": "minimize", "name": "mean_distance"},
    "parameters": {
        "height_ratio-tilt_angle": {"values": values},
    },
    "project": project,
}

sweep_id = wandb.sweep(sweep_config, project=sweep_config["project"])
print(sweep_id)
print("Combinations:", len(values))
pprint.pprint(sweep_config)
print(sweep_id)
