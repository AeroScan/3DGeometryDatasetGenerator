from .base_curve import BaseCurve

class Circle(BaseCurve):

    @classmethod
    def toDict(cls, adaptor, mesh_data=None, transforms=None, shape_orientation=0):        
        
        shape, features = super().toDict(adaptor, mesh_data=mesh_data,
                                         transforms=transforms, shape_orientation=shape_orientation)
        
        features['radius'] = shape.Radius()

        return features