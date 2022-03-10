from lib.primitives.base_curve_feature import BaseCurveFeature

from lib.tools import gpXYZ2List

class Circle(BaseCurveFeature):

    @staticmethod
    def primitiveType():
        return 'Circle'
    
    def __init__(self, shape, params=None):
        super().__init__()
        self.shape = shape.Circle()
        self.location = None
        self.x_axis = None
        self.y_axis = None
        self.z_axis = None
        self.radius = None
        self.fromShape()

    def getLocation(self):
        return gpXYZ2List(self.shape.Location())

    def getAxis(self):
        x_axis = gpXYZ2List(self.shape.XAxis().Direction())
        y_axis = gpXYZ2List(self.shape.YAxis().Direction())
        z_axis = gpXYZ2List(self.shape.Axis().Direction())

        return [x_axis, y_axis, z_axis]
    
    def getRadius(self):
        return self.shape.Radius()

    def fromShape(self):
        self.location = self.getLocation()
        self.x_axis = self.getAxis()[0]
        self.y_axis = self.getAxis()[1]
        self.z_axis = self.getAxis()[2]
        self.radius = self.getRadius()

    def toDict(self):
        features = super().toDict()
        features['type'] = Circle.primitiveType()
        features['location'] = self.location
        features['x_axis'] = self.x_axis
        features['y_axis'] = self.y_axis
        features['z_axix'] = self.z_axis
        features['radius'] = self.radius

        return features
        
        