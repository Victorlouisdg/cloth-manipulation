import sys
import os

CIPC_PATH = "/home/idlab185/Codim-IPC"
CIPC_PYTHON_PATH = os.path.join(CIPC_PATH, "Python")
CIPC_BUILD_PATH = os.path.join(CIPC_PATH, "build")

sys.path.insert(0, CIPC_PYTHON_PATH)
sys.path.insert(0, CIPC_BUILD_PATH)

from JGSL import *
import Drivers


import numpy as np
import json

def to_Vector3d(v):
    return Vector3d(v[0], v[1], v[2])


def simulate(cloth_path, ground_path, output_dir, waypoints=None):
    sim = Drivers.FEMDiscreteShellBase("double", 3, output_dir)


    # Ground plane
    sim.add_shell_3D(
        ground_path,
        Vector3d(0, 0, 0),
        Vector3d(0, 0, 0),
        Vector3d(0, 1, 0),
        0,
    )

    # Cloth
    sim.add_shell_3D(
        cloth_path,
        Vector3d(0, 0.01, 0),
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
    vIndRange = Vector4i(4, 0, 5, -1)

    vIndRange2 = Vector4i(61, 0, 62, -1)  # vertex 57

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

    velocities = []

    with open("/home/idlab185/waypoints_vel.json") as json_file:
        data = json.load(json_file)
        for vel in data["waypoints"]["velocities"]:
            velocities.append(Vector3d(vel["x"], vel["z"], vel["y"]))


    sim.write(0)
    for f in range(sim.frame_num):
        # Reset DBCs
        sim.DBC = Storage.V4dStorage()
        sim.DBCMotion = Storage.V2iV3dV3dV3dSdStorage()

        # Ground plane DBC
        sim.set_DBC_with_range(*ground_DBC)

        # Trajectory DBC
        v = velocities[f]
        # v = to_Vector3d(v)
        sim.set_DBC_with_range(x_min, x_max, v, *rotation, vIndRange)
        sim.set_DBC_with_range(x_min, x_max, v, *rotation, vIndRange2)


        # Setting w too doesn't change anything.
        # w = to_Vector3d(waypoints[f + 1])
        # sim.set_DBC_with_range(w, w, v, *rotation, vIndRange)

        # Advance
        sim.current_frame = f + 1
        sim.advance_one_frame(f + 1)
        sim.write(f + 1)

        if Get_Parameter("Terminate", False):
            break
