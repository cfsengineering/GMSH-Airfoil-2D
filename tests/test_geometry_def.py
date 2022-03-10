import os
import gmsh
import gmshairfoil2d.__init__
from gmshairfoil2d.geometry_def import Rectangle, Circle, PlaneSurface

LIB_DIR = os.path.dirname(gmshairfoil2d.__init__.__file__)
test_data_dir = os.path.join(LIB_DIR, os.path.dirname(LIB_DIR), "tests", "test_data")


def test_mesh_rectangle():
    """
    Test if a simple generated mesh formed of a square domain with a circular
    hole inside is meshed correctly

    """
    
    # Generate Geometry :
    gmsh.initialize()
    box = Rectangle(0, 0, 0, 1, 1, mesh_size=0.5)
    surface_domain = PlaneSurface([box])
    
    gmsh.model.occ.synchronize()
    box.define_bc()
    surface_domain.define_bc()
    
    # Generate mesh
    gmsh.model.mesh.generate(2)
    gmsh.write(os.path.join(test_data_dir, "mesh_test.su2"))
    gmsh.finalize()

    # Test if the generated mesh is correct
    with open(os.path.join(test_data_dir, "mesh_test.su2"), "r") as f:
        mesh_test = f.read()
    with open(os.path.join(test_data_dir, "mesh.su2"), "r") as f:
        mesh_origin = f.read()
        
    assert mesh_test == mesh_origin
