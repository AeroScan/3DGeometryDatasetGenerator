import gmsh

import argparse

import pprint

from tqdm import tqdm

import numpy as np

import psutil
import gc
import time

from OCC.Core.GeomAbs import (GeomAbs_CurveType, GeomAbs_SurfaceType)
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
from OCC.Core.TopoDS import TopoDS_Face
from OCC.Extend.DataExchange import read_step_file
from OCC.Extend.TopologyUtils import TopologyExplorer

POSSIBLE_CURVE_TYPES = ['line', 'circle', 'ellipse']
POSSIBLE_SURFACE_TYPES = ['plane', 'cylinder', 'cone', 'sphere', 'torus']

def generateBaseCurveFeature(node, tp):
    node_tags, node_coords, node_params = node
    feature = {
        'sharp': True,
        'vert_indices': node_tags,
        'vert_parameters': node_params,
    }
    return feature

def generateBaseSurfaceFeature(node, elem, type):
    node_tags, node_coords, node_params = node
    elem_types, elem_tags, elem_node_tags = elem
    node_params = np.resize(node_params, (int(node_params.shape[0]/2), 2))
    feature = {
        'vert_indices': node_tags,
        'vert_parameters': node_params,
        'face_indices': elem_tags[0],
    }
    return feature

def gpXYZ2List(gp):
    return [gp.X(), gp.Y(), gp.Z()]

def generateLineFeature(dim, shp, tag):

    if shp == "" and tag != -1: # Loaded by GMSH
        node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)

        f = generateBaseCurveFeature((node_tags, node_coords, node_params), 'Line')

    else: # Loaded by PythonOCC
        shape = shp.Line()

        f = {
            'type': 'Line',
            'location': gpXYZ2List(shape.Location()),
            'direction': gpXYZ2List(shape.Direction()),
        }

    feature = {**f}

    return feature

def generateCircleFeature(dim, shp, tag):

    if shp == "" and tag != -1:
        node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)

        f = generateBaseCurveFeature((node_tags, node_coords, node_params), 'Circle')

    else:

        shape = shp.Circle()

        f = {
            'type': 'Circle',
            'location': gpXYZ2List(shape.Location()),
            'z_axis': gpXYZ2List(shape.Axis().Direction()),
            'radius': shape.Radius(),
            'x_axis': gpXYZ2List(shape.XAxis().Direction()),
            'y_axis': gpXYZ2List(shape.YAxis().Direction()),
        }

    feature = {**f}

    return feature

def generateEllipseFeature(dim, shp, tag):

    if shp == "" and tag != -1:
        node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)

        f = generateBaseCurveFeature((node_tags, node_coords, node_params), 'Ellipse')
    
    else:
        shape = shp.Ellipse()

        f = {
            'type': 'Ellipse',
            'focus1': gpXYZ2List(shape.Focus1()),
            'focus2': gpXYZ2List(shape.Focus2()),
            'x_axis': gpXYZ2List(shape.XAxis().Direction()),
            'y_axis': gpXYZ2List(shape.YAxis().Direction()),
            'z_axis': gpXYZ2List(shape.Axis().Direction()),
            'x_radius': shape.MajorRadius(),
            'y_radius': shape.MinorRadius(),
        }

    feature = {**f}

    return feature

def generatePlaneFeature(dim, shp, tag):

    if shp == "" and tag != -1:
        node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)
        elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dim, tag)

        f = generateBaseSurfaceFeature((node_tags, node_coords, node_params), (elem_types, elem_tags, elem_node_tags), 'Plane')

    else:
        shape = shp.Plane()

        f = {
            'type': 'Plane',
            'location': gpXYZ2List(shape.Location()),
            'normal': gpXYZ2List(shape.Axis().Direction()),
            'x_axis': gpXYZ2List(shape.XAxis().Direction()),
            'y_axis': gpXYZ2List(shape.YAxis().Direction()),
            'z_axis': gpXYZ2List(shape.Axis().Direction()),
            'coefficients': list(shape.Coefficients()),
        }

    feature = {**f}

    return feature

