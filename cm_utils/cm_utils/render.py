import os
import bpy
import subprocess


def render(renders_dir):
    scene = bpy.context.scene
    scene.render.resolution_percentage = 50
    scene.render.filepath = (
        renders_dir if renders_dir[-1] == os.sep else renders_dir + os.sep
    )

    bpy.ops.render.render(animation=True)

    # Encode video
    command = (
        f'ffmpeg -y -framerate 25 -i "{renders_dir}/%04d.png" "{renders_dir}/video.mp4"'
    )
    subprocess.call([command], shell=True)
