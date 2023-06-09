import numpy as np 

from copy import copy

from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.IMeshTools import IMeshTools_Parameters
from OCC.Core.GeomAbs import GeomAbs_CurveType
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.BRepTools import breptools_Compare
from OCC.Core.STEPConstruct import STEPConstruct_PointHasher
from OCC.Core.gp import gp_Pnt

from lib.AsGeometryOCCWrapper import CurveFactory
import pprint
pp = pprint.PrettyPrinter(indent=4)

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
    #Loop for faces 
    problematics = 0
    #locations = []
    #locations_map = {}
    for face_index, face in enumerate(tqdm(faces)):

        face_orientation = face.Orientation()

        brep_tool = BRep_Tool()
        location = TopLoc_Location()
        #status = searchEntityInMap(location, locations_map, use_issame=False)
        #if status == -1:
         #   addEntityToMap(0, location, locations_map)
        
        triangulation = brep_tool.Triangulation(face, location, 0)
        transform = location.Transformation()
        trans = np.array(transform.TranslationPart().Coord())
        R = transform.GetRotation()
        rot = np.array([R.X(), R.Y(), R.Z(), R.W()])

        #if not(np.all(trans == [0, 0, 0]) and np.all(rot == [0, 0, 0, 1])):
        #    #print('problematic')
        #    problematics += 1
        #    continue

        if triangulation is None:
            #WARNING
            continue

        number_vertices = triangulation.NbNodes()

        face_vert_global_map = np.zeros(number_vertices, dtype=np.int64) - 1 # map local face mesh id to global mesh id
        face_vert_params = []
        face_vert_local_map = np.arange(number_vertices, dtype=np.int64)     # map ids to another local ids (useful in deal with repeated vertices)

        edge_vertices_local_data = []
        #looking to all edges that bound the current face
        edges_index = face_edges_map[face_index]

        for edge_index in edges_index:
            #print('vmd:', vertices_mesh_data)

            edge = edges[edge_index] #TopoDS_Edge object
            
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

            edge_vert_local_unique, edge_vert_local_counts = np.unique(edge_vert_local, return_counts=True)
            if len(edge_vert_local_unique) == 1:
                print('----------------------------------------')
                print('PROBLEM OF ONE VERTEX JUST')
                print('Type:', str(GeomAbs_CurveType(BRepAdaptor_Curve(edge).GetType())))
                print('Index:',edge_index)
                print('Edge Local:',edge_vert_local)
                print('Edge Param Local:',edge_param_local)
                print('Edge Global:', edge_vert_global_map)
                print('Edge Param Global:', edge_param_global)
                print('Vertices:', vertices_index)
                print('Vertices Parmams:', vertices_params)

            mask_major_2 = edge_vert_local_counts >= 2
            len_diff = np.count_nonzero(mask_major_2)
            assert len_diff <= 1, \
                   f'More than one repreated vertex in Polygon On Triangulation. {str(BRepAdaptor_Curve(edge).GetType())} {edge_vert_local}'

            #some edges have more than two vertices with the same id because of the siz of the edges, we are not working with it
            if True: # len(edge_vert_local_unique) > 1:
                #closeness fixing
                '''
                    Assuming 'nodes' as mesh vertices and 'vertices' as curves vertices:
                    - a curve is "closed" if it has just one vertex
                    - a closed curve must have the same node as first and last node (problem 1)
                    - an openned curve must not have the same node as first and last node (problem 2)
                '''
                if len(vertices_index) == 1:
                    is_foward = np.allclose(vertices_params, edge_param_local[0], rtol=0.)
                    is_reversed = np.allclose(vertices_params, edge_param_local[-1], rtol=0.)

                    if is_foward and is_reversed:
                        print('NUMERICAL ERROR')
                        print(vertices_params, edge_param_local[[0, -1]])
                        foward_distance = np.linalg.norm(vertices_params - edge_param_local[0])
                        reversed_distance = np.linalg.norm(vertices_params - edge_param_local[-1])
                        if foward_distance <= reversed_distance:
                            is_reversed = False
                        else:
                            is_foward = False
                        
                        print(is_foward, is_reversed)

                    assert is_foward or is_reversed, 'It is not repeating in the start and end vertices.'

                    if len_diff == 0:
                        #triangulation is not closed but the egde is

                        #print('Problem 1 to be Solved')
                        
                        #assuming that reapeated vertex happen just at the start and end indices
                        if is_foward:
                            bound_indices = [0, -1]
                        elif is_reversed:
                            bound_indices = [-1, 0]

                        first_vertex, last_vertex = edge_vert_local[bound_indices]

                        edge_vert_local[bound_indices[1]] = first_vertex

                        assert face_vert_local_map[last_vertex] == last_vertex or face_vert_local_map[last_vertex] == first_vertex

                        face_vert_local_map[last_vertex] = first_vertex


                elif len(vertices_index) == 2:
                    is_foward = np.allclose(vertices_params, edge_param_local[[0, -1]], rtol=0.)
                    is_reversed = np.allclose(vertices_params, edge_param_local[[-1, 0]], rtol=0.)

                    if is_foward and is_reversed:
                        print('NUMERICAL ERROR')
                        print(vertices_params, edge_param_local[[0, -1]])
                        foward_distance = np.linalg.norm(vertices_params - edge_param_local[[0, -1]])
                        reversed_distance = np.linalg.norm(vertices_params - edge_param_local[[-1, 0]])
                        if foward_distance <= reversed_distance:
                            is_reversed = False
                        else:
                            is_foward = False
                        print(is_foward, is_reversed)

                    assert is_foward or is_reversed, 'It is not repeating in the start and end vertices.'
                    
                    if len_diff == 1:
                        print('Problem 2 to be Solved')
                        assert edge_vert_local[0] == edge_vert_local[-1], \
                            'Wrong Assumption. Closeness is not about first and last nodes always'
                        
                        #print('Problem 2 to be Solved')
                        local_vertices = [vertices[vertex_index] for vertex_index in vertices_index]


                        is_last_id = True
                        min_dist = float('inf')
                        node_array = np.array(triangulation.Node(int(edge_vert_local[0] + 1)).Transformed(transform).Coord())
                        for i, lv in enumerate(local_vertices):
                            vert_array = np.array(brep_tool.Pnt(lv).Coord())
                            curr_dist = np.linalg.norm(vert_array - node_array)
                            if curr_dist < min_dist:
                                is_last_id = not bool(i)
                                min_dist = curr_dist
                        
                        is_last_id = (not is_last_id) if is_reversed else is_last_id
                        
                        id_to_change = 0 if is_last_id else -1

                        #print(id_to_change)
                        right_tol = brep_tool.Tolerance(local_vertices[id_to_change])
                        right_pnt = brep_tool.Pnt(local_vertices[id_to_change]).Transformed(transform.Inverted())
                        current_index = edge_vert_local[id_to_change]
                        #print(right_pnt.Coord())     

                        face_nodes_match_indices = []
                        for i in range(1, number_vertices + 1):
                            if triangulation.Node(i).IsEqual(right_pnt, right_tol) and (i - 1) != current_index:
                                face_nodes_match_indices.append(i - 1)

                            
                        assert len(face_nodes_match_indices) == 1, \
                               f'{current_index} {face_nodes_match_indices}'
                            
                        edge_vert_local[id_to_change] = face_nodes_match_indices[0]

                        if len(edge_vert_local_unique) == 1:
                            print('Type:', str(GeomAbs_CurveType(BRepAdaptor_Curve(edge).GetType())))
                            print('Index:',edge_index)
                            print('Edge Local:',edge_vert_local)
                            print('Edge Param Local:', edge_param_local)
                            print('Face Global:', face_vert_global_map[edge_vert_local])
                            print('----------------------------------------')


                else:
                    assert False, f'Edge {edge_index} has {len(vertices_index)} bound vertices'

            
            vertices_local_index_map = np.zeros(len(vertices_index), dtype=np.int64) - 1
            vertices_global_index_map = np.zeros(len(vertices_index), dtype=np.int64) - 1        
            
            #TODO: maybe this part can be merged in the closeness correction
            for id, vertex_index in enumerate(vertices_index):
                param = vertices_params[id]
                
                mask = np.isclose(edge_param_local, param, rtol=0.)
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

            evld = {
                'edge_index': edge_index,
                'vert_indices': edge_vert_local,
                'vert_parameters': edge_param_local,
            }

            edge_vertices_local_data.append(evld)
   
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

        for evld in edge_vertices_local_data:
            edge_index = evld['edge_index']

            edges_mesh_data[edge_index]['vert_indices'] = face_vert_global_map[evld['vert_indices']].tolist()
            edges_mesh_data[edge_index]['vert_parameters'] = evld['vert_parameters'].tolist()
        
        faces_mesh_data[face_index] = {'vert_indices': face_vert_global_map.tolist(), 
                                       'vert_parameters': face_vert_params, 'face_indices': face_indices}

    #unique_vert = np.arange(len(mesh_vertices))
    #unique_vert_faces = np.unique(np.asarray(mesh_faces))
    #assert np.all(unique_vert_faces == unique_vert), \
    #           f'ERROR: unreferenced vertices in global mesh'

    #print('problematics:', problematics)
    #print('good:', len(faces) - problematics)
    #print('locations:', len(locations))

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
    parameters.InParallel = True

    brep_mesh = BRepMesh_IncrementalMesh(shape, parameters)
    brep_mesh.Perform()
    assert brep_mesh.IsDone()