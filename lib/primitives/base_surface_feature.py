
class BaseSurfaceFeature:
    PRIMITIVES_PARAMS = {
        'Plane': ['type', 'location', 'normal', 'x_axis', 'y_axis', 'z_axis', 'coefficients', 'vert_indices', 'vert_parameters', 'face_indices'],
        'Cylinder': ['type', 'location', 'x_axis', 'y_axis', 'z_axis', 'coefficients', 'radius', 'vert_indices', 'vert_parameters', 'face_indices'],
        'Cone': ['type', 'location', 'x_axis', 'y_axis', 'z_axis', 'coefficients', 'radius', 'angle', 'apex', 'vert_indices', 'vert_parameters', 'face_indices'],
        'Sphere': ['type', 'location', 'x_axis', 'y_axis', 'z_axis', 'coefficients', 'radius', 'vert_indices', 'vert_parameters', 'face_indices'],
        'Torus': ['type', 'location', 'x_axis', 'y_axis', 'z_axis', 'max_radius', 'min_radius', 'vert_indices', 'vert_parameters', 'face_indices'],
    }

    def __init__(self):
        self.vert_indices = None
        self.vert_parameters = None
        self.face_indices = None

    def fromMesh(self, mesh):
        self.vert_indices = mesh['vert_indices'] if 'vert_indices' in mesh.keys() else []
        self.vert_parameters = mesh['vert_parameters'] if 'vert_parameters' in mesh.keys() else []
        self.face_indices = mesh['face_indices'] if 'face_indices' in mesh.keys() else []
    
    def toDict(self):
        features = {}
        features['vert_indices'] = self.vert_indices
        features['vert_parameters'] = self.vert_parameters
        features['face_indices'] = self.face_indices
        
        return features

    def createBaseDict(self):
        features = {}
        for value in BaseSurfaceFeature.PRIMITIVES_PARAMS[self.class_child]:
            features[value] = None

        return features