from .base_surface import BaseSurface

class Plane(BaseSurface):

    @classmethod
    def toDict(cls, geom_adaptor, mesh_data=None, transforms=None, shape_orientation=0):   

        _, features = super().toDict(geom_adaptor, mesh_data=mesh_data,
                                         transforms=transforms, shape_orientation=shape_orientation)

        return features