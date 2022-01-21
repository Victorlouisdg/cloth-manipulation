import sys
import os

CIPC_PATH = "../../Codim-IPC"
CIPC_PYTHON_PATH = os.path.join(CIPC_PATH, "Python")
CIPC_BUILD_PATH = os.path.join(CIPC_PATH, "build")

sys.path.insert(0, CIPC_PYTHON_PATH)
sys.path.insert(0, CIPC_BUILD_PATH)

from JGSL import *
from cm_utils import export_as_obj

translation0 = Vector3d(0, 0, 0)
scale1 = Vector3d(1, 1, 1)
rotation_center0 = Vector3d(0, 0, 0)
rotation_axis1 = Vector3d(0, 1, 0)
rotation_angle0 = 0  # degrees

identity_transform = (
    translation0,
    scale1,
    rotation_center0,
    rotation_axis1,
    rotation_angle0,
)


class SimulationCIPC:
    def __init__(self, paths, fps):
        self.paths = paths

        self.output_folder = paths["cipc"]

        Kokkos_Initialize()

        self.fps = fps
        self.timestep_size = 1.0 / fps

        # Coordinates of the vertices
        self.vertex_coordinates = Storage.V3dStorage()
        self.vertex_coordinates_original = Storage.V3dStorage()

        # Triangles
        self.triangles = Storage.V3iStorage()

        # Line Segments = used for hair simulation
        self.line_segments = StdVectorVector2i()

        # List of with at index i, the sum of the number of vertices
        # of the ith object and all object added before it.
        # This is used to differentiate between added object,
        # because coordinates etc. are stored contiguously.
        self.vertex_counts_cumulative = StdVectorXi()

        self.elasticity = FIXED_COROTATED_2.Create()
        self.gravity = Vector3d(0, -9.81, 0)

        # Initialized by Initialize_Discrete_Shell
        # map from each edge to its corresponding triangle(s)?
        self.edge_to_triangle = StdMapPairiToi()
        # Contains a hinge edge + the two other vertices affected by the hinge
        self.hinges = StdVectorVector4i()
        self.edge_info = (
            StdVectorVector3d()
        )  # dihedral angle, edge length, sometinhg with normals
        self.node_attributes = (
            Storage.V3dV3dV3dSdStorage()
        )  # x0, v, g, mass, see DATA_TYPE.h
        self.mass_matrix = CSR_MATRIX_D()
        self.body_force = StdVectorXd()
        self.triangle_attributes = Storage.M2dM2dSdStorage()  # IB, P
        self.kappa = Vector3d(1e5, 0, 0)  # not sure what this variable is for

        # Additional CIPC_attributes

        # Stitches
        self.stitch_info = StdVectorVector3i()
        self.stitch_ratio = StdVectorXd()
        self.stitch_stiffness = 10

        # Rods
        self.rod = StdVectorVector2i()
        self.rod_info = StdVectorVector3d()
        self.rod_hinge = StdVectorVector3i()
        self.rod_hinge_info = StdVectorVector3d()

        self.tetrahedra = Storage.V4iStorage()
        self.tetrahedron_attributes = Storage.M3dM3dSdStorage()
        self.tetrahedron_elasticity = FIXED_COROTATED_3.Create()

        # Point particles
        self.discrete_particle = StdVectorXi()

        # Random CIPC stuff, some of these should be material properties
        self.bendingStiffMult = 1
        self.fiberStiffMult = Vector4d(0, 0, 0, 0)
        self.inextLimit = Vector3d(0, 0, 0)
        # Strain limiting: 1.01 means max 1% stretching, but why 2d?
        self.strain_limit = Vector2d(1.01, 0)
        self.sHat = Vector2d(1, 1)
        self.kappa_s = Vector2d(0, 0)
        self.friction_iterations = 1
        self.friction_coefficient = 0  # todo set with cloth material?
        self.muComp = StdVectorXd()  # list of mus?
        self.DBC = Storage.V4dStorage()

        # Solver settings
        self.projected_newton_tolerance = 1e-3
        self.static_solve = False
        self.epsv2 = 1e-6  # not sure what this is

        self.cipc_initialized = False

        self.enable_collisions = True

        self.cloths = []
        self.materials_cloth = {}

    def add_cloth(self, cloth, material):
        if self.cipc_initialized:
            print("WARNING: you cannot add objects after the simulation has started.")
            return

        self.cloths.append(cloth)
        self.materials_cloth[cloth] = material
        self._add_shell(cloth)

    def add_collider(self, object, friction_coefficient):
        if self.cipc_initialized:
            print("WARNING: you cannot add objects after the simulation has started.")
            return

        self._add_shell(object)
        # TODO make collider static
        # TODO bookkeeping for actuation and import

    def _add_shell(self, object):
        file_path = export_as_obj(object, self.paths["run"])
        # TODO read object transform, ignored for now
        counter = FEM.DiscreteShell.Add_Shell(
            file_path,
            *identity_transform,
            self.vertex_coordinates,
            self.triangles,
            self.vertex_counts_cumulative,
        )

    def initialize_cipc(self):
        MeshIO.Append_Attribute(
            self.vertex_coordinates, self.vertex_coordinates_original
        )  # not sure if this is needed

        cloth = self.cloths[0]
        material_cloth = self.materials_cloth[cloth]
        thickness = material_cloth["thickness"]

        # dHat2 == thickness_elastic_squared = thickness ** 2

        self.thickness_elastic_squared = FEM.DiscreteShell.Initialize_Shell_Hinge_EIPC(
            material_cloth["density_volumetric"],
            material_cloth["youngs_modulus"],
            material_cloth["poissons_ratio"],
            thickness,
            self.timestep_size,
            0.0,  # this input seems to be unused?
            self.vertex_coordinates,
            self.triangles,
            self.line_segments,
            self.edge_to_triangle,
            self.hinges,
            self.edge_info,
            self.node_attributes,
            self.mass_matrix,
            self.gravity,
            self.body_force,
            self.triangle_attributes,
            self.elasticity,
            self.kappa,
        )

        self.cipc_initialized = True

    def step(self, action):
        if not self.cipc_initialized:
            self.initialize_cipc()

        cloth = self.cloths[0]
        material_cloth = self.materials_cloth[cloth]
        thickness = material_cloth["thickness"]

        FEM.DiscreteShell.Advance_One_Step_IE_Hinge(
            self.triangles,
            self.line_segments,
            self.DBC,
            self.edge_to_triangle,
            self.hinges,
            self.edge_info,
            thickness,
            self.bendingStiffMult,
            self.fiberStiffMult,
            self.inextLimit,  # also called fiberLimit
            self.strain_limit,
            self.sHat,
            self.kappa_s,
            self.body_force,
            self.timestep_size,
            self.projected_newton_tolerance,
            self.enable_collisions,
            self.thickness_elastic_squared,
            self.kappa,
            self.friction_coefficient,
            self.epsv2,
            self.friction_iterations,
            self.vertex_counts_cumulative,
            self.muComp,
            self.static_solve,
            self.vertex_coordinates,
            self.node_attributes,
            self.mass_matrix,
            self.triangle_attributes,
            self.elasticity,
            self.tetrahedra,
            self.tetrahedron_attributes,
            self.tetrahedron_elasticity,
            self.rod,
            self.rod_info,
            self.rod_hinge,
            self.rod_hinge_info,
            self.stitch_info,
            self.stitch_ratio,
            self.stitch_stiffness,
            self.discrete_particle,
            self.output_folder,
        )
