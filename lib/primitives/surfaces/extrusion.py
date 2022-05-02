from lib.primitives.base_surface_feature import BaseSurfaceFeature

class Extrusion(BaseSurfaceFeature):

    @staticmethod
    def primitiveType():
        return 'Extrusion'

    @staticmethod
    def getPrimitiveParams():
        return ['direction', 'curve']

    