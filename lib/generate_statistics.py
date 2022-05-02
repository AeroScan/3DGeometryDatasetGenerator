

def generateStatistics(features, mesh):
    result = {}
    result['number_vertices'] = len(mesh['vertices'])
    result['number_faces'] = len(mesh['faces'])
    result['number_curves'] = len(features['curves'])
    result['number_surfaces'] = len(features['surfaces'])
    curves_dict = {}
    for curve in features['curves']:
        if curve['type'] not in curves_dict:
            curves_dict[curve['type']] = {'number_vertices': 0, 'number_curves': 0}
        curves_dict[curve['type']]['number_vertices'] += len(curve['vert_indices'])
        curves_dict[curve['type']]['number_curves'] += 1
    result['curves'] = curves_dict
    surfaces_dict = {}
    for surface in features['surfaces']:
        if surface['type'] not in surfaces_dict:
            surfaces_dict[surface['type']] = {'number_vertices': 0, 'number_faces': 0, 'number_surfaces': 0}
        surfaces_dict[surface['type']]['number_vertices'] += len(surface['vert_indices'])
        surfaces_dict[surface['type']]['number_faces'] += len(surface['face_indices'])
        surfaces_dict[surface['type']]['number_surfaces'] += 1
    result['surfaces'] = surfaces_dict 
    return result