def generateCylinderFeature(dim, shp, tag):

    if shp == "" and tag != -1:
        node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)
        elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dim, tag)

        f = generateBaseSurfaceFeature((node_tags, node_coords, node_params), (elem_types, elem_tags, elem_node_tags), 'Cylinder')

    else:
        shape = shp.Cylinder()

        f = {
            'type': 'Cylinder',
            'location': gpXYZ2List(shape.Location()),
            'x_axis': gpXYZ2List(shape.XAxis().Direction()),
            'y_axis': gpXYZ2List(shape.YAxis().Direction()),
            'z_axis': gpXYZ2List(shape.Axis().Direction()),
            'coefficients': list(shape.Coefficients()),
            'radius': shape.Radius(),
        }

    feature = {**f}

    return feature

def generateConeFeature(dim, shp, tag):

    if shp == "" and tag != -1:
        node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)
        elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dim, tag)

        f = generateBaseSurfaceFeature((node_tags, node_coords, node_params), (elem_types, elem_tags, elem_node_tags), 'Cone')

    else:
        shape = shp.Cone()

        f = {
            'type': 'Cone',
            'location': gpXYZ2List(shape.Location()),
            'x_axis': gpXYZ2List(shape.XAxis().Direction()),
            'y_axis': gpXYZ2List(shape.YAxis().Direction()),
            'z_axis': gpXYZ2List(shape.Axis().Direction()),
            'coefficients': list(shape.Coefficients()),
            'radius': shape.RefRadius(),
            'angle': shape.SemiAngle(),
            'apex': gpXYZ2List(shape.Apex()),
        }

    feature = {**f}

    return feature

def generateSphereFeature(dim, shp, tag):

    if shp == "" and tag != -1:
        node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)
        elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dim, tag)

        f = generateBaseSurfaceFeature((node_tags, node_coords, node_params), (elem_types, elem_tags, elem_node_tags), 'Sphere')

    else:
        shape = shp.Sphere()

        x_axis = np.array(gpXYZ2List(shape.XAxis().Direction()))
        y_axis = np.array(gpXYZ2List(shape.YAxis().Direction()))
        z_axis = np.cross(x_axis, y_axis)

        f = {
            'type': 'Sphere',
            'location': gpXYZ2List(shape.Location()),
            'x_axis': x_axis.tolist(),
            'y_axis': y_axis.tolist(),
            'z_axis': z_axis.tolist(),
            'coefficients': list(shape.Coefficients()),
            'radius': shape.Radius(),
        }

    feature = {**f}

    return feature

def generateTorusFeature(dim, shp, tag):

    if shp == "" and tag != -1:
        node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dim, tag)
        elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dim, tag)

        f = generateBaseSurfaceFeature((node_tags, node_coords, node_params), (elem_types, elem_tags, elem_node_tags), 'Torus')

    else:
        shape = shp.Torus()

        f = {
            'type': 'Torus',
            'location': gpXYZ2List(shape.Location()),
            'x_axis': gpXYZ2List(shape.XAxis().Direction()),
            'y_axis': gpXYZ2List(shape.YAxis().Direction()),
            'z_axis': gpXYZ2List(shape.Axis().Direction()),
            #'coefficients': list(shape.Coefficients()),
            'max_radius': shape.MajorRadius(),
            'min_radius': shape.MinorRadius(),
        }

    feature = {**f}

    return feature

def generateFeature(dim, tag, type, shp=""):
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

# def processMM(shape, entities, dim_info):
#     features = {}

#     for dim, info in dim_info.items():
#         name, _ = info
#         features[name] = []

#     print("\nGenerating Features...")
#     for d in tqdm(range(0, len(entities))):
#         if d in dim_info.keys() and len(shape[d]) == len(entities[d]):
#             for i in range(0, len(shape[d])):
#                 shp = shape[d][i]
#                 tag = entities[d][i]

#                 if d == 0:
#                     pass
#                 elif d == 1:
#                     t1 = str(GeomAbs_CurveType(shp.GetType())).split('_')[-1]
#                 elif d == 2:
#                     t1 = str(GeomAbs_SurfaceType(shp.GetType())).split('_')[-1]
#                 elif d == 3:
#                     pass
#                 else:
#                     print('Error:\tdimension> 3.')
#                     continue
                
#                 tp = t1

