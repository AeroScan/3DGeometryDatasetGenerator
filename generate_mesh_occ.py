import numpy as np 

from OCC.Core import BRepBuilderAPI
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh

MAX_INT = 2**31 - 1

def get_hashcode(entity):
    return entity.HashCode(MAX_INT)

def process_face(face, first_vertex=0):
    print(face)
    face_orientation_wrt_surface_normal = face.Orientation()

    brep_tool = BRep_Tool()
    location = TopLoc_Location()
    mesh = brep_tool.Triangulation(face, location)
    verts = []
    triangle = []
    # normals = []
    # centroids = []
    if mesh != None:

        num_vertices = mesh.NbNodes()
        for i in range(1, num_vertices + 1):
            verts.append(list(mesh.Node(i).Coord()))        
        verts = np.array(verts)

        num_tris = mesh.NbTriangles()
        for i in range(1, num_tris + 1):
            index1, index2, index3 = mesh.Triangle(i).Get()
            if face_orientation_wrt_surface_normal == 0:
             triangle.append([first_vertex + index1 - 1, first_vertex + index2 - 1, first_vertex + index3 - 1])
            elif face_orientation_wrt_surface_normal == 1:
             triangle.append([first_vertex + index3 - 1, first_vertex + index2 - 1, first_vertex + index1 - 1])
            else:
                print("Broken face orientation", face_orientation_wrt_surface_normal)
        
        # # Get mesh normals
        # pt1, pt2, pt3 = verts[index1 - 1], verts[index2 - 1], verts[index3 - 1]
        # centroid = (pt1 + pt2 + pt3) / 3
        # centroids.append(centroid)
        # normal = np.cross(pt2-pt1, pt3-pt1)
        # norm = np.linalg.norm(normal)
        # if not np.isclose(norm, 0):
        #     normal /= norm
        # if face_orientation_wrt_surface_normal == 1:
        #     normal -= normal
        # normals.append(normal)

    return verts, triangle

def generateMeshOcc(shapes):
    parts = []

    # parts = load_parts_from_step_files(pathname) # return list of the TopoDS
    parts = [shapes]
    
    indices = range(len(parts))
    meshes = []
    vertex_count = 0
    for index in indices:

        part = parts[index]
        print(f'TIPO DA PARTE: {type(part)}')

        explorer = TopologyExplorer(part, ignore_orientation=False)

        # constructor
        mesh = BRepMesh_IncrementalMesh(part, 0.01, True, 0.1, True)
        # set the shape that will go tringulated 
        mesh.SetShape(part)
        mesh.Perform()
        assert mesh.IsDone()

        nr_faces = explorer.number_of_faces()
        meshes = [None]*nr_faces

        faces = explorer.faces()
        fake_index = 0
        for face in faces:
            expected_face_index = get_hashcode(face)

            try:
                verts, triangle = process_face(face, first_vertex=vertex_count)
                assert meshes[fake_index] == None
                meshes[fake_index] = {"vertices": np.array(verts), "faces": np.array(triangle)}
            except Exception as e:
                meshes[fake_index] = {"vertices": np.array([]), "faces": np.array([])}
                continue
                
            fake_index += 1 ## arrumar o indice da face baseado no indice dado pelo OCC 
                            # importante para garantir a mesma ordem entre processMesh e processFeatures
            vertex_count += len(verts) ## a confirmar
            
            ## verts indices; faces indices; verts params
    return meshes
