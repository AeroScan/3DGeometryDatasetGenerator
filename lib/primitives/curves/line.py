from .base_curve import BaseCurve

class Line(BaseCurve):

    @classmethod
    def toDict(cls, brep_adaptor, mesh_data=None, transforms=None, shape_orientation=0):        
        
        _, features = super().toDict(brep_adaptor, mesh_data=mesh_data,
                                         transforms=transforms, shape_orientation=shape_orientation)

        return features