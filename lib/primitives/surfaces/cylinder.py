from .base_surfaces import BaseElementarySurface

class Cylinder(BaseElementarySurface):

    @staticmethod
    def getName():
        return 'Cylinder'

    @classmethod
    def toDict(cls, adaptor, mesh_data=None, transforms=None, shape_orientation=0):   

        shape, features = super().toDict(adaptor, mesh_data=mesh_data,
                                         transforms=transforms, shape_orientation=shape_orientation)

        features['radius'] = shape.Radius()

        return features