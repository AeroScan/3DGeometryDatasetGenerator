# 3D Geometry Dataset Generator
## Overview
**Authors: Igor Maurell (igormaurell@gmail.com), Pedro Corçaque (pedrollcorc@gmail.com)**

The 3D Geometry Dataset Generator software uses Pythonocc and Gmsh API to process BRep CAD files to generate a machine learning geometry dataset. Furthermore, the h5_parser.py can be used to pass all the generated data to h5 format.

## Formats
### Input Formats
- STEP
- BRep
- Iges
### Output Formats
- YAML (Geometry Features)
- OBJ (CAD Mesh)

## Dependencies
Just a list of dependencies, follow the installation steps to install them all.
- [Anaconda](https://www.anaconda.com)
- [Pythonocc (>= 7.5.0)](https://github.com/tpaviot/pythonocc-core)
- [Gmsh API (Our Fork)](https://gmsh.info/)
- [argparse](https://pypi.org/project/argparse/)
- [tqdm](https://github.com/tqdm/tqdm)
- [PyYAML](https://pypi.org/project/PyYAML/)
- [numpy](https://pypi.org/project/numpy/)
- [sortedcontainers](https://pypi.org/project/sortedcontainers/0.8.4/)
- [termcolor](https://pypi.org/project/termcolor/)
- [h5py](https://www.h5py.org/)
- [pypcd](https://github.com/dimatura/pypcd)
- [mesh_point_sampling](https://github.com/igormaurell/mesh_point_sampling)

## Installation

### Apt dependencies:

    $ sudo apt-get install software-properties-common
    $ sudo apt-get install libtool autoconf automake gfortran gdebi
    $ sudo apt-get install gcc-multilib libxi-dev libxmu-dev libxmu-headers
    $ sudo apt-get install libx11-dev mesa-common-dev libglu1-mesa-dev
    $ sudo apt-get install libfontconfig1-dev
    $ sudo apt-get install libfreetype6 libfreetype6-dev
    $ sudo apt-get install tcl tcl-dev tk tk-dev
    $ sudo apt-get install libfltk1.3-dev

### Create Conda Env
Create conda env:

    $ conda create --name=pyoccenv python=3.7
    $ conda activate pyoccenv

### OCC (7.5.0)
Download the "tgz" file on https://dev.opencascade.org/release, than:

    $ cd ~/Downloads
    $ tar xf opencascade-7.5.0.tgz
    $ cd opencascade-7.5.0
    $ mkdir build && cd build
    $ cmake ..
    $ make
    $ sudo make install

### Pythonocc (7.5.1)

    $ conda install -c conda-forge pythonocc-core=7.5.1

### Gmsh (4.8.4)
On your prefered folder, install:

    $ git clone https://github.com/igormaurell/gmsh
    $ cd gmsh
    $ mkdir build && cd build
    $ cmake -DCMAKE_INSTALL_PREFIX=/opt/gmsh -DENABLE_BUILD_DYNAMIC=1 ..
    $ make
    $ sudo make install

Add to PYTHONPATH,

for bash:

    $ echo export PYTHONPATH="${PYTHONPATH}:/opt/gmsh/lib" >> ~/.bashrc
    $ source ~/.bashrc
    
for zsh:

    $ echo export PYTHONPATH="${PYTHONPATH}:/opt/gmsh/lib" >> ~/.zshrc
    $ source ~/.zshrc

### pypcd
On your prefered folder, install:

    $ git clone https://github.com/igormaurell/pypcd
    $ cd pypcd
    $ python setup.py install

### mesh_point_sampling
On your prefered folder, install:

    $ git clone --recursive https://github.com/igormaurell/mesh_point_sampling
    $ cd mesh_point_sampling
    $ mkdir build && cd build
    $ cmake ..
    $ make
    $ make install

### 3D Geometry Dataset Generator
On your workspace folder, download:

    $ git clone https://github.com/AeroScan/3DGeometryDatasetGenerator
    $ cd 3DGeometryDatasetGenerator
    $ pip install -r requirements.txt

## Using
After install, you can use:
    
    $ conda activate pyoccenv
    $ python dataset_generator.py --help
    $ python h5_parser.py --help