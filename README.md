# cloth-manipulation
Cloth manipulation through simulation with C-IPC

## Installation
* Clone this repo.
* Clone [C-IPC](https://github.com/ipc-sim/Codim-IPC), install it's dependencies and build.
* Download [blender](https://www.blender.org/download/), all recent versions should work.
* add this to .bashrc `export PATH="$PATH:/home/<name>/Blender/blender-3.0.0-linux-x64/"`


## Running an experiment
`cd experiments/trajectory_height`
`blender scene.blend -b -P run_experiment.py -- -ht 0.25`

## Experiment flow
* Model piece of cloth in blender.
* Export as obj.
* Animate "base" path blender.
* Choose certain parameter values for base path and export as velocity trajectories.
* Execute these trajectories with C-IPC.
* Calculate losses of the final result.

## CIPC build
Build with blender python. `sudo apt install libpython3.9-dev` if `Python.h` not found.
```
~/Blender/blender-3.0.0-linux-x64/3.0/python/bin/python3.9 build.py
```
Not sure if it is strictly necessary to use the Blender python to call `build.py` itself.


```python
import subprocess

# https://stackoverflow.com/questions/15291500/i-have-2-versions-of-python-installed-but-cmake-is-using-older-version-how-do

BLENDER_PYTHON = "~/Blender/blender-3.0.0-linux-x64/3.0/python/bin/python3.9"
PYTHON_LIBS = "/usr/lib/libpython3.9.so"
INCLUDE_DIRS ="/usr/include/python3.9/"

runCommand = f'mkdir build\ncd build\nrm -rf CMakeCache.txt\ncmake -DCMAKE_BUILD_TYPE=Release -DPYTHON_EXECUTABLE:FILEPATH={BLENDER_PYTHON} -DPYTHON_LIBRARIES={PYTHON_LIBS} -DPYTHON_INCLUDE_DIRS={INCLUDE_DIRS} ..\nmake -j 15'
subprocess.call([runCommand], shell=True)
```

If build fails due to tests, go to `build/partio-src/CMakeLists.txt` and comment `ADD_SUBDIRECTORY (src/tests)`
