import os
import argparse
from pathlib import Path

from OCC.Core.gp import gp_Ax1, gp_Dir, gp_Pnt
from OCC.Extend.ShapeFactory import rotate_shape
from OCC.Extend.DataExchange import read_step_file, write_step_file

CAD_FORMATS = ['.step', '.stp', '.STEP']
def list_files(input_dir: str, formats: list, return_str=False) -> list:
    files = []
    path = Path(input_dir)
    for file_path in path.glob('*'):
        if file_path.suffix.lower() in formats:
            files.append(file_path if not return_str else str(file_path))
    return sorted(files)

def makeNewStepFile(new_shape, filename: str):
    print(f'Writing a new file...')
    write_step_file(a_shape=new_shape, filename=filename, application_protocol="AP203")
    print(f'Done.\n\n')

def rotateStepFile(step_path: str, axis: str, angle: float, add_rotated: bool = False):
    print(f'Opening file...')
    shape = read_step_file(filename=step_path, verbosity=False)
    print(f'Done.\n')
    if axis == 'x':
        axis = gp_Ax1(gp_Pnt(0.0, 0.0, 0.0), gp_Dir(1.0, 0.0, 0.0))
    elif axis == 'y':
        axis = gp_Ax1(gp_Pnt(0.0, 0.0, 0.0), gp_Dir(0.0, 1.0, 0.0))
    else:
        axis = gp_Ax1(gp_Pnt(0.0, 0.0, 0.0), gp_Dir(0.0, 0.0, 1.0))
    print(f'Rotating model...')
    shape = rotate_shape(shape=shape, axis=axis, angle=angle)
    print(f'Done.\n')
    output_path = step_path
    if add_rotated:
        splits = output_path.split('.')
        splits[-2] += '_rotated'
        output_path = '.'.join(splits)
    makeNewStepFile(new_shape=shape, filename=output_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Step Rotation')
    parser.add_argument('input_path', type=str, default='.', help='path to input directory or input file.')
    parser.add_argument('axis_rotation', type=str, default='x', help='axis to rotate the input models. Possible axis: x, y, z.')
    parser.add_argument('angle_rotation', type=float, help='angle to rotate the input models. Interval: [-270, 270].')
    parser.add_argument('-r', '--add_rotated', action='store_true', help="flag to add '_rotated' in file name.")
    args = vars(parser.parse_args())

    input_path = args['input_path']
    axis = args['axis_rotation']
    angle = args['angle_rotation']
    add_rotated = args['add_rotated']

    assert axis in 'xyz'

    if os.path.exists(input_path):
        if os.path.isdir(input_path):
            files = list_files(input_path, CAD_FORMATS)
        else:
            files = [input_path]
    else:
        print('[Step Rotator] Input path not found')
        exit()

    for file in files:
        file = str(file)
        print(f'[Step Rotator] Processing file {file}')
        rotateStepFile(step_path=file, axis=axis, angle=angle, add_rotated=add_rotated)
