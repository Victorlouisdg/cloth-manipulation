from scipy.spatial.transform import Slerp, Rotation
from cm_utils.geometry import update_4x4_with_3x3


def keyframe_locations(object, poses):
    for frame, pose in poses.items():
        object.matrix_world = pose
        object.keyframe_insert(data_path="location", frame=frame)


def keyframe_orientations(object, poses):
    # Keyframing the orientation of the object in all frames
    key_rots = Rotation.from_matrix([pose.to_3x3() for pose in poses.values()])
    key_times = list(poses.keys())
    slerp = Slerp(key_times, key_rots)

    for i in range(key_times[0], key_times[-1] + 1):
        update_4x4_with_3x3(object.matrix_world, slerp(i).as_matrix())
        object.keyframe_insert(data_path="rotation_euler", frame=i)


def keyframe_visibility(object, start_frame, end_frame):
    object.hide_render = True
    object.hide_viewport = True
    object.keyframe_insert(data_path="hide_render", frame=max(0, start_frame - 1))
    object.keyframe_insert(data_path="hide_viewport", frame=max(0, start_frame - 1))
    object.hide_render = False
    object.hide_viewport = False
    object.keyframe_insert(data_path="hide_render", frame=start_frame)
    object.keyframe_insert(data_path="hide_viewport", frame=start_frame)
    object.keyframe_insert(data_path="hide_render", frame=end_frame)
    object.keyframe_insert(data_path="hide_viewport", frame=end_frame)
    object.hide_render = True
    object.hide_viewport = True
    object.keyframe_insert(data_path="hide_render", frame=end_frame + 1)
    object.keyframe_insert(data_path="hide_viewport", frame=end_frame + 1)
