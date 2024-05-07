import json
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from dataclasses import dataclass
import re

phase2_directory = "./phase2PerQueryOZ/"
phase2_general_directory = "./phase2PerQuery/"
neo_directory = "./neo4jFabricData/"
images_directory = "./neo4jFabricImages/"

line_format_s3 = re.compile(r"QueryId=(\d+) Results=(\d+) time=(\d+)ms")
line_format_neo = re.compile(r"ready to start consuming query after (\d+) ms, results consumed after another (\d+) ms")

@dataclass
class QueryResult:
    idx: int
    time: int
    results: int

def avg(l: list[int]) -> float:
    return sum(l)/len(l)

def read_s3_file(name: str) -> list[QueryResult]:
    with open(name) as f:
        lines = f.read().strip().split("\n")
    res = list()
    for l in lines:
        if not l.startswith('{'):
            matches = line_format_s3.findall(l)[0]
            res.append(QueryResult(int(matches[0]), int(matches[2]), int(matches[1])))
    return res

def read_neo_file(name: str) -> list[int]:
    with open(name) as f:
        lines = f.read().strip().split("\n")
    res = list()
    for l in lines:
        if not l.startswith("ready"):
            continue
        matches = line_format_neo.findall(l)[0]
        res.append(int(matches[0]) + int(matches[1]))
    return res

# types are the values that would be shown on the x-axis. For queries it
# will be Q1,Q2..etc. The times is a dictionary that contains a key and
# a list of size len(types) which contains the value to be displayed for
# that type.
def chart(name: str, times: dict[str, list[float]], types: list[str], 
          width=0.20, x_label=None):
    x = np.arange(len(types))
    mult = 0

    fig, ax = plt.subplots(layout='constrained')
    for fs, time_array in times.items():
        offset = width*mult
        rects = ax.bar(x+offset, time_array, width, label=fs)
        ax.bar_label(rects, padding=3, rotation='vertical', fmt='{:,.1f}')
        mult += 1

    ax.set_ylabel("Running time milliseconds")
    if x_label is not None:
        ax.set_xlabel(x_label)
    ax.set_title("Average time")
    ax.set_xticks(x+width, types)
    ax.legend(loc='upper right', ncols=1)
    plt.ylim(1, 100_000)
    plt.yscale("log")
    plt.savefig(name)
    plt.yscale("linear")

def compare(fabric: str, s3_oz_file: str, s3_general_file: str, image_file: str):
    fabric_times = read_neo_file(fabric)
    s3_oz_times = read_s3_file(s3_oz_file)
    s3_general_times = read_s3_file(s3_general_file)

    labels = ["Q"+str(i) for i in range(1,8)]
    values = {"Neo4J Fabric": list(), "S3 OZ": list(), "S3 General": list()}
    for i in range(7):
        fab_avg = avg(fabric_times[(20*i)+1:20*(i+1)])
        values["Neo4J Fabric"].append(fab_avg)

        s3_oz_avg = avg([res.time for res in s3_oz_times[20*i:20*(i+1)]])
        values["S3 OZ"].append(s3_oz_avg)

        s3_gen_avg = avg([res.time for res in s3_general_times[20*i:20*(i+1)]])
        values["S3 General"].append(s3_gen_avg)
    chart(image_file, values, labels, width=0.22)

def add_dir(filenames: list[str], directory: str) -> list[str]:
    return [directory+i for i in filenames]

def main():
    s3_oz = add_dir(["s3_bfs_1_1.txt", "s3_dfs_1_1.txt"], phase2_directory)
    s3_general = add_dir(["s3_bfs_1_1.txt", "s3_dfs_1_1.txt"], phase2_general_directory)
    fabric = neo_directory + "res_alternate.txt"
    file_names = add_dir(["bfs_cmp.png", "dfs_cmp.png"], images_directory)

    compare(fabric, s3_oz[0], s3_general[0], file_names[0])
    compare(fabric, s3_oz[1], s3_general[1], file_names[1])

if __name__ == "__main__":
    main()
