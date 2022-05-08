from lib.primitives.base_surface_feature import BaseSurfaceFeature

from OCC.Core.TColgp import TColgp_Array2OfPnt
from OCC.Core.TColStd import TColStd_Array1OfReal, TColStd_Array2OfReal

import numpy as np

class BSplineSurface(BaseSurfaceFeature):

    @staticmethod
    def primitiveType():
        return 'BSpline'

    @staticmethod
    def getPrimitiveParams():
        return ['type', 'u_rational', 'v_rational', 'u_closed', 'v_closed', 'continuity',
                'u_degree', 'v_degree', 'poles', 'u_knots', 'v_knots', 'weights']
    
    def __init__(self, shape=None, mesh: dict = None):
        super().__init__()
        self.u_rational = None
        self.v_rational = None
        self.u_closed = None
        self.v_closed = None
        self.continuity = None
        self.u_degree = None
        self.v_degree = None
        self.poles = None
        self.u_knots = None
        self.v_knots = None
        self.weights = None
        if shape is not None:
            self.fromShape(shape=shape)
        if mesh is not None:
            self.fromMesh(mesh=mesh)
    
    def _getPoles(self, shape):
        k_degree = TColgp_Array2OfPnt(1, shape.NbUPoles(), 1, shape.NbVPoles())
        shape.Poles(k_degree)
        cols = []
        for i in range(k_degree.ColLength()):
            rows = []
            for j in range(k_degree.RowLength()):
                rows.append(list(k_degree.Value(i+1, j+1).Coord()))
            cols.append(rows)
        return cols

    def _getUKnots(self, shape):
        u_knots = []
        for _, knots in enumerate(shape.UKnots()):
            u_knots.append(knots)
        return u_knots

    def _getVKnots(self, shape):
        v_knots = []
        for _, knots in enumerate(shape.VKnots()):
            v_knots.append(knots)
        return v_knots

    def _getWeights(self, shape):
        k_degree = TColStd_Array2OfReal(1, shape.NbUPoles(), 1, shape.NbVPoles())
        shape.Weights(k_degree)
        cols = []
        for i in range(k_degree.ColLength()):
            rows = []
            for j in range(k_degree.RowLength()):
                rows.append(k_degree.Value(i+1, j+1))
            cols.append(rows)
        return cols

    def fromShape(self, shape):
        shape = shape.BSpline()
        print(f'NbUKnots: {shape.NbUKnots()}')
        print(f'NbVKnots: {shape.NbVKnots()}')
        self.u_rational = shape.IsURational()
        self.v_rational = shape.IsVRational()
        self.u_closed = shape.IsUClosed()
        self.v_closed = shape.IsVClosed()
        self.continuity = shape.Continuity()
        self.u_degree = shape.UDegree()
        self.v_degree = shape.VDegree()
        self.poles = self._getPoles(shape=shape)
        self.u_knots = self._getUKnots(shape=shape)
        self.v_knots = self._getVKnots(shape=shape)
        print(f'Length UKnots: {len(self.u_knots)}')
        print(f'Length VKnots: {len(self.v_knots)}')
        self.weights = self._getWeights(shape=shape)
    
    def fromMesh(self, mesh):
        super().fromMesh(mesh)
        
    def toDict(self):
        features = super().toDict()
        features['type'] = BSplineSurface.primitiveType()
        features['u_rational'] = self.u_rational
        features['v_rational'] = self.v_rational
        features['u_closed'] = self.u_closed
        features['v_closed'] = self.v_closed
        features['continuity'] = self.continuity
        features['u_degree'] = self.u_degree
        features['v_degree'] = self.v_degree
        features['poles'] = self.poles
        features['u_knots'] = self.u_knots
        features['v_knots'] = self.v_knots
        features['weights'] = self.weights

        return features

    def normalize(self, R=np.eye(3,3), t=np.zeros(3), s=1.):
        pass