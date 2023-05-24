import numpy as np

from lib.tools import gpXYZ2List
from .base_surface import BaseSurface

class Plane(BaseSurface):

    @staticmethod
    def primitiveType():
        return 'Plane'

    @staticmethod
    def getPrimitiveParams():
        return ['type', 'location', 'normal', 'x_axis', 'y_axis', 'z_axis', 'coefficients', 'vert_indices', 'vert_parameters', 'face_indices']
    
    def __init__(self, shape = None, mesh: dict = None):
        super().__init__()
        self.location = None
        self.x_axis = None
        self.y_axis = None
        self.z_axis = None
        self.coefficients = None
        self.normal = None
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
        self.coefficients = list(shape.Coefficients())
        self.normal = gpXYZ2List(shape.Axis().Direction())

    def fromMesh(self, mesh):
        super().fromMesh(mesh)

    def toDict(self):
        features = super().toDict()
        features['type'] = Plane.primitiveType()
        features['location'] = self.location
        features['x_axis'] = self.x_axis
        features['y_axis'] = self.y_axis
        features['z_axis'] = self.z_axis
        features['coefficients'] = self.coefficients
        features['normal'] = self.normal

        return features

    def _getNewCoefficients(self):

        # Cartesian equation of the plane: ax + by + cz = d or ax + by + cz - d = 0
        # In this case: self.coefficients[0]*x + self.coefficients[1]*y + self.coefficients[2]*x + self.coefficients[3] = 0.0

        # z_axis = [self.coefficients[0], self.coefficients[1], self.coefficients[2]]
        # Because: z_axis is a normal vector of the plane, so:
        #   z_axis = a*i + b*j + c*k
        #   z_axis = self.coefficients[0]*i + self.coefficients[1]*j + self.coefficients[2]*k

        # Therefore, d = self.coefficients[0]*self.location[0] + self.coefficients[1]*self.location[1] + self.coefficients[2]*self.location[2]

        d = -(self.z_axis[0]*self.location[0] + self.z_axis[1]*self.location[1] + self.z_axis[2]*self.location[2])
        
        return [self.z_axis[0], self.z_axis[1], self.z_axis[2], d]
    
    def normalize(self, R=np.eye(3,3), t=np.zeros(3), s=1.):
        self.location = R @ self.location
        self.x_axis = R @ self.x_axis
        self.y_axis = R @ self.y_axis
        self.z_axis = R @ self.z_axis
        self.normal = R @ self.normal

        self.location += t

        self.location *= s

        self.location = self.location.tolist()
        self.x_axis = self.x_axis.tolist()
        self.y_axis = self.y_axis.tolist()
        self.z_axis = self.z_axis.tolist()
        self.normal = self.normal.tolist()

        self.coefficients = self._getNewCoefficients()