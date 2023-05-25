from .base_surfaces import BaseElementarySurface

class Plane(BaseElementarySurface):

    @staticmethod
    def getName():
        return 'Plane'

    @classmethod
    def toDict(cls, adaptor, mesh_data=None, transforms=None, shape_orientation=0):   

        _, features = super().toDict(adaptor, mesh_data=mesh_data,
                                         transforms=transforms, shape_orientation=shape_orientation)

        return features