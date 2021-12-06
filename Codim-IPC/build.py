import subprocess

# https://stackoverflow.com/questions/15291500/i-have-2-versions-of-python-installed-but-cmake-is-using-older-version-how-do

BLENDER_PYTHON = "~/Blender/blender-2.93.3-linux-x64/2.93/python/bin/python3.9"
PYTHON_LIBS = "/usr/lib/libpython3.9.so"
INCLUDE_DIRS ="/usr/include/python3.9/"

runCommand = f'mkdir build\ncd build\nrm -rf CMakeCache.txt\ncmake -DCMAKE_BUILD_TYPE=Release -DPYTHON_EXECUTABLE:FILEPATH={BLENDER_PYTHON} -DPYTHON_LIBRARIES={PYTHON_LIBS} -DPYTHON_INCLUDE_DIRS={INCLUDE_DIRS} ..\nmake -j 15'
subprocess.call([runCommand], shell=True)