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
        attribute given for the class Point,Note that a mesh size larger
        than the resolution given by the cloud of points
        will not be taken into account
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

        # Just a check that the points start with the (0,0,0) point (or min), bc then we assume that are sorted
        if self.le_indx != 0:
            print("Error in the points numeration")
            sys.exit()

        # Check if the airfoil end in a single point, or with two different points (vertical of each other)
        vertical = False
        # If both are so close to one, they are vertical and not just neighbouring point (bc te is always 1)
        # Just need to check if the one before or after and then label them correctly
        if self.points[self.te_indx-1].x > 0.9999:
            te_up_indx = self.te_indx-1
            te_down_indx = self.te_indx
            vertical = True
        elif self.points[self.te_indx+1].x > 0.9999:
            te_up_indx = self.te_indx
            te_down_indx = self.te_indx+1
            vertical = True

        t = True
        # If end with two points, add one point in the prolongation of the curves to get pointy edge
        if vertical and t:
            # Compute the prolongation of the last segment and their meetpoint : it will be the new point
            x, y, z, w = self.points[te_up_indx].x, self.points[
                te_up_indx].y, self.points[te_down_indx].x, self.points[te_down_indx].y
            a, b, c, d = x - self.points[te_up_indx-1].x, y-self.points[te_up_indx -
                                                                        1].y, z-self.points[te_down_indx+1].x, w-self.points[te_down_indx+1].y
            print("x,y,z,w", x, y, z, w, "a,b,c,d", a, b, c, d)
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

            # We compute mu: solution from the system (x,y)+lambda(a,b)=(z,w)+mu(c,d) that gives us the intersection point
            if b*c-a*d != 0:
                mu = (b*(x-z)+a*(w-y))/(b*c-a*d)
            else:
                mu = 0.01
                # TODO choose what to do in this case (as parallel can be treated as the ones <1 I think)
            if z+mu*c <= 1.1 and z+mu*c > 1:
                new = Point(z+mu*c, w+mu*d, 0, self.mesh_size)
            # Check that it is not in the wrong direction (like with oaf095), and otherwise constrain it
            elif z+mu*c <= 1:
                '''
                print("Was <1")
                flag = Point(2, 1, 0, self.mesh_size)
                for i in range(2, 20):
                    a, b, c, d = x - self.points[te_up_indx-i].x, y-self.points[te_up_indx -
                                                                                i].y, z-self.points[te_down_indx+i].x, w-self.points[te_down_indx+i].y
                    mu = (b*(x-z)+a*(w-y))/(b*c-a*d)
                    print(i, z+mu*c, w+mu*d)
                    if z+mu*c <= 1.05 and z+mu*c > 1:
                        new = Point(z+mu*c, w+mu*d, 0, self.mesh_size)
                        break
                    else:
                        if i == 19:
                            new = Point(1.05, -0.04, 0, self.mesh_size)
                            # TODO : change la coord en y et fix tout ca
                '''
                new = Point(z+mu*c, w+mu*d, 0, self.mesh_size)
            # Check that it is not absurdly far (like with hh02), and otherwise constrain it
            else:
                # if too far, we take the point p in the middle of (x,y) and (z,w), and add the vector mean of (a,b) and (c,d) until we reach 1.05
                px, py = (x+z)/2, (y+w)/2
                e, f = (a+c)/2, (b+d)/2
                lambd = (1.05-px)/e
                new = Point(1.05, py+lambd*f, 0, self.mesh_size)
                # TODO fix that for weird come back
                # new = Point(z+mu*c, w+mu*d, 0, self.mesh_size)

            # Now insert the point in th list of points and change the index for te to be the new point
            self.points.insert(te_down_indx, new)
            self.te = new
            self.te_indx = te_down_indx

    def gen_skin(self):
        """
        Method to generate the two splines forming the foil, Only call this function when the points
        of the airfoil are in their final position
        -------
        """
        # create a spline from the leading edge to the trailing edge (up part)

        self.upper_spline = Spline(
            self.points[self.le_indx: self.te_indx + 1])

        # create a spline from the trailing edge to the leading edge (down part)
        self.lower_spline = Spline(
            self.points[self.te_indx:] +
            self.points[: (self.le_indx) + 1]  # just le which is coord 0
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
        return CurveLoop([self.upper_spline, self.lower_spline]).tag

    def define_bc(self):
        """
        Method that define the marker of the airfoil for the boundary condition
        -------
        """

        self.bc = gmsh.model.addPhysicalGroup(
            self.dim, [self.upper_spline.tag, self.lower_spline.tag]
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
            radius of the farfield (when needed)
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

    def __init__(self, airfoil_spline, dx_lead, dx_trail, dy, ext_mesh_size, height, ratio):
        z = 0
        self.airfoil_spline = airfoil_spline

        self.dx_lead = dx_lead
        self.dx_trail = dx_trail
        self.dy = dy

        self.mesh_size = ext_mesh_size

        # print("airfoil le", airfoil_spline.le.x, airfoil_spline.le.y)

        # The k smallest element for structured grid inlet line. First compute k & k2 (want first coordinate after 0.031)
        for p in airfoil_spline.points:
            if p.x > 0.031:
                k = airfoil_spline.points.index(p)
                break
        l = len(airfoil_spline.points)
        for i in range(l-1, -1, -1):
            if airfoil_spline.points[i].x > 0.031:
                k2 = l-i
                break

        # Then split the splines, and order by coordinate x (not needed imo but well)
        upper_spline, lower_spline = self.airfoil_spline.gen_skin()
        self.le_upper_point = sorted(
            upper_spline.point_list, key=lambda p: p.x)[k]
        self.le_lower_point = sorted(
            lower_spline.point_list, key=lambda p: p.x)[k2]
        upper_spline_front, upper_spline_back = gmsh.model.geo.splitCurve(
            upper_spline.tag, [self.le_upper_point.tag])
        lower_spline_back, lower_spline_front = gmsh.model.geo.splitCurve(
            lower_spline.tag, [self.le_lower_point.tag])

        # Create the new front spline
        upper_points_front = sorted(
            upper_spline.point_list, key=lambda p: p.x)[:k+1]
        lower_points_front = sorted(
            lower_spline.point_list, key=lambda p: p.x)[:k2+1]
        lower_points_front.reverse()
        points_front = lower_points_front[:-1] + upper_points_front
        points_front_tag = [point.tag for point in points_front]
        spline_front = gmsh.model.geo.addSpline(points_front_tag)

        # Create points on the outside domain (& center point)
        self.points = [
            Point(0.5, 0, z, self.mesh_size),
            Point(self.airfoil_spline.le.x - self.dx_lead,
                  self.dy / 2, z, self.mesh_size),
            Point(self.airfoil_spline.te.x, self.dy / 2, z, self.mesh_size),
            Point(self.airfoil_spline.te.x + self.dx_trail,
                  self.dy / 2, z, self.mesh_size),
            Point(self.airfoil_spline.te.x + self.dx_trail,
                  self.airfoil_spline.te.y, z, self.mesh_size),
            Point(self.airfoil_spline.te.x + self.dx_trail, -
                  self.dy / 2, z, self.mesh_size),
            Point(self.airfoil_spline.te.x, - self.dy / 2, z, self.mesh_size),
            Point(self.airfoil_spline.le.x - self.dx_lead, -
                  self.dy / 2, z, self.mesh_size),
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
        circle_arc = gmsh.model.geo.addCircleArc(
            self.points[7].tag, self.points[0].tag, self.points[1].tag)

        # planar surfaces for structured grid are named from A-E
        # straight lines are numbered from L0 to L10
        #
        #        ------------------------------------
        #       /   \              L1    |      L2  |
        # circ /     \L0      B          |    C     |       *1 : dx_leading
        #     /  A    \                L8|          |L3     *2 : dx_wake
        #    /    *1  /00000000000000\   |   *2     |       *3 : dy
        #   (    ----(000000000000000000)|----------|
        #    \        \00000000000000/   |      L10 |*3
        #     \       /                  |          |
        #      \     /L7      E        L9|    D     |L4
        #       \   /                    |          |
        #        ------------------------------------
        #                      L6               L5

        # Compute number of nodes needed to have the desired first layer height (=nb of layer +1)(on half height)
        # int(self.dy / 2 / self.mesh_size) + 1 //// old way
        nb_points_y = 3+int(math.log(1+dy/2/height*(ratio-1))/math.log(ratio))
        progression_y = ratio
        progression_y_inv = 1/ratio

        # set number of points in x direction at wake
        nb_points_wake = int(self.dx_trail / self.mesh_size) + 1
        progression_wake = 0.98
        progression_wake_inv = 1/0.98

        # set number of points on upper and lower part of airfoil
        # Why this formula : we estimate we want the heught at 1/4 to be like the neighbour. As the neighbour is transfinite, mesh size is roughly 1/2 total mesh_size
        nb_airfoil = int((1+dx_lead/4)/ext_mesh_size*2)

        # set number of points on front of airfoil
        # First compute radius of circle
        r = math.sqrt(dy*dy/4+(0.5+dx_lead)*(0.5+dx_lead))
        # Then we compute the estimated angle of the front part
        theta = 2 * math.atan(dy/(1+2*dx_lead))
        # Now same, we assume we want the same length at 1/4 of the length, as the other is multiplied by 2 to be with the transfinite, we mult by 1.4 to be reasonable
        # (2 pi r/4)*(theta/(2 pi))/extmeshsize, then +1 bc speaks of nb of nodes
        nb_airfoil_front = max(4, int((r/4*theta)/ext_mesh_size*1.4)+1)
        # transfinite curve A
        gmsh.model.geo.mesh.setTransfiniteCurve(
            self.lines[7].tag, nb_points_y, "Progression", progression_y_inv)  # same for plane E
        gmsh.model.geo.mesh.setTransfiniteCurve(spline_front, nb_airfoil_front)
        gmsh.model.geo.mesh.setTransfiniteCurve(
            self.lines[0].tag, nb_points_y, "Progression", progression_y)  # same for plane B
        gmsh.model.geo.mesh.setTransfiniteCurve(circle_arc, nb_airfoil_front)

        # transfinite curve B
        gmsh.model.geo.mesh.setTransfiniteCurve(self.lines[1].tag, nb_airfoil)
        gmsh.model.geo.mesh.setTransfiniteCurve(
            self.lines[8].tag, nb_points_y, "Progression", progression_y)  # same for plane C
        gmsh.model.geo.mesh.setTransfiniteCurve(
            upper_spline_back, nb_airfoil, "Bump", 0.2)

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
            lower_spline_back, nb_airfoil, "Bump", 0.2)
        gmsh.model.geo.mesh.setTransfiniteCurve(self.lines[6].tag, nb_airfoil)

        # transfinite surface A (forces structured mesh)
        gmsh.model.geo.addCurveLoop(
            [self.lines[7].tag, spline_front, self.lines[0].tag, - circle_arc], 1)
        gmsh.model.geo.addPlaneSurface([1], 1)
        gmsh.model.geo.mesh.setTransfiniteSurface(1)

        # transfinite surface B
        gmsh.model.geo.addCurveLoop(
            [self.lines[0].tag, self.lines[1].tag, - self.lines[8].tag, - upper_spline_back], 2)
        gmsh.model.geo.addPlaneSurface([2], 2)
        gmsh.model.geo.mesh.setTransfiniteSurface(2)

        # transfinite surface C
        gmsh.model.geo.addCurveLoop(
            [self.lines[8].tag, self.lines[2].tag, self.lines[3].tag, self.lines[10].tag], 3)
        gmsh.model.geo.addPlaneSurface([3], 3)
        gmsh.model.geo.mesh.setTransfiniteSurface(3)

        # transfinite surface D
        gmsh.model.geo.addCurveLoop(
            [- self.lines[9].tag, - self.lines[10].tag, self.lines[4].tag, self.lines[5].tag], 4)
        gmsh.model.geo.addPlaneSurface([4], 4)
        gmsh.model.geo.mesh.setTransfiniteSurface(4)

        # transfinite surface E
        gmsh.model.geo.addCurveLoop(
            [self.lines[7].tag, - lower_spline_back, self.lines[9].tag, self.lines[6].tag], 5)
        gmsh.model.geo.addPlaneSurface([5], 5)
        gmsh.model.geo.mesh.setTransfiniteSurface(5)

        # recombine surface to create quadrilateral elements
        gmsh.model.geo.mesh.setRecombine(2, 1, 90)
        gmsh.model.geo.mesh.setRecombine(2, 2, 90)
        gmsh.model.geo.mesh.setRecombine(2, 3, 90)
        gmsh.model.geo.mesh.setRecombine(2, 4, 90)
        gmsh.model.geo.mesh.setRecombine(2, 5, 90)
