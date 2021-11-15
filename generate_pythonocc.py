from OCC.Core import STEPControl
from OCC.Core.GeomAbs import GeomAbs_CurveType, GeomAbs_SurfaceType
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.TopoDS import TopoDS_Face
from OCC.Extend.DataExchange import read_step_file
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.Interface import Interface_Static_IVal, Interface_Static_SetCVal
from OCC.Core.ShapeProcess import ShapeProcess_OperLibrary
from OCC.Extend.TopologyUtils import (list_of_shapes_to_compound)
from OCC.Core.IFSelect import IFSelect_RetDone, IFSelect_ItemsByEntity

from sortedcontainers import SortedSet

from functools import reduce

from tools import gpXYZ2List

from tqdm import tqdm
import numpy as np

MAX_INT = 2**31 - 1

POSSIBLE_CURVE_TYPES = ['line', 'circle', 'ellipse']
POSSIBLE_SURFACE_TYPES = ['plane', 'cylinder', 'cone', 'sphere', 'torus']
POSSIBLE_UNITS = ['1', 'inch', 'mm', '??', 'ft', 'mi', 'm', 'km', 'mil', 'um', 'cm', 'uin']

# Generate lines information
def generateLineFeature(shape) -> dict:
    shape = shape.Line()

    feature = {
        'type': 'Line',
        'location': gpXYZ2List(shape.Location()),
        'direction': gpXYZ2List(shape.Direction()),
    }

    return {**feature}

# Generate circles information
def generateCircleFeature(shape) -> dict:
    shape = shape.Circle()

    feature = {
        'type': 'Circle',
        'location': gpXYZ2List(shape.Location()),
        'z_axis': gpXYZ2List(shape.Axis().Direction()),
        'radius': shape.Radius(),
        'x_axis': gpXYZ2List(shape.XAxis().Direction()),
        'y_axis': gpXYZ2List(shape.YAxis().Direction()),
    }

    if feature['radius'] == 0:
        return None
    else:
        return {**feature}

# Generate ellipses information
def generateEllipseFeature(shape) -> dict:
    shape = shape.Ellipse()

    feature = {
        'type': 'Ellipse',
        'focus1': gpXYZ2List(shape.Focus1()),
        'focus2': gpXYZ2List(shape.Focus2()),
        'x_axis': gpXYZ2List(shape.XAxis().Direction()),
        'y_axis': gpXYZ2List(shape.YAxis().Direction()),
        'z_axis': gpXYZ2List(shape.Axis().Direction()),
        'x_radius': shape.MajorRadius(),
        'y_radius': shape.MinorRadius(),
    }

    if feature['x_radius'] == 0 or feature['y_radius'] == 0:
        return None
    else:
        return {**feature}

# Generate planes information
def generatePlaneFeature(shape) -> dict:
    shape = shape.Plane()

    feature = {
        'type': 'Plane',
        'location': gpXYZ2List(shape.Location()),
        'normal': gpXYZ2List(shape.Axis().Direction()),
        'x_axis': gpXYZ2List(shape.XAxis().Direction()),
        'y_axis': gpXYZ2List(shape.YAxis().Direction()),
        'z_axis': gpXYZ2List(shape.Axis().Direction()),
        'coefficients': list(shape.Coefficients()),
    }

    return {**feature}

# Generate cylinders information
def generateCylinderFeature(shape) -> dict:
    shape = shape.Cylinder()

    feature = {
        'type': 'Cylinder',
        'location': gpXYZ2List(shape.Location()),
        'x_axis': gpXYZ2List(shape.XAxis().Direction()),
        'y_axis': gpXYZ2List(shape.YAxis().Direction()),
        'z_axis': gpXYZ2List(shape.Axis().Direction()),
        'coefficients': list(shape.Coefficients()),
        'radius': shape.Radius(),
    }

    if feature['radius'] == 0:
        return None
    else:
        return {**feature}

# Generate cones information
def generateConeFeature(shape) -> dict:
    shape = shape.Cone()

    feature = {
        'type': 'Cone',
        'location': gpXYZ2List(shape.Location()),
        'x_axis': gpXYZ2List(shape.XAxis().Direction()),
        'y_axis': gpXYZ2List(shape.YAxis().Direction()),
        'z_axis': gpXYZ2List(shape.Axis().Direction()),
        'coefficients': list(shape.Coefficients()),
        'radius': shape.RefRadius(),
        'angle': shape.SemiAngle(),
        'apex': gpXYZ2List(shape.Apex()),
    }

    if feature['radius'] == 0:
        return None
    else:
        return {**feature}

# Generate spheres information
def generateSphereFeature(shape) -> dict:
    shape = shape.Sphere()

    x_axis = np.array(gpXYZ2List(shape.XAxis().Direction()))
    y_axis = np.array(gpXYZ2List(shape.YAxis().Direction()))
    z_axis = np.cross(x_axis, y_axis)

    feature = {
        'type': 'Sphere',
        'location': gpXYZ2List(shape.Location()),
        'x_axis': x_axis.tolist(),
        'y_axis': y_axis.tolist(),
        'z_axis': z_axis.tolist(),
        'coefficients': list(shape.Coefficients()),
        'radius': shape.Radius(),
    }

    if feature['radius'] == 0:
        return None
    else:
        return {**feature}

