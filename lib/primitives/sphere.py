import numpy as np
from lib.tools import gpXYZ2List

from lib.primitives.base_surface_feature import BaseSurfaceFeature

class Sphere(BaseSurfaceFeature):
    
    @staticmethod
    def primitiveType():
        return 'Sphere'

    @staticmethod
    def getPrimitiveParams():
        return ['type', 'location', 'x_axis', 'y_axis', 'z_axis', 'coefficients', 'radius', 'vert_indices', 'vert_parameters', 'face_indices']

    def __init__(self, shape = None, mesh: dict = None):
        super().__init__()
        self.location = None
        self.x_axis = None
        self.y_axis = None
        self.z_axis = None
        self.coefficients = None
        self.radius = None
        if shape is not None:
            self.fromShape(shape=shape)
        if mesh is not None:
            self.fromMesh(mesh=mesh)

    def getAxis(shape):
        x_axis = np.array(gpXYZ2List(shape.XAxis().Direction()))
        y_axis = np.array(gpXYZ2List(shape.YAxis().Direction()))
        z_axis = np.cross(x_axis, y_axis)

        return [x_axis.tolist(), y_axis.tolist(), z_axis.tolist()]
    
    def fromShape(self, shape):
        shape = shape.Sphere()
        axis = self.getAxis(shape)
        self.location = gpXYZ2List(shape.Location())
        self.x_axis = axis[0]
        self.y_axis = axis[1]
        self.z_axis = axis[2]
        self.coefficients = list(shape.Coefficients())
        self.radius = shape.Radius()

    def fromMesh(self, mesh):
        super().fromMesh(mesh)

    def toDict(self):
        features = super().toDict()
        features['type'] = Sphere.primitiveType()
        features['location'] = self.location
        features['x_axis'] = self.x_axis
        features['y_axis'] = self.y_axis
        features['z_axis'] = self.z_axis
        features['coefficients'] = self.coefficients
        features['radius'] = self.radius

        return features
