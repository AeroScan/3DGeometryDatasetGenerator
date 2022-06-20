from .primitives import *

class FeaturesFactory:
    TYPES = {
        'curve': {
            'base': BaseCurveFeature,
            'types': {
                'line': Line,
                'circle': Circle,
                'ellipse': Ellipse,
            },
        },
        'surface': {
            'base': BaseSurfaceFeature,
            'types': {
                'plane': Plane,
                'cylinder': Cylinder,
                'cone': Cone,
                'sphere': Sphere,
                'torus': Torus,
            },
        },
    }
    
    @staticmethod
    def getPrimitiveObject(type, geometry_type, shape=None, mesh=None,):
        type = type.lower()
        geometry_type = geometry_type.lower()
        if geometry_type in FeaturesFactory.TYPES.keys():
            if type in FeaturesFactory.TYPES[geometry_type]['types'].keys(): 
                return FeaturesFactory.TYPES[geometry_type]['types'][type](shape=shape, mesh=mesh)
            else:
                return FeaturesFactory.TYPES[geometry_type]['base'](shape=shape, mesh=mesh)

    @staticmethod
    def getDictFromPrimitive(primitive) -> dict:
        feature = {}
        feature = primitive.toDict()
        return feature

    @staticmethod
    def removeNoneValuesOfDict(d: dict) -> dict:
        for key in d.keys():
            i = 0
            while i < len(d[key]):
                if d[key][i] is None:
                    d[key].pop(i)
                else:
                    i = i + 1

        return d

    @staticmethod
    def getListOfDictFromPrimitive(primitives: dict) -> dict:
        i = 0
        while i < len(primitives['curves']):
            if primitives['curves'][i].primitiveType() != 'BaseCurve':
                primitives['curves'][i] = FeaturesFactory.getDictFromPrimitive(primitives['curves'][i])
                i += 1
            else:
                primitives['curves'].pop(i)
        i = 0
        while i < len(primitives['surfaces']):
            if primitives['surfaces'][i].primitiveType() != 'BaseSurface':
                primitives['surfaces'][i] = FeaturesFactory.getDictFromPrimitive(primitives['surfaces'][i])
                i += 1
            else:
                primitives['surfaces'].pop(i)
        
        features = {
            'curves': primitives['curves'],
            'surfaces': primitives['surfaces']
        }

        return features