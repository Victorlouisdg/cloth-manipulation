from abc import ABC, abstractmethod

import airo_blender_toolkit as abt
import bpy
import numpy as np
from airo_blender_toolkit.path import BezierPath, TiltedEllipticalArcPath
from airo_blender_toolkit.time_parametrization import MinimumJerk
from airo_blender_toolkit.trajectory import Trajectory
from mathutils import Matrix


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

        start_pose = abt.Frame.from_vectors(X, Y, Z, sleeve_middle)

        return start_pose

    def make_target_mesh(self, cloth, cloth_thickness=0.001):
        cloth_folded = cloth.copy()
        cloth_folded.data = cloth.data.copy()
        bpy.context.collection.objects.link(cloth_folded)
        cloth_folded.name = f"{cloth.name} Target"

        origin, X = self.fold_line()
        Z = np.array([0.0, 0.0, 1.0])
        Y = np.cross(Z, X)
        basis = abt.Frame.from_vectors(X, Y, Z, origin)
        basis_inv = Matrix(np.linalg.inv(basis))
        basis = Matrix(basis)

        for v in cloth_folded.data.vertices:
            co = v.co
            co = basis_inv @ co

            if co.y >= 0.0:
                co.y *= -1
                co.z += cloth_thickness
                co = basis @ co
                v.co = co

        return cloth_folded


class EllipticalFoldTrajectory(Trajectory):
    def __init__(self, fold, end_angle=170, scale=1.0, tilt_angle=0, orientation_mode="rotated"):
        path = TiltedEllipticalArcPath(
            fold.gripper_start_pose(),
            *fold.fold_line(),
            end_angle=end_angle,
            scale=scale,
            tilt_angle=tilt_angle,
            orientation_mode=orientation_mode,
        )
        super().__init__(path, MinimumJerk())


class BezierFoldTrajectory(Trajectory):
    def __init__(self, fold, height_ratio=1.0, tilt_angle=0, early_stop=0.95):
        start_pose = fold.gripper_start_pose()

        # Mimic end pose of circular arc
        ciruclar_trajectory = EllipticalFoldTrajectory(fold, end_angle=170)
        end_pose = ciruclar_trajectory.path.end

        start_position = start_pose.position
        end_position = end_pose.position

        mid_position = abt.project_point_on_line(start_position, *fold.fold_line())
        start_to_mid = start_position - mid_position
        start_to_fold_line_distance = np.linalg.norm(start_to_mid)

        # Note that we do not halve this distance, because the curve will lie
        # halfway between the control point and the ground
        raised_mid_position = mid_position.copy()
        raised_mid_position[2] = height_ratio * start_to_fold_line_distance * 2

        start_to_end = end_position - start_position

        tilted_mid_position = abt.rotate_point(
            raised_mid_position, start_position, start_to_end, np.deg2rad(tilt_angle)
        )

        control_points = [start_position, tilted_mid_position, end_position]

        # TODO: consider allowing control points to be full poses and interpolation orienation
        path = BezierPath(control_points, start_pose.orientation, end_pose.orientation)
        super().__init__(path, MinimumJerk())
