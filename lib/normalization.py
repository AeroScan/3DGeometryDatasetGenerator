from OCC.Core.gp import gp_Trsf, gp_GTrsf, gp_Mat
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_GTransform

from math import radians

class Normalization:

    @staticmethod
    def translate_shp(shp, vec, copy=False):
        if shp is None:
            raise AssertionError("[NORMALIZATION] Shape is Null.")

        trns = gp_Trsf()
        trns.SetTranslation(vec)
        brep_trns = BRepBuilderAPI_Transform(shp, trns, copy)
        brep_trns.Build()
        shp = brep_trns.Shape()

        return shp

    @staticmethod
    def rotate_shp(shp, axis, angle, unit="deg"):
        if shp is None:
            raise AssertionError("[NORMALIZATION] Shape is Null.")

        if unit == "deg":
            angle = radians(angle)

        trns = gp_Trsf()
        trns.SetRotation(axis, angle)
        brep_trns = BRepBuilderAPI_Transform(shp, trns, False)
        brep_trns.Build()
        shp = brep_trns.Shape()
        
        return shp
    
    @staticmethod
    def scale_shp(shp, fx, fy, fz):
        if shp is None:
            raise AssertionError("[NORMALIZATION] Shape is Null.")

        scale_trsf = gp_GTrsf()
        rot = gp_Mat(fx, 0.0, 0.0, 0.0, fy, 0.0, 0.0, 0.0, fz)
        scale_trsf.SetVectorialPart(rot)
        brep_trsf = BRepBuilderAPI_GTransform(shp, scale_trsf)
        shp = brep_trsf.Shape()

        return shp