"""
This script contain the definition of geometrical objects needed to build the geometry.
"""

from operator import attrgetter
import gmsh
import numpy as np
import math
import sys


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
        self.tag = gmsh.model.geo.addPoint(
            self.x, self.y, self.z, self.mesh_size)

    def rotation(self, angle, origin, axis):
        """
        Method to rotate the object Point
        ...
        Parameters
        ----------
        angle : float
            angle of rotation in rad
        origin : tuple
            tuple of point (x,y,z) which is the origin of the rotation
        axis : tuple
            tuple of point (x,y,z) which represent the axis of rotation
        """
        gmsh.model.geo.rotate(
            [(self.dim, self.tag)],
            *origin,
            *axis,
            angle,
        )

    def translation(self, vector):
        """
        Method to translate the object Point

        ...

        Parameters
        ----------
        direction : tuple
            tuple of point (x,y,z) which represent the direction of the translation
        """
        gmsh.model.geo.translate([(self.dim, self.tag)], *vector)


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
        self.tag = gmsh.model.geo.addLine(
            self.start_point.tag, self.end_point.tag)

    def rotation(self, angle, origin, axis):
        """
        Method to rotate the object Line
        ...

        Parameters
        ----------
        angle : float
            angle of rotation in rad
        origin : tuple
            tuple of point (x,y,z) which is the origin of the rotation
        axis : tuple
            tuple of point (x,y,z) which represent the axis of rotation
        """
        gmsh.model.geo.rotate(
            [(self.dim, self.tag)],
            *origin,
            *axis,
            angle,
        )

    def translation(self, vector):
        """
        Method to translate the object Line
        ...

        Parameters
        ----------
        direction : tuple
            tuple of point (x,y,z) which represent the direction of the translation
        """
        gmsh.model.geo.translate([(self.dim, self.tag)], *vector)


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

        # generate the Lines tag list to follow
        self.tag_list = [point.tag for point in self.point_list]
        self.dim = 1
        # create the gmsh object and store the tag of the geometric object
        self.tag = gmsh.model.geo.addSpline(self.tag_list)

    def rotation(self, angle, origin, axis):
        """
        Method to rotate the object Spline

        Rotate the spline itself (curve, startpoint, endpoint), then rotate the intermediate points
        ...

        Parameters
        ----------
        angle : float
            angle of rotation in rad
        origin : tuple
            tuple of point (x,y,z) which is the origin of the rotation
        axis : tuple
            tuple of point (x,y,z) which represent the axis of rotation
        """
        gmsh.model.geo.rotate(
            [(self.dim, self.tag)],
            *origin,
            *axis,
            angle,
        )

        [
            interm_point.rotation(angle, origin, axis)
            for interm_point in self.point_list[1:-1]
        ]

    def translation(self, vector):
        """
        Method to translate the object Line

        Translate the spline itself (curve, startpoint,endpoint), then translate the indermediate points
        ...

        Parameters
        ----------
        direction : tuple
            tuple of point (x,y,z) which represent the direction of the translation
        """
        gmsh.model.geo.translate([(self.dim, self.tag)], *vector)
        [interm_point.translation(vector)
         for interm_point in self.point_list[1:-1]]


