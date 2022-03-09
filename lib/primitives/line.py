from lib.primitives.base_curve_feature import BaseCurveFeature

from tools import gpXYZ2List

class Line(BaseCurveFeature):

    @staticmethod
    def primitiveType():
        return 'Line'
    
    def __init__(self, shape):
        super().__init__()
        self.shape = shape.Line()
        self.location = None
        self.direction = None
        self.fromShape()

    def getLocation(self):
        return gpXYZ2List(self.shape.Location())
    
    def getDirection(self):
        return gpXYZ2List(self.shape.Direction())

    def fromShape(self):
        self.location = self.getLocation()
        self.direction = self.getDirection()
