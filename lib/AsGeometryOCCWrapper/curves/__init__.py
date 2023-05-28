from typing import Union

from OCC.Core.GeomAbs import GeomAbs_CurveType
from OCC.Core.TopoDS import TopoDS_Edge
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.GeomAdaptor import GeomAdaptor_Curve
from OCC.Core.Geom import Geom_Curve

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

    @classmethod
    def adaptor2Geom(cls, adaptor: Union[BRepAdaptor_Curve, GeomAdaptor_Curve]):
        cls_type = GeomAbs_CurveType(adaptor.GetType())
        if cls_type in cls.CURVE_CLASSES:
            geom = cls.CURVE_CLASSES[cls_type].adaptor2Geom(adaptor)
            return geom, cls_type

    @classmethod
    def fromTopoDS(cls, topods: TopoDS_Edge):
        brep_adaptor = BRepAdaptor_Curve(topods)
        return cls.fromAdaptor(brep_adaptor, topods_orientation=topods.Orientation())
        
    @classmethod
    def fromAdaptor(cls, adaptor: Union[BRepAdaptor_Curve, GeomAdaptor_Curve], topods_orientation: int = 0):
        r = cls.adaptor2Geom(adaptor)
        if r is not None:
            return cls.fromGeom(r[0], topods_orientation=topods_orientation, cls_type=r[1])
    
    @classmethod
    def fromGeom(cls, geom: Geom_Curve, topods_orientation: int = 0, cls_type: GeomAbs_CurveType = None):
        if cls_type is None:
            cls_type = GeomAbs_CurveType(GeomAdaptor_Curve(geom).GetType())

        if cls_type in cls.CURVE_CLASSES:
            return cls.CURVE_CLASSES[cls_type](geom, topods_orientation=topods_orientation)
        else:
            return None
    