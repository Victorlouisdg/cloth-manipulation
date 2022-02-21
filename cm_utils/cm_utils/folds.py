from abc import ABC, abstractmethod

import airo_blender_toolkit as abt
import numpy as np

from cm_utils.trajectory import CircularArcPath


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


class CircularArcFoldPath(CircularArcPath):
    def __init__(self, fold):
        self.fold = fold
        print(fold.gripper_start_pose())
        super().__init__(fold.gripper_start_pose(), *fold.fold_line(), end_angle=180)
