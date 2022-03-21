import numpy as np 

from copy import copy

from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.gp import gp_Pnt
from OCC.Core.STEPConstruct import STEPConstruct_PointHasher

MAX_INT = 2**31 - 1

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

def registerEdgeMeshInGlobalMesh(edge, mesh):
    assert 'vertices' in mesh.keys() and 'vertices_hcs' in mesh.keys()

    brep_tool = BRep_Tool()
    location = TopLoc_Location()
    brep_mesh = brep_tool.Polygon3D(edge, location)
    transform = location.Transformation()

    edge_mesh_data = {}
    if brep_mesh != None:
        vertices = mesh['vertices']
        vertices_hcs = mesh['vertices_hcs']

        vert_indices = []

        nodes = list(brep_mesh.Nodes())
        vert_parameters = list(brep_mesh.Parameters())

        for i in range(1, len(nodes) + 1):
            pnt = nodes[i-1]
            pnt.Transform(transform)
            index, hc = findPointInListWithHashCode(pnt, vertices, vertices_hcs)
            if index < 0:
                old_index = index
                vertices.append(np.array(pnt.Coord()))
                index = len(vertices) - 1
                if old_index == -2:
                    vertices_hcs[hc].append(index)
                else:
                    vertices_hcs[hc] = [index]
            vert_indices.append(index)

        if len(vert_indices) > 0:
            edge_mesh_data['vert_indices'] = vert_indices
            edge_mesh_data['vert_parameters'] = vert_parameters

    return edge_mesh_data


def registerFaceMeshInGlobalMesh(face, mesh, face_edges, edges_data):

    assert 'vertices' in mesh.keys() and 'faces' in mesh.keys()

    face_orientation = face.Orientation()

    brep_tool = BRep_Tool()
    location = TopLoc_Location()
    brep_mesh = brep_tool.Triangulation(face, location)
    transform = location.Transformation()

    face_mesh_data = {}
    out_edges_data = {}
    if brep_mesh != None:
        verts = mesh['vertices']  

        vert_parameters = []

        number_vertices = brep_mesh.NbNodes()
        vert_indices = np.zeros(number_vertices, dtype=np.int64) - 1
        for face_edge in face_edges:
            hc = face_edge.HashCode(MAX_INT)

            if hc in edges_data:
                found_edge = False
                for i, edge_data in enumerate(edges_data[hc]):
                    edge = edge_data['entity']
                    if face_edge.IsSame(edge):
                        found_edge = True
                        #l = TopLoc_Location()
                        poly_on_triang = brep_tool.PolygonOnTriangulation(face_edge, brep_mesh, location)
                        if poly_on_triang is not None:
                            poly_nodes = list(poly_on_triang.Nodes())
                            edge_index = edge_data['index']
                            edge_mesh_data = edge_data['mesh_data']

                            if edge_mesh_data == {}:
                                edge_vert_indices = copy(poly_nodes)
                                edge_vert_parameters = list(poly_on_triang.Parameters())
                                out_edges_mesh_data = {'vert_indices': edge_vert_indices, 'vert_parameters': edge_vert_parameters}
                                out_edge_data = {'index': edge_index, 'hc_list_index': i, 'mesh_data': out_edges_mesh_data}
                                if hc in out_edges_data:
                                    out_edges_data[hc].append(out_edge_data)
                                else:
                                    out_edges_data[hc] = [out_edge_data]
                            else:
                                poly_nodes_arr = np.array(poly_nodes, dtype=np.int64) - 1
                                edge_vert_indices_arr = np.array(edge_mesh_data['vert_indices'], dtype=np.int64)
                                assert len(poly_nodes_arr) == len(edge_vert_indices_arr)
                                vert_indices[poly_nodes_arr] = edge_vert_indices_arr   
                        else:
                            print('ERROR: none polygon on triangulation.')
                        break
                if found_edge == False:
                    print('ERROR: some edge has not been computed before. (IsSame Error)')
            else:
                print('ERROR: some edge has not been computed before. (HashCode Error)')

        face
        for i in range(1, number_vertices + 1):
            pnt = brep_mesh.Node(i)
            pnt.Transform(transform)
            pnt_array = np.array(pnt.Coord())

            if vert_indices[i - 1] == -1:
                verts.append(pnt_array)
                vert_indices[i - 1] = len(verts) - 1

            uv_node = brep_mesh.UVNode(i)
            vert_parameters.append(list(uv_node.Coord()))
        
        for key in out_edges_data:
            for i in range(len(out_edges_data[key])):
                out_edges_data[key][i]['mesh_data']['vert_indices'] = [int(vert_indices[j - 1]) for j in out_edges_data[key][i]['mesh_data']['vert_indices']]

        vert_indices = vert_indices.tolist()

        faces = mesh['faces']           
        face_indices = []
    
        number_faces = brep_mesh.NbTriangles()
        for i in range(1, number_faces + 1):
            i1, i2, i3 = brep_mesh.Triangle(i).Get()
            i1 = vert_indices[i1 - 1]
            i2 = vert_indices[i2 - 1]
            i3 = vert_indices[i3 - 1]
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

            face_mesh_data = {'vert_indices': vert_indices, 'vert_parameters': vert_parameters, 'face_indices': face_indices}

    return face_mesh_data, out_edges_data