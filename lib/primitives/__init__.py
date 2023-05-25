from OCC.Core.GeomAdaptor import GeomAdaptor_Curve, GeomAdaptor_Surface
from OCC.Core.GeomAbs import GeomAbs_CurveType, GeomAbs_SurfaceType
from OCC.Core.TopoDS import TopoDS_Edge, TopoDS_Face
from OCC.Core.BRep import BRep_Tool

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

def toDict(topods, mesh_data=None, transforms=None):
    shape_orientation = topods.Orientation()

    if isinstance(topods, TopoDS_Edge):
        geom = BRep_Tool.Curve(topods)[0]
        geom_adaptor = GeomAdaptor_Curve(geom)

        cls_name = str(GeomAbs_CurveType(geom_adaptor.GetType())).split('_')[-1]
        if cls_name in CURVE_CLASSES:
            return CURVE_CLASSES[cls_name].toDict(geom_adaptor, mesh_data=mesh_data,
                                                  transforms=transforms, shape_orientation=shape_orientation)
        else:
            return None
        
    elif isinstance(topods, TopoDS_Face):
        geom = BRep_Tool.Surface(topods)
        geom_adaptor = GeomAdaptor_Surface(geom)

        cls_name = str(GeomAbs_SurfaceType(geom_adaptor.GetType())).split('_')[-1]
        if cls_name in SURFACE_CLASSES:
            return SURFACE_CLASSES[cls_name].toDict(geom_adaptor, mesh_data=mesh_data,
                                                    transforms=transforms, shape_orientation=shape_orientation)
        else:
            return None
    else:
        assert False, f'Code is not ready to deal with {type(topods)} type of shape.'
