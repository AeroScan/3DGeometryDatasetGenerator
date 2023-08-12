import numpy as np 

from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.IMeshTools import IMeshTools_Parameters
from OCC.Core.GeomAbs import GeomAbs_CurveType
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.BRepTools import breptools_Compare
from OCC.Core.gp import gp_Pnt, gp_Pnt2d
import OCC.Core.ShapeFix as ShapeFix
from OCC.Core.ShapeAnalysis import ShapeAnalysis_Surface
from asGeometryOCCWrapper.surfaces import SurfaceFactory

from tqdm import tqdm

from lib.logger import Logger

logger = Logger()

MAX_INT = 2**31 - 1

# def findPointInListWithHashCode(point, points, hash_codes):
#     hc = STEPConstruct_PointHasher.HashCode(point, MAX_INT)
#     index = -1
#     if hc in hash_codes:
#         index = -2
#         for i in hash_codes[hc]:
#             if STEPConstruct_PointHasher.IsEqual(point, points[i]):
#                 index = i
#                 break
#     return index, hc

def paramsMerge(a, b):
    i = 0
    j = 0
    k = 0
    merge_list = np.zeros(len(a) + len(b), dtype=np.int32) - 1
    a_map = np.zeros(len(a), dtype=np.int32) - 1
    b_map = np.zeros(len(b), dtype=np.int32) - 1

    while i < len(a) and j < len(b):
        if np.isclose(a[i], b[j], rtol=0.): # the 99% case
            merge_list[k] = a[i]
            a_map[i] = k
            b_map[j] = k
            i+=1
            j+=1
        elif a[i] < b[j]:
            merge_list[k] = a[i]
            a_map[i] = k
            i+=1
        else:
            merge_list[k] = b[j] 
            b_map[j] = k
            j+=1
        k+=1

    if i < len(a):
        diff = len(a) - i
        new_k = k + diff
        merge_list[k:new_k] = a[i:]
        a_map[i:] = np.arange(k, new_k)
        k = new_k

    elif j < len(b):
        diff = len(b) - j
        new_k = k + diff
        merge_list[k:new_k] = b[j:]
        b_map[j:] = np.arange(k, new_k)
        k = new_k

    return merge_list[:k], a_map, b_map

def searchEntityInMap(entity, map, use_issame=True):
    hc = entity.HashCode(MAX_INT)
    index = -1
    if hc in map:
        for qindex, qentity in map[hc]:
            if use_issame:
                if entity.IsSame(qentity):
                    index = qindex
                    break
            else:
                if entity.IsEqual(qentity):
                    index = qindex
                    break
    return index

def addEntityToMap(index, entity, map):
    hc = entity.HashCode(MAX_INT)
    if hc in map:
        map[hc].append((index, entity))
    else:
        map[hc] = [(index, entity)]

