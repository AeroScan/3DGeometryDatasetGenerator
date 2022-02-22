from OCC.Core.GeomAbs import GeomAbs_CurveType, GeomAbs_SurfaceType
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCC.Core.TopoDS import TopoDS_Face
from OCC.Extend.DataExchange import read_step_file
from TopologyUtils import TopologyExplorer
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh

from functools import reduce

from tools import gpXYZ2List

from tqdm import tqdm
import numpy as np

MAX_INT = 2**31 - 1

POSSIBLE_CURVE_TYPES = ['line', 'circle', 'ellipse']
POSSIBLE_SURFACE_TYPES = ['plane', 'cylinder', 'cone', 'sphere', 'torus']

# Generate lines information
def generateLineFeature(shape, face_indices=[]) -> dict:
    shape = shape.Line()

    feature = {
        'type': 'Line',
        'location': gpXYZ2List(shape.Location()),
        'direction': gpXYZ2List(shape.Direction()),
    }

    return {**feature}

# Generate circles information
def generateCircleFeature(shape, face_indices=[]) -> dict:
    shape = shape.Circle()

    feature = {
        'type': 'Circle',
        'location': gpXYZ2List(shape.Location()),
        'z_axis': gpXYZ2List(shape.Axis().Direction()),
        'radius': shape.Radius(),
        'x_axis': gpXYZ2List(shape.XAxis().Direction()),
        'y_axis': gpXYZ2List(shape.YAxis().Direction()),
    }

    if feature['radius'] == 0:
        return None
    else:
        return {**feature}

# Generate ellipses information
def generateEllipseFeature(shape, face_indices=[]) -> dict:
    shape = shape.Ellipse()

    feature = {
        'type': 'Ellipse',
        'focus1': gpXYZ2List(shape.Focus1()),
        'focus2': gpXYZ2List(shape.Focus2()),
        'x_axis': gpXYZ2List(shape.XAxis().Direction()),
        'y_axis': gpXYZ2List(shape.YAxis().Direction()),
        'z_axis': gpXYZ2List(shape.Axis().Direction()),
        'x_radius': shape.MajorRadius(),
        'y_radius': shape.MinorRadius(),
    }

    if feature['x_radius'] == 0 or feature['y_radius'] == 0:
        return None
    else:
        return {**feature}

# Generate planes information
def generatePlaneFeature(shape, face_indices=[]) -> dict:
    shape = shape.Plane()

    f1 = {
        'type': 'Plane',
        'location': gpXYZ2List(shape.Location()),
        'normal': gpXYZ2List(shape.Axis().Direction()),
        'x_axis': gpXYZ2List(shape.XAxis().Direction()),
        'y_axis': gpXYZ2List(shape.YAxis().Direction()),
        'z_axis': gpXYZ2List(shape.Axis().Direction()),
        'coefficients': list(shape.Coefficients()),
    }

    if face_indices:
        f2 = {
            'face_indices': face_indices,
        }

        feature = {**f1, **f2}

        return {**feature}
    else:
        return {**f1}


# Generate cylinders information
def generateCylinderFeature(shape, face_indices=[]) -> dict:
    shape = shape.Cylinder()

    f1 = {
        'type': 'Cylinder',
        'location': gpXYZ2List(shape.Location()),
        'x_axis': gpXYZ2List(shape.XAxis().Direction()),
        'y_axis': gpXYZ2List(shape.YAxis().Direction()),
        'z_axis': gpXYZ2List(shape.Axis().Direction()),
        'coefficients': list(shape.Coefficients()),
        'radius': shape.Radius(),
    }

    if face_indices:
        f2 = {
            'face_indices': face_indices,
        }

        feature = {**f1, **f2}

        if feature['radius'] == 0:
            return None
        else:
            return {**feature}
    else:
        if f1['radius'] == 0:
            return None
        else:
            return {**f1}

