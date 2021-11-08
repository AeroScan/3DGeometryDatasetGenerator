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

from generate_lsspfn import generateLSSPFN

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
    parser.add_argument('-nl', '--noise_limit', type=float, default= 10, help='noise_limit for point cloud, if necessary. Default: 10.')

    args = vars(parser.parse_args())

    folder_name = args['folder']
    h5_folder_name = join(folder_name, args['h5_folder_name'])
    mesh_folder_name = join(folder_name, args['mesh_folder_name'])
    features_folder_name = join(folder_name, args['features_folder_name'])
    pc_folder_name = join(folder_name, args['pc_folder_name'])
    curve_types = args['curve_types'].split(',')
    surface_types = [s.lower() for s in args['surface_types'].split(',')]
    mps_ns = args['mesh_point_sampling_n_samples']
    lpcp_r = sorted([float(x) for x in args['large_point_cloud_preprocessing_resolutions'].split(',')])
    noise_limit = args['noise_limit']

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
        mkdir(h5_folder_name)
    
    print(f'\nGenerating dataset for {len(features_files)} features files...\n')

    generateLSSPFN(features_folder_name, features_files, mesh_folder_name, mesh_files, pc_folder_name, pc_folders, h5_folder_name, mps_ns, lpcp_r, noise_limit, surface_types)

    print()