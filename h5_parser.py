from yaml import load
import h5py
import pypcd

from tqdm import tqdm
import argparse

import numpy as np

from pypcd import pypcd

from tools import loadFeatures

from os import listdir, mkdir, system, remove
from os.path import isfile, join, exists

import gc

def generatePCD2LSSPFN(pc_filename, pc_files, mps_ns, lpcp_r, lpcp_nl, mesh_filename=None): 
    pc_files_out = []
    for resolution in lpcp_r:
        point_position = pc_filename.rfind('.')
        str_resolution = str(resolution).replace('.','-')
        pc_filename_gt = f'{pc_filename[:point_position]}_{str_resolution}_gt{pc_filename[point_position:]}'
        pc_filename_noisy = f'{pc_filename[:point_position]}_{str_resolution}_noisy{pc_filename[point_position:]}'

        pc_files_out.append(pc_filename_noisy)
        pc_files_out.append(pc_filename_gt)

        filtered = False
        if pc_filename_gt not in pc_files:
            if not exists(pc_filename):
                if mesh_filename is None:
                    return []
                system(f'mesh_point_sampling {mesh_filename} {pc_filename} --n_samples {mps_ns} --write_normals --no_vis_result')
            system(f'large_point_cloud_preprocessing {pc_filename} {pc_filename} --vg {resolution} --centralize --align')
            filtered = True
            system(f'large_point_cloud_preprocessing {pc_filename} {pc_filename_gt} --cube_reescale_factor 1')

        if pc_filename_noisy not in pc_files:
            if not exists(pc_filename):
                if mesh_filename is None:
                    return []
                system(f'mesh_point_sampling {mesh_filename} {pc_filename} --n_samples {mps_ns} --write_normals --no_vis_result')
            if filtered:
               system(f'large_point_cloud_preprocessing {pc_filename} {pc_filename} --vg {resolution} --centralize --align')
            system(f'large_point_cloud_preprocessing {pc_filename} {pc_filename_noisy} --noise_limit {lpcp_nl} --cube_reescale_factor 1')
    if exists(pc_filename):
        remove(pc_filename)
    return pc_files_out

def generateH52LSSPFN(pc_files, features_data, h5_file, surface_types):
    print(pc_files)
    pc_filename_gt = ''
    pc_filename_noisy = ''
    for f in pc_files:
        if 'gt' in f:
            pc_filename_gt = f
        elif 'noisy' in f:
            pc_filename_noisy = f
    if pc_filename_noisy == '' or pc_filename_gt == '':
        print(f'{pc_files} has no gt or noisy cloud.')
        return None
        
    pc = pypcd.PointCloud.from_path(pc_filename_gt).pc_data

    gt_points = np.ndarray(shape=(pc['x'].shape[0], 3), dtype=np.float64)
    gt_points[:, 0] = pc['x']
    gt_points[:, 1] = pc['y']
    gt_points[:, 2] = pc['z']
    
    gt_normals = np.ndarray(shape=(pc['x'].shape[0], 3), dtype=np.float64)
    gt_normals[:, 0] = pc['normal_x']
    gt_normals[:, 1] = pc['normal_y']
    gt_normals[:, 2] = pc['normal_z']

    gt_labels = pc['label']

    pc = pypcd.PointCloud.from_path(pc_filename_noisy).pc_data

    noisy_points = np.ndarray(shape=(pc['x'].shape[0], 3), dtype=np.float64)
    noisy_points[:, 0] = pc['x']
    noisy_points[:, 1] = pc['y']
    noisy_points[:, 2] = pc['z']

    del pc
    gc.collect()

    print(gt_points)
    print(noisy_points)


    #h5_file.create_dataset('gt_types', data=gt_types)

    return h5_file

def createH5File(filename):
    return h5py.File(filename, 'w')

def filterFeaturesData(feature_data, curve_types, surface_types):
    i = 0
    while i < len(features_data['curves']):
        feature = features_data['curves'][i]
        if feature['type'] not in curve_types:
            features_data['curves'].pop(i)
        else:
            i+=1

    i = 0
    while i < len(features_data['surfaces']):
        feature = features_data['surfaces'][i]
        if feature['type'] not in surface_types:
            features_data['surfaces'].pop(i)
        else:
            i+=1

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
    parser.add_argument('-lpcp_r', '--large_point_cloud_preprocessing_resolutions', type=str, default= '10', help='list of resolutions for large_point_cloud_preprocessing execution, if necessary. Default: 10.')
    parser.add_argument('-lpcp_nl', '--large_point_cloud_preprocessing_noise_limit', type=float, default= 10, help='noise_limit for large_point_cloud_preprocessing execution, if necessary. Default: 10.')

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

        pc_filename = filename + '.pcd'
        mesh_filename = filename + '.obj'
        
        pc_folder_files = []
        if mesh_filename in mesh_files:
            index = mesh_files.index(mesh_filename)
            mesh_files.pop(index)

            if not exists(pc_folder_name):
                mkdir(pc_folder_name)
            pc_folder_files_name = join(pc_folder_name, filename)
            if not exists(pc_folder_files_name):
                mkdir(pc_folder_files_name)
            pc_folder_files = sorted([join(pc_folder_files_name, f) for f in listdir(pc_folder_files_name) if isfile(join(pc_folder_files_name, f))])
            pc_folder_files = generatePCD2LSSPFN(join(pc_folder_files_name, pc_filename), pc_folder_files, mps_ns, lpcp_r, lpcp_nl, mesh_filename=join(mesh_folder_name, mesh_filename))

        elif filename in pc_folders:
            index = pc_folders.index(filename)
            pc_folders.pop(index)
            pc_folder_files_name = join(pc_folder_name, filename)
            pc_folder_files = sorted([join(pc_folder_files_name, f) for f in listdir(pc_folder_files_name) if isfile(join(pc_folder_files_name, f))])
            pc_folder_files = generatePCD2LSSPFN(join(pc_folder_files_name, pc_filename), pc_folder_files, mps_ns, lpcp_r, lpcp_nl)
            if len(pc_folder_files) == 0:
                print(f'\n{filename} has no OBJ and not has all PCD files.')
                continue

        else:
            print(f'\nFeature {filename} has no PCD or OBJ to use.')
            continue

        feature_ext =  features_filename[(point_position + 1):]
        features_data = loadFeatures(join(features_folder_name, filename), feature_ext)
        filterFeaturesData(features_data, curve_types, surface_types)

        for i, resolution in enumerate(lpcp_r):
            str_resolution = str(resolution).replace('.','-')
            h5_filename = join(h5_folder_name, f'{filename}_{str_resolution}.h5')
            h5_file = createH5File(h5_filename)

            h5_file = generateH52LSSPFN(pc_folder_files[(i*2):(i*2+2)], features_data['surfaces'], h5_file, surface_types)

            h5_file.close()
        print('\nProcess done.')