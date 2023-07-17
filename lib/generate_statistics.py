import numpy as np
from tqdm import tqdm
import open3d as o3d


def generate_area_from_surface(surface, vertices: np.array, faces: np.array) -> float:
    """ This function returns the area from the received surface """
    try:
        face_indices = surface["face_indices"]
        vert_indices = np.unique(surface["vert_indices"])
    except TypeError:
        face_indices = surface.face_indices
        vert_indices = np.unique(surface.vert_indices)

    if len(vert_indices) > 0 and len(face_indices) > 0:
        vertices = vertices[vert_indices]
        faces = faces[face_indices]

        faces_n = []
        for face in faces:
            aux = np.hstack([np.where(vert_indices == vert)[0] for vert in face])
            faces_n.append(aux)
        faces_n = np.asarray(faces_n)

        surface_mesh = o3d.geometry.TriangleMesh()
        surface_mesh.vertices = o3d.utility.Vector3dVector(vertices)
        surface_mesh.triangles = o3d.utility.Vector3iVector(faces_n)

        return surface_mesh.get_surface_area()

    return 0.

def generateStatisticsOld(features, mesh, only_stats=False):
    result = {}
    result['number_vertices'] = len(mesh['vertices'])
    result['number_faces'] = len(mesh['faces'])
    result['number_curves'] = len(features['curves'])
    result['number_surfaces'] = len(features['surfaces'])
    
    curves_dict = {}
    surfaces_dict = {}

    mesh_obj = o3d.geometry.TriangleMesh()
    mesh_obj.vertices = o3d.utility.Vector3dVector(np.asarray(mesh['vertices']))
    mesh_obj.triangles = o3d.utility.Vector3iVector(np.asarray(mesh['faces']))

    result['bounding_box'] = mesh_obj.get_min_bound().tolist() + (mesh_obj.get_max_bound() - mesh_obj.get_min_bound()).tolist() 

    print("Generating for curves: ")
    for curve in tqdm(features["curves"]):
        if curve is not None:
            tp = curve["type"]
            if tp not in curves_dict:
                curves_dict[tp] = {'number_vertices': 0, 'number_curves': 0, 'number_void_curves': 0}
            curves_dict[tp]['number_vertices'] += len(curve["vert_indices"])
            curves_dict[tp]['number_curves'] += 1
    result['curves'] = curves_dict
    result['number_void_curves'] = 0
    surfaces_dict['area'] = 0.0
    total_area_of_surfaces = 0.0
    print("Generating for surfaces: ")
    for surface in tqdm(features['surfaces']):
        if surface is not None:
            tp = surface["type"]
            if tp not in surfaces_dict:
                surfaces_dict[tp] = {'number_vertices': 0, 'number_faces': 0, 'number_surfaces': 0, 'number_void_surfaces': 0, 'area': 0}
            # surface_area = generate_area_from_surface(surface, mesh_obj)
            surface_area = generate_area_from_surface(surface, mesh["vertices"], mesh["faces"])
            surfaces_dict[tp]['number_vertices'] += len(surface["vert_indices"])
            surfaces_dict[tp]['number_faces'] += len(surface["face_indices"])
            surfaces_dict[tp]['number_surfaces'] += 1
            surfaces_dict[tp]['area'] += surface_area
            total_area_of_surfaces += surface_area
    surfaces_dict['area'] = total_area_of_surfaces
    result['surfaces'] = surfaces_dict
    result['number_void_surfaces'] = 0
    return result

def generateStatistics(geometries_data, mesh):
    result = {}
    result['number_vertices'] = len(mesh.vertices)
    result['number_faces'] = len(mesh.triangles)
    result['number_curves'] = len(geometries_data['curves'])
    result['number_surfaces'] = len(geometries_data['surfaces'])

    result['bounding_box'] = mesh.get_min_bound().tolist() + (mesh.get_max_bound() - mesh.get_min_bound()).tolist() 

    curves_dict = {}
    surfaces_dict = {}

    print("Generating for curves: ")
    for curve in tqdm(geometries_data["curves"]):
        if curve['geometry'] is not None:
            tp = curve['geometry'].getType()
            if tp not in curves_dict:
                curves_dict[tp] = {'number_vertices': 0, 'number_curves': 0, 'number_void_curves': 0}
            
            mesh_info = curve['geometry'].getMeshInfo()
            curves_dict[tp]['number_curves'] += 1
            
            if mesh_info is not None and len(mesh_info['vert_indices']) > 0:
                curves_dict[tp]['number_vertices'] += len(mesh_info['vert_indices'])
                mesh = curve['geometry'].getMesh()
                if mesh is not None:
                    # perimeter
                    pass
            else:
                curves_dict[tp]['number_void_curves'] += 1

    number_void_curves = sum([curves_dict[tp]['number_void_curves'] for tp in curves_dict.keys()])

    print("Generating for surfaces: ")
    for surface in tqdm(geometries_data['surfaces']):
        if surface['geometry'] is not None:
            tp = surface['geometry'].getType()
            if tp not in surfaces_dict:
                surfaces_dict[tp] = {'number_vertices': 0, 'number_faces': 0, 'number_surfaces': 0, 'number_void_surfaces': 0, 'area': 0}
            
            mesh_info = surface['geometry'].getMeshInfo()
            surfaces_dict[tp]['number_surfaces'] += 1
            
            if mesh_info is not None and len(mesh_info['face_indices']) > 0:
                surfaces_dict[tp]['number_vertices'] += len(mesh_info['vert_indices'])
                surfaces_dict[tp]['number_faces'] += len(mesh_info['face_indices'])
                mesh = surface['geometry'].getMesh()
                if mesh is not None:
                    surfaces_dict[tp]['area'] += mesh.get_surface_area()
            else:
                surfaces_dict[tp]['number_void_surfaces'] += 1

    total_area_of_surfaces = sum([surfaces_dict[tp]['area'] for tp in surfaces_dict.keys()])
    number_void_surfaces = sum([surfaces_dict[tp]['number_void_surfaces'] for tp in surfaces_dict.keys()])
    surfaces_dict['area'] = total_area_of_surfaces
    
    result['number_void_curves'] = number_void_curves
    result['number_void_surfaces'] = number_void_surfaces
    result['curves'] = curves_dict
    result['surfaces'] = surfaces_dict
    return result