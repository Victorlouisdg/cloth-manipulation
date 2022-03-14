import os
import sys

from cloth_manipulation.materials.material import Material

CIPC_PATH = "../../Codim-IPC"
CIPC_PYTHON_PATH = os.path.join(CIPC_PATH, "Python")
CIPC_BUILD_PATH = os.path.join(CIPC_PATH, "build")

sys.path.insert(0, CIPC_PYTHON_PATH)
sys.path.insert(0, CIPC_BUILD_PATH)

import bpy
from airo_blender_toolkit.keyframe import keyframe_visibility
from JGSL import (
    CSR_MATRIX_D,
    FEM,
    FIXED_COROTATED_2,
    FIXED_COROTATED_3,
    TIMER_FLUSH,
    Kokkos_Initialize,
    MeshIO,
    StdMapPairiToi,
    StdVectorVector2i,
    StdVectorVector3d,
    StdVectorVector3i,
    StdVectorVector4i,
    StdVectorXd,
    StdVectorXi,
    Storage,
    Vector2d,
    Vector3d,
    Vector4d,
    Vector4i,
)

from cloth_manipulation import export_as_obj

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


def to_Vector3d(v):
    return Vector3d(v[0], v[2], -v[1])


class SimulationCIPC:
    def __init__(self, filepaths, frames_per_second):
        self.filepaths = filepaths

        self.output_folder = filepaths["cipc"]

        self.blender_objects_input = []
        self.blender_objects_output = {}

        Kokkos_Initialize()

        self.current_frame = 0
        self.frames_per_second = frames_per_second
        self.timestep_size = 1.0 / frames_per_second
        bpy.context.scene.render.fps = frames_per_second

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
        self.vertex_index_ranges = []

        self.elasticity = FIXED_COROTATED_2.Create()
        self.gravity = Vector3d(0, -9.81, 0)

        # Initialized by Initialize_Discrete_Shell
        # map from each edge to its corresponding triangle(s)?
        self.edge_to_triangle = StdMapPairiToi()
        # Contains a hinge edge + the two other vertices affected by the hinge
        self.hinges = StdVectorVector4i()
        self.edge_info = StdVectorVector3d()  # dihedral angle, edge length, sometinhg with normals
        self.node_attributes = Storage.V3dV3dV3dSdStorage()  # x0, v, g, mass, see DATA_TYPE.h
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
        # Strain limiting: 1.01 means max 1% stretching, second component for compression?
        self.strain_limit = Vector2d(1.01, 0)
        self.sHat = Vector2d(1, 1)
        self.kappa_s = Vector2d(0, 0)
        self.friction_iterations = 1
        self.friction_coefficient = 0.5
        self.muComp = StdVectorXd()  # list of mus?
        self.DBC = Storage.V4dStorage()
        self.DBCMotion = Storage.V2iV3dV3dV3dSdStorage()

        # Solver settings
        self.projected_newton_tolerance = 1e-3
        self.static_solve = False
        self.epsv2 = 1e-6  # not sure what this is

        self.cipc_initialized = False

        self.enable_collisions = True

        self.cloths = []
        self.materials_cloth = {}

        self.static_object_DBCs = []

    def add_cloth(self, cloth, material: Material):
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

        index_range = self._add_shell(object)
        positions_min = Vector3d(-100, -100, -100)
        positions_max = Vector3d(100, 100, 100)
        rotation = (Vector3d(0, 0, 0), Vector3d(0, 1, 0), 0)
        velocity = Vector3d(0, 0, 0)

        DBC = (
            positions_min,
            positions_max,
            velocity,
            *rotation,
            index_range,
        )

        self.static_object_DBCs.append(DBC)

        # TODO bookkeeping for actuation and import

    def _add_shell(self, object):

        self.blender_objects_input.append(object)

        # TODO triangulate if necessary
        filepath = export_as_obj(object, self.filepaths["run"])
        # TODO read object transform, ignored for now
        index_range = FEM.DiscreteShell.Add_Shell(
            filepath,
            *identity_transform,
            self.vertex_coordinates,
            self.triangles,
            self.vertex_counts_cumulative,
        )

        self.vertex_index_ranges.append(index_range)
        return index_range

    def initialize_cipc(self):
        MeshIO.Append_Attribute(
            self.vertex_coordinates, self.vertex_coordinates_original
        )  # not sure if this is needed

        cloth = self.cloths[0]
        material_cloth = self.materials_cloth[cloth]
        thickness = material_cloth.thickness

        # dHat2 == thickness_elastic_squared = thickness ** 2

        self.thickness_elastic_squared = FEM.DiscreteShell.Initialize_Shell_Hinge_EIPC(
            material_cloth.density_volumetric,
            material_cloth.youngs_modulus,
            material_cloth.poissons_ratio,
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

        # From initialize_OIPC, usually called with thickness 0.001 and offset 0
        stiffMult = 1
        self.thickness_elastic_squared = FEM.DiscreteShell.Initialize_OIPC(
            0.0, 0.0, thickness, 0.0, self.mass_matrix, self.kappa, stiffMult
        )
        # self.elasticIPC = False # redundant
        # self.thickness = offset

        self.cipc_initialized = True

        self.save_current_state_to_disk()
        self.import_cipc_output_from_disk_to_blender(self.current_frame)

    @property
    def vertex_counts(self):
        vertex_counts_cumulative = self.vertex_counts_cumulative
        _vertex_counts = [vertex_counts_cumulative[0]]
        for i in range(1, len(vertex_counts_cumulative)):
            count = vertex_counts_cumulative[i]
            count_prev = vertex_counts_cumulative[i - 1]
            vertex_count = count - count_prev
            _vertex_counts.append(vertex_count)
        return _vertex_counts

    def save_current_state_to_disk(self):
        shell_path = os.path.join(self.output_folder, f"shell{self.current_frame}.obj")
        MeshIO.Write_TriMesh_Obj(self.vertex_coordinates, self.triangles, shell_path)

    def import_cipc_output_from_disk_to_blender(self, frame):
        file = os.path.join(self.output_folder, f"shell{frame}.obj")

        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.import_scene.obj(filepath=file, split_mode="OFF")

        # All the CIPC shells are saved and imported as single mesh that we split up.
        object = bpy.context.selected_objects[0]
        object.data.materials.clear()  # Remove the default material

        vertex_counts = self.vertex_counts
        vertex_counts.pop(-1)  # We don't need to split the last object
        objects = []

        for i in range(len(vertex_counts)):
            vertex_range = range(vertex_counts[i])
            object_split_off = SimulationCIPC._split_object(object, vertex_range)
            object_split_off.name = f"{self.blender_objects_input[i].name}_{frame}"
            objects.append(object_split_off)

        objects.append(object)
        object.name = f"{self.blender_objects_input[-1].name}_{frame}"

        for object in objects:
            keyframe_visibility(object, frame, frame)

        self.blender_objects_output[frame] = objects

    @staticmethod
    def _split_object(object, vertex_indices_to_split_off):
        mesh = object.data
        bpy.context.view_layer.objects.active = object
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")

        for v in mesh.vertices:
            if v.index in vertex_indices_to_split_off:
                v.select = True

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.separate(type="SELECTED")
        bpy.ops.object.mode_set(mode="OBJECT")

        object_split_off = bpy.context.selected_objects[-1]
        return object_split_off

    def run(self, amount_of_steps):
        for _ in range(amount_of_steps):
            self.step({})

    def step(self, action: dict[int, list] = {}):
        """Advance the simulation a single time step. The action argument can be used to script the motion of several
        vertices. Action should be a dictionary that maps a vertex index to the velocity the vertex should have during
        the following time step.

        Args:
            action (dict[int, list]): dictionary that maps vertex indices to velocities.
        """
        if not self.cipc_initialized:
            self.initialize_cipc()

        cloth = self.cloths[0]
        material_cloth = self.materials_cloth[cloth]
        thickness = material_cloth.thickness

        self.DBC = Storage.V4dStorage()
        self.DBCMotion = Storage.V2iV3dV3dV3dSdStorage()
        print("STEP")
        print(action)
        for vertex_id, velocity in action.items():
            print(vertex_id)
            # index_range = (vertex_id, vertex_id + 1)
            index_range = Vector4i(vertex_id, 0, vertex_id + 1, -1)
            positions_min = Vector3d(-100, -100, -100)
            positions_max = Vector3d(100, 100, 100)
            rotation = (Vector3d(0, 0, 0), Vector3d(0, 1, 0), 0)
            # velocity = Vector3d(0, 0, 0)

            # velocity = [0, 0, 0.5]

            print(velocity)

            DBC = (
                positions_min,
                positions_max,
                to_Vector3d(velocity),
                *rotation,
                index_range,
            )

            DBCRangeMin, DBCRangeMax, v, rotCenter, rotAxis, angVelDeg, vIndRange = DBC

            FEM.Init_Dirichlet(
                self.vertex_coordinates,
                DBCRangeMin,
                DBCRangeMax,
                v,
                rotCenter,
                rotAxis,
                angVelDeg,
                self.DBC,
                self.DBCMotion,
                vIndRange,
            )

        for DBC in self.static_object_DBCs:
            DBCRangeMin, DBCRangeMax, v, rotCenter, rotAxis, angVelDeg, vIndRange = DBC

            FEM.Init_Dirichlet(
                self.vertex_coordinates,
                DBCRangeMin,
                DBCRangeMax,
                v,
                rotCenter,
                rotAxis,
                angVelDeg,
                self.DBC,
                self.DBCMotion,
                vIndRange,
            )

        print("thickness", thickness)
        print("thickness2", self.thickness_elastic_squared)

        # thickness = 0.01
        # self.thickness_elastic_squared = thickness * thickness

        FEM.Step_Dirichlet(self.DBCMotion, self.timestep_size, self.DBC)

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

        self.current_frame += 1
        self.save_current_state_to_disk()
        TIMER_FLUSH(0, 100, self.timestep_size, self.timestep_size)

        print("Importing", self.current_frame)

        self.import_cipc_output_from_disk_to_blender(self.current_frame)
