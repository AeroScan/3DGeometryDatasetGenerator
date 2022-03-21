from OCC.Core.GeomAbs import GeomAbs_CurveType, GeomAbs_SurfaceType
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCC.Core.TopoDS import TopoDS_Face
from OCC.Extend.DataExchange import read_step_file
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.IMeshTools import IMeshTools_Parameters
from lib.features_factory import FeaturesFactory
from lib.tools import searchEntityByHashCode, updateEntitiesDictBySearchCode
from lib.generate_mesh_occ import registerEdgeMeshInGlobalMesh, registerFaceMeshInGlobalMesh
from lib.TopologyUtils import TopologyExplorer

from tqdm import tqdm
import numpy as np

MAX_INT = 2**31 - 1

def processEdgesHighestDim(edges, features: dict, edges_dict={}, use_tqdm=False):
    count = 0
    for edge in edges if not use_tqdm else tqdm(edges):
        edge_hc = edge.HashCode(MAX_INT)
        search_code = searchEntityByHashCode(edge, edge_hc, edges_dict)
        if search_code == 2:
            continue
        else:
            edges_dict = updateEntitiesDictBySearchCode(edge, edge_hc, search_code, edges_dict)

        curve = BRepAdaptor_Curve(edge)
        tp = str(GeomAbs_CurveType(curve.GetType())).split('_')[-1].lower()

        # Change the mesh value to mesh_params when processing curves
        features['curves'].append(FeaturesFactory.getPrimitiveObject(type=tp, shape=curve, mesh={}))

        count += 1
    return count

def processFacesHighestDim(faces, topology, features: dict, faces_dict={}, mesh={}, mesh_generator='occ', use_tqdm=False):
    edges_dict = {}
    count = 0
    
    for face in faces if not use_tqdm else tqdm(faces):
        face_hc = face.HashCode(MAX_INT)
        search_code = searchEntityByHashCode(face, face_hc, faces_dict)
        if search_code == 2:
            continue
        else:
            faces_dict = updateEntitiesDictBySearchCode(face, face_hc, search_code, faces_dict)

        surface = BRepAdaptor_Surface(face, True)
        tp = str(GeomAbs_SurfaceType(surface.GetType())).split('_')[-1].lower()
        
        if mesh_generator == 'occ':
            mesh, mesh_params = registerFaceMeshInGlobalMesh(face, mesh)
            
            features['surfaces'].append(FeaturesFactory.getPrimitiveObject(type=tp, shape=surface, mesh=mesh_params))
        else:
            features['surfaces'].append(FeaturesFactory.getPrimitiveObject(type=tp, shape=surface, mesh=None))

        processEdgesHighestDim(topology.edges_from_face(face), features, edges_dict=edges_dict)

        count += 1

    return count

def processHighestDim(faces, topology, features: dict, faces_dict={}, mesh={}, mesh_generator='occ', use_tqdm=False):
    print('\n[PythonOCC] Using Highest Dim Only, trying with Solids...')
    count_solids = 0
    for solid in tqdm(topology.solids()):
        processFacesHighestDim(topology.faces_from_solids(solid), topology, features, mesh=mesh, mesh_generator=mesh_generator, faces_dict=faces_dict)   
        count_solids += 1

    if count_solids == 0:
        print('\n[PythonOCC] There are no Solids, using Faces as highest dim...')
        count_faces = processFacesHighestDim(topology.faces(), topology, features, mesh=mesh, mesh_generator=mesh_generator, use_tqdm=True)

        if count_faces == 0:
            print('\n[PythonOCC] There are no Faces, using Curves as highest dim...')
            count_edges = processFacesHighestDim(topology.edges(), features, mesh_generator=mesh_generator, use_tqdm=True) 

            if count_edges == 0:
                print('\n[PythonOCC] There are no Curves to use...')

def processNoHighestDim(topology, generate_mesh):
    print('\n[PythonOCC] Using all the Shapes')
    features = {}
    features['curves'] = []
    features['surfaces'] = []

    mesh = {'vertices': [], 'faces': [], 'vertices_hcs': {}}
    edges_data = {}

    i = 0
    for edge in tqdm(topology.edges()):
        curve = BRepAdaptor_Curve(edge)
        tp = str(GeomAbs_CurveType(curve.GetType())).split('_')[-1].lower()

        edge_mesh_data = {}
        if generate_mesh:
            hc = edge.HashCode(MAX_INT)
            edge_mesh_data = registerEdgeMeshInGlobalMesh(edge, mesh)
            edge_full_data = {'index': i, 'entity': edge, 'mesh_data': edge_mesh_data}
            if hc in edges_data:
                edges_data[hc].append(edge_full_data)
            else:
                edges_data[hc] = [edge_full_data]

        features['curves'].append(FeaturesFactory.getPrimitiveObject(type=tp, shape=curve, mesh=edge_mesh_data))
        i += 1

    for face in tqdm(topology.faces()):
        surface = BRepAdaptor_Surface(face, True)
        tp = str(GeomAbs_SurfaceType(surface.GetType())).split('_')[-1].lower()

        face_mesh_data = {}
        if generate_mesh:
            face_mesh_data, out_edges_data = registerFaceMeshInGlobalMesh(face, mesh, topology.edges_from_face(face), edges_data)    
            for key in out_edges_data:
                for i in range(len(out_edges_data[key])):
                    edges_data[key][out_edges_data[key][i]['hc_list_index']]['mesh_data'] = out_edges_data[key][i]['mesh_data']
                    if features['curves'][out_edges_data[key][i]['index']] is not None:
                        features['curves'][out_edges_data[key][i]['index']].fromMesh(out_edges_data[key][i]['mesh_data'])

        features['surfaces'].append(FeaturesFactory.getPrimitiveObject(type=tp, shape=surface, mesh=face_mesh_data))

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
            pass
            #features, mesh = processHighestDim(topology, generate_mesh)
        else:
            features, mesh = processNoHighestDim(topology, generate_mesh)

        if mesh is not {}:
            mesh['vertices'] = np.asarray(mesh['vertices'])
            mesh['faces'] = np.asarray(mesh['faces'])

    else:
        if use_highest_dim:
            pass
            #features, mesh = processHighestDim(topology, generate_mesh)
        else:
            features, mesh = processNoHighestDim(topology, generate_mesh)

    
    return features, mesh

def processPythonOCC(input_name: str, generate_mesh=True, use_highest_dim=True, debug=True) -> dict:
    shape = read_step_file(input_name, verbosity=debug)

    features, mesh = process(shape, generate_mesh=generate_mesh, use_highest_dim=use_highest_dim)
    
    return shape, features, mesh













''''


'''