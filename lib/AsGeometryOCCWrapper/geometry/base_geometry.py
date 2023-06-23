import abc
from typing import Union

from OCC.Core.Geom import Geom_Curve, Geom_Surface
from OCC.Core.gp import gp_Trsf, gp_Quaternion, gp_Vec, gp_Mat
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCC.Core.GeomAdaptor import GeomAdaptor_Curve, GeomAdaptor_Surface

import numpy as np
import open3d as o3d

EPS = np.finfo(np.float32).eps

#TODO: change the place of these functions
def angleDeviation(arrs1, arrs2):
    angles = []
    for i in range(len(arrs1)):
        angles.append(angleVectors(arrs1[i], arrs2[i]))
    return np.degrees(np.array(angles))

def angleVectors(n1, n2):
    n1_unit = n1/(np.linalg.norm(n1) + EPS)
    n2_unit = n2/(np.linalg.norm(n2) + EPS)
    return np.arccos(np.clip(np.dot(n1_unit, n2_unit), -1.0, 1.0))

def distanceDeviation(arrs1, arrs2):
    return np.linalg.norm(arrs1 - arrs2, axis=1)

class BaseGeometry(metaclass=abc.ABCMeta):

    POSSIBLE_TRANSFORMS = ['rotation', 'translation',
                           'scale', 'mirror']
    
    MESH_INFO_KEYS = ['vert_indices', 'vert_parameters']
    
    @staticmethod
    @abc.abstractmethod
    def getType():
        pass

    @staticmethod
    @abc.abstractmethod
    def adaptor2Geom(adaptor: Union[BRepAdaptor_Curve, GeomAdaptor_Curve, BRepAdaptor_Surface, GeomAdaptor_Surface]):
        pass

    def __init__(self, geom: Union[Geom_Curve, Geom_Surface], topods_orientation: int = 0,
                 mesh_info: dict = None):
        
        self.setGeom(geom, topods_orientation=topods_orientation)

        self._mesh = None #optional

        self.setMeshInfo(mesh_info)
    
    @abc.abstractmethod
    def projectPointsOnGeometry(self, points):
        pass

    def _fixOrientation(self):
        pass

    def _doTransformOCC(self, trsf: gp_Trsf):
        self._geom.Transform(trsf)
    
    #TODO: transform mesh too
    #TODO: may change this BaseGeometry static call
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
    
        self._doTransformOCC(trsf)
    
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
        features['foward'] = not bool(self._orientation)

        if self._mesh_info is not None:
            features = dict(features, **(self._mesh_info))

        return features
    
    def setGeom(self, geom: Union[Geom_Curve, Geom_Surface], topods_orientation: int = 0):
        self._geom = geom
        self._orientation = topods_orientation
        self._fixOrientation()

    #TODO: test it
    def _testMeshInfo(self, mesh_info):
        print(self.__class__.MESH_INFO_KEYS)
        print(mesh_info.keys())
        mesh_info_sizes = {}
        mesh_info_errors = []
        for mi, miv in mesh_info.items():
            error1 = not(mi in self.__class__.MESH_INFO_KEYS)
            error2 = False
            if not error1:
                sub_mi = mi.split('_')[0]
                if sub_mi in mesh_info_sizes.keys():
                    error2 = not(mesh_info_sizes[sub_mi] == len(miv))
            mesh_info_errors.append(error1 or error2)

        print(mesh_info_errors)
        return any(mesh_info_errors)

    #TODO
    @classmethod
    def _testMeshIndices(cls, local_mesh):
        return True

    #TODO: create a enum
    '''
    0  - NOTHING
    1  - JUST_MESH_INFO
    2  - JUST_LOCAL_MESH
    3  - BOTH_MAY_WRONG
    4  - BOTH_RIGHT
    '''

    def setMeshInfo(self, mesh_info: dict):     
        self._mesh_info = mesh_info

        if self._mesh_info is None:
            if self._mesh is None:
                return 0
            return 2

        #TODO: add a more robust logic, testing if the size of mesh info parts are equal to vertices of existing mesh
        if self._mesh is not None:
            self._mesh = None

        return 1

    def setMesh(self, local_mesh: Union[o3d.geometry.LineSet, o3d.geometry.TriangleMesh], mesh_info: dict = None):
        self.setMeshInfo(mesh_info)

        if self._mesh_info:
            self._mesh_info = None

        self._mesh = local_mesh
        return 2
    
    def setMeshByGlobal(self, global_mesh: Union[o3d.geometry.LineSet, o3d.geometry.TriangleMesh], mesh_info: dict):
        self._mesh = None

        if self.setMeshInfo(mesh_info) == 0:
            return 0
        
        return 1
        

        
