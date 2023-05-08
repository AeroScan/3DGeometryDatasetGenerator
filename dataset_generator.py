import shutil
import os
import time
import argparse
from pathlib import Path
import gc
import numpy as np
from termcolor import colored
from tqdm import tqdm
import yaml
from lib.tools import (
    computeTranslationVector,
    writeFeatures,
    writeMeshOBJ,
    rotation_matrix_from_vectors,
    get_files_from_input_path,
    output_name_converter,
    writeJSON,
    loadMeshOBJ,
    loadFeatures,
    create_dirs,
    list_files)
from lib.generate_gmsh import processGMSH
from lib.generate_pythonocc import processPythonOCC
from lib.features_factory import FeaturesFactory
from lib.generate_statistics import generateStatistics

CAD_FORMATS = ['.step', '.stp', '.STEP']
MESH_FORMATS = ['.OBJ', '.obj']
FEATURES_FORMATS = ['.pkl', '.PKL', '.yml', '.yaml', '.YAML', '.json', '.JSON']
STATISTICS_FORMATS = [".json", ".JSON"]

def parse_opt():
    """ Function to organize all the possible arguments """
    parser = argparse.ArgumentParser(description='Dataset Generator')
    parser.add_argument('input_path', type=str, default='./dataset/step/', help='Path to the input directory')
    parser.add_argument('output_path', type=str, default='./results/', help='Path to the output directory where processed files will be saved')
    parser.add_argument('--meta_path', type=str, default='', help="Path to the directory containing metadata information such as file URLs, author names, vertical up axis of the model, and model type (large or small plant and large or small part)")
    parser.add_argument('--delete_old_data', action='store_true', help='Boolean flag indicating whether to delete old data in the output directory')
    parser.add_argument('--verbose', action='store_true', help='Boolean flag indicating whether to run the code in debug mode.')

    # Meta parser general
    mesh_parser = parser.add_argument_group("Mesh commands")
    mesh_parser.add_argument("--mesh_generator", type=str, default="occ", choices=["occ", "gmsh"], help="Name of the mesh generator to use")
    mesh_parser.add_argument('--mesh_folder', type=str or None, default=None, help='Path to the folder where the mesh will be saved')
    mesh_parser.add_argument('use_highest_dim', action='store_true', help='Boolean flag indicating whether to use the highest dimension of the mesh')
    mesh_parser.add_argument('--mesh_size', type=float, default=1e+22, help="The edge size of the mesh, used in conjunction with the GMSH mesh generator")

    # Feature parser general
    feature_parser = parser.add_argument_group("Feature commands")
    feature_parser.add_argument('--features_folder', type=str or None, default=None, help='Path to the folder containing the features to be extracted')
    feature_parser.add_argument('--features_file_type', type=str, default='json', choices=["json", "pkl", "yaml"], help='The file type of the features')

    # Stats parser general
    stats_parser = parser.add_argument_group("Stats commands")
    stats_parser.add_argument('--statistics_folder', type=str or None, default=None, help='Path to the folder where statistics will be saved')
    stats_parser.add_argument('--only_stats', action='store_true', help='Boolean flag indicating whether to only generate statistics without processing the data.')

    return parser.parse_args()

