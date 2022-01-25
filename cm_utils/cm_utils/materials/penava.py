from .material import Material

# Material from Penava et al. [2014]
# The Young's moduli are from Table 3, a combination of row 4 and 7
# The Poisson's ratio's are from TODO
# The planar densities are from Table 1, row 5
# The fabric thicknesses are from Table 1, row 6

cotton = Material(
    name="Cotton Penava",
    youngs_modulus=0.821e6,
    poissons_ratio=0.243,
    density_planar=0.1503,
    thickness=0.318e-3,
)

wool = Material(
    name="Wool Penava",
    youngs_modulus=0.170e6,
    poissons_ratio=0.277,
    density_planar=0.2348,
    thickness=0.568e-3,
)

wool_lycra = Material(
    name="Wool+Lycra Penava",
    youngs_modulus=0.076e6,
    poissons_ratio=0.071,
    density_planar=0.1782,
    thickness=0.328e-3,
)

polyester = Material(
    name="Polyester Penava",
    youngs_modulus=0.478e6,
    poissons_ratio=0.381,
    density_planar=0.1646,
    thickness=0.252e-3,
)

materials = [cotton, wool, wool_lycra, polyester]
