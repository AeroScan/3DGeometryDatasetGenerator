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

from tqdm import tqdm

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
    print('\n[PythonOCC] Mapping Vertices...')
    for i, vertex in enumerate(tqdm(vertices)):
        vertices_mesh_data.append(-1)
        addEntityToMap(i, vertex, vertices_map)
    vertices_mesh_data = np.asarray(vertices_mesh_data)

    edges_mesh_data = []
    edge_vertices_map = []
    edges_map = {}
    print('\n[PythonOCC] Mapping Edges...')
    for i, edge in enumerate(tqdm(edges)):
        edges_mesh_data.append({'vert_indices': [], 'vert_parameters': []})
        addEntityToMap(i, edge, edges_map)
        vertices_indices = [searchEntityInMap(vertex, vertices_map) for vertex in topology.vertices_from_edge(edge)]
        edge_vertices_map.append(vertices_indices)

    faces_mesh_data = []
    face_edges_map = []
    faces_map = {}
    print('\n[PythonOCC] Mapping Faces...')
    for i, face in enumerate(tqdm(faces)):
        faces_mesh_data.append({'vert_indices': [], 'vert_parameters': [], 'face_indices': []})
        addEntityToMap(i, face, faces_map)
        edges_indices = [searchEntityInMap(edge, edges_map) for edge in topology.edges_from_face(face)]
        face_edges_map.append(edges_indices)
    mesh_vertices = []
    mesh_faces = []
    print('\n[PythonOCC] Generating Mesh Data...')
    for face_index, face in enumerate(tqdm(faces                                                                                           )):
        #print('----------------------------------------------------')
        #print("FACE_INDEX: ", face_index)

        face_orientation = face.Orientation()

        brep_tool = BRep_Tool()
        location = TopLoc_Location()
        triangulation = brep_tool.Triangulation(face, location, 0)
        transform = location.Transformation()

        if triangulation is None:
            #WARNING
            continue

        number_vertices = triangulation.NbNodes()

        face_vert_global_map = np.zeros(number_vertices, dtype=np.int64) - 1 # map local face mesh id to global mesh id
        face_vert_params = []
        face_vert_local_map = np.arange(number_vertices, dtype=np.int64) # map ids to another local ids (useful in deal with repeated vertices)

        #looking to all edges that bound the current face
        edges_index = face_edges_map[face_index]
        has_degenerated_edge = False
        polygons = []
        #if 385157 not in edges_index:
        #    continue

        for edge_index in edges_index:            
            edge = edges[edge_index] #TopoDS_Edge object

            vertices_index = edge_vertices_map[edge_index]

            polygon = brep_tool.PolygonOnTriangulation(edge, triangulation, location) # projecting edge in the face triangulation
            if polygon is None:
                #WARNING
                continue

            edge_vert_local = np.asarray(polygon.Nodes(), dtype=np.int64) - 1 # map from mesh edge indices to face mesh indices
            edge_param_local = np.asarray(polygon.Parameters())

            edge_vert_local_unique = np.unique(edge_vert_local)
            if (len(edge_vert_local) -  len(edge_vert_local_unique)) > 1:
                has_degenerated_edge = True
            elif (len(edge_vert_local) - len(edge_vert_local_unique)) == 1 and  \
                 (len(edge_vert_local) == 2 or edge_vert_local[0] != edge_vert_local[-1] or len(vertices_index) == 2):
                has_degenerated_edge = True
            
            if has_degenerated_edge:
                print(f'WARNING: degenerated edge ({edge_index}), canceling face ({face_index})')
                break
            
            polygons.append((edge_index, polygon))

        if has_degenerated_edge:
            continue


        for edge_index, polygon in polygons:
            edge = edges[edge_index] #TopoDS_Edge object

            edge_vert_local = np.asarray(polygon.Nodes(), dtype=np.int64) - 1 # map from mesh edge indices to face mesh indices
            edge_param_local = np.asarray(polygon.Parameters())
            
            is_none = False
            if len(edges_mesh_data[edge_index]['vert_indices']) == 0:
                is_none = True
                edge_vert_global_map = np.zeros(len(edge_vert_local), dtype=np.int64) - 1
                edge_param_global = np.zeros(len(edge_vert_local), dtype=np.float64) - 1
            else:
                edge_vert_global_map = edges_mesh_data[edge_index]['vert_indices'].copy()
                edge_param_global = edges_mesh_data[edge_index]['vert_parameters'].copy()
                
            # if there is already global parameters for the edge
            local_edge_map = np.arange(len(edge_vert_local))
            if not is_none:
                if len(edge_param_local) != len(edge_param_global):
                    # need to merge two edge params
                    merge_params, local_edge_map, global_edge_map = paramsMerge(edge_param_local, edge_param_global)
        
                    edges_mesh_data[edge_index]['vert_indices'] = np.zeros(len(merge_params), dtype=np.int64) - 1
                    edges_mesh_data[edge_index]['vert_indices'][global_edge_map] = edge_vert_global_map

                    edges_mesh_data[edge_index]['vert_parameters'] = np.zeros(len(merge_params), dtype=np.float64) - 1
                    edges_mesh_data[edge_index]['vert_parameters'][global_edge_map] = edge_param_global

                    edge_vert_global_map = edges_mesh_data[edge_index]['vert_indices'][local_edge_map]
                    edge_param_global = edges_mesh_data[edge_index]['vert_parameters'][local_edge_map]

                assert np.all(edge_param_local == edge_param_global), f'{edge_index}: {edge_param_local} != {edge_param_global}'

            assert len(edge_vert_local) == len(edge_vert_global_map), f'{edge_index} {edge_param_local} {edge_param_global}'

            vertices_index = edge_vertices_map[edge_index]
            vertices_params = np.array([brep_tool.Parameter(vertices[vertex_index], edge, face) 
                                        for vertex_index in vertices_index])
            vertices_array = np.asarray([brep_tool.Pnt(vertices[vertex_index]).Transformed(transform.Inverted()).Coord() 
                                        for vertex_index in vertices_index])

            edge_vert_local_unique, edge_vert_local_counts = np.unique(edge_vert_local, return_counts=True)
            mask_major_2 = edge_vert_local_counts >= 2
            len_diff = np.count_nonzero(mask_major_2)


            assert len_diff <= 1, \
                   f'More than one repreated vertex in Polygon On Triangulation. {str(BRepAdaptor_Curve(edge).GetType())} {edge_vert_local}'

            #some edges have more than two vertices with the same id because of the siz of the edges, we are not working with it
            '''
                Assuming 'nodes' as mesh vertices and 'vertices' as curves vertices:
                - a curve is "closed" if it has just one vertex
                - a closed curve must have the same node as first and last node (problem 1)
                - an openned curve must not have the same node as first and last node (problem 2)
            '''
            if len(vertices_index) >= 1:
                indices = [0, -1]
                if len(vertices_index) == 2:
                    indices = [[0, -1], [-1, 0]]

                is_foward = np.allclose(vertices_params, edge_param_local[indices[0]], rtol=0.)
                is_reversed = np.allclose(vertices_params, edge_param_local[indices[1]], rtol=0.)

                if is_foward and is_reversed:
                    print('AAAA')
                    nodes_array = np.asarray([triangulation.Node(int(evl - 1)).Transformed(transform.Inverted()).Coord()
                                              for evl in edge_vert_local[[0, -1]]])
                    
                    is_foward = np.allclose(vertices_array, nodes_array[indices[0]], rtol=0.)
                    is_reversed = np.allclose(vertices_array, nodes_array[indices[1]], rtol=0.)

                    if is_foward and is_reversed:
                        print('ERROR')
                        continue
                
                new_indices = [-1, 0] if is_reversed else [0, -1]

                if len(vertices_index) == 1 and len_diff == 0:
                    #triangulation is not closed but the egde is
                    #changing triangulation to be closed too
                    if is_foward:
                        bound_indices = [0, -1]
                    elif is_reversed:
                        bound_indices = [-1, 0]

                    first_vertex, last_vertex = edge_vert_local[bound_indices]

                    edge_vert_local[bound_indices[1]] = first_vertex

                    assert face_vert_local_map[last_vertex] == last_vertex or face_vert_local_map[last_vertex] == first_vertex

                    face_vert_local_map[last_vertex] = first_vertex


                # elif len(vertices_index) == 2 and len_diff == 1:
                #     continue
                #     #triangulation is closed but the egde is not
                #     print(edge_index)
                #     node = np.asarray(triangulation.Node(int(edge_vert_local[0] + 1)).Coord())
                #     dists = np.linalg.norm(vertices_array - node, axis=1)
                #     keep_first = np.argmin(dists) == 0

                #     print('BEFORE:')
                #     print(f'{edge_vert_local} {edge_vert_global_map} {face_vert_global_map[edge_vert_local]} {vertices_index} {vertices_mesh_data[vertices_index]}')
                #     print(edge_param_local)
                #     print(edge_param_global)
                #     print(vertices_params)
                #     print(vertices_array)
                #     print(np.asarray([triangulation.Node(int(i + 1)).Coord() for i in edge_vert_local[[0,-1]]]))
                #     if keep_first:
                #         edge_vert_local = edge_vert_local[:-1]
                #         edge_vert_global_map = edge_vert_global_map[:-1]
                #         edge_param_local = edge_param_local[:-1]
                #         edge_param_global = edge_param_global[:-1]
                #         local_edge_map = local_edge_map[:-1]
                #         vertices_index = vertices_index[:-1]
                #         vertices_params = vertices_params[:-1]
                #         vertices_array = vertices_array[:-1]
                #         new_indices = [0]
                #     else:
                #         edge_vert_local = edge_vert_local[1:]
                #         edge_vert_global_map = edge_vert_global_map[1:]
                #         edge_param_local = edge_param_local[1:]
                #         edge_param_global = edge_param_global[1:]
                #         local_edge_map = local_edge_map[1:]
                #         vertices_index = vertices_index[1:]
                #         vertices_params = vertices_params[1:]
                #         vertices_array = vertices_array[1:]
                #         new_indices = [-1]
                    
                #     print('=================================================\nAFTER:')
                #     print(f'{edge_vert_local} {edge_vert_global_map} {face_vert_global_map[edge_vert_local]} {vertices_index} {vertices_mesh_data[vertices_index]}')
                #     print(edge_param_local)
                #     print(edge_param_global)
                #     print(vertices_params)
                #     print(vertices_array)
                #     print(triangulation.Node(int((edge_vert_local[0] if keep_first else edge_vert_local[-1]) + 1)).Coord())

                #     #continue

                vertices_local_index_map = np.zeros(len(vertices_index), dtype=np.int64) - 1
                
                for id, vertex_index in enumerate(vertices_index):
                    #print('==================')
                    #print('vert index:', vertex_index)
                    vertex_local_edge_index = new_indices[id]
                    #print('node index:', vertex_local_edge_index)

                    vertex_local_index = edge_vert_local[vertex_local_edge_index]
                    #print('edge local index:', vertex_local_index)
                    vertex_global_index = vertices_mesh_data[vertex_index]
                    #print('vert global index:', vertex_global_index)
                    #print('edge global index:', edge_vert_global_map[vertex_local_edge_index])

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
  
            else:
                assert False, f'Edge {edge_index} has {len(vertices_index)} bound vertices'       
                

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
                       f'{edge_vert_global_map[edge_mask][face_mask]}'
                                
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
            # print('mask:', mask_minus_one)
            # print('global:', face_vert_global_map)
            # print('remap:', face_vert_local_map)
            # print('global remapped:', face_vert_global_map[face_vert_local_map])
            # print(face_vert_global_map[~(face_vert_global_map == face_vert_global_map[face_vert_local_map])])
            # print(mask_minus_one)
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
                    assert np.allclose(mesh_vertices[i1_m], np.array(triangulation.Node(i1).Transformed(transform).Coord()), rtol=0.) and \
                           np.allclose(mesh_vertices[i2_m], np.array(triangulation.Node(i2).Transformed(transform).Coord()), rtol=0.) and \
                           np.allclose(mesh_vertices[i3_m], np.array(triangulation.Node(i3).Transformed(transform).Coord()), rtol=0.), \
                           f'Vertices remapping problem.\n' \
                           f'{mesh_vertices[i1_m]} != {np.array(triangulation.Node(i1).Transformed(transform).Coord())} or \n' \
                           f'{mesh_vertices[i2_m]} != {np.array(triangulation.Node(i2).Transformed(transform).Coord())} or \n' \
                           f'{mesh_vertices[i3_m]} != {np.array(triangulation.Node(i3).Transformed(transform).Coord())}'
                continue
                
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

    #print('problematics:', problematics)
    #print('good:', len(faces) - problematics)
    #print('locations:', len(locations))

    for edge_index in range(len(edges_mesh_data)):
        if type(edges_mesh_data[edge_index]['vert_indices']) is not list:
            edges_mesh_data[edge_index]['vert_indices'] = edges_mesh_data[edge_index]['vert_indices'].tolist()
        if type(edges_mesh_data[edge_index]['vert_parameters']) is not list:
            edges_mesh_data[edge_index]['vert_parameters'] = edges_mesh_data[edge_index]['vert_parameters'].tolist()
                                    
    return mesh_vertices, mesh_faces, edges_mesh_data, faces_mesh_data

def OCCMeshGeneration(shape):
    print('\n[PythonOCC] Mesh Generation...')
    parameters = IMeshTools_Parameters()

    #Ref: https://dev.opencascade.org/doc/refman/html/struct_i_mesh_tools___parameters.html#a3027dc569da3d3e3fcd76e0615befb27
    parameters.MeshAlgo = -1
    parameters.Angle = 0.1
    parameters.Deflection = 0.01
    parameters.MinSize = 0.01
    parameters.Relative = True
    parameters.ForceFaceDeflection = True
    parameters.InParallel = True

    brep_mesh = BRepMesh_IncrementalMesh(shape, parameters)
    brep_mesh.Perform()
    assert brep_mesh.IsDone()