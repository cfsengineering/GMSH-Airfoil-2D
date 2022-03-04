from geometry_def import Point, Line, CurveLoop
import gmsh

gmsh.initialize()


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
