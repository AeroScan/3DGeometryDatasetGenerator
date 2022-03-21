from encodings import search_function
import numpy as np 

from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.gp import gp_Pnt
from OCC.Core.STEPConstruct import STEPConstruct_PointHasher

MAX_INT = 2**31 - 1

def findPointInList(point, points_list):
    index = -1
    try:
        index = points_list.index(point)
    except ValueError:
        index = -1
    return index

def findPointInListWithHashCode(point, points, hash_codes):
    hc = STEPConstruct_PointHasher.HashCode(point, MAX_INT)
    index = -1
    if hc in hash_codes:
        index = -2
        for i in hash_codes[hc]:
            array = points[i]
            point2 = gp_Pnt(array[0], array[1], array[2])
            if STEPConstruct_PointHasher.IsEqual(point, point2):
                index = i
                break
    return index, hc

def registerFaceMeshInGlobalMesh(face, mesh):

    assert 'vertices' in mesh.keys() and 'faces' in mesh.keys()

    face_orientation = face.Orientation()

    brep_tool = BRep_Tool()
    location = TopLoc_Location()
    brep_mesh = brep_tool.Triangulation(face, location)
    transform = location.Transformation()
    """ object.Triangulation returns the triangulation present on the face """

    verts = mesh['vertices']  
    verts_hc = mesh['vertices_hashcode'] if 'vertices_hashcode' in mesh.keys() else None

    uv_params = []
    vert_indices = []

    if brep_mesh is not None:
        number_vertices = brep_mesh.NbNodes()

        for i in range(1, number_vertices + 1):
            pnt = brep_mesh.Node(i)
            pnt.Transform(transform)
            pnt_array = np.array(pnt.Coord())
            index = -1
            if verts_hc is None:
                index = findPointInList(pnt_array, verts)
                if index == -1:
                    verts.append(pnt_array)
                    index = len(verts) - 1
            else:
                index, hc = findPointInListWithHashCode(pnt, verts, verts_hc)
                if index < 0:
                    old_index = index
                    verts.append(pnt_array)
                    index = len(verts) - 1
                    if old_index == -2:
                        verts_hc[hc].append(index)
                    else:
                        verts_hc[hc] = [index]
            
            uv_node = brep_mesh.UVNode(i)
            uv_params.append(list(uv_node.Coord()))
            vert_indices.append(index)

        faces = mesh['faces']           
        face_indices = []
    
        number_faces = brep_mesh.NbTriangles()
        """ NbTriangles returns the number of triangles in the face """
        for i in range(1, number_faces + 1):
            i1, i2, i3 = brep_mesh.Triangle(i).Get()
            i1 = vert_indices[i1 - 1]
            i2 = vert_indices[i2 - 1]
            i3 = vert_indices[i3 - 1]
            # if i1 == i2 or i2 == i3 or i1 == i3:
            #     print(f'WARNING: face {len(faces)} has two vertices with the same index.')
            if face_orientation == 0:
                verts_of_face = np.array([i1 , i2, i3])
                faces.append(verts_of_face)
                face_indices.append(len(faces) - 1)
            elif face_orientation == 1:
                verts_of_face = np.array([i3, i2, i1])
                faces.append(verts_of_face)
                face_indices.append(len(faces) - 1)
            else:
                print("Broken face orientation", face_orientation)

        mesh_params_of_the_face = {'vert_indices': vert_indices, 'vert_parameters': uv_params, 'face_indices': face_indices}

        return mesh, mesh_params_of_the_face
        
    else:
        print('Could not generate mesh for surface')
        return None
        
