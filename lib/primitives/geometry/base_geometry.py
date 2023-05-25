import abc
from typing import Union

from OCC.Core.GeomAdaptor import GeomAdaptor_Curve, GeomAdaptor_Surface
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface

class BaseGeometry(metaclass=abc.ABCMeta):

    @staticmethod
    @abc.abstractmethod
    def getName():
        pass

    @staticmethod
    @abc.abstractmethod
    def _fixOrientation(shape, tp: str, shape_orientation: int):
        pass

    @classmethod
    def toDict(cls, adaptor: Union[GeomAdaptor_Curve, GeomAdaptor_Surface, BRepAdaptor_Curve, BRepAdaptor_Surface],
               mesh_data: dict = None, transforms: list = [], shape_orientation: int = 0):
        
        features = {}

        tp = cls.getName()
        assert tp is not None, "Static method getName() must be implemented in the derived class."
        
        shape = getattr(adaptor, tp)()

        for T in transforms:
            shape.Transform(T)

        features['type'] = tp

        if mesh_data is not None:
            features['sharp'] = mesh_data['sharp'] if 'sharp' in mesh_data.keys() else True
            features['vert_indices'] = mesh_data['vert_indices'] if 'vert_indices' in mesh_data.keys() else []
            features['vert_parameters'] = mesh_data['vert_parameters'] if 'vert_parameters' in mesh_data.keys() else []

        shape = cls._fixOrientation(shape, str(tp), shape_orientation)

        return shape, features