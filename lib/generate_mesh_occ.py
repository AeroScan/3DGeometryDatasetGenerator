import numpy as np 

from copy import copy

from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.gp import gp_Pnt
from OCC.Core.STEPConstruct import STEPConstruct_PointHasher
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.IMeshTools import IMeshTools_Parameters

from sortedcontainers import SortedSet

from tqdm import tqdm

MAX_INT = 2**31 - 1

def findPointInListWithHashCode(point, points, hash_codes):
    hc = STEPConstruct_PointHasher.HashCode(point, MAX_INT)
    index = -1
    if hc in hash_codes:
        index = -2
        for i in hash_codes[hc]:
            array = points[i]
            point2 = gp_Pnt(array[0], array[1], array[2])
            if STEPConstruct_PointHasher.IsEqual(point, point2):
                index = i
                break
    return index, hc

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

def computeMeshData(edges, faces, topology):
    edges_mesh_data = []
    edges_map = {}
    print('\n[PythonOCC] Mapping Edges...')
    for i, edge in tqdm(enumerate(edges)):
        edges_mesh_data.append(SortedSet())
        addEntityToMap(i, edge, edges_map)

    faces_mesh_data = []
    face_edges_map = []
    faces_map = {}
    print('\n[PythonOCC] Mapping Faces...')
    for i, face in tqdm(enumerate(faces)):
        faces_mesh_data.append(None)
        addEntityToMap(i, face, faces_map)
        edges_indices = [searchEntityInMap(edge, edges_map) for edge in topology.edges_from_face(face)]
        face_edges_map.append(edges_indices)
        
    mesh_vertices = []
    mesh_faces = []
    print('\n[PythonOCC] Generating Mesh Data...')
    for face_index, face in tqdm(enumerate(faces)):     
        face_orientation = face.Orientation()

        brep_tool = BRep_Tool()
        location = TopLoc_Location()
        triangulation = brep_tool.Triangulation(face, location)
        transform = location.Transformation()

        if triangulation is None:
            print(f'ERROR: face {face_index} could not be triangularized.')
            continue

        number_vertices = triangulation.NbNodes()
        vert_indices = [-1 for x in range(number_vertices)]
        vert_parameters = []

        for edge_index in face_edges_map[face_index]:
            edge = edges[edge_index]

            polygon = brep_tool.PolygonOnTriangulation(edge, triangulation, location)

            if polygon is None:
                print(f'ERROR: edge {edge_index} do not form a polygon on face {face_index} triangulation.')
                continue

            polygon_nodes = [x - 1 for x in polygon.Nodes()]
            polygon_parameters = list(polygon.Parameters())
            minus_one = [-1 for i in range(len(polygon_nodes))]    

            polygon_mesh_data_set = SortedSet(zip(polygon_parameters, minus_one, polygon_nodes))

            edge_mesh_data_set = edges_mesh_data[edge_index]

            edge_mesh_data_set.union(polygon_mesh_data_set)

            i = 0
            while i < (len(edge_mesh_data_set) - 1):
                parameters_curr, global_id_curr, local_id_curr = edge_mesh_data_set[i]
                parameters_next, global_id_next, local_id_next = edge_mesh_data_set[i+1]

                if parameters_curr == parameters_next:
                    global_id_curr = global_id_next if global_id_next != -1 else global_id_curr
                    local_id_curr = local_id_next if local_id_next != -1 else local_id_curr
                    vert_indices[local_id_curr] = global_id_curr
                    edge_mesh_data_set.pop(i+1)
                    edge_mesh_data_set[i] = (parameters_curr, global_id_curr, local_id_curr)
            
                i+=1

            edges_mesh_data[edge_index] = edge_mesh_data_set

        for i in range(1, number_vertices + 1):
            pnt = triangulation.Node(i)
            pnt.Transform(transform)
            pnt_array = np.array(pnt.Coord())

            if vert_indices[i - 1] == -1:
                mesh_vertices.append(pnt_array)
                vert_indices[i - 1] = len(mesh_vertices) - 1

            uv_node = triangulation.UVNode(i)
            vert_parameters.append(list(uv_node.Coord()))

        for edge_index in face_edges_map[face_index]:
            edge_mesh_data_set = edges_mesh_data[edge_index]
            i = 0
            while i < len(edge_mesh_data_set):
                parameters_curr, global_id_curr, local_id_curr = edge_mesh_data_set[i]
                if global_id_curr == -1:
                    global_id_curr = vert_indices[local_id_curr]
                local_id_curr = -1
                edges_mesh_data[edge_index][i] = (parameters_curr, global_id_curr, local_id_curr)
                i +=1

    # for hc, ind in modified_edges_data:
    #     mesh_data = edges_data[hc][ind]['mesh_data']
    #     mask = (mesh_data['vert_indices'] == -1)
    #     mesh_data['vert_indices'][mask] = vert_indices[mesh_data['vert_local_indices'][mask]]
    #     mesh_data['vert_indices'] = mesh_data['vert_indices'].tolist()
    #     edges_data[hc][ind]['mesh_data'].pop('vert_local_indices')
          
        face_indices = []

        number_faces = triangulation.NbTriangles()
        for i in range(1, number_faces + 1):
            i1, i2, i3 = triangulation.Triangle(i).Get()
            i1 = vert_indices[i1 - 1]
            i2 = vert_indices[i2 - 1]
            i3 = vert_indices[i3 - 1]
            if face_orientation == 0:
                verts_of_face = np.array([i1 , i2, i3])
                mesh_faces.append(verts_of_face)
                face_indices.append(len(mesh_faces) - 1)
            elif face_orientation == 1:
                verts_of_face = np.array([i3, i2, i1])
                mesh_faces.append(verts_of_face)
                face_indices.append(len(mesh_faces) - 1)
            else:
                print("Broken face orientation", face_orientation)


        