#                 if tp in dim_info[d][1]:
#                     feature = generateFeature(d, shp, tag, tp)
#                     features[dim_info[d][0]].append(feature)
#         else:
#             if d in dim_info.keys():
#                 print('Error:\tdimension {} is not the same in model and mesh.'.format(d))
#     print('Done.\n')
#     return features

def float2str(n, limit = 10):
    if abs(n) >= 10**limit:
        return ('%.' + str(limit) + 'e') % n
    elif abs(n) <= 1/(10**limit) and n != 0:
        return ('%.' + str(limit) + 'e') % n
    elif n == -0.0:
        return str(0.0)
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
    for key, value in d.items(): # key = curves / surfaces - value = todas primitivas
        if len(value) == 0:
            result += key + ': []\n'
            continue
        result += key + ':\n'
        for d2 in value: # d2 é um dicionario por loop
            result += '- '
            for key2, value2 in d2.items():
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
            del d2
            gc.collect()
    return result  

def splitEntitiesByDim(entities):
    print('\nSpliting Entities by Dim...')
    new_entities = [[], [], [], []]
    for dim, tag in tqdm(entities):
        new_entities[dim].append(tag)
    print('Done.')
    return new_entities

# def splitShapeByDim(shape):
#     print('\nSpliting Shape by Dim...')
#     new_shape = [[], [], [], []]
#     te = TopologyExplorer(shape)
#     #dimension 1
#     for edge in tqdm(te.edges()):
#         curv = BRepAdaptor_Curve(edge) # guardar dict com parametros
#         new_shape[1].append(curv)
#     #dimension 2
#     for face in tqdm(te.faces()):
#         surf = BRepAdaptor_Surface(face, True)
#         new_shape[2].append(surf)
#     print('Done.')
#     return new_shape

def processShape2Feature(shp, tp, dim):
    return generateFeature(dim, -1, tp, shp)    # tag=-1 to process PythonOCC only

def generateFeatureByDim(shape, features):
    print('\nGenerating Features by Dim...')

    features['curves'] = []
    features['surfaces'] = []
    te = TopologyExplorer(shape)
    #dimension 1
    for edge in tqdm(te.edges()):
        curv = BRepAdaptor_Curve(edge)
        tp = str(GeomAbs_CurveType(curv.GetType())).split('_')[-1].lower()
        if tp in POSSIBLE_CURVE_TYPES:
            feature = processShape2Feature(curv, tp, 1)
            features['curves'].append(feature)
    #dimension 2
    for face in tqdm(te.faces()):
        surf = BRepAdaptor_Surface(face, True)
        tp = str(GeomAbs_SurfaceType(surf.GetType())).split('_')[-1].lower()
        if tp in POSSIBLE_SURFACE_TYPES:
            feature = processShape2Feature(surf, tp, 2)
            features['surfaces'].append(feature)
    print('Done.')    

def mergeFeaturesOCCandGMSH(features, entities):
    print('\nMerging features PythonOCC and GMSH...')
    for dim in range(0, len(entities)):
        if dim == 1:
            if len(features['curves']) != len(entities[dim]):
                print('\nThere are a number of different curves.\n')
            for i in range(0, len(features['curves'])):
                tag = entities[dim][i]
                tp = gmsh.model.getType(dim, tag).lower()

                if tp in POSSIBLE_CURVE_TYPES:
                    feature = generateFeature(dim, tag, tp)

                    features['curves'][i].update(feature)

        elif dim == 2:
            if len(features['surfaces']) != len(entities[dim]):
                print('\nThere are a number of different surfaces.\n')                         
            for i in tqdm(range(0, len(features['surfaces']))):
                tag = entities[dim][i]
                tp = gmsh.model.getType(dim, tag).lower()

                if tp in POSSIBLE_SURFACE_TYPES:
                    feature = generateFeature(dim, tag, tp)

                    features['surfaces'][i].update(feature)
    print('Done.\n')

