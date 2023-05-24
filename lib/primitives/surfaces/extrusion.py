from .base_surface import BaseSurface
from lib.primitives.curves.curve_factory import CurveFactory

import numpy as np

class Extrusion(BaseSurface):

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

    def _getCurveObject(self, curve):
        return CurveFactory.getPrimitiveObject(type=curve.GetType(), shape=curve, mesh={})

    ## Missing fix orientation part 
    def fromShape(self, shape):
        surface = shape
        curve = shape.BasisCurve()
        self.direction = list(surface.Direction().Coord())
        self.curve = self._getCurveObject(curve=curve)

    def fromMesh(self, mesh):
        super().fromMesh(mesh=mesh)
    
    def toDict(self):
        features = super().toDict()
        features['type'] = Extrusion.primitiveType()
        features['direction'] = self.direction
        features['curve'] = CurveFactory.getDictFromPrimitive(primitive=self.curve)

        return features

    def normalize(self, R=np.eye(3,3), t=np.zeros(3), s=1.):
        self.curve = self.curve.normalize(R=R, t=t, s=s)

        self.direction = R @ self.direction

        self.direction = self.direction.tolist()