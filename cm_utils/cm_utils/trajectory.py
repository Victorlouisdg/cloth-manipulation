from abc import ABC, abstractmethod

import numpy as np
from scipy.spatial.transform import Rotation


def homogeneous_transform(x_column, y_column, z_column, translation):
    matrix = np.identity(4)
    matrix[0:3, 0] = x_column
    matrix[0:3, 1] = y_column
    matrix[0:3, 2] = z_column
    matrix[0:3, 3] = translation
    return matrix


class CartesianPath(ABC):
    @abstractmethod
    def pose(self, completion):
        pass

    @property
    def start_pose(self):
        return self.pose(0.0)

    @property
    def end_pose(self):
        return self.pose(1.0)


class CircularArcPath(CartesianPath):
    def __init__(self, reference_pose, center, rotation_axis, start_angle=0, end_angle=360):
        self.reference_pose = np.array(reference_pose)
        self.center = np.array(center)
        self.rotation_axis = np.array(rotation_axis)
        self.start_angle = start_angle
        self.end_angle = end_angle
        # TODO add option rotate_orientation

    def _rotation_basis(self):
        X = self.rotation_axis
        # random Y and Z orthogonal to X to complete the basis
        Y = np.random.randn(3)
        Y -= Y.dot(X) * X  # remove component parallel to X
        Y /= np.linalg.norm(Y)
        Z = np.cross(X, Y)
        return homogeneous_transform(X, Y, Z, self.center)

    def pose(self, completion):
        rotation_angle = self.start_angle + completion * (self.end_angle - self.start_angle)
        basis = self._rotation_basis()
        rotation_matrix = np.identity(4)
        rotation_matrix[:3, :3] = Rotation.from_rotvec([rotation_angle, 0, 0], degrees=True).as_matrix()
        P = self.reference_pose.copy()
        P = np.linalg.inv(basis) @ P
        P = rotation_matrix @ P
        P = basis @ P
        pose = P
        # if not rotate_orientation: set 3x3 back to start_pose
        return pose


class TimeParametrizaion:
    pass


class EasedArcLength(TimeParametrizaion):
    pass


class CartesianTrajectory:
    """A trajectory is a time parametirzed path."""

    def __init__(self):
        pass

        self.cartsian_path = 0
        self.time_parametrization = 0

    def pose(completion=0.5):
        pass


# class EasedCircleTrajectory():
#     def __init__(self):
#         pass

#         self.cartsian_path = CirclePath()
#         self.path_timing = 0

# class EasedArcLengthTrajectory(CartesianTrajectory):
#     def __init__(self, path):
#         self.path = path

#     def get_pose(trajectory_completion=0.5):
#         pass
