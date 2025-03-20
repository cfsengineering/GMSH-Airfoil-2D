from pathlib import Path

import gmsh
import gmshairfoil2d.__init__
from gmshairfoil2d.geometry_def import Circle, PlaneSurface, Rectangle

LIB_DIR = Path(gmshairfoil2d.__init__.__file__).parents[1]
test_data_dir = Path(LIB_DIR, "tests", "test_data")


def test_mesh_rectangle():
    """
    Test if a simple generated mesh formed of a square domain with a circular
    hole inside is meshed correctly

    """

    # Generate Geometry :
    gmsh.initialize()
    box = Rectangle(0, 0, 0, 1, 1, mesh_size=0.5)
    surface_domain = PlaneSurface([box])

    gmsh.model.geo.synchronize()
    box.define_bc()
    surface_domain.define_bc()

    # Generate mesh
    gmsh.model.mesh.generate(2)
    gmsh.write(str(Path(test_data_dir, "mesh_test.su2")))
    gmsh.finalize()

    # Test if the generated mesh is correct
    with open(Path(test_data_dir, "mesh_test.su2"), "r") as f:
        mesh_test = f.read()
    with open(Path(test_data_dir, "mesh.su2"), "r") as f:
        mesh_origin = f.read()

    assert mesh_test == mesh_origin


test_mesh_rectangle()