# Generate cones information
def generateConeFeature(shape, face_indices=[]) -> dict:
    shape = shape.Cone()

    f1 = {
        'type': 'Cone',
        'location': gpXYZ2List(shape.Location()),
        'x_axis': gpXYZ2List(shape.XAxis().Direction()),
        'y_axis': gpXYZ2List(shape.YAxis().Direction()),
        'z_axis': gpXYZ2List(shape.Axis().Direction()),
        'coefficients': list(shape.Coefficients()),
        'radius': shape.RefRadius(),
        'angle': shape.SemiAngle(),
        'apex': gpXYZ2List(shape.Apex()),
    }

    if face_indices:
        f2 = {
            'face_indices': face_indices,
        }

        feature = {**f1, **f2}

        if feature['radius'] == 0:
            return None
        else:
            return {**feature}
    else:
        if f1['radius'] == 0:
            return None
        else:
            return {**f1}

# Generate spheres information
def generateSphereFeature(shape, face_indices=[]) -> dict:
    shape = shape.Sphere()

    x_axis = np.array(gpXYZ2List(shape.XAxis().Direction()))
    y_axis = np.array(gpXYZ2List(shape.YAxis().Direction()))
    z_axis = np.cross(x_axis, y_axis)

    f1 = {
        'type': 'Sphere',
        'location': gpXYZ2List(shape.Location()),
        'x_axis': x_axis.tolist(),
        'y_axis': y_axis.tolist(),
        'z_axis': z_axis.tolist(),
        'coefficients': list(shape.Coefficients()),
        'radius': shape.Radius(),
    }

    if face_indices:
        f2 = {
            'face_indices': face_indices,
        }

        feature = {**f1, **f2}

        if feature['radius'] == 0:
            return None
        else:
            return {**feature}
    else:
        if f1['radius'] == 0:
            return None
        else:
            return {**f1}

# Generate torus information
def generateTorusFeature(shape, face_indices=[]) -> dict:
    shape = shape.Torus()

    f1 = {
        'type': 'Torus',
        'location': gpXYZ2List(shape.Location()),
        'x_axis': gpXYZ2List(shape.XAxis().Direction()),
        'y_axis': gpXYZ2List(shape.YAxis().Direction()),
        'z_axis': gpXYZ2List(shape.Axis().Direction()),
        # 'coefficients': list(shape.Coefficients()),
        'max_radius': shape.MajorRadius(),
        'min_radius': shape.MinorRadius(),
    }

    if face_indices:
        f2 = {
            'face_indices': face_indices,
        }

        feature = {**f1, **f2}

        if feature['max_radius'] == 0 or feature['min_radius'] == 0:
            return None
        else:
            return {**feature}
    else:
        if f1['max_radius'] == 0 or f1['min_radius'] == 0:
            return None
        else:
            return {**f1}

# Call function by type
def generateFeature(type: str, shape, face_indices=[]):
    generate_functions_dict = {
        'line': generateLineFeature,
        'circle': generateCircleFeature,
        'ellipse': generateEllipseFeature,
        'plane': generatePlaneFeature,
        'cylinder': generateCylinderFeature,
        'cone': generateConeFeature,
        'sphere': generateSphereFeature,
        'torus': generateTorusFeature,
    }
    if type.lower() in generate_functions_dict.keys():
        return generate_functions_dict[type.lower()](shape, face_indices=face_indices)

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

        if tp in POSSIBLE_CURVE_TYPES:
            feature = generateFeature(type=tp, shape=curve)
            features['curves'].append(feature)
        else:
            features['curves'].append(None)
        count += 1
    return count

def _process_face(face, vert_index, face_index):

    face_orientation_wrt_surface_normal = face.Orientation()

    brep_tool = BRep_Tool()
    location = TopLoc_Location()
    mesh = brep_tool.Triangulation(face, location)
    faces = {}
    verts = []
    triangle = []
    if mesh != None:
        
        num_vertices = mesh.NbNodes()
        for i in range(1, num_vertices + 1):
            verts.append(list(mesh.Node(i).Coord()))        
        verts = np.array(verts)

        num_tris = mesh.NbTriangles()
        for i in range(1, num_tris + 1):
            index1, index2, index3 = mesh.Triangle(i).Get()
            if face_orientation_wrt_surface_normal == 0:
             triangle.append([vert_index + index1 - 1, vert_index + index2 - 1, vert_index + index3 - 1])
            elif face_orientation_wrt_surface_normal == 1:
             triangle.append([vert_index + index3 - 1, vert_index + index2 - 1, vert_index + index1 - 1])
            else:
                print("Broken face orientation", face_orientation_wrt_surface_normal)

        for face in triangle:
            faces[str(face_index)] = face
            face_index += 1

    return verts, triangle, faces, face_index


