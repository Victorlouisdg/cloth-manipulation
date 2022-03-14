import airo_blender_toolkit as abt
import numpy as np
from airo_blender_toolkit.path import BezierPath
from scipy.spatial.transform import Rotation

P0 = np.array([0.0, 0.0, 0.0])
P1 = np.array([0.5, 0.0, 1.0])
P2 = np.array([1.0, 0.0, 0.0])

control_ponits0 = [P0, P1, P2]

start_orientation = np.identity(3)
end_orientation = Rotation.from_rotvec(np.array([0, 180, 0]), degrees=True).as_matrix()

tilt_angle = 60
angle = np.deg2rad(90 - tilt_angle)
P1_alt = np.array([0.5, np.cos(angle), np.sin(angle)])
control_ponits1 = [P0, P1_alt, P2]

path0 = BezierPath(control_ponits0, start_orientation, end_orientation)
path1 = BezierPath(control_ponits1, start_orientation, end_orientation)

for t in np.linspace(0, 1, 100):
    pose0 = path0.pose(t)
    pose1 = path1.pose(t)
    abt.visualize_transform(pose0, 0.05)
    abt.visualize_transform(pose1, 0.05)
