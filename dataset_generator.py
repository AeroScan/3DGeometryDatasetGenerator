from tools import writeYAML
from generate_gmsh import processGMSH
from generate_pythonocc import processPythonOCC

import os
import time
import argparse
from pathlib import Path

INPUT_FORMATS = ['.step', '.stp']

def list_files(input_dir: str) -> list:
    files = []
    path = Path(input_directory)
    for file_path in path.glob('*'):
        if file_path.suffix.lower() in INPUT_FORMATS:
            files.append(file_path)
    return files

def output_name_converter(input_path):
    filename = str(input_path).split('/')[-1]
    
    for f in INPUT_FORMATS:
        if f in filename:
            filename = filename.replace(f, '')
    return filename

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dataset Generator')
    parser.add_argument('input_dir', type=str, default='.', help='directory of input files.')
    parser.add_argument('output_dir', type=str, default='./results/', help='results directory')
    parser.add_argument('--mesh_size', type=float, default=1e22, help='mesh size max. default: 1e+22')
    parser.add_argument("-l", "--log", action="store_true", help='show log of results')
    args = vars(parser.parse_args())

    input_directory = args['input_dir']
    output_directory = args['output_dir']
    mesh_size = args['mesh_size']
    log = args['log']

    # List files
    files = list_files(input_directory)

    # Test the directories
    if not os.path.isdir(output_directory):
        print('Output directory not found, changing to "./results/"...')
        output_directory = './results/'
    if not os.path.isdir(input_directory):
        print('input directory not found, trying to use directory "."...')
        input_directory = '.'

    error_counter = 0
    processorErrors = []
    # Main loop
    time_initial = time.time()
    for file in files:
        file = str(file)
        output_name = output_name_converter(file)
        if '/' is not output_directory[-1:]:
            output_directory = output_directory + '/'
        
        try:
            print('\nProcessing file ' + file + '...')

            print('\n+-----PythonOCC-----+')
            features = processPythonOCC(file)

            print('\n+-----GMSH-----+')
            output_obj = output_directory + 'obj/'
            if not os.path.isdir(output_obj):
                os.mkdir(output_obj)
            output_obj += output_name
            processGMSH(input_name=file, mesh_size=mesh_size, features=features, output_name=output_obj)

            print('\n+-----Writing YAML results-----+')
            output_yaml = output_directory + 'yaml/'
            if not os.path.isdir(output_yaml):
                os.mkdir(output_yaml)
            output_yaml += output_name
            writeYAML(output_name=output_yaml, features=features)
            print('\nProcess done.')
        except:
            processorErrors.append(file)
            error_counter += 1
    time_finish = time.time()
    
    if log:
        print('\n\n+----------Log----------+')
        print(f'Processed files: {len(files) - error_counter}')
        print(f'Unprocessed files: {error_counter}')
        print(f'List of unprocessed files: {processorErrors}')
        print(f'Time used: {time_finish - time_initial}')
        print('+---------------------------+')

    

