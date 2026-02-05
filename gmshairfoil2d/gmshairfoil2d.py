"""Main module for GMSH airfoil 2D mesh generation."""

import argparse
import math
import sys
from pathlib import Path

import gmsh
from gmshairfoil2d.airfoil_func import (four_digit_naca_airfoil, get_airfoil_points,
                                        get_all_available_airfoil_names, read_airfoil_from_file)
from gmshairfoil2d.geometry_def import (AirfoilSpline, Circle, PlaneSurface,
                                        Rectangle, outofbounds, CType)
from gmshairfoil2d.config_handler import read_config, merge_config_with_args, create_example_config


def _calculate_spline_length(spline):
    """Calculate the length of a spline based on its points.
    
    Parameters
    ----------
    spline : object
        Spline object with point_list attribute
    
    Returns
    -------
    float
        Total length of the spline
    """
    if not hasattr(spline, 'point_list') or not spline or not spline.point_list:
        return 0
    
    points = spline.point_list
    if len(points) < 2:
        return 0
    
    return sum(
        math.sqrt((points[i].x - points[i+1].x)**2 + 
                 (points[i].y - points[i+1].y)**2)
        for i in range(len(points) - 1)
    )


def apply_transfinite_to_surfaces(airfoil_obj, airfoil_mesh_size, name=""):
    """
    Apply transfinite meshing to all three splines (upper, lower, and front) of an 
    airfoil or flap object for smooth cell transitions based on edge lengths.
    
    The key is to distribute nodes proportionally to each edge's length:
    - longer edges get more points
    - all edges get consistent cell sizing at junctions
    
    Parameters
    ----------
    airfoil_obj : AirfoilSpline
        The airfoil or flap object containing front_spline, upper_spline, lower_spline
    airfoil_mesh_size : float
        The target mesh size to maintain consistent cell dimensions
    name : str, optional
        Name of the object (for logging purposes)
    """
    # Calculate the length of each spline
    l_front = _calculate_spline_length(airfoil_obj.front_spline) if hasattr(airfoil_obj, 'front_spline') else 0
    l_upper = _calculate_spline_length(airfoil_obj.upper_spline) if hasattr(airfoil_obj, 'upper_spline') else 0
    l_lower = _calculate_spline_length(airfoil_obj.lower_spline) if hasattr(airfoil_obj, 'lower_spline') else 0
    
    # Calculate total perimeter
    total_length = l_front + l_upper + l_lower
    
    if total_length == 0:
        print(f"Warning: {name} has zero total length, skipping transfinite meshing")
        return
    
    # Distribute points proportionally to edge lengths
    # Target cell size should be approximately airfoil_mesh_size on all edges
    total_points = max(20, int(total_length / airfoil_mesh_size))
    
    # Distribute points based on proportion of each edge length
    # Front gets a multiplier for higher density at leading edge (Bump effect)
    front_multiplier = 2  # 100% extra density for front region
    weighted_length = l_front * front_multiplier + l_upper + l_lower
    
    nb_points_front = max(15, int((l_front * front_multiplier / weighted_length) * total_points))
    nb_points_upper = max(15, int((l_upper / weighted_length) * total_points))
    nb_points_lower = max(15, int((l_lower / weighted_length) * total_points))
    
    # Apply transfinite curves
    if hasattr(airfoil_obj, 'front_spline') and airfoil_obj.front_spline:
        gmsh.model.mesh.setTransfiniteCurve(
            airfoil_obj.front_spline.tag, nb_points_front, "Bump", 10)
    
    if hasattr(airfoil_obj, 'upper_spline') and airfoil_obj.upper_spline:
        gmsh.model.mesh.setTransfiniteCurve(airfoil_obj.upper_spline.tag, nb_points_upper)
    
    if hasattr(airfoil_obj, 'lower_spline') and airfoil_obj.lower_spline:
        gmsh.model.mesh.setTransfiniteCurve(airfoil_obj.lower_spline.tag, nb_points_lower)
    
    if name:
        # Calculate actual cell sizes for info
        front_cell_size = l_front / (nb_points_front - 1) if nb_points_front > 1 else 0
        upper_cell_size = l_upper / (nb_points_upper - 1) if nb_points_upper > 1 else 0
        lower_cell_size = l_lower / (nb_points_lower - 1) if nb_points_lower > 1 else 0
        
        print(f"Applied transfinite meshing to {name}:")
        print(f"  - Front spline: {nb_points_front:3d} points, length={l_front:.4f}, cell size ~ {front_cell_size:.6f}")
        print(f"  - Upper spline: {nb_points_upper:3d} points, length={l_upper:.4f}, cell size ~ {upper_cell_size:.6f}")
        print(f"  - Lower spline: {nb_points_lower:3d} points, length={l_lower:.4f}, cell size ~ {lower_cell_size:.6f}")


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
        "--config",
        type=str,
        metavar="PATH",
        help="Path to YAML configuration file",
    )

    parser.add_argument(
        "--save_config",
        type=str,
        metavar="PATH",
        help="Save configuration to a YAML file",
    )

    parser.add_argument(
        "--example_config",
        action="store_true",
        help="Create an example configuration file (config_example.yaml)",
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
        help="NACA airfoil 4 digit",
    )

    parser.add_argument(
        "--airfoil",
        type=str,
        metavar="NAME",
        nargs="?",
        help="Name of an airfoil profile in the database (database available with the --list argument)",
    )

    parser.add_argument(
        "--airfoil_path",
        type=str,
        metavar="PATH",
        help="Path to a custom .dat file with airfoil coordinates",
    )

    parser.add_argument(
        "--flap_path",
        type=str,
        metavar="PATH",
        help="Path to a custom .dat file with flap coordinates",
    )

    parser.add_argument(
        "--aoa",
        type=float,
        nargs="?",
        help="Angle of attack [deg] (default: 0 [deg])",
        default=0.0,
    )

    parser.add_argument(
        "--deflection",
        type=float,
        nargs="?",
        help="Angle of flap deflection [deg] (default: 0 [deg])",
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
        "--farfield_ctype",
        action="store_true",
        help="Generate a structured circular farfield (CType) for hybrid meshes",
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
        help="Mesh size of the airfoil contour [m]  (default 0.01m) (for normal, bl and structured)",
    )

    parser.add_argument(
        "--flap_mesh_size",
        type=float,
        metavar="SIZE",
        nargs="?",
        default=None,
        help="Mesh size of the flap contour [m] (if not provided, defaults to 85%% of airfoil_mesh_size)",
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
        help="Do the unstructured meshing (with triangles), without a boundary layer",
    )

    parser.add_argument(
        "--first_layer",
        type=float,
        metavar="HEIGHT",
        nargs="?",
        default=3e-5,
        help="Height of the first layer [m] (default 3e-5m) (for bl and structured)",
    )

    parser.add_argument(
        "--ratio",
        type=float,
        metavar="RATIO",
        nargs="?",
        default=1.2,
        help="Growth ratio of layers (default 1.2) (for bl and structured)",
    )

    parser.add_argument(
        "--nb_layers",
        type=int,
        metavar="INT",
        nargs="?",
        default=35,
        help="Total number of layers in the boundary layer (default 35)",
    )

    parser.add_argument(
        "--format",
        type=str,
        nargs="?",
        default="su2",
        help="Format of the mesh file, e.g: msh, vtk, wrl, stl, mesh, cgns, su2, dat (default su2)",
    )

    parser.add_argument(
        "--structured",
        action="store_true",
        help="Generate a structured mesh",
    )
    parser.add_argument(
        "--arg_struc",
        type=str,
        metavar="[LxL]",
        default="10x10",
        help="Parameters for the structured mesh [wake length (axis x)]x[total height (axis y)] [m] (default 10x10)",
    )

    parser.add_argument(
        "--output",
        type=str,
        metavar="PATH",
        nargs="?",
        default=".",
        help="Output path for the mesh file (default : current dir)",
    )

    parser.add_argument(
        "--ui",
        action="store_true",
        help="Open GMSH user interface to see the mesh",
    )
    args = parser.parse_args()

    # Handle configuration file operations
    if args.example_config:
        create_example_config()
        sys.exit()

    # Load configuration from file if provided
    if args.config:
        try:
            config_dict = read_config(args.config)
            args = merge_config_with_args(config_dict, args)
            print(f"Configuration loaded from: {args.config}")
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading configuration: {e}", file=sys.stderr)
            sys.exit(1)

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    if args.list:
        get_all_available_airfoil_names()
        sys.exit()

    # Airfoil choice
    cloud_points = None
    airfoil_name = None

    # Check that only one airfoil source is specified
    airfoil_sources = [args.naca, args.airfoil, args.airfoil_path]
    specified_sources = [s for s in airfoil_sources if s is not None]
    
    if len(specified_sources) > 1:
        print("\nError: Only one airfoil source can be specified at a time!")
        print("Choose one of: --naca, --airfoil, or --airfoil_path\n")
        sys.exit(1)

    if args.naca:
        airfoil_name = args.naca
        cloud_points = four_digit_naca_airfoil(airfoil_name)

    if args.airfoil:
        airfoil_name = args.airfoil
        cloud_points = get_airfoil_points(airfoil_name)

    if args.airfoil_path:
        airfoil_name = Path(args.airfoil_path).stem
        cloud_points = read_airfoil_from_file(args.airfoil_path)

        if args.flap_path:
            airfoil_name = Path(args.airfoil_path).stem
            flap_points = read_airfoil_from_file(args.flap_path)

    if cloud_points is None:
        print("\nNo airfoil profile specified, exiting")
        print("You must use --naca, --airfoil, or --airfoil_path\n")
        parser.print_help()
        sys.exit()

    # Make the points all start by the (0,0) (or minimum of coord x when not exactly 0) and go clockwise
    # --> to be easier to deal with after (in airfoilspline)
    le = min(p[0] for p in cloud_points)
    for p in cloud_points:
        if p[0] == le:
            debut = cloud_points.index(p)
    cloud_points = cloud_points[debut:]+cloud_points[:debut]
    if cloud_points[1][1] < cloud_points[0][1]:
        cloud_points.reverse()
        cloud_points = cloud_points[-1:] + cloud_points[:-1]

    # Angle of attack
    aoa = -args.aoa * (math.pi / 180)

    # Generate Geometry
    gmsh.initialize()

    # Airfoil
    airfoil = AirfoilSpline(
        cloud_points, args.airfoil_mesh_size, name="airfoil")
    airfoil.rotation(aoa, (0.5, 0, 0), (0, 0, 1))
    gmsh.model.geo.synchronize()

    if args.flap_path:
        # Use flap_mesh_size if provided, otherwise use 85% of airfoil_mesh_size
        flap_mesh_size = args.flap_mesh_size if args.flap_mesh_size else args.airfoil_mesh_size * 0.85
        flap = AirfoilSpline(
            flap_points, flap_mesh_size, name="flap", is_flap=True)
        flap.rotation(aoa, (0.5, 0, 0), (0, 0, 1))
        if args.deflection:
            flap.rotation(-args.deflection * (math.pi / 180), (flap.le.x, flap.le.y, 0), (0, 0, 1))
        gmsh.model.geo.synchronize()

    # If structured, all is done in CType
    if args.structured:
        dx_wake, dy = [float(value)for value in args.arg_struc.split("x")]
        mesh = CType(airfoil, dx_wake, dy,
                     args.airfoil_mesh_size, args.first_layer, args.ratio, aoa)
        mesh.define_bc()

    else:
        k1, k2 = airfoil.gen_skin()
        if args.flap_path:
            k1_flap, k2_flap = flap.gen_skin()
        # Choose the parameters for bl (when exist)
        if not args.no_bl:
            N = args.nb_layers
            r = args.ratio
            d = [args.first_layer]
            # Construct the vector of cumulative distance of each layer from airfoil
            for i in range(1, N):
                d.append(d[-1] - (-d[0]) * r**i)
        else:
            d = [0]

        # Need to check that the layers or airfoil do not go outside the box/circle (d[-1] is the total height of bl)
        outofbounds(airfoil, args.box, args.farfield, d[-1])

        # External domain
        if args.farfield_ctype:
            # Use C-type farfield (unstructured) for hybrid meshes
            ext_domain = CType(
                airfoil, args.farfield, args.farfield, args.ext_mesh_size,
                structured=args.structured
            )
        elif args.box:
            length, width = [float(value) for value in args.box.split("x")]
            ext_domain = Rectangle(0.5, 0, 0, length, width,
                                   mesh_size=args.ext_mesh_size)
        else:
            ext_domain = Circle(0.5, 0, 0, radius=args.farfield,
                                mesh_size=args.ext_mesh_size)
        gmsh.model.geo.synchronize()

        # Create the surface for the mesh
        if args.flap_path:
            surface = PlaneSurface([ext_domain, airfoil, flap])

        else:
            surface = PlaneSurface([ext_domain, airfoil])

        gmsh.model.geo.synchronize()

        # Create the boundary layer
        if not args.no_bl:
            curv = [airfoil.upper_spline.tag,
                    airfoil.lower_spline.tag, airfoil.front_spline.tag]
            if args.flap_path:
                curv += [flap.upper_spline.tag,
                         flap.lower_spline.tag, flap.front_spline.tag]

            # Creates a new mesh field of type 'BoundaryLayer' and assigns it an ID (f).
            f = gmsh.model.mesh.field.add('BoundaryLayer')

            # Add the curves where we apply the boundary layer (around the airfoil for us)
            gmsh.model.mesh.field.setNumbers(f, 'CurvesList', curv)
            gmsh.model.mesh.field.setNumber(f, 'Size', d[0])  # size 1st layer
            gmsh.model.mesh.field.setNumber(f, 'Ratio', r)  # Growth ratio
            # Total thickness of boundary layer
            gmsh.model.mesh.field.setNumber(f, 'Thickness', d[-1])

            # Forces to use quads and not triangle when =1 (i.e. true)
            gmsh.model.mesh.field.setNumber(f, 'Quads', 1)

            # Enter the points where we want a "fan" (points must be at end on line)(only te for us)
            if args.flap_path:
                print(f"airfoil.te.tag, flap.te.tag = {airfoil.te.tag, flap.te.tag}")
                gmsh.model.mesh.field.setNumbers(
                    f, "FanPointsList", [airfoil.te.tag, flap.te.tag])
            else:
                gmsh.model.mesh.field.setNumbers(
                    f, "FanPointsList", [airfoil.te.tag])

            gmsh.model.mesh.field.setAsBoundaryLayer(f)

        # Define boundary conditions (name the curves)
        ext_domain.define_bc()
        surface.define_bc()
        airfoil.define_bc()
        if args.flap_path:
            flap.define_bc()

    gmsh.model.geo.synchronize()

    # Choose the parameters of the mesh : we want the mesh size according to the points and not curvature (doesn't work with farfield)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 1)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

    if not args.structured and not args.no_bl:
        # Apply transfinite meshing to all three splines (front, upper, lower) 
        # for consistent cell sizing around the airfoil/flap surfaces
        
        # Apply to airfoil
        apply_transfinite_to_surfaces(airfoil, args.airfoil_mesh_size, name="Airfoil")
        
        # Apply to flap if present
        if args.flap_path:
            apply_transfinite_to_surfaces(flap, args.airfoil_mesh_size, name="Flap")
        
        # Choose the nbs of points in the fan at the te:
        # Compute coef : between 10 and 25, 15 when usual mesh size but adapted to mesh size
        coef = max(10, min(25, 15*0.01/args.airfoil_mesh_size))
        gmsh.option.setNumber("Mesh.BoundaryLayerFanElements", coef)

    # Generate mesh
    gmsh.model.mesh.generate(2)
    gmsh.model.mesh.optimize("Laplace2D", 5)

    # Open user interface of GMSH
    if args.ui:
        gmsh.fltk.run()

    # Mesh file name and output
    if airfoil_name:
        airfoil_name = airfoil_name.replace(".dat", "")

    if args.flap_path:
        airfoil_name = airfoil_name + "_flap"

    mesh_path = Path(
        args.output, f"mesh_airfoil_{airfoil_name}.{args.format}")
    gmsh.write(str(mesh_path))
    gmsh.finalize()

    # Save configuration if requested
    if args.save_config:
        # Remove None values and internal arguments from the config dict
        config_dict = {k: v for k, v in vars(args).items() 
                      if v is not None and v is not False 
                      and k not in ['config', 'save_config', 'example_config', 'list']}
        from gmshairfoil2d.config_handler import write_config
        write_config(config_dict, args.save_config)


if __name__ == "__main__":
    main()
