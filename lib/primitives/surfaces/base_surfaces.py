import abc
from typing import Union

from OCC.Core.GeomAdaptor import GeomAdaptor_Surface
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface

import numpy as np

from lib.tools import gpXYZ2List
from ..geometry.base_geometry import BaseGeometry

class BaseSurface(BaseGeometry, metaclass=abc.ABCMeta):

    @staticmethod
    @abc.abstractmethod
    def getName():
        pass

    @staticmethod
    @abc.abstractmethod
    def _fixOrientation(shape, tp: str, shape_orientation: int):
        pass

    @classmethod
    def toDict(cls, adaptor: Union[GeomAdaptor_Surface, BRepAdaptor_Surface], mesh_data: dict = None, 
               transforms: list = [], shape_orientation: int = 0):
        shape, features = super().toDict(adaptor, mesh_data=mesh_data, transforms=transforms,
                                         shape_orientation=shape_orientation)
        if mesh_data is not None: 
            features['face_indices'] = mesh_data['face_indices'] if 'face_indices' in mesh_data.keys() else []
        
        return shape, features

class BaseElementarySurface(BaseSurface, metaclass=abc.ABCMeta):

    @staticmethod
    @abc.abstractmethod
    def getName():
        pass

    @staticmethod
    def _addAxes2Features(shape, features):
        features['x_axis'] = gpXYZ2List(shape.XAxis().Direction())
        features['y_axis'] = gpXYZ2List(shape.YAxis().Direction())
        features['z_axis'] = gpXYZ2List(shape.Axis().Direction())
    
        return features

    @staticmethod
    def _addCoeff2Features(shape, features):
        features['coefficients'] = list(shape.Coefficients())
    
        return features

    @staticmethod
    def _fixOrientation(shape, tp: str, shape_orientation: int):
        if shape_orientation == 1:
            old_loc = np.array(gpXYZ2List(shape.Location()))
            old_axis = np.array(gpXYZ2List(shape.Axis().Direction()))
            shape.Mirror(shape.Position().Ax2())
            new_loc = np.array(gpXYZ2List(shape.Location()))
            new_axis = np.array(gpXYZ2List(shape.Axis().Direction()))
            
            assert np.all(np.isclose(old_axis, -new_axis)) and \
                   np.all(np.isclose(old_loc, new_loc)), \
                   f'Sanity Check Failed: problem in reversing a {tp}. ' \
                   f'\n\t\t~~~~~ {old_axis} != {-new_axis} or' \
                   f'{old_loc} != {new_loc} ~~~~~'
            
        return shape

    @classmethod
    def toDict(cls, adaptor: Union[GeomAdaptor_Surface, BRepAdaptor_Surface], mesh_data: dict = None, 
               transforms: list = [], shape_orientation: int = 0):

        shape, features = super().toDict(adaptor, mesh_data=mesh_data, transforms=transforms,
                                         shape_orientation=shape_orientation)
        
        features['location'] = gpXYZ2List(shape.Location())
        features = cls._addAxes2Features(shape, features)
        features = cls._addCoeff2Features(shape, features)
        
        return shape, features

class BaseBoundedSurface(BaseSurface, metaclass=abc.ABCMeta):

    @staticmethod
    @abc.abstractmethod
    def getName():
        pass
 
    @staticmethod
    def _fixOrientation(shape, tp: str, shape_orientation: int):
        if shape_orientation == 1:
            old_bounds = shape.Bounds()
            old_us, old_vs = np.asarray(old_bounds[:2]), np.asarray(old_bounds[2:])
            shape.UReverse()
            shape.VReverse()
            new_bounds = shape.Bounds()
            new_us, new_vs = np.asarray(new_bounds[:2]), np.asarray(new_bounds[2:])
            
            assert np.all(np.isclose(old_us, np.flip(new_us))) and \
                   np.all(np.isclose(old_vs, np.flip(new_vs))), \
                   f'Sanity Check Failed: problem in reversing a {tp}. ' \
                   f'\n\t\t~~~~~ {old_us} != {np.flip(new_us)} or' \
                   f'{old_vs} != {np.flip(new_vs)} ~~~~~'
            
        return shape
    
    @classmethod
    def toDict(cls, adaptor: Union[GeomAdaptor_Surface, BRepAdaptor_Surface], mesh_data: dict = None, 
               transforms: list = [], shape_orientation: int = 0):
        shape, features = super().toDict(adaptor, mesh_data=mesh_data, transforms=transforms,
                                         shape_orientation=shape_orientation)
        
        return shape, features
    
class BaseSweptSurface(BaseSurface, metaclass=abc.ABCMeta):

    @staticmethod
    @abc.abstractmethod
    def getName():
        pass
 
    @staticmethod
    def _fixOrientation(shape, tp: str, shape_orientation: int):
        return shape

    @classmethod
    def toDict(cls, adaptor: Union[GeomAdaptor_Surface, BRepAdaptor_Surface], mesh_data: dict = None, 
               transforms: list = [], shape_orientation: int = 0):
        shape, features = super().toDict(adaptor, mesh_data=mesh_data, transforms=transforms,
                                         shape_orientation=shape_orientation)
        
        return shape, features