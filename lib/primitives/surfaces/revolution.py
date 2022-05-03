from lib.primitives.base_surface_feature import BaseSurfaceFeature
from lib.primitives.curve_factory import CurveFactory

class Revolution(BaseSurfaceFeature):

    @staticmethod
    def primitiveType():
        return 'Revolution'

    @staticmethod
    def getPrimitiveParams():
        return ['location', 'z_axis', 'curve', 'vert_indices', 'vert_parameters', 'face_indices']
    
    def __init__(self, shape=None, mesh: dict = None):
        super().__init__()
        self.location = None
        self.z_axis = None
        self.curve = None
        if shape is not None:
            self.fromShape(shape=shape)
        if mesh is not None:
            self.fromMesh(mesh=mesh)

    def _getCurveInfo(self, curve):
        c = CurveFactory.getPrimitiveObject(type=curve.GetType(), shape=curve, mesh={})
        return CurveFactory.getDictFromPrimitive(primitive=c)

    def fromShape(self, shape):
        surface = shape.AxeOfRevolution()
        curve = shape.BasisCurve()
        self.location = list(surface.Location().Coord())
        self.z_axis = list(surface.Direction().Coord())
        self.curve = self._getCurveInfo(curve=curve)

    def fromMesh(self, mesh):
        super().fromMesh(mesh=mesh)

    def toDict(self):
        features = super().toDict()
        features['type'] = Revolution.primitiveType()
        features['location'] = self.location
        features['z_axis'] = self.z_axis
        features['curve'] = self.curve

        return features
