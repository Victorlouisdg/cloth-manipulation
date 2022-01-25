#import sys

import sys
import os

from cm_utils.dirs import ensure_output_paths

CIPC_PATH = "../../Codim-IPC"
CIPC_PYTHON_PATH = os.path.join(CIPC_PATH, "Python")
CIPC_BUILD_PATH = os.path.join(CIPC_PATH, "build")


sys.path.insert(0, CIPC_PYTHON_PATH)
sys.path.insert(0, CIPC_BUILD_PATH)

#sys.path.insert(0, "../../Python")
import Drivers
from JGSL import *
import numpy as np
import json

def to_Vector3d(v):
    return Vector3d(v[0], v[1], v[2])


if __name__ == "__main__":

    paths = ensure_output_paths()


    sim = Drivers.FEMDiscreteShellBase("double", 3, paths["cipc"])

    # Ground plane
    sim.add_shell_3D(
        "/home/idlab185/cloth-manipulation/experiments/draping/ground.obj",
        Vector3d(0, 0, 0),
        Vector3d(0, 0, 0),
        Vector3d(0, 1, 0),
        0,
    )

    # Cloth
    sim.add_shell_3D(
        "/home/idlab185/cloth-manipulation/experiments/draping/cloth.obj",
        Vector3d(0, 0, 0),
        Vector3d(0, 0, 0),
        Vector3d(0, 1, 0),
        0,
    )

    algI = 0
    clothI = 0
    membEMult = 0.01
    bendEMult = 0.1
    sim.mu = 0.4
    sim.muComp = StdVectorXd([0, 0, sim.mu, 0, 0, sim.mu, sim.mu, sim.mu, 0.1])

    sim.dt = 0.04
    sim.frame_dt = 0.04
    sim.frame_num = 100
    sim.withCollision = True

    # density, E, nu, thickness, initial displacement case
    # iso
    sim.initialize(
        sim.cloth_density_iso[clothI],
        sim.cloth_Ebase_iso[clothI] * membEMult,
        sim.cloth_nubase_iso[clothI],
        sim.cloth_thickness_iso[clothI],
        0,
    )
    sim.bendingStiffMult = bendEMult / membEMult
    sim.kappa_s = Vector2d(1e3, 0)
    sim.s = Vector2d(sim.cloth_SL_iso[clothI], 0)

    sim.initialize_OIPC(1e-3, 0)

    x_min = Vector3d(-10, -10, -10)
    x_max = Vector3d(10, 10, 10)
    bbox = x_min, x_max
    v0 = Vector3d(0, 0, 0)
    rotation = (Vector3d(0, 0, 0), Vector3d(0, 1, 0), 0)

    vIndRangeGround = Vector4i(0, 0, 4, -1)

    ground_DBC = (
        x_min,
        x_max,
        Vector3d(0, 0, 0),
        Vector3d(0, 0, 0),
        Vector3d(0, 1, 0),
        0,
        vIndRangeGround,
    )


    sim.write(0)
    for f in range(sim.frame_num):
        # Reset DBCs
        sim.DBC = Storage.V4dStorage()
        sim.DBCMotion = Storage.V2iV3dV3dV3dSdStorage()

        # Ground plane DBC
        #sim.set_DBC_with_range(*ground_DBC)

        # Setting w too doesn't change anything.
        # w = to_Vector3d(waypoints[f + 1])
        # sim.set_DBC_with_range(w, w, v, *rotation, vIndRange)

        # Advance
        sim.current_frame = f + 1
        sim.advance_one_frame(f + 1)
        sim.write(f + 1)

        if Get_Parameter("Terminate", False):
            break