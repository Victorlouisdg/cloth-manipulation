import airo_blender_toolkit as abt
import blenderproc as bproc
import bpy
import numpy as np
import scipy.spatial.transform as transform
from airo_blender_toolkit.keypointed_object import KeypointedObject


def transformation_matrix_from_position_and_vecs(pos, x, y, z):
    transformation_matrix = np.eye(4)
    transformation_matrix[:3, 0] = x
    transformation_matrix[:3, 1] = y
    transformation_matrix[:3, 2] = z
    transformation_matrix[:3, 3] = pos
    return transformation_matrix


class TowelFold:
    def __init__(self, kp1, kp2, kp3, kp4) -> None:
        # cloth is assumed to be below robot.
        # kp1 is most to the left of the "upper" two
        # others are clockwise

        self.cloth_position = (kp1 + kp2 + kp3 + kp4) / 4
        self.x = ((kp2 - kp1) + (kp3 - kp4)) / 2  # average the two vectors to cope w/ slight non-rectangular cloth
        self.len = np.linalg.norm(self.x)
        self.x /= self.len
        self.z = np.array([0, 0, 1])

        self.y = np.cross(self.z, self.x)
        self.robot_to_cloth_base_transform = transformation_matrix_from_position_and_vecs(
            self.cloth_position, self.x, self.y, self.z
        )

    def fold_pose_in_cloth_frame(self, t):
        assert t <= 1 and t >= 0
        angle = np.pi - t * np.pi
        position = np.array([self.len / 2.0 * np.cos(angle), 0, self.len / 2.5 * np.sin(angle)])

        position[2] += 0.085 / 2 * np.sin(np.pi / 4) - 0.01
        # offset for open gripper
        orientation_angle = -5 * np.pi / 4 + t * np.pi / 4
        x = np.array([np.cos(orientation_angle), 0, np.sin(orientation_angle)])
        x /= np.linalg.norm(x)
        y = np.array([0, 1, 0])

        z = np.cross(x, y)
        return transformation_matrix_from_position_and_vecs(position, x, y, z)

    def pregrasp_pose_in_cloth_frame(self, alpha):
        grasp_pose = self.fold_pose_in_cloth_frame(0)
        pregrasp_pose = grasp_pose
        pregrasp_pose[0, 3] = pregrasp_pose[0, 3] - alpha

        return pregrasp_pose

    @staticmethod
    def pose_to_rotvec_waypoint(pose):
        position = pose[:3, 3]
        rpy = transform.Rotation.from_matrix(pose[:3, :3]).as_rotvec()
        return np.concatenate((position, rpy))


class Towel(KeypointedObject):
    def __init__(self):
        bpy.ops.mesh.primitive_plane_add(size=0.5)

        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                override = bpy.context.copy()
                override["area"] = area
                bpy.ops.transform.rotate(override, value=0.7, orient_axis="Z", orient_type="GLOBAL")
                bpy.ops.object.transform_apply(override, location=True, rotation=True, scale=True)
        self.blender_object = bpy.context.active_object

        keypoint_ids = {
            "corner": [0, 1, 2, 3],
        }

        super().__init__(self.blender_object, keypoint_ids)


bproc.init()
towel = Towel()
towel.visualize_keypoints()

keypoints = towel.keypoints_3D["corner"]

keypoints = [np.array(keypoint) for keypoint in keypoints]
print(keypoints)


towel_fold = TowelFold(keypoints[2], keypoints[3], keypoints[1], keypoints[0])

pregrasp_in_towel = towel_fold.pregrasp_pose_in_cloth_frame(0.05)
pregrasp = towel_fold.robot_to_cloth_base_transform @ pregrasp_in_towel

print(pregrasp)

abt.visualize_transform(towel_fold.robot_to_cloth_base_transform)

abt.visualize_transform(pregrasp)

abt.visualize_line([0, 0, 0], towel_fold.x)

num_waypoints = 8
for t in range(0, num_waypoints + 1):
    i = t / num_waypoints
    wp = towel_fold.robot_to_cloth_base_transform @ towel_fold.fold_pose_in_cloth_frame(i)
    abt.visualize_transform(wp, scale=0.05)
