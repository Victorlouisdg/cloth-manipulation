import bpy
import glob
import os
import subprocess


cloth_color = [0.113616, 0.584227, 1.000000, 1.000000]
cloth_material = bpy.data.materials.new(name="Cloth")
cloth_material.diffuse_color = cloth_color
cloth_material.use_nodes = True
cloth_bsdf = cloth_material.node_tree.nodes["Principled BSDF"]
cloth_bsdf.inputs["Base Color"].default_value = cloth_color
cloth_bsdf.inputs["Roughness"].default_value = 0.9

output_dir = "/home/idlab185/Codim-IPC/Projects/FEMShell/output/25_blender_cloth/"

files = glob.glob(output_dir + "shell*.obj")
files.sort()

for file in files:
    bpy.ops.import_scene.obj(filepath=file)
    obj = bpy.context.selected_objects[0]

    num = file.split("shell")[1].split(".obj")[0]

    obj.hide_render = True
    obj.keyframe_insert(data_path="hide_render", frame=1)
    obj.hide_render = False
    obj.keyframe_insert(data_path="hide_render", frame=int(num) + 1)
    obj.hide_render = True
    obj.keyframe_insert(data_path="hide_render", frame=int(num) + 2)

    # Separate ground and cloth
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    ground_vertices = [0, 1, 2, 3]
    mesh = obj.data
    bpy.ops.object.mode_set(mode="OBJECT")
    for v in mesh.vertices:
        if v.index in ground_vertices:
            v.select = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.separate(type="SELECTED")
    bpy.ops.object.mode_set(mode="OBJECT")

    cloth = bpy.data.objects[f"shell{num}"]
    ground = bpy.data.objects[f"shell{num}.001"]

    cloth.data.materials[0] = cloth_material


bpy.context.scene.frame_end = int(num) + 1

# Rendering

for obj in bpy.data.objects:
    obj.select_set(False)

for obj in bpy.data.objects:
    if obj.name.startswith("Cube"):
        obj.select_set(True)

bpy.ops.object.delete()

bpy.data.objects["Camera"].location = (1.5, -1.5, 1.2)
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = [
    0.5,
    0.5,
    0.5,
    1.0,
]

renders_dir = os.path.join(output_dir, "renders/")

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.filepath = renders_dir
scene.cycles.samples = 128


bpy.ops.render.render(animation=True)

# Encode video
command = f"ffmpeg -y -framerate 24 -i {renders_dir}/%04d.png {output_dir}/video.mp4"
subprocess.call([command], shell=True)
