from lib.tools import gpXYZ2List

from .base_surfaces import BaseElementarySurface

class Sphere(BaseElementarySurface):

    @staticmethod
    def getName():
        return 'Sphere'
    
    @staticmethod
    def _addAxes2Features(shape, features):
        x_axis = shape.XAxis().Direction()
        y_axis = shape.YAxis().Direction()
        features['x_axis'] = gpXYZ2List(x_axis)
        features['y_axis'] = gpXYZ2List(y_axis)
        features['z_axis'] = gpXYZ2List(x_axis.Crossed(y_axis))
    
        return features

    @classmethod
    def toDict(cls, adaptor, mesh_data=None, transforms=None, shape_orientation=0):   

        shape, features = super().toDict(adaptor, mesh_data=mesh_data,
                                         transforms=transforms, shape_orientation=shape_orientation)

        features['radius'] = shape.Radius()

        return features