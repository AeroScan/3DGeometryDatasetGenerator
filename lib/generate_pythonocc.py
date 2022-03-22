from pyexpat import features
from OCC.Core.GeomAbs import GeomAbs_CurveType, GeomAbs_SurfaceType
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCC.Core.TopoDS import TopoDS_Face
from OCC.Extend.DataExchange import read_step_file
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.IMeshTools import IMeshTools_Parameters
from lib.features_factory import FeaturesFactory
from lib.generate_mesh_occ import registerEdgeMeshInGlobalMesh, registerFaceMeshInGlobalMesh
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

    mesh = {'vertices': [], 'faces': [], 'vertices_hcs': {}}
    edges_data = {}

    i = 0
    for edge in tqdm(edges):
        curve = BRepAdaptor_Curve(edge)
        tp = str(GeomAbs_CurveType(curve.GetType())).split('_')[-1].lower()

        if generate_mesh:
            hc = edge.HashCode(MAX_INT)
            edge_mesh_data = registerEdgeMeshInGlobalMesh(edge, mesh)
            edge_full_data = {'index': i, 'entity': edge, 'mesh_data': edge_mesh_data}
            if hc in edges_data:
                edges_data[hc].append(edge_full_data)
            else:
                edges_data[hc] = [edge_full_data]

        features['curves'].append(FeaturesFactory.getPrimitiveObject(type=tp, shape=curve, mesh={}))
        i += 1

    for face in tqdm(faces):
        surface = BRepAdaptor_Surface(face, True)
        tp = str(GeomAbs_SurfaceType(surface.GetType())).split('_')[-1].lower()

        face_mesh_data = {}
        if generate_mesh:
            face_mesh_data, edges_data = registerFaceMeshInGlobalMesh(face, mesh, topology.edges_from_face(face), edges_data)    

        features['surfaces'].append(FeaturesFactory.getPrimitiveObject(type=tp, shape=surface, mesh=face_mesh_data))

    for key in edges_data:
        for i in range(len(edges_data[key])):
            if features['curves'][edges_data[key][i]['index']] is not None:
                features['curves'][edges_data[key][i]['index']].fromMesh(edges_data[key][i]['mesh_data'])

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
        print('\n[PythonOCC] Mesh Generation')
        mesh = {}
        mesh['vertices'] = []
        mesh['faces'] = []

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