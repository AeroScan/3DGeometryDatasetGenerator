from tkinter.tix import MAX
from tqdm import tqdm
import numpy as np

from OCC.Extend.DataExchange import read_step_file, read_step_file_with_names_colors
from OCC.Extend.TopologyUtils import TopologyExplorer, list_of_shapes_to_compound
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Common
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Compound
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.TopoDS import TopoDS_Face

from lib.generate_mesh_occ import OCCMeshGeneration, computeMeshData, searchEntityInMap
from lib.tools import heal_shape, load_file_with_semantic_data, writeJSON, writeYAML
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
        mesh['vertices'], mesh['faces'], edges_mesh_data, faces_mesh_data, faces_map = computeMeshData(vertices, edges, faces, topology)

    geometries_data = {'curves': [], 'surfaces': []}
    for i in range(len(edges)):
        geometry = CurveFactory.fromTopoDS(edges[i])
        if geometry is not None:
            geometries_data['curves'].append({'geometry': geometry, 'mesh_data': edges_mesh_data[i]})
    for i in range(len(faces)):
        geometry = SurfaceFactory.fromTopoDS(faces[i])
        if geometry is not None:
            geometries_data['surfaces'].append({'geometry': geometry, 'mesh_data': faces_mesh_data[i]})

    return geometries_data, mesh, faces_mesh_data, faces_map

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

    geometries_data, mesh, _, _ = processEdgesAndFaces(vertices, edges, faces, topology, generate_mesh)

    return geometries_data, mesh
    

def processNoHighestDim(topology, generate_mesh):
    print('\n[PythonOCC] Using all the Shapes')

    vertices = [v for v in topology.vertices()]
    edges = [e for e in topology.edges()]
    faces = [f for f in topology.faces()]
    print(f"FACES: {len(faces)}")
    # exit()
    geometries_data, mesh, faces_mesh_data, faces_map = processEdgesAndFaces(vertices, edges, faces, topology, generate_mesh)

    return geometries_data, mesh, faces_mesh_data, faces_map

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
        geometries_data, mesh, faces_mesh_data, faces_map = processNoHighestDim(topology, generate_mesh)

    if mesh != {}:
        mesh['vertices'] = np.asarray(mesh['vertices'])
        mesh['faces'] = np.asarray(mesh['faces'])
    
    return geometries_data, mesh, faces_mesh_data, faces_map


def find_corresponding_face(original_face, target_shape):
    # Use the geometric properties to find the corresponding face in the target shape
    original_surface = BRep_Tool.Surface(original_face)
    
    explorer = TopExp_Explorer(target_shape, TopAbs_FACE)
    while explorer.More():
        target_face = topods_Face(explorer.Current())
        target_surface = BRep_Tool.Surface(target_face)
        
        # Compare the geometric properties, adjust the comparison criteria as needed
        if original_surface.IsEqual(target_surface, 1e-6):  # Adjust tolerance as needed
            return target_face
        
        explorer.Next()
    
    return None  # No corresponding face found

def processPythonOCC(input_name: str, generate_mesh=True, use_highest_dim=True, scale_to_mm=1, debug=False, generate_semantic: bool = True, labels: list = ["tank", "pipe", "silo", "instrumentation", "floor", "wall", "structure"], semantic_name: str = './semantic'):
    shape = None
    shape_filtered = None
    semantic_data = []
    
    if generate_semantic: # To change by a new parameter
        if not labels:
            print("No labels found. Using default names from the file.")

        """ Read step file with names """
        output = {}
        output = read_step_file_with_names_colors(input_name)
        
        list_of_shapes = []
        for shp, name_color_list in output.items():
            shape = shp
            name = name_color_list[0]
            color = name_color_list[1]

            list_of_shapes.append(shape)

            if labels:
                if name.lower() in labels:
                    semantic_data.append((name, shape))
            else:
                if name:
                    semantic_data.append((name, shape))
        shape_with_name, result = list_of_shapes_to_compound(list_of_shapes)
        shape = shape_with_name
        # shape_without_name      = read_step_file(input_name, as_compound=True)

        # topology_with_name    = TopologyExplorer(shape_with_name)
        # topology_without_name = TopologyExplorer(shape_without_name)

        # number_of_faces_with_names    = topology_with_name.number_of_faces()
        # number_of_faces_without_names = topology_without_name.number_of_faces()

        # print(f"number of faces with names: {number_of_faces_with_names}")
        # print(f"number of faces without names: {number_of_faces_without_names}")

        # print("Generating compound with BRepAlgoAPI_Common...")
        # shape_filtered = BRepAlgoAPI_Common(shape_with_name, shape_without_name).Shape()
        # topology_filtered = TopologyExplorer(shape_filtered)
        
        # number_of_faces_filtered = topology_filtered.number_of_faces()
        # print(f"number of faces filtered: {number_of_faces_filtered}")
        
        # for face_with_name in topology_with_name.faces():
        #     is_face_in_filtered = any(face_with_name.IsSame(face_filtered) for face_filtered in topology_filtered.faces())
        #     if is_face_in_filtered:
        #         print("There one")

        # exit()

        if not result:
            print("Warning: all shapes were not added to the compound") # TODO: check this warning
    else:
        shape = read_step_file(input_name, verbosity=debug)
        shape = heal_shape(shape, scale_to_mm)
        # top_healed = TopologyExplorer(shape)
        # faces_healed = [f for f in tqdm(top_healed.faces())] # 744 faces

    geometries_data, mesh, faces_mesh_data, faces_map_mesh = process(shape, generate_mesh=generate_mesh, use_highest_dim=use_highest_dim)

    if semantic_data and faces_mesh_data:
        print("Processing semantic data...")
        semantic_data_dict = {}
        semantic_data_dict["semantic"] = []
        faces_with_labels = []
        face_counter = 0

        for produto in semantic_data:
            """ produto list:
            ('Tank', <class 'TopoDS_Compound'>)
            ('Pipe', <class 'TopoDS_Solid'>)
            ('Pipe', <class 'TopoDS_Solid'>)
            ('Valve', <class 'TopoDS_Compound'>)
            ('Valve', <class 'TopoDS_Compound'>)
            """
            _name, _shape = produto
            topology = TopologyExplorer(_shape)
            faces = [f for f in tqdm(topology.faces())] # 744 faces
            """faces list:
            <class 'TopoDS_Face'>, <class 'TopoDS_Face'>, <class 'TopoDS_Face'>, ...
            """
            vert_indices = []
            vert_parameters = []
            face_indices = []
            for face in faces:

                face_index = searchEntityInMap(face, faces_map_mesh)

                if face_index == -1:
                    print("Warning: Face do not found in mesh!") # TODO: Check this
                    continue
                face_counter += len(faces_mesh_data[face_index]["face_indices"])
                faces_with_labels.append(face_index)

                vert_indices += faces_mesh_data[face_index]["vert_indices"]
                vert_parameters += faces_mesh_data[face_index]["vert_parameters"]
                face_indices += faces_mesh_data[face_index]["face_indices"]
            semantic_data_dict["semantic"].append(
                {
                    "label": _name,
                    "vert_indices": np.unique(np.asarray(vert_indices)).tolist(),
                    "vert_parameters": np.unique(np.asarray(vert_parameters)).tolist(),
                    "face_indices": np.unique(np.asarray(face_indices)).tolist(),
                }
            )

        # print(f"COUNTER_FACES: {face_counter}")
        # face_counter = 0
        # topology = TopologyExplorer(shape)
        # faces = [f for f in topology.faces()] # 1531
        # print(f">> FACES_OUT: {len(faces)}")

        # count = 0
        # vert_indices = []
        # vert_parameters = []
        # face_indices = []
        # for face in faces:
        #     face_index = searchEntityInMap(face, faces_map_mesh)

        #     if face_index == -1:
        #         print("WARNING HERE")

        #     if face_index not in faces_with_labels:
        #         count += 1
        #         face_counter += len(faces_mesh_data[face_index]["face_indices"])

        #         vert_indices += faces_mesh_data[face_index]["vert_indices"]
        #         vert_parameters += faces_mesh_data[face_index]["vert_parameters"]
        #         face_indices += faces_mesh_data[face_index]["face_indices"]
    
        # semantic_data_dict["semantic"].append(
        #     {
        #         "label": "unlabeled",
        #         "vert_indices": np.unique(np.asarray(vert_indices)).tolist(),
        #         "vert_parameters": np.unique(np.asarray(vert_parameters)).tolist(),
        #         "face_indices": np.unique(np.asarray(face_indices)).tolist()
        #     }
        # )
        # print(f">> semantic list: {len(semantic_data_dict['semantic'])}")
        # print(f"COUNTER_FACES: {face_counter}")

        writeJSON(semantic_name, semantic_data_dict)
        print("Done.\n")
    
    return shape, geometries_data, mesh