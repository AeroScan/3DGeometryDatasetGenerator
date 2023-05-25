from .base_curve import BaseCurve
from lib.tools import gpXYZ2List

class Ellipse(BaseCurve):

    @classmethod
    def toDict(cls, adaptor, mesh_data=None, transforms=None, shape_orientation=0):        
        
        shape, features = super().toDict(adaptor, mesh_data=mesh_data,
                                         transforms=transforms, shape_orientation=shape_orientation)
        
        features['focus1'] = gpXYZ2List(shape.Focus1())
        features['focus2'] = gpXYZ2List(shape.Focus2())
        features['x_radius'] = shape.MajorRadius()
        features['y_radius'] = shape.MinorRadius()

        return features