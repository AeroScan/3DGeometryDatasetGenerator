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

def computeNewVerticesAndFaces(face, mesh):

    assert 'vertices' in mesh.keys() and 'faces' in mesh.keys()

    face_orientation = face.Orientation()

    brep_tool = BRep_Tool()
    location = TopLoc_Location()
    brep_mesh = brep_tool.Triangulation(face, location)
    transform = location.Transformation()
    """ object.Triangulation returns the triangulation present on the face """

    old_verts = mesh['vertices']
    old_verts_hc = mesh['vertices_hashcode'] if 'vertices_hashcode' in mesh.keys() else None
    old_faces = mesh['faces']

    new_verts = []
    new_verts_hc = {}
    uv_params = []
    vert_indices = []

    if brep_mesh != None:
        number_vertices = brep_mesh.NbNodes()

        for i in range(1, number_vertices + 1):
            pnt = brep_mesh.Node(i)
            pnt.Transform(transform)
            pnt_array = np.array(pnt.Coord())
            index = -1
            if old_verts_hc is None:
                index = findPointInList(pnt_array, old_verts)
                if index == -1:
                    new_verts.append(pnt_array)
                    index = len(old_verts) + len(new_verts)
            else:
                index, hc = findPointInListWithHashCode(pnt, old_verts, old_verts_hc)
                if index < 0:
                    old_index = index
                    new_verts.append(pnt_array)
                    index = len(old_verts) + len(new_verts) - 1
                    if old_index == -2:
                        new_verts_hc[hc] = old_verts_hc[hc]
                        new_verts_hc[hc].append(index)
                    else:
                        new_verts_hc[hc] = [index]
            
            uv_node = brep_mesh.UVNode(i)
            uv_params.append(np.array(uv_node.Coord()))
            vert_indices.append(index)
                    
        new_faces = []
        face_indices = []
    
        number_faces = brep_mesh.NbTriangles()
        """ NbTriangles returns the number of triangles in the face """
        for i in range(1, number_faces + 1):
            i1, i2, i3 = brep_mesh.Triangle(i).Get()
            i1 = vert_indices[i1 - 1]
            i2 = vert_indices[i2 - 1]
            i3 = vert_indices[i3 - 1]
            if face_orientation == 0:
                verts_of_face = [i1 , i2, i3]
                new_faces.append(verts_of_face)
                face_indices.append(len(old_faces) + i)
            elif face_orientation == 1:
                verts_of_face = [i3, i2, i1]
                new_faces.append(verts_of_face)
                face_indices.append(len(old_faces) + i)
            else:
                print("Broken face orientation", face_orientation)

    return np.array(new_verts), np.array(new_faces), new_verts_hc, np.array(vert_indices), np.array(face_indices), np.array(uv_params)

def registerFaceMeshInGlobalMesh(face, mesh):

    new_verts, new_faces, new_hashcodes, vert_indices, face_indices, uv_params = computeNewVerticesAndFaces(face, mesh)

    if len(mesh['vertices']) == 0:
        mesh['vertices'] = np.array(new_verts)
    elif len(new_verts) > 0:
       mesh['vertices'] = np.concatenate((mesh['vertices'], new_verts))
    if len(mesh['faces']) == 0:
        mesh['faces'] = np.array(new_faces)
    elif len(new_faces) > 0:
        mesh['faces'] = np.concatenate((mesh['faces'], new_faces))
    if len(new_hashcodes) > 0:
        mesh['vertices_hashcode'].update(new_hashcodes)

    return mesh, vert_indices, face_indices, uv_params
        
        
