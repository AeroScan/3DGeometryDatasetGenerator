import numpy as np

from OCC.Core.GeomAbs import GeomAbs_CurveType, GeomAbs_SurfaceType
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCC.Core.TopoDS import TopoDS_Edge, TopoDS_Face

from .curves import (
    Line,
)

from .surfaces import (
    Plane,
)

CURVE_CLASSES = {
    'Line': Line,
}

SURFACE_CLASSES = {
    'Plane': Plane,
}

def generateBRepAdaptorObject(topods_shape):
    brep_adaptor = None
    if isinstance(topods_shape, TopoDS_Edge):
        brep_adaptor = BRepAdaptor_Curve(topods_shape)
    elif isinstance(topods_shape, TopoDS_Face):
        brep_adaptor = BRepAdaptor_Surface(topods_shape)
    else:
        assert False, f'Code is not ready to deal with {topods_shape.ShapeType()} type of Geometry.'
    
    return brep_adaptor

def toDict(brep_adaptor, mesh_data=None, transform=None):
    if isinstance(brep_adaptor, BRepAdaptor_Curve):
        cls_name = str(GeomAbs_CurveType(brep_adaptor.GetType())).split('_')[-1]
        if cls_name in CURVE_CLASSES:
            return CURVE_CLASSES[cls_name].toDict(brep_adaptor, mesh_data=mesh_data, transform=transform)
        else:
            return None
    elif isinstance(brep_adaptor, BRepAdaptor_Surface):
        cls_name = str(GeomAbs_SurfaceType(brep_adaptor.GetType())).split('_')[-1]
        if cls_name in SURFACE_CLASSES:
            return SURFACE_CLASSES[cls_name].toDict(brep_adaptor, mesh_data=mesh_data, transform=transform)
        else:
            return None
    else:
        assert False, f'Code is not ready to deal with {type(brep_adaptor)} type of Geometry.'
