from .base_curve import BaseCurve

class Line(BaseCurve):

    @classmethod
    def toDict(cls, brep_adaptor, mesh_data=None, transforms=None):        
        
        _, features = super().toDict(brep_adaptor, mesh_data=mesh_data,
                                         transforms=transforms)

        print(features['direction'])

        return features