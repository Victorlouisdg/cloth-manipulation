import os
import subprocess

import bpy


def render(renders_dir, resolution_percentage=100):
    scene = bpy.context.scene
    scene.render.resolution_percentage = resolution_percentage
    scene.render.filepath = renders_dir if renders_dir[-1] == os.sep else renders_dir + os.sep

    bpy.ops.render.render(animation=True)


def encode_video(renders_dir, video_path):
    ffmpeg_args = "-y -hide_banner -loglevel error -nostats -framerate 25"
    command = f'ffmpeg {ffmpeg_args} -i "{renders_dir}/%04d.png" "{video_path}"'
    subprocess.run([command], shell=True, stdout=subprocess.DEVNULL)
