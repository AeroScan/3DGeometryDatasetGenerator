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

def computeNewVerticesAndFaces(face, old_verts, old_verts_hc=None):
    """ 
    @params
    face: Surface to process.
    vert_index: Index of the next vertex. For the first surface vert_index is equal to FIRST_VERT_INDEX.
    face_index: Index of the next face. For the first surface face_index is equal to FIRST_FACE_INDEX.

    @returns
    verts: Array of the vertices present in the surface.
    faces: Array of the faces present in the surface.
    face_index: Number to create the list of faces of the shape.
    """

    face_orientation = face.Orientation()

    brep_tool = BRep_Tool()
    location = TopLoc_Location()
    mesh = brep_tool.Triangulation(face, location)
    transform = location.Transformation()
    """ object.Triangulation returns the triangulation present on the face """
    
    new_verts = []
    new_verts_index = []
    new_verts_hc = {}

    if mesh != None:
        number_vertices = mesh.NbNodes()

        for i in range(1, number_vertices + 1):
            pnt = mesh.Node(i)
            pnt.Transform(transform)
            pnt_array = np.array(pnt.Coord()) 
            if old_verts_hc is None:
                index = findPointInList(pnt_array, old_verts)
                if index == -1:
                    new_verts.append(pnt_array)
                    new_index = len(old_verts) + len(new_verts)
                    new_verts_index.append(new_index)             
                else:
                    new_verts_index.append(index)
            else:
                index, hc = findPointInListWithHashCode(pnt, old_verts, old_verts_hc)
                if index < 0:
                    new_verts.append(pnt_array)
                    new_index = len(old_verts) + len(new_verts) - 1
                    new_verts_index.append(new_index) 
                    if index == -2:
                        new_verts_hc[hc] = old_verts_hc[hc]
                        new_verts_hc[hc].append(new_index)
                    else:
                        new_verts_hc[hc] = [new_index]
                else:
                    new_verts_index.append(index)
                    
        new_faces = []
    
        number_faces = mesh.NbTriangles()
        """ NbTriangles returns the number of triangles in the face """
        for i in range(1, number_faces + 1):
            i1, i2, i3 = mesh.Triangle(i).Get()
            i1 = new_verts_index[i1 - 1]
            i2 = new_verts_index[i2 - 1]
            i3 = new_verts_index[i3 - 1]
            if face_orientation == 0:
                verts_of_face = [i1 , i2, i3]
                new_faces.append(verts_of_face)
            elif face_orientation == 1:
                verts_of_face = [i3, i2, i1]
                new_faces.append(verts_of_face)
            else:
                print("Broken face orientation", face_orientation)

    return np.array(new_verts), np.array(new_faces), new_verts_hc

def registerFaceMeshInGlobalMesh(face, mesh):
    """ 
    @params
    face: Surface to process.
    meshes: Meshes' list of the shape. For the first face meshes is a empty list.
    vert_init_of_face: Vertice indice for the face. For the first face vert_init_of_face is equal
                       to FIRST_VERT_INDEX of the generateFeatureByDim function.
    face_init_indice: Face indice for the list of indices. For the first face face_init_indice is
                       to FIRST_FACE_INDEX of the generateFeatureByDim function.

    @returns
    meshes: List of meshes of already processed faces of the shape.
    nbVerts: Number of vertices of mesh.
    faces_indices: Dict of all faces of the shape.
    last_face_index: Last indice of the face. Used for update the face_init_indice variable.
    """
    verts, faces, hashcodes = computeNewVerticesAndFaces(face, mesh['vertices'], mesh['vertices_hashcode'])

    if len(mesh['vertices']) == 0:
        mesh['vertices'] = np.array(verts)
    elif len(verts) > 0:
       mesh['vertices'] = np.concatenate((mesh['vertices'], verts))
    if len(mesh['faces']) == 0:
        mesh['faces'] = np.array(faces)
    elif len(faces) > 0:
        mesh['faces'] = np.concatenate((mesh['faces'], faces))
    if len(hashcodes) > 0:
        mesh['vertices_hashcode'].update(hashcodes)

    return mesh
        
        
