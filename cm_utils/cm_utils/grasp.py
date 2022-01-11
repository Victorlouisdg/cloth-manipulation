import bpy
import numpy as np


def bounding_box(coords):
    coords = np.array(coords)

    x_min = np.min(coords[:, 0])
    y_min = np.min(coords[:, 1])
    z_min = np.min(coords[:, 2])

    x_max = np.max(coords[:, 0])
    y_max = np.max(coords[:, 1])
    z_max = np.max(coords[:, 2])

    return (x_min, y_min, z_min), (x_max, y_max, z_max)


def between(v, min, max):
    return v >= min and v <= max


def check_interval_overlap(a, b, c, d):
    return between(c, a, b) or between(d, a, b) or between(a, c, d) or between(b, c, d)


def check_bb_overlap(bbox0, bbox1):
    min0, max0 = bbox0
    min1, max1 = bbox1

    min0_x, min0_y, min0_z = min0
    max0_x, max0_y, max0_z = max0
    min1_x, min1_y, min1_z = min1
    max1_x, max1_y, max1_z = max1

    x_overlap = check_interval_overlap(min0_x, max0_x, min1_x, max1_x)
    y_overlap = check_interval_overlap(min0_y, max0_y, min1_y, max1_y)
    z_overlap = check_interval_overlap(min0_z, max0_z, min1_z, max1_z)

    return x_overlap and y_overlap and z_overlap


def find_grasped_vertices(obj, gripper):
    gripper_verts = [gripper.matrix_world @ v.co for v in gripper.data.vertices]
    gripper_bb = bounding_box(gripper_verts)

    grasped_vertices = set()

    for p in obj.data.polygons:
        poly_verts = [obj.matrix_world @ obj.data.vertices[id].co for id in p.vertices]
        poly_bb = bounding_box(poly_verts)

        if check_bb_overlap(gripper_bb, poly_bb):
            for id in p.vertices:
                grasped_vertices.add(id)

    return grasped_vertices


def get_grasped_verts_trajectories(obj, gripper, start_frame, end_frame):
    grasped_vertices = find_grasped_vertices(obj, gripper)

    # Make gripper parent to make cloth move with gripper as if it was a rigid body
    obj.parent = gripper
    obj.matrix_parent_inverse = gripper.matrix_world.inverted()

    scene = bpy.context.scene
    dt = 1.0 / scene.render.fps

    trajectories = {id: [] for id in grasped_vertices}
    times = []

    obj_verts = obj.data.vertices

    for i in range(start_frame, end_frame + 1):
        scene.frame_set(i)
        times.append(i * dt)

        for id in grasped_vertices:
            trajectories[id].append(obj.matrix_world @ obj_verts[id].co)

    scene.frame_set(0)

    obj.parent = None
    return trajectories, times


def visualize_trajectories(trajectories):
    collection = bpy.data.collections.new("Trajectories")
    bpy.context.scene.collection.children.link(collection)

    for id, trajectory in trajectories.items():
        vertices = trajectory
        edges = [(i, i + 1) for i in range(len(trajectory) - 1)]
        faces = []
        mesh = bpy.data.meshes.new(f"Trajectory{id}")
        mesh.from_pydata(vertices, edges, faces)
        mesh.update()
        object = bpy.data.objects.new(f"Trajectory{id}", mesh)
        collection.objects.link(object)


def set_trajectory_height(gripper, height):
    action = gripper.animation_data.action
    zcurve = action.fcurves[2]
    z1_key = zcurve.keyframe_points[1]
    z1_key.co[1] = height
    z1_key.handle_left[1] = height
    z1_key.handle_right[1] = height


def calculate_velocities(trajectories, times):
    velocities = {}
    for id, trajectory in trajectories.items():
        velocities[id] = []
        for i in range(len(trajectory) - 1):
            x, x_next = trajectory[i], trajectory[i + 1]
            t, t_next = times[i], times[i + 1]
            dx = x_next - x
            dt = t_next - t
            v = dx / dt
            velocities[id].append(v)
    return velocities


def make_gripper(name):
    """Makes a new Blender object that can serve as gripper.

    Args:
        name (str): name of the object in Blender
    """
    bpy.ops.mesh.primitive_cube_add(size=0.05)
    cube = bpy.context.active_object
    cube.name = name
    return cube


if __name__ == "__main__":
    objects = bpy.data.objects
    cloth = objects["cloth_simple"]
    gripper = objects["gripper"]
    trajectories, _ = get_grasped_verts_trajectories(cloth, gripper)
    visualize_trajectories(trajectories)
