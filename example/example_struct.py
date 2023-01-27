from gmshairfoil2d.airfoil_func import NACA_4_digit_geom
from gmshairfoil2d.geometry_def import CType, AirfoilSpline
import gmsh

# Open gmsh GUI
GUI_flag = True

# Generate NACA 4 digit profil
cloud_points = NACA_4_digit_geom("0012", nb_points=100)

# Generate Geometry :
gmsh.initialize()
gmsh.model.add("example_NACA_struct")

# 1)Airfoil
mesh_size_foil = 0.1
naca0012 = AirfoilSpline(cloud_points, mesh_size_foil)
naca0012.translation((-0.5, 0, 0))
naca0012.rotation(-0.2, (0, 0, 0), (0, 0, 1))

# 2)Farfield
mesh_size = 0.2
farfield = CType(naca0012, 0, 1, 10, 10, mesh_size=mesh_size)


gmsh.model.geo.synchronize()

# Generate mesh
gmsh.model.mesh.generate(2)

if GUI_flag is True:
    gmsh.fltk.run()

gmsh.finalize()
