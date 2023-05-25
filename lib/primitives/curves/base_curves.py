import abc
from typing import Union

from OCC.Core.gp import gp_Ax2
from OCC.Core.GeomAdaptor import GeomAdaptor_Curve
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve

import numpy as np

from lib.tools import gpXYZ2List
from ..geometry.base_geometry import BaseGeometry

class BaseCurve(BaseGeometry, metaclass=abc.ABCMeta):

    @staticmethod
    @abc.abstractmethod
    def getName():
        pass

    @staticmethod
    @abc.abstractmethod
    def _fixOrientation(shape, tp: str, shape_orientation: int):
        pass

    @classmethod
    def toDict(cls, adaptor: Union[GeomAdaptor_Curve, BRepAdaptor_Curve], mesh_data: dict = None, 
               transforms: list = [], shape_orientation: int = 0):
        shape, features = super().toDict(adaptor, mesh_data=mesh_data, transforms=transforms,
                                         shape_orientation=shape_orientation)

        return shape, features

class BaseLineCurve(BaseCurve, metaclass=abc.ABCMeta):

    @staticmethod
    @abc.abstractmethod
    def getName():
        pass

    @staticmethod
    def _fixOrientation(shape, tp: str, shape_orientation: int):
        if shape_orientation == 1:
            old_direction = np.array(gpXYZ2List(shape.Direction()))
            shape.Reverse()
            new_direction = np.array(gpXYZ2List(shape.Direction()))
            
            assert np.all(np.isclose(new_direction, -old_direction)), \
                   f'Sanity Check Failed: problem in reversing a {tp}. ' \
                   f'\n\t\t~~~~~ {new_direction} != {-old_direction} ~~~~~'
        
        return shape

    @classmethod
    def toDict(cls, adaptor: Union[GeomAdaptor_Curve, BRepAdaptor_Curve], mesh_data: dict = None,
               transforms: list = [], shape_orientation: int = 0):       

        shape, features = super().toDict(adaptor, mesh_data=mesh_data, transforms=transforms,
                                         shape_orientation=shape_orientation)
                       
        features['location'] = gpXYZ2List(shape.Location())
        features['direction'] = gpXYZ2List(shape.Direction())
            
        return shape, features

class BaseConicCurve(BaseCurve, metaclass=abc.ABCMeta):

    @staticmethod
    @abc.abstractmethod
    def getName():
        pass

    @staticmethod
    def _fixOrientation(shape, tp: str, shape_orientation: int):
        if shape_orientation == 1:
            old_loc = np.array(gpXYZ2List(shape.Location()))
            old_axis = np.array(gpXYZ2List(shape.Axis().Direction()))
            shape.Mirror(gp_Ax2(shape.Location(), shape.XAxis().Direction(),
                                shape.YAxis().Direction()))
            
            new_loc = np.array(gpXYZ2List(shape.Location()))
            new_axis = np.array(gpXYZ2List(shape.Axis().Direction()))
            
            assert np.all(np.isclose(old_axis, -new_axis)) and np.all(np.isclose(old_loc, new_loc)), \
                    f'Sanity Check Failed: problem in reversing a {str(tp)}. ' \
                    f'\n\t\t~~~~~ {old_axis} != {-new_axis} or ' \
                    f'{old_loc} != {new_loc} ~~~~~'
        
        return shape

    @classmethod
    def toDict(cls, adaptor: Union[GeomAdaptor_Curve, BRepAdaptor_Curve], mesh_data: dict = None,
               transforms: list = [], shape_orientation: int = 0):       

        shape, features = super().toDict(adaptor, mesh_data=mesh_data, transforms=transforms,
                                         shape_orientation=shape_orientation)
                       
        features['location'] = gpXYZ2List(shape.Location())
        features['x_axis'] = gpXYZ2List(shape.XAxis().Direction())
        features['y_axis'] = gpXYZ2List(shape.YAxis().Direction())
        features['z_axis'] = gpXYZ2List(shape.Axis().Direction())
            
        return shape, features

class BaseBoundedCurve(BaseCurve, metaclass=abc.ABCMeta):

    @staticmethod
    @abc.abstractmethod
    def getName():
        pass

    @staticmethod
    def _fixOrientation(shape, tp: str, shape_orientation: int):
        if shape_orientation == 1:
                old_start = np.array(gpXYZ2List(shape.StartPoint()))
                old_end = np.array(gpXYZ2List(shape.EndPoint()))
                shape.Reverse()
                new_start = np.array(gpXYZ2List(shape.StartPoint()))
                new_end = np.array(gpXYZ2List(shape.EndPoint()))
                assert np.all(np.isclose(old_start, new_end)) and np.all(np.isclose(old_end, new_start)), \
                       f'Sanity Check Failed: problem in reversing a {str(tp)}. '\
                       f'\n\t\t~~~~~ {old_start} != {new_end} or ' \
                       f'{old_end} != {new_start} ~~~~~'
        
        return shape

    @classmethod
    def toDict(cls, adaptor: Union[GeomAdaptor_Curve, BRepAdaptor_Curve], mesh_data: dict = None,
               transforms: list = [], shape_orientation: int = 0):       

        shape, features = super().toDict(adaptor, mesh_data=mesh_data, transforms=transforms,
                                         shape_orientation=shape_orientation)
                       
        return shape, features