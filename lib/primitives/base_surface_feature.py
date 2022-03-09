
class BaseSurfaceFeature:
    PRIMITIVES_PARAMS = {
        'Plane': ['type', 'location', 'normal', 'x_axis', 'y_axis', 'z_axis', 'coefficients', 'vert_indices', 'vert_parameters', 'face_indices'],
        'Cylinder': ['type', 'location', 'x_axis', 'y_axis', 'z_axis', 'coefficients', 'radius', 'vert_indices', 'vert_parameters', 'face_indices'],
        'Cone': ['type', 'location', 'x_axis', 'y_axis', 'z_axis', 'coefficients', 'radius', 'angle', 'apex', 'vert_indices', 'vert_parameters', 'face_indices'],
        'Sphere': ['type', 'location', 'x_axis', 'y_axis', 'z_axis', 'coefficients', 'radius', 'vert_indices', 'vert_parameters', 'face_indices'],
        'Torus': ['type', 'location', 'x_axis', 'y_axis', 'z_axis', 'max_radius', 'min_radius', 'vert_indices', 'vert_parameters', 'face_indices'],
    }

    def __init__(self):
        self.class_child = self.__class__.__name__
        assert self.class_child in BaseSurfaceFeature.PRIMITIVES_PARAMS.keys()
        self.vert_indices = None
        self.vert_parameters = None
        self.face_indices = None

    def fromDict(self, params={}):
        self.vert_indices = params['vert_indices'] if 'vert_indices' in params.keys() else None
        self.vert_parameters = params['vert_parameters'] if 'vert_parameters' in params.keys() else None
        self.face_indices = params['face_indices'] if 'face_indices' in params.keys() else None

    def createBaseDict(self):
        features = {}
        for value in BaseSurfaceFeature.PRIMITIVES_PARAMS[self.class_child]:
            features[value] = None

        return features