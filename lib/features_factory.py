from typing import SupportsFloat
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
        if type in FeaturesFactory.SURFACES_TYPES.keys(): 
            return FeaturesFactory.SURFACES_TYPES[type](shape, params)
        elif type in FeaturesFactory.CURVES_TYPES.keys():
            return FeaturesFactory.CURVES_TYPES[type](shape, params)
        else:
            return None

    def getDictFromPrimitive(primitive):
        feature = {}
        feature = primitive.toDict()
        return feature

    def getListOfDictFromPrimitive(primitives: dict):
        features = {}

        features['curves'] = []
        features['surfaces'] = []
        
        curves = primitives['curves']
        surfaces = primitives['surfaces']

        for curve in curves:
            if curve is not None:
                features['curves'].append(FeaturesFactory.getDictFromPrimitive(curve))
        for surface in surfaces:
            if surface is not None:
                features['surfaces'].append(FeaturesFactory.getDictFromPrimitive(surface))

        return features



        
