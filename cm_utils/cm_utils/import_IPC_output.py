import glob
import os

import bpy

from cm_utils.keyframe import keyframe_visibility


def import_cipc_output(cipc_output_dir, frame):
    # WARNING: currently assumes ground has 4 verts and was added to cipc scene first

    cloth_color = [0.113616, 0.584227, 1.000000, 1.000000]
    cloth_material = bpy.data.materials.new(name="Cloth")
    cloth_material.diffuse_color = cloth_color
    cloth_material.use_nodes = True
    cloth_bsdf = cloth_material.node_tree.nodes["Principled BSDF"]
    cloth_bsdf.inputs["Base Color"].default_value = cloth_color
    cloth_bsdf.inputs["Roughness"].default_value = 0.9

    # output_dir = "/home/idlab185/Codim-IPC/Projects/FEMShell/output/25_blender_cloth/"

    file = os.path.join(cipc_output_dir, f"shell{frame}.obj")

    sim_collection = bpy.data.collections.new("sim")
    bpy.context.scene.collection.children.link(sim_collection)

    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.import_scene.obj(filepath=file, split_mode="OFF")
    cloth = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = cloth
    bpy.ops.object.transform_apply()

    cloth.name = f"sim{frame}"

    ground_vertices = [0, 1, 2, 3]
    mesh = cloth.data

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for v in mesh.vertices:
        if v.index in ground_vertices:
            v.select = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")

    # Hide the new cloth object on all other frames
    keyframe_visibility(cloth, frame, frame)

    cloth.data.materials[0] = cloth_material
    return cloth


def import_cipc_outputs(cipc_output_dir):
    # WARNING: currently assumes ground has 4 verts and was added to cipc scene first

    cloth_color = [0.113616, 0.584227, 1.000000, 1.000000]
    cloth_material = bpy.data.materials.new(name="Cloth")
    cloth_material.diffuse_color = cloth_color
    cloth_material.use_nodes = True
    cloth_bsdf = cloth_material.node_tree.nodes["Principled BSDF"]
    cloth_bsdf.inputs["Base Color"].default_value = cloth_color
    cloth_bsdf.inputs["Roughness"].default_value = 0.9

    # output_dir = "/home/idlab185/Codim-IPC/Projects/FEMShell/output/25_blender_cloth/"

    shell_glob = os.path.join(cipc_output_dir, "shell*.obj")

    files = glob.glob(shell_glob)
    files.sort()

    sim_collection = bpy.data.collections.new("sim")
    bpy.context.scene.collection.children.link(sim_collection)

    for file in files:
        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.import_scene.obj(filepath=file, split_mode="OFF")
        cloth = bpy.context.selected_objects[0]
        bpy.context.view_layer.objects.active = cloth
        bpy.ops.object.transform_apply()

        num = file.split("shell")[1].split(".obj")[0]

        cloth.name = f"sim{num}"

        ground_vertices = [0, 1, 2, 3]
        mesh = cloth.data

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")
        for v in mesh.vertices:
            if v.index in ground_vertices:
                v.select = True
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.delete(type="VERT")
        bpy.ops.object.mode_set(mode="OBJECT")

        # Hide the new cloth object on all other frames
        keyframe_visibility(cloth, int(num), int(num))

        cloth.data.materials[0] = cloth_material

    scene = bpy.context.scene
    scene.frame_set(scene.frame_start)
    # bpy.context.scene.frame_end = int(num)


# MANUALLY MOVING CLOTH VERTS INTO NEW MESH
# cloth_verts = [v.co for v in mesh.vertices[4:]]
# cloth_edges = []
# cloth_faces = []

# for edge in mesh.edges:
#     edge_verts = [v - 4 for v in edge.vertices]
#     if edge_verts[0] >= 0:
#         cloth_edges.append(edge_verts)

# for poly in mesh.polygons[2:]:
#     poly_verts = [v - 4 for v in poly.vertices]
#     if poly_verts[0] >= 0:
#         cloth_faces.append(poly_verts)

# cloth_mesh = bpy.data.meshes.new("sim_mesh{num}")
# cloth_mesh.from_pydata(cloth_verts, cloth_edges, cloth_faces)
# cloth_mesh.update()
# cloth = bpy.data.objects.new(f"sim{num}", cloth_mesh)
# sim_collection.objects.link(cloth)

# bpy.ops.object.select_all(action="DESELECT")
# obj.select_set(True)
# bpy.ops.object.delete()
