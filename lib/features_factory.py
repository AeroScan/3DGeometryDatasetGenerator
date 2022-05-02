from .primitives import *

class FeaturesFactory:
    SURFACES_TYPES = {
        'plane': Plane,
        'cylinder': Cylinder,
        'cone': Cone,
        'sphere': Sphere,
        'torus': Torus,
        'revolution': Revolution,
        'extrusion': Extrusion,
        'bsplinesurface': BSplineSurface,
    }
    CURVES_TYPES = {
        'line': Line,
        'circle': Circle,
        'ellipse': Ellipse,
        'bsplinecurve': BSplineCurve,
    }
    
    @staticmethod
    def getPrimitiveObject(type, shape, mesh: dict):
        type = type.lower()
        if type in FeaturesFactory.SURFACES_TYPES.keys(): 
            return FeaturesFactory.SURFACES_TYPES[type](shape=shape, mesh=mesh)
        elif type in FeaturesFactory.CURVES_TYPES.keys():
            return FeaturesFactory.CURVES_TYPES[type](shape=shape, mesh=mesh)
        else:
            return None

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
        for i in range(0, len(primitives['curves'])):
            if primitives['curves'][i] is not None:
                primitives['curves'][i] = FeaturesFactory.getDictFromPrimitive(primitives['curves'][i])
        for i in range(0, len(primitives['surfaces'])):
            if primitives['surfaces'][i] is not None:
                primitives['surfaces'][i] = FeaturesFactory.getDictFromPrimitive(primitives['surfaces'][i])
        
        features = {
            'curves': primitives['curves'],
            'surfaces': primitives['surfaces']
        }

        features = FeaturesFactory.removeNoneValuesOfDict(d=features)

        return features

    @staticmethod
    def updatePrimitiveWithMeshParams(primitive, mesh: dict):
        return primitive.fromMesh(mesh)