import os
import bpy
import subprocess


def render(renders_dir):
    # for obj in bpy.data.objects:
    #     obj.select_set(False)

    # for obj in bpy.data.objects:
    #     if obj.name.startswith("Cube"):
    #         obj.select_set(True)

    # bpy.ops.object.delete()

    # bpy.data.objects["Camera"].location = (1.5, -1.5, 1.2)
    # bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = [
    #     0.5,
    #     0.5,
    #     0.5,
    #     1.0,
    # ]

    scene = bpy.context.scene
    scene.render.resolution_percentage = 25

    # scene.render.engine = "CYCLES"
    # scene.render.image_settings.file_format = "PNG"
    # scene.render.image_settings.color_mode = "RGB"
    # scene.render.resolution_x = 1024
    # scene.render.resolution_y = 1024
    scene.render.filepath = renders_dir if renders_dir[-1] == os.sep else renders_dir + os.sep
    # scene.cycles.samples = 128

    bpy.ops.render.render(animation=True)

    # Encode video
    command = (
        f'ffmpeg -y -framerate 25 -i "{renders_dir}/%04d.png" "{renders_dir}/video.mp4"'
    )
    subprocess.call([command], shell=True)