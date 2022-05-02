from lib.primitives.base_surface_feature import BaseSurfaceFeature

from OCC.Core.TColgp import TColgp_Array2OfPnt
from OCC.Core.TColStd import TColStd_Array1OfReal, TColStd_Array2OfReal

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
        interval = TColgp_Array2OfPnt(1, shape.NbUPoles(), 1, shape.NbVPoles())
        """ Poles()
        Returns the poles of the B-spline surface.

        Raised if the length of P in the U and V direction is not equal to NbUpoles and NbVPoles.
        """
        shape.Poles(interval)
        cols = []
        for i in range(interval.ColLength()):
            rows = []
            for j in range(interval.RowLength()):
                rows.append(list(interval.Value(i+1, j+1).Coord()))
            cols.append(rows)
        return cols

    def _getKnots(self, shape, param: str):
        assert param == 'v' or param == 'u'
        if param == 'u':
            """ [1, NumberOfPoles + UDegree + 1] """
            interval = TColStd_Array1OfReal(1, shape.NbUPoles() + shape.UDegree() + 1)
            """ UKnotSequence()
            Returns the uknots sequence. In this sequence the knots with a multiplicity greater 
            than 1 are repeated. Example : Ku = {k1, k1, k1, k2, k3, k3, k4, k4, k4}. 
            """
            shape.UKnotSequence(interval)
        elif param == 'v':
            """ [1, NumberOfPoles + VDegree + 1] """
            interval = TColStd_Array1OfReal(1, shape.NbVPoles() + shape.VDegree() + 1)
            """ VKnotSequence()
            Returns the uknots sequence. In this sequence the knots with a multiplicity greater 
            than 1 are repeated. Example : Ku = {k1, k1, k1, k2, k3, k3, k4, k4, k4}. 
            """
            shape.VKnotSequence(interval)
        
        knots = []
        for i in range(interval.Length()):
            knots.append(interval.Value(i+1))
        return knots

    def _getWeights(self, shape):
        interval = TColStd_Array2OfReal(1, shape.NbUPoles(), 1, shape.NbVPoles())
        shape.Weights(interval)
        cols = []
        for i in range(interval.ColLength()):
            rows = []
            for j in range(interval.RowLength()):
                rows.append(interval.Value(i+1, j+1))
            cols.append(rows)
        return cols

    def fromShape(self, shape):
        shape = shape.BSpline()
        self.u_rational = shape.IsURational()
        self.v_rational = shape.IsVRational()
        self.u_closed = shape.IsUClosed()
        self.v_closed = shape.IsVClosed()
        self.continuity = shape.Continuity()
        self.u_degree = shape.UDegree()
        self.v_degree = shape.VDegree()
        self.poles = self._getPoles(shape=shape)
        self.u_knots = self._getKnots(shape=shape, param='u')
        self.v_knots = self._getKnots(shape=shape, param='v')
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