def main():
    """ The main loop of the generator """
    args = parse_opt()

    # ---> General arguments
    input_path = args.input_path
    output_path = args.output_path
    meta_path = args.meta_path
    delete_old_data = args.delete_old_data
    verbose = args.verbose
    # <--- General arguments

    # ---> Mesh arguments
    mesh_generator = args.mesh_generator
    mesh_folder = args.mesh_folder
    use_highest_dim = args.use_highest_dim
    mesh_size = args.mesh_size
    # <--- Mesh arguments

    # ---> Features arguments
    features_folder = args.features_folder
    features_file_type = args.features_file_type
    # <--- Features arguments

    # ---> Stats arguments
    statistics_folder = args.statistics_folder
    only_stats = args.only_stats
    # <--- Stats arguments

    # ---> Directories verifications
    files = get_files_from_input_path(input_path)

    mesh_folder_dir = os.path.join(output_path, mesh_folder if mesh_folder is not None else f"{output_path}/mesh")
    features_folder_dir = os.path.join(output_path, features_folder if features_folder is not None else f"{output_path}/features")
    statistics_folder_dir = os.path.join(output_path, statistics_folder if statistics_folder is not None else f"{output_path}/stats")
    create_dirs(output_path, mesh_folder_dir, features_folder_dir, statistics_folder_dir)

    mesh_files = list_files(mesh_folder_dir, MESH_FORMATS, return_str=True)
    mesh_files = [mesh_file[(mesh_file.rfind('/') + 1):mesh_file.rindex('.')] for mesh_file in mesh_files]
    features_files = list_files(features_folder_dir, FEATURES_FORMATS, return_str=True)
    features_files = [f[(f.rfind('/') + 1):f.rindex('.')] for f in features_files]
    statistics_files = list_files(statistics_folder_dir, STATISTICS_FORMATS, return_str=True)
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
            mesh_name = os.path.join(mesh_folder_dir, output_name)
            print(f'\nProcessing file - Model {filename} - [{idx+1}/{len(files)}]:')

            shape, features, mesh = processPythonOCC(file, generate_mesh=(mesh_generator=="occ"), \
                                                     use_highest_dim=use_highest_dim, \
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
            vertical_up_axis = np.array([0., 0., 1.])
            unit_scale = 1000

            if meta_path != "":
                meta_filename = output_name + ".yml"
                meta_file = os.path.join(meta_path, meta_filename)

                with open(meta_file, "r") as meta_file_object:
                    print("\n[Normalization] Using meta_file")
                    file_info = yaml.load(meta_file_object, Loader=yaml.FullLoader)

                    vertical_up_axis = np.array(file_info["vertical_up_axis"]) if \
                                        "vertical_up_axis" in file_info.keys() or  \
                                        file_info["vertical_up_axis"] is None \
                                            else np.array([0., 0., 1.])
                    
                    unit_scale = file_info["unit_scale"] if "unit_scale" \
                                    in file_info.keys() else 1000
                    
            vertices = mesh["vertices"]

            R = rotation_matrix_from_vectors(vertical_up_axis)

            vertices = (R @ vertices.T).T

            t = computeTranslationVector(vertices)
            vertices += t

            s = 1./unit_scale
            vertices *= s

            FeaturesFactory.normalizeShape(features, R=R, t=t, s=s)
            print("\n[Normalization] Done.")

            print('\n[Generating statistics]')
            stats = generateStatistics(features, mesh)
            print("\n[Statistics] Done.")

            print('\n[Writing meshes]')
            writeMeshOBJ(mesh_name, mesh)
            print('\n[Writing meshes] Done.')

            print(f'\n[Writing Features]')
            features = FeaturesFactory.getListOfDictFromPrimitive(features)
            features_name = os.path.join(features_folder_dir, output_name)
            writeFeatures(features_name=features_name, features=features, tp=features_file_type)
            print("\n[Writing Features] Done.")

            print('\n[Writing Statistics]')
            stats_name = os.path.join(statistics_folder_dir, (output_name + '.json'))
            writeJSON(stats_name, stats)
            print("\n[Writing Statistics] Done.")

            print('\n[Generator] Process done.')

            del stats
            del features
            del mesh
            gc.collect()
    else:
        print("\n[Reading features]")
        features = [str(feature).replace('.'+str(features_file_type), '') for feature in \
                    Path(features_folder_dir).glob("*."+str(features_file_type))]
        print("\n[Reading features] Done.")

        for idx, feature in enumerate(features):
            model_name = str(feature).split("/")[-1]
            print(f"\nProcessing file - Model {model_name} - [{idx+1}/{len(features)}]:")
            if model_name in statistics_files and not delete_old_data:
                print(f"\nStats of the model {model_name} already exist.")
                continue

            mesh_p = Path(os.path.join(mesh_folder_dir, model_name))

            print("\n[Load mesh]")
            mesh = loadMeshOBJ(mesh_p)
            print("\n[Load mesh] Done.")

            print("\n[Load feature]")
            features_data = loadFeatures(feature, features_file_type)
            print("\n[Load feature] Done.")

            print("\n[Generating statistics]")
            stats = generateStatistics(features_data, mesh, only_stats=only_stats)
            print("\n[Generating statistics] Done.")

            print('\n[Writing Statistics]')
            os.makedirs(statistics_folder_dir, exist_ok=True)
            stats_name = os.path.join(statistics_folder_dir, (model_name + '.json'))
            writeJSON(stats_name, stats)
            print('\n[Writing Statistics] Done.')

            del mesh, features_data, stats
            gc.collect()
    # <--- Main loop

if __name__ == '__main__':
    main()
