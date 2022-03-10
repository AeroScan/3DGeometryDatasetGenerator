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

POSSIBLE_CURVE_TYPES = ['line', 'circle', 'ellipse']
POSSIBLE_SURFACE_TYPES = ['plane', 'cylinder', 'cone', 'sphere', 'torus']

# # Generate lines information
# def generateLineFeature(shape) -> dict:
#     # shape = shape.Line()

#     # feature = {
#     #     'type': 'Line',
#     #     'location': gpXYZ2List(shape.Location()),
#     #     'direction': gpXYZ2List(shape.Direction()),
#     # }
#     feature = Line(shape).getFeatures()

#     return {**feature}

# # Generate circles information
# def generateCircleFeature(shape) -> dict:
#     # shape = shape.Circle()

#     # feature = {
#     #     'type': 'Circle',
#     #     'location': gpXYZ2List(shape.Location()),
#     #     'z_axis': gpXYZ2List(shape.Axis().Direction()),
#     #     'radius': shape.Radius(),
#     #     'x_axis': gpXYZ2List(shape.XAxis().Direction()),
#     #     'y_axis': gpXYZ2List(shape.YAxis().Direction()),
#     # }

#     # if feature['radius'] == 0:
#     #     return None
#     # else:
#     #     return {**feature}
#     feature = Circle(shape).getFeatures()

#     return {**feature} if feature is not None else None

# # Generate ellipses information
# def generateEllipseFeature(shape) -> dict:
#     # shape = shape.Ellipse()

#     # feature = {
#     #     'type': 'Ellipse',
#     #     'focus1': gpXYZ2List(shape.Focus1()),
#     #     'focus2': gpXYZ2List(shape.Focus2()),
#     #     'x_axis': gpXYZ2List(shape.XAxis().Direction()),
#     #     'y_axis': gpXYZ2List(shape.YAxis().Direction()),
#     #     'z_axis': gpXYZ2List(shape.Axis().Direction()),
#     #     'x_radius': shape.MajorRadius(),
#     #     'y_radius': shape.MinorRadius(),
#     # }

#     # if feature['x_radius'] == 0 or feature['y_radius'] == 0:
#     #     return None
#     # else:
#     #     return {**feature}

#     feature = Ellipse(shape).getFeatures()

#     return {**feature} if feature is not None else None

# # Generate planes information
# def generatePlaneFeature(shape) -> dict:
#     # shape = shape.Plane()

#     # feature = {
#     #     'type': 'Plane',
#     #     'location': gpXYZ2List(shape.Location()),
#     #     'normal': gpXYZ2List(shape.Axis().Direction()),
#     #     'x_axis': gpXYZ2List(shape.XAxis().Direction()),
#     #     'y_axis': gpXYZ2List(shape.YAxis().Direction()),
#     #     'z_axis': gpXYZ2List(shape.Axis().Direction()),
#     #     'coefficients': list(shape.Coefficients()),
#     # }

#     feature = Plane(shape).getFeatures()

#     return {**feature}


# # Generate cylinders information
# def generateCylinderFeature(shape) -> dict:
#     # shape = shape.Cylinder()

#     # feature = {
#     #     'type': 'Cylinder',
#     #     'location': gpXYZ2List(shape.Location()),
#     #     'x_axis': gpXYZ2List(shape.XAxis().Direction()),
#     #     'y_axis': gpXYZ2List(shape.YAxis().Direction()),
#     #     'z_axis': gpXYZ2List(shape.Axis().Direction()),
#     #     'coefficients': list(shape.Coefficients()),
#     #     'radius': shape.Radius(),
#     # }

#     feature = Cylinder(shape).getFeatures()

#     return {**feature}

# # Generate cones information
# def generateConeFeature(shape) -> dict:
#     # shape = shape.Cone()

#     # feature = {
#     #     'type': 'Cone',
#     #     'location': gpXYZ2List(shape.Location()),
#     #     'x_axis': gpXYZ2List(shape.XAxis().Direction()),
#     #     'y_axis': gpXYZ2List(shape.YAxis().Direction()),
#     #     'z_axis': gpXYZ2List(shape.Axis().Direction()),
#     #     'coefficients': list(shape.Coefficients()),
#     #     'radius': shape.RefRadius(),
#     #     'angle': shape.SemiAngle(),
#     #     'apex': gpXYZ2List(shape.Apex()),
#     # }

#     feature = Cone(shape).getFeatures()

#     return {**feature}