class CurveLoop:
    """
    A class to represent the CurveLoop geometrical object of gmsh
    Curveloop object are an addition entity of the existing line that forms it
    Curveloop must be created when the geometry is in its final layout

    ...

    Attributes
    ----------
    line_list : list(Line)
        List of Line object, in the order of the wanted CurveLoop and closed
        Possibility to give either the tags directly, or the object Line
    """

    def __init__(self, line_list):

        self.line_list = line_list
        self.dim = 1
        # generate the Lines tag list to follow
        self.tag_list = [line.tag for line in self.line_list]
        # create the gmsh object and store the tag of the geometric object
        self.tag = gmsh.model.geo.addCurveLoop(self.tag_list)

    def close_loop(self):
        """
        Method to form a close loop with the current geometrical object. In our case,
        we already have it so just return the tag

        Returns
        -------
        _ : int
            return the tag of the CurveLoop object
        """
        return self.tag

    def define_bc(self):
        """
        Method that define the marker of the CurveLoop (when used as boundary layer boundary)
        for the boundary condition
        -------
        """

        self.bc = gmsh.model.addPhysicalGroup(self.dim, [self.tag])
        self.physical_name = gmsh.model.setPhysicalName(
            self.dim, self.bc, "top of boundary layer")


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
    zc : float
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

        # create multiples ArcCircle to merge in one circle

        # first compute how many points on the circle (for the meshing to be alined with the points)
        self.distribution = math.floor(
            (np.pi * 2 * self.radius) / self.mesh_size)
        realmeshsize = (np.pi * 2 * self.radius)/self.distribution

        # Create the center of the circle
        center = Point(self.xc, self.yc, self.zc, realmeshsize)

        # Create all the points for the circle
        points = []
        for i in range(0, self.distribution):
            angle = 2 * np.pi / self.distribution * i
            p = Point(self.xc+self.radius*math.cos(angle), self.yc+self.radius *
                      math.sin(angle), self.zc, realmeshsize)
            points.append(p)
        # Add the first point last for continuity when creating the arcs
        points.append(points[0])

        # Create arcs between two neighbouring points to create a circle
        self.arcCircle_list = [
            gmsh.model.geo.addCircleArc(
                points[i].tag,
                center.tag,
                points[i+1].tag,
            )
            for i in range(0, self.distribution)
        ]

        # Remove the duplicated points generated by the arcCircle
        gmsh.model.geo.synchronize()
        gmsh.model.geo.removeAllDuplicates()

    def close_loop(self):
        """
        Method to form a close loop with the current geometrical object

        Returns
        -------
        _ : int
            return the tag of the CurveLoop object
        """
        return gmsh.model.geo.addCurveLoop(self.arcCircle_list)

    def define_bc(self):
        """
        Method that define the marker of the circle
        for the boundary condition
        -------
        """

        self.bc = gmsh.model.addPhysicalGroup(self.dim, self.arcCircle_list)
        self.physical_name = gmsh.model.setPhysicalName(
            self.dim, self.bc, "farfield")

    def rotation(self, angle, origin, axis):
        """
        Method to rotate the object Circle
        ...

        Parameters
        ----------
        angle : float
            angle of rotation in rad
        origin : tuple
            tuple of point (x,y,z) which is the origin of the rotation
        axis : tuple
            tuple of point (x,y,z) which represent the axis of rotation
        """
        [
            gmsh.model.geo.rotate(
                [(self.dim, arccircle)],
                *origin,
                *axis,
                angle,
            )
            for arccircle in self.arcCircle_list
        ]

    def translation(self, vector):
        """
        Method to translate the object Circle
        ...

        Parameters
        ----------
        direction : tuple
            tuple of point (x,y,z) which represent the direction of the translation
        """
        [
            gmsh.model.geo.translate([(self.dim, arccircle)], *vector)
            for arccircle in self.arcCircle_list
        ]


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

    def __init__(self, xc, yc, z, dx, dy, mesh_size):

        self.xc = xc
        self.yc = yc
        self.z = z

        self.dx = dx
        self.dy = dy

        self.mesh_size = mesh_size
        self.dim = 1
        # Generate the 4 corners of the rectangle
        self.points = [
            Point(self.xc - self.dx / 2, self.yc -
                  self.dy / 2, z, self.mesh_size),
            Point(self.xc + self.dx / 2, self.yc -
                  self.dy / 2, z, self.mesh_size),
            Point(self.xc + self.dx / 2, self.yc +
                  self.dy / 2, z, self.mesh_size),
            Point(self.xc - self.dx / 2, self.yc +
                  self.dy / 2, z, self.mesh_size),
        ]
        gmsh.model.geo.synchronize()

        # Generate the 4 lines of the rectangle
        self.lines = [
            Line(self.points[0], self.points[1]),
            Line(self.points[1], self.points[2]),
            Line(self.points[2], self.points[3]),
            Line(self.points[3], self.points[0]),
        ]

        gmsh.model.geo.synchronize()

    def close_loop(self):
        """
        Method to form a close loop with the current geometrical object

        Returns
        -------
        _ : int
            return the tag of the CurveLoop object
        """
        return CurveLoop(self.lines).tag

    def define_bc(self):
        """
        Method that define the different markers of the rectangle for the boundary condition
        self.lines[0] => wall_bot
        self.lines[1] => outlet
        self.lines[2] => wall_top
        self.lines[3] => inlet
        -------
        """

        self.bc_in = gmsh.model.addPhysicalGroup(
            self.dim, [self.lines[3].tag], tag=-1)
        gmsh.model.setPhysicalName(self.dim, self.bc_in, "inlet")

        self.bc_out = gmsh.model.addPhysicalGroup(
            self.dim, [self.lines[1].tag])
        gmsh.model.setPhysicalName(self.dim, self.bc_out, "outlet")

        self.bc_wall = gmsh.model.addPhysicalGroup(
            self.dim, [self.lines[0].tag, self.lines[2].tag]
        )
        gmsh.model.setPhysicalName(self.dim, self.bc_wall, "wall")

        self.bc = [self.bc_in, self.bc_out, self.bc_wall]

    def rotation(self, angle, origin, axis):
        """
        Method to rotate the object Rectangle
        ...

        Parameters
        ----------
        angle : float
            angle of rotation in rad
        origin : tuple
            tuple of point (x,y,z) which is the origin of the rotation
        axis : tuple
            tuple of point (x,y,z) which represent the axis of rotation
        """
        [line.rotation(angle, origin, axis) for line in self.lines]

    def translation(self, vector):
        """
        Method to translate the object Rectangle
        ...

        Parameters
        ----------
        direction : tuple
            tuple of point (x,y,z) which represent the direction of the translation
        """
        [line.translation(vector) for line in self.lines]


