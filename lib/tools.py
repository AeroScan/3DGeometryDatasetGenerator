import os
import numpy as np
import pickle
import json
import yaml
import open3d as o3d
from pathlib import Path

CAD_FORMATS = ['.step', '.stp', '.STEP']
MESH_FORMATS = ['.OBJ', '.obj']
FEATURES_FORMATS = ['.pkl', '.PKL', '.yml', '.yaml', '.YAML', '.json', '.JSON']

# Convert a float to string
def float2str(number, limit = 10) -> str:
    if abs(number) >= 10**limit:
        return ('%.' + str(limit) + 'e') % number
    elif abs(number) <= 1/(10**limit) and number != 0:
        return ('%.' + str(limit) + 'e') % number
    elif type(number) == int and number == 0:
        return str(0)
    elif number == 0.0:
        return str(0.0)
    else:
        return str(number)

# Convert a list to string
def list2str(l: list, prefix, LINE_SIZE = 90) -> str:
    l = '[' + ', '.join(float2str(n) for n in l) + ']'
    string = '' 
    last_end = -1
    last_com = 0
    for i, element in enumerate(l):
        if element == ',':
            if i > (last_end + 1 + (LINE_SIZE - len(prefix))):
                if last_end == -1:
                    string += l[last_end + 1:last_com + 1] + '\n'
                else:
                    string += prefix + l[last_end + 2: last_com + 1] + '\n'
                last_end = last_com
            last_com = i
    if last_end == -1:
        string += l[last_end + 1:len(l)]
    else:
        string += prefix + l[last_end + 2:len(l)]
    return string

# Convert a dict to string
def generateFeaturesYAML(features: dict) -> str:
    result = ''
    for key, value in features.items():
        if len(value) == 0:
            result += key + ': []\n'
            continue
        result += key + ':\n'
        
        while len(value) > 0:
            d = value[0]
            result += '- '
            for key2, value2 in d.items():
                if result[-2:] != '- ':
                    result += '  '
                result += key2 + ': '
                if type(value2).__module__ == np.__name__:
                    value2 = value2.tolist()
                if type(value2) != list:
                    result += str(value2) + '\n'
                else:
                    if len(value2) == 0:
                        result += '[]\n'
                    elif type(value2[0]) != list:
                        result += list2str(value2, '    ') + '\n'
                    else:
                        result += '\n'
                        for elem in value2:
                            result += '  - ' + list2str(elem, '    ') + '\n'
            value.pop(0)
    return result

# Convert the gpXYZ (gmsh data) to list
def gpXYZ2List(gp):
    return [gp.X(), gp.Y(), gp.Z()]


YAML_NAMES = ['yaml', 'yml']
JSON_NAMES = ['json']
PKL_NAMES  = ['pkl']

# Write features file
def writeYAML(features_name: str, features: dict):
    with open(features_name, 'w') as f:
        features_yaml = generateFeaturesYAML(features)
        f.write(features_yaml)

def writeJSON(features_name: str, features: dict):
    with open(features_name, 'w') as f:
        json.dump(features, f, indent=4)

def writePKL(features_name: str, features: dict):
    with open(features_name, 'wb') as f:
        pickle.dump(features, f)

def writeFeatures(features_name: str, features: dict, tp: str):
    for feature in features['surfaces']:
        if feature['face_indices'] is None:
            print(feature)
    if tp.lower() in YAML_NAMES:
        writeYAML(f'{features_name}.{tp}', features)
    elif tp.lower() in PKL_NAMES:
        writePKL(f'{features_name}.{tp}', features)
    else:
        writeJSON(f'{features_name}.{tp}', features)

# Load features file
def loadYAML(features_name: str):
    with open(features_name, 'r') as f:
        data = yaml.load(f, Loader=yaml.Loader)
    return data

def loadJSON(features_name: str):
    with open(features_name, 'r') as f:
        data = json.load(f)
    return data

