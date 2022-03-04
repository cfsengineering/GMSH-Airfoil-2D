#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  3 12:02:13 2022

@author: tony
"""

import gmsh

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
        for line in line_list:
            self.tag_list.append(line.tag)
        # create the gmsh object and store the tag of the geometric object
        self.tag = gmsh.model.occ.addCurveLoop(self.tag_list)


class Circle:
    def __init__(self, xc, yc, zc, radius):
        # Position of the disk center
        self.xc = xc
        self.yc = yc
        self.zc = zc
        self.radius = radius
        self.dim = 1
        # create the gmsh object and store the tag of the geometric object
        self.tag = gmsh.model.occ.addCircle(self.xc, self.yc, self.zc, self.radius)


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
