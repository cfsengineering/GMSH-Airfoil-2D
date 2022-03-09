"""
This script contain the definition of geometrical objects needed to build the geometry.
"""

from operator import attrgetter
import gmsh
import numpy as np
import math


class Point:
    """
    A class to represent the point geometrical object of gmsh
    
    ...
    
    Attributes
    ----------
    x : float
        position in x
    y : float
        position in y
    z : float
        position in z
    mesh_size : float
        If mesh_size is > 0, add a meshing constraint
            at that point
    """

    def __init__(self, x, y, z, mesh_size):

        self.x = x
        self.y = y
        self.z = z

        self.mesh_size = mesh_size
        self.dim = 0

        # create the gmsh object and store the tag of the geometric object
        self.tag = gmsh.model.occ.addPoint(self.x, self.y, self.z, self.mesh_size)


class Line:
    """
    A class to represent the Line geometrical object of gmsh
    
    ...
    
    Attributes
    ----------
    start_point : Point
        first point of the line
    end_point : Point
        second point of the line
    """

    def __init__(self, start_point, end_point):

        self.start_point = start_point
        self.end_point = end_point

        self.dim = 1

        # create the gmsh object and store the tag of the geometric object
        self.tag = gmsh.model.occ.addLine(self.start_point.tag, self.end_point.tag)


class Spline:
    """
    A class to represent the Spine geometrical object of gmsh
    
    ...
    
    Attributes
    ----------
    points_list : list(Point)
        list of Point object forming the Spline
    """

    def __init__(self, point_list):
        self.point_list = point_list

        # generate the Lines tag list to folow
        self.tag_list = [point.tag for point in self.point_list]
        self.dim = 1
        # create the gmsh object and store the tag of the geometric object
        self.tag = gmsh.model.occ.addSpline(self.tag_list)


class CurveLoop:
    """
    A class to represent the CurveLoop geometrical object of gmsh
    
    ...
    
    Attributes
    ----------
    line_list : list(Line)
        List of Line object, in the order of the wanted CurveLoop and closed
    """

    def __init__(self, line_list):

        self.line_list = line_list

        # generate the Lines tag list to folow
        self.tag_list = [line.tag for line in self.line_list]
        # create the gmsh object and store the tag of the geometric object
        self.tag = gmsh.model.occ.addCurveLoop(self.tag_list)


class Circle:
    """
    A class to represent a Circle geometrical object, composed of many arcCircle object of gmsh
    
    ...
    
    Attributes
    ----------
    xc : float
        position of the center in x
    yc : float
        position of the center in y
    z : float
        position in z
    radius : float
        radius of the circle
    mesh_size : float
        determine the mesh resolution and how many segment the
        resulting circle will be composed of
    """

    def __init__(self, xc, yc, zc, radius, mesh_size):
        # Position of the disk center
        self.xc = xc
        self.yc = yc
        self.zc = zc

        self.radius = radius
        self.mesh_size = mesh_size
        self.dim = 1

        # create a structured arcCricle to merge in one curveloop
        self.distribution = math.floor((np.pi * 2 * self.radius) / self.mesh_size)
        self.points_list = [
            Point(
                self.xc + self.radius * np.cos(2 * np.pi / self.distribution * i),
                self.yc + self.radius * np.sin(2 * np.pi / self.distribution * i),
                self.zc,
                self.mesh_size,
            )
            for i in range(0, self.distribution)
        ]

        # Merge in one Spline
        self.circle_spline = Spline(self.points_list + [self.points_list[0]])
        # Form CurveLoop
        self.tag = CurveLoop([self.circle_spline]).tag


class Rectangle:
    """
    A class to represent a rectangle geometrical object, composed of 4 Lines object of gmsh
    
    ...
    
    Attributes
    ----------
    xc : float
        position of the center in x
    yc : float
        position of the center in y
    z : float
        position in z
    dx: float
        length of the rectangle along the x direction
    dy: float
        length of the rectangle along the y direction
    mesh_size : float
        attribute given for the class Point
    """

    def __init__(self, xc, yc, z, dx, dy, mesh_size, made_of_spline=True):

        self.xc = xc
        self.yc = yc
        self.z = z

        self.dx = dx
        self.dy = dy

        self.mesh_size = mesh_size
        self.dim = 1
        self.made_of_spline = made_of_spline

        # Generate the 4 corners of the rectangle
        self.points = [
            Point(self.xc - self.dx / 2, self.yc - self.dy / 2, z, self.mesh_size),
            Point(self.xc + self.dx / 2, self.yc - self.dy / 2, z, self.mesh_size),
            Point(self.xc + self.dx / 2, self.yc + self.dy / 2, z, self.mesh_size),
            Point(self.xc - self.dx / 2, self.yc + self.dy / 2, z, self.mesh_size),
        ]

        # Generate the 4 lines or Spline of the rectangle
        if self.made_of_spline == True:
            self.lines = [
                Spline([self.points[0], self.points[1]]),
                Spline([self.points[1], self.points[2]]),
                Spline([self.points[2], self.points[3]]),
                Spline([self.points[3], self.points[0]]),
            ]
        else:
            self.lines = [
                Line(self.points[0], self.points[1]),
                Line(self.points[1], self.points[2]),
                Line(self.points[2], self.points[3]),
                Line(self.points[3], self.points[0]),
            ]
        self.tag = CurveLoop(self.lines).tag

    def define_bc(self):
        """
        Method that define the different markers of the rectangle for the boundary condition
        self.lines[0] => wall_bot
        self.lines[1] => outlet
        self.lines[2] => wall_top
        self.lines[3] => inlet
        -------
        """

        self.bc_in = gmsh.model.addPhysicalGroup(self.dim, [self.lines[3].tag], tag=-1)
        gmsh.model.setPhysicalName(self.dim, self.bc_in, "inlet")

        self.bc_out = gmsh.model.addPhysicalGroup(self.dim, [self.lines[1].tag])
        gmsh.model.setPhysicalName(self.dim, self.bc_out, "outlet")

        self.bc_wall = gmsh.model.addPhysicalGroup(
            self.dim, [self.lines[0].tag, self.lines[2].tag]
        )
        gmsh.model.setPhysicalName(self.dim, self.bc_wall, "wall")

        self.bc = [self.bc_in, self.bc_out, self.bc_wall]


