import gmsh

import argparse

import pprint

from tqdm import tqdm

import numpy as np

from OCC.Core.GeomAbs import (GeomAbs_CurveType, GeomAbs_SurfaceType)
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.TopoDS import TopoDS_Face
from OCC.Extend.DataExchange import read_step_file
from OCC.Extend.TopologyUtils import TopologyExplorer

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

def gpXYZ2List(gp):
    return [gp.X(), gp.Y(), gp.Z()]

def generateLineFeature(dim, shp, tag):
    node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)

    feature = generateBaseCurveFeature((node_tags, node_coords, node_params), 'Line')

    shape = shp.Line()

    feature = {
        'location': gpXYZ2List(shape.Location()),
        'direction': gpXYZ2List(shape.Direction()),
    }

    return feature

def generateCircleFeature(dim, shp, tag):
    node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)

    feature = generateBaseCurveFeature((node_tags, node_coords, node_params), 'Circle')
    
    shape = shp.Circle()

    feature = {
        'location': gpXYZ2List(shape.Location()),
        'z_axis': gpXYZ2List(shape.Axis().Direction()),
        'radius': shape.Radius(),
        'x_axis': gpXYZ2List(shape.XAxis().Direction()),
        'y_axis': gpXYZ2List(shape.YAxis().Direction()),
    }

    return feature

def generateEllipseFeature(dim, shp, tag):
    node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)

    feature = generateBaseCurveFeature((node_tags, node_coords, node_params), 'Ellipse')
    
    shape = shp.Ellipse()

    feature = {
        'focus1': gpXYZ2List(shape.Focus1()),
        'focus2': gpXYZ2List(shape.Focus2()),
        'x_axis': gpXYZ2List(shape.XAxis().Direction()),
        'y_axis': gpXYZ2List(shape.YAxis().Direction()),
        'z_axis': gpXYZ2List(shape.Axis().Direction()),
        'x_radius': shape.MajorRadius(),
        'y_radius': shape.MinorRadius(),
    }

    return feature

def generatePlaneFeature(dim, shp, tag):
    node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)
    elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dim, tag)

    feature = generateBaseSurfaceFeature((node_tags, node_coords, node_params), (elem_types, elem_tags, elem_node_tags), 'Plane')

    shape = shp.Plane()

    feature = {
        'location': gpXYZ2List(shape.Location()),
        'normal': gpXYZ2List(shape.Axis().Direction()),
        'x_axis': gpXYZ2List(shape.XAxis().Direction()),
        'y_axis': gpXYZ2List(shape.YAxis().Direction()),
        'z_axis': gpXYZ2List(shape.Axis().Direction()),
        'coefficients': list(shape.Coefficients()),
    }

    return feature

def generateCylinderFeature(dim, shp, tag):
    node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)
    elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dim, tag)

    feature = generateBaseSurfaceFeature((node_tags, node_coords, node_params), (elem_types, elem_tags, elem_node_tags), 'Cylinder')

    shape = shp.Cylinder()

    feature = {
        'location': gpXYZ2List(shape.Location()),
        'x_axis': gpXYZ2List(shape.XAxis().Direction()),
        'y_axis': gpXYZ2List(shape.YAxis().Direction()),
        'z_axis': gpXYZ2List(shape.Axis().Direction()),
        'coefficients': list(shape.Coefficients()),
        'radius': shape.Radius(),
    }

    return feature

def generateConeFeature(dim, shp, tag):
    node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)
    elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dim, tag)

    feature = generateBaseSurfaceFeature((node_tags, node_coords, node_params), (elem_types, elem_tags, elem_node_tags), 'Cone')

    shape = shp.Cone()

    feature = {
        'location': gpXYZ2List(shape.Location()),
        'x_axis': gpXYZ2List(shape.XAxis().Direction()),
        'y_axis': gpXYZ2List(shape.YAxis().Direction()),
        'z_axis': gpXYZ2List(shape.Axis().Direction()),
        'coefficients': list(shape.Coefficients()),
        'radius': shape.Radius(),
        'angle': shape.SemiAngle(),
        'apex': gpXYZ2List(shape.Apex()),
    }

    return feature

def generateSphereFeature(dim, shp, tag):
    node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)
    elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dim, tag)

    feature = generateBaseSurfaceFeature((node_tags, node_coords, node_params), (elem_types, elem_tags, elem_node_tags), 'Sphere')

    shape = shp.Sphere()

    x_axis = np.array(gpXYZ2List(shape.XAxis().Direction()))
    y_axis = np.array(gpXYZ2List(shape.YAxis().Direction()))
    z_axis = np.cross(x_axis, y_axis)

    feature = {
        'location': gpXYZ2List(shape.Location()),
        'x_axis': x_axis.tolist(),
        'y_axis': y_axis.tolist(),
        'z_axis': z_axis.tolist(),
        'coefficients': list(shape.Coefficients()),
        'radius': shape.Radius(),
    }

    return feature

