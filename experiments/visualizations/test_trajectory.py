import airo_blender_toolkit as abt
import numpy as np

from cm_utils.trajectory import CircularArcPath

path = CircularArcPath(np.identity(4), [1, 0, 0], [0, 1, 0], end_angle=180)

for completion in np.linspace(0, 1, 10):
    pose = path.pose(completion)
    abt.visualize_transform(pose, 0.1)
