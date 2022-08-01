from . import *

class CurveFactory:
    CURVE_TYPES = {
        'line': Line,
        'circle': Circle,
        'ellipse': Ellipse,
        'bsplinecurve': BSplineCurve,
    }

    @staticmethod
    def getPrimitiveObject(type, shape, mesh: dict):
        type = type.lower()
        if type in CurveFactory.CURVE_TYPES.keys():
            return CurveFactory.CURVE_TYPES[type](shape=shape, mesh=mesh)
        else:
            return None

    @staticmethod
    def getDictFromPrimitive(primitive) -> dict:
        feature = {}
        feature = primitive.toDict()
        return feature