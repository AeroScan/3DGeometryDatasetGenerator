from generate_pythonocc import processPythonOCC
from generate_gmsh import processGMSH, mergeFeaturesOCCandGMSH
from tools import writeYAML

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='3D Geometry Dataset Generator.')
    parser.add_argument('input', type=str, help='input file in CAD formats.')
    parser.add_argument('output', type=str, help='output file name for mesh and features.')
    parser.add_argument('--mesh_size', type=float, default=10, help='mesh size.')
    args = vars(parser.parse_args())

    input_name = args['input']
    output_name = args['output']
    mesh_size = args['mesh_size']

    # Process in PythonOCC
    features = processPythonOCC(input_name)

    # Process in GMSH
    processGMSH(input_name, mesh_size, features, output_name)

    # Write YAML
    writeYAML(output_name, features)
