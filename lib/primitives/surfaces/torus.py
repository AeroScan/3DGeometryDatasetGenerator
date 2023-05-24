import numpy as np

from lib.tools import gpXYZ2List
from .base_surface import BaseSurface

class Torus(BaseSurface):
    
    @staticmethod
    def primitiveType():
        return 'Torus'

    @staticmethod
    def getPrimitiveParams():
        return ['type', 'location', 'x_axis', 'y_axis', 'z_axis', 'max_radius', 'min_radius', 'vert_indices', 'vert_parameters', 'face_indices']

    def __init__(self, shape = None, mesh: dict = None):
        super().__init__()
        self.location = None
        self.x_axis = None
        self.y_axis = None
        self.z_axis = None
        self.max_radius = None
        self.min_radius = None
        if shape is not None:
            self.fromShape(shape=shape)
        if mesh is not None:
            self.fromMesh(mesh=mesh)

    def fromShape(self, shape):
        shape = self.geometryFromShape(shape)
        self.location = gpXYZ2List(shape.Location())
        self.x_axis = gpXYZ2List(shape.XAxis().Direction())
        self.y_axis = gpXYZ2List(shape.YAxis().Direction())
        self.z_axis = gpXYZ2List(shape.Axis().Direction())
        self.max_radius = shape.MajorRadius()
        self.min_radius = shape.MinorRadius()

    def fromMesh(self, mesh):
        super().fromMesh(mesh)

    def toDict(self):
        features = super().toDict()
        features['type'] = Torus.primitiveType()
        features['location'] = self.location
        features['x_axis'] = self.x_axis
        features['y_axis'] = self.y_axis
        features['z_axis'] = self.z_axis
        features['max_radius'] = self.max_radius
        features['min_radius'] = self.min_radius

        return features
    
    def normalize(self, R=np.eye(3,3), t=np.zeros(3), s=1.):
        self.location = R @ self.location
        self.x_axis = R @ self.x_axis
        self.y_axis = R @ self.y_axis
        self.z_axis = R @ self.z_axis
        
        self.location += t

        self.location *= s
        self.max_radius *= s
        self.min_radius *= s

        self.location = self.location.tolist()
        self.x_axis = self.x_axis.tolist()
        self.y_axis = self.y_axis.tolist()
        self.z_axis = self.z_axis.tolist()