from lib.tools import gpXYZ2List
from OCC.Core.gp import gp_Trsf

class Plane:

    @classmethod
    def toDict(cls, brep_adaptor, mesh_data=None, transform=None):        
        if transform is None:
            transform = gp_Trsf()
        
        plane = brep_adaptor.Plane()

        plane.Transform(transform)

        features = {}
        features['type'] = cls.__name__
        features['location'] = gpXYZ2List(plane.Location())
        features['x_axis'] = gpXYZ2List(plane.XAxis().Direction())
        features['y_axis'] = gpXYZ2List(plane.YAxis().Direction())
        features['z_axis'] = gpXYZ2List(plane.Axis().Direction())
        features['coefficients'] = list(plane.Coefficients())
        features['normal'] = gpXYZ2List(plane.Axis().Direction())

        features['vert_indices'] = mesh_data['vert_indices'] if 'vert_indices' in mesh_data.keys() else []
        features['vert_parameters'] = mesh_data['vert_parameters'] if 'vert_parameters' in mesh_data.keys() else []
        features['face_indices'] = mesh_data['face_indices'] if 'face_indices' in mesh_data.keys() else []

        return features