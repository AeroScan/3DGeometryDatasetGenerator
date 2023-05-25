from .base_surfaces import BaseElementarySurface

class Torus(BaseElementarySurface):

    @staticmethod
    def getName():
        return 'Torus'
    
    @staticmethod
    def _addCoeff2Features(shape, features):    
        return features

    @classmethod
    def toDict(cls, adaptor, mesh_data=None, transforms=None, shape_orientation=0):   

        shape, features = super().toDict(adaptor, mesh_data=mesh_data,
                                         transforms=transforms, shape_orientation=shape_orientation)

        features['max_radius'] = shape.MajorRadius()
        features['min_radius'] = shape.MinorRadius()

        return features