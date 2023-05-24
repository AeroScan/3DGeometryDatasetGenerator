import numpy as np

from .base_curve import BaseCurve
from lib.tools import gpXYZ2List

class Line(BaseCurve):

    @staticmethod
    def primitiveType():
        return 'Line'

    @staticmethod
    def getPrimitiveParams():
        return ['type', 'location', 'direction', 'sharp', 'vert_indices', 'vert_parameters']
    
    def __init__(self, shape = None, mesh: dict = None):
        super().__init__()
        self.location = None
        self.direction = None
        if shape is not None:
            self.fromShape(shape=shape)
        if mesh is not None:
            self.fromMesh(mesh=mesh)

    def fromShape(self, shape):
        shape = self.geometryFromShape(shape)
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
    
    def normalize(self, R=np.eye(3,3), t=np.zeros(3), s=1.):
        self.location = R @ self.location
        self.direction = R @ self.direction
        
        self.location += t
        
        self.location *= s

        self.location = self.location.tolist()
        self.direction = self.direction.tolist()