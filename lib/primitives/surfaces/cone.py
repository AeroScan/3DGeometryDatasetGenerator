from lib.tools import gpXYZ2List

from .base_surfaces import BaseElementarySurface

class Cone(BaseElementarySurface):

    @staticmethod
    def getName():
        return 'Cone'

    @classmethod
    def toDict(cls, adaptor, mesh_data=None, transforms=None, shape_orientation=0):   

        shape, features = super().toDict(adaptor, mesh_data=mesh_data,
                                         transforms=transforms, shape_orientation=shape_orientation)

        features['radius'] = shape.RefRadius()
        features['angle'] = shape.SemiAngle()
        features['apex'] = gpXYZ2List(shape.Apex())

        return features