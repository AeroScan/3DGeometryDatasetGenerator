import numpy as np 

from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopLoc import TopLoc_Location

MAX_INT = 2**31 - 1

def _process_face(face, vert_index, face_index):
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
    verts = []
    faces = []
    faces_d = {}

    if mesh != None:
        number_vertices = mesh.NbNodes()
        """ NbNodes returns the number of vertices in the face """
        for i in range(1, number_vertices + 1):
            pnt = mesh.Node(i)
            pnt.Transform(transform)
            verts.append(list(pnt.Coord()))        
        verts = np.array(verts)

        number_faces = mesh.NbTriangles()
        """ NbTriangles returns the number of triangles in the face """
        for i in range(1, number_faces + 1):
            i1, i2, i3 = mesh.Triangle(i).Get()
            """ object.Triangle(index_face).Get() returns the indices of the nodes of THIS triangle """
            if face_orientation == 0:
                verts_of_face = [vert_index + i1 - 1, vert_index + i2 - 1, vert_index + i3 - 1]
                faces.append(verts_of_face)
            elif face_orientation == 1:
                verts_of_face = [vert_index + i3 - 1, vert_index + i2 - 1, vert_index + i1 - 1]
                faces.append(verts_of_face)
            else:
                print("Broken face orientation", face_orientation)
        
        for fc in faces:
            faces_d[str(face_index)] = fc
            face_index += 1

    return verts, faces, face_index, faces_d

def generateMeshHighestDim(face, meshes, vert_init_of_face, face_init_indice):
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
    faces: Dict of all faces of the shape.
    last_face_indice: Last indice of the face. Used for update the face_init_indice variable.
    """
    pass

def generateMeshAllShapes(face, meshes, vert_init_of_face, face_init_indice):
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
    try:
        verts, faces, face_index, faces_d = _process_face(face, vert_init_of_face, face_init_indice)

        nbVerts = len(verts)

        face_indices = []
        for index in faces_d.keys():
            face_indices.append(int(index))

        last_face_index = face_index

        meshes.append({"vertices": np.array(verts), "faces": np.array(faces)})
    except Exception as e:
        meshes.append({"vertices": np.array([]), "faces": np.array([])})
    
    return meshes, nbVerts, face_indices, last_face_index, verts
        
        
