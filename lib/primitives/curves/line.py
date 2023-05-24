from lib.tools import gpXYZ2List
from OCC.Core.gp import gp_Trsf

class Line:

    @classmethod
    def toDict(cls, brep_adaptor, mesh_data=None, transform=None):        
        if transform is None:
            transform = gp_Trsf()
        
        line = brep_adaptor.Line()

        line.Transform(transform)

        features = {}
        features['type'] = cls.__name__
        features['location'] = gpXYZ2List(line.Location())
        features['direction'] = gpXYZ2List(line.Direction())

        features['sharp'] = mesh_data['sharp'] if 'sharp' in mesh_data.keys() else True
        features['vert_indices'] = mesh_data['vert_indices'] if 'vert_indices' in mesh_data.keys() else []
        features['vert_parameters'] = mesh_data['vert_parameters'] if 'vert_parameters' in mesh_data.keys() else []

        return features