# # Generate spheres information
# def generateSphereFeature(shape) -> dict:
#     # shape = shape.Sphere()

#     # x_axis = np.array(gpXYZ2List(shape.XAxis().Direction()))
#     # y_axis = np.array(gpXYZ2List(shape.YAxis().Direction()))
#     # z_axis = np.cross(x_axis, y_axis)

#     # feature = {
#     #     'type': 'Sphere',
#     #     'location': gpXYZ2List(shape.Location()),
#     #     'x_axis': x_axis.tolist(),
#     #     'y_axis': y_axis.tolist(),
#     #     'z_axis': z_axis.tolist(),
#     #     'coefficients': list(shape.Coefficients()),
#     #     'radius': shape.Radius(),
#     # }

#     feature = Sphere(shape).getFeatures()

#     return {**feature}

# # Generate torus information
# def generateTorusFeature(shape) -> dict:
#     # shape = shape.Torus()

#     # feature = {
#     #     'type': 'Torus',
#     #     'location': gpXYZ2List(shape.Location()),
#     #     'x_axis': gpXYZ2List(shape.XAxis().Direction()),
#     #     'y_axis': gpXYZ2List(shape.YAxis().Direction()),
#     #     'z_axis': gpXYZ2List(shape.Axis().Direction()),
#     #     # 'coefficients': list(shape.Coefficients()),
#     #     'max_radius': shape.MajorRadius(),
#     #     'min_radius': shape.MinorRadius(),
#     # }
#     feature = Torus(shape).getFeatures()

#     return {**feature}

# # Call function by type
# def generateFeature(type, shape):
#     # generate_functions_dict = {
#     #     'line': generateLineFeature,
#     #     'circle': generateCircleFeature,
#     #     'ellipse': generateEllipseFeature,
#     #     'plane': generatePlaneFeature,
#     #     'cylinder': generateCylinderFeature,
#     #     'cone': generateConeFeature,
#     #     'sphere': generateSphereFeature,
#     #     'torus': generateTorusFeature,
#     # }
#     # if type.lower() in generate_functions_dict.keys():
#     #     return generate_functions_dict[type.lower()](shape)
    
#     return FeaturesFactory(type, shape).getFeatureByType()

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

        # if tp in POSSIBLE_CURVE_TYPES:
        #     feature = FeaturesFactory(type_=tp, shape=curve).getFeatureByType()
        #     features['curves'].append(feature)
        # else:
        #     features['curves'].append(None)
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
        
        feature = {}
        if mesh_generator == 'occ':
            mesh, mesh_params = registerFaceMeshInGlobalMesh(face, mesh)
            
            features['surfaces'].append(FeaturesFactory.getPrimitiveObject(type=tp, shape=surface, params=mesh_params))
        else:
            features['surfaces'].append(FeaturesFactory.getPrimitiveObject(type=tp, shape=surface, params=None))

        # surface = BRepAdaptor_Surface(face, True)
        # tp = str(GeomAbs_SurfaceType(surface.GetType())).split('_')[-1].lower()

        # if tp in POSSIBLE_SURFACE_TYPES:
        #     feature.update(FeaturesFactory(type_=tp, shape=surface).getFeatureByType())
        #     features['surfaces'].append(feature)
        # else:
        #     features['surfaces'].append(None)

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

            # if tp in POSSIBLE_CURVE_TYPES:
            #     feature = FeaturesFactory(type_=tp, shape=curve).getFeatureByType()
            #     features['curves'].append(feature)
            # else:
            #     features['curves'].append(None)

        for face in tqdm(topology.faces()):
            surface = BRepAdaptor_Surface(face, True)
            tp = str(GeomAbs_SurfaceType(surface.GetType())).split('_')[-1].lower()

            feature = {}
            if mesh_generator == 'occ':
                mesh, mesh_params = registerFaceMeshInGlobalMesh(face, mesh)
                
                features['surfaces'].append(FeaturesFactory.getPrimitiveObject(type=tp, shape=surface, params=mesh_params))
            else:
                features['surfaces'].append(FeaturesFactory.getPrimitiveObject(type=tp, shape=surface, params=None))

            # surface = BRepAdaptor_Surface(face, True)
            # tp = str(GeomAbs_SurfaceType(surface.GetType())).split('_')[-1].lower()

            # if tp in POSSIBLE_SURFACE_TYPES:
            #     feature.update(FeaturesFactory(type_=tp, shape=surface).getFeatureByType())
            #     features['surfaces'].append(feature)
            # else:
            #     features['surfaces'].append(None)

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