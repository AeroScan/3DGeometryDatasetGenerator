import json
from lib.tools import (
    computeTranslationVector,
    writeFeatures, 
    writeMeshOBJ, 
    computeRotationMatrix,
    list_files,
    output_name_converter,
    writeJSON,
    loadMeshOBJ,
    loadFeatures
    )
from lib.generate_gmsh import processGMSH
from lib.generate_pythonocc import processPythonOCC
from lib.features_factory import FeaturesFactory
from lib.generate_statistics import (
    generateStatistics,
    generateAreaFromSurface
)

import shutil
import os
import time
import argparse
import math
import numpy as np
from pathlib import Path

from termcolor import colored

import gc

CAD_FORMATS = ['.step', '.stp', '.STEP']
MESH_FORMATS = ['.OBJ', '.obj']
FEATURES_FORMATS = ['.pkl', '.PKL', '.yml', '.yaml', '.YAML', '.json', '.JSON']

POSSIBLE_MESH_GENERATORS = ['occ' , 'gmsh']

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dataset Generator')
    parser.add_argument('input_path', type=str, default='.', help='path to input directory or input file.')
    parser.add_argument('output_dir', type=str, default='./results/', help='results directory.')
    parser.add_argument('-d_dt', '--delete_old_data', action='store_true', help='delete old data.')
    parser.add_argument('-mg', '--mesh_generator', type=str, default='occ', help='method to be used for mesh generation. Possible methods: occ and gmsh. Default: occ')
    parser.add_argument('-mfn', '--mesh_folder_name', type=str, default = 'mesh', help='mesh folder name. Default: mesh.')
    parser.add_argument('-ffn', '--features_folder_name', type=str, default = 'features', help='features folder name. \
    Default: features.')
    parser.add_argument('-sfn', '--statistics_folder_name', type=str, default = 'stats', help='stats folder name. \
    Default: stats.')
    parser.add_argument('-ms', '--mesh_size', type=float, default=1e22, help='mesh size max. Default: 1e+22.')
    parser.add_argument('-nuhd', '--no_use_highest_dim', action='store_false', help='use highest dim to explore file topology. Default: True.')
    parser.add_argument('-fft', '--features_file_type', type=str, default='json', help='type of the file to save the dict of features. Default: json. Possible types: json, yaml and pkl.')
    parser.add_argument('-nud', '--no_use_debug', action='store_false', help='use debug mode in PythonOCC and GMSH libraries. Default: True.')
    parser.add_argument('-n', '--normalize', action='store_false', help='no normalize the shape. Center in origin, scale in meters and axis z on the top. Default: True')
    parser.add_argument('-s', '--only_stats', action='store_true', help='set the dataset generator to generate only the statistics. Default: False')
    args = vars(parser.parse_args())

    input_path =                args['input_path']
    output_directory =          args['output_dir']
    delete_old_data =           args['delete_old_data']
    mesh_folder_name =          args['mesh_folder_name']
    features_folder_name =      args['features_folder_name']
    statistics_folder_name =    args['statistics_folder_name']
    mesh_size =                 args['mesh_size']
    use_highest_dim =           args['no_use_highest_dim']
    features_file_type =        args['features_file_type']
    use_debug =                 args['no_use_debug']
    mesh_generator =            args['mesh_generator'].lower()
    normalize_shape =           args['normalize']
    only_stats =                args["only_stats"]

    assert mesh_generator in POSSIBLE_MESH_GENERATORS

    # Test the directories
    if os.path.exists(input_path):
        if os.path.isdir(input_path):
            files = list_files(input_path, CAD_FORMATS)
        else:
            files = [input_path]
    else:
        print('[Generator Error] Input path not found')
        exit()

    os.makedirs(output_directory, exist_ok=True)

    mesh_folder_dir = os.path.join(output_directory, mesh_folder_name)
    features_folder_dir = os.path.join(output_directory, features_folder_name)
    statistics_folder_dir = os.path.join(output_directory, statistics_folder_name)
    
    os.makedirs(mesh_folder_dir, exist_ok=True)
    os.makedirs(features_folder_dir, exist_ok=True)
    os.makedirs(statistics_folder_dir, exist_ok=True)

    mesh_files = list_files(mesh_folder_dir, MESH_FORMATS, return_str=True)
    mesh_files = [f[(f.rfind('/') + 1):f.rindex('.')] for f in mesh_files]
    features_files = list_files(features_folder_dir, FEATURES_FORMATS, return_str=True)
    features_files = [f[(f.rfind('/') + 1):f.rindex('.')] for f in features_files]

    i = 0
    while i < len(files):
        f = str(files[i])
        filename = f[(f.rfind('/') + 1):f.rindex('.')]
        if filename in mesh_files and filename in features_files and not delete_old_data:
            files.pop(i)
        else:
            i += 1

    # ---------------------------------------------------------------------------------------------------- #
    error_counter = 0
    processorErrors = []
    if not only_stats:
        # Main loop
        time_initial = time.time()
        for file in files:
            file = str(file)
            output_name = output_name_converter(file, CAD_FORMATS)
            mesh_name = os.path.join(mesh_folder_dir, output_name)
            print('\n[Generator] Processing file ' + file + '...')
            
            print('\n+-----------PythonOCC----------+')
            shape, features, mesh = processPythonOCC(file, generate_mesh=(mesh_generator=='occ'), use_highest_dim=use_highest_dim, debug=use_debug)

            if mesh_generator == 'gmsh':
                print('\n+-------------GMSH-------------+')
                features, mesh = processGMSH(input_name=file, mesh_size=mesh_size, features=features, mesh_name=mesh_name, shape=shape, use_highest_dim=use_highest_dim, debug=use_debug)
            
            if normalize_shape:
                print('\n[Generator] Normalization in progress...')
                vertices = mesh['vertices']

                R = computeRotationMatrix(math.pi/2, np.array([1., 0., 0.]))
                vertices = (R @ vertices.T).T

                t = computeTranslationVector(vertices)
                vertices += t

                s = 1./1000
                vertices *= s

                mesh['vertices'] = vertices

                FeaturesFactory.normalizeShape(features, R=R, t=t, s=s)

            print(f'\nGenerating Stats...')            
            stats = generateStatistics(features, mesh)

            print(f'\nWriting meshes in obj file...')
            writeMeshOBJ(mesh_name, mesh)

            print(f'\nWriting Features in {features_file_type} format...')
            features = FeaturesFactory.getListOfDictFromPrimitive(features)
            features_name = os.path.join(features_folder_dir, output_name)
            writeFeatures(features_name=features_name, features=features, tp=features_file_type)

            print(f'\nWriting Statistics in json file..')
            stats_name = os.path.join(statistics_folder_dir, (output_name + '.json'))
            writeJSON(stats_name, stats)    

            print('\n[Generator] Process done.')

            #del stats
            del features
            del mesh
            gc.collect()

        time_finish = time.time()

    else: 
        time_initial = time.time()

        # Remove stats files
        shutil.rmtree(statistics_folder_dir)

        # List files
        # meshes = [mesh for mesh in mesh_folder.glob("*.obj")]
        features = [str(feature).replace('.'+str(features_file_type), '') for feature in Path(features_folder_dir).glob("*."+str(features_file_type))]

        for feature in features:
            # Find the correspondent mesh
            model_name = str(feature).split("/")[-1]
            mesh_p = Path(os.path.join(mesh_folder_dir, model_name))

            mesh = loadMeshOBJ(mesh_p)

            features_data = loadFeatures(feature, features_file_type)

            stats = generateStatistics(features_data, mesh, only_stats=only_stats)

            print(f'\nWriting Statistics in json file..')
            os.makedirs(statistics_folder_dir, exist_ok=True)
            stats_name = os.path.join(statistics_folder_dir, (model_name + '.json'))
            writeJSON(stats_name, stats)

        time_finish = time.time()
    # ---------------------------------------------------------------------------------------------------- #

    print('\n\n+-----------LOG--------------+')
    print(f'Processed files: {len(files) - error_counter}')
    print(f'Unprocessed files: {error_counter}')
    print(f'List of unprocessed files: {processorErrors}')
    print(f'Time used: {time_finish - time_initial}')
    print('+----------------------------+')

    if processorErrors:
        with open('./files_unprocessed.txt', 'w') as f:
            for item in processorErrors:
                s = ''
                s = str(item) + '\n'
                f.write(s)
        print(colored('\n[LOG] Unprocessed files listed in: files_unprocessed.txt\n', 'blue'))