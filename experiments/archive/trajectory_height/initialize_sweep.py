import pprint

import wandb

sweep_config = {
    "project": "cloth-manipulation",
    "entity": "victorlouis",
    "name": "my-sweep",
    "method": "random",
    "metric": {"goal": "minimize", "name": "mean_distance"},
    "parameters": {"height": {"min": 0.2, "max": 0.6}},
}

sweep_id = wandb.sweep(sweep_config)
print(sweep_id)
pprint.pprint(sweep_config)
