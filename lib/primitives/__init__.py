from OCC.Core.GeomAbs import GeomAbs_CurveType, GeomAbs_SurfaceType
from OCC.Core.TopoDS import TopoDS_Edge, TopoDS_Face
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface

from .curves import (
    Line, Circle, Ellipse, BSpline
)

from .surfaces import (
    Plane, Cylinder, Cone, Sphere, Torus
)

CURVE_CLASSES = {
    GeomAbs_CurveType.GeomAbs_Line: Line,
    GeomAbs_CurveType.GeomAbs_Circle: Circle,
    GeomAbs_CurveType.GeomAbs_Ellipse: Ellipse,
    GeomAbs_CurveType.GeomAbs_BSplineCurve: BSpline,
}

SURFACE_CLASSES = {
    GeomAbs_SurfaceType.GeomAbs_Plane: Plane,
    GeomAbs_SurfaceType.GeomAbs_Cylinder: Cylinder,
    GeomAbs_SurfaceType.GeomAbs_Cone: Cone,
    GeomAbs_SurfaceType.GeomAbs_Sphere: Sphere,
    GeomAbs_SurfaceType.GeomAbs_Torus: Torus,
}

def toDict(topods, mesh_data=None, transforms=None):
    shape_orientation = topods.Orientation()

    if isinstance(topods, TopoDS_Edge):
        brep_adaptor = BRepAdaptor_Curve(topods)

        cls_name = GeomAbs_CurveType(brep_adaptor.GetType())
        if cls_name in CURVE_CLASSES:
            return CURVE_CLASSES[cls_name].toDict(brep_adaptor, mesh_data=mesh_data,
                                                  transforms=transforms, shape_orientation=shape_orientation)
        else:
            return None
        
    elif isinstance(topods, TopoDS_Face):
        brep_adaptor = BRepAdaptor_Surface(topods)

        cls_name = GeomAbs_CurveType(brep_adaptor.GetType())
        if cls_name in SURFACE_CLASSES:
            return SURFACE_CLASSES[cls_name].toDict(brep_adaptor, mesh_data=mesh_data,
                                                    transforms=transforms, shape_orientation=shape_orientation)
        else:
            return None
    else:
        assert False, f'Code is not ready to deal with {type(topods)} type of shape.'
