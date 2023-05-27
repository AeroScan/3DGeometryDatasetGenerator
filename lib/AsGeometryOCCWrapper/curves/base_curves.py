import abc
from typing import Union

from OCC.Core.gp import gp_Ax2
from OCC.Core.GeomAdaptor import GeomAdaptor_Curve
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve

import numpy as np

from ..geometry.base_geometry import BaseGeometry

class BaseCurve(BaseGeometry, metaclass=abc.ABCMeta):

    def __init__(self, adaptor: Union[GeomAdaptor_Curve, BRepAdaptor_Curve],
                 transforms: list = {}, face_orientation: int = 0):
        super().__init__(adaptor, transforms=transforms, face_orientation=face_orientation)

class BaseLineCurve(BaseCurve, metaclass=abc.ABCMeta):

    def _fixOrientation(self, face_orientation: int):
        if face_orientation == 1:
            old_direction = np.array(self.getDirection())
            self._shape.Reverse()
            new_direction = np.array(self.getDirection())
            
            assert np.all(np.isclose(new_direction, -old_direction)), \
                   f'Sanity Check Failed: problem in reversing a {self.getType()}. ' \
                   f'\n\t\t~~~~~ {new_direction} != {-old_direction} ~~~~~'

    def getLocation(self):
        return self._shape.Location().Coord()
    
    def getDirection(self):
        return self._shape.Direction().Coord()

    def toDict(self):
        features = super().toDict()
                       
        features['location'] = self.getLocation()
        features['direction'] = self.getDirection()
            
        return features

class BaseConicCurve(BaseCurve, metaclass=abc.ABCMeta):

    def _fixOrientation(self, face_orientation: int):
        if face_orientation == 1:
            old_loc = np.array(self.getLocation())
            old_axis = np.array(self.getZAxis())
            self._shape.Mirror(gp_Ax2(self._shape.Location(), self._shape.XAxis().Direction(),
                                self._shape.YAxis().Direction()))
            new_loc = np.array(self.getLocation())
            new_axis = np.array(self.getZAxis())
            
            assert np.all(np.isclose(old_axis, -new_axis)) and np.all(np.isclose(old_loc, new_loc)), \
                    f'Sanity Check Failed: problem in reversing a {str(self.getType())}. ' \
                    f'\n\t\t~~~~~ {old_axis} != {-new_axis} or ' \
                    f'{old_loc} != {new_loc} ~~~~~'
    
    def getLocation(self):
        return self._shape.Location().Coord()
    
    def getXAxis(self):
        return self._shape.XAxis().Direction().Coord()

    def getYAxis(self):
        return self._shape.YAxis().Direction().Coord()
    
    def getZAxis(self):
        return self._shape.Axis().Direction().Coord()
        
    def toDict(self):       
        features = super().toDict()
                       
        features['location'] = self.getLocation()
        features['x_axis'] = self.getXAxis()
        features['y_axis'] = self.getYAxis()
        features['z_axis'] = self.getZAxis()
            
        return features

class BaseBoundedCurve(BaseCurve, metaclass=abc.ABCMeta):

    def _fixOrientation(self, face_orientation: int):
        if face_orientation == 1:
                old_start = np.array(self.getStartPoint())
                old_end = np.array(self.getEndPoint())
                self._shape.Reverse()
                new_start = np.array(self.getStartPoint())
                new_end = np.array(self.getEndPoint())
                assert np.all(np.isclose(old_start, new_end)) and np.all(np.isclose(old_end, new_start)), \
                       f'Sanity Check Failed: problem in reversing a {str(self.getType())}. '\
                       f'\n\t\t~~~~~ {old_start} != {new_end} or ' \
                       f'{old_end} != {new_start} ~~~~~'
                
    def getStartPoint(self):
        return self._shape.StartPoint().Coord()
    
    def getEndPoint(self):
        return self._shape.EndPoint().Coord()