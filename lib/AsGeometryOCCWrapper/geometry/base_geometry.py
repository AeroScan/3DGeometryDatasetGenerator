import abc
from typing import Union

from OCC.Core.GeomAdaptor import GeomAdaptor_Curve, GeomAdaptor_Surface
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCC.Core.gp import gp_Trsf, gp_Quaternion, gp_Vec, gp_Mat

class BaseGeometry(metaclass=abc.ABCMeta):

    POSSIBLE_TRANSFORMS = ['rotation', 'translation',
                           'scale', 'mirror']

    @staticmethod
    @abc.abstractmethod
    def getType():
        pass

    @abc.abstractmethod
    def _fixOrientation(self, tp: str, face_orientation: int):
        pass

    def _generateInternalData(self, adaptor: Union[GeomAdaptor_Curve, GeomAdaptor_Surface, BRepAdaptor_Curve, BRepAdaptor_Surface]):
        self._shape = getattr(adaptor, self.getType())()

    def __init__(self, adaptor: Union[GeomAdaptor_Curve, GeomAdaptor_Surface, BRepAdaptor_Curve, BRepAdaptor_Surface],
                 transforms: list = {}, face_orientation: int = 0):
        
        self._generateInternalData(adaptor)       
        self.applyTransforms(transforms)
        self._fixOrientation(face_orientation)

    def doTransformOCC(self, trsf: gp_Trsf):
        self._shape.Transform(trsf)
    
    def applyTransform(self, transform: dict):
        transform_exists = [key in BaseGeometry.POSSIBLE_TRANSFORMS for key in transform.keys()]
        if not all(transform_exists):
            not_exit_transforms = [transform.keys()[i] for i in range(len(transform_exists)) if transform_exists[i] == False]
            print(f'Transforms {not_exit_transforms} must be in {BaseGeometry.POSSIBLE_TRANSFORMS} list.')

        trsf = gp_Trsf()
        if 'rotation' in transform.keys():
            trsf.SetRotation(gp_Quaternion(gp_Mat(*([item for sublist in transform['rotation'] for item in sublist]))))
        if 'translation' in transform.keys():
            trsf.SetTranslation(gp_Vec(*transform['translation']))
        if 'scale' in transform.keys():
            trsf.SetScaleFactor(transform['scale'])
        if 'mirror' in transform.keys():
            pass
    
        self.doTransformOCC(trsf)
    
    def applyTransformAndReturn(self, transform: dict):
        self.applyTransform(transform)
        return self

    def applyTransforms(self, transforms: list):
        for transform in transforms:
            self.applyTransform(transform)
        
    def applyTransformsAndReturn(self, transforms: list):
        self.applyTransforms(transforms)
        return self

    def toDict(self):
        
        features = {}
        features['type'] = self.getType()

        return features