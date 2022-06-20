from abc import abstractmethod
import numpy as np

class BaseCurveFeature:
    @staticmethod
    def primitiveType():
        return 'BaseCurve'

    def __init__(self, shape = None, mesh: dict = None):
        self.sharp = None
        self.vert_indices = None
        self.vert_parameters = None
        if shape is not None:
            self.fromShape(shape=shape)
        if mesh is not None:
            self.fromMesh(mesh=mesh)

    @abstractmethod
    def fromShape(self, shape):
        pass

    def fromMesh(self, mesh: dict) -> None:
        self.sharp = mesh['sharp'] if 'sharp' in mesh.keys() else True
        self.vert_indices = mesh['vert_indices'] if 'vert_indices' in mesh.keys() else []
        self.vert_parameters = mesh['vert_parameters'] if 'vert_parameters' in mesh.keys() else []

    def toDict(self) -> dict:
        features = {}
        features['sharp'] = self.sharp
        features['vert_indices'] = self.vert_indices
        features['vert_parameters'] = self.vert_parameters

        return features
    
    @abstractmethod
    def normalize(self, R=np.eye(3,3), t=np.zeros(3), s=1.):
        pass