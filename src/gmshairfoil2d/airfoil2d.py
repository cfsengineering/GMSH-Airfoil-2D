from geometry_def import Point, Line, CurveLoop
from operator import attrgetter
import gmsh
import numpy as np


class Airfoil:
    """
    Generate an CurveLoop formed with the cloud of points
    representing the airfoil. Note that a Mesh size larger
    than the resolution given by the cloud of points
    will not be taken into account
    """

    def __init__(self, point_cloud, mesh_size, name="airfoil"):
        self.name = name
        self.dim = 1
        # Generate Points object from the point_cloud
        self.points = [
            Point(point_cord[0], point_cord[1], point_cord[2], mesh_size)
            for point_cord in point_cloud
        ]

        self.lines = [
            Line(self.points[i], self.points[i + 1])
            for i in range(-1, len(self.points) - 1)
        ]

        self.CurveLoop = CurveLoop(self.lines)
        self.tag = self.CurveLoop.tag
        # Define BC
        gmsh.model.occ.synchronize()
        self.bc = gmsh.model.addPhysicalGroup(self.dim, self.CurveLoop.tag_list)
        gmsh.model.setPhysicalName(self.dim, self.bc, self.name)


class AirfoilSpline:
    """
    Constructing the foil using Spline which result in
    a better meshing possibility when the foil consist
    of only few points
    """

    def __init__(self, point_cloud, mesh_size, name="airfoil"):
        self.name = name
        self.dim = 1
        # Generate Points object from the point_cloud
        self.points = [
            Point(point_cord[0], point_cord[1], point_cord[2], mesh_size)
            for point_cord in point_cloud
        ]
        self.le = min(self.points, key=attrgetter("x"))
        self.te = max(self.points, key=attrgetter("x"))
        self.points_tag = [point.tag for point in self.points]
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

        # Define BC
        gmsh.model.occ.synchronize()
        self.bc = gmsh.model.addPhysicalGroup(
            self.dim, [self.upper_spline_tag, self.lower_spline_tag]
        )
        gmsh.model.setPhysicalName(self.dim, self.bc, self.name)


def NACA_4_digit_geom(alpha, first_d, second_d, third_d, fourth_d, nb_points=100):

    # parameter from NACA DIGIT
    theta_line = np.linspace(0, np.pi, nb_points)
    x_line = 0.5 * (1 - np.cos(theta_line))
    m = first_d / 100
    p = second_d / 10
    t = (third_d * 10 + fourth_d) / 100
    # camber line front of the airfoil (befor p)
    x_line_front = x_line[x_line < p]
    # camber line back of the airfoil (after p)
    x_line_back = x_line[x_line >= p]
    # total camber line
    if p != 0:
        y_c = np.concatenate(
            (
                (m / p ** 2) * (2 * p * x_line_front - x_line_front ** 2),
                (m / (1 - p) ** 2)
                * (1 - 2 * p + 2 * p * x_line_back - x_line_back ** 2),
            ),
            axis=0,
        )
        dyc_dx = np.concatenate(
            (
                (2 * m / p ** 2) * (p - x_line_front),
                (2 * m / (1 - p) ** 2) * (p - x_line_back),
            ),
            axis=0,
        )
    else:
        y_c = (0 * x_line_front, 0 * x_line_back)
        dyc_dx = y_c

    # thickness line
    y_t = (
        t
        / 0.2
        * (
            0.2969 * x_line ** 0.5
            - 0.126 * x_line
            - 0.3516 * x_line ** 2
            + 0.2843 * x_line ** 3
            + -0.1036 * x_line ** 4
        )
    )
    if p != 0:
        theta = np.arctan(dyc_dx)
        # upper and lower surface
        x_u = x_line - y_t * np.sin(theta)
        y_u = y_c + y_t * np.cos(theta)
        x_l = x_line + y_t * np.sin(theta)
        y_l = y_c - y_t * np.cos(theta)
    else:
        # upper and lower surface
        x_u = x_line
        y_u = y_t
        x_l = x_line
        y_l = -y_t
    # concatenate the upper and lower
    final_x = np.concatenate((x_u[:-1], np.flip(x_l[1:])), axis=0)
    final_y = np.concatenate((y_u[:-1], np.flip(y_l[1:])), axis=0)

    # create the 3d points cloud
    points_cloud = []
    nb_pts_final = len(final_x)

    for k in range(0, nb_pts_final):
        points_cloud.append([final_x[k], final_y[k], 0])
    return points_cloud