def processFacesHighestDim(faces, topology, features: dict, meshes, no_use_gmsh, vertex_counter, faces_dict={}, use_tqdm=False):
    edges_dict = {}
    count = 0

    # *** Setup para geração da mesh com PythonOCC *** #
    if no_use_gmsh:
        FIRST_FACE_INDEX = 0
        FIRST_VERT_INDEX = 0
        face_index = FIRST_FACE_INDEX
        fake_index = 0
    # *** Setup para geração da mesh com PythonOCC *** #
    
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
        
        # *** Generate mesh with OCC *** #
        face_indices = []
        if no_use_gmsh:
            # fake_index seria o index da surface, e não face do triangulo
            try:
                verts, triangles, tri_faces_dict, face_index = _process_face(face, vert_index=vertex_counter, face_index=face_index)

                for index in tri_faces_dict.keys():
                    face_indices.append(int(index))
                meshes.append({"vertices": np.array(verts), "faces": np.array(triangles)})
            except Exception as e:
                meshes.append({"vertices": np.array([]), "faces": np.array([])})
                continue

            fake_index += 1
            vertex_counter += len(verts)
        # *** Generate mesh with OCC *** #

        surface = BRepAdaptor_Surface(face, True)
        tp = str(GeomAbs_SurfaceType(surface.GetType())).split('_')[-1].lower()

        if tp in POSSIBLE_SURFACE_TYPES:
            feature = generateFeature(type=tp, shape=surface, face_indices=face_indices)
            features['surfaces'].append(feature)
        else:
            features['surfaces'].append(None)

        processEdgesHighestDim(topology.edges_from_face(face), features, edges_dict=edges_dict)

        count += 1

        # # *** Generate mesh with OCC *** #
        # if no_use_gmsh:

        #     try:
        #         verts, triangles, tri_faces_dict, face_index = _process_face(face, vert_index=vertex_counter, face_index=face_index)
        #         assert meshes[fake_index] == None
        #         meshes[fake_index] = {"vertices": np.array(verts), "faces": np.array(triangles)}
        #     except Exception as e:
        #         meshes[fake_index] = {"vertices": np.array([]), "faces": np.array([])}
        #         continue

        #     fake_index += 1
        #     vertex_counter += len(verts) 
        # # *** Generate mesh with OCC *** #

    if no_use_gmsh:
        return count, meshes, verts
    else:
        return count, [], []