class Airfoil:
    """
    A class to represent and airfoil as a CurveLoop object formed with lines

    ...

    Attributes
    ----------
    point_cloud : list(list(float))
        List of points forming the airfoil in the order,
        each point is a list containing in the order
        its position x,y,z
    mesh_size : float
        attribute given for the class Point, Note that a mesh size larger
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

    def gen_skin(self):
        """
        Method to generate the line forming the foil, Only call this function when the points
        of the airfoil are in their final position
        -------
        """
        self.lines = [
            Line(self.points[i], self.points[i + 1])
            for i in range(-1, len(self.points) - 1)
        ]
        self.lines_tag = [line.tag for line in self.lines]

    def close_loop(self):
        """
        Method to form a close loop with the current geometrical object

        Returns
        -------
        _ : int
            return the tag of the CurveLoop object
        """
        return CurveLoop(self.lines).tag

    def define_bc(self):
        """
        Method that define the marker of the airfoil for the boundary condition
        -------
        """

        self.bc = gmsh.model.addPhysicalGroup(self.dim, self.lines_tag)
        gmsh.model.setPhysicalName(self.dim, self.bc, self.name)

    def rotation(self, angle, origin, axis):
        """
        Method to rotate the object CurveLoop
        ...

        Parameters
        ----------
        angle : float
            angle of rotation in rad
        origin : tuple
            tuple of point (x,y,z) which is the origin of the rotation
        axis : tuple
            tuple of point (x,y,z) which represent the axis of rotation
        """
        [point.rotation(angle, origin, axis) for point in self.points]

    def translation(self, vector):
        """
        Method to translate the object CurveLoop
        ...

        Parameters
        ----------
        direction : tuple
            tuple of point (x,y,z) which represent the direction of the translation
        """
        [point.translation(vector) for point in self.points]


class AirfoilSpline:
    """
    A class to represent and airfoil as a CurveLoop object formed with Splines
    ...

    Attributes
    ----------
    point_cloud : list(list(float))
        List of points forming the airfoil in the order,
        each point is a list containing in the order
        its position x,y,z
    mesh_size : float
        attribute given for the class Point, (Note that a mesh size larger
        than the resolution given by the cloud of points
        will not be taken into account --> Not implemented)
    name : str
        name of the marker that will be associated to the airfoil
        boundary condition
    """

    def __init__(self, point_cloud, mesh_size,  name="airfoil"):

        self.name = name
        self.dim = 1
        self.mesh_size = mesh_size

        # Generate Points object from the point_cloud
        self.points = [
            Point(point_cord[0], point_cord[1], point_cord[2], mesh_size)
            for point_cord in point_cloud
        ]

        # Find leading and trailing edge location
        # in space
        self.le = min(self.points, key=attrgetter("x"))
        self.te = max(self.points, key=attrgetter("x"))
        # in the list of point
        self.te_indx = self.points.index(self.te)
        self.le_indx = self.points.index(self.le)

        # Check if the airfoil end in a single point, or with two different points (vertical of each other)
        vertical = False
        # If two (in the end) are so close in coordinate x, they are vertical and not just neighbouring point (examples below)
        # Just need to check if the one before or after and then label them correctly
        if self.points[self.te_indx-1].x > self.te.x-0.0001:
            te_up_indx = self.te_indx-1
            te_down_indx = self.te_indx
            vertical = True
        elif self.points[self.te_indx+1].x > self.te.x-0.0001:
            te_up_indx = self.te_indx
            te_down_indx = self.te_indx+1
            vertical = True

        # If end with two points, add one point in the prolongation of the curves to get pointy edge
        if vertical:
            # Compute the prolongation of the last segment and their meetpoint : it will be the new point
            x, y, z, w = self.points[te_up_indx].x, self.points[
                te_up_indx].y, self.points[te_down_indx].x, self.points[te_down_indx].y
            a, b, c, d = x - self.points[te_up_indx-1].x, y-self.points[te_up_indx -
                                                                        1].y, z-self.points[te_down_indx+1].x, w-self.points[te_down_indx+1].y
            #
            # We have that (x,y) are the coordinates of te_up and (z,w) the coordinates of te_down
            # p1 is the point before te_up and p2 the point after te_down
            #      \
            #       . p1
            #        \ vector from p1 to (x,y) is (a,b)
            #         \
            #          . (x,y)
            #  p2
            #  .----->.  . <- want to compute this point (which will be our new te)
            #       (z,w)
            #   vector from p2 to (z,w) is (c,d)
            #

            nothing = False
            # We compute mu: solution from the system (x,y)+lambda(a,b)=(z,w)+mu(c,d) that gives us the intersection point
            if b*c-a*d != 0:
                mu = (b*(x-z)+a*(w-y))/(b*c-a*d)
            else:
                # only happens with vr7b and vr8b (parallel edges so no solutions)
                mu = 10000000
                # will be treated in the else

            # Now to be coherent, we want the pointy edge to have a x coordinate between te.x and 0.1 further
            if z+mu*c <= self.te.x + 0.1 and z+mu*c > self.te.x:
                new = Point(z+mu*c, w+mu*d, 0, self.mesh_size)

            # If not, it can be in the wrong direction (like with oaf095) or absurdly far (like with hh02), and so we constrain it
            # (happens with roughly 40 airfoils, most because not well discretized)

            # First we take off the ones in this case (new would be so close) are the one not well coded with two really close horizontally points (like s2091). So we just don't do anything
            elif z+mu*c > self.te.x-0.001 and z+mu*c <= self.te.x:
                nothing = True
            else:
                # if too far or behind, we take the point p in the middle of (x,y) and (z,w), and add the vector mean of (a,b) and (c,d) until we reach 1.05 (or te +0.05 to be precise)
                px, py = (x+z)/2, (y+w)/2
                e, f = (a+c)/2, (b+d)/2
                lambd = (self.te.x + 0.05-px)/e
                new = Point(self.te.x + 0.05, py+lambd*f, 0, self.mesh_size)

            if not nothing:
                # Now insert the point in th list of points and change the index for te to be the new point
                self.points.insert(te_down_indx, new)
                self.te = new
                self.te_indx = te_down_indx

    def gen_skin(self):
        """
        Method to generate the three splines forming the foil, Only call this function when the points
        of the airfoil are in their final position
        -------
        """
        # Find the first point after 0.049 in the upper band lower spline
        debut = True
        for p in self.points:
            if p.x > 0.049 and debut:
                k1 = self.points.index(p)
                debut = False
            if p.x <= 0.049 and not debut:
                k2 = self.points.index(p)-1
                break

        # create a spline from the up middle point to the trailing edge (up part)
        self.upper_spline = Spline(
            self.points[k1: self.te_indx + 1])

        # create a spline from the trailing edge to the up down point (down part)
        self.lower_spline = Spline(
            self.points[self.te_indx:k2+1]
        )

        # Create a spline for the front part of the airfoil
        self.front_spline = Spline(self.points[k2:]+self.points[:k1+1])

        return k1, k2

    def gen_skin_struct(self, k1, k2):
        """
        Method to generate the two splines forming the foil for structural mesh, Only call this function when the points
        of the airfoil are in their final position
        -------
        """
        # create a spline from the up middle point to the trailing edge (up part)
        self.upper_spline = Spline(
            self.points[k1: self.te_indx + 1])

        # create a spline from the trailing edge to the up down point (down part)
        self.lower_spline = Spline(
            self.points[self.te_indx:k2+1]
        )
        return self.upper_spline, self.lower_spline

    def close_loop(self):
        """
        Method to form a close loop with the current geometrical object

        Returns
        -------
        _ : int
            return the tag of the CurveLoop object
        """
        return CurveLoop([self.upper_spline, self.lower_spline, self.front_spline]).tag

    def define_bc(self):
        """
        Method that define the marker of the airfoil for the boundary condition
        -------
        """

        self.bc = gmsh.model.addPhysicalGroup(
            self.dim, [self.upper_spline.tag,
                       self.lower_spline.tag, self.front_spline.tag]
        )
        gmsh.model.setPhysicalName(self.dim, self.bc, self.name)

    def rotation(self, angle, origin, axis):
        """
        Method to rotate the object AirfoilSpline
        ...

        Parameters
        ----------
        angle : float
            angle of rotation in rad
        origin : tuple
            tuple of point (x,y,z) which is the origin of the rotation
        axis : tuple
            tuple of point (x,y,z) which represent the axis of rotation
        """
        [point.rotation(angle, origin, axis) for point in self.points]
        gmsh.model.geo.synchronize()

    def translation(self, vector):
        """
        Method to translate the object AirfoilSpline
        ...

        Parameters
        ----------
        direction : tuple
            tuple of point (x,y,z) which represent the direction of the translation
        """
        [point.translation(vector) for point in self.points]


class PlaneSurface:
    """
    A class to represent the PlaneSurface geometrical object of gmsh

    ...

    Attributes
    ----------
    geom_objects : list(geom_object)
        List of geometrical object able to form closedloop,
        First the object will be closed in ClosedLoop
        the first curve loop defines the exterior contour; additional curve loop
        define holes in the surface domaine

    """

    def __init__(self, geom_objects):

        self.geom_objects = geom_objects
        # close_loop() will form a close loop object and return its tag
        self.tag_list = [geom_object.close_loop()
                         for geom_object in self.geom_objects]
        self.dim = 2

        # create the gmsh object and store the tag of the geometric object
        self.tag = gmsh.model.geo.addPlaneSurface(self.tag_list)

    def define_bc(self):
        """
        Method that define the domain marker of the surface
        -------
        """
        self.ps = gmsh.model.addPhysicalGroup(self.dim, [self.tag])
        gmsh.model.setPhysicalName(self.dim, self.ps, "fluid")


def outofbounds(airfoil, box, radius, blthick):
    """Method that checks if the boundary layer or airfoil goes out of the box/farfield
    (which is a problem for meshing later)

    Args:
        cloud_points (AirfoilSpline):
            The AirfoilSpline containing the points
        box (string):
            the box arguments received by the parser (float x float)
        radius (float):
            radius of the farfield
        blthick (float):
            total thickness of the boundary layer (0 for mesh without bl)
    """
    if box:
        length, width = [float(value) for value in box.split("x")]
        # Compute the min and max values in the x and y directions
        minx = min(p.x for p in airfoil.points)
        maxx = max(p.x for p in airfoil.points)
        miny = min(p.y for p in airfoil.points)
        maxy = max(p.y for p in airfoil.points)
        # Check :
        # If the max-0.5 (which is just recentering the airfoil in 0)+bl thickness value is bigger than length/2 --> too far right.
        # Same with min and left. (minx & maxx should be 0 & 1 but we recompute to be sure)
        # Same in y.
        if abs(maxx-0.5)+abs(blthick) > length/2 or abs(minx-0.5)+abs(blthick) > length/2 or abs(maxy)+abs(blthick) > width/2 or abs(miny)+abs(blthick) > width/2:
            print("\nThe boundary layer or airfoil is bigger than the box, exiting")
            print(
                "You must change the boundary layer parameters or choose a bigger box\n")
            sys.exit()
    else:
        # Compute the further from (0.5,0,0) a point is (norm of (x-0.5,y))
        maxr = math.sqrt(max((p.x-0.5)*(p.x-0.5)+p.y*p.y
                             for p in airfoil.points))
        # Check if furthest + bl is bigger than radius
        if maxr+abs(blthick) > radius:
            print("\nThe boundary layer or airfoil is bigger than the circle, exiting")
            print(
                "You must change the boundary layer parameters or choose a bigger radius\n")
            sys.exit()


class CType:
    """
    A class to represent a C-type structured mesh.
    """

    def __init__(self, airfoil_spline, dx_trail, dy, mesh_size, height, ratio, aoa):
        z = 0
        self.airfoil_spline = airfoil_spline

        self.dx_trail = dx_trail
        self.dy = dy

        self.mesh_size = mesh_size
        # Because all the computations are based on the mesh size at the trailing edge which is the biggest accross the whole airfoil, we take it bigger
        # so that the mesh size is right mostly on the middle of the airfoil
        mesh_size_end = mesh_size*2
        self.mesh_size_end = mesh_size_end

        self.firstheight = height
        self.ratio = ratio
        self.aoa = aoa

        # First compute k1 & k2 the first coordinate after 0.041 (up & down)
        debut = True
        for p in airfoil_spline.points:
            if p.x > 0.041 and debut:
                k1 = airfoil_spline.points.index(p)
                debut = False
            if p.x <= 0.041 and not debut:
                k2 = airfoil_spline.points.index(p)-1
                break

        upper_spline_back, lower_spline_back = self.airfoil_spline.gen_skin_struct(
            k1, k2)
        self.le_upper_point = airfoil_spline.points[k1]
        self.le_lower_point = airfoil_spline.points[k2]

        # Create the new front spline (from the two front parts)
        upper_points_front = airfoil_spline.points[:k1+1]
        lower_points_front = airfoil_spline.points[k2:]
        points_front = lower_points_front + upper_points_front
        points_front_tag = [point.tag for point in points_front]
        spline_front = gmsh.model.geo.addSpline(points_front_tag)
        self.spline_front, self.upper_spline_back, self.lower_spline_back = spline_front, upper_spline_back, lower_spline_back

        # Create points on the outside domain (& center point)
        #        p1                      p2                p3
        #        -------------------------------------------
        #       / \                      |                 |
        #      /    \                    |                 |
        #     /       \                  |                 |       *1 : dx_wake
        #    /        /00000000000000\   |                 |       *2 : dy (total height)
        #   (        (0000000(p0)0000000)|-----------------| p4
        #    \        \00000000000000/   |       *1        |*2
        #     \       /                  |                 |
        #      \    /                    |                 |
        #       \ /                      |                 |
        #        ------------------------------------------- p5
        #       p7                       p6

        # We want the line to p1 to be perpendicular to airfoil for better boundary layer, and same for p2
        # We compute the normal to the line linking the points before and after our point of separation (point[k1]&point[k2])
        xup, yup, xdown, ydown = airfoil_spline.points[k1].x, airfoil_spline.points[
            k1].y,  airfoil_spline.points[k2].x, airfoil_spline.points[k2].y
        xupbefore, yupbefore, xupafter, yupafter = airfoil_spline.points[
            k1-1].x, airfoil_spline.points[k1-1].y, airfoil_spline.points[k1+1].x, airfoil_spline.points[k1+1].y
        xdownbefore, ydownbefore, xdownafter, ydownafter = airfoil_spline.points[
            k2-1].x, airfoil_spline.points[k2-1].y, airfoil_spline.points[k2+1].x, airfoil_spline.points[k2+1].y
        directionupx, directionupy, directiondownx, directiondowny = yupbefore - \
            yupafter, xupafter-xupbefore, ydownafter-ydownbefore, xdownbefore-xdownafter
        # As the points coordinates we get are not rotated, we need to change it by hand
        cos, sin = math.cos(aoa), math.sin(aoa)
        directionupx, directionupy, directiondownx, directiondowny = cos*directionupx-sin * directionupy, sin * \
            directionupx+cos * directionupy, cos*directiondownx-sin * \
            directiondowny, sin*directiondownx+cos * directiondowny
        xup, yup, xdown, ydown = cos*xup-sin*yup, sin*xup + \
            cos*yup, cos*xdown-sin*ydown, sin*xdown+cos*ydown

        # Then compute where the line in this direction going from point[k1] intersect the line y=dy/2 (i.e. the horizontal line where we want L1)
        pt1x, pt1y, pt7x, pt7y = xup+(dy/2-yup)/directionupy*directionupx, dy/2, xdown + \
            (0-dy/2-ydown)/directiondowny*directiondownx, -dy/2
        # Check that the line doesn't go "back" or "too far", and constrain it to go between le-0.05*dy and le-3.5
        pt1x = max(min(pt1x, airfoil_spline.le.x-0.05*dy),
                   airfoil_spline.le.x-3.5)
        pt7x = max(min(pt7x, airfoil_spline.le.x-0.05*dy),
                   airfoil_spline.le.x-3.5)
        # Compute the center of the circle : we want a x coordinate of 0.5, and compute cy so that p1 and p7 are at same distance from the (0.5,cy)
        centery = (pt1y+pt7y)/2 + (0.5-(pt1x+pt7x)/2)/(pt1y-pt7y)*(pt7x-pt1x)

        # Create the 8 points we wanted
        self.points = [
            Point(0.5, centery, z, self.mesh_size_end),  # 0
            Point(pt1x, pt1y, z, self.mesh_size_end),  # 1
            Point(self.airfoil_spline.te.x, self.dy /
                  2, z, self.mesh_size_end),  # 2
            Point(self.airfoil_spline.te.x + self.dx_trail,
                  self.dy / 2, z, self.mesh_size_end),  # 3
            Point(self.airfoil_spline.te.x + self.dx_trail,
                  self.airfoil_spline.te.y, z, self.mesh_size_end),  # 4
            Point(self.airfoil_spline.te.x + self.dx_trail, -
                  self.dy / 2, z, self.mesh_size_end),  # 5
            Point(self.airfoil_spline.te.x, -
                  self.dy / 2, z, self.mesh_size_end),  # 6
            Point(pt7x, pt7y, z, self.mesh_size_end),  # 7
        ]

        # Create all the lines : outside and surface separation
        self.lines = [
            Line(self.le_upper_point, self.points[1]),  # 0
            Line(self.points[1], self.points[2]),  # 1
            Line(self.points[2], self.points[3]),  # 2
            Line(self.points[3], self.points[4]),  # 3
            Line(self.points[4], self.points[5]),  # 4
            Line(self.points[5], self.points[6]),  # 5
            Line(self.points[6], self.points[7]),  # 6
            Line(self.points[7], self.le_lower_point),  # 7
            Line(self.airfoil_spline.te, self.points[2]),  # 8
            Line(self.airfoil_spline.te, self.points[6]),  # 9
            Line(self.points[4], self.airfoil_spline.te),  # 10
        ]

        # Circle arc for C shape at the front
        self.circle_arc = gmsh.model.geo.addCircleArc(
            self.points[7].tag, self.points[0].tag, self.points[1].tag)

        # planar surfaces for structured grid are named from A-E
        # straight lines are numbered from L0 to L10
        #
        #        --------------------------------------
        #       /   \              L1   |      L2     |
        # circ /     \L0      B         |       C     |
        #     /  A    \               L8|             |L3     *1 : dx_wake
        #    /        /00000000000000\  |     *1      |       *2 : dy
        #   (       (000000000000000000)|-------------|
        #    \        \00000000000000/  |      L10    |*2
        #     \       /                 |             |
        #      \     /L7      E       L9|    D        |L4
        #       \   /                   |             |
        #        --------------------------------------
        #                      L6               L5

        # Now we compute all of the parameters to have smooth mesh around mesh size

        # HEIGHT
        # Compute number of nodes needed to have the desired first layer height (=nb of layer (N) +1)
        # Computation : we have that dy/2 is total height, and let a=first layer height
        # dy/2= a + a*ratio + a*ratio^2 + ... + a*ratio^(N-1) and rearrange to get the following equation
        nb_points_y = 3+int(math.log(1+dy/2/height*(ratio-1))/math.log(ratio))
        progression_y = ratio
        progression_y_inv = 1/ratio

        # WAKE
        # Set a progression to adapt slightly the wake (don't need as much precision further away from airfoil)
        progression_wake = 1/1.025
        progression_wake_inv = 1.025
        # Set number of points in x direction at wake to get desired meshsize on the one next to airfoil
        # (solve dx_trail = meshsize + meshsize*1.02 + meshsize*1.02^2 + ... + meshsize*1.02^(N-1) with N=nb of intervals)
        nb_points_wake = int(
            math.log(1+dx_trail*0.025/mesh_size_end)/math.log(1.025))+1

        # AIRFOIL CENTER
        # Set number of points on upper and lower part of airfoil. Want mesh size at the end (b) to be meshsizeend, and at the front (a) meshsizeend/coef to be more coherent with airfoilfront
        if mesh_size_end > 0.05:
            coeffdiv = 4
        elif mesh_size_end >= 0.03:
            coeffdiv = 3
        else:
            coeffdiv = 2
        a, b, l = mesh_size_end/coeffdiv, mesh_size_end, airfoil_spline.te.x
        # So compute ratio and nb of points accordingly: (solve l=a+a*r+a*r^2+a*r^(N-1) and a*r^(N-1)=b, and N=nb of intervals=nb of points-1)
        ratio_airfoil = (l-a)/(l-b)
        if l-b < 0:
            nb_airfoil = 3
        else:
            nb_airfoil = max(3, int(math.log(b/a)/math.log(ratio_airfoil))+2)

        # AIRFOIL FRONT
        # Now we can try to put the good number of point on the front to have a good mesh
        # First we estimate the length of the spline
        x, y, v, w = airfoil_spline.points[k1].x, airfoil_spline.points[
            k2].y, airfoil_spline.points[k1].x, airfoil_spline.points[k2].y
        c1, c2 = airfoil_spline.le.x, airfoil_spline.le.y
        estim_length = (math.sqrt((x-c1)*(x-c1)+(y-c2)*(y-c2)) +
                        math.sqrt((v-c1)*(v-c1)+(w-c2)*(w-c2)))+0.01
        # Compute nb of points if they were all same size, multiply par a factor (3) to have an okay number (and good when apply bump)
        nb_airfoil_front = max(
            4, int(estim_length/mesh_size_end*coeffdiv*3))+4

        # Now we set all the corresponding transfinite curve we need (with our coefficient computed before)

        # transfinite curve A
        gmsh.model.geo.mesh.setTransfiniteCurve(
            self.lines[7].tag, nb_points_y, "Progression", progression_y_inv)  # same for plane E
        if mesh_size_end < 0.04:
            gmsh.model.geo.mesh.setTransfiniteCurve(
                spline_front, nb_airfoil_front, "Bump", 12)
        else:
            gmsh.model.geo.mesh.setTransfiniteCurve(
                spline_front, nb_airfoil_front, "Bump", 7)
        gmsh.model.geo.mesh.setTransfiniteCurve(
            self.lines[0].tag, nb_points_y, "Progression", progression_y)  # same for plane B
        # Because of different length of L1 and L6, need a bigger coefficient when point 1 and 7 are really far (coef is 1 when far and 9 when close)
        coef = 8/3*(pt1x+pt7x)/2+31/3
        if dy < 6:
            coef = (coef+2)/3
        if dy <= 3:
            coef = (coef + 2)/3
        gmsh.model.geo.mesh.setTransfiniteCurve(
            self.circle_arc, nb_airfoil_front, "Bump", 1/coef)

        # transfinite curve B
        gmsh.model.geo.mesh.setTransfiniteCurve(
            self.lines[8].tag, nb_points_y, "Progression", progression_y)  # same for plane C
        gmsh.model.geo.mesh.setTransfiniteCurve(
            upper_spline_back.tag, nb_airfoil, "Progression", ratio_airfoil)
        # For L1, we adapt depeding if the curve is much longer than 1 or not (if goes "far in the front")
        if pt1x < airfoil_spline.le.x-1.5:
            gmsh.model.geo.mesh.setTransfiniteCurve(
                self.lines[1].tag, nb_airfoil, "Progression", 1/ratio_airfoil)
        elif pt1x < airfoil_spline.le.x-0.7:
            gmsh.model.geo.mesh.setTransfiniteCurve(
                self.lines[1].tag, nb_airfoil, "Progression", 1/math.sqrt(ratio_airfoil))
        else:
            gmsh.model.geo.mesh.setTransfiniteCurve(
                self.lines[1].tag, nb_airfoil)

        # transfinite curve C
        gmsh.model.geo.mesh.setTransfiniteCurve(
            self.lines[2].tag, nb_points_wake, "Progression", progression_wake_inv)
        gmsh.model.geo.mesh.setTransfiniteCurve(
            self.lines[3].tag, nb_points_y, "Progression", progression_y_inv)
        gmsh.model.geo.mesh.setTransfiniteCurve(
            self.lines[10].tag, nb_points_wake, "Progression", progression_wake)  # same for plane D

        # transfinite curve D
        gmsh.model.geo.mesh.setTransfiniteCurve(
            self.lines[9].tag, nb_points_y, "Progression", progression_y)  # same for plane E
        gmsh.model.geo.mesh.setTransfiniteCurve(
            self.lines[4].tag, nb_points_y, "Progression", progression_y)
        gmsh.model.geo.mesh.setTransfiniteCurve(
            self.lines[5].tag, nb_points_wake, "Progression", progression_wake)

        # transfinite curve E
        gmsh.model.geo.mesh.setTransfiniteCurve(
            lower_spline_back.tag, nb_airfoil, "Progression", 1/ratio_airfoil)
        # For L6, we adapt depeding if the line is much longer than 1 or not (if goes "far in the front")
        if pt7x < airfoil_spline.le.x-1.5:
            gmsh.model.geo.mesh.setTransfiniteCurve(
                self.lines[6].tag, nb_airfoil, "Progression", ratio_airfoil)
        elif pt7x < airfoil_spline.le.x-0.4:
            gmsh.model.geo.mesh.setTransfiniteCurve(
                self.lines[6].tag, nb_airfoil, "Progression", math.sqrt(ratio_airfoil))
        else:
            gmsh.model.geo.mesh.setTransfiniteCurve(
                self.lines[6].tag, nb_airfoil)

        # Now we add the surfaces

        # transfinite surface A (forces structured mesh)
        c1 = gmsh.model.geo.addCurveLoop(
            [self.lines[7].tag, spline_front, self.lines[0].tag, - self.circle_arc])
        surf1 = gmsh.model.geo.addPlaneSurface([c1])
        gmsh.model.geo.mesh.setTransfiniteSurface(surf1)

        # transfinite surface B
        c2 = gmsh.model.geo.addCurveLoop(
            [self.lines[0].tag, self.lines[1].tag, - self.lines[8].tag, - upper_spline_back.tag])
        surf2 = gmsh.model.geo.addPlaneSurface([c2])
        gmsh.model.geo.mesh.setTransfiniteSurface(surf2)

        # transfinite surface C
        c3 = gmsh.model.geo.addCurveLoop(
            [self.lines[8].tag, self.lines[2].tag, self.lines[3].tag, self.lines[10].tag])
        surf3 = gmsh.model.geo.addPlaneSurface([c3])
        gmsh.model.geo.mesh.setTransfiniteSurface(surf3)

        # transfinite surface D
        c4 = gmsh.model.geo.addCurveLoop(
            [- self.lines[9].tag, - self.lines[10].tag, self.lines[4].tag, self.lines[5].tag])
        surf4 = gmsh.model.geo.addPlaneSurface([c4])
        gmsh.model.geo.mesh.setTransfiniteSurface(surf4)

        # transfinite surface E
        c5 = gmsh.model.geo.addCurveLoop(
            [self.lines[7].tag, - lower_spline_back.tag, self.lines[9].tag, self.lines[6].tag])
        surf5 = gmsh.model.geo.addPlaneSurface([c5])
        gmsh.model.geo.mesh.setTransfiniteSurface(surf5)
        self.curveloops = [c1, c2, c3, c4, c5]
        self.surfaces = [surf1, surf2, surf3, surf4, surf5]

        # Lastly, recombine surface to create quadrilateral elements
        gmsh.model.geo.mesh.setRecombine(2, surf1, 90)
        gmsh.model.geo.mesh.setRecombine(2, surf2, 90)
        gmsh.model.geo.mesh.setRecombine(2, surf3, 90)
        gmsh.model.geo.mesh.setRecombine(2, surf4, 90)
        gmsh.model.geo.mesh.setRecombine(2, surf5, 90)

    def define_bc(self):
        """
        Method that define the domain marker of the surface, the airfoil and the farfield
        -------
        """

        # Airfoil
        self.bc = gmsh.model.addPhysicalGroup(
            1, [self.upper_spline_back.tag,
                self.lower_spline_back.tag, self.spline_front]
        )
        gmsh.model.setPhysicalName(1, self.bc, "airfoil")

        # Farfield
        self.bc = gmsh.model.addPhysicalGroup(1, [self.lines[1].tag, self.lines[2].tag,
                                                  self.lines[3].tag, self.lines[4].tag, self.lines[5].tag, self.lines[6].tag, self.circle_arc])
        gmsh.model.setPhysicalName(1, self.bc, "farfield")

        # Surface
        self.bc = gmsh.model.addPhysicalGroup(2, self.surfaces)
        gmsh.model.setPhysicalName(2, self.bc, "fluid")
