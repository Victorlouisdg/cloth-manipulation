class Material:
    def __init__(self, name, youngs_modulus, poissons_ratio, density_planar, thickness):
        """[summary]

        Args:
            name (string): name of the material
            youngs_modulus (float): Young's modulus of the material in Pascal
            poissons_ratio (float): Poisson's ratio of the material, dimensionless, usually between 0 and 0.5
            density_planar (float): Weight of the fabric in kg/m^2
            thickness (float): Fabric thickness in meters
        """
        self.name = name
        self.youngs_modulus = youngs_modulus
        self.poissons_ratio = poissons_ratio
        self.density_planar = density_planar
        self.thickness = thickness

    @property
    def density_volumetric(self):
        """[summary]

        Returns:
            float: Volumetric density of the material in kg/m^3
        """
        return self.density_planar / self.thickness
