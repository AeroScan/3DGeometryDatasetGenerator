from OCC.Core.GeomAbs import GeomAbs_SurfaceType
import numpy as np

from lib.tools import gpXYZ2List

class BaseSurface:

    GEOM_ELEMENTARY_TYPE = [GeomAbs_SurfaceType.GeomAbs_Plane, GeomAbs_SurfaceType.GeomAbs_Cylinder,
                            GeomAbs_SurfaceType.GeomAbs_Cone, GeomAbs_SurfaceType.GeomAbs_Torus,
                            GeomAbs_SurfaceType.GeomAbs_Sphere]
    GEOM_BOUNDED_TYPE = [GeomAbs_SurfaceType.GeomAbs_BSplineSurface, GeomAbs_SurfaceType.GeomAbs_BezierSurface]
    GEOM_SWEPT_TYPE = [GeomAbs_SurfaceType.GeomAbs_SurfaceOfExtrusion, GeomAbs_SurfaceType.GeomAbs_SurfaceOfRevolution]
    GEOM_OTHERS_TYPE = [GeomAbs_SurfaceType.GeomAbs_OffsetSurface, GeomAbs_SurfaceType.GeomAbs_OtherSurface]

    @classmethod
    def toDict(cls, geom_adaptor, mesh_data=None, transforms=None, shape_orientation=0):        
        if transforms is None:
            transforms = []
        
        shape = getattr(geom_adaptor, cls.__name__)()

        for T in transforms:
            shape.Transform(T)

        features = {}
        features['type'] = cls.__name__

        tp = GeomAbs_SurfaceType(geom_adaptor.GetType())

        if tp in BaseSurface.GEOM_ELEMENTARY_TYPE:
            
            if shape_orientation == 1:
                old_loc = np.array(gpXYZ2List(shape.Location()))
                old_axis = np.array(gpXYZ2List(shape.Axis().Direction()))
                shape.Mirror(shape.Position().Ax2())
                new_loc = np.array(gpXYZ2List(shape.Location()))
                new_axis = np.array(gpXYZ2List(shape.Axis().Direction()))
                
                assert np.all(old_axis == -new_axis) and np.all(old_loc == new_loc), f'Problem in reversing a {tp}.'

            features['location'] = gpXYZ2List(shape.Location())
            features['x_axis'] = gpXYZ2List(shape.XAxis().Direction())
            features['y_axis'] = gpXYZ2List(shape.YAxis().Direction())
            features['z_axis'] = gpXYZ2List(shape.Axis().Direction())
            features['coefficients'] = list(shape.Coefficients())
        
        if tp in BaseSurface.GEOM_BOUNDED_TYPE:
            if shape_orientation == 1:
                old_bounds = shape.Bounds()
                old_us, old_vs = old_bounds[:2], old_bounds[2:]
                shape.UReverse()
                shape.VReverse()
                new_bounds = shape.Bounds()
                new_us, new_vs = new_bounds[:2], new_bounds[2:]
                
                assert old_us == new_us[::-1] and old_vs == new_vs[::-1], f'Problem in reversing a {tp}.'

        if tp in BaseSurface.GEOM_SWEPT_TYPE:
            pass
            #features['curve'] = shape.BasisCurve()

        if mesh_data is not None:
            features['vert_indices'] = mesh_data['vert_indices'] if 'vert_indices' in mesh_data.keys() else []
            features['vert_parameters'] = mesh_data['vert_parameters'] if 'vert_parameters' in mesh_data.keys() else []
            features['face_indices'] = mesh_data['face_indices'] if 'face_indices' in mesh_data.keys() else []

        return shape, features