# Generate torus information
def generateTorusFeature(shape) -> dict:
    shape = shape.Torus()

    feature = {
        'type': 'Torus',
        'location': gpXYZ2List(shape.Location()),
        'x_axis': gpXYZ2List(shape.XAxis().Direction()),
        'y_axis': gpXYZ2List(shape.YAxis().Direction()),
        'z_axis': gpXYZ2List(shape.Axis().Direction()),
        # 'coefficients': list(shape.Coefficients()),
        'max_radius': shape.MajorRadius(),
        'min_radius': shape.MinorRadius(),
    }

    if feature['max_radius'] == 0 or feature['min_radius'] == 0:
        return None
    else:
        return {**feature}

# Call function by type
def generateFeature(type: str, shape):
    generate_functions_dict = {
        'line': generateLineFeature,
        'circle': generateCircleFeature,
        'ellipse': generateEllipseFeature,
        'plane': generatePlaneFeature,
        'cylinder': generateCylinderFeature,
        'cone': generateConeFeature,
        'sphere': generateSphereFeature,
        'torus': generateTorusFeature,
    }
    if type.lower() in generate_functions_dict.keys():
        return generate_functions_dict[type.lower()](shape)

# Generate features by dimensions
def generateFeatureByDim(shape, features: dict, use_highest_dim=True):
    features['curves'] = []
    features['surfaces'] = []
    topology = TopologyExplorer(shape)

    if use_highest_dim:
        faces = SortedSet()
        edges = SortedSet()
        for solid in tqdm(topology.solids()):
            for face in topology.faces_from_solids(solid):

                face_hc = face.HashCode(MAX_INT)
                if faces.count(face_hc) > 0:
                    continue
                faces.add(face_hc)


                surface = BRepAdaptor_Surface(face, True)
                tp = str(GeomAbs_SurfaceType(surface.GetType())).split('_')[-1].lower()

                if tp in POSSIBLE_SURFACE_TYPES:
                    feature = generateFeature(type=tp, shape=surface)
                    features['surfaces'].append(feature)
                else:
                    features['surfaces'].append(None)
                
                for edge in topology.edges_from_face(face):

                    edge_hc = edge.HashCode(MAX_INT)
                    if edges.count(edge_hc) > 0:
                        continue
                    edges.add(edge_hc)

                    curve = BRepAdaptor_Curve(edge)
                    tp = str(GeomAbs_CurveType(curve.GetType())).split('_')[-1].lower()

                    if tp in POSSIBLE_CURVE_TYPES:
                        feature = generateFeature(type=tp, shape=curve)
                        features['curves'].append(feature)
                    else:
                        features['curves'].append(None)     
                
    else:
        for edge in tqdm(topology.edges()):
            curve = BRepAdaptor_Curve(edge)
            tp = str(GeomAbs_CurveType(curve.GetType())).split('_')[-1].lower()

            if tp in POSSIBLE_CURVE_TYPES:
                feature = generateFeature(type=tp, shape=curve)
                features['curves'].append(feature)
            else:
                features['curves'].append(None)
        
        for face in tqdm(topology.faces()):
            surface = BRepAdaptor_Surface(face, True)
            tp = str(GeomAbs_SurfaceType(surface.GetType())).split('_')[-1].lower()

            if tp in POSSIBLE_SURFACE_TYPES:
                feature = generateFeature(type=tp, shape=surface)
                features['surfaces'].append(feature)
            else:
                features['surfaces'].append(None)       

def read_step(input_name, as_compound=True, verbosity=False, unit='m'):
    step_reader = STEPControl_Reader()
    status = step_reader.ReadFile(input_name)

    # To control the input/output unit
    print(f'Unidade padrão: {POSSIBLE_UNITS[Interface_Static_IVal("xstep.cascade.unit")]}')
    if unit in POSSIBLE_UNITS:
        Interface_Static_SetCVal('xstep.cascade.unit', unit.upper())
        print(f'Unidade alterada para: {POSSIBLE_UNITS[Interface_Static_IVal("xstep.cascade.unit")]}')

    if status == IFSelect_RetDone:
        if verbosity:
            failsonly = False
            step_reader.PrintCheckLoad(failsonly, IFSelect_ItemsByEntity)
            step_reader.PrintCheckTransfer(failsonly, IFSelect_ItemsByEntity)
        transfer_result = step_reader.TransferRoots()
        if not transfer_result:
            raise AssertionError("Transfer failed.")
        _nbs = step_reader.NbShapes()
        if _nbs == 0:
            raise AssertionError("No shape to transfer.")
        elif _nbs == 1:  # most cases
            return step_reader.Shape(1)
        elif _nbs > 1:
            print("Number of shapes:", _nbs)
            shps = []
            # loop over root shapes
            for k in range(1, _nbs + 1):
                new_shp = step_reader.Shape(k)
                if not new_shp.IsNull():
                    shps.append(new_shp)
            if as_compound:
                compound, result = list_of_shapes_to_compound(shps)
                if not result:
                    print("Warning: all shapes were not added to the compound")
                return compound
            else:
                print("Warning, returns a list of shapes.")
                return shps
    else:
        raise AssertionError("Error: can't read file.")
    return None

# Main function
def processPythonOCC(input_name: str, unit: str, use_highest_dim=True) -> dict:
    features = {}

    # shape = read_step_file(filename=input_name, as_compound=True, verbosity=False)

    shape = read_step(input_name, unit=unit)

    generateFeatureByDim(shape, features, use_highest_dim=use_highest_dim)

    return shape, features