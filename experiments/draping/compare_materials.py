from cm_utils.dirs import ensure_output_paths
import bpy
from cm_utils.material_properties import materials_penava
from cm_utils.cipc_sim import SimulationCIPC

objects = bpy.data.objects
cloth_name = "cloth"
cloth = objects[cloth_name]
sphere = objects["sphere"]

materials = materials_penava

cotton = materials["cotton"]

friction_coefficient = 0.4

# SimulationCIPC is an adaptor between Blender and CIPC

paths = ensure_output_paths()

simulation = SimulationCIPC(paths, 25)
simulation.add_collider(sphere, friction_coefficient)
simulation.add_cloth(cloth, cotton)

simulation.initialize_cipc()

simulation.step({})
