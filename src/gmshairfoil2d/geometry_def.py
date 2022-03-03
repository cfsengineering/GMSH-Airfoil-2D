#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  3 12:02:13 2022

@author: tony
"""
#------------------------------------------------------------------------------
import gmsh
import numpy as np
#This script contain the definition of geometrical objects needed to build
#the geometry and latter the mesh
class Point:
  def __init__(self, x, y, z, meshSize):
    #position in space
    self.x = x
    self.y = y
    self.z = z
    self.meshSize = meshSize
    #point object are of dim 0
    self.dim = 0 
    #create the gmsh object and store the tag of the geometric object
    self.tag = gmsh.model.occ.addPoint(self.x,self.y,self.z,self.meshSize)
    
class Line:
  def __init__(self, startTag, endTag):
    #tag of the two points forming the line
    self.startTag = startTag
    self.endTag = endTag
    #line object are of dim 1
    self.dim = 1
    #create the gmsh object and store the tag of the geometric object
    self.tag = gmsh.model.occ.addLine(self.startTag,self.endTag )

class CurveLoop:
  def __init__(self,startTag, endTag):
    #tag of the starting and ending line
    self.startTag = startTag
    self.endTag = endTag
    #number of line in the curve
    self.nbLine = endTag-startTag +1
    #Assuming that the Line between the start and end tag form a closed loop
    self.curveTags = np.linspace(self.startTag,self.endTag,self.nbLine).astype(int)
    #CurveLoop object are of dim 1
    self.dim = 1
    #create the gmsh object and store the tag of the geometric object
    self.tag = gmsh.model.occ.addCurveLoop(self.curveTags)
    
class PlaneSurface:
  def __init__(self,curveloopTags):
    #A plane surface defined by one or more curve loops tags
    #The first curve loop defines the exterior contour; additional curve loop
    #define holes in the surface domaine
    if type(curveloopTags) == int: #if only one curve loop is used
        self.curveloopTags = [curveloopTags]#put in a array
    else:
        self.curveloopTags = curveloopTags # it is already an array
    #PlaneSurface object are of dim 2
    self.dim = 2
    #create the gmsh object and store the tag of the geometric object
    self.tag = gmsh.model.occ.addPlaneSurface(self.curveloopTags)
#end
#------------------------------------------------------------------------------