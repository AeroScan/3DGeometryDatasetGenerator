import numpy as np
from lib.tools import gpXYZ2List

from lib.primitives.base_surface_feature import BaseSurfaceFeature

class Sphere(BaseSurfaceFeature):
    
    @staticmethod
    def primitiveType():
        return 'Sphere'

    def __init__(self, shape, params=None):
        super().__init__()
        self.shape = shape.Sphere()
        self.location = None
        self.x_axis = None
        self.y_axis = None
        self.z_axis = None
        self.coefficients = None
        self.radius = None
        self.fromShape(params)
    
    def getLocation(self):
        return gpXYZ2List(self.shape.Location())

    def getCoefficients(self):
        return list(self.shape.Coefficients())

    def getAxis(self):
        x_axis = np.array(gpXYZ2List(self.shape.XAxis().Direction()))
        y_axis = np.array(gpXYZ2List(self.shape.YAxis().Direction()))
        z_axis = np.cross(x_axis, y_axis)
        return [x_axis.tolist(), y_axis.tolist(), z_axis.tolist()]

    def getRadius(self):
        return self.shape.Radius()
    
    def fromShape(self, params):
        if params is not None:
            super().fromDict(params)
        self.location = self.getLocation()
        self.x_axis = self.getAxis()[0]
        self.y_axis = self.getAxis()[1]
        self.z_axis = self.getAxis()[2]
        self.coefficients = self.getCoefficients()
        self.radius = self.getRadius()