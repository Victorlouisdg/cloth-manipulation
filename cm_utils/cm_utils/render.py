import os
import bpy
import subprocess


def render(renders_dir, resolution_percentage=100):
    scene = bpy.context.scene
    scene.render.resolution_percentage = resolution_percentage
    scene.render.filepath = (
        renders_dir if renders_dir[-1] == os.sep else renders_dir + os.sep
    )

    bpy.ops.render.render(animation=True)

    # Encode video
    command = (
        f'ffmpeg -y -hide_banner -loglevel error -nostats -framerate 25 -i "{renders_dir}/%04d.png" "{renders_dir}/video.mp4"'
    )
    subprocess.run([command], shell=True, stdout=subprocess.DEVNULL)
