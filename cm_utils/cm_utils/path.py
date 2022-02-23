from abc import ABC, abstractmethod

import numpy as np
from airo_blender_toolkit import homogeneous_transform
from scipy.spatial.transform import Rotation, Slerp


class CartesianPath(ABC):
    @abstractmethod
    def pose(self, path_completion):
        pass

    @property
    def start(self):
        return self.pose(0.0)

    @property
    def end(self):
        return self.pose(1.0)

    def arc_length(self, segments=1000):
        total = 0.0
        for i in range(segments):
            p0 = self.pose(float(i) / segments)
            p1 = self.pose(float(i + 1) / segments)
            total += np.linalg.norm(p1 - p0)
        return total

    def check_arc_length_parametrization(self, segments=10):
        arc_length = self.arc_length(segments)
        total = 0.0
        print("Completion | Arc Length")
        for i in range(segments):
            p0 = self.pose(float(i) / segments)
            p1 = self.pose(float(i + 1) / segments)
            total += np.linalg.norm(p1 - p0)
            print(f"{float(i + 1) / segments:.3f} {total / arc_length:.3f}")


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
        X /= np.linalg.norm(X)

        start_position = self.reference_start_pose[0:3, 3].T
        center_to_start = start_position - self.center
        origin = self.center + np.dot(center_to_start, X) * X

        Y = start_position - origin
        Y /= np.linalg.norm(Y)
        Z = np.cross(X, Y)

        return homogeneous_transform(X, Y, Z, origin)

    def pose(self, path_completion=0.5):
        """Get a pose along the path at a given completion.

        Args:
            completion (float): fractional distance along the path

        Returns:
            np.ndarray: a 4x4 matrix that describes a 3D pose
        """
        angle = self.start_angle + path_completion * (self.end_angle - self.start_angle)
        basis = self._rotation_basis()
        rotation_matrix = np.identity(4)
        rotation_matrix[:3, :3] = Rotation.from_rotvec([angle, 0, 0], degrees=True).as_matrix()
        P = self.reference_start_pose.copy()
        P = np.linalg.inv(basis) @ P
        P = rotation_matrix @ P
        P = basis @ P
        pose = P

        if self.orientation_mode == "constant":
            pose[:3, :3] = self.reference_start_pose[:3, :3]
        elif self.orientation_mode == "slerp":
            # TODO remove, SLERP is same as default for circular arc
            orientations = Rotation.from_matrix([self.reference_start_pose[:3, :3], self.reference_end_pose[:3, :3]])
            slerp = Slerp([0.0, 1.0], orientations)
            interpolated_orientation = slerp(path_completion).as_matrix()
            pose[:3, :3] = interpolated_orientation
        return pose


class EllipticalArcPath(CircularArcPath):
    def __init__(
        self,
        reference_pose,
        center,
        rotation_axis,
        scale=0.5,
        start_angle=0,
        end_angle=360,
        orientation_mode="rotated",
    ):
        self.scale = scale
        super().__init__(reference_pose, center, rotation_axis, start_angle, end_angle, orientation_mode)

    def pose(self, path_completion=0.5):
        """Get a pose along the path at a given completion.

        Args:
            completion (float): fractional distance along the path

        Returns:
            np.ndarray: a 4x4 matrix that describes a 3D pose
        """
        angle = self.start_angle + path_completion * (self.end_angle - self.start_angle)
        basis = self._rotation_basis()

        rotation_matrix = np.identity(4)
        rotation_matrix[:3, :3] = Rotation.from_rotvec([angle, 0, 0], degrees=True).as_matrix()

        scale_matrix = np.identity(4)
        scale_matrix[2, 2] = self.scale

        P = self.reference_start_pose.copy()
        P = np.linalg.inv(basis) @ P
        P = rotation_matrix @ P
        P = scale_matrix @ P
        # print(self.scale)
        # P[2, 3] *= self.scale
        P = basis @ P
        pose = P

        if self.orientation_mode == "constant":
            pose[:3, :3] = self.reference_start_pose[:3, :3]
        elif self.orientation_mode == "slerp":
            # TODO remove, SLERP is same as default for circular arc
            orientations = Rotation.from_matrix([self.reference_start_pose[:3, :3], self.reference_end_pose[:3, :3]])
            slerp = Slerp([0.0, 1.0], orientations)
            interpolated_orientation = slerp(path_completion).as_matrix()
            pose[:3, :3] = interpolated_orientation
        return pose


class TiltedEllipticalArcPath(CircularArcPath):
    def __init__(
        self,
        reference_pose,
        center,
        rotation_axis,
        scale=0.5,
        start_angle=0,
        end_angle=360,
        orientation_mode="rotated",
        tilt_angle=30,
    ):
        self.scale = scale
        self.tilt_angle = tilt_angle
        super().__init__(reference_pose, center, rotation_axis, start_angle, end_angle, orientation_mode)

    def pose(self, path_completion=0.5):
        """Get a pose along the path at a given completion.

        Args:
            completion (float): fractional distance along the path

        Returns:
            np.ndarray: a 4x4 matrix that describes a 3D pose
        """
        angle = self.start_angle + path_completion * (self.end_angle - self.start_angle)
        basis = self._rotation_basis()

        rotation_matrix = np.identity(4)
        rotation_matrix[:3, :3] = Rotation.from_rotvec([angle, 0, 0], degrees=True).as_matrix()

        scale_matrix = np.identity(4)
        scale_matrix[2, 2] = self.scale

        tilt_matrix = np.identity(4)
        tilt_matrix[:3, :3] = Rotation.from_rotvec(np.array([0, self.tilt_angle, 0]), degrees=True).as_matrix()

        P = self.reference_start_pose.copy()
        P = np.linalg.inv(basis) @ P
        P = rotation_matrix @ P
        P = scale_matrix @ P
        P[:, 3] = tilt_matrix @ P[:, 3]
        P = basis @ P
        pose = P

        if self.orientation_mode == "constant":
            pose[:3, :3] = self.reference_start_pose[:3, :3]
        elif self.orientation_mode == "slerp":
            # TODO remove, SLERP is same as default for circular arc
            orientations = Rotation.from_matrix([self.reference_start_pose[:3, :3], self.reference_end_pose[:3, :3]])
            slerp = Slerp([0.0, 1.0], orientations)
            interpolated_orientation = slerp(path_completion).as_matrix()
            pose[:3, :3] = interpolated_orientation
        return pose
