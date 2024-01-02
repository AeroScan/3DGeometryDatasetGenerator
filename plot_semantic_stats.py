import os
import argparse
import json
import matplotlib.pyplot as plt
from pathlib import Path
from tqdm import tqdm

def list_files(input_dir: str, formats: list, return_str=False) -> list:
    files = []
    path = Path(input_dir)
    for file_path in path.glob('*'):
        if file_path.suffix.lower() in formats:
            files.append(file_path if not return_str else str(file_path))
    return sorted(files)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("input_dir", type=str, help="Path to semantic directory.")
    parser.add_argument("output_dir", type=str, help="Path to output figures and stats file.")
    parser.add_argument("--visualize", "-v", type=bool, help="Show graphs.")
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir
    visualize = args.visualize

    os.makedirs(output_dir, exist_ok=True)

    semantic_files = list_files(input_dir, [".json"], return_str=False)
    assert semantic_files, f"There is no semantic file in {input_dir}"

    semantic_dataset_stats = {}
    semantic_dataset_stats["models"] = len(semantic_files)
    semantic_dataset_stats["classes"] = []
    semantic_dataset_stats["instances_per_class"] = {}

    for semantic_file in tqdm(semantic_files):
        filename = semantic_file.name.rstrip(".json")
        semantic_file_dir = os.path.join(output_dir, filename)
        os.makedirs(semantic_file_dir, exist_ok=True)

        data = None
        with open(semantic_file, 'r') as file:
            data = json.load(file)

        labels_dict = {}
        for instance in data["semantic"]:
            label = instance["label"]
            if label == "unlabeled":
                continue
            if label not in labels_dict.keys():
                labels_dict[label] = 1
            else:
                labels_dict[label] += 1

            if label not in semantic_dataset_stats["classes"]:
                semantic_dataset_stats["classes"].append(label)
            
            if label not in semantic_dataset_stats["instances_per_class"].keys():
                semantic_dataset_stats["instances_per_class"][label] = 1
            else:
                semantic_dataset_stats["instances_per_class"][label] += 1

        labels = list(labels_dict.keys())
        counts = list(labels_dict.values())

        plt.pie(counts, labels=None, startangle=90)
        plt.title(f'{filename}')

        plt.legend([f'{label}: {count}' for label, count in zip(labels, counts)], loc='lower right', bbox_to_anchor=(1.0, 0.0))

        fig_path = os.path.join(semantic_file_dir, f'{filename}_instances_pie_chart.png')
        plt.savefig(fig_path)

        if visualize:
            plt.show()
    
    general_stats = os.path.join(output_dir, f"dataset_stats.json")
    with open(general_stats, 'w') as file:
        json.dump(semantic_dataset_stats, file)

    labels = list(semantic_dataset_stats["instances_per_class"].keys())
    counts = list(semantic_dataset_stats["instances_per_class"].values())

    plt.pie(counts, labels=None, startangle=90)
    plt.title(f'Instâncias por classe')

    plt.legend([f'{label}: {count}' for label, count in zip(labels, counts)], loc='lower right')

    fig_path = os.path.join(output_dir, f'dataset_stats_instances_pie_chart.png')
    plt.savefig(fig_path)
        