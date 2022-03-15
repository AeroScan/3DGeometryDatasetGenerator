from lib.tools import gpXYZ2List
from lib.primitives.base_surface_feature import BaseSurfaceFeature

class Cone(BaseSurfaceFeature):
    
    @staticmethod
    def primitiveType():
        return 'Cone'

    @staticmethod
    def getPrimitiveParams():
        return ['type', 'location', 'x_axis', 'y_axis', 'z_axis', 'coefficients', 'radius', 'angle', 'apex', 'vert_indices', 'vert_parameters', 'face_indices']

    def __init__(self, shape = None, mesh: dict = None):
        super().__init__()
        self.location = None
        self.x_axis = None
        self.y_axis = None
        self.z_axis = None
        self.coefficients = None
        self.radius = None
        self.angle = None
        self.apex = None
        if shape is not None:
            self.fromShape(shape=shape)
        if mesh is not None:
            self.fromMesh(mesh=mesh)

    def fromShape(self, shape):
        shape = shape.Cone()
        self.location = gpXYZ2List(shape.Location())
        self.x_axis = gpXYZ2List(shape.XAxis().Direction())
        self.y_axis = gpXYZ2List(shape.YAxis().Direction())
        self.z_axis = gpXYZ2List(shape.Axis().Direction())
        self.coefficients = list(shape.Coefficients())
        self.radius = shape.RefRadius()
        self.angle = shape.SemiAngle()
        self.apex = gpXYZ2List(shape.Apex())

    def fromMesh(self, mesh):
        super().fromMesh(mesh)

    def toDict(self):
        features = super().toDict()
        features['type'] = Cone.primitiveType()
        features['location'] = self.location
        features['x_axis'] = self.x_axis
        features['y_axis'] = self.y_axis
        features['z_axis'] = self.z_axis
        features['coefficients'] = self.coefficients
        features['radius'] = self.radius
        features['angle'] = self.angle
        features['apex'] = self.apex

        return features