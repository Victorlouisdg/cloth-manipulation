import bpy
import json
import os

fps = 25
n_sim_frames = 100

scene = bpy.context.scene
scene.frame_start = 0
scene.frame_end = n_sim_frames
scene.render.fps = 25

obj = bpy.data.objects['Cone']

locations = []
times = []

dt = 1.0 / fps

for i in range(n_sim_frames + 1):
    scene.frame_set(i)
    locations.append(obj.location.copy())
    times.append(dt * i) 
    
scene.frame_set(0)

print(len(locations))

output_dir = "/home/idlab185/"

locations_json = []

for loc in locations:
    locations_json.append({
        "x": loc.x,
        "y": loc.y,
        "z": loc.z,
    })

velocities_json = []

for i in range(n_sim_frames):
    delta = locations[i + 1] - locations[i]
    velocities_json.append({
        "x": delta.x / dt,
        "y": delta.y / dt,
        "z": delta.z / dt,
    })


waypoints = {
    "locations": locations_json,
    "velocities": velocities_json,
    "times": times
}

waypoints_json = {"waypoints": waypoints}

with open(os.path.join(output_dir, "waypoints_vel.json"), "w") as f:
    json.dump(waypoints_json, f, indent=2)