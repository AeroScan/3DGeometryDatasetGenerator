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
    
    def getPrimitiveObject(type, shape):
        type = type.lower()
        assert type in FeaturesFactory.SURFACES_TYPES.keys() or type in FeaturesFactory.CURVES_TYPES.keys()
        geometry = 'curve' if type in FeaturesFactory.CURVES_TYPES.keys() else 'surface'
        if geometry == 'curve':
            FeaturesFactory.CURVES_TYPES[type](shape)
        elif geometry == 'surface':
            FeaturesFactory.SURFACES_TYPES[type](shape)
        else:
            pass

    def getDictFromPrimitive(primitive):
        feature = {}
        feature = primitive.toDict()
        return feature

    def getListOfDictFromPrimitive(primitive_list):
        features = {}
        features['surfaces'] = []
        features['curves'] = []
        for primitive in primitive_list:
            if issubclass(primitive, BaseCurveFeature):
                features['curves'].append(FeaturesFactory.getDictFromPrimitive(primitive))
            elif issubclass(primitive, BaseSurfaceFeature):
                features['surfaces'].append(FeaturesFactory.getDictFromPrimitive(primitive))
            else:
                pass

        return features



        
