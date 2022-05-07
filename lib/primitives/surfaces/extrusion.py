from lib.primitives.base_surface_feature import BaseSurfaceFeature
from lib.primitives.curve_factory import CurveFactory

class Extrusion(BaseSurfaceFeature):

    @staticmethod
    def primitiveType():
        return 'Extrusion'

    @staticmethod
    def getPrimitiveParams():
        return ['direction', 'curve', 'vert_indices', 'vert_parameters', 'face_indices']

    def __init__(self, shape=None, mesh: dict = None):
        super().__init__()
        self.direction = None
        self.curve = None
        if shape is not None:
            self.fromShape(shape=shape)
        if mesh is not None:
            self.fromMesh(mesh=mesh)

    def _getCurveInfo(self, curve):
        c = CurveFactory.getPrimitiveObject(type=curve.GetType(), shape=curve, mesh={})
        return CurveFactory.getDictFromPrimitive(primitive=c)

    def fromShape(self, shape):
        surface = shape
        curve = shape.BasisCurve()
        self.direction = list(surface.Direction().Coord())
        self.curve = self._getCurveInfo(curve=curve)

    def fromMesh(self, mesh):
        super().fromMesh(mesh=mesh)
    
    def toDict(self):
        features = super().toDict()
        features['type'] = Extrusion.primitiveType()
        features['direction'] = self.direction
        features['curve'] = self.curve

        return features