#TODO:remove unreferenced vertices per surface or curve
def computeMeshData(vertices, edges, faces, topology):
    vertices_mesh_data = []
    vertices_map = {}
    logger.log('[Generate Mesh OCC] Mapping Vertices...', "info")
    for i, vertex in enumerate(tqdm(vertices)):
        vertices_mesh_data.append(-1)
        addEntityToMap(i, vertex, vertices_map)
    vertices_mesh_data = np.asarray(vertices_mesh_data)

    edges_mesh_data = []
    edge_vertices_map = []
    edges_map = {}
    logger.log('[Generate Mesh OCC] Mapping Edges...', "info")
    for i, edge in enumerate(tqdm(edges)):
        edges_mesh_data.append({'vert_indices': [], 'vert_parameters': []})
        addEntityToMap(i, edge, edges_map)
        vertices_indices = [searchEntityInMap(vertex, vertices_map) for vertex in topology.vertices_from_edge(edge)]
        edge_vertices_map.append(vertices_indices)

    faces_mesh_data = []
    face_edges_map = []
    faces_map = {}
    logger.log('[Generate Mesh OCC] Mapping Faces...', "info")
    for i, face in enumerate(tqdm(faces)):
        faces_mesh_data.append({'vert_indices': [], 'vert_parameters': [], 'face_indices': []})
        addEntityToMap(i, face, faces_map)
        edges_indices = [searchEntityInMap(edge, edges_map) for edge in topology.edges_from_face(face)]
        face_edges_map.append(edges_indices)
    mesh_vertices = []
    mesh_faces = []
    logger.log('[Generate Mesh OCC] Generating Mesh Data...', "info")
    for face_index, face in enumerate(tqdm(faces)):

        face_orientation = face.Orientation()

        brep_tool = BRep_Tool()
        location = TopLoc_Location()
        triangulation = brep_tool.Triangulation(face, location, 0)
        transform = location.Transformation()

        if triangulation is None:
            logger.log("[Generate Mesh OCC] The triangulation is None", "warn")
            continue

        number_vertices = triangulation.NbNodes()

        face_vert_global_map = np.zeros(number_vertices, dtype=np.int64) - 1 # map local face mesh id to global mesh id
        face_vert_params = []
        face_vert_local_map = np.arange(number_vertices, dtype=np.int64) # map ids to another local ids (useful in deal with repeated vertices)
        face_vertex_node_map = np.zeros(number_vertices, dtype=np.int64) - 1

        #looking to all edges that bound the current face
        edges_index = face_edges_map[face_index]
        has_degenerated_edge = False
        edges_data = []

        for edge_index in edges_index:            
            edge = edges[edge_index] #TopoDS_Edge object

            vertices_index = edge_vertices_map[edge_index]
            vertices_params = np.array([brep_tool.Parameter(vertices[vertex_index], edge, face) 
                                        for vertex_index in vertices_index])
            vertices_array = np.asarray([brep_tool.Pnt(vertices[vertex_index]).Transformed(transform.Inverted()).Coord() 
                                        for vertex_index in vertices_index])

            polygon = brep_tool.PolygonOnTriangulation(edge, triangulation, location) # projecting edge in the face triangulation
            if polygon is None:
                logger.log("[Generate Mesh OCC] The polygon is None", "warn")
                continue

            edge_vert_local = np.asarray(polygon.Nodes(), dtype=np.int64) - 1 # map from mesh edge indices to face mesh indices
            edge_param_local = np.asarray(polygon.Parameters())

            edge_vert_local_unique = np.unique(edge_vert_local)
            if (len(edge_vert_local) -  len(edge_vert_local_unique)) > 1:
                has_degenerated_edge = True
                logger.log(f'[Generate Mesh OCC] degenerated edge ({edge_index}), canceling face ({face_index})', "warn")
                break

            elif (len(edge_vert_local) - len(edge_vert_local_unique)) == 1 and  \
                 (len(edge_vert_local) == 2 or edge_vert_local[0] != edge_vert_local[-1] or len(vertices_index) == 2):
                has_degenerated_edge = True
                logger.log(f'[Generate Mesh OCC] degenerated edge ({edge_index}), canceling face ({face_index})', "warn")
                break

            if len(edges_mesh_data[edge_index]['vert_indices']) == 0:
                edge_vert_global_map = np.zeros(len(edge_vert_local), dtype=np.int64) - 1
                edge_param_global = np.zeros(len(edge_vert_local), dtype=np.float64) - 1
            else:
                edge_vert_global_map = edges_mesh_data[edge_index]['vert_indices'].copy()
                edge_param_global = edges_mesh_data[edge_index]['vert_parameters'].copy()

            edge_vert_local_unique = np.unique(edge_vert_local)
            '''
                Assuming 'nodes' as mesh vertices and 'vertices' as curves vertices:
                - a curve is "closed" if it has just one vertex
                - a closed curve must have the same node as first and last node (problem 1)
                - an openned curve must not have the same node as first and last node (problem 2)
            '''
            indices = [0, -1]
            if len(vertices_index) == 2:
                indices = [[0, -1], [-1, 0]]

            is_foward = np.allclose(vertices_params, edge_param_local[indices[0]], rtol=0.)
            is_reversed = np.allclose(vertices_params, edge_param_local[indices[1]], rtol=0.)

            if is_foward and is_reversed:
                nodes_array = np.asarray([triangulation.Node(int(evl - 1)).Transformed(transform.Inverted()).Coord()
                                            for evl in edge_vert_local[[0, -1]]])
                
                is_foward = np.allclose(vertices_array, nodes_array[indices[0]], rtol=0.)
                is_reversed = np.allclose(vertices_array, nodes_array[indices[1]], rtol=0.)

                if is_foward and is_reversed:
                    logger.log('[Generate Mesh OCC] is_foward and is_reversed', "error")
                    continue
            
            bound_indices = [-1, 0] if is_reversed else [0, -1]

            vertex_nodes = edge_vert_local[bound_indices[:len(vertices_index)]]
            current_vertex = face_vertex_node_map[vertex_nodes]
            diff_mask = current_vertex != vertices_index
            if np.any(np.logical_and(diff_mask, current_vertex != -1)):
                has_degenerated_edge = True
                logger.log(f'[Generate Mesh OCC] degenerated edge ({edge_index}), canceling face ({face_index})', "warn")
                break
            else:
                face_vertex_node_map[vertex_nodes] = vertices_index

            ed = {
                'e': edge,
                'ei': edge_index,
                'vi': vertices_index,
                'vp': vertices_params,
                'va': vertices_array,
                'evl': edge_vert_local,
                'epl': edge_param_local,
                'evgm': edge_vert_global_map,
                'epg': edge_param_global,
                'bi': bound_indices,
            }

            edges_data.append(ed)

        if has_degenerated_edge:
            continue

        for ed in edges_data:
            edge = ed['e']
            edge_index = ed['ei']
            vertices_index = ed['vi']
            vertices_params = ed['vp']
            vertices_array = ed['va']
            edge_vert_local = ed['evl']
            edge_param_local = ed['epl']
            edge_vert_global_map = ed['evgm']
            edge_param_global = ed['epg']
            bound_indices = ed['bi']


            if len(vertices_index) == 1 and edge_vert_local[0] != edge_vert_local[-1]:
                #triangulation is not closed but the egde is
                #changing triangulation to be closed too

                first_vertex, last_vertex = edge_vert_local[bound_indices]

                edge_vert_local[bound_indices[1]] = first_vertex

                assert face_vert_local_map[last_vertex] == last_vertex or face_vert_local_map[last_vertex] == face_vert_local_map[first_vertex], \
                        f'{vertices_array} \n {np.asarray([triangulation.Node(int(i + 1)).Coord() for i in edge_vert_local[[0,-1]]])}'

                #face_vert_local_map[last_vertex] = face_vert_local_map[first_vertex]
                face_vert_local_map[face_vert_local_map == last_vertex] = face_vert_local_map[first_vertex]

            # if there is already global parameters for the edge
            local_edge_map = np.arange(len(edge_vert_local))

            if len(edge_param_local) != len(edge_param_global):
                # need to merge two edge params
                merge_params, local_edge_map, global_edge_map = paramsMerge(edge_param_local, edge_param_global)
    
                edges_mesh_data[edge_index]['vert_indices'] = np.zeros(len(merge_params), dtype=np.int64) - 1
                edges_mesh_data[edge_index]['vert_indices'][global_edge_map] = edge_vert_global_map

                edges_mesh_data[edge_index]['vert_parameters'] = np.zeros(len(merge_params), dtype=np.float64) - 1
                edges_mesh_data[edge_index]['vert_parameters'][global_edge_map] = edge_param_global

                edge_vert_global_map = edges_mesh_data[edge_index]['vert_indices'][local_edge_map]
                edge_param_global = edges_mesh_data[edge_index]['vert_parameters'][local_edge_map]

            assert len(edge_vert_local) == len(edge_vert_global_map), f'{edge_index} {edge_param_local} {edge_param_global}'

            vertices_local_index_map = np.zeros(len(vertices_index), dtype=np.int64) - 1
            for id, vertex_index in enumerate(vertices_index):

                vertex_local_edge_index = bound_indices[id]
                vertex_local_index = edge_vert_local[vertex_local_edge_index]
                vertex_global_index = vertices_mesh_data[vertex_index]

                if vertex_global_index == -1:
                    assert edge_vert_global_map[vertex_local_edge_index] == -1, \
                        'vertex has no global index but edge already has.' \
                        f' Edge global vertices: {edge_vert_global_map}'
                    
                else:
                    if edge_vert_global_map[vertex_local_edge_index] != -1:
                        assert edge_vert_global_map[vertex_local_edge_index] == vertex_global_index and \
                                np.allclose(edge_param_global[vertex_local_edge_index], vertices_params[id]), \
                                'different global indices between vertex and edge.\n' \
                                f'{edge_vert_global_map[vertex_local_edge_index]} != {vertex_global_index}\n' \
                                f'{edge_param_global[vertex_local_edge_index]} != {vertices_params[id]}\n' \
                                f'{edge_vert_local} {edge_vert_global_map} {face_vert_global_map[edge_vert_local]} {vertices_index} {vertices_mesh_data[vertices_index]}'
                    
                    edge_vert_global_map[vertex_local_edge_index] = vertex_global_index
                    edge_param_global[vertex_local_edge_index] = vertices_params[id]

                vertices_local_index_map[id] = vertex_local_index 

            edge_mask = edge_vert_global_map != -1 # already mapped edge vertex mask

            #Edge already has global params, need to verify consistecy and pass the node ids to face
            if np.any(edge_mask):

                #Verify if params are the same, may me reverse oriented (or not)
                assert np.allclose(edge_param_local[edge_mask], edge_param_global[edge_mask], rtol=0.), \
                       f'Edge {edge_index} has different vertex parameters. \n' \
                       f'{edge_param_local[edge_mask]} != {edge_param_global[edge_mask]}'

                face_mask = face_vert_global_map[edge_vert_local[edge_mask]] != -1 # already mapped face vertex mask
                
                #assert face_vert_global_map[edge_vert_local[edge_mask]][face_mask]

                #('aaaaaaaaaa:', edge_vert_global_map[edge_mask][face_mask])
                assert np.all(~face_mask) or np.all(face_vert_global_map[edge_vert_local[edge_mask]][face_mask] \
                                                    == edge_vert_global_map[edge_mask][face_mask]), \
                       f'Failed in match global indices from different edges. ' \
                       f'{face_vert_global_map[edge_vert_local[edge_mask]][face_mask]} != ' \
                       f'{edge_vert_global_map[edge_mask][face_mask]} \n' \
                       f'{face_index} {edge_index} {edge_vert_local}'
                                
                face_vert_global_map[edge_vert_local[edge_mask]] = edge_vert_global_map[edge_mask]

            # to deal with edges that have not been global mapped before
            for i in (edge_vert_local + 1):
                if face_vert_global_map[i - 1] == -1 and face_vert_local_map[i - 1] == (i - 1):
                    pnt = triangulation.Node(int(i))
                    pnt.Transform(transform)
                    pnt_array = np.array(pnt.Coord())
                    mesh_vertices.append(pnt_array)
                    face_vert_global_map[i - 1] = len(mesh_vertices) - 1
            
            mask_minus_one = face_vert_global_map == -1

            assert np.all(np.logical_or(mask_minus_one, face_vert_global_map == face_vert_global_map[face_vert_local_map]))

            face_vert_global_map = face_vert_global_map[face_vert_local_map]

            vertices_mesh_data[np.asarray(vertices_index)] = face_vert_global_map[np.array(vertices_local_index_map)]    

            if len(edges_mesh_data[edge_index]['vert_indices']) > 0:
                edges_mesh_data[edge_index]['vert_indices'][local_edge_map] = face_vert_global_map[edge_vert_local]
                edges_mesh_data[edge_index]['vert_parameters'][local_edge_map] = edge_param_local
            else:
                edges_mesh_data[edge_index]['vert_indices'] = face_vert_global_map[edge_vert_local]
                edges_mesh_data[edge_index]['vert_parameters'] = edge_param_local

        for i in range(1, number_vertices + 1):
            if face_vert_local_map[i - 1] == (i - 1):
                if face_vert_global_map[i - 1] == -1:
                    pnt = triangulation.Node(i)
                    pnt.Transform(transform)
                    pnt_array = np.array(pnt.Coord())
                    mesh_vertices.append(pnt_array)
                    face_vert_global_map[i - 1] = len(mesh_vertices) - 1

                uv_node = triangulation.UVNode(i)
                face_vert_params.append(list(uv_node.Coord()))

        face_indices = []
        number_faces = triangulation.NbTriangles()
        for i in range(1, number_faces + 1):
            i1, i2, i3 = triangulation.Triangle(i).Get()
            i1_m = face_vert_global_map[i1 - 1]
            i2_m = face_vert_global_map[i2 - 1]
            i3_m = face_vert_global_map[i3 - 1]

            if i1_m == i2_m or i1_m == i3_m or i2_m == i3_m:
                if i1 == i2 or i1 == i3 or i2 == i3:
                    #not a reamapping problem
                    pass
                else:
                    #remapping warning: lets see if vertex coordinates have changed
                    if not (np.allclose(mesh_vertices[i1_m], np.array(triangulation.Node(i1).Transformed(transform).Coord()), rtol=0.) and \
                           np.allclose(mesh_vertices[i2_m], np.array(triangulation.Node(i2).Transformed(transform).Coord()), rtol=0.) and \
                           np.allclose(mesh_vertices[i3_m], np.array(triangulation.Node(i3).Transformed(transform).Coord()), rtol=0.)):
                        logger.log(f'[Generate Mesh OCC] Vertices remapping problem.\n' \
                              f'{mesh_vertices[i1_m]} != {np.array(triangulation.Node(i1).Transformed(transform).Coord())} or \n' \
                              f'{mesh_vertices[i2_m]} != {np.array(triangulation.Node(i2).Transformed(transform).Coord())} or \n' \
                              f'{mesh_vertices[i3_m]} != {np.array(triangulation.Node(i3).Transformed(transform).Coord())}', "error")
                
            if face_orientation == 0:
                verts_of_face = np.array([i1_m, i2_m, i3_m])
                mesh_faces.append(verts_of_face)
                face_indices.append(len(mesh_faces) - 1)
            elif face_orientation == 1:
                verts_of_face = np.array([i3_m, i2_m, i1_m])
                mesh_faces.append(verts_of_face)
                face_indices.append(len(mesh_faces) - 1)
            else:
                assert False, 'Face Orientation not Supported yet.'        
      
        faces_mesh_data[face_index] = {'vert_indices': face_vert_global_map.tolist(), 
                                       'vert_parameters': face_vert_params, 'face_indices': face_indices}

    #unique_vert = np.arange(len(mesh_vertices))
    #unique_vert_faces = np.unique(np.asarray(mesh_faces))
    #assert np.all(unique_vert_faces == unique_vert), \
    #           f'ERROR: unreferenced vertices in global mesh'

    for edge_index in range(len(edges_mesh_data)):
        if type(edges_mesh_data[edge_index]['vert_indices']) is not list:
            edges_mesh_data[edge_index]['vert_indices'] = edges_mesh_data[edge_index]['vert_indices'].tolist()
        if type(edges_mesh_data[edge_index]['vert_parameters']) is not list:
            edges_mesh_data[edge_index]['vert_parameters'] = edges_mesh_data[edge_index]['vert_parameters'].tolist()
                                    
    return mesh_vertices, mesh_faces, edges_mesh_data, faces_mesh_data

def OCCMeshGeneration(shape):
    logger.log('[Generate Mesh OCC] Mesh Generation...', "info")
    parameters = IMeshTools_Parameters()

    #Ref: https://dev.opencascade.org/doc/refman/html/struct_i_mesh_tools___parameters.html#a3027dc569da3d3e3fcd76e0615befb27
    parameters.MeshAlgo = -1
    parameters.Angle = 0.1
    parameters.Deflection = 0.01
    parameters.MinSize = 0.01
    parameters.Relative = True
    parameters.InParallel = True

    brep_mesh = BRepMesh_IncrementalMesh(shape, parameters)
    brep_mesh.Perform()
    assert brep_mesh.IsDone()