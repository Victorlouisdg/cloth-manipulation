import os
import sys

sys.path.append(os.path.dirname(__file__))

from cm_utils.materials.penava import materials
from simulate_drape import run_drape_simulation

for material in materials:
    run_drape_simulation(
        sphere_radius=0.1, cloth_size=0.45, cloth_subdivisions=8, cloth_material=material, simulation_steps=25
    )
