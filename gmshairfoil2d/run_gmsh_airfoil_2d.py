import argparse
import math
import sys
import os

import gmsh

from airfoil_func import (
    NACA_4_digit_geom,
    get_airfoil_points,
    get_all_available_airfoil_names,
)
from geometry_def import AirfoilSpline, Circle, PlaneSurface, Rectangle

# Instantiate the parser
parser = argparse.ArgumentParser(description="Optional arguement description")

# Switch : Display list of available airfoil
parser.add_argument(
    "--list",
    action="store_true",
    help="Display all airfoil available in the database : https://m-selig.ae.illinois.edu/ads/coord_database.html",
)

parser.add_argument(
    "--naca", type=str, nargs="?", help="NACA airfoil 4 digit (default 0012)"
)

parser.add_argument(
    "--airfoil",
    type=str,
    nargs="?",
    help="Name of an airfoil profile in the database (database available with the --list argument)",
)

parser.add_argument("--aoa", type=float, nargs="?", help="Angle of attack in deg")

parser.add_argument(
    "--farfield",
    type=float,
    nargs="?",
    help="Create a circular farfield mesh of given radius [m] (default 10m)",
)
parser.add_argument(
    "--box",
    type=str,
    nargs="?",
    help="Create a box mesh of dimensions [lenght]x[height] [m]",
)
parser.add_argument(
    "--foil_mesh_size",
    type=float,
    nargs="?",
    help="Mesh size of the airfoil countour [m]  (default 0.01m)",
)

parser.add_argument(
    "--ext_mesh_size",
    type=float,
    nargs="?",
    help="Mesh size of the external domain [m] (default 0.2m)",
)

parser.add_argument(
    "--format",
    type=str,
    nargs="?",
    help="format of the mesh file, e.g: msh, vtk, wrl, stl, mesh, cgns, su2, dat (default su2)",
)

parser.add_argument(
    "--output",
    type=str,
    nargs="?",
    help="output path for the mesh file ex : /home/mymeshes (default : current dir)",
)

# Switch GUI
parser.add_argument(
    "--ui", action="store_true", help="Open GMSH user interface to see the mesh"
)
args = parser.parse_args()

if len(sys.argv) == 1:
    parser.print_help()
    sys.exit()

if args.list:
    get_all_available_airfoil_names()
    sys.exit()


# Airfoil choice

cloud_points = None
if args.naca:
    airfoil_name = args.naca
    cloud_points = NACA_4_digit_geom(airfoil_name)

if args.airfoil:
    airfoil_name = args.airfoil
    cloud_points = get_airfoil_points(airfoil_name)

if cloud_points is None:
    print("\nNo airfoil profile specified, exiting")
    print("You must use --naca or --airfoil\n")
    parser.print_help()
    sys.exit()

# Angle of attack
aoa = 0
if args.aoa:
    aoa = -args.aoa * (math.pi / 180)

# Generate Geometry :
gmsh.initialize()

# 1) External domain
ext_mesh_size = 0.2
if args.ext_mesh_size:
    ext_mesh_size = args.ext_mesh_size

if args.box:
    lenght, width = [float(value) for value in args.box.split("x")]
    ext_domain = Rectangle(0.5, 0, 0, lenght, width, mesh_size=ext_mesh_size)
else:
    radius = 10
    if args.farfield:
        radius = args.farfield

    ext_domain = Circle(0.5, 0, 0, radius=radius, mesh_size=ext_mesh_size)

# 2) Airfoil
mesh_size_foil = 0.01
if args.foil_mesh_size:
    mesh_size_foil = args.foil_mesh_size

airfoil = AirfoilSpline(cloud_points, mesh_size_foil)
airfoil.rotation(aoa, (0.5, 0, 0), (0, 0, 1))
airfoil.gen_skin()

# 3)Generate domain
surface_domain = PlaneSurface([ext_domain, airfoil])

# Synchronize and generate BC marker
gmsh.model.occ.synchronize()
ext_domain.define_bc()
airfoil.define_bc()
surface_domain.define_bc()

# Generate mesh
gmsh.model.mesh.generate(2)
if args.ui:
    gmsh.fltk.run()

# Mesh file name and output
format = "su2"
if args.format:
    format = args.format

path_file = ""
if args.output:
    path_file = args.o

mesh_path = os.path.join(path_file, f"mesh_airfoil_{airfoil_name}.{format}")
gmsh.write(mesh_path)
gmsh.finalize()
