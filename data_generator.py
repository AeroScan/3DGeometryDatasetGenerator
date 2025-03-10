import os
import argparse
from pathlib import Path
import gc
import numpy as np
import yaml
from lib.tools import (
    computeTranslationVector,
    writeFeatures,
    writeMeshPLY,
    rotation_matrix_from_vectors,
    get_files_from_input_path,
    output_name_converter,
    remove_by_filename,
    writeJSON,
    loadMeshPLY,
    loadFeatures,
    create_dirs,
    list_files,
    compareDictsWithTolerance)
from lib.generate_gmsh import processGMSH
from lib.generate_pythonocc import processPythonOCC
from lib.generate_statistics import generateStatistics, generateStatisticsOld

from asGeometryOCCWrapper.curves import CurveFactory
from asGeometryOCCWrapper.surfaces import SurfaceFactory

import open3d as o3d

CAD_FORMATS = ['.step', '.stp', '.STEP']
MESH_FORMATS = ['.ply', '.PLY']
FEATURES_FORMATS = ['.pkl', '.PKL', '.yml', '.yaml', '.YAML', '.json', '.JSON']
STATS_FORMATS = [".json", ".JSON"]

def parse_opt():
    """ Function to organize all the possible arguments """
    parser = argparse.ArgumentParser(description='General arguments')
    parser.add_argument('input_path', type=str, default='./dataset/step/', help='Path to the input directory')
    parser.add_argument('output_path', type=str, default='./results/', help='Path to the output directory where processed files will be saved')
    parser.add_argument('--meta_path', type=str, default='', help="Path to the directory containing metadata information such as file URLs, author names, vertical up axis of the model, and model type (large or small plant and large or small part)")
    parser.add_argument('--use_highest_dim', action='store_true', help='Boolean flag to indicate whether to use the highest dimension of the input CAD as reference or not')
    parser.add_argument('--delete_old_data', action='store_true', help='Boolean flag indicating whether to delete old data in the output directory')
    parser.add_argument('--verbose', action='store_true', help='Boolean flag indicating whether to run the code in debug mode.')

    # Mesh parser general
    mesh_parser = parser.add_argument_group("Mesh arguments")
    mesh_parser.add_argument("--mesh_generator", type=str, default="occ", choices=["occ", "gmsh"], help="Name of the mesh generator to use")
    mesh_parser.add_argument('--mesh_folder', type=str, default="mesh", help='Path to the folder where the mesh will be saved')

    # Gmsh parser general
    gmsh_parser = parser.add_argument_group("GMSH arguments")
    gmsh_parser.add_argument('--mesh_size', type=float, default=1e+22, help="The edge size of the mesh, used in conjunction with the GMSH mesh generator")

    # Feature parser general
    feature_parser = parser.add_argument_group("Feature arguments")
    feature_parser.add_argument('--features_folder', type=str, default="features", help='Path to the folder containing the features to be extracted')
    feature_parser.add_argument('--features_file_type', type=str, default='pkl', choices=["pkl", "json", "yaml"], help='The file type of the features')

    # Stats parser general
    stats_parser = parser.add_argument_group("Stats arguments")
    stats_parser.add_argument('--stats_folder', type=str, default="stats", help='Path to the folder where statistics will be saved')
    stats_parser.add_argument('--only_stats', action='store_true', help='Boolean flag indicating whether to only generate statistics without processing the data.')

    return parser.parse_args()