def loadPKL(features_name: str):
    with open(features_name, 'rb') as f:
        data = pickle.load(f)
    return data

def loadFeatures(features_name: str, tp: str):
    if tp.lower() in YAML_NAMES:
        return loadYAML(f'{features_name}.{tp}')
    elif tp.lower() in PKL_NAMES:
        return loadPKL(f'{features_name}.{tp}')
    else:
        return loadJSON(f'{features_name}.{tp}')

def filterFeaturesData(features_data, curve_types, surface_types):
    i = 0
    while i < len(features_data['curves']):
        feature = features_data['curves'][i]
        if feature['type'].lower() not in curve_types:
            features_data['curves'].pop(i)
        else:
            i+=1

    i = 0
    while i < len(features_data['surfaces']):
        feature = features_data['surfaces'][i]
        if feature['type'].lower() not in surface_types:
            features_data['surfaces'].pop(i)
        else:
            i+=1 

def writeMeshOBJ(filename, mesh_dict):
    mesh = o3d.geometry.TriangleMesh()
    mesh.vertices = o3d.utility.Vector3dVector(np.asarray(mesh_dict['vertices']))
    mesh.triangles = o3d.utility.Vector3iVector(np.asarray(mesh_dict['faces']))
    o3d.io.write_triangle_mesh(filename + '.obj', mesh, print_progress=True)

def loadMeshOBJ(filename):
    mesh = o3d.io.read_triangle_mesh(str(filename) + '.obj', print_progress=True)
    v, f = np.asarray(mesh.vertices), np.asarray(mesh.triangles)
    mesh = {'vertices': v, 'faces': f}
    return mesh

def list_files(input_dir: str, formats: list, return_str=False) -> list:
    files = []
    path = Path(input_dir)
    for file_path in path.glob('*'):
        if file_path.suffix.lower() in formats:
            files.append(file_path if not return_str else str(file_path))
    return sorted(files)

def output_name_converter(input_path, formats):
    filename = str(input_path).split('/')[-1]
    
    for f in formats:
        if f in filename:
            filename = filename.replace(f, '')
    return filename

def rotation_matrix_from_vectors(vec1, vec2=np.array([0., 0., 1.])):
    """ Find the rotation matrix that aligns vec1 to vec2
    :param vec1: A 3d "source" vector
    :param vec2: A 3d "destination" vector
    :return mat: A transform matrix (3x3) which when applied to vec1, aligns it with vec2.
    https://stackoverflow.com/questions/45142959/calculate-rotation-matrix-to-align-two-vectors-in-3d-space
    """
    a, b = (vec1 / np.linalg.norm(vec1)).reshape(3), (vec2 / np.linalg.norm(vec2)).reshape(3)
    v = np.cross(a, b)
    if any(v): #if not all zeros then
        c = np.dot(a, b)
        s = np.linalg.norm(v)
        kmat = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        return np.eye(3) + kmat + kmat.dot(kmat) * ((1 - c) / (s ** 2))

    else:
        return np.eye(3) #cross of all zeros only occurs on identical directions

def computeTranslationVector(vertices):
    bounding_box_min = np.min(vertices, axis=0).tolist()
    bounding_box_max = np.max(vertices, axis=0).tolist()
    tx = - (bounding_box_max[0] + bounding_box_min[0]) * 0.5
    ty = - (bounding_box_max[1] + bounding_box_min[1]) * 0.5
    tz = - bounding_box_min[2]
    t = np.array([tx, ty, tz])

    return t

def get_files_from_input_path(input_path):
    """ To get files from input path """
    if os.path.exists(input_path):
        if os.path.isdir(input_path):
            files = list_files(input_path, CAD_FORMATS)
        else:
            files = [input_path]
    else:
        raise FileNotFoundError("Input path not found.")

    return files

def create_dirs(*directories):
    """ To create the directories """
    try:
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    except OSError as os_error:
        raise OSError from os_error
