import gmsh 

import numpy as np

from tools import float2str

from tqdm import tqdm

FIRST_NODE_TAG = 0
FIRST_ELEM_TAG = 0

# Get nodes and sets the first node to 0
def getNodes(dimension: int, tag: int, include_boundary = True):
    node_tags, node_coords, node_params = gmsh.model.mesh.getNodes(dimension, tag, includeBoundary = include_boundary)

    if len(node_tags) == 0 or len(node_coords) == 0 or len(node_params) == 0:
        return node_tags, node_coords, node_params

    if dimension == 1 and len(node_tags) > 2 and node_tags[-2] < node_tags[0]:
        node_tags = np.roll(node_tags, 1)
        temp = node_tags[0]
        node_tags[0] = node_tags[-1]
        node_tags[-1] = temp

        node_coords = np.roll(node_coords, 3)
        for i in range(0, 3):
            temp = node_coords[i]
            node_coords[i] = node_coords[i - 3]
            node_coords[i - 3] = temp
        
        node_params = np.roll(node_params, dimension)
        for i in range(0, dimension):
            temp = node_params[i]
            node_params[i] = node_params[i - dimension]
            node_params[i - dimension] = temp
        
    if dimension > 1:
        node_params = np.resize(node_params, (int(node_params.shape[0]/dimension), dimension))
    
    node_tags -= FIRST_NODE_TAG
    return node_tags, node_coords, node_params

# Get elements and sets the first element to 0
def getElements(dimension: int, tag: int):
    elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(dimension, tag)
    
    if len(elem_tags) == 0 or len(elem_node_tags) == 0:
        return elem_types, elem_tags, elem_node_tags
   
    elem_tags[0] -= FIRST_ELEM_TAG
    elem_node_tags[0] -= FIRST_NODE_TAG
    return elem_types, elem_tags, elem_node_tags

# Generate features of the curves
def generateGMSHCurveFeature(dimension: int, tag: int) -> dict:
    node_tags, node_coords, node_params = getNodes(dimension, tag)
    
    feature = {
        'sharp': True,
        'vert_indices': node_tags,
        'vert_parameters': node_params,
    }

    return feature

# Generate features of the surfaces
def generateGMSHSurfaceFeature(dimension: int, tag: int) -> dict:
    node_tags, node_coords, node_params = getNodes(dimension, tag)
    elem_types, elem_tags, elem_node_tags = getElements(dimension, tag)
    
    feature = {
        'vert_indices': node_tags,
        'vert_parameters': node_params,
        'face_indices': np.array([]) if len(elem_tags) == 0 else elem_tags[0],
    }

    return feature

# Separates entities by dimension
def splitEntitiesByDim(entities):
    new_entities = [[], [], [], []]
    for dimension, tag in tqdm(entities):
        new_entities[dimension].append(tag)
    return new_entities

# Joins the dictionaries generated by PythonOCC and GMSH
def mergeFeaturesOCCandGMSH(features: dict, entities):
    for dimension in range(0, len(entities)):
        if dimension == 1:
            for i in tqdm(range(0, len(features['curves']))):
                tag = entities[dimension][i]
                 
                if features['curves'][i] is not None:
                    feature = generateGMSHCurveFeature(dimension, tag)

                    features['curves'][i].update(feature)
        if dimension == 2:
            for i in tqdm(range(0, len(features['surfaces']))):
                tag = entities[dimension][i]

                if features['surfaces'][i] is not None:
                    feature = generateGMSHSurfaceFeature(dimension, tag)

                    features['surfaces'][i].update(feature)

    for key in features.keys():
        i = 0
        while i < len(features[key]):
            if features[key][i] is None:
                features[key].pop(i)
            else:
                i = i + 1

# Configure the GMSH
def setupGMSH(mesh_size: float):

    gmsh.option.setNumber("Mesh.MeshSizeMin", 0)
    gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
    
    gmsh.option.setNumber("General.ExpertMode", 1)

    # gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    # gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 1)
    # gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)

    # Defines the algorithm to be used 
    # gmsh.option.setNumber("Mesh.Algorithm", 6) # Default 6 - Frontal Delaunay

    # Define the number of threads for mesh generate
    # gmsh.option.setNumber("Mesh.MaxNumThreads2D", 8)

    # gmsh.option.setNumber("Mesh.RefineSteps", 20)
    # gmsh.option.setNumber("Mesh.Smoothing", 20)

# Write a string in OBJ format
def writeOBJ(output_name: str):
    node_tags, node_coords, node_params = getNodes(-1, -1, include_boundary = False)
    elem_types, elem_tags, elem_node_tags = getElements(2, -1)

    obj_content = ''

    node_coords = np.resize(node_coords, (int(node_coords.shape[0]/3), 3))

    for coord in node_coords:
        obj_content += 'v ' + float2str(coord[0]) + ' ' + float2str(coord[1]) + ' ' + float2str(coord[2]) + '\n'

    lut = [-1 for i in range(0, len(node_tags))]
    entities = gmsh.model.occ.getEntities(2)
    i = 0
    for dim, tag in entities:
        n_t, n_c, n_p = getNodes(dim, tag)
        for j in range(0, len(n_t)):
            if lut[n_t[j]] == -1:
                normal = gmsh.model.getNormal(tag, n_p[j])
                obj_content += 'vn ' + float2str(normal[0]) + ' ' + float2str(normal[1]) + ' ' + float2str(normal[2]) + '\n'
                lut[n_t[j]] = i
                i+= 1

    elem_node_tags[0] += 1
    elem_node_tags[0] = np.resize(elem_node_tags[0], (int(elem_node_tags[0].shape[0]/3), 3))
    for node_tags in elem_node_tags[0]:
        n0 = int(node_tags[0])
        n1 = int(node_tags[1])
        n2 = int(node_tags[2])
        obj_content += 'f ' + str(n0) + '//' + str(lut[n0 - 1] + 1) + ' ' + str(n1) + '//' + str(lut[n1 - 1] + 1) + ' ' + str(n2) + '//' + str(lut[n2 - 1] + 1) + '\n'

    f = open(output_name, 'w')
    f.write(obj_content)

# Main function
def processGMSH(input_name: str, mesh_size: float, features: dict, mesh_name: str, shape = None, use_highest_dim=True):
    global FIRST_NODE_TAG, FIRST_ELEM_TAG

    gmsh.initialize()

    if shape is None:
        gmsh.model.occ.importShapes(input_name, highestDimOnly=use_highest_dim)
    else:
        shape_pnt = int(shape.this)
        gmsh.model.occ.importShapesNativePointer(shape_pnt, highestDimOnly=use_highest_dim)

    gmsh.model.occ.synchronize()

    setupGMSH(mesh_size=mesh_size)

    gmsh.model.mesh.generate(2)

    node_tags, _, _ = gmsh.model.mesh.getNodes(-1, -1)
    _, elem_tags, _ = gmsh.model.mesh.getElements(2, -1)
    FIRST_NODE_TAG = node_tags[0]
    FIRST_ELEM_TAG = elem_tags[0][0]

    writeOBJ(mesh_name + '.obj')

    entities = splitEntitiesByDim(gmsh.model.occ.getEntities())

    mergeFeaturesOCCandGMSH(features=features, entities=entities)
        
    gmsh.finalize()