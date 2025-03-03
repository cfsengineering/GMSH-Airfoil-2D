#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import math
import sys
from pathlib import Path

import gmsh
from gmshairfoil2d.airfoil_func import (NACA_4_digit_geom, get_airfoil_points,
                                        get_all_available_airfoil_names)
from gmshairfoil2d.geometry_def import (AirfoilSpline, Circle, PlaneSurface,
                                        Rectangle, CurveLoop, Line, Point)


def main():
    # Instantiate the parser
    parser = argparse.ArgumentParser(
        description="Optional argument description",
        usage=argparse.SUPPRESS,
        formatter_class=lambda prog: argparse.HelpFormatter(
            prog, max_help_position=80, width=99
        ),
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="Display all airfoil available in the database : https://m-selig.ae.illinois.edu/ads/coord_database.html",
    )

    parser.add_argument(
        "--naca",
        type=str,
        metavar="4DIGITS",
        nargs="?",
        help="NACA airfoil 4 digit (default 0012)",
    )

    parser.add_argument(
        "--airfoil",
        type=str,
        metavar="NAME",
        nargs="?",
        help="Name of an airfoil profile in the database (database available with the --list argument)",
    )

    parser.add_argument(
        "--aoa",
        type=float,
        nargs="?",
        help="Angle of attack [deg] (default: 0 [deg])",
        default=0.0,
    )

    parser.add_argument(
        "--farfield",
        type=float,
        metavar="RADIUS",
        nargs="?",
        default=10,
        help="Create a circular farfield mesh of given radius [m] (default 10m)",
    )
    parser.add_argument(
        "--box",
        type=str,
        metavar="LENGTHxWIDTH",
        nargs="?",
        help="Create a box mesh of dimensions [length]x[height] [m]",
    )
    parser.add_argument(
        "--airfoil_mesh_size",
        type=float,
        metavar="SIZE",
        nargs="?",
        default=0.01,
        help="Mesh size of the airfoil contour [m]  (default 0.01m)",
    )

    parser.add_argument(
        "--ext_mesh_size",
        type=float,
        metavar="SIZE",
        nargs="?",
        default=0.2,
        help="Mesh size of the external domain [m] (default 0.2m)",
    )

    parser.add_argument(
        "--no_bl",
        action="store_true",
        help="Do the meshing without a boundary layer (made with quads)",
    )

    parser.add_argument(
        "--first_layer",
        type=float,
        metavar="HEIGHT",
        nargs="?",
        default=3e-5,
        help="Height of the first layer [m] (default 3e-5m)",
    )

    parser.add_argument(
        "--ratio_bl",
        type=float,
        metavar="RATIO",
        nargs="?",
        default=1.2,
        help="Growth ratio for the boundary layer (default 1.2)",
    )

    parser.add_argument(
        "--nb_layers",
        type=int,
        metavar="NB",
        nargs="?",
        default=35,
        help="Total number of layers in the boundary layer (default 35)",
    )

    parser.add_argument(
        "--format",
        type=str,
        nargs="?",
        default="msh",
        help="format of the mesh file, e.g: msh, vtk, wrl, stl, mesh, cgns, su2, dat (default msh)",
    )

    parser.add_argument(
        "--output",
        type=str,
        metavar="PATH",
        nargs="?",
        default=".",
        help="output path for the mesh file (default : current dir)",
    )

    parser.add_argument(
        "--ui",
        action="store_true",
        help="Open GMSH user interface to see the mesh",
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

    print("before", cloud_points)
    # Points need to go clockwise
    l = len(cloud_points)
    if cloud_points[0][0] > 0.5 and cloud_points[l//4][1] > 0:
        cloud_points.reverse()
    if cloud_points[0][0] < 0.5 and cloud_points[l//4][1] < 0:
        cloud_points.reverse()
    print("\nafter", cloud_points)

    # Angle of attack
    aoa = -args.aoa * (math.pi / 180)

    # Generate Geometry
    gmsh.initialize()

    # Airfoil
    airfoil = AirfoilSpline(cloud_points, args.airfoil_mesh_size)
    airfoil.rotation(aoa, (0.5, 0, 0), (0, 0, 1))
    airfoil.gen_skin()
    gmsh.model.geo.synchronize()

    if args.no_bl:  # just want normal mesh, define the interior boundary as the airfoil
        boundary_middle = airfoil
    else:
        # Create a boundary layer

        # Choose the parameters
        N = args.nb_layers
        r = args.ratio_bl
        d = [-args.first_layer]
        # Construct the vector of cumulative distance of each layer from airfoil
        for i in range(1, N):
            d.append(d[-1] - (-d[0]) * r**i)

        # Function that does the boundary layer
        extbl_tags = gmsh.model.geo.extrudeBoundaryLayer(
            gmsh.model.getEntities(1), [1] * N, d, True)
        gmsh.model.geo.synchronize()

        # Create curve loop with "top" curves of the boundary layer, to define the rest of the mesh
        # (use ::2 bc once every two in extbl_tags there is a surface that we don't want. Only want lines. Somehow if with geo we must put every 4? Still don't understand but works)
        boundary_middle = CurveLoop([c[1] for c in extbl_tags[::4]])
        gmsh.model.geo.synchronize()

    # External domain
    if args.box:
        length, width = [float(value) for value in args.box.split("x")]
        ext_domain = Rectangle(0.5, 0, 0, length, width,
                               mesh_size=args.ext_mesh_size)
    else:
        ext_domain = Circle(0.5, 0, 0, radius=args.farfield,
                            mesh_size=args.ext_mesh_size)

    gmsh.model.geo.synchronize()

    # Create the surface for the triangular mesh
    surface = PlaneSurface([ext_domain, boundary_middle])
    gmsh.model.geo.synchronize()

    # Define boundary conditions (name the curves)
    ext_domain.define_bc()
    surface.define_bc()
    airfoil.define_bc()
    boundary_middle.define_bc()

    # Generate mesh
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 1)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.model.mesh.generate(2)

    # Open user interface of GMSH
    if args.ui:
        gmsh.fltk.run()

    # Mesh file name and output
    mesh_path = Path(
        args.output, f"mesh_airfoil_{airfoil_name}.{args.format}")
    gmsh.write(str(mesh_path))
    gmsh.finalize()


if __name__ == "__main__":
    main()
