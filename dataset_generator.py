from tools import writeFeatures
from generate_gmsh import processGMSH
from generate_pythonocc import processPythonOCC

import os
import time
import argparse
from pathlib import Path

from termcolor import colored

INPUT_FORMATS = ['.step', '.stp']

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
    parser.add_argument('--mesh_folder_name', type=str, default = 'mesh', help='mesh folder name. Default: mesh.')
    parser.add_argument('--features_folder_name', type=str, default = 'features', help='features folder name. Default: features.')
    parser.add_argument('--mesh_size', type=float, default=1e22, help='mesh size max. Default: 1e+22.')
    parser.add_argument('--no_use_highest_dim', action='store_false', help='use highest dim to explore file topology. Default: True.')
    parser.add_argument('--features_file_type', type=str, default='json', help='type of the file to save the dict of features. Default: json. Possible types: json, yaml and pkl.')
    args = vars(parser.parse_args())

    input_path = args['input_path']
    output_directory = args['output_dir']
    mesh_folder_name = args['mesh_folder_name']
    features_folder_name = args['features_folder_name']
    mesh_size = args['mesh_size']
    use_highest_dim = args['no_use_highest_dim']
    features_file_type = args['features_file_type']

    # Test the directories
    if os.path.exists(input_path):
        if os.path.isdir(input_path):
            files = list_files(input_path)
        else:
            files = [input_path]
    else:
        print('input path not found')
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

        try:
            print('\nProcessing file ' + file + '...')

            print('\n+-----------PythonOCC----------+')
            shape, features = processPythonOCC(file, use_highest_dim=use_highest_dim)

            print('\n+-------------GMSH-------------+')
            mesh_name = os.path.join(mesh_folder_dir, output_name)
            processGMSH(input_name=file, mesh_size=mesh_size, features=features, mesh_name=mesh_name, shape=shape, use_highest_dim=use_highest_dim)

            print('\nWriting Features...')
            features_name = os.path.join(features_folder_dir, output_name)
            writeFeatures(features_name=features_name, features=features, tp=features_file_type)
            print('\nProcess done.')
            
        except Exception as e:
            print(colored(f'Error   : {e}', 'red'))
            processorErrors.append(file)
            error_counter += 1

    time_finish = time.time()
    
    print('\n\n+-----------LOG--------------+')
    print(f'Processed files: {len(files) - error_counter}')
    print(f'Unprocessed files: {error_counter}')
    print(f'List of unprocessed files: {processorErrors}')
    print(f'Time used: {time_finish - time_initial}')
    print('+----------------------------+')