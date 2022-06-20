

def generateStatistics(features, mesh):
    result = {}
    result['number_vertices'] = len(mesh['vertices'])
    result['number_faces'] = len(mesh['faces'])
    result['number_curves'] = len(features['curves'])
    result['number_surfaces'] = len(features['surfaces'])
    curves_dict = {}
    for curve in features['curves']:
        tp = curve.primitiveType() if curve.primitiveType() != 'BaseCurve' else 'Other'
        if tp not in curves_dict:
            curves_dict[tp] = {'number_vertices': 0, 'number_curves': 0}
        curves_dict[tp]['number_vertices'] += len(curve.vert_indices)
        curves_dict[tp]['number_curves'] += 1
    result['curves'] = curves_dict
    surfaces_dict = {}
    for surface in features['surfaces']:
        tp = surface.primitiveType() if surface.primitiveType() != 'BaseSurface' else 'Other'
        if tp not in surfaces_dict:
            surfaces_dict[tp] = {'number_vertices': 0, 'number_faces': 0, 'number_surfaces': 0}
        surfaces_dict[tp]['number_vertices'] += len(surface.vert_indices)
        surfaces_dict[tp]['number_faces'] += len(surface.face_indices)
        surfaces_dict[tp]['number_surfaces'] += 1
    result['surfaces'] = surfaces_dict 
    return result