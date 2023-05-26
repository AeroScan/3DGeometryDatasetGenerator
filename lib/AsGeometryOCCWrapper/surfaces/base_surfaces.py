import abc
from typing import Union

from OCC.Core.gp import gp_Ax2
from OCC.Core.GeomAdaptor import GeomAdaptor_Surface
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface

import numpy as np

from ..geometry.base_geometry import BaseGeometry

class BaseSurface(BaseGeometry, metaclass=abc.ABCMeta):

    def __init__(self, adaptor: Union[GeomAdaptor_Surface, BRepAdaptor_Surface],
                 transforms: list = {}, face_orientation: int = 0):
        super().__init__(adaptor, transforms=transforms, face_orientation=face_orientation)

class BaseElementarySurface(BaseSurface, metaclass=abc.ABCMeta):

    def _fixOrientation(self, face_orientation: int):
        if face_orientation == 1:
            old_loc = np.array(self.getLocation())
            old_xaxis = np.array(self.getXAxis())
            old_yaxis = np.array(self.getYAxis())
            self._shape.Mirror(gp_Ax2(self._shape.Location(), self._shape.XAxis().Direction(), self._shape.Axis().Direction()))
            self._shape.Mirror(gp_Ax2(self._shape.Location(), self._shape.YAxis().Direction(), self._shape.Axis().Direction()))
            new_loc = np.array(self.getLocation())
            new_xaxis = np.array(self.getXAxis())
            new_yaxis = np.array(self.getYAxis())
            
            assert np.all(np.isclose(old_xaxis, -new_xaxis)) and  \
                   np.all(np.isclose(old_yaxis, -new_yaxis)) and  \
                   np.all(np.isclose(old_loc, new_loc)), \
                   f'Sanity Check Failed: problem in reversing a {self.getName()}. ' \
                   f'\n\t\t~~~~~ {old_xaxis} != {-new_xaxis} or ' \
                   f'{old_yaxis} != {-new_yaxis} or ' \
                   f'{old_loc} != {new_loc} ~~~~~'
    
    def getLocation(self):
        return self._shape.Location().Coord()

    def getCoefficients(self):
        return list(self._shape.Coefficients())
    
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
        features['coefficients'] = self.getCoefficients()
            
        return features

class BaseBoundedSurface(BaseSurface, metaclass=abc.ABCMeta):
    
    def _fixOrientation(self, face_orientation: int):
        pass
 
    # def _fixOrientation(self, face_orientation: int):
    #     if face_orientation == 1:
    #         old_lower_bound = np.array(self.getLowerBound())
    #         old_upper_bound = np.array(self.getUpperBound())
    #         self._shape.UReverse()
    #         self._shape.VReverse()
    #         new_lower_bound = np.array(self.getLowerBound())
    #         new_upper_bound = np.array(self.getUpperBound())
            
    #         assert np.all(np.isclose(old_lower_bound, new_upper_bound)) and \
    #                np.all(np.isclose(old_upper_bound, new_lower_bound)), \
    #                f'Sanity Check Failed: problem in reversing a {self.getName()}. ' \
    #                f'\n\t\t~~~~~ {old_lower_bound} != {new_upper_bound} or' \
    #                f'{old_upper_bound} != {np.flip(new_lower_bound)} ~~~~~'
        
    def getLowerBound(self):
        return tuple(self._shape.Bounds()[2:])

    def getUpperBound(self):
        return tuple(self._shape.Bounds()[:2])

    def toDict(self):
        features = super().toDict()
            
        return features
    
class BaseSweptSurface(BaseSurface, metaclass=abc.ABCMeta):
 
    def _fixOrientation(self, face_orientation: int):
        pass

    def toDict(self):
        features = super().toDict()
            
        return features