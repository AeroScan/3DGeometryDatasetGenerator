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
    
    def getPrimitiveObject(type, shape, mesh: dict):
        type = type.lower()
        if type in FeaturesFactory.SURFACES_TYPES.keys(): 
            return FeaturesFactory.SURFACES_TYPES[type](shape=shape, mesh=mesh)
        elif type in FeaturesFactory.CURVES_TYPES.keys():
            return FeaturesFactory.CURVES_TYPES[type](shape=shape, mesh=mesh)
        else:
            return None

    def getDictFromPrimitive(primitive) -> dict:
        feature = {}
        feature = primitive.toDict()
        return feature

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

        for key in features.keys():
            i = 0
            while i < len(features[key]):
                if features[key][i] is None:
                    features[key].pop(i)
                else:
                    i = i + 1

        return features

    def updatePrimitiveWithMeshParams(primitive, mesh: dict):
        return primitive.fromMesh(mesh)

