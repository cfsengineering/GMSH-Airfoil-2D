from airfoil_func import NACA_4_digit_geom
from geometry_def import PlaneSurface, Circle, AirfoilSpline
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
farfield = Circle(0, 0, 0, 10, mesh_size=mesh_size_far)

# 2)Airfoil
mesh_size_foil = 0.01
naca0012 = AirfoilSpline(cloud_points, mesh_size_foil)
naca0012.translation((-0.5, 0, 0))
naca0012.rotation(-0.2, (0, 0, 0), (0, 0, 1))
naca0012.gen_skin()


# 3)Generate domain
surface_domain = PlaneSurface([farfield, naca0012])

# Synchronize and generate BC marker
gmsh.model.occ.synchronize()
naca0012.define_bc()
farfield.define_bc()
surface_domain.define_bc()

# Generate mesh
gmsh.model.mesh.generate(2)

if GUI_flag is True:
    gmsh.fltk.run()

gmsh.write("mesh.su2")
gmsh.finalize()
