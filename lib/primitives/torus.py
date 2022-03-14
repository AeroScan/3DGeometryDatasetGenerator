from lib.tools import gpXYZ2List

from lib.primitives.base_surface_feature import BaseSurfaceFeature

class Torus(BaseSurfaceFeature):
    
    @staticmethod
    def primitiveType():
        return 'Torus'

    def __init__(self):
        super().__init__()
        self.location = None
        self.x_axis = None
        self.y_axis = None
        self.z_axis = None
        self.max_radius = None
        self.min_radius = None

    def fromShape(self, shape):
        shape = shape.Torus()
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