class PlaneSurface:
    """
    A class to represent the PlaneSurface geometrical object of gmsh
    
    ...
    
    Attributes
    ----------
    curveLoop_list : list(CurveLoop)
        List of CurveLoop object, the first curve loop defines
        the exterior contour; additional curve loop
        define holes in the surface domaine

    """

    def __init__(self, curveLoop_list):

        self.curveLoop_list = curveLoop_list
        self.tag_list = [curveLoop.tag for curveLoop in self.curveLoop_list]

        self.dim = 2

        # create the gmsh object and store the tag of the geometric object
        self.tag = gmsh.model.occ.addPlaneSurface(self.tag_list)

    def define_bc(self):
        """
        Method that define the domain marker of the surface
        -------
        """
        self.ps = gmsh.model.addPhysicalGroup(self.dim, [self.tag])
        gmsh.model.setPhysicalName(self.dim, self.ps, "fluid")


class Airfoil:
    """
    A class to represent and airfoil as a CurveLoop object formed with lines
    
    ...
    
    Attributes
    ----------
    point_cloud : list(list(float))
        List of points forming the airfoil in the order,
        each point is a list containing in the order
        its postion x,y,z
    mesh_size : float
        attribute given for the class Point,Note that a mesh size larger
        than the resolution given by the cloud of points
        will not be taken into account
    name : str
        name of the marker that will be associated to the airfoil
        boundary condition
    """

    def __init__(self, point_cloud, mesh_size, name="airfoil"):

        self.name = name
        self.dim = 1
        # Generate Points object from the point_cloud
        self.points = [
            Point(point_cord[0], point_cord[1], point_cord[2], mesh_size)
            for point_cord in point_cloud
        ]
        # Generate Lines object from Points
        self.lines = [
            Line(self.points[i], self.points[i + 1])
            for i in range(-1, len(self.points) - 1)
        ]

        self.CurveLoop = CurveLoop(self.lines)
        self.tag = self.CurveLoop.tag

    def define_bc(self):
        """
        Method that define the marker of the airfoil for the boundary condition
        -------
        """
        self.bc = gmsh.model.addPhysicalGroup(self.dim, self.CurveLoop.tag_list)
        gmsh.model.setPhysicalName(self.dim, self.bc, self.name)


class AirfoilSpline:
    """
    A class to represent and airfoil as a CurveLoop object formed with Splines
    ...
    
    Attributes
    ----------
    point_cloud : list(list(float))
        List of points forming the airfoil in the order,
        each point is a list containing in the order
        its postion x,y,z
    mesh_size : float
        attribute given for the class Point,Note that a mesh size larger
        than the resolution given by the cloud of points
        will not be taken into account
    name : str
        name of the marker that will be associated to the airfoil
        boundary condition
    """

    def __init__(self, point_cloud, mesh_size, name="airfoil"):

        self.name = name
        self.dim = 1

        # Generate Points object from the point_cloud
        self.points = [
            Point(point_cord[0], point_cord[1], point_cord[2], mesh_size)
            for point_cord in point_cloud
        ]
        # Find leading and trailing edge location
        self.le = min(self.points, key=attrgetter("x"))
        self.te = max(self.points, key=attrgetter("x"))

        self.points_tag = [point.tag for point in self.points]

        # Create the Splines depending on the le and te location in point_cloud
        if self.le.tag < self.te.tag:
            # create a spline from the leading edge to the trailing edge
            self.upper_spline_tag = gmsh.model.occ.addSpline(
                self.points_tag[
                    self.points_tag.index(self.le.tag) : self.points_tag.index(
                        self.te.tag
                    )
                    + 1
                ]
            )
            # create a spline from the trailing edge to the leading edge
            self.lower_spline_tag = gmsh.model.occ.addSpline(
                self.points_tag[
                    self.points_tag.index(self.te.tag) : self.points_tag[-1]
                ]
                + self.points_tag[0 : self.points_tag.index(self.le.tag) + 1]
            )

        else:
            self.upper_spline_tag = gmsh.model.occ.addSpline(
                (
                    self.points_tag[
                        (self.points_tag).index(self.le.tag) : (self.points_tag[-1])
                    ]
                    + self.points_tag[0 : self.points_tag.index(self.te.tag) + 1]
                )
            )
            self.lower_spline_tag = gmsh.model.occ.addSpline(
                self.points_tag[
                    self.points_tag.index(self.te.tag) : self.points_tag.index(
                        self.le.tag
                    )
                    + 1
                ]
            )

        # form the curvedloop
        self.tag = gmsh.model.occ.addCurveLoop(
            [self.upper_spline_tag, self.lower_spline_tag]
        )

    def define_bc(self):
        """
        Method that define the marker of the airfoil for the boundary condition
        -------
        """
        self.bc = gmsh.model.addPhysicalGroup(
            self.dim, [self.upper_spline_tag, self.lower_spline_tag]
        )
        gmsh.model.setPhysicalName(self.dim, self.bc, self.name)
        gmsh.model.setPhysicalName(self.dim, self.bc, self.name)
