
class BaseCurveFeature:
    PRIMITIVES_PARAMS = {
        'Line': ['type', 'location', 'direction', 'sharp', 'vert_indices', 'vert_parameters'],
        'Circle': ['type', 'location', 'x_axis', 'y_axis', 'z_axis', 'radius', 'sharp', 'vert_indices', 'vert_parameters'],
        'Ellipse': ['type', 'focus1', 'focus2', 'x_axis', 'y_axis', 'z_axis', 'x_radius', 'y_radius', 'sharp', 'vert_indices', 'vert_parameters'],
    }

    def __init__(self):
        self.sharp = None
        self.vert_indices = None
        self.vert_parameters = None
        self.createBaseDict()

    def fromMesh(self, params):
        self.sharp = params['sharp'] if 'sharp' in params.keys() else 'true'
        self.vert_indices = params['vert_indices'] if 'vert_indices' in params.keys() else []
        self.vert_parameters = params['vert_parameters'] if 'vert_parameters' in params.keys() else []

    def toDict(self):
        features = {}
        features['sharp'] = self.sharp
        features['vert_indices'] = self.vert_indices
        features['vert_parameters'] = self.vert_parameters
        return features
    
    def createBaseDict(self):
        self.features = {}
        for value in BaseCurveFeature.PRIMITIVES_PARAMS[self.class_child]:
            self.features[value] = None