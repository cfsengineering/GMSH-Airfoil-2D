import sys
import os
import gmsh
import gmshairfoil2d.__init__
from gmshairfoil2d.geometry_def import Rectangle, Circle, PlaneSurface

LIB_DIR = os.path.dirname(gmshairfoil2d.__init__.__file__)
test_data_dir = os.path.join(LIB_DIR, os.path.dirname(LIB_DIR), "tests", "test_data")


def test_mesh_circle_into_rectangle():
    """
    Test if a simple generated mesh formed of a square domain with a circular
    hole inside is meshed correctly

    """
    # Generate Geometry :
    gmsh.initialize()

    mesh_size = 0.1
    Box = Rectangle(0, 0, 0, 2, 2, mesh_size)
    Disk = Circle(0, 0, 0, 0.5, mesh_size)
    surface_domain = PlaneSurface([Box, Disk])
    gmsh.model.occ.synchronize()
    # Generate mesh
    gmsh.model.mesh.generate(2)
    gmsh.write(os.path.join(test_data_dir, "mesh_test.su2"))
    gmsh.finalize()

    with open(os.path.join(test_data_dir, "mesh_test.su2"), "r") as f:
        mesh_test = f.read()
    f.close()

    with open(os.path.join(test_data_dir, "mesh.su2"), "r") as f:
        mesh_origin = f.read()
    f.close()
    # Test if conform
    assert mesh_test == mesh_origin
