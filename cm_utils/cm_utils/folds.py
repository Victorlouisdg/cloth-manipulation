from cm_utils.keyframe import (
    keyframe_locations,
    keyframe_orientations,
    keyframe_visibility,
)
import numpy as np
from mathutils import Vector, Matrix
import bpy
from abc import ABC, abstractmethod
from cm_utils.geometry import rotate_point, vectors_to_matrix_4x4


class Fold(ABC):
    """Base class to represent a cloth folding motion.
    A fold is derived from cloth keypoints and two simple parameters.

    Each child class has to overwrite two important functions:
    1) get_fold_basis()
    2) get_gripper_start_pose()
    """

    def __init__(self, keypoints, height_ratio, offset_ratio):
        self.keypoints = keypoints
        self.height_ratio = height_ratio
        self.offset_ratio = offset_ratio

        self.fold_basis = self.get_fold_basis()
        self.gripper_start_pose = self.get_gripper_start_pose()
        self.gripper_end_pose = Fold.get_gripper_end_pose(
            self.gripper_start_pose, self.fold_basis
        )
        self.gripper_middle_pose = Fold.get_gripper_middle_pose(
            self.gripper_start_pose,
            self.gripper_end_pose,
            self.fold_basis,
            self.height_ratio,
            self.offset_ratio,
        )

    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def get_fold_basis(self):
        """Get the fold basis for this fold.
        The x-axis of the basis should point along the fold line.
        The translation of the basis should point to a point on the fold line.
        The basis is later utilized to get the gripper end pose by 180 degree rotation around the x-axis.
        """
        pass

    @abstractmethod
    def get_gripper_start_pose(self):
        pass

    @staticmethod
    def get_gripper_end_pose(start_pose, fold_basis):
        M = start_pose
        M = fold_basis.inverted() @ M
        M = Matrix.Rotation(np.deg2rad(180), 4, "X") @ M
        M = fold_basis @ M
        end_pose = M
        end_pose.col[3][2] = 0.05
        return end_pose

    @staticmethod
    def get_gripper_middle_pose(
        start_pose, end_pose, fold_basis, height_ratio, offset_ratio
    ):
        start_position = start_pose.translation
        end_position = end_pose.translation
        start_to_end_distance = (start_position - end_position).length

        M = start_pose
        M = fold_basis.inverted() @ M
        M = Matrix.Rotation(np.deg2rad(90), 4, "X") @ M
        M = Matrix.Translation((offset_ratio * start_to_end_distance, 0, 0)) @ M
        M = fold_basis @ M
        middle_pose = M
        middle_pose.col[3][2] = height_ratio * start_to_end_distance
        return middle_pose

    def make_gripper(self):
        """Makes a new Blender object that can serve as gripper.

        Args:
            name (str): name of the object in Blender
        """
        bpy.ops.mesh.primitive_cube_add(size=0.05)
        cube = bpy.context.active_object
        cube.name = f"gripper_{self.name()}"
        return cube

    def make_keyframed_gripper(self, start_frame, end_frame):
        gripper = self.make_gripper()

        middle_frame = (start_frame + end_frame) // 2
        poses = {
            start_frame: self.gripper_start_pose,
            middle_frame: self.gripper_middle_pose,
            end_frame: self.gripper_end_pose,
        }

        keyframe_locations(gripper, poses)
        keyframe_orientations(gripper, poses)
        keyframe_visibility(gripper, start_frame, end_frame)

        gripper.matrix_world = self.gripper_start_pose
        return gripper

    def make_folded_cloth_target(self, cloth):
        fold_basis = self.fold_basis

        cloth_folded = cloth.copy()
        cloth_folded.data = cloth.data.copy()
        bpy.context.collection.objects.link(cloth_folded)
        cloth_folded.name = f"cloth_target_{self.name()}"

        for v in cloth_folded.data.vertices:
            co = v.co
            co = fold_basis.inverted() @ co

            if co.y >= 0.0:
                co.y *= -1
                co.z += 0.001
                co = fold_basis @ co
                v.co = co

        return cloth_folded


class SleeveFold(Fold):
    def __init__(self, keypoints, height_ratio, offset_ratio, left_or_right, angle=30):
        self.left_or_right = left_or_right
        self.angle = angle
        super().__init__(keypoints, height_ratio, offset_ratio)

    def name(self):
        return f"{self.left_or_right}_sleeve_fold"

    def get_fold_basis(self):
        keypoints = self.keypoints
        left_or_right = self.left_or_right
        angle = self.angle

        armpit = keypoints[f"{left_or_right}_armpit"]
        corner_bottom = keypoints[f"{left_or_right}_corner_bottom"]

        if left_or_right == "left":
            angle = 180 - angle

        angle = np.deg2rad(angle)
        up = Vector([0, 0, 1])

        rotated = Vector(rotate_point(corner_bottom, armpit, up, angle))
        vector_along_fold = (rotated - armpit).normalized()

        basis_X = vector_along_fold
        basis_Z = up
        basis_Y = basis_Z.cross(basis_X)
        new_basis = vectors_to_matrix_4x4(basis_X, basis_Y, basis_Z, armpit)
        return new_basis

    def get_gripper_start_pose(self):
        keypoints = self.keypoints
        left_or_right = self.left_or_right

        sleeve_top = keypoints[f"{left_or_right}_sleeve_top"]
        sleeve_bottom = keypoints[f"{left_or_right}_sleeve_bottom"]
        shoulder = keypoints[f"{left_or_right}_shoulder"]
        armpit = keypoints[f"{left_or_right}_armpit"]
        sleeve_middle = (sleeve_top + sleeve_bottom) / 2
        shoulder_middle = (shoulder + armpit) / 2

        up = Vector([0, 0, 1])

        gripper_translation = sleeve_middle.to_4d()
        gripper_X = (shoulder_middle - sleeve_middle).normalized()
        gripper_Z = up
        gripper_Y = gripper_Z.cross(gripper_X)

        start_pose = vectors_to_matrix_4x4(
            gripper_X, gripper_Y, gripper_Z, gripper_translation
        )
        return start_pose
