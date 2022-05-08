from lib.primitives.base_curve_feature import BaseCurveFeature

from OCC.Core.TColStd import TColStd_Array1OfReal
from OCC.Core.TColgp import TColgp_Array1OfPnt

import numpy as np

class BSplineCurve(BaseCurveFeature):

    @staticmethod
    def primitiveType():
        return 'BSpline'
    
    @staticmethod
    def getPrimitiveParams():
        return ['type', 'rational', 'closed', 'continuity', 'degree', 'poles', 'knots', 'weights', 'vert_indices', 'vert_parameters']

    def __init__(self, shape=None, mesh: dict = None):
        super().__init__()
        self.rational = None
        self.closed = None
        self.continuity = None
        self.degree = None
        self.poles = None
        self.knots = None
        self.weights = None
        if shape is not None:
            self.fromShape(shape=shape)
        if mesh is not None:
            self.fromMesh(mesh=mesh)

    def _getPoles(self, shape):
        k_degree = TColgp_Array1OfPnt(1, shape.NbPoles())
        shape.Poles(k_degree)
        points = []
        for i in range(k_degree.Length()):
            points.append(list(k_degree.Value(i+1).Coord()))
        return points

    def _getKnots(self, shape):
        k_degree = TColStd_Array1OfReal(1, shape.NbPoles() + shape.Degree() + 1)
        shape.KnotSequence(k_degree)
        knots = []
        for i in range(k_degree.Length()):
            knots.append(k_degree.Value(i+1))
        return knots

    def _getWeights(self, shape):
        k_degree = TColStd_Array1OfReal(1, shape.NbPoles())
        shape.Weights(k_degree)
        weights = []
        for i in range(k_degree.Length()):
            weights.append(k_degree.Value(i+1))
        return weights

    def fromShape(self, shape):
        shape = shape.BSpline()
        self.rational = shape.IsRational()
        self.closed = shape.IsClosed()
        self.continuity = shape.Continuity()
        self.degree = shape.Degree()
        self.poles = self._getPoles(shape=shape)
        self.knots = self._getKnots(shape=shape)
        self.weights = self._getWeights(shape=shape)

    def fromMesh(self, mesh):
        super().fromMesh(mesh)

    def toDict(self):
        features = super().toDict()
        features['type'] = BSplineCurve.primitiveType()
        features['rational'] = self.rational
        features['closed'] = self.closed
        features['continuity'] = self.continuity
        features['degree'] = self.degree
        features['poles'] = self.poles
        features['knots'] = self.knots
        features['weights'] = self.weights

        return features

    def normalize(self, R=np.eye(3,3), t=np.zeros(3), s=1.):
        pass