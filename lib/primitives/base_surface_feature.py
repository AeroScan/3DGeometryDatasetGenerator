from abc import abstractmethod
import numpy as np

class BaseSurfaceFeature:

    def __init__(self):
        self.vert_indices = None
        self.vert_parameters = None
        self.face_indices = None

    def fromMesh(self, mesh: dict) -> None:
        self.vert_indices = mesh['vert_indices'] if 'vert_indices' in mesh.keys() else []
        self.vert_parameters = mesh['vert_parameters'] if 'vert_parameters' in mesh.keys() else []
        self.face_indices = mesh['face_indices'] if 'face_indices' in mesh.keys() else []
    
    def toDict(self) -> dict:
        features = {}
        features['vert_indices'] = self.vert_indices
        features['vert_parameters'] = self.vert_parameters
        features['face_indices'] = self.face_indices
        
        return features
    
    @abstractmethod
    def normalize(self, R=np.eye(3,3), t=np.zeros(3), s=1.):
        pass