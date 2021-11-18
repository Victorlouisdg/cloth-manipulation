"""Trajectory Height experiment.

   This file will take as input a height and return a loss value.

   1) Export the objs and trajectory.
   2) Setup and run IPC
   3) Import first IPC output and last back into blender.
   4) Calculate loss.
"""

import sys
import argparse
from cm_utils import test


def run(height):
    print("Running Trajectory Height experiment with height: ", height)

# CIPC_PATH = /home/Codim-IPC/

if __name__ == "__main__":
    test.test_print()

    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--') + 1:]
        parser = argparse.ArgumentParser()
        parser.add_argument('ht', 'height', dest='height', type=float)
        args = parser.parse_known_args(argv)[0]
        print('height: ', args.height)
        height = args.height

        run(height)



