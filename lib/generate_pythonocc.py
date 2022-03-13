from OCC.Core.GeomAbs import GeomAbs_CurveType, GeomAbs_SurfaceType
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCC.Core.TopoDS import TopoDS_Face
from OCC.Extend.DataExchange import read_step_file
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh

from functools import reduce
from lib.features_factory import FeaturesFactory

from lib.tools import gpXYZ2List
from lib.generate_mesh_occ import registerFaceMeshInGlobalMesh
from lib.TopologyUtils import TopologyExplorer

from tqdm import tqdm
import numpy as np

MAX_INT = 2**31 - 1

def processEdgesHighestDim(edges, features: dict, edges_dict={}, use_tqdm=False):
    count = 0
    for edge in edges if not use_tqdm else tqdm(edges):
        edge_hc = edge.HashCode(MAX_INT)
        if edge_hc in edges_dict:
            edges_list = edges_dict[edge_hc]
            unique = True
            for f in edges_list:
                if edge.IsSame(f):
                    unique = False
                    break
            if not unique:
                continue
            else:
               edges_list.append(edge)  
        else:
            edges_dict[edge_hc] = [edge]

        curve = BRepAdaptor_Curve(edge)
        tp = str(GeomAbs_CurveType(curve.GetType())).split('_')[-1].lower()

        features['curves'].append(FeaturesFactory.getPrimitiveObject(type=tp, shape=curve, params=None))

        count += 1
    return count

def processFacesHighestDim(faces, topology, features: dict, faces_dict={}, mesh={}, mesh_generator='occ', use_tqdm=False):
    edges_dict = {}
    count = 0
    
    for face in faces if not use_tqdm else tqdm(faces):

        face_hc = face.HashCode(MAX_INT)
        if face_hc in faces_dict:
            faces_list = faces_dict[face_hc]
            unique = True
            for f in faces_list:
                if face.IsSame(f):
                    unique = False
                    break
            if not unique:
                continue
            else:
                faces_list.append(face) 
        else:
            faces_dict[face_hc] = [face]

        surface = BRepAdaptor_Surface(face, True)
        tp = str(GeomAbs_SurfaceType(surface.GetType())).split('_')[-1].lower()
        
        if mesh_generator == 'occ':
            mesh, mesh_params = registerFaceMeshInGlobalMesh(face, mesh)
            
            features['surfaces'].append(FeaturesFactory.getPrimitiveObject(type=tp, shape=surface, params=mesh_params))
        else:
            features['surfaces'].append(FeaturesFactory.getPrimitiveObject(type=tp, shape=surface, params=None))

        processEdgesHighestDim(topology.edges_from_face(face), features, edges_dict=edges_dict)

        count += 1

    return count

# Generate features by dimensions
def generateFeatureByDim(shape, features: dict, mesh = {}, mesh_generator='occ', use_highest_dim=True):
    print('\n[PythonOCC] Topology Exploration to Generate Features by Dimension')
    features['curves'] = []
    features['surfaces'] = []
    topology = TopologyExplorer(shape)

    if mesh_generator == 'occ':
        mesh['vertices'] = np.array([])
        mesh['faces'] = np.array([])
        mesh['vertices_hashcode'] = {}

        linear_deflection = 0.01
        isRelative = True
        angular_deflection = 0.1
        isInParallel = True

        brep_mesh = BRepMesh_IncrementalMesh(shape, linear_deflection, isRelative, angular_deflection, isInParallel)
        brep_mesh.SetShape(shape)
        brep_mesh.Perform()
        assert brep_mesh.IsDone()
    
    if use_highest_dim:
        print('\n[PythonOCC] Using Highest Dim Only, trying with Solids...')
        faces_dict = {}
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

    else:
        print('\n[PythonOCC] Using all the Shapes')
        for edge in tqdm(topology.edges()):
            curve = BRepAdaptor_Curve(edge)
            tp = str(GeomAbs_CurveType(curve.GetType())).split('_')[-1].lower()

            features['curve'].append(FeaturesFactory.getPrimitiveObject(type=tp, shape=curve))

        for face in tqdm(topology.faces()):
            surface = BRepAdaptor_Surface(face, True)
            tp = str(GeomAbs_SurfaceType(surface.GetType())).split('_')[-1].lower()

            if mesh_generator == 'occ':
                mesh, mesh_params = registerFaceMeshInGlobalMesh(face, mesh)
                
                features['surfaces'].append(FeaturesFactory.getPrimitiveObject(type=tp, shape=surface, params=mesh_params))
            else:
                features['surfaces'].append(FeaturesFactory.getPrimitiveObject(type=tp, shape=surface, params=None))

    if mesh_generator == 'occ':
        return mesh

# Main function
def processPythonOCC(input_name: str, mesh_generator, use_highest_dim=True, debug=True) -> dict:
    features = {}

    shape = read_step_file(input_name, verbosity=debug)

    if mesh_generator == 'occ':
        mesh = generateFeatureByDim(shape, features, mesh_generator=mesh_generator, use_highest_dim=use_highest_dim)
        return shape, features, mesh
    elif mesh_generator == 'gmsh':
        _ = generateFeatureByDim(shape, features, use_highest_dim=use_highest_dim)
        return shape, features, None
    else:
        raise Exception('Mesh Generator not available')