# 3D Geometry Dataset Generator
## Overview
**Authors: Igor Maurell (igormaurell@gmail.com), Pedro Corçaque (pedrollcorc@gmail.com)**

The 3D Geometry Dataset Generator software uses Pythonocc and Gmsh API to process BRep CAD files to generate a machine learning geometry dataset.

## Formats
### Input Formats
- STEP, BRep, Iges (CAD File)
- YAML (Metadata File)
### Output Formats
- JSON, YAML, PKL (Geometry Features)
- PLY (CAD Mesh)
- JSON (Stats)

## Dependencies
Just a list of dependencies, follow the installation steps to install them all.
- [Anaconda](https://www.anaconda.com)
- [Pythonocc (>= 7.7.0)](https://github.com/tpaviot/pythonocc-core)
- [Gmsh API](https://gmsh.info/)
- [argparse](https://pypi.org/project/argparse/)
- [tqdm](https://github.com/tqdm/tqdm)
- [PyYAML](https://pypi.org/project/PyYAML/)
- [numpy](https://pypi.org/project/numpy/)

## Installation

### Apt dependencies:

    sudo apt-get install software-properties-common cmake
    sudo apt-get install libtool autoconf automake gfortran gdebi
    sudo apt-get install gcc-multilib libxi-dev libxmu-dev libxmu-headers
    sudo apt-get install libx11-dev mesa-common-dev libglu1-mesa-dev
    sudo apt-get install libfontconfig1-dev
    sudo apt-get install libfreetype6 libfreetype6-dev
    sudo apt-get install tcl tcl-dev tk tk-dev
    sudo apt-get install libfltk1.3-dev

### Create Conda Env
Create conda env:

    conda create --name=pyoccenv python=3.9
    conda activate pyoccenv

### OCC (7.7.0)
Download the "tgz" file on https://dev.opencascade.org/release, than:

    cd ~/Downloads
    tar xf opencascade-7.7.0.tgz
    cd opencascade-7.7.0
    mkdir build && cd build
    cmake ..
    make
    sudo make install

### Pythonocc (7.7.0)

    conda install -c conda-forge pythonocc-core=7.7.0

### 3D Geometry Dataset Generator
On your workspace folder, download:

    git clone https://github.com/AeroScan/3DGeometryDatasetGenerator
    cd 3DGeometryDatasetGenerator
    pip install -r requirements.txt

## Using
After install, you can use:
    
    conda activate pyoccenv
    python data_generator.py --help
