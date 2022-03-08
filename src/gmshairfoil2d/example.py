from airfoil_func import NACA_4_digit_geom
from geometry_def import PlaneSurface, Rectangle, Circle, AirfoilSpline
import gmsh

# Open gmsh GUI
GUI_flag = True

# Generate NACA 4 digit profil
cloud_points = NACA_4_digit_geom("0012", nb_points=100)

# Generate Geometry :
gmsh.initialize()
gmsh.model.add("example_NACA")

# 1)Farfield
mesh_size_far = 0.5
farfield = Circle(0.5, 0, 0, radius=10, mesh_size=mesh_size_far)

# 2)Airfoil
mesh_size_foil = 0.01
naca0012 = AirfoilSpline(cloud_points, mesh_size_foil)

# 3)Generate domain
surface_domain = PlaneSurface([farfield, naca0012])

# Synchronize and mesh geometry
gmsh.model.occ.synchronize()
gmsh.model.mesh.generate(2)

if GUI_flag is True:
    gmsh.fltk.run()
    
gmsh.write("mesh.su2")
gmsh.finalize()
