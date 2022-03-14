from lib.tools import gpXYZ2List

from lib.primitives.base_surface_feature import BaseSurfaceFeature

class Torus(BaseSurfaceFeature):
    
    @staticmethod
    def primitiveType():
        return 'Torus'

    def __init__(self, shape, params=None):
        super().__init__()
        self.shape = shape.Torus()
        self.location = None
        self.x_axis = None
        self.y_axis = None
        self.z_axis = None
        self.max_radius = None
        self.min_radius = None
        self.fromShape(params)
    
    def getLocation(self):
        return gpXYZ2List(self.shape.Location())

    def getAxis(self):
        x_axis = gpXYZ2List(self.shape.XAxis().Direction())
        y_axis = gpXYZ2List(self.shape.YAxis().Direction())
        z_axis = gpXYZ2List(self.shape.Axis().Direction())
        return [x_axis, y_axis, z_axis]

    def getRadius(self):
        return [self.shape.MajorRadius(), self.shape.MinorRadius()]

    def fromShape(self, params):
        if params is not None:
            super().fromDict(params)
        self.location = self.getLocation()
        self.x_axis = self.getAxis()[0]
        self.y_axis = self.getAxis()[1]
        self.z_axis = self.getAxis()[2]
        self.max_radius = self.getRadius()[0]
        self.min_radius = self.getRadius()[1]

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

    def updateWithMeshParams(self, params):
        super().fromDict(params)
        
        return True