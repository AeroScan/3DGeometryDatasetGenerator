from .primitives import *

class FeaturesFactory:
    SURFACES_TYPES = {
        'plane': Plane,
        'cylinder': Cylinder,
        'cone': Cone,
        'sphere': Sphere,
        'torus': Torus,
    }
    CURVES_TYPES = {
        'line': Line,
        'circle': Circle,
        'ellipse': Ellipse,
    }
    
    def getPrimitiveObject(type, shape, params):
        type = type.lower()
        assert type in FeaturesFactory.SURFACES_TYPES.keys() or type in FeaturesFactory.CURVES_TYPES.keys()
        geometry = 'curve' if type in FeaturesFactory.CURVES_TYPES.keys() else 'surface'
        if geometry == 'curve':
            return FeaturesFactory.CURVES_TYPES[type](shape, params)
        elif geometry == 'surface':
            return FeaturesFactory.SURFACES_TYPES[type](shape, params)
        else:
            return None

    def getDictFromPrimitive(primitive):
        feature = {}
        feature = primitive.toDict()
        return feature

    def readListOfDictOfPrimitives(geometries, primitives: dict):
        if not geometries:
            raise Exception('No feature to write.')
        

    def getListOfDictFromPrimitive(primitives: dict):
        features = {}
        geometries = [geometry for geometry in primitives.keys()]

        for primitive in primitives:
            if issubclass(primitive, BaseCurveFeature):
                features['curves'].append(FeaturesFactory.getDictFromPrimitive(primitive))
            elif issubclass(primitive, BaseSurfaceFeature):
                features['surfaces'].append(FeaturesFactory.getDictFromPrimitive(primitive))
            else:
                pass

        return features



        
