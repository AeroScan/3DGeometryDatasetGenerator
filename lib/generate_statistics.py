from functools import partial
import numpy as np
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map
import open3d as o3d
from psutil import cpu_count

def generate_area_from_surface(surface, vertices: np.array, faces: np.array) -> float:
    """ This function returns the area from the received surface """
    try:
        face_indices = surface["face_indices"]
        vert_indices = np.unique(surface["vert_indices"])
    except:
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

def generate_area_from_surfaces(mesh, surface) -> list:
    """ This method returns a list with all surfaces area """
    try:
        surface_type = surface.primitiveType() if surface.primitiveType() != 'BaseSurface' \
                                                  else 'Other'
    except:
        surface_type = surface["type"]

    if surface is None:
        return (surface_type, 0.0)
    else:
        surface_area = generate_area_from_surface(surface, mesh["vertices"], mesh["faces"])
        return (surface_type, surface_area)

def generate_statistics(features, mesh, only_stats=False):
    """ This function get all the stats from the model """
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

    result['bounding_box'] = mesh_obj.get_min_bound().tolist() + \
                            (mesh_obj.get_max_bound() - mesh_obj.get_min_bound()).tolist()

    if only_stats:
        print("Generating for curves: ")
        for curve in tqdm(features["curves"]):
            if curve is not None:
                tp = curve["type"]
                if tp not in curves_dict:
                    curves_dict[tp] = {'number_vertices': 0, 'number_curves': 0}
                curves_dict[tp]['number_vertices'] += len(curve["vert_indices"])
                curves_dict[tp]['number_curves'] += 1
        result['curves'] = curves_dict
        surfaces_dict['area'] = 0.0
        total_area_of_surfaces = 0.0
        print("Generating for surfaces: ")
        for surface in tqdm(features['surfaces']):
            if surface is not None:
                tp = surface["type"]
                if tp not in surfaces_dict:
                    surfaces_dict[tp] = {'number_vertices': 0, 'number_faces': 0, \
                                         'number_surfaces': 0, 'area': 0}
                surfaces_dict[tp]['number_vertices'] += len(surface["vert_indices"])
                surfaces_dict[tp]['number_faces'] += len(surface["face_indices"])
                surfaces_dict[tp]['number_surfaces'] += 1

        workers = min(32, cpu_count()+4)
        chunksize = len(features["surfaces"]) // workers
        results = []
        results += process_map(partial(generate_area_from_surfaces, mesh), features["surfaces"], \
                               max_workers=workers, chunksize=chunksize)

        for surface_type, surface_area in results:
            total_area_of_surfaces += surface_area
            surfaces_dict[surface_type]["area"] += surface_area

        surfaces_dict['area'] = total_area_of_surfaces
        result['surfaces'] = surfaces_dict
    else:
        print("Generating for curves: ")
        for curve in tqdm(features['curves']):
            if curve is not None:
                tp = curve.primitiveType() if curve.primitiveType() != 'BaseCurve' else 'Other'
                if tp not in curves_dict:
                    curves_dict[tp] = {'number_vertices': 0, 'number_curves': 0}
                curves_dict[tp]['number_vertices'] += len(curve.vert_indices)
                curves_dict[tp]['number_curves'] += 1
        result['curves'] = curves_dict
        surfaces_dict['area'] = 0.0
        total_area_of_surfaces = 0.0
        print("Generating for surfaces: ")
        for surface in tqdm(features['surfaces']):
            if surface is not None:
                tp = surface.primitiveType() if surface.primitiveType() != 'BaseSurface' else 'Other'
                if tp not in surfaces_dict:
                    surfaces_dict[tp] = {'number_vertices': 0, 'number_faces': 0, \
                                         'number_surfaces': 0, 'area': 0}
                surfaces_dict[tp]['number_vertices'] += len(surface.vert_indices)
                surfaces_dict[tp]['number_faces'] += len(surface.face_indices)
                surfaces_dict[tp]['number_surfaces'] += 1

        workers = min(32, cpu_count()+4)
        chunksize = len(features["surfaces"]) // workers
        results = []
        results += process_map(partial(generate_area_from_surfaces, mesh), features["surfaces"], \
                               max_workers=workers, chunksize=chunksize)

        for surface_type, surface_area in results:
            total_area_of_surfaces += surface_area
            surfaces_dict[surface_type]["area"] += surface_area

        surfaces_dict['area'] = total_area_of_surfaces
        result['surfaces'] = surfaces_dict
    return result
