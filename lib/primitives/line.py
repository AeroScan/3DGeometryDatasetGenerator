from lib.primitives.base_curve_feature import BaseCurveFeature

from lib.tools import gpXYZ2List

class Line(BaseCurveFeature):

    @staticmethod
    def primitiveType():
        return 'Line'
    
    def __init__(self):
        self.location = None
        self.direction = None

    def fromShape(self, shape):
        shape = shape.Line()
        self.location = gpXYZ2List(shape.Location())
        self.direction = gpXYZ2List(shape.Direction())

    def fromMesh(self, mesh):
        super().fromMesh(mesh)

    def toDict(self):
        features = super().toDict()
        features['type'] = Line.primitiveType()
        features['location'] = self.location
        features['direction'] = self.direction

        return features