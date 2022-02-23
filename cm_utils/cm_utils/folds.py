from abc import ABC, abstractmethod

import airo_blender_toolkit as abt
import numpy as np

from cm_utils.path import CircularArcPath, EllipticalArcPath, TiltedEllipticalArcPath
from cm_utils.time_parametrization import MinimumJerk
from cm_utils.trajectory import Trajectory


class Fold(ABC):
    """Base class to represent a cloth folding motion.
    A fold is derived from cloth keypoints.
    """

    def __init__(self, keypoints):
        self.keypoints = keypoints

    @abstractmethod
    def fold_line(self):
        pass

    @abstractmethod
    def gripper_start_pose(self):
        pass


class SleeveFold(Fold):
    def __init__(self, keypoints, left_or_right, angle=30):
        self.left_or_right = left_or_right
        self.angle = angle
        super().__init__(keypoints)

    def fold_line(self):
        keypoints = self.keypoints
        left_or_right = self.left_or_right
        angle = self.angle

        armpit = keypoints[f"{left_or_right}_armpit"]
        corner_bottom = keypoints[f"{left_or_right}_corner_bottom"]

        if left_or_right == "left":
            angle = 180 - angle

        angle = np.deg2rad(angle)
        up = np.array([0, 0, 1])

        rotated = abt.rotate_point(corner_bottom, armpit, up, angle)
        line_direction = rotated - armpit
        line_direction /= np.linalg.norm(line_direction)

        point_on_line = armpit

        return point_on_line, line_direction

    def gripper_start_pose(self):
        keypoints = self.keypoints
        left_or_right = self.left_or_right

        sleeve_top = keypoints[f"{left_or_right}_sleeve_top"]
        sleeve_bottom = keypoints[f"{left_or_right}_sleeve_bottom"]
        shoulder = keypoints[f"{left_or_right}_shoulder"]
        armpit = keypoints[f"{left_or_right}_armpit"]
        sleeve_middle = (sleeve_top + sleeve_bottom) / 2
        shoulder_middle = (shoulder + armpit) / 2

        up = np.array([0, 0, 1])
        X = up
        Z = shoulder_middle - sleeve_middle
        Z /= np.linalg.norm(Z)
        Y = np.cross(Z, X)

        start_pose = abt.homogeneous_transform(X, Y, Z, sleeve_middle)
        return start_pose


class CircularArcFoldTrajectory(Trajectory):
    def __init__(self, fold, end_angle=170, orientation_mode="rotated"):
        path = CircularArcPath(
            fold.gripper_start_pose(), *fold.fold_line(), end_angle=end_angle, orientation_mode=orientation_mode
        )
        super().__init__(path, MinimumJerk())


class EllipticalArcFoldTrajectory(Trajectory):
    def __init__(self, fold, end_angle=170, orientation_mode="rotated"):
        path = EllipticalArcPath(
            fold.gripper_start_pose(), *fold.fold_line(), end_angle=end_angle, orientation_mode=orientation_mode
        )
        super().__init__(path, MinimumJerk())


class TiltedEllipticalArcFoldTrajectory(Trajectory):
    def __init__(self, fold, end_angle=170, orientation_mode="rotated", tilt_angle=30):
        path = TiltedEllipticalArcPath(
            fold.gripper_start_pose(),
            *fold.fold_line(),
            end_angle=end_angle,
            orientation_mode=orientation_mode,
            tilt_angle=tilt_angle,
        )
        super().__init__(path, MinimumJerk())
