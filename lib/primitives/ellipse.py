from lib.primitives.base_curve_feature import BaseCurveFeature

from lib.tools import gpXYZ2List

class Ellipse(BaseCurveFeature):

    @staticmethod
    def primitiveType():
        return 'Ellipse'
    
    def __init__(self, shape, params=None):
        super().__init__()
        self.shape = shape.Ellipse()
        self.focus1 = None
        self.focus2 = None
        self.x_axis = None
        self.y_axis = None
        self.z_axis = None
        self.x_radius = None
        self.y_radius = None
        self.fromShape()

    def getFocus(self):
        return [gpXYZ2List(self.shape.Focus1()), gpXYZ2List(self.shape.Focus2())]

    def getAxis(self):
        x_axis = gpXYZ2List(self.shape.XAxis().Direction())
        y_axis = gpXYZ2List(self.shape.YAxis().Direction())
        z_axis = gpXYZ2List(self.shape.Axis().Direction())

        return [x_axis, y_axis, z_axis]

    def getRadius(self):
        return [self.shape.MajorRadius(), self.shape.MinorRadius()]

    def fromShape(self):
        self.focus1 = self.getFocus()[0]
        self.focus2 = self.getFocus()[1]
        self.x_axis = self.getAxis()[0]
        self.y_axis = self.getAxis()[1]
        self.z_axis = self.getAxis()[2]
        self.x_radius = self.getRadius()[0]
        self.y_radius = self.getRadius()[1]

    def toDict(self):
        features = super().toDict()
        features['type'] = Ellipse.primitiveType()
        features['focus1'] = self.focus1
        features['focus2'] = self.focus2
        features['x_axis'] = self.x_axis
        features['y_axis'] = self.y_axis
        features['z_axis'] = self.z_axis
        features['x_radius'] = self.x_radius
        features['y_radius'] = self.y_radius

        return features

    def updateWithMeshParams(self, params):
        super().fromDict(params)
        
        return True