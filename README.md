# 3D Geometry Dataset Generator
## Overview
**Authors: Igor Maurell (igormaurell@gmail.com), Pedro Corçaque (pedrollcorc@gmail.com)**

The 3D Geometry Dataset Generator software uses Pythonocc and Gmsh API to process BRep CAD files to generate a machine learning geometry dataset.

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
- [Pythonocc (>= 7.5.0)](https://github.com/tpaviot/pythonocc-core)
- [Gmsh API (Our Fork)](https://github.com/igormaurell/gmsh)
- [argparse](https://pypi.org/project/argparse/)
- [tqdm](https://github.com/tqdm/tqdm)
- [PyYAML](https://pypi.org/project/PyYAML/)
- [numpy](https://pypi.org/project/numpy/)

## Installation
### OCC (7.5.0)
Install dependencies:

    $ sudo apt-get install software-properties-common
    $ sudo apt-get install libtool autoconf automake gfortran gdebi
    $ sudo apt-get install gcc-multilib libxi-dev libxmu-dev libxmu-headers
    $ sudo apt-get install libx11-dev mesa-common-dev libglu1-mesa-dev
    $ sudo apt-get install libfontconfig1-dev
    $ sudo apt-get install libfreetype6 libfreetype6-dev
    $ sudo apt-get install tcl tcl-dev tk tk-dev

Download the "tgz" file on https://dev.opencascade.org/release, than:

    $ cd ~/Downloads
    $ tar xf opencascade-7.5.0.tar.gz
    $ cd opencascade-7.5.0
    $ mkdir build && cd build
    $ cmake ..
    $ make
    $ sudo make install



### Gmsh (4.8.4)
Install:

    $ git clone https://github.com/igormaurell/gmsh
    $ mkdir build && cd build
    $ cmake -DCMAKE_INSTALL_PREFIX=/opt/gmsh -DENABLE_BUILD_DYNAMIC=1 ..
    $ make
    $ make install

Add to PYTHONPATH:

    $ echo "export PYTHONPATH=${PYTHONPATH}:/opt/gmsh/lib" >> ~/.bashrc
    $ echo "export PYTHONPATH=${PYTHONPATH}:/opt/gmsh/lib" >> ~/.zshrc



### Pythonocc (7.5.1)
Create conda env:

    $ conda create --name=pyoccenv python=3.7
    $ conda activate pyoccenv
    $ conda install -c conda-forge pythonocc-core=7.5.1



### 3D Geometry Dataset Generator
Download:

    $ git clone https://github.com/AeroScan/3DGeometryDatasetGenerator
    $ cd 3DGeometryDatasetGenerator
    $ pip install -r requirements.txt

## Using
After install, use the help to understand the parameters, doing:
    
    $ python dataset_generator.py --help