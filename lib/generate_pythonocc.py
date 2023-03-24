from OCC.Core.GeomAbs import GeomAbs_CurveType, GeomAbs_SurfaceType
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCC.Core.TopoDS import TopoDS_Face
from OCC.Extend.DataExchange import read_step_file
from OCC.Extend.TopologyUtils import TopologyExplorer
from lib.features_factory import FeaturesFactory
from lib.generate_mesh_occ import OCCMeshGeneration, computeMeshData
from lib.TopologyUtils import TopologyExplorer

from tqdm import tqdm
import numpy as np

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

def processEdgesAndFaces(edges, faces, topology, generate_mesh):
    features = {}
    features['curves'] = []
    features['surfaces'] = []

    mesh = {}
    edges_mesh_data = [{} for x in edges]
    faces_mesh_data = [{} for x in faces]

    if generate_mesh:
        mesh['vertices'], mesh['faces'], edges_mesh_data, faces_mesh_data = computeMeshData(edges, faces, topology)
    
    print('\n[PythonOCC] Generating Features...')
    for i, edge in enumerate(tqdm(edges)):
        curve = BRepAdaptor_Curve(edge)
        tp = str(GeomAbs_CurveType(curve.GetType())).split('_')[-1].lower()

        features['curves'].append(FeaturesFactory.getPrimitiveObject(tp, shape=curve, mesh=edges_mesh_data[i]))

    for i, face in enumerate(tqdm(faces)):
        surface = BRepAdaptor_Surface(face, True)
        tp = str(GeomAbs_SurfaceType(surface.GetType())).split('_')[-1].lower()
        
        features['surfaces'].append(FeaturesFactory.getPrimitiveObject(tp, shape=surface, mesh=faces_mesh_data[i]))

    return features, mesh

def addEdgesToDict(edges, edges_dict):
    for edge in edges:
        edge_hc = edge.HashCode(MAX_INT)
        search_code = searchEntityByHashCode(edge, edge_hc, edges_dict)
        if search_code == 2:
            continue
        else:
            edges_dict = updateEntitiesDictBySearchCode(edge, edge_hc, search_code, edges_dict)
    return edges_dict

def addFacesAndAssociatedEdgesToDict(faces, topology, faces_dict, edges_dict):
    for face in faces:
        face_hc = face.HashCode(MAX_INT)
        search_code = searchEntityByHashCode(face, face_hc, faces_dict)
        if search_code == 2:
            continue
        else:
            edges_dict = addEdgesToDict(topology.edges_from_face(face), edges_dict)
            faces_dict = updateEntitiesDictBySearchCode(face, face_hc, search_code, faces_dict)
   
    return faces_dict, edges_dict

def processHighestDim(topology, generate_mesh):
    print('\n[PythonOCC] Using Highest Dim Only, trying with Solids...')
    faces_dict = {}
    edges_dict = {}

    done = False
    for solid in tqdm(topology.solids()):
        faces_dict, edges_dict = addFacesAndAssociatedEdgesToDict(topology.faces_from_solids(solid), topology, faces_dict, edges_dict)   
        done = True

    if not done:
        print('\n[PythonOCC] There are no Solids, using Faces as highest dim...')
        faces_dict, edges_dict = addFacesAndAssociatedEdgesToDict(topology.faces(), topology, faces_dict, edges_dict)
        done = (faces_dict != {})

        if not done == 0:
            print('\n[PythonOCC] There are no Faces, using Curves as highest dim...')
            edges_dict = addEdgesToDict(topology.edges(), edges_dict) 
            done = (edges_dict != {})

            if not done == 0:
                print('\n[PythonOCC] There are no Entities to use...')

    edges= []
    for key in edges_dict:
        edges += edges_dict[key]

    faces = []
    for key in faces_dict:
        faces += faces_dict[key]

    features, mesh = processEdgesAndFaces(edges, faces, topology, generate_mesh)

    return features, mesh
    

def processNoHighestDim(topology, generate_mesh):
    print('\n[PythonOCC] Using all the Shapes')

    edges = [e for e in topology.edges()]
    faces = [f for f in topology.faces()]

    features, mesh = processEdgesAndFaces(edges, faces, topology, generate_mesh)

    return features, mesh

# Generate features by dimensions
def process(shape, generate_mesh=True, use_highest_dim=True):
    print('\n[PythonOCC] Topology Exploration to Generate Features by Dimension')

    topology = TopologyExplorer(shape)

    if generate_mesh:
        OCCMeshGeneration(shape)
    
    mesh = {}
    
    if use_highest_dim:
        features, mesh = processHighestDim(topology, generate_mesh)
    else:
        features, mesh = processNoHighestDim(topology, generate_mesh)

    if mesh != {}:
        mesh['vertices'] = np.asarray(mesh['vertices'])
        mesh['faces'] = np.asarray(mesh['faces'])
    
    return features, mesh

def processPythonOCC(input_name: str, generate_mesh=True, use_highest_dim=True, debug=True) -> dict:
    shape = read_step_file(input_name, verbosity=debug)

    features, mesh = process(shape, generate_mesh=generate_mesh, use_highest_dim=use_highest_dim)
    
    return shape, features, mesh