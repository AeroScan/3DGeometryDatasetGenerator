import numpy as np 

from copy import copy

from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.gp import gp_Pnt
from OCC.Core.STEPConstruct import STEPConstruct_PointHasher
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.IMeshTools import IMeshTools_Parameters

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
    for i, edge in enumerate(tqdm(edges)):
        edges_mesh_data.append({'vert_indices': [], 'vert_parameters': []})
        addEntityToMap(i, edge, edges_map)

    faces_mesh_data = []
    face_edges_map = []
    faces_map = {}
    print('\n[PythonOCC] Mapping Faces...')
    for i, face in enumerate(tqdm(faces)):
        faces_mesh_data.append(None)
        addEntityToMap(i, face, faces_map)
        edges_indices = [searchEntityInMap(edge, edges_map) for edge in topology.edges_from_face(face)]
        face_edges_map.append(edges_indices)
        
    mesh_vertices = []
    mesh_faces = []
    print('\n[PythonOCC] Generating Mesh Data...')
    for face_index, face in enumerate(tqdm(faces)):     
        face_orientation = face.Orientation()

        brep_tool = BRep_Tool()
        location = TopLoc_Location()
        triangulation = brep_tool.Triangulation(face, location)
        transform = location.Transformation()

        if triangulation is None:
            print(f'ERROR: face {face_index} could not be triangularized.')
            continue

        number_vertices = triangulation.NbNodes()
        vert_indices = np.zeros(number_vertices, dtype=np.int64) - 1
        vert_parameters = []

        for edge_index in face_edges_map[face_index]:
            edge = edges[edge_index]

            polygon = brep_tool.PolygonOnTriangulation(edge, triangulation, location)

            if polygon is None:
                print(f'ERROR: edge {edge_index} do not form a polygon on face {face_index} triangulation.')
                continue

            polygon_nodes = list(polygon.Nodes())
            polygon_parameters = list(polygon.Parameters())

            vert_indices_curr = edges_mesh_data[edge_index]['vert_indices']
            vert_parameters_curr = edges_mesh_data[edge_index]['vert_parameters']

            vert_indices_curr_final = []
            vert_local_indices_curr_final = []
            vert_parameters_curr_final = []

            i = 0
            j = 0
            while i < len(polygon_nodes) and j < len(vert_indices_curr):
                if polygon_parameters[i] == vert_parameters_curr[j]:
                    vert_indices_curr_final.append(vert_indices_curr[j])
                    vert_local_indices_curr_final.append(-1)
                    vert_parameters_curr_final.append(polygon_parameters[i])
                    vert_indices[polygon_nodes[i] - 1] = vert_indices_curr[j]
                    j += 1
                    i += 1
                elif polygon_parameters[i] > vert_parameters_curr[j]:
                    vert_indices_curr_final.append(vert_indices_curr[j])
                    vert_local_indices_curr_final.append(-1)
                    vert_parameters_curr_final.append(vert_parameters_curr[j])
                    j += 1
                else:
                    vert_indices_curr_final.append(-1)
                    vert_local_indices_curr_final.append(polygon_nodes[i] - 1)
                    vert_parameters_curr_final.append(polygon_parameters[i])
                    i += 1
            
            while i < len(polygon_nodes):
                vert_indices_curr_final.append(-1)
                vert_local_indices_curr_final.append(polygon_nodes[i] - 1)
                vert_parameters_curr_final.append(polygon_parameters[i])
                i += 1
            
            while j < len(vert_indices_curr):
                vert_indices_curr_final.append(vert_indices_curr[j])
                vert_local_indices_curr_final.append(-1)
                vert_parameters_curr_final.append(vert_parameters_curr[j])
                j += 1

            new_edge_mesh_data = {'vert_indices': np.asarray(vert_indices_curr_final), 'vert_local_indices': np.asarray(vert_local_indices_curr_final), 'vert_parameters': vert_parameters_curr_final}

            edges_mesh_data[edge_index] = new_edge_mesh_data

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
            mesh_data = edges_mesh_data[edge_index]
            mask = (mesh_data['vert_indices'] == -1)
            mesh_data['vert_indices'][mask] = vert_indices[mesh_data['vert_local_indices'][mask]]
            mesh_data['vert_indices'] = mesh_data['vert_indices'].tolist()
            edges_mesh_data[edge_index].pop('vert_local_indices')

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
        
        faces_mesh_data[face_index] = {'vert_indices': vert_indices.tolist(), 'vert_parameters': vert_parameters, 'face_indices': face_indices}

    return mesh_vertices, mesh_faces, edges_mesh_data, faces_mesh_data

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