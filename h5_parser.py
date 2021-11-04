from yaml import load
import h5py
import pypcd

from tqdm import tqdm
import argparse

import numpy as np

from tools import loadFeatures

from os import listdir, mkdir, system, remove
from os.path import isfile, join, exists

def generatePCD2LSSPFN(pc_filename, pc_files, mps_ns, lpcp_r, lpcp_nl, mesh_filename=None): 
    for resolution in lpcp_r:
        point_position = pc_filename.rfind('.')
        str_resolution = str(resolution).replace('.','-')
        pc_filename_truth = f'{pc_filename[:point_position]}_{str_resolution}{pc_filename[point_position:]}'
        pc_filename_noisy = f'{pc_filename[:point_position]}_{str_resolution}_noisy{pc_filename[point_position:]}'

        filtered = False
        if pc_filename_truth not in pc_files:
            if not exists(pc_filename):
                if mesh_filename is None:
                    return False
                system(f'mesh_point_sampling {mesh_filename} {pc_filename} --n_samples {mps_ns} --write_normals --no_vis_result')
            system(f'large_point_cloud_preprocessing {pc_filename} {pc_filename} --vg {resolution} --centralize --align')
            filtered = True
            system(f'large_point_cloud_preprocessing {pc_filename} {pc_filename_truth} --cube_reescale_factor 1')

        if pc_filename_noisy not in pc_files:
            if not exists(pc_filename):
                if mesh_filename is None:
                    return False
                system(f'mesh_point_sampling {mesh_filename} {pc_filename} --n_samples {mps_ns} --write_normals --no_vis_result')
            if filtered:
               system(f'large_point_cloud_preprocessing {pc_filename} {pc_filename} --vg {resolution} --centralize --align')
            system(f'large_point_cloud_preprocessing {pc_filename} {pc_filename_noisy} --noise_limit {lpcp_nl} --cube_reescale_factor 1')
    if exists(pc_filename):
        remove(pc_filename)
    return True

def createH5File(filename):
    return h5py.File(filename, 'w')

def addFeatures2H5(features_data, h5_file, curve_types, surface_types):
    gt_types = []
    for feature in tqdm(features_data['curves']):
        if feature['type'] in curve_types:
            gt_types.append(curve_types.index(feature['type']))

    for feature in tqdm(features_data['surfaces']):
        if feature['type'] in surface_types:
            gt_types.append(surface_types.index(feature['type']) + len(curve_types))

    gt_types = np.array(gt_types)

    h5_file.create_dataset('gt_types', data=gt_types)

    return h5_file

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Converts a dataset from OBJ and YAML to HDF5')
    parser.add_argument('folder', type=str, help='dataset folder.')
    parser.add_argument('--h5_folder_name', type=str, default = 'h5', help='h5 folder name.')
    parser.add_argument('--mesh_folder_name', type=str, default = 'mesh', help='mesh folder name.')
    parser.add_argument('--features_folder_name', type=str, default = 'features', help='features folder name.')
    parser.add_argument('--pc_folder_name', type=str, default = 'pc', help='point cloud folder name.')
    parser.add_argument('--curve_types', type=str, default = '', help='types of curves to generate. Default = ')
    parser.add_argument('--surface_types', type=str, default = 'plane,cylinder,cone,sphere', help='types of surfaces to generate. Default = plane,cylinder,cone,sphere')
    parser.add_argument('-mps_ns', '--mesh_point_sampling_n_samples', type=int, default= '1000000', help='n_samples param for mesh_point_sampling execution, if necessary. Default: 100000000.')
    parser.add_argument('-lpcp_r', '--large_point_cloud_preprocessing_resolutions', type=str, default= '0.01', help='list of resolutions for large_point_cloud_preprocessing execution, if necessary. Default: 0.01.')
    parser.add_argument('-lpcp_nl', '--large_point_cloud_preprocessing_noise_limit', type=float, default= 0.01, help='noise_limit for large_point_cloud_preprocessing execution, if necessary. Default: 0.01.')

    args = vars(parser.parse_args())

    folder_name = args['folder']
    h5_folder_name = join(folder_name, args['h5_folder_name'])
    mesh_folder_name = join(folder_name, args['mesh_folder_name'])
    features_folder_name = join(folder_name, args['features_folder_name'])
    pc_folder_name = join(folder_name, args['pc_folder_name'])
    curve_types = args['curve_types'].split(',')
    surface_types = args['surface_types'].split(',')
    mps_ns = args['mesh_point_sampling_n_samples']
    lpcp_r = sorted([float(x) for x in args['large_point_cloud_preprocessing_resolutions'].split(',')])
    lpcp_nl = args['large_point_cloud_preprocessing_noise_limit']

    mesh_files = []
    features_files = []
    pc_folders = []
    if exists(mesh_folder_name):
        mesh_files = sorted([f for f in listdir(mesh_folder_name) if isfile(join(mesh_folder_name, f))])
    if exists(features_folder_name):
        features_files = sorted([f for f in listdir(features_folder_name) if isfile(join(features_folder_name, f))])
    if exists(pc_folder_name):
        pc_folders = sorted([f for f in listdir(pc_folder_name) if not isfile(join(pc_folder_name, f))])

    if len(features_files) == 0:
        print('There is no features file to process.')
        exit()
    
    if len(mesh_files) == 0 and len(pc_folders) == 0:
        print('There is no mesh or point cloud file.')
        exit()

    if not exists(h5_folder_name):
        print(h5_folder_name)
        mkdir(h5_folder_name)

    for features_filename in features_files:
        print('\nProcessing ' + features_filename + '...\n')


        point_position = features_filename.rfind('.')
        filename = features_filename[:point_position]
        feature_ext =  features_filename[(point_position + 1):]
        features_data = loadFeatures(join(features_folder_name, filename), feature_ext)


        h5_filename = join(h5_folder_name, filename + '.h5')
        h5_file = createH5File(h5_filename)
        h5_file = addFeatures2H5(features_data, h5_file, curve_types, surface_types)


        pc_filename = filename + '.pcd'
        mesh_filename = filename + '.obj'
        
        if mesh_filename in mesh_files:
            index = mesh_files.index(mesh_filename)
            mesh_files.pop(index)

            if not exists(pc_folder_name):
                mkdir(pc_folder_name)
            pc_folder_files_name = join(pc_folder_name, filename)
            if not exists(pc_folder_files_name):
                mkdir(pc_folder_files_name)
            pc_folder_files = sorted([join(pc_folder_files_name, f) for f in listdir(pc_folder_files_name) if isfile(join(pc_folder_files_name, f))])
            generatePCD2LSSPFN(join(pc_folder_files_name, pc_filename), pc_folder_files, mps_ns, lpcp_r, lpcp_nl, mesh_filename=join(mesh_folder_name, mesh_filename))

        elif filename in pc_folders:
            index = pc_folders.index(filename)
            pc_folders.pop(index)
            pc_folder_files_name = join(pc_folder_name, filename)
            pc_folder_files = sorted([join(pc_folder_files_name, f) for f in listdir(pc_folder_files_name) if isfile(join(pc_folder_files_name, f))])
            if generatePCD2LSSPFN(join(pc_folder_files_name, pc_filename), pc_folder_files, mps_ns, lpcp_r, lpcp_nl):
                print(f'\n{filename} has no OBJ and not has all PCD files.')
                continue

        else:
            print(f'\nFeature {filename} has no PCD or OBJ to use.')
            continue

        h5_file.close()
        print('\nProcess done.')