def OCCMeshGeneration(shape):
    print('\n[PythonOCC] Mesh Generation...')
    parameters = IMeshTools_Parameters()

    #Ref: https://dev.opencascade.org/doc/refman/html/struct_i_mesh_tools___parameters.html#a3027dc569da3d3e3fcd76e0615befb27
    parameters.MeshAlgo = -1
    parameters.Angle = 0.1
    parameters.Deflection = 0.01
    # parameters.MinSize = 0.1
    parameters.Relative = True
    parameters.InParallel = True

    brep_mesh = BRepMesh_IncrementalMesh(shape, parameters)
    brep_mesh.Perform()
    assert brep_mesh.IsDone()

def registerEdgeMeshInGlobalMesh(edge, mesh):
    assert 'vertices' in mesh.keys() and 'vertices_hcs' in mesh.keys()

    brep_tool = BRep_Tool()
    location = TopLoc_Location()
    brep_mesh = brep_tool.Polygon3D(edge, location)
    transform = location.Transformation()

    edge_mesh_data = {}
    if brep_mesh != None:
        vertices = mesh['vertices']
        vertices_hcs = mesh['vertices_hcs']

        vert_indices = []

        nodes = list(brep_mesh.Nodes())
        vert_parameters = list(brep_mesh.Parameters())

        for i in range(1, len(nodes) + 1):
            pnt = nodes[i-1]
            pnt.Transform(transform)
            index, hc = findPointInListWithHashCode(pnt, vertices, vertices_hcs)
            if index < 0:
                old_index = index
                vertices.append(np.array(pnt.Coord()))
                index = len(vertices) - 1
                if old_index == -2:
                    vertices_hcs[hc].append(index)
                else:
                    vertices_hcs[hc] = [index]
            vert_indices.append(index)

        if len(vert_indices) > 0:
            edge_mesh_data['vert_indices'] = vert_indices
            edge_mesh_data['vert_parameters'] = vert_parameters

    return edge_mesh_data


