from lib.tools import gpXYZ2List
import copy
class BaseCurve:

    GEOM_LINE_TYPES = ['gp_Lin']
    GEOM_CONIC_TYPES = ['gp_Circ', 'gp_Elips', 'gp_Hypr', 'gp_Parab']
    GEOM_BOUNDEDCURVE_TYPES = ['Geom_BSplineCurve', 'Geom_BezierCurve', 'Geom_TrimmedCurve']

    @classmethod
    def toDict(cls, brep_adaptor, mesh_data=None, transforms=None):        
        if transforms is None:
            transforms = []

        orientation = brep_adaptor.Edge().Orientation()
        
        shape = getattr(brep_adaptor, cls.__name__)()

        for T in transforms:
            shape.Transform(T)

        features = {}
        features['type'] = cls.__name__

        if shape.__class__.__name__ in GEOM_LINE_TYPES:
            features['location'] = gpXYZ2List(shape.Location())
            features['direction'] = gpXYZ2List(shape.Direction())
            
        elif isinstance(brep_adaptor, Geom_Conic):
            features['location'] = gpXYZ2List(shape.Location())
            features['x_axis'] = gpXYZ2List(shape.XAxis())
            features['y_axis'] = gpXYZ2List(shape.YAxis())
            features['z_axis'] = gpXYZ2List(shape.ZAxis())

        if mesh_data is not None:
            features['sharp'] = mesh_data['sharp'] if 'sharp' in mesh_data.keys() else True
            features['vert_indices'] = mesh_data['vert_indices'] if 'vert_indices' in mesh_data.keys() else []
            features['vert_parameters'] = mesh_data['vert_parameters'] if 'vert_parameters' in mesh_data.keys() else []

        print(features)

        return shape, features