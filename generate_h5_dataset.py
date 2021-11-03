import h5py
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import pypcd
from tqdm import tqdm
import argparse

import numpy as np

from os import listdir, mkdir
from os.path import isfile, join, exists

def createH5File(h5_filename):
    h5_file = h5py.File(h5_filename, 'w')
    return h5_file

def addPointsAndNormals2H5(pc_file, h5_file):
    return

def addFeatures2H5(feature_file, h5_file, curve_types, surface_types):
    feature_data = load(feature_file, Loader=Loader)

    print(feature_data.keys())

    gt_types = []
    for feature in feature_data['curves']:
        if feature['type'] in curve_types:
            gt_types.append(curve_types.index(feature['type']))

    for feature in feature_data['surfaces']:
        if feature['type'] in surface_types:
            gt_types.append(surface_types.index(feature['type']) + len(curve_types))

    gt_types = np.array(gt_types)

    h5_file.create_dataset('gt_types', data=gt_types)

    return h5_file

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Converts a dataset from OBJ and YAML to HDF5')
    parser.add_argument('folder', type=str, help='dataset folder.')
    parser.add_argument('--mesh_folder_name', type=str, default = 'mesh', help='mesh folder name.')
    parser.add_argument('--feature_folder_name', type=str, default = 'feature', help='feature folder name.')
    parser.add_argument('--pc_folder_name', type=str, default = 'pc', help='point cloud folder name.')
    parser.add_argument('--curve_types', type=str, default = '', help='types of curves to generate. Default = ')
    parser.add_argument('--surface_types', type=str, default = 'plane,cylinder,cone,sphere', help='types of surfaces to generate. Default = plane,cylinder,cone,sphere')
    args = vars(parser.parse_args())

    folder = args['folder']
    mesh_folder_name = join(folder, args['mesh_folder_name'])
    feature_folder_name = join(folder, args['feature_folder_name'])
    pc_folder_name = join(folder, args['pc_folder_name'])
    curve_types = args['curve_types'].split(',')
    surface_types = args['surface_types'].split(',')

    mesh_files = []
    feature_files = []
    pc_files = []
    if exists(mesh_folder_name):
        mesh_files = sorted([f for f in listdir(mesh_folder_name) if isfile(join(mesh_folder_name, f))])
    if exists(feature_folder_name):
        feature_files = sorted([f for f in listdir(feature_folder_name) if isfile(join(feature_folder_name, f))])
    if exists(pc_folder_name):
        pc_files = sorted([f for f in listdir(pc_folder_name) if isfile(join(pc_folder_name, f))])

    if len(feature_files) == 0:
        print('There is no features file to process.')
        exit()
    
    if len(mesh_files) == 0 and len(pc_files) == 0:
        print('There is no mesh or point cloud file.')
        exit()

    for feature_filename in feature_files:
        print('\nProcessing ' + feature_filename + '...\n')

        mesh_filename = feature_filename[:feature_filename.rfind('.')] + '.obj'
        pc_filename = feature_filename[:feature_filename.rfind('.')] + '.pcd'
        h5_filename = feature_filename[:feature_filename.rfind('.')] + '.h5'
        
        h5_file = createH5File(join(folder, h5_filename))

        feature_file = open(join(folder, feature_folder_name, feature_filename), 'r')

        h5_file = addFeatures2H5(feature_file, h5_file, curve_types, surface_types)

        if pc_files.index(pc_filename) != -1:
            pass
            #h5_file = addFeatures2H5(feature_file, h5_file)
        
        elif mesh_files.index(mesh_filename) != -1:
            pass
        
        else:
            print('Feature ' + feature_filename + ' has no PCD or OBJ to use.')
        
        h5_file.close()

        print('\nProcess done.\n')