def main():
    """ The main loop of the generator """
    args = parse_opt()

    # ---> General arguments
    input_path = args.input_path
    output_path = args.output_path
    use_highest_dim = args.use_highest_dim
    meta_path = args.meta_path
    delete_old_data = args.delete_old_data
    verbose = args.verbose
    # <--- General arguments

    # ---> Mesh arguments
    mesh_generator = args.mesh_generator
    mesh_folder = args.mesh_folder
    # <--- Mesh arguments

    # ---> GMSH arguments
    mesh_size = args.mesh_size
    # <--- GMSH arguments

    # ---> Features arguments
    features_folder = args.features_folder
    features_file_type = args.features_file_type
    # <--- Features arguments

    # ---> Stats arguments
    stats_folder = args.stats_folder
    only_stats = args.only_stats
    # <--- Stats arguments

    # ---> Directories verifications
    files = get_files_from_input_path(input_path)
    
    mesh_folder_dir = os.path.join(output_path, mesh_folder)
    features_folder_dir = os.path.join(output_path, features_folder)
    stats_folder_dir = os.path.join(output_path, stats_folder)
    create_dirs(output_path, mesh_folder_dir, features_folder_dir, stats_folder_dir)

    mesh_files = list_files(mesh_folder_dir, MESH_FORMATS, return_str=True)
    mesh_files = [mesh_file[(mesh_file.rfind('/') + 1):mesh_file.rindex('.')] for mesh_file in mesh_files]
    features_files = list_files(features_folder_dir, FEATURES_FORMATS, return_str=True)
    features_files = [f[(f.rfind('/') + 1):f.rindex('.')] for f in features_files]
    statistics_files = list_files(stats_folder_dir, STATS_FORMATS, return_str=True)
    statistics_files = [f[(f.rfind('/') + 1):f.rindex('.')] for f in statistics_files]

    i = 0
    while i < len(files):
        file_str = str(files[i])
        filename = file_str[(file_str.rfind('/') + 1):file_str.rindex('.')]
        if filename in mesh_files and filename in features_files and not delete_old_data:
            files.pop(i)
        else:
            i += 1
    # <--- Directories verifications

    # ---> Main loop
    if not only_stats:
        for idx, file in enumerate(files):
            file = str(file)
            filename = file.rsplit("/", maxsplit=1)[-1]
            output_name = output_name_converter(file, CAD_FORMATS)

            features_name = os.path.join(features_folder_dir, output_name)
            remove_by_filename(features_name, FEATURES_FORMATS)
            mesh_name = os.path.join(mesh_folder_dir, output_name)
            remove_by_filename(mesh_name, MESH_FORMATS)
            stats_name = os.path.join(stats_folder_dir, output_name)
            remove_by_filename(stats_name, STATS_FORMATS)

            vertical_up_axis = np.array([0., 0., 1.])
            unit_scale = 1000

            if meta_path != "":
                meta_filename = output_name + ".yml"
                meta_file = os.path.join(meta_path, meta_filename)
                if os.path.isfile(meta_file):
                    with open(meta_file, "r") as meta_file_object:
                        print("\n[Normalization] Using meta_file")
                        file_info = yaml.load(meta_file_object, Loader=yaml.FullLoader)

                        vertical_up_axis = np.array(file_info["vertical_up_axis"]) if \
                                            "vertical_up_axis" in file_info.keys() or  \
                                            file_info["vertical_up_axis"] is None \
                                                else np.array([0., 0., 1.])

                        unit_scale = file_info["unit_scale"] if "unit_scale" \
                                        in file_info.keys() else 1000
                        
            scale_to_mm = 1000/unit_scale
            unit_scale = 1000

            print(f'\nProcessing file - Model {filename} - [{idx+1}/{len(files)}]:')

            shape, geometries_data, mesh = processPythonOCC(file, generate_mesh=(mesh_generator=="occ"), \
                                                            use_highest_dim=use_highest_dim, scale_to_mm=scale_to_mm, \
                                                            debug=verbose)
            print("\n[PythonOCC] Done.")
            if mesh_generator == "gmsh":
                print('\n[GMSH]:')
                features, mesh = processGMSH(input_name=file, mesh_size=mesh_size, \
                                             features=features, mesh_name=mesh_name, \
                                                shape=shape, use_highest_dim=use_highest_dim, \
                                                    debug=verbose)
                print("\n[GMSH] Done.")

            print('\n[Normalization]')
            R = np.eye(3)
            t = np.zeros(3)
            s = 1./unit_scale
            if len(mesh["vertices"]) > 0:
                R = rotation_matrix_from_vectors(vertical_up_axis)
                mesh["vertices"] = (R @ mesh["vertices"].T).T
                t = computeTranslationVector(mesh["vertices"])
                mesh["vertices"] += t
                mesh["vertices"] *= s

            #TODO: need to use o3d mesh in whole code
            o3d_mesh = o3d.geometry.TriangleMesh()
            if len(mesh["vertices"]) > 0:
                o3d_mesh.vertices = o3d.utility.Vector3dVector(np.asarray(mesh['vertices']))
                o3d_mesh.triangles = o3d.utility.Vector3iVector(np.asarray(mesh['faces']))

            del mesh
            gc.collect()

            # normalizing and adding mesh data
            transforms = [{'rotation': R}, {'translation': t}, {'scale': s}]
            features = {'curves': [], 'surfaces': []}
            for edge_idx in range(len(geometries_data['curves'])):
                geometries_data['curves'][edge_idx]['geometry'].applyTransforms(transforms)

                mesh_data = geometries_data['curves'][edge_idx]['mesh_data']
                geometries_data['curves'][edge_idx]['geometry'].setMeshByGlobal(o3d_mesh, mesh_data)

                del geometries_data['curves'][edge_idx]['mesh_data']

            for face_idx in range(len(geometries_data['surfaces'])):
                geometries_data['surfaces'][face_idx]['geometry'].applyTransforms(transforms)

                mesh_data = geometries_data['surfaces'][face_idx]['mesh_data']
                geometries_data['surfaces'][face_idx]['geometry'].setMeshByGlobal(o3d_mesh, mesh_data)

                del geometries_data['surfaces'][face_idx]['mesh_data']

            print("\n[Normalization] Done.")

            print('\n[Generating statistics]')
            stats = generateStatistics(geometries_data, o3d_mesh)
            print("\n[Statistics] Done.")

            print('\n[Writing meshes]')
            writeMeshPLY(mesh_name, o3d_mesh)
            print('\n[Writing meshes] Done.')

            print('\n[Writing Features]')
             # creating features dict
            features = {'curves': [], 'surfaces': []}
            for edge_data in geometries_data['curves']:
                if edge_data['geometry'] is not None:
                    features['curves'].append(dict(edge_data['geometry'].toDict()))
            for face_data in geometries_data['surfaces']:
                if face_data['geometry'] is not None:
                    features['surfaces'].append(dict(face_data['geometry'].toDict()))
            writeFeatures(features_name=features_name, features=features, tp=features_file_type)
            print("\n[Writing Features] Done.")

            print('\n[Writing Statistics]')
            writeJSON(stats_name, stats)
            print("\n[Writing Statistics] Done.")

            print('\n[Generator] Process done.')

            #del stats
            del features
            del o3d_mesh
            gc.collect()
    else:
        print("Reading features list...")
        features = list(set(features_files) - set(statistics_files)) if not delete_old_data else \
                                                                    features_files
        for idx, feature_name in enumerate(features):
            print(f"\nProcessing file - Model {feature_name} - [{idx+1}/{len(features)}]:")

            stats_name = os.path.join(stats_folder_dir, feature_name)
            remove_by_filename(stats_name, STATS_FORMATS)

            mesh_p = Path(os.path.join(mesh_folder_dir, feature_name))

            mesh = loadMeshPLY(mesh_p)

            features_path = os.path.join(features_folder_dir, feature_name)
            features_data = loadFeatures(features_path, features_file_type)

            geometries = {'curves': [], 'surfaces': []}
            for curve_data in features_data['curves']:
                curve = CurveFactory.fromDict(curve_data)
                curve.setMeshByGlobal(mesh)
                geometries['curves'].append({'geometry': curve})
            for surface_data in features_data['surfaces']:
                surface = SurfaceFactory.fromDict(surface_data)
                surface.setMeshByGlobal(mesh)
                geometries['surfaces'].append({'geometry': surface})

            print("\nGenerating statistics...")
            stats = generateStatistics(geometries, mesh)

            print("Writing stats in statistic file...")
            writeJSON(stats_name, stats)

            del mesh, features_data, stats
            gc.collect()
        print(f"\nDone. {len(features)} were processed.")
    # <--- Main loop

if __name__ == '__main__':
    main()
