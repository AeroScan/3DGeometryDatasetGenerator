from lib.primitives.base_curve_feature import BaseCurveFeature

from lib.tools import gpXYZ2List

class Ellipse(BaseCurveFeature):

    @staticmethod
    def primitiveType():
        return 'Ellipse'

    @staticmethod
    def getPrimitiveParams():
        return ['type', 'focus1', 'focus2', 'x_axis', 'y_axis', 'z_axis', 'x_radius', 'y_radius', 'sharp', 'vert_indices', 'vert_parameters']
    
    def __init__(self, shape = None, mesh: dict = None):
        super().__init__()
        self.focus1 = None
        self.focus2 = None
        self.x_axis = None
        self.y_axis = None
        self.z_axis = None
        self.x_radius = None
        self.y_radius = None
        if shape is not None:
            self.fromShape(shape=shape)
        if mesh is not None:
            self.fromMesh(mesh=mesh)

    def fromShape(self, shape):
        shape = shape.Ellipse()
        self.focus1 = gpXYZ2List(shape.Focus1())
        self.focus2 = gpXYZ2List(shape.Focus2())
        self.x_axis = gpXYZ2List(shape.XAxis().Direction())
        self.y_axis = gpXYZ2List(shape.YAxis().Direction())
        self.z_axis = gpXYZ2List(shape.Axis().Direction())
        self.x_radius = shape.MajorRadius()
        self.y_radius = shape.MinorRadius()

    def fromMesh(self, mesh):
        super().fromMesh(mesh)

    def toDict(self):
        features = super().toDict()
        features['type'] = Ellipse.primitiveType()
        features['focus1'] = self.focus1
        features['focus2'] = self.focus2
        features['x_axis'] = self.x_axis
        features['y_axis'] = self.y_axis
        features['z_axis'] = self.z_axis
        features['x_radius'] = self.x_radius
        features['y_radius'] = self.y_radius

        return features