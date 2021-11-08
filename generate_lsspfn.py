from tqdm import tqdm

from os import listdir, mkdir, system, remove
from os.path import isfile, join, exists

import h5py

import numpy as np

from pypcd import pypcd

import gc

from tools import loadFeatures, generateFace2PrimitiveMap, filterFeaturesData

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
                system(f'mesh_point_sampling {mesh_filename} {pc_filename} --n_samples {mps_ns} --write_normals --no_vis_result > /dev/null')
            system(f'large_point_cloud_preprocessing {pc_filename} {pc_filename} --vg {resolution} --centralize --align > /dev/null')
            filtered = True
            system(f'large_point_cloud_preprocessing {pc_filename} {pc_filename_gt} --cube_reescale_factor 1 > /dev/null')

        if pc_filename_noisy not in pc_files:
            if not exists(pc_filename):
                if mesh_filename is None:
                    return []
                system(f'mesh_point_sampling {mesh_filename} {pc_filename} --n_samples {mps_ns} --write_normals --no_vis_result > /dev/null')
            if filtered:
               system(f'large_point_cloud_preprocessing {pc_filename} {pc_filename} --vg {resolution} --centralize --align > /dev/null')
            system(f'large_point_cloud_preprocessing {pc_filename} {pc_filename_noisy} --noise_limit {lpcp_nl} --cube_reescale_factor 1 > /dev/null')
    if exists(pc_filename):
        remove(pc_filename)
    return pc_files_out

def generateH52LSSPFN(pc_files, face_2_primitive, features_data, h5_filename, surface_types):
    h5_file = h5py.File(h5_filename, 'w')
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

    h5_file.create_dataset('gt_points', data=gt_points)

    del gt_points
    gc.collect()
    
    gt_normals = np.ndarray(shape=(pc['x'].shape[0], 3), dtype=np.float64)
    gt_normals[:, 0] = pc['normal_x']
    gt_normals[:, 1] = pc['normal_y']
    gt_normals[:, 2] = pc['normal_z']

    h5_file.create_dataset('gt_normals', data=gt_normals)

    del gt_normals
    gc.collect()

    gt_labels = pc['label']
    features_points = [[] for f in features_data]
    for i in range(0, len(gt_labels)):
        index = face_2_primitive[gt_labels[i]]
        features_points[index].append(i)
        gt_labels[i] = index
    
    h5_file.create_dataset('gt_labels', data=gt_labels)

    del pc
    del gt_labels
    gc.collect()

    pc = pypcd.PointCloud.from_path(pc_filename_noisy).pc_data

    noisy_points = np.ndarray(shape=(pc['x'].shape[0], 3), dtype=np.float64)
    noisy_points[:, 0] = pc['x']
    noisy_points[:, 1] = pc['y']
    noisy_points[:, 2] = pc['z']

    h5_file.create_dataset('noisy_points', data=noisy_points)

    del pc
    del noisy_points
    gc.collect()

    point_position = h5_filename.rfind('.')
    point_position = point_position if point_position >= 0 else len(point_position)
    bar_position = h5_filename.rfind('/')
    bar_position = bar_position if bar_position >= 0 else 0

    name = h5_filename[bar_position:point_position]

    print(name)

    # for i, feature in enumerate(features_data):
    #     grp = h5_file.create_group('{name}_soup_{i}')
    #     gt_indices = np.array(features_points[i])
    #     grp.create_dataset('gt_indices', data=gt_indices)

    h5_file.close()

def generateLSSPFN(features_folder_name, features_files, mesh_folder_name, mesh_files, pc_folder_name, pc_folders, h5_folder_name, mps_ns, lpcp_r, lpcp_nl, surface_types):
    for features_filename in tqdm(features_files):
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
        filterFeaturesData(features_data, [], surface_types)

        face_2_primitive = generateFace2PrimitiveMap(features_data)

        for i, resolution in enumerate(lpcp_r):
            str_resolution = str(resolution).replace('.','-')
            h5_filename = join(h5_folder_name, f'{filename}_{str_resolution}.h5')
            
            generateH52LSSPFN(pc_folder_files[(i*2):(i*2+2)], face_2_primitive, features_data['surfaces'], h5_filename, surface_types)   