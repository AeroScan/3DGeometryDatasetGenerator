from typing import Union

from OCC.Core.GeomAbs import GeomAbs_SurfaceType
from OCC.Core.TopoDS import TopoDS_Face
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.GeomAdaptor import GeomAdaptor_Surface

from .cone import Cone
from .plane import Plane
from .torus import Torus
from .sphere import Sphere
from .cylinder import Cylinder
#from .extrusion import Extrusion
#from .revolution import Revolution
from .bspline_surface import BSplineSurface

class SurfaceFactory:

    SURFACE_CLASSES = {
        GeomAbs_SurfaceType.GeomAbs_Plane: Plane,
        GeomAbs_SurfaceType.GeomAbs_Cylinder: Cylinder,
        GeomAbs_SurfaceType.GeomAbs_Cone: Cone,
        GeomAbs_SurfaceType.GeomAbs_Sphere: Sphere,
        GeomAbs_SurfaceType.GeomAbs_Torus: Torus,
        GeomAbs_SurfaceType.GeomAbs_BSplineSurface: BSplineSurface
    }
    @staticmethod
    def fromTopoDS(topods: TopoDS_Face, transforms: list = []):
        brep_adaptor = BRepAdaptor_Surface(topods)
        return SurfaceFactory.fromAdaptor(brep_adaptor, transforms=transforms, face_orientation=topods.Orientation())

    @staticmethod
    def fromAdaptor(brep_adaptor: Union[BRepAdaptor_Surface, GeomAdaptor_Surface], transforms: list = [], face_orientation: int=0):
        cls_name = GeomAbs_SurfaceType(brep_adaptor.GetType())
        if cls_name in SurfaceFactory.SURFACE_CLASSES:
            return SurfaceFactory.SURFACE_CLASSES[cls_name](brep_adaptor, transforms=transforms, 
                                                        face_orientation=face_orientation)
        else:
            return None
    