def registerFaceMeshInGlobalMesh(face, mesh, face_edges, edges_data):

    assert 'vertices' in mesh.keys() and 'faces' in mesh.keys()

    face_orientation = face.Orientation()

    brep_tool = BRep_Tool()
    location = TopLoc_Location()
    brep_mesh = brep_tool.Triangulation(face, location)
    transform = location.Transformation()

    face_mesh_data = {}
    modified_edges_data = []
    if brep_mesh is not None:
        verts = mesh['vertices']  

        vert_parameters = []

        number_vertices = brep_mesh.NbNodes()
        vert_indices = np.zeros(number_vertices, dtype=np.int64) - 1
        for face_edge in face_edges:
            hc = face_edge.HashCode(MAX_INT)

            if hc in edges_data:
                found_edge = False
                for ind, edge_data in enumerate(edges_data[hc]):
                    if face_edge.IsSame(edge_data['entity']):
                        found_edge = True
                        poly_on_triang = brep_tool.PolygonOnTriangulation(face_edge, brep_mesh, location)
                        if poly_on_triang is not None:
                            if 'vert_indices' not in edge_data['mesh_data']:
                                edge_data['mesh_data']['vert_indices'] = []
                            if 'vert_parameters' not in edge_data['mesh_data']:
                                edge_data['mesh_data']['vert_parameters'] = []

                            poly_nodes = list(poly_on_triang.Nodes())
                            poly_parmeters = list(poly_on_triang.Parameters())

                            vert_indices_curr = edge_data['mesh_data']['vert_indices']
                            vert_parameters_curr = edge_data['mesh_data']['vert_parameters']

                            vert_indices_curr_final = []
                            vert_local_indices_curr_final = []
                            vert_parameters_curr_final = []
                                                        
                            i = 0
                            j = 0
                            while i < len(poly_nodes) and j < len(vert_indices_curr):
                                if poly_parmeters[i] == vert_parameters_curr[j]:
                                    vert_indices_curr_final.append(vert_indices_curr[j])
                                    vert_local_indices_curr_final.append(-1)
                                    vert_parameters_curr_final.append(poly_parmeters[i])
                                    vert_indices[poly_nodes[i] - 1] = vert_indices_curr[j]
                                    j += 1
                                    i += 1
                                elif poly_parmeters[i] > vert_parameters_curr[j]:
                                    vert_indices_curr_final.append(vert_indices_curr[j])
                                    vert_local_indices_curr_final.append(-1)
                                    vert_parameters_curr_final.append(vert_parameters_curr[j])
                                    j += 1
                                else:
                                    vert_indices_curr_final.append(-1)
                                    vert_local_indices_curr_final.append(poly_nodes[i] - 1)
                                    vert_parameters_curr_final.append(poly_parmeters[i])
                                    i += 1
                            
                            while i < len(poly_nodes):
                                vert_indices_curr_final.append(-1)
                                vert_local_indices_curr_final.append(poly_nodes[i] - 1)
                                vert_parameters_curr_final.append(poly_parmeters[i])
                                i += 1
                            
                            while j < len(vert_indices_curr):
                                vert_indices_curr_final.append(vert_indices_curr[j])
                                vert_local_indices_curr_final.append(-1)
                                vert_parameters_curr_final.append(vert_parameters_curr[j])
                                j += 1
                                
                            new_edge_mesh_data = {'vert_indices': np.asarray(vert_indices_curr_final), 'vert_local_indices': np.asarray(vert_local_indices_curr_final), 'vert_parameters': vert_parameters_curr_final}

                            edges_data[hc][ind]['mesh_data'] = new_edge_mesh_data

                            modified_edges_data.append((hc, ind))
                        else:
                            print('ERROR: none polygon on triangulation.')
                        break
                if found_edge == False:
                    print('ERROR: some edge has not been computed before. (IsSame Error)')
            else:
                print('ERROR: some edge has not been computed before. (HashCode Error)')

        
        for i in range(1, number_vertices + 1):
            pnt = brep_mesh.Node(i)
            pnt.Transform(transform)
            pnt_array = np.array(pnt.Coord())

            if vert_indices[i - 1] == -1:
                verts.append(pnt_array)
                vert_indices[i - 1] = len(verts) - 1

            uv_node = brep_mesh.UVNode(i)
            vert_parameters.append(list(uv_node.Coord()))
        
        for hc, ind in modified_edges_data:
            mesh_data = edges_data[hc][ind]['mesh_data']
            mask = (mesh_data['vert_indices'] == -1)
            mesh_data['vert_indices'][mask] = vert_indices[mesh_data['vert_local_indices'][mask]]
            mesh_data['vert_indices'] = mesh_data['vert_indices'].tolist()
            edges_data[hc][ind]['mesh_data'].pop('vert_local_indices')

        faces = mesh['faces']           
        face_indices = []
    
        number_faces = brep_mesh.NbTriangles()
        for i in range(1, number_faces + 1):
            i1, i2, i3 = brep_mesh.Triangle(i).Get()
            i1 = vert_indices[i1 - 1]
            i2 = vert_indices[i2 - 1]
            i3 = vert_indices[i3 - 1]
            if face_orientation == 0:
                verts_of_face = np.array([i1 , i2, i3])
                faces.append(verts_of_face)
                face_indices.append(len(faces) - 1)
            elif face_orientation == 1:
                verts_of_face = np.array([i3, i2, i1])
                faces.append(verts_of_face)
                face_indices.append(len(faces) - 1)
            else:
                print("Broken face orientation", face_orientation)

            face_mesh_data = {'vert_indices': vert_indices.tolist(), 'vert_parameters': vert_parameters, 'face_indices': face_indices}

    return face_mesh_data, edges_data