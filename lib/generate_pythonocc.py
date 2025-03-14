from tqdm import tqdm
import numpy as np

from OCC.Extend.DataExchange import read_step_file
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.gp import gp_Trsf
import OCC.Core.ShapeFix as ShapeFix

from lib.generate_mesh_occ import OCCMeshGeneration, computeMeshData
from asGeometryOCCWrapper import CurveFactory, SurfaceFactory

MAX_INT = 2**31 - 1

def searchEntityByHashCode(entity, hash_code, dictionary):
    search_code = 0 # 0: not_found; 1: not_found_but_hashcode_exists; 2: found
    if hash_code in dictionary:
        search_code = 1
        entities_list = dictionary[hash_code]
        for f in entities_list:
            if entity.IsSame(f):
                search_code = 2
                break
    return search_code

def updateEntitiesDictBySearchCode(entity, hash_code, search_code, dictionary):
    if search_code == 0:
        dictionary[hash_code] = [entity]
    elif search_code == 1:
        dictionary[hash_code].append(entity) 
    return dictionary

def processEdgesAndFaces(vertices, edges, faces, topology, generate_mesh):
    mesh = {}
    edges_mesh_data = [{} for _ in edges]
    faces_mesh_data = [{} for _ in faces]        
    if generate_mesh:
        mesh['vertices'], mesh['faces'], edges_mesh_data, faces_mesh_data = computeMeshData(vertices, edges, faces, topology)

    geometries_data = {'curves': [], 'surfaces': []}
    for i in range(len(edges)):
        geometry = CurveFactory.fromTopoDS(edges[i])
        if geometry is not None:
            geometries_data['curves'].append({'geometry': geometry, 'mesh_data': edges_mesh_data[i]})
    for i in range(len(faces)):
        geometry = SurfaceFactory.fromTopoDS(faces[i])
        if geometry is not None:
            geometries_data['surfaces'].append({'geometry': geometry, 'mesh_data': faces_mesh_data[i]})

    return geometries_data, mesh

# def addEdgesToDict(edges, edges_dict):
#     for edge in edges:
#         edge_hc = edge.HashCode(MAX_INT)
#         search_code = searchEntityByHashCode(edge, edge_hc, edges_dict)
#         if search_code == 2:
#             continue
#         else:
#             edges_dict = updateEntitiesDictBySearchCode(edge, edge_hc, search_code, edges_dict)
#     return edges_dict

def addVerticesToDict(vertices, vertices_dict):
    for vertex in vertices:
        vertex_hc = vertex.HashCode(MAX_INT)
        search_code = searchEntityByHashCode(vertex, vertex_hc, vertices_dict)
        if search_code == 2:
            continue
        else:
            vertices_dict = updateEntitiesDictBySearchCode(vertex, vertex_hc, search_code, vertices_dict)
    return vertices_dict

def addEdgesAndAssociatedVerticesToDict(edges, topology, edges_dict, vertices_dict):
    for edge in edges:
        edge_hc = edge.HashCode(MAX_INT)
        search_code = searchEntityByHashCode(edge, edge_hc, edges_dict)
        if search_code == 2:
            continue
        else:
            vertices_dict = addVerticesToDict(topology.vertices_from_edge(edge), vertices_dict)
            edges_dict = updateEntitiesDictBySearchCode(edge, edge_hc, search_code, edges_dict)
   
    return edges_dict, vertices_dict

def addFacesAndAssociatedEdgesToDict(faces, topology, faces_dict, edges_dict, vertices_dict):
    for face in faces:
        face_hc = face.HashCode(MAX_INT)
        search_code = searchEntityByHashCode(face, face_hc, faces_dict)
        if search_code == 2:
            continue
        else:
            edges_dict, vertices_dict = addEdgesAndAssociatedVerticesToDict(topology.edges_from_face(face), edges_dict)
            faces_dict = updateEntitiesDictBySearchCode(face, face_hc, search_code, faces_dict)
   
    return faces_dict, edges_dict, vertices_dict

def processHighestDim(topology, generate_mesh):
    print('\n[PythonOCC] Using Highest Dim Only, trying with Solids...')
    faces_dict = {}
    edges_dict = {}

    done = False
    for solid in tqdm(topology.solids()):
        faces_dict, edges_dict, vertices_dict = addFacesAndAssociatedEdgesToDict(topology.faces_from_solids(solid), topology, faces_dict, edges_dict)   
        done = True

    if not done:
        print('\n[PythonOCC] There are no Solids, using Faces as highest dim...')
        faces_dict, edges_dict, vertices_dict = addFacesAndAssociatedEdgesToDict(topology.faces(), topology, faces_dict, edges_dict)
        done = (faces_dict != {})

        if not done == 0:
            print('\n[PythonOCC] There are no Faces, using Curves as highest dim...')
            edges_dict, vertices_dict = addEdgesAndAssociatedVerticesToDict(topology.edges(), edges_dict) 
            done = (edges_dict != {})

            if not done == 0:
                print('\n[PythonOCC] There are no Entities to use...')
    
    vertices = []
    for key in vertices_dict:
        vertices += vertices_dict[key]

    edges= []
    for key in edges_dict:
        edges += edges_dict[key]

    faces = []
    for key in faces_dict:
        faces += faces_dict[key]

    geometries_data, mesh = processEdgesAndFaces(vertices, edges, faces, topology, generate_mesh)

    return geometries_data, mesh
    

def processNoHighestDim(topology, generate_mesh):
    print('\n[PythonOCC] Using all the Shapes')

    vertices = [v for v in topology.vertices()]
    edges = [e for e in topology.edges()]
    faces = [f for f in topology.faces()]

    geometries_data, mesh = processEdgesAndFaces(vertices, edges, faces, topology, generate_mesh)

    return geometries_data, mesh

# Generate features by dimensions
def process(shape, generate_mesh=True, use_highest_dim=True):
    print('\n[PythonOCC] Topology Exploration to Generate Features by Dimension')

    topology = TopologyExplorer(shape)

    if generate_mesh:
        OCCMeshGeneration(shape)
    
    mesh = {}
    
    if use_highest_dim:
        geometries_data, mesh = processHighestDim(topology, generate_mesh)
    else:
        geometries_data, mesh = processNoHighestDim(topology, generate_mesh)

    if mesh != {}:
        mesh['vertices'] = np.asarray(mesh['vertices'])
        mesh['faces'] = np.asarray(mesh['faces'])
    
    return geometries_data, mesh

def processPythonOCC(input_name: str, generate_mesh=True, use_highest_dim=True, scale_to_mm=1, debug=False) -> dict:
    shape = read_step_file(input_name, verbosity=debug)

    scaling_transformation = gp_Trsf()
    scaling_transformation.SetScaleFactor(scale_to_mm)
    transform_builder = BRepBuilderAPI_Transform(shape, scaling_transformation)

    shape = transform_builder.Shape()

    healer = ShapeFix.ShapeFix_Shape(shape)
    healer.Perform()
    shape = healer.Shape()

    # extend_status = ShapeExtend_Status()
    # healer.Status(extend_status)

    # if extend_status == ShapeExtend_Status.ShapeExtend_OK:
    #     print("Shape healing successful.")
    # else:
    #     print("Shape healing failed.")

    geometries_data, mesh = process(shape, generate_mesh=generate_mesh, use_highest_dim=use_highest_dim)
    
    return shape, geometries_data, mesh