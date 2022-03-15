import argparse
from airfoil_func import (
    NACA_4_digit_geom,
    get_airfoil_points,
    get_all_available_airfoil_names,
)
from geometry_def import PlaneSurface, Circle, Rectangle, AirfoilSpline
import gmsh
import sys
import math

# Instantiate the parser
parser = argparse.ArgumentParser(description="Optional arguement description")

# Switch : Display list of available airfoil
parser.add_argument(
    "--list",
    action="store_true",
    help="Display all airfoil available in the database : https://m-selig.ae.illinois.edu/ads/coord_database.html",
)


parser.add_argument(
    "--naca", type=str, nargs="?", help="NACA airfoil 4 digit, ex : 4412"
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
    help="Create a circular farfield mesh of given radius [m]",
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
    help="Mesh size of the airfoil countour [m]",
)

parser.add_argument(
    "--ext_mesh_size",
    type=float,
    nargs="?",
    help="Mesh size of the external domain [m]",
)

parser.add_argument(
    "--format",
    type=str,
    nargs="?",
    help="format of the mesh file ex: .su2",
)

parser.add_argument(
    "--o",
    type=str,
    nargs="?",
    help="output path for the mesh file ex : home/myfolde/",
)

# Switch GUI
parser.add_argument("--ui", action="store_true", help="Open GMSH GUI to see the mesh")
args = parser.parse_args()

if len(sys.argv) == 1:
    parser.print_help()
    sys.exit()

if args.list is True:
    get_all_available_airfoil_names()

else:
    # Foil and angle of attack
    if args.naca is None:
        cloud_points = get_airfoil_points(args.airfoil)
    else:
        # Generate NACA 4 digit profil
        print(args)
        cloud_points = NACA_4_digit_geom(args.naca)

    if args.aoa is None:
        aoa = 0
    else:
        aoa = -args.aoa * (math.pi / 180)

    # Generate Geometry :
    gmsh.initialize()

    # 1)External domain

    if args.ext_mesh_size is None:
        ext_mesh_size = 0.2
    else:
        ext_mesh_size = args.ext_mesh_size

    if args.farfield is not None:
        # create a circular farfield
        ext_domain = Circle(0.5, 0, 0, radius=args.farfield, mesh_size=ext_mesh_size)
    elif args.box is not None:
        # create a Box (lenght x height)
        lenght, width = [float(value) for value in args.box.split("x")]
        ext_domain = Rectangle(0.5, 0, 0, lenght, width, mesh_size=ext_mesh_size)
    else:
        # if no argument is given create a circular farfield by default
        ext_domain = Circle(0.5, 0, 0, radius=10, mesh_size=0.2)

    if args.foil_mesh_size is None:
        mesh_size_foil = 0.01
    else:
        mesh_size_foil = args.foil_mesh_size
    # 2)Airfoil
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
    if args.ui is True:
        gmsh.fltk.run()

    # mesh file name and output
    if args.format is None:
        format = ".su2"
    else:
        format = args.format

    if args.o is None:
        path_file = ""
    else:
        path_file = args.o

    gmsh.write(path_file + "mesh" + format)
    gmsh.finalize()
