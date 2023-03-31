import numpy as np

def lineseg_dist(p, a, b):

    # normalized tangent vector
    d = np.divide(b - a, np.linalg.norm(b - a))

    # signed parallel distance components
    s = np.dot(a - p, d)
    t = np.dot(p - b, d)

    # clamped parallel distance
    h = np.maximum.reduce([s, t, 0])

    # perpendicular distance component
    c = np.cross(p - a, d)

    return np.hypot(h, np.linalg.norm(c))

def distance_between_two_points(a, b):
    squared_dist = np.sum((a-b)**2, axis=0)
    return np.sqrt(squared_dist)

def generateAreaFromSurface(surface, vertices:list, faces: list):
    try:
        face_indices = surface.face_indices
    except:
        face_indices = surface["face_indices"]

    for face in face_indices:
        faces = faces[face]
        
        face_index = faces.tolist()
        
        v1 = vertices[face_index[0]]
        
        v2 = vertices[face_index[1]]
        
        v3 = vertices[face_index[2]]

        height = lineseg_dist(v1, v2, v3)
        base = distance_between_two_points(v2, v3)

        return height * base

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