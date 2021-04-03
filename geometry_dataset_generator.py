import gmsh

import argparse

import pprint

#import yaml

from tqdm import tqdm

import numpy as np


def generateBaseCurveFeature(node, type):
    node_tags, node_coords, node_params = node
    feature = {
        'type': type,
        'vert_indices': node_tags.tolist(),
        'vert_parameters': node_params.tolist(),
    }
    return feature

def generateBaseSurfaceFeature(node, elem, type):
    node_tags, node_coords, node_params = node
    elem_types, elem_tags, elem_node_tags = elem
    node_params = np.resize(node_params, (int(node_params.shape[0]/2), 2))
    feature = {
        'type': type,
        'vert_indices': node_tags.tolist(),
        'vert_parameters': node_params.tolist(),
        'face_indices': elem_tags[0].tolist(),
    }
    return feature


def generateLineFeature(dim, tag):
    node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)

    feature = generateBaseCurveFeature((node_tags, node_coords, node_params), 'Line')

    #aqui eh feita a busca dos outros parametros

    return feature

def generateCircleFeature(dim, tag):
    node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)

    feature = generateBaseCurveFeature((node_tags, node_coords, node_params), 'Circle')
    
    return feature

def generatePlaneFeature(dim, tag):
    node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)
    elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dim, tag)

    feature = generateBaseSurfaceFeature((node_tags, node_coords, node_params), (elem_types, elem_tags, elem_node_tags), 'Plane')

    #aqui eh feita a busca dos outros parametros

    return feature

def generateCylinderFeature(dim, tag):
    node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)
    elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dim, tag)

    feature = generateBaseSurfaceFeature((node_tags, node_coords, node_params), (elem_types, elem_tags, elem_node_tags), 'Cylinder')

    return feature

def generateConeFeature(dim, tag):
    node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)
    elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dim, tag)

    feature = generateBaseSurfaceFeature((node_tags, node_coords, node_params), (elem_types, elem_tags, elem_node_tags), 'Cone')

    return feature

def generateSphereFeature(dim, tag):
    node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)
    elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dim, tag)

    feature = generateBaseSurfaceFeature((node_tags, node_coords, node_params), (elem_types, elem_tags, elem_node_tags), 'Sphere')

    return feature

def generateTorusFeature(dim, tag):
    node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)
    elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dim, tag)

    feature = generateBaseSurfaceFeature((node_tags, node_coords, node_params), (elem_types, elem_tags, elem_node_tags), 'Torus')

    return feature


def generateFeature(dim, tag, type):
    generate_functions_dict = {
        'circle': generateCircleFeature,
        'line': generateLineFeature,
        'plane': generatePlaneFeature,
        'cylinder': generateCylinderFeature,
        'cone': generateConeFeature,
        'sphere': generateSphereFeature,
        'torus': generateTorusFeature,
    }
    if type.lower() in generate_functions_dict.keys():
        return generate_functions_dict[type.lower()](dim, tag)


def processMM(dim_info):
    model_composition = {}
    features = {}

    for dim, info in dim_info.items():
        name, _ = info
        features[name] = []

    print("\nGenerating Features...")
    for dim, tag in tqdm(entities):
        type = gmsh.model.getType(dim, tag)

        if dim in dim_info.keys() and type in dim_info[dim][1]:
            if type not in model_composition.keys():
                model_composition[type] = 1
            else:
                model_composition[type] += 1 

            feature = generateFeature(dim, tag, type)
            features[dim_info[dim][0]].append(feature)
    return model_composition, features

def float2str(n, limit = 10):
    if abs(n) >= 10**limit:
        return ('%.' + str(limit) + 'e') % n
    elif abs(n) <= 1/(10**limit):
        return ('%.' + str(limit) + 'e') % n
    else:
        return str(n)

def list2str(l, prefix, LINE_SIZE = 90):
    l = '[' + ', '.join(float2str(x) for x in l) + ']'
    text = ''
    last_end = -1
    last_com = 0
    for i, elem in enumerate(l):
        if elem == ',':
            if i > (last_end + 1 + (LINE_SIZE - len(prefix))):
                if last_end == -1:
                    text += l[last_end+1:last_com+1]+'\n'
                else:
                    text += prefix + l[last_end+2:last_com+1]+'\n'
                last_end = last_com
            last_com = i
    if last_end == -1:
        text += l[last_end+1:len(l)]
    else:
        text += prefix + l[last_end+2:len(l)]
    return text

def generateFeaturesYAML(d):
    result = ''
    for key, value in d.items():
        if len(value) == 0:
            result += key + ': []\n'
            continue
        result += key + ':\n'
        for d2 in value:
            result += '- '
            for key2, value2 in d2.items():
                if result[-2:] != '- ':
                    result += '  '
                result += key2 + ': '
                if type(value2) != list:
                    result += value2 + '\n'
                else:
                    if len(value2) == 0:
                        result += '[]\n'
                    elif type(value2[0]) != list:
                        result += list2str(value2, '    ') + '\n'
                    else:
                        result += '\n'
                        for elem in value2:
                            result += '  - ' + list2str(elem, '    ') + '\n'
    return result


if __name__ == '__main__':
    gmsh.initialize()

    parser = argparse.ArgumentParser(description='3D Geometry Dataset Generator.')
    parser.add_argument('input', type=str, help='input file in CAD formats.')
    parser.add_argument('output', type=str, help='output file name for mesh and features.')
    parser.add_argument("-v", "--visualize", action="store_true", help='visualize mesh')
    parser.add_argument("-l", "--log", action="store_true", help='show log of results')
    parser.add_argument('--mesh_size', type = float, default = 5, help='mesh size in meters.')
    args = vars(parser.parse_args())

    input_name = args['input']
    output_name = args['output']
    visualize = args['visualize']
    mesh_size = args['mesh_size']
    log = args['log']

    gmsh.model.occ.importShapes(input_name)
    #gmsh.model.occ.healShapes() ##Tratamento interessante para os shapes
    gmsh.model.occ.synchronize()

    print('\nProcessing Model {} ({}D)'.format(gmsh.model.getCurrent(), str(gmsh.model.getDimension())))    

    entities = gmsh.model.getEntities()

    gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
    gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
    gmsh.model.mesh.generate(2)
    #gmsh.model.mesh.refine()
    gmsh.model.mesh.optimize('', True)

    dim_name_types = {
        1 : ('curves', ['Line', 'Cicle']),
        2 : ('surfaces', ['Plane', 'Cylinder', 'Cone', 'Sphere', 'Torus'])
    }
    model_composition, features = processMM(dim_name_types)

    if log:
        pp = pprint.PrettyPrinter(indent=2)
        print('\n---------- LOG ----------')
        print('Dimensions considered and its information:')
        pp.pprint(dim_name_types)
        print('\nModel Composition:')
        pp.pprint(model_composition)

        print('\nFeatures:')
        print('- Curves:')
        for f in features['curves']:
            pp.pprint(f)

        print('\n- Surfaces:')
        for f in features['surfaces']:
            pp.pprint(f)
        print('---------- END LOG ----------')

    gmsh.write(output_name + '.stl')

    # pp = pprint.PrettyPrinter(indent=2)
    # pp.pprint(features)
    with open(output_name + '.yaml', 'w') as f:
        features_yaml = generateFeaturesYAML(features)
        f.write(features_yaml)

    gmsh.model.setVisibility(gmsh.model.getEntities(3), 0)
    gmsh.model.setColor(gmsh.model.getEntities(2), 249, 166, 2)
    if visualize:
        gmsh.fltk.run()


    gmsh.finalize()
