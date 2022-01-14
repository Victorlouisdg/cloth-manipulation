import sys
import os

CIPC_PATH = "../../Codim-IPC"
CIPC_PYTHON_PATH = os.path.join(CIPC_PATH, "Python")
CIPC_BUILD_PATH = os.path.join(CIPC_PATH, "build")

sys.path.insert(0, CIPC_PYTHON_PATH)
sys.path.insert(0, CIPC_BUILD_PATH)

from JGSL import *
import Drivers

import bpy


def cipc_action(gripper, cloth, grasped, frame):
    scene = bpy.context.scene
    scene.frame_set(frame)

    positions = {}
    for id in grasped:
        positions[id] = cloth.matrix_world @ cloth.data.vertices[id].co

    cloth.parent = gripper
    cloth.matrix_parent_inverse = gripper.matrix_world.inverted()

    # gripper_pose = gripper.matrix_world.copy()
    # scene.frame_set(frame + 1)
    # gripper_pose_next = gripper.matrix_world.copy()
    # transform = gripper_pose_next @ gripper_pose.inverted()
    # matrix_world_new = transform @ cloth.matrix_world
    # positions_next = {}
    # for id in grasped:
    #     positions_next[id] = matrix_world_new @ cloth.data.vertices[id].co

    scene.frame_set(frame + 1)
    positions_next = {}
    for id in grasped:
        positions_next[id] = cloth.matrix_world @ cloth.data.vertices[id].co
    cloth.parent = None

    velocities = {}
    dt = 1.0 / scene.render.fps

    for id in grasped:
        p = positions[id]
        p_next = positions_next[id]
        v = (p_next - p) / dt
        velocities[id] = v

    return velocities


def to_Vector3d(v):
    return Vector3d(v[0], v[2], -v[1])


class Simulation:
    def __init__(self, cloth_path, ground_path, output_dir):
        sim = Drivers.FEMDiscreteShellBase("double", 3, output_dir)

        self.sim = sim

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
            Vector3d(0, 0, 0),
            Vector3d(0, 0, 0),
            Vector3d(0, 1, 0),
            0,
        )

        algI = 0  # isotropic
        clothI = 0  # cotton
        membEMult = 0.01
        bendEMult = 0.1
        sim.mu = 0.4
        sim.muComp = StdVectorXd([0, 0, sim.mu, 0, 0, sim.mu, sim.mu, sim.mu, 0.1])

        sim.dt = 0.04
        sim.frame_dt = 0.04
        sim.frame_num = 100
        sim.withCollision = True

        # density, E, nu, thickness, initial displacement case
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

        self.x_min = Vector3d(-10, -10, -10)
        self.x_max = Vector3d(10, 10, 10)
        self.rotation = (Vector3d(0, 0, 0), Vector3d(0, 1, 0), 0)

        vIndRangeGround = Vector4i(0, 0, 4, -1)

        self.ground_DBC = (
            self.x_min,
            self.x_max,
            Vector3d(0, 0, 0),
            Vector3d(0, 0, 0),
            Vector3d(0, 1, 0),
            0,
            vIndRangeGround,
        )

        sim.write(0)

    def step(self, action={}):
        """Advance the C-IPC simulation a single frame.

        Args:
            action (dict): dictionary with keys the vertex ids and values the vertex velcoties
        """
        sim = self.sim
        controlled_vertices = action.keys()

        # Reset DBCs
        sim.DBC = Storage.V4dStorage()
        sim.DBCMotion = Storage.V2iV3dV3dV3dSdStorage()

        # Ground plane DBC
        sim.set_DBC_with_range(*self.ground_DBC)

        for id in controlled_vertices:
            v = to_Vector3d(action[id])
            vIndRange = Vector4i(4 + id, 0, 5 + id, -1)
            sim.set_DBC_with_range(self.x_min, self.x_max, v, *self.rotation, vIndRange)

        # Advance
        sim.current_frame += 1
        sim.advance_one_frame(sim.current_frame)
        sim.write(sim.current_frame)
