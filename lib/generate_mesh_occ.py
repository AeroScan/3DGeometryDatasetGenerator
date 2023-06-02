import numpy as np 

from copy import copy

from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.gp import gp_Pnt
from OCC.Core.STEPConstruct import STEPConstruct_PointHasher
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.IMeshTools import IMeshTools_Parameters
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
from OCC.Core.GeomAbs import GeomAbs_CurveType, GeomAbs_SurfaceType

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

#TODO:remove unreferenced vertices per surface or curve
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
        faces_mesh_data.append({'vert_indices': [], 'vert_parameters': [], 'face_indices': []})
        addEntityToMap(i, face, faces_map)
        edges_indices = [searchEntityInMap(edge, edges_map) for edge in topology.edges_from_face(face)]
        face_edges_map.append(edges_indices)
    mesh_vertices = []
    mesh_faces = []
    print('\n[PythonOCC] Generating Mesh Data...')
    for face_index, face in enumerate(tqdm(faces)):
        print(str(GeomAbs_SurfaceType(BRepAdaptor_Surface(face).GetType())))
        print('============================================================================')

        face_orientation = face.Orientation()

        brep_tool = BRep_Tool()
        location = TopLoc_Location()
        triangulation = brep_tool.Triangulation(face, location, 0)
        transform = location.Transformation()

        if triangulation is None:
            continue

        number_vertices = triangulation.NbNodes()
        face_vert_global_map = np.zeros(number_vertices, dtype=np.int64) - 1
        face_vert_params = []

        #starting with edges that already have vertices
        edges_index = face_edges_map[face_index]
        edges_index = sorted(edges_index, key=lambda x: len(edges_mesh_data[x]['vert_indices']))[::-1]
        print([len(edges_mesh_data[x]['vert_indices']) for x in edges_index])
        for edge_index in edges_index:
            #print(face_vert_global_map)
            #print('====')
            #print(edge_index)
            edge = edges[edge_index]
            print(str(GeomAbs_CurveType(BRepAdaptor_Curve(edge).GetType())), edge_index)

            polygon = brep_tool.PolygonOnTriangulation(edge, triangulation, location)

            if polygon is None:
                #WARNING
                continue

            closed = brep_tool.IsClosed(edge)

            edge_vert_local = np.asarray(polygon.Nodes(), dtype=np.int64) - 1
            edge_param_local = np.asarray(polygon.Parameters())

            if closed:
                last_vert = edge_vert_local[-1]
                edge_vert_local[-1] = edge_vert_local[0]
                print(edge_vert_local)

            edge_vert_global = np.asarray(edges_mesh_data[edge_index]['vert_indices'], dtype=np.int64)
            edge_param_global = np.asarray(edges_mesh_data[edge_index]['vert_parameters'])
            #print(edge_vert_global)

            if len(edge_vert_global) > 0:
                #Edge already has global params, need to verify consistecy and pass the node ids to face

                assert len(edge_vert_local) == len(edge_vert_global), \
                       f'{len(edge_vert_local)} != {len(edge_vert_global)}'
                
                #Verify if params are the same (may me reversed oriented)
                assert np.all(np.isclose(edge_param_local, edge_param_global)), \
                   f'Edge {edge_index} has different vertex parameters. \n' \
                   f'{edge_param_local} != {edge_param_global}'
                
                #Verify if nodes that are already global mapped have the same global ids to the current one
                already_mapped_edge_mask = face_vert_global_map[edge_vert_local] != -1
                #print(already_mapped_edge_mask)
                #print(face_vert_global_map[edge_vert_local][already_mapped_edge_mask] == edge_param_global[already_mapped_edge_mask])
                print('map:', face_vert_global_map)
                print('edge_local:', edge_vert_local)
                print('edge_global:', edge_vert_global)
                assert np.all(face_vert_global_map[edge_vert_local][already_mapped_edge_mask] \
                              == edge_vert_global[already_mapped_edge_mask]), \
                             'Failed in match global indices from different edges.' \
                             f'\n{face_vert_global_map[edge_vert_local][already_mapped_edge_mask]}' \
                             f'!= {edge_vert_global[already_mapped_edge_mask]}' \
                             f'\n{np.asarray(mesh_vertices)[face_vert_global_map[edge_vert_local][already_mapped_edge_mask]]}' \
                             f'== {np.asarray(mesh_vertices)[edge_vert_global[already_mapped_edge_mask]]}?'
                
                assert (closed and edge_vert_global[0] == edge_vert_global[-1]) or not closed
                
                face_vert_global_map[edge_vert_local] = edge_vert_global
                if closed:
                    face_vert_global_map[last_vert] = face_vert_global_map[edge_vert_local[0]]
            
            else:
                #face_edges_data[edge_index] = {}   
                #face_edges_data[edge_index]['vert_indices_local'] = edge_vert_local
                #face_edges_data[edge_index]['vert_parameters'] = edge_param_local
                
                for i in (edge_vert_local + 1):
                    if face_vert_global_map[i - 1] == -1:
                        pnt = triangulation.Node(int(i))
                        pnt.Transform(transform)
                        pnt_array = np.array(pnt.Coord())
                        mesh_vertices.append(pnt_array)
                        face_vert_global_map[i - 1] = len(mesh_vertices) - 1
                
                if closed:
                    face_vert_global_map[last_vert] = face_vert_global_map[edge_vert_local[0]]
                
                edges_mesh_data[edge_index]['vert_indices'] = face_vert_global_map[edge_vert_local].tolist()
                edges_mesh_data[edge_index]['vert_parameters'] = edge_param_local.tolist()
                

            
            #print(face_vert_global_map)

        for i in range(1, number_vertices + 1):
            if face_vert_global_map[i - 1] == -1:
                pnt = triangulation.Node(i)
                pnt.Transform(transform)
                pnt_array = np.array(pnt.Coord())
                mesh_vertices.append(pnt_array)
                face_vert_global_map[i - 1] = len(mesh_vertices) - 1

            uv_node = triangulation.UVNode(i)
            face_vert_params.append(list(uv_node.Coord()))


        #print(face_vert_global_map)

        face_indices = []

        print(face_vert_global_map)

        number_faces = triangulation.NbTriangles()
        for i in range(1, number_faces + 1):
            i1, i2, i3 = triangulation.Triangle(i).Get()
            #print(i1, i2, i3)
            i1 = face_vert_global_map[i1 - 1]
            i2 = face_vert_global_map[i2 - 1]
            i3 = face_vert_global_map[i3 - 1]
            if i1 == i2 or i1 == i3 or i2 == i3:
                #WARNING
                print('ERROR: ignoring faces with repeated vertices (temporary solution)')
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
        
        #for edge_index, edge_data in face_edges_data.items():
        #    edges_mesh_data[edge_index]['vert_indices'] = face_vert_global_map[edge_data['vert_indices_local']].tolist()
        #    edges_mesh_data[edge_index]['vert_parameters'] = edge_data['vert_parameters'].tolist()

        print('--------------------------------------')
        print(len(mesh_vertices), number_vertices)
        unique_vert = np.arange(len(mesh_vertices))
        #print(unique_vert)
        unique_vert_faces = np.unique(np.asarray(mesh_faces))
        #print(unique_vert_faces)

        #print(unique_vert_faces)
        #print(unique_vert)

        assert np.all(unique_vert_faces == unique_vert), \
               f'ERROR: unreferenced vertices'
        
        faces_mesh_data[face_index] = {'vert_indices': face_vert_global_map.tolist(), 'vert_parameters': face_vert_params, 'face_indices': face_indices}

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