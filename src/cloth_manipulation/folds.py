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


class SleeveFold(Fold):
    def __init__(self, keypoints, side, angle=30):
        self.side = side
        self.angle = angle
        super().__init__(keypoints)

    def fold_line(self):
        keypoints = self.keypoints
        side = self.side
        angle = self.angle

        armpit = keypoints[f"armpit_{side}"]
        corner_bottom = keypoints[f"bottom_{side}"]

        if side == "left":
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
        side = self.side

        sleeve_top = keypoints[f"sleeve_top_{side}"]
        sleeve_bottom = keypoints[f"sleeve_bottom_{side}"]
        shoulder = keypoints[f"shoulder_{side}"]
        armpit = keypoints[f"armpit_{side}"]
        sleeve_middle = (sleeve_top + sleeve_bottom) / 2
        shoulder_middle = (shoulder + armpit) / 2

        up = np.array([0, 0, 1])
        X = up
        Z = shoulder_middle - sleeve_middle
        Z /= np.linalg.norm(Z)
        Y = np.cross(Z, X)

        start_pose = abt.Frame.from_vectors(X, Y, Z, sleeve_middle)

        return start_pose


class SideFold(Fold):
    def __init__(self, keypoints, side, gripper_positioning="top"):
        self.side = side
        self.gripper_positioning = gripper_positioning
        super().__init__(keypoints)

    def fold_line(self):
        keypoints = self.keypoints
        side = self.side

        armpit_left = keypoints["armpit_left"]
        keypoints["shoulder_left"]
        bottom_left = keypoints["bottom_left"]
        armpit_right = keypoints["armpit_right"]
        keypoints["shoulder_right"]
        bottom_right = keypoints["bottom_right"]

        if side == "left":
            line_direction = (armpit_left - bottom_left).normalized()
            point_on_line = 0.75 * bottom_left + 0.25 * bottom_right
        else:
            line_direction = (bottom_right - armpit_right).normalized()
            point_on_line = 0.25 * bottom_left + 0.75 * bottom_right

        line_direction /= np.linalg.norm(line_direction)

        return point_on_line, line_direction

    def gripper_start_pose(self):
        keypoints = self.keypoints
        side = self.side
        gripper_positioning = self.gripper_positioning

        armpit_left = keypoints["armpit_left"]
        bottom_left = keypoints["bottom_left"]
        armpit_right = keypoints["armpit_right"]
        bottom_right = keypoints["bottom_right"]

        armpit = armpit_left if side == "left" else armpit_right
        bottom = bottom_left if side == "left" else bottom_right

        left_to_right = (armpit_right - armpit_left).normalized()
        right_to_left = (armpit_left - armpit_right).normalized()

        gripper_translation = armpit if gripper_positioning == "top" else bottom

        up = np.array([0, 0, 1])
        X = up
        Z = left_to_right if side == "left" else right_to_left
        Z /= np.linalg.norm(Z)
        Y = np.cross(Z, X)

        start_pose = abt.Frame.from_vectors(X, Y, Z, gripper_translation)

        return start_pose


class MiddleFold(Fold):
    def __init__(self, keypoints, side, angle=30):
        self.side = side
        super().__init__(keypoints)

    def fold_line(self):
        keypoints = self.keypoints

        shoulder_left = keypoints["shoulder_left"]
        bottom_left = keypoints["bottom_left"]
        shoulder_right = keypoints["shoulder_right"]
        bottom_right = keypoints["bottom_right"]

        middle_left = 0.5 * shoulder_left + 0.5 * bottom_left
        middle_right = 0.5 * shoulder_right + 0.5 * bottom_right

        right_to_left = (middle_left - middle_right).normalized()

        line_direction = right_to_left
        line_direction /= np.linalg.norm(line_direction)

        point_on_line = middle_left

        return point_on_line, line_direction

    def gripper_start_pose(self):
        keypoints = self.keypoints
        side = self.side

        # # TODO
        armpit_left = keypoints["armpit_left"]
        bottom_left = keypoints["bottom_left"]
        armpit_right = keypoints["armpit_right"]
        bottom_right = keypoints["bottom_right"]

        if side == "left":
            gripper_translation = 0.75 * bottom_left + 0.25 * bottom_right
            bottom_to_top = (armpit_left - bottom_left).normalized()
        else:
            gripper_translation = 0.25 * bottom_left + 0.75 * bottom_right
            bottom_to_top = (armpit_right - bottom_right).normalized()

        up = np.array([0, 0, 1])
        X = up
        Z = bottom_to_top
        Y = np.cross(Z, X)

        start_pose = abt.Frame.from_vectors(X, Y, Z, gripper_translation)

        return start_pose


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
    def __init__(self, fold, height_ratio=1.0, tilt_angle=0, end_height=0.05, end_angle=170):
        start_pose = fold.gripper_start_pose()

        # Mimic end pose of circular arc
        ciruclar_trajectory = EllipticalFoldTrajectory(fold, end_angle=end_angle)
        end_pose = ciruclar_trajectory.path.end
        if end_height is not None:
            end_pose.position[2] = end_height

        start_position = start_pose.position
        end_position = end_pose.position

        mid_position = abt.project_point_on_line(start_position, *fold.fold_line())
        start_to_mid = start_position - mid_position
        start_to_fold_line_distance = np.linalg.norm(start_to_mid)

        # Note that we do not halve this distance, because the curve will lie
        # halfway between the control point and the ground
        raised_mid_position = mid_position.copy()
        raised_mid_position[2] += height_ratio * start_to_fold_line_distance * 2

        start_to_end = end_position - start_position

        tilted_mid_position = abt.rotate_point(
            raised_mid_position, start_position, start_to_end, np.deg2rad(tilt_angle)
        )

        control_points = [start_position, tilted_mid_position, end_position]

        # TODO: consider allowing control points to be full poses and interpolation orienation
        path = BezierPath(control_points, start_pose.orientation, end_pose.orientation)
        super().__init__(path, MinimumJerk())
