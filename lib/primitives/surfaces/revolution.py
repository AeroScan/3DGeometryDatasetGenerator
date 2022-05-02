from lib.primitives.base_surface_feature import BaseSurfaceFeature

class Revolution(BaseSurfaceFeature):

    @staticmethod
    def primitiveType():
        return 'Revolution'

    @staticmethod
    def getPrimitiveParams():
        return ['location', 'z_axis', 'curve']