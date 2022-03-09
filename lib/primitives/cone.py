from tools import gpXYZ2List

from lib.primitives.base_surface_feature import BaseSurfaceFeature

class Cone(BaseSurfaceFeature):
    
    @staticmethod
    def primitiveType():
        return 'Cone'

    def __init__(self, shape):
        super().__init__()
        self.shape = shape.Cone()
        self.location = None
        self.x_axis = None
        self.y_axis = None
        self.z_axis = None
        self.coefficients = None
        self.radius = None
        self.angle = None
        self.apex = None
        self.fromShape()
    
    def getLocation(self):
        return gpXYZ2List(self.shape.Location())

    def getAxis(self):
        x_axis = gpXYZ2List(self.shape.XAxis().Direction())
        y_axis = gpXYZ2List(self.shape.YAxis().Direction())
        z_axis = gpXYZ2List(self.shape.Axis().Direction())
        return [x_axis, y_axis, z_axis]

    def getCoefficients(self):
        return list(self.shape.Coefficients())

    def getRadius(self):
        return self.shape.RefRadius()

    def getAngle(self):
        return self.shape.SemiAngle()
    
    def getApex(self):
        return gpXYZ2List(self.shape.Apex())

    def fromShape(self):
        self.location = self.getLocation()
        self.x_axis = self.getAxis()[0]
        self.y_axis = self.getAxis()[1]
        self.z_axis = self.getAxis()[2]
        self.coefficients = self.getCoefficients()
        self.radius = self.getRadius()
        self.angle = self.getAngle()
        self.apex = self.getApex()