# Fabric thickness in meters, from Penava et al. [2014], Table 1, row 6
thicknesses_penava = {
    "cotton": 0.318e-3,
    "wool": 0.568e-3,
    "wool_lycra": 0.328e-3,
    "polyester": 0.252e-3,
}

# Fabric weight in kg/m^2, from Penava et al. [2014], Table 1, row 5
density_planar_penava = {
    "cotton": 0.1503,
    "wool": 0.2348,
    "wool_lycra": 0.1782,
    "polyester": 0.1646,
}

# Penava et al. [2014], Table 3, combination of row 4 and 7
youngs_modulus_penava = {
    "cotton": 0.318e-3,  # Pascal
    "wool": 0.568e-3,
    "wool_lycra": 0.328e-3,
    "polyester": 0.252e-3,
}

# dimensionless, usually between 0 and 0.5
poissons_ratio_penava = {
    "cotton": 0.243,
    "wool": 0.277,
    "wool_lycra": 0.071,
    "polyester": 0.381,
}


def make_material_penava(material_name):
    thickness = thicknesses_penava[material_name]
    density_planar = density_planar_penava[material_name]
    density_volumetric = density_planar / thickness

    material = {
        "thickness": thickness,
        "density_planar": density_planar,
        "density_volumetric": density_volumetric,
        "youngs_modulus": youngs_modulus_penava[material_name],
        "poissons_ratio": poissons_ratio_penava[material_name],
    }
    return material


material_names_penava = ["cotton", "wool", "wool_lycra", "polyester"]
materials_penava = {name: make_material_penava(name) for name in material_names_penava}
