# cloth-manipulation
Cloth manipulation through simulation with C-IPC

## Installation
* Clone this repo.
* Clone [C-IPC](https://github.com/ipc-sim/Codim-IPC), install it's dependencies and build.
* Download [blender](https://www.blender.org/download/), all recent versions should work.
* add this to .bashrc `export PATH="$PATH:/home/idlab185/Blender/blender-2.93.3-linux-x64/"`


## Running an experiment
SET trajectory_height=0.3
`blender --python experiments/trajectory_height/run.py --background`
or
`cd experiments/trajectory_height`
`blender -b -P run.py -- -ht 0.25`

## Experiment flow
* Model piece of cloth in blender.
* Export as obj.
* Animate "base" path blender.
* Choose certain parameter values for base path and export as velocity trajectories.
* Execute these trajectories with C-IPC.
* Calculate losses of the final result.