import numpy as np

def generateAreaFromSurface(surface, vertices:list, faces: list):
    area_of_surface = 0.0
    try:
        face_indices = surface.face_indices
    except:
        face_indices = surface["face_indices"]

    for id in face_indices:
        triangle = faces[id].tolist()

        A = vertices[triangle[0]]
        
        B = vertices[triangle[1]]
        
        C = vertices[triangle[2]]

        area =  np.linalg.norm(np.cross((B - A), (C - A)))/2

        area_of_surface += area
    
    return area_of_surface

def generateStatistics(features, mesh, only_stats=False):
    result = {}
    result['number_vertices'] = len(mesh['vertices'])
    result['number_faces'] = len(mesh['faces'])
    result['number_curves'] = len(features['curves'])
    result['number_surfaces'] = len(features['surfaces'])

    curves_dict = {}
    surfaces_dict = {}
    if only_stats:
        for curve in features["curves"]:
            if curve is not None:
                tp = curve["type"]
                if tp not in curves_dict:
                    curves_dict[tp] = {'number_vertices': 0, 'number_curves': 0}
                curves_dict[tp]['number_vertices'] += len(curve["vert_indices"])
                curves_dict[tp]['number_curves'] += 1
        result['curves'] = curves_dict
        # ----------------------------- #
        surfaces_dict['area'] = 0.0
        total_area_of_surfaces = 0.0
        for surface in features['surfaces']:
            if surface is not None:
                tp = surface["type"]
                if tp not in surfaces_dict:
                    surfaces_dict[tp] = {'number_vertices': 0, 'number_faces': 0, 'number_surfaces': 0, 'area': 0}
                surface_area = generateAreaFromSurface(surface, mesh["vertices"], mesh["faces"])
                surfaces_dict[tp]['number_vertices'] += len(surface["vert_indices"])
                surfaces_dict[tp]['number_faces'] += len(surface["face_indices"])
                surfaces_dict[tp]['number_surfaces'] += 1
                surfaces_dict[tp]['area'] += surface_area
            total_area_of_surfaces += surface_area
        surfaces_dict['area'] = total_area_of_surfaces
        result['surfaces'] = surfaces_dict 
    else:
        for curve in features['curves']:
            if curve is not None:
                tp = curve.primitiveType() if curve.primitiveType() != 'BaseCurve' else 'Other'
                if tp not in curves_dict:
                    curves_dict[tp] = {'number_vertices': 0, 'number_curves': 0}
                curves_dict[tp]['number_vertices'] += len(curve.vert_indices)
                curves_dict[tp]['number_curves'] += 1
        result['curves'] = curves_dict
        # ----------------------------- #
        surfaces_dict['area'] = 0.0
        total_area_of_surfaces = 0.0
        for surface in features['surfaces']:
            if surface is not None:
                tp = surface.primitiveType() if surface.primitiveType() != 'BaseSurface' else 'Other'
                if tp not in surfaces_dict:
                    surfaces_dict[tp] = {'number_vertices': 0, 'number_faces': 0, 'number_surfaces': 0, 'area': 0}
                surface_area = generateAreaFromSurface(surface, mesh["vertices"], mesh["faces"])
                surfaces_dict[tp]['number_vertices'] += len(surface.vert_indices)
                surfaces_dict[tp]['number_faces'] += len(surface.face_indices)
                surfaces_dict[tp]['number_surfaces'] += 1
                surfaces_dict[tp]['area'] += surface_area
            total_area_of_surfaces += surface_area
        surfaces_dict['area'] = total_area_of_surfaces
        result['surfaces'] = surfaces_dict 
    return result