def generateTorusFeature(dim, shp, tag):
    node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)
    elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dim, tag)

    feature = generateBaseSurfaceFeature((node_tags, node_coords, node_params), (elem_types, elem_tags, elem_node_tags), 'Torus')

    shape = shp.Torus()

    feature = {
        'location': gpXYZ2List(shape.Location()),
        'x_axis': gpXYZ2List(shape.XAxis().Direction()),
        'y_axis': gpXYZ2List(shape.YAxis().Direction()),
        'z_axis': gpXYZ2List(shape.Axis().Direction()),
        #'coefficients': list(shape.Coefficients()),
        'max_radius': shape.MajorRadius(),
        'min_radius': shape.MinorRadius(),
    }

    return feature


def generateFeature(dim, shp, tag, type):
    generate_functions_dict = {
        'line': generateLineFeature,
        'circle': generateCircleFeature,
        'ellipse': generateEllipseFeature,
        'plane': generatePlaneFeature,
        'cylinder': generateCylinderFeature,
        'cone': generateConeFeature,
        'sphere': generateSphereFeature,
        'torus': generateTorusFeature,
    }
    if type.lower() in generate_functions_dict.keys():
        return generate_functions_dict[type.lower()](dim, shp, tag)


def processMM(shape, entities, dim_info):
    model_composition = {}
    features = {}

    for dim, info in dim_info.items():
        name, _ = info
        features[name] = []

    print("\nGenerating Features...")
    for d in tqdm(range(0, len(entities))):
        if d in dim_info.keys() and len(shape[d]) == len(entities[d]):
            for i in range(0, len(shape[d])):
                shp = shape[d][i]
                tag = entities[d][i]

                if dim == 0:
                    pass
                elif dim == 1:
                    t1 = str(GeomAbs_CurveType(shp.GetType())).split('_')[-1]
                elif dim == 2:
                    t1 = str(GeomAbs_SurfaceType(shp.GetType())).split('_')[-1]
                elif dim == 3:
                    pass
                else:
                    print('Error:\tdimension >3.')
                    continue

                t2 = gmsh.model.getType(d, tag)
                
                if t1 == t2:
                    tp = t1
                else:
                    print('Error:\t{} != {}.'.format(t1,t2))
                    continue

                if tp in dim_info[d][1]:
                    if tp not in model_composition.keys():
                        model_composition[tp] = 1
                    else:
                        model_composition[tp] += 1 

                    feature = generateFeature(d, shp, tag, tp)
                    features[dim_info[dim][0]].append(feature)
        else:
            if d in dim_info.keys():
                print('Error:\tdimension {} is not the same in model and mesh.'.format(d))
    print('Done.\n')
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
    return result    

def splitEntitiesByDim(entities):
    print('\nSpliting Entities by Dim...')
    new_entities = [[], [], [], []]
    for dim, tag in tqdm(entities):
        new_entities[dim].append(tag)
    print('Done.')
    return new_entities

def splitShapeByDim(shape):
    print('\nSpliting Shape by Dim...')
    new_shape = [[], [], [], []]
    for face in TopologyExplorer(shape).faces():
        surf = BRepAdaptor_Surface(face, True)
        new_shape[2].append(surf)
    print('Done.')
    return new_shape

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

    print('\nLoading with Pythonocc...')
    shape = read_step_file(input_name)
    print('Done.\n')

    print('Loading with Gmsh')
    gmsh.model.occ.importShapes(input_name)
    #gmsh.model.occ.healShapes() ##Tratamento interessante para os shapes
    gmsh.model.occ.synchronize()
    print('Done.')

    print('\nProcessing Model {} ({}D)'.format(gmsh.model.getCurrent(), str(gmsh.model.getDimension())))    
    gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
    gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
    print('Generating Mesh...')
    gmsh.model.mesh.generate(2)
    #gmsh.model.mesh.refine()
    gmsh.model.mesh.optimize('', True)
    print('Done.')

    shape = splitShapeByDim(shape)

    entities = splitEntitiesByDim(gmsh.model.getEntities())

    dim_name_types = {
        1 : ('curves', ['Line', 'Circle', 'Ellipse']),
        2 : ('surfaces', ['Plane', 'Cylinder', 'Cone', 'Sphere', 'Torus'])
    }
    model_composition, features = processMM(shape, entities, dim_name_types)

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
