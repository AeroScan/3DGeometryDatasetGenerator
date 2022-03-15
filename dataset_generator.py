from lib.tools import writeFeatures, writeMeshOBJ
from lib.generate_gmsh import processGMSH
from lib.generate_pythonocc import processPythonOCC
from lib.features_factory import FeaturesFactory

import os
import time
import argparse
from pathlib import Path

from termcolor import colored

INPUT_FORMATS = ['.step', '.stp', '.STEP']

POSSIBLE_MESH_GENERATORS = ['occ' , 'gmsh']

def list_files(input_dir: str) -> list:
    files = []
    path = Path(input_dir)
    for file_path in path.glob('*'):
        if file_path.suffix.lower() in INPUT_FORMATS:
            files.append(file_path)
    return sorted(files)


def output_name_converter(input_path):
    filename = str(input_path).split('/')[-1]
    
    for f in INPUT_FORMATS:
        if f in filename:
            filename = filename.replace(f, '')
    return filename


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dataset Generator')
    parser.add_argument('input_path', type=str, default='.', help='path to input directory or input file.')
    parser.add_argument('output_dir', type=str, default='./results/', help='results directory.')
    parser.add_argument('-mg', '--mesh_generator', type=str, default='occ', help='method to be used for mesh generation. Possible methods: occ and gmsh. Default: occ')
    parser.add_argument('-mfn', '--mesh_folder_name', type=str, default = 'mesh', help='mesh folder name. Default: mesh.')
    parser.add_argument('-ffn', '--features_folder_name', type=str, default = 'features', help='features folder name. \
    Default: features.')
    parser.add_argument('-ms', '--mesh_size', type=float, default=1e22, help='mesh size max. Default: 1e+22.')
    parser.add_argument('-nuhd', '--no_use_highest_dim', action='store_false', help='use highest dim to explore file topology. Default: True.')
    parser.add_argument('-fft', '--features_file_type', type=str, default='json', help='type of the file to save the dict of features. Default: json. Possible types: json, yaml and pkl.')
    parser.add_argument('-nud', '--no_use_debug', action='store_false', help='use debug mode in PythonOCC and GMSH libraries. Default: True.')
    args = vars(parser.parse_args())

    input_path = args['input_path']
    output_directory = args['output_dir']
    mesh_folder_name = args['mesh_folder_name']
    features_folder_name = args['features_folder_name']
    mesh_size = args['mesh_size']
    use_highest_dim = args['no_use_highest_dim']
    features_file_type = args['features_file_type']
    use_debug = args['no_use_debug']
    mesh_generator = args['mesh_generator'].lower()

    assert mesh_generator in POSSIBLE_MESH_GENERATORS

    # Test the directories
    if os.path.exists(input_path):
        if os.path.isdir(input_path):
            files = list_files(input_path)
        else:
            files = [input_path]
    else:
        print('[Generator Error] Input path not found')
        exit()

    if not os.path.isdir(output_directory):
        os.mkdir(output_directory)

    mesh_folder_dir = os.path.join(output_directory, mesh_folder_name)
    features_folder_dir = os.path.join(output_directory, features_folder_name)
    
    if not os.path.isdir(mesh_folder_dir):
        os.mkdir(mesh_folder_dir)
    if not os.path.isdir(features_folder_dir):
        os.mkdir(features_folder_dir)

    # Main loop
    error_counter = 0
    processorErrors = []
    time_initial = time.time()
    for file in files:
        file = str(file)
        output_name = output_name_converter(file)
        mesh_name = os.path.join(mesh_folder_dir, output_name)
        print('\n[Generator] Processing file ' + file + '...')
        
        print('\n+-----------PythonOCC----------+')
        shape, features, mesh = processPythonOCC(file, mesh_generator=mesh_generator, use_highest_dim=use_highest_dim, debug=use_debug)

        if mesh_generator == 'gmsh':
            print('\n+-------------GMSH-------------+')
            processGMSH(input_name=file, mesh_size=mesh_size, features=features, mesh_name=mesh_name, shape=shape, use_highest_dim=use_highest_dim, debug=use_debug)
        elif mesh_generator == 'occ':
            if mesh is not {}:
                print(f'\nWriting meshes in obj file...')
                writeMeshOBJ(mesh_name, mesh)

        features = FeaturesFactory.getListOfDictFromPrimitive(features)
        print(f'\nWriting Features in {features_file_type} format...')
        features_name = os.path.join(features_folder_dir, output_name)
        writeFeatures(features_name=features_name, features=features, tp=features_file_type)
        print('\n[Generator] Process done.')

    time_finish = time.time()
    
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