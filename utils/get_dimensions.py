from os import listdir
from os.path import join, isfile, isdir
import csv
import argparse
import numpy as np
from tqdm import tqdm

FILE_TYPES = ["obj", "OBJ"]


def _get_files_from_directory(foldername):
    directories = [foldername]

    filenames = []
    while len(directories) > 0:
        current_dir = directories.pop(0)
        files = [join(current_dir, f) for f in listdir(current_dir) if f[-3:] in FILE_TYPES and isfile(join(current_dir, f))]
        dirs = [join(current_dir, d) for d in listdir(current_dir) if isdir(join(current_dir, d))]

        filenames += files
        directories += dirs
    
    return filenames


def _get_dimensions(filename):
    min = None
    max = None
    with open(filename, "r") as obj_file:
        lines = obj_file.readlines()
        for line in lines:
            if line[0] == "v":
                splited_line = line.split(" ")
                verts = np.array([splited_line[1], splited_line[2], splited_line[3].replace("\n", "")]).astype(float).reshape(-1, 3)

                if min is not None:
                    verts = np.vstack((verts, min))                   
                if max is not None:
                    verts = np.vstack((verts, max))
                
                min = np.min(verts, axis=0)
                max = np.max(verts, axis=0)
        l, w, h = tuple(max-min)
    return l, w, h


def _write_csv_file(foldername, results):
    outname = join(foldername, "result.csv")

    with open(outname, "w") as file:
        writer = csv.writer(file)
        writer.writerows(results)


def main(args):
    
    foldername = args.foldername
    
    filenames = _get_files_from_directory(foldername)
    results = []
    print(f"Start the processing to {len(filenames)} files...")
    for filename in tqdm(filenames):
        l, w, h = _get_dimensions(filename)

        result = (filename.split("/")[-1], str(l).replace(".", ","), str(w).replace(".", ","), str(h).replace(".", ","))
        results.append(result)
    print(f"Done.\n")

    print("Writing the result file...")
    _write_csv_file(foldername, results)
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A helper to get the dimensions of models in .obj format.")
    parser.add_argument("foldername")
    args = parser.parse_args()

    main(args)  