def processGMSH(input_name, mesh_size):
    gmsh.initialize()

    print('\nLoading with Gmsh')
    gmsh.model.occ.importShapes(input_name)
    # gmsh.model.occ.healShapes() ##Tratamento interessante para os shapes
    gmsh.model.occ.synchronize()
    print('Done.\n')

    print('\nProcessing Model {} ({}D)'.format(gmsh.model.getCurrent(), str(gmsh.model.getDimension())))    
    gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
    gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
    print('\nGenerating Mesh...')
    gmsh.model.mesh.generate(2)
    print('Generating Finish\n')
    gmsh.model.mesh.refine()
    print('Refine Finish\n')
    gmsh.model.mesh.optimize('', True)
    print('Done.\n')

def main():
    initial_time = time.time() / 60.0

    parser = argparse.ArgumentParser(description='3D Geometry Dataset Generator.')
    parser.add_argument('input', type=str, help='input file in CAD formats.')
    parser.add_argument('output', type=str, help='output file name for mesh and features.')
    parser.add_argument("-v", "--visualize", action="store_true", help='visualize mesh')
    # parser.add_argument("-l", "--log", action="store_true", help='show log of results')
    parser.add_argument('--mesh_size', type = float, default = 5, help='mesh size.')
    args = vars(parser.parse_args())

    input_name = args['input']
    output_name = args['output']
    visualize = args['visualize']
    mesh_size = args['mesh_size']
    # log = args['log']

    # Begin PythonOCC process
    print('\nLoading with Pythonocc...')
    shape = read_step_file(input_name)
    print('Done.\n')

    features = {}
    generateFeatureByDim(shape, features) # feature without gmsh

    del shape
    gc.collect()

    processGMSH(input_name, mesh_size)
    
    print('\nWriting stl..')
    gmsh.write(output_name + '.stl')
    print('Done.\n')

    # # Begin Gmsh Process
    # gmsh.initialize()

    # print('\nLoading with Gmsh')
    # gmsh.model.occ.importShapes(input_name)
    # # gmsh.model.occ.healShapes() ##Tratamento interessante para os shapes
    # gmsh.model.occ.synchronize()
    # print('Done.\n')

    # print('\nProcessing Model {} ({}D)'.format(gmsh.model.getCurrent(), str(gmsh.model.getDimension())))    
    # gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size)
    # gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
    # print('\nGenerating Mesh...')
    # gmsh.model.mesh.generate(2)
    # print('Generating Finish\n')
    # gmsh.model.mesh.refine()
    # print('Refine Finish\n')
    # gmsh.model.mesh.optimize('', True)
    # print('Done.\n')

    # print('\nWriting stl..')
    # gmsh.write(output_name + '.stl')
    # print('Done.\n')

    entities = splitEntitiesByDim(gmsh.model.getEntities())

    mergeFeaturesOCCandGMSH(features, entities)

    if visualize:
        gmsh.model.setVisibility(gmsh.model.getEntities(3), 0)
        gmsh.model.setColor(gmsh.model.getEntities(2), 249, 166, 2)
        gmsh.fltk.run()

    gmsh.finalize()

    del entities
    gc.collect()

    # dim_name_types = {
    #     1 : ('curves', ['Line', 'Circle', 'Ellipse']),
    #     2 : ('surfaces', ['Plane', 'Cylinder', 'Cone', 'Sphere', 'Torus'])
    # }
    # features = processMM(new_shape, entities, dim_name_types)

    # if log:
    #     pp = pprint.PrettyPrinter(indent=2)
    #     print('\n---------- LOG ----------')
    #     print('Dimensions considered and its information:')
    #     pp.pprint(dim_name_types)
    #     print('\nModel Composition:')
    #     pp.pprint(model_composition)

    #     print('\nFeatures:')
    #     print('- Curves:')
    #     for f in features['curves']:
    #         pp.pprint(f)

    #     print('\n- Surfaces:')
    #     for f in features['surfaces']:
    #         pp.pprint(f)
    #     print('---------- END LOG ----------')
 
    # pp = pprint.PrettyPrinter(indent=2)
    # pp.pprint(features)
    print('\nWriting yaml...')
    with open(output_name + '.yaml', 'w') as f:
        features_yaml = generateFeaturesYAML(features)
        f.write(features_yaml)
    print('Done.\n')

    del features, features_yaml
    gc.collect()

    final_time = time.time() / 60.0
    delta = (final_time - initial_time)
    print('Total time: ' + str(delta) + ' minutos\n')

if __name__ == '__main__':
    main()
