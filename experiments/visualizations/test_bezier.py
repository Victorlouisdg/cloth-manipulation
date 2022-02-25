import airo_blender_toolkit as abt
import numpy as np
from airo_blender_toolkit.path import BezierPath
from scipy.spatial.transform import Rotation

P0 = np.array([0.0, 0.0, 0.0])
P1 = np.array([0.5, 1.0, 1.0])
P2 = np.array([1.0, 0.0, 0.0])

control_ponits = [P0, P1, P2]

start_orientation = np.identity(3)
end_orientation = Rotation.from_rotvec(np.array([0, 180, 0]), degrees=True).as_matrix()

path = BezierPath(control_ponits, start_orientation, end_orientation)

for t in np.linspace(0, 1, 100):
    pose = path.pose(t)
    abt.visualize_transform(pose, 0.05)


P0 = np.array([0.0, 0.0, 0.0])
P1 = np.array([0.0, 2.0, 0.5])
P2 = np.array([1.0, 0.0, 1.0])
P3 = np.array([1.0, 0.0, 0.0])

control_ponits = [P0, P1, P2, P3]


path = BezierPath(control_ponits, start_orientation, end_orientation)

for t in np.linspace(0, 1, 100):
    pose = path.pose(t)
    abt.visualize_transform(pose, 0.05)
