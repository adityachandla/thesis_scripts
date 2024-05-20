import common
import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from dataclasses import dataclass
import re

base_dir = "../data/partTest/"
image_directory = "../images/partitionSizeComparison/"

NUM_QUERIES = 7
PARALLELISM = [1,2,4,6,10,20]
PARTITIONS = [2,16,64,128]

def create_chart(bucket: str, algorithm: str):
    # On the x axis we want the parallelism and 
    # on the y axis we want the total running time
    plt.subplots(layout="constrained")

    _, ax = plt.subplots(layout='constrained')
    for part in PARTITIONS:
        running_times = []
        for p in PARALLELISM:
            file_name = f"{base_dir}part{part}_{bucket}/s3_{algorithm}_{p}_10.txt"
            times, _ = common.read_file(file_name)
            total_running_time = common.sum_time(times)/p
            running_times.append(total_running_time)
        ax.plot(PARALLELISM, running_times, label=f"{part}MB", marker='o')

    ax.set_ylabel("Running time seconds")
    ax.set_xlabel("Parallelism")
    ax.set_title("Partition size impact")
    ax.legend(loc='upper right', ncols=1)
    plt.savefig(f"{image_directory}cmp_{bucket}_{algorithm}.png")
    plt.close()

def main():
    sns.set_theme()

    bucket_types = ["general"]
    algorithms  = ["bfsp", "dfsp"]

    for bucket in bucket_types:
        for algorithm in algorithms:
            create_chart(bucket, algorithm)


if __name__ == "__main__":
    main()
