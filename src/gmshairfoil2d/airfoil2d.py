from geometry_def import Point, Line, CurveLoop
import gmsh
from operator import attrgetter


class Airfoil:
    """
    Generate an CurveLoop formed with the cloud of points
    representing the airfoil. Note that a Mesh size larger
    than the resolution given by the cloud of points
    will not be taken into account
    """

    def __init__(self, point_cloud, mesh_size):
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


class AirfoilSpline:
    """
    Constructing the foil using Spline which result in
    a better meshing possibility when the foil consist
    of only few points
    """

    def __init__(self, point_cloud, mesh_size):
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
        self.tag = self.tag = gmsh.model.occ.addCurveLoop(
            [self.upper_spline_tag, self.lower_spline_tag]
        )
