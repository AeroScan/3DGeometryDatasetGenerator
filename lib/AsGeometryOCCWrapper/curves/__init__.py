from typing import Union

from OCC.Core.GeomAbs import GeomAbs_CurveType
from OCC.Core.TopoDS import TopoDS_Edge
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.GeomAdaptor import GeomAdaptor_Curve

from .line import Line
from .circle import Circle
from .ellipse import Ellipse
from .bspline import BSpline

class CurveFactory:

    CURVE_CLASSES = {
        GeomAbs_CurveType.GeomAbs_Line: Line,
        GeomAbs_CurveType.GeomAbs_Circle: Circle,
        GeomAbs_CurveType.GeomAbs_Ellipse: Ellipse,
        GeomAbs_CurveType.GeomAbs_BSplineCurve: BSpline,
    }

    @staticmethod
    def fromTopoDS(topods: TopoDS_Edge, transforms: list = []):
        brep_adaptor = BRepAdaptor_Curve(topods)
        return CurveFactory.fromAdaptor(brep_adaptor, transforms=transforms, face_orientation=topods.Orientation())

    @staticmethod
    def fromAdaptor(brep_adaptor: Union[BRepAdaptor_Curve, GeomAdaptor_Curve], transforms: list = [], face_orientation: int=0):
        cls_name = GeomAbs_CurveType(brep_adaptor.GetType())
        if cls_name in CurveFactory.CURVE_CLASSES:
            return CurveFactory.CURVE_CLASSES[cls_name](brep_adaptor, transforms=transforms, 
                                                        face_orientation=face_orientation)
        else:
            return None
    