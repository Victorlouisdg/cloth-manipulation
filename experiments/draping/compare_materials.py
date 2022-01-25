from cm_utils.dirs import ensure_output_paths
from cm_utils.materials.penava import materials
from cm_utils.cipc_sim import SimulationCIPC

import bpy

objects = bpy.data.objects
cloth_name = "cloth"
cloth = objects[cloth_name]
sphere = objects["sphere"]

cotton = materials[0]

friction_coefficient = 0.4

# SimulationCIPC is an adaptor between Blender and CIPC
paths = ensure_output_paths()

simulation_steps = 50

simulation = SimulationCIPC(paths, 25)
simulation.add_collider(sphere, friction_coefficient)
simulation.add_cloth(cloth, cotton)
simulation.initialize_cipc()
simulation.run(simulation_steps)

cloth.hide_viewport = True
sphere.hide_viewport = True

bpy.context.scene.render.fps = 25
bpy.context.scene.frame_start = 0
bpy.context.scene.frame_end = simulation_steps

bpy.context.scene.frame_set(0)
