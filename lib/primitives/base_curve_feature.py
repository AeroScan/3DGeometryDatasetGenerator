
class BaseCurveFeature:
    PRIMITIVES_PARAMS = {
        'Line': ['type', 'location', 'direction', 'sharp', 'vert_indices', 'vert_parameters'],
        'Circle': ['type', 'location', 'x_axis', 'y_axis', 'z_axis', 'radius', 'sharp', 'vert_indices', 'vert_parameters'],
        'Ellipse': ['type', 'focus1', 'focus2', 'x_axis', 'y_axis', 'z_axis', 'x_radius', 'y_radius', 'sharp', 'vert_indices', 'vert_parameters'],
    }

    def __init__(self):
        self.class_child = self.__class__.__name__
        assert self.class_child in BaseCurveFeature.PRIMITIVES_PARAMS.keys()
        self.vert_indices = None
        self.vert_parameters = None
        self.createBaseDict()

    def createBaseDict(self):
        self.features = {}
        for value in BaseCurveFeature.PRIMITIVES_PARAMS[self.class_child]:
            self.features[value] = None

    def fromDict(self, params):
        self.vert_indices = params['vert_indices']
        self.vert_parameters = params['vert_parameters']