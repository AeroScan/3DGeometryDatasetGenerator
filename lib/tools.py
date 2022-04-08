import numpy as np
import pickle
import json
import yaml
import igl
import os
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity
from OCC.Core.Interface import Interface_Static_IVal, Interface_Static_SetCVal
from lib.TopologyUtils import list_of_shapes_to_compound

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

def writeMeshOBJ(filename, mesh):
    igl.write_triangle_mesh(f'{filename}.obj', mesh['vertices'], mesh['faces'])

POSSIBLE_UNITS = ['1', 'inch', 'mm', '??', 'ft', 'mi', 'm', 'km', 'mil', 'um', 'cm', 'uin']
def read_step(filename: str, as_compound: bool=True, verbosity: bool=True):
    if not os.path.isfile(filename):
        raise FileNotFoundError(f'{filename} not found.')

    step_reader = STEPControl_Reader()
    status = step_reader.ReadFile(filename)

    original_unit = POSSIBLE_UNITS[Interface_Static_IVal('xstep.cascade.unit')]
    print(f'Unidade original: {original_unit}')
    if original_unit != 'm':
        Interface_Static_SetCVal('xstep.cascade.unit', 'M')
        print(f'Convertivo para: {POSSIBLE_UNITS[Interface_Static_IVal("xstep.cascade.unit")]}')

    if status == IFSelect_RetDone:
        if verbosity:
            failsonly = False
            step_reader.PrintCheckLoad(failsonly, IFSelect_ItemsByEntity)
            step_reader.PrintCheckTransfer(failsonly, IFSelect_ItemsByEntity)
        transfer_result = step_reader.TransferRoots()
        if not transfer_result:
            raise AssertionError("Transfer failed.")
        _nbs = step_reader.NbShapes()
        if _nbs == 0:
            raise AssertionError("No shape to transfer.")
        elif _nbs == 1:  # most cases
            return step_reader.Shape(1)
        elif _nbs > 1:
            print("Number of shapes:", _nbs)
            shps = []
            # loop over root shapes
            for k in range(1, _nbs + 1):
                new_shp = step_reader.Shape(k)
                if not new_shp.IsNull():
                    shps.append(new_shp)
            if as_compound:
                compound, result = list_of_shapes_to_compound(shps)
                if not result:
                    print("Warning: all shapes were not added to the compound")
                return compound
            else:
                print("Warning, returns a list of shapes.")
                return shps
    else:
        raise AssertionError("Error: can't read file.")
    return None
