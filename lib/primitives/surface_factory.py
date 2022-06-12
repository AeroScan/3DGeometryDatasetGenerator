from .surfaces import *

class SurfaceFactory:
    SURFACE_TYPES = {
        'plane': Plane,
        'cylinder': Cylinder,
        'cone': Cone,
        'sphere': Sphere,
        'torus': Torus,
        'revolution': Revolution,
        'extrusion': Extrusion,
        'bsplinesurface': BSplineSurface,
    }

    @staticmethod
    def getPrimitiveObject(type, shape, mesh: dict):
        type = type.lower()
        if type in SurfaceFactory.SURFACE_TYPES.keys():
            return SurfaceFactory.SURFACE_TYPES[type](shape=shape, mesh=mesh)
        else:
            return None

    @staticmethod
    def getDictFromPrimitive(primitive) -> dict:
        feature = {}
        feature = primitive.toDict()
        return feature