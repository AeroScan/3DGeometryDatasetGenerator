from .base_surfaces import BaseSurface
from lib.AsGeometryOCCWrapper.curves.curve_factory import CurveFactory

import numpy as np

class Revolution(BaseSurface):

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

    def _getCurveObject(self, curve):
        return CurveFactory.getPrimitiveObject(type=curve.GetType(), shape=curve, mesh={})

    ## Missing fix orientation part 
    def fromShape(self, shape):
        surface = shape.AxeOfRevolution()
        curve = shape.BasisCurve()
        self.location = list(surface.Location().Coord())
        self.z_axis = list(surface.Direction().Coord())
        self.curve = self._getCurveObject(curve=curve)

    def fromMesh(self, mesh):
        super().fromMesh(mesh=mesh)

    def toDict(self):
        features = super().toDict()
        features['type'] = Revolution.primitiveType()
        features['location'] = self.location
        features['z_axis'] = self.z_axis
        features['curve'] = CurveFactory.getDictFromPrimitive(primitive=self.curve)

        return features

    def normalize(self, R=np.eye(3,3), t=np.zeros(3), s=1.):
        self.curve = self.curve.normalize(R=R, t=t, s=s)

        self.location = R @ self.location
        self.z_axis = R @ self.z_axis

        self.location += t

        self.location = self.location.tolist()
        self.z_axis = self.z_axis.tolist()
