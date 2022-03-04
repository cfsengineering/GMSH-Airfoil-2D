#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  3 12:02:13 2022

@author: tony
"""

import gmsh
import numpy as np
import math

# This script contain the definition of geometrical objects needed to build
# the geometry and latter the mesh


class Point:
    def __init__(self, x, y, z, mesh_size):
        # position in space
        self.x = x
        self.y = y
        self.z = z
        self.mesh_size = mesh_size
        self.dim = 0
        # create the gmsh object and store the tag of the geometric object
        self.tag = gmsh.model.occ.addPoint(self.x, self.y, self.z, self.mesh_size)


class Line:
    def __init__(self, start_point, end_point):
        # tag of the two points forming the line
        self.start_point = start_point
        self.end_point = end_point
        self.dim = 1
        # create the gmsh object and store the tag of the geometric object
        self.tag = gmsh.model.occ.addLine(self.start_point.tag, self.end_point.tag)


class CurveLoop:
    def __init__(self, line_list):
        # Line list must be in the order of the wanted CurveLoop and closed
        self.line_list = line_list
        self.tag_list = []
        # generate the Lines tag list to folow
        self.tag_list = [line.tag for line in self.line_list]
        # create the gmsh object and store the tag of the geometric object
        self.tag = gmsh.model.occ.addCurveLoop(self.tag_list)


class Circle:
    def __init__(self, xc, yc, zc, radius, mesh_size=None):
        # Position of the disk center
        self.xc = xc
        self.yc = yc
        self.zc = zc
        self.radius = radius
        self.mesh_size = mesh_size
        self.dim = 1
        if mesh_size is None:
            # create the Circle and directly create the corresponding curveloop
            self.tag = gmsh.model.occ.addCurveLoop(
                gmsh.model.occ.addCircle(self.xc, self.yc, self.zc, self.radius)
            )
        else:
            # create a structured arcCricle to merge in one curveloop
            self.distribution = math.floor((np.pi * 2 * self.radius) / self.mesh_size)
            self.arcCircle_list = [
                gmsh.model.occ.addCircle(
                    self.xc,
                    self.yc,
                    self.zc,
                    self.radius,
                    angle1=2 * np.pi / self.distribution * i,
                    angle2=2 * np.pi / self.distribution * (1 + i),
                )
                for i in range(0, self.distribution)
            ]
            self.tag = gmsh.model.occ.addCurveLoop(self.arcCircle_list)


class Rectangle:
    def __init__(self, xc, yc, z, dx, dy, mesh_size):
        self.xc = xc
        self.yc = yc
        self.z = z
        self.dx = dx
        self.dy = dy
        self.mesh_size = mesh_size
        self.dim = 1
        # generate 4 points, 4 lines
        self.points = [
            Point(self.xc - self.dx / 2, self.yc - self.dy / 2, z, self.mesh_size),
            Point(self.xc + self.dx / 2, self.yc - self.dy / 2, z, self.mesh_size),
            Point(self.xc + self.dx / 2, self.yc + self.dy / 2, z, self.mesh_size),
            Point(self.xc - self.dx / 2, self.yc + self.dy / 2, z, self.mesh_size),
        ]
        self.lines = [
            Line(self.points[0], self.points[1]),
            Line(self.points[1], self.points[2]),
            Line(self.points[2], self.points[3]),
            Line(self.points[3], self.points[0]),
        ]
        # Create the corresponding curveloop
        self.tag = CurveLoop(self.lines).tag


class PlaneSurface:
    """
    A plane surface defined by one or more curve loops tags
    The first curve loop defines the exterior contour; additional curve loop
    define holes in the surface domaine
    """

    def __init__(self, curveLoop_list):
        self.curveLoop_list = curveLoop_list
        self.tag_list = [curveLoop.tag for curveLoop in self.curveLoop_list]
        self.dim = 2
        # create the gmsh object and store the tag of the geometric object
        self.tag = gmsh.model.occ.addPlaneSurface(self.tag_list)
