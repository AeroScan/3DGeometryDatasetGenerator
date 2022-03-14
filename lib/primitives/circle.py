from lib.primitives.base_curve_feature import BaseCurveFeature

from lib.tools import gpXYZ2List

class Circle(BaseCurveFeature):

    @staticmethod
    def primitiveType():
        return 'Circle'
    
    def __init__(self):
        super().__init__()
        self.location = None
        self.x_axis = None
        self.y_axis = None
        self.z_axis = None
        self.radius = None

    def fromShape(self, shape):
        shape = shape.Circle()
        self.location = gpXYZ2List(shape.Location())
        self.x_axis = gpXYZ2List(shape.XAxis().Direction())
        self.y_axis = gpXYZ2List(shape.YAxis().Direction())
        self.z_axis = gpXYZ2List(shape.Axis().Direction())
        self.radius = shape.Radius()

    def fromMesh(self, mesh):
        super().fromMesh(mesh)

    def toDict(self):
        features = super().toDict()
        features['type'] = Circle.primitiveType()
        features['location'] = self.location
        features['x_axis'] = self.x_axis
        features['y_axis'] = self.y_axis
        features['z_axis'] = self.z_axis
        features['radius'] = self.radius

        return features