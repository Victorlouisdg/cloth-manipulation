from abc import ABC, abstractmethod

import numpy as np
from airo_blender_toolkit import homogeneous_transform
from scipy.spatial.transform import Rotation, Slerp


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
    def __init__(
        self, reference_pose, center, rotation_axis, start_angle=0, end_angle=360, orientation_mode="rotated"
    ):
        self.reference_start_pose = np.array(reference_pose)
        self.center = np.array(center)
        self.rotation_axis = np.array(rotation_axis)
        self.start_angle = start_angle
        self.end_angle = end_angle

        self.orientation_mode = "rotated"
        self.reference_end_pose = self.pose(1.0)
        self.orientation_mode = orientation_mode

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
        P = self.reference_start_pose.copy()
        P = np.linalg.inv(basis) @ P
        P = rotation_matrix @ P
        P = basis @ P
        pose = P

        if self.orientation_mode == "constant":
            pose[:3, :3] = self.reference_start_pose[:3, :3]
        elif self.orientation_mode == "slerp":
            orientations = Rotation.from_matrix([self.reference_start_pose[:3, :3], self.reference_end_pose[:3, :3]])
            slerp = Slerp([0.0, 1.0], orientations)
            interpolated_orientation = slerp(completion).as_matrix()
            pose[:3, :3] = interpolated_orientation

        return pose


# class TimeParametrizaion:
#     pass


# class EasedArcLength(TimeParametrizaion):
#     pass


# class CartesianTrajectory:
#     """A trajectory is a time parametirzed path."""

#     def __init__(self):
#         pass

#         self.cartsian_path = 0
#         self.time_parametrization = 0

#     def pose(completion=0.5):
#         pass


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
