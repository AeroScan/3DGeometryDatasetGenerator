from OCC.Core.GeomAbs import GeomAbs_CurveType
from OCC.Core.gp import gp_Ax1
import numpy as np

from lib.tools import gpXYZ2List

class BaseCurve:

    GEOM_LINE_TYPE = [GeomAbs_CurveType.GeomAbs_Line]
    GEOM_CONIC_TYPE = [GeomAbs_CurveType.GeomAbs_Circle, GeomAbs_CurveType.GeomAbs_Ellipse,
                       GeomAbs_CurveType.GeomAbs_Hyperbola, GeomAbs_CurveType.GeomAbs_Parabola]
    GEOM_BOUNDED_TYPE = [GeomAbs_CurveType.GeomAbs_BezierCurve, GeomAbs_CurveType.GeomAbs_BSplineCurve]
    GEOM_OTHERS_TYPE = [GeomAbs_CurveType.GeomAbs_OffsetCurve, GeomAbs_CurveType.GeomAbs_OtherCurve]

    @classmethod
    def toDict(cls, adaptor, mesh_data=None, transforms=None, shape_orientation=0):        
        if transforms is None:
            transforms = []
        
        shape = getattr(adaptor, cls.__name__)()

        for T in transforms:
            shape.Transform(T)

        features = {}
        features['type'] = cls.__name__

        tp = GeomAbs_CurveType(adaptor.GetType())

        if tp in BaseCurve.GEOM_LINE_TYPE:
            
            if shape_orientation == 1:
                old_direction = np.array(gpXYZ2List(shape.Direction()))
                shape.Reverse()
                new_direction = np.array(gpXYZ2List(shape.Direction()))
                
                assert np.all(new_direction == -old_direction), f'Problem in reversing a {str(tp)}.'

            features['location'] = gpXYZ2List(shape.Location())
            features['direction'] = gpXYZ2List(shape.Direction())
            
        elif tp in BaseCurve.GEOM_CONIC_TYPE:

            if shape_orientation == 1:
                old_loc = np.array(gpXYZ2List(shape.Location()))
                old_axis = np.array(gpXYZ2List(shape.Axis().Direction()))
                shape.Mirror(shape.Position().Axis())
                new_loc = np.array(gpXYZ2List(shape.Location()))
                new_axis = np.array(gpXYZ2List(shape.Axis().Direction()))
                print(old_axis, new_axis)
                
                assert np.all(old_axis == -new_axis) and np.all(old_loc == new_loc), f'Problem in reversing a {str(tp)}.'

            features['location'] = gpXYZ2List(shape.Location())
            features['x_axis'] = gpXYZ2List(shape.XAxis().Direction())
            features['y_axis'] = gpXYZ2List(shape.YAxis().Direction())
            features['z_axis'] = gpXYZ2List(shape.Axis().Direction())
        
        elif tp in BaseCurve.GEOM_BOUNDED_TYPE:
            if shape_orientation == 1:
                old_fp = shape.FirstParameter()
                old_lp = shape.LastParameter()
                shape.Reverse()
                new_fp = shape.FirstParameter()
                new_lp = shape.LastParameter()
                assert np.all(old_fp == new_lp) and np.all(old_lp == new_fp), f'Problem in reversing a {str(tp)}.'

        if mesh_data is not None:
            features['sharp'] = mesh_data['sharp'] if 'sharp' in mesh_data.keys() else True
            features['vert_indices'] = mesh_data['vert_indices'] if 'vert_indices' in mesh_data.keys() else []
            features['vert_parameters'] = mesh_data['vert_parameters'] if 'vert_parameters' in mesh_data.keys() else []

        return shape, features