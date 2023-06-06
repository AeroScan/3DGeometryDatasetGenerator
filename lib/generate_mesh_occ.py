import numpy as np 

from copy import copy

from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.IMeshTools import IMeshTools_Parameters
from OCC.Core.GeomAbs import GeomAbs_CurveType
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.BRepTools import breptools_Compare

from tqdm import tqdm

MAX_INT = 2**31 - 1


def searchEntityInMap(entity, map):
    hc = entity.HashCode(MAX_INT)
    index = -1
    if hc in map:
        for qindex, qentity in map[hc]:
            if entity.IsSame(qentity):
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
    #Loop for faces 
    for face_index, face in enumerate(tqdm(faces)):
        #print('----------------------------------------')

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
        face_vert_local_map = np.arange(number_vertices, dtype=np.int64)     # map ids to another local ids (useful in deal with repeated vertices)

        #looking to all edges that bound the current face
        edges_index = face_edges_map[face_index]
        for edge_index in edges_index:
            #print('vmd:', vertices_mesh_data)

            edge = edges[edge_index] #TopoDS_Edge object

            brep_adaptor = BRepAdaptor_Curve(edge)
            #print(str(GeomAbs_CurveType(brep_adaptor.GetType())))
            
            polygon = brep_tool.PolygonOnTriangulation(edge, triangulation, location) # projecting edge in the face triangulation
            if polygon is None:
                #WARNING
                continue

            edge_vert_local = np.asarray(polygon.Nodes(), dtype=np.int64) - 1 # map from mesh edge indices to face mesh indices
            edge_param_local = np.asarray(polygon.Parameters())
            
            egi = np.asarray(edges_mesh_data[edge_index]['vert_indices'], dtype=np.int64)
            edge_vert_global_map = egi if len(egi) > 0 else (np.zeros(len(edge_vert_local), dtype=np.int64) - 1) # map from mesh edge indices to global mesh indices
            egp = np.asarray(edges_mesh_data[edge_index]['vert_parameters'], dtype=np.float64)
            edge_param_global = egp if len(egp) > 0 else (np.zeros(len(edge_param_local), dtype=np.float64) - 1)

            vertices_index = edge_vertices_map[edge_index]
            vertices_params = np.array([brep_tool.Parameter(vertices[vertex_index], edge, face) for vertex_index in vertices_index])

            edge_vert_local_unique, unique_indices = np.unique(edge_vert_local, return_index=True)
            len_diff = len(edge_vert_local) - len(edge_vert_local_unique)
            assert len_diff <= 1, \
                   'More than one repreated vertex in Polygon On Triangulation'
            
            if len(vertices_index) == 1:
                is_first = np.allclose(vertices_params, edge_param_local[0])
                is_last = np.allclose(vertices_params, edge_param_local[-1])
                
                assert is_first or is_last, 'It is not repeating in the start and end vertices.'

                if len_diff == 0:
                    print('Problem 1 to be Solved')
                    
                    #assuming that reapeated vertex happen just at the start and end indices
                    if is_first:
                        bound_indices = [0, -1]
                    elif is_last:
                        bound_indices = [-1, 0]

                    #print(edge_param_local[bound_indices])

                    first_vertex, last_vertex = edge_vert_local[bound_indices]

                    #print(first_vertex, last_vertex)
                    #assert face_vert_global_map[last_vertex] == -1 or face_vert_global_map[last_vertex] == -2, \
                    #       f'{face_vert_global_map[last_vertex]} {face_vert_global_map[first_vertex]}'

                    #face_vert_global_map[last_vertex] = -2
                    edge_vert_local[bound_indices[1]] = first_vertex

                    assert face_vert_local_map[last_vertex] == last_vertex or face_vert_local_map[last_vertex] == first_vertex
                    face_vert_local_map[last_vertex] = first_vertex

                    #print(face_vert_local_map)

            elif len(vertices_index) == 2:
                assert not breptools_Compare(vertices[vertices_index[0]], vertices[vertices_index[1]]), \
                       f'Edge has two equal bound vertices with different ids.'

                assert np.allclose(vertices_params, edge_param_local[[0,-1]]) or np.allclose(vertices_params, edge_param_local[[-1,0]]), \
                       'Solution to fix NOT closed problem did not work.' 
                
                if len_diff == 1:
                    print('Problem 2 to be Solved')

            else:
                assert False, f'Edge {edge_index} has {len(vertices_index)} bound vertices'
                           
            vertices_local_index_map = np.zeros(len(vertices_index), dtype=np.int64) - 1
            vertices_global_index_map = np.zeros(len(vertices_index), dtype=np.int64) - 1
            for id, vertex_index in enumerate(vertices_index):
                param = vertices_params[id]
                
                mask = np.isclose(edge_param_local, param)
                indices = np.where(mask)[0]
                
                assert len(indices) == 1, f'{len(indices)} params close to the same vertex.'

                vertex_local_edge_index = indices[0]

                vertex_local_index = edge_vert_local[vertex_local_edge_index]
                vertex_global_index = vertices_mesh_data[vertex_index]

                if vertex_global_index == -1:
                    assert edge_vert_global_map[vertex_local_edge_index] == -1, \
                           'vertex has no global index but edge already has.' \
                           f' Edge global vertices: {edge_vert_global_map}'
                    
                else:
                    if edge_vert_global_map[vertex_local_edge_index] != -1:
                        assert edge_vert_global_map[vertex_local_edge_index] == vertex_global_index, \
                            'different global indices between vertex and edge.' \
                            f' {edge_vert_global_map[vertex_local_edge_index]} != {vertex_global_index}'
                    
                    edge_vert_global_map[vertex_local_edge_index] = vertex_global_index
                    edge_param_global[vertex_local_edge_index] = param

                vertices_local_index_map[id] = vertex_local_index
                vertices_global_index_map[id] = vertex_global_index

            edge_mask = edge_vert_global_map != -1 # already mapped edge vertex mask

            #Edge already has global params, need to verify consistecy and pass the node ids to face
            if np.any(edge_mask):

                #Verify if params are the same, may me reverse oriented (or not)
                assert np.all(np.isclose(edge_param_local[edge_mask], edge_param_global[edge_mask])), \
                       f'Edge {edge_index} has different vertex parameters. \n' \
                       f'{edge_param_local[edge_mask]} != {edge_param_global[edge_mask]}'

                face_mask = face_vert_global_map[edge_vert_local[edge_mask]] != -1 # already mapped face vertex mask
                
                #Assert to verify local remap
                assert np.all(face_vert_global_map[edge_vert_local[edge_mask]][face_mask] == \
                              face_vert_global_map[face_vert_local_map][edge_vert_local[edge_mask]][face_mask])
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
                if face_vert_global_map[i - 1] == -1:
                    pnt = triangulation.Node(int(i))
                    pnt.Transform(transform)
                    pnt_array = np.array(pnt.Coord())
                    mesh_vertices.append(pnt_array)
                    face_vert_global_map[i - 1] = len(mesh_vertices) - 1
            
            edges_mesh_data[edge_index]['vert_indices'] = face_vert_global_map[edge_vert_local].tolist()
            edges_mesh_data[edge_index]['vert_parameters'] = edge_param_local.tolist()
            vertices_mesh_data[np.array(vertices_index)] = face_vert_global_map[np.array(vertices_local_index_map)]
                
        for i in range(1, number_vertices + 1):
            if face_vert_global_map[i - 1] != -2:
                if face_vert_global_map[i - 1] == -1:
                    pnt = triangulation.Node(i)
                    pnt.Transform(transform)
                    pnt_array = np.array(pnt.Coord())
                    mesh_vertices.append(pnt_array)
                    face_vert_global_map[i - 1] = len(mesh_vertices) - 1

                uv_node = triangulation.UVNode(i)
                face_vert_params.append(list(uv_node.Coord()))
        

        face_vert_global_map = face_vert_global_map[face_vert_local_map]

        vertices_local_faces_indices = []
        face_indices = []
        number_faces = triangulation.NbTriangles()
        for i in range(1, number_faces + 1):
            i1, i2, i3 = triangulation.Triangle(i).Get()
            vertices_local_faces_indices += [i1, i2, i3]
            i1 = face_vert_global_map[i1 - 1]
            i2 = face_vert_global_map[i2 - 1]
            i3 = face_vert_global_map[i3 - 1]
            if i1 == i2 or i1 == i3 or i2 == i3:
                #WARNING: ignoring faces with repeated vertices (temporary solution)
                continue
            if face_orientation == 0:
                verts_of_face = np.array([i1, i2, i3])
                mesh_faces.append(verts_of_face)
                face_indices.append(len(mesh_faces) - 1)
            elif face_orientation == 1:
                verts_of_face = np.array([i3, i2, i1])
                mesh_faces.append(verts_of_face)
                face_indices.append(len(mesh_faces) - 1)
            else:
                assert False, 'Face Orientation not Supported yet.'

        occ_error = not np.all(np.unique(vertices_local_faces_indices) - 1 == np.arange(number_vertices))

        unique_vert = np.unique(face_vert_global_map)
        unique_vert_faces = np.unique(np.asarray(mesh_faces[face_indices[0]:(face_indices[-1] + 1)]), axis=None)
                                      
        diff = np.setdiff1d(unique_vert, unique_vert_faces)
        #Verifying unreferenced vertices
        if not occ_error:
            assert len(diff) == 0, f'ERROR: unreferenced vertices local mesh: {diff}'
        else:
            print('OCC ERROR')
        
        faces_mesh_data[face_index] = {'vert_indices': face_vert_global_map.tolist(), 'vert_parameters': face_vert_params, 'face_indices': face_indices}

    #unique_vert = np.arange(len(mesh_vertices))
    #unique_vert_faces = np.unique(np.asarray(mesh_faces))
    #assert np.all(unique_vert_faces == unique_vert), \
    #           f'ERROR: unreferenced vertices in global mesh'

    return mesh_vertices, mesh_faces, edges_mesh_data, faces_mesh_data

def OCCMeshGeneration(shape):
    print('\n[PythonOCC] Mesh Generation...')
    parameters = IMeshTools_Parameters()

    #Ref: https://dev.opencascade.org/doc/refman/html/struct_i_mesh_tools___parameters.html#a3027dc569da3d3e3fcd76e0615befb27
    parameters.MeshAlgo = -1
    parameters.Angle = 0.1
    parameters.Deflection = 0.01
    #parameters.MinSize = 0.1
    parameters.Relative = True
    parameters.InParallel = True

    brep_mesh = BRepMesh_IncrementalMesh(shape, parameters)
    brep_mesh.Perform()
    assert brep_mesh.IsDone()




# def findPointInListWithHashCode(point, points, hash_codes):
#     hc = STEPConstruct_PointHasher.HashCode(point, MAX_INT)
#     index = -1
#     if hc in hash_codes:
#         index = -2
#         for i in hash_codes[hc]:
#             array = points[i]
#             point2 = gp_Pnt(array[0], array[1], array[2])
#             if STEPConstruct_PointHasher.IsEqual(point, point2):
#                 index = i
#                 break
#     return index, hc