# Generate features by dimensions
def generateFeatureByDim(shape, features: dict, meshes, no_use_gmsh, use_highest_dim=True):
    print('\n[PythonOCC] Topology Exploration to Generate Features by Dimension')
    features['curves'] = []
    features['surfaces'] = []
    topology = TopologyExplorer(shape)

    # *** Setup para geração da mesh com PythonOCC *** #
    vertex_counter = 0
    if no_use_gmsh:
        fake_index = 0
        mesh = BRepMesh_IncrementalMesh(shape, 0.01, True, 0.1, True)
        mesh.SetShape(shape)
        mesh.Perform()
        assert mesh.IsDone()

        # nr_faces = topology.number_of_faces()
        # meshes = [None]*nr_faces   
    # *** Setup para geração da mesh com PythonOCC *** # 

    if use_highest_dim:
        print('\n[PythonOCC] Using Highest Dim Only, trying with Solids...')
        faces_dict = {}
        count_solids = 0
        for solid in tqdm(topology.solids()):
            _, meshes, verts = processFacesHighestDim(topology.faces_from_solids(solid), topology, features, meshes, no_use_gmsh=no_use_gmsh, vertex_counter = vertex_counter, faces_dict=faces_dict)     
            vertex_counter += len(verts)    
            count_solids += 1

        if count_solids == 0:
            print('\n[PythonOCC] There are no Solids, using Faces as highest dim...')
            count_faces, meshes, verts = processFacesHighestDim(topology.faces(), topology, features, meshes, no_use_gmsh=no_use_gmsh, vertex_counter = vertex_counter, use_tqdm=True)
            vertex_counter += len(verts)    

            if count_faces == 0:
                print('\n[PythonOCC] There are no Faces, using Curves as highest dim...')
                count_edges, meshes, verts = processFacesHighestDim(topology.edges(), features, meshes, no_use_gmsh=no_use_gmsh, vertex_counter = vertex_counter, use_tqdm=True)
                vertex_counter += len(verts)    

                if count_edges == 0:
                    print('\n[PythonOCC] There are no Curves to use...')

    else:

        print('\n[PythonOCC] Using all the Shapes')
        for edge in tqdm(topology.edges()):
            curve = BRepAdaptor_Curve(edge)
            tp = str(GeomAbs_CurveType(curve.GetType())).split('_')[-1].lower()

            if tp in POSSIBLE_CURVE_TYPES:
                feature = generateFeature(type=tp, shape=curve)
                features['curves'].append(feature)
            else:
                features['curves'].append(None)

        for face in tqdm(topology.faces()):
            surface = BRepAdaptor_Surface(face, True)
            tp = str(GeomAbs_SurfaceType(surface.GetType())).split('_')[-1].lower()

            if tp in POSSIBLE_SURFACE_TYPES:
                feature = generateFeature(type=tp, shape=surface)
                features['surfaces'].append(feature)
            else:
                features['surfaces'].append(None)         

            # *** Generate mesh with OCC *** #
            if no_use_gmsh:
                try:
                    verts, triangles = _process_face(face, first_vertex=vertex_counter)
                    assert meshes[fake_index] == None
                    meshes[fake_index] = {"vertices": np.array(verts), "faces": np.array(triangles)}
                except Exception as e:
                    meshes[fake_index] = {"vertices": np.array([]), "faces": np.array([])}
                    continue
            
                fake_index += 1
                vertex_counter += len(verts)
            # *** Generate mesh with OCC *** #

    if meshes:
        return meshes

# Main function
def processPythonOCC(input_name: str, no_use_gmsh, use_highest_dim=True, debug=True) -> dict:
    features = {}
    meshes = []

    shape = read_step_file(input_name, verbosity=debug)
    meshes = generateFeatureByDim(shape, features, meshes, no_use_gmsh=no_use_gmsh, use_highest_dim=use_highest_dim)

    return shape, features, meshes

# # Main function
# def processPythonOCC(input_name: str, use_highest_dim=True) -> dict:
#     features = {}

#     import time

#     shape = read_step_file(input_name)
    
#     time_initial = time.time()
#     features = {}
#     features['curves'] = []
#     features['surfaces'] = []
#     topology = TopologyExplorer(shape)
#     for edge in tqdm(topology.edges()):
#         features['curves'].append(edge)

#     for face in tqdm(topology.faces()):
#         features['surfaces'].append(face)

#     time_finish = time.time()
#     print('Time Old:', time_finish - time_initial, 'sec')
#     print()

#     time_initial = time.time()
#     features2 = {}
#     features2['curves'] = []
#     features2['surfaces'] = []
#     topology2 = TopologyExplorer2(shape)
#     for edge in tqdm(topology2.edges()):
#         features2['curves'].append(edge)
    
#     for face in tqdm(topology2.faces()):
#         features2['surfaces'].append(face)

#     time_finish = time.time()
#     print('Time New:', time_finish - time_initial, 'sec')
#     print()

#     diffs = 0
#     for i in range(len(features['curves'])):
#         if not features['curves'][i].IsSame(features2['curves'][i]):
#             diffs+= 1
#     for i in range(len(features['surfaces'])):
#         if not features['surfaces'][i].IsSame(features2['surfaces'][i]):
#             diffs+= 1 

#     print('Number of Differences:', diffs)

#     exit()

#     return shape, features