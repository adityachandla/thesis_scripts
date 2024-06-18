import json
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from dataclasses import dataclass
import re

phase2_directory = "../data/phase2PerQueryOZ/"
neo_directory = "../data/neo4jData/"
images_directory = "../images/neo4jDataImages/"

line_format_s3 = re.compile(r"QueryId=(\d+) Results=(\d+) time=(\d+)ms")
line_format_neo = re.compile(r"Query\w+=(\d+),RunningTime=(\d+),NumRes=(\d+)")

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

def read_neo_file(name: str) -> list[QueryResult]:
    with open(name) as f:
        lines = f.read().strip().split("\n")
    res = list()
    for l in lines:
        if not l.startswith("Q"):
            continue
        matches = line_format_neo.findall(l)[0]
        # Query id starts with 1 in this benchmark ;)
        res.append(QueryResult(int(matches[0])-1, int(matches[1]), int(matches[2])))
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
    plt.ylim(0.01, 100_000)
    plt.yscale("log")
    plt.savefig(name)
    plt.yscale("linear")

def compare(low_level: str, traversal: str, cypher: str, s3_file: str, image_file: str):
    low_level_times = read_neo_file(low_level)
    traversal_times = read_neo_file(traversal)
    cypher_times = read_neo_file(cypher)
    s3_times = read_s3_file(s3_file)

    labels = ["Q"+str(i) for i in range(1,8)]
    values = {"Low Level": list(),"Traversal":list(), "Cypher": list(), "S3 OZ": list()}
    for i in range(7):
        # Neo4j times are in microseconds
        ll_avg = avg([res.time/1000 for res in low_level_times[20*i:20*(i+1)]])
        values["Low Level"].append(ll_avg)

        trav_avg = avg([res.time/1000 for res in traversal_times[20*i:20*(i+1)]])
        values["Traversal"].append(trav_avg)

        # First cypher query creates query plan.
        cypher_avg = avg([res.time/1000 for res in cypher_times[(20*i)+1:20*(i+1)]])
        values["Cypher"].append(cypher_avg)

        s3_avg = avg([res.time for res in s3_times[20*i:20*(i+1)]])
        values["S3 OZ"].append(s3_avg)
    chart(image_file, values, labels)

def compare_lib(traversal: str, gds: str, pregel: str, s3_file: str, image_file: str):
    traversal_times = read_neo_file(traversal)
    gds_times = read_neo_file(gds)
    pregel_times = read_neo_file(pregel)
    s3_times = read_s3_file(s3_file)

    labels = [str(i) for i in range(1,5)]
    values = {"Traversal": list(),"GDS":list(), "Pregel": list(), "S3 OZ": list()}
    for i in range(4):
        # Neo4j times are in microseconds
        trav_avg = avg([res.time/1000 for res in traversal_times[40*i:40*(i+1)]])
        values["Traversal"].append(trav_avg)

        gds_avg = avg([res.time/1000 for res in gds_times[20*i:20*(i+1)]])
        values["GDS"].append(gds_avg)

        pregel_avg = avg([res.time/1000 for res in pregel_times[(20*i)+1:20*(i+1)]])
        values["Pregel"].append(pregel_avg)

        s3_avg = avg([res.time for res in s3_times[40*i:40*(i+1)]])
        values["S3 OZ"].append(s3_avg)
    chart(image_file, values, labels, width=0.15, x_label="Num hops")

def add_dir(filenames: list[str], directory: str) -> list[str]:
    return [directory+i for i in filenames]

def compare_neo4j():
    s3 = add_dir(["s3_bfs_1_1.txt", "s3_dfs_1_1.txt"], phase2_directory)
    low_level = add_dir(["ll_bfs.txt", "ll_dfs.txt"], neo_directory)
    traversal = add_dir(["traversal_bfs.txt", "traversal_dfs.txt"], neo_directory)
    cypher = add_dir(["cypher.txt", "cypher.txt"], neo_directory)
    file_names = add_dir(["bfs_query.png", "dfs_query.png"], images_directory)

    for i in range(len(file_names)):
        compare(low_level[i], traversal[i], cypher[i], s3[i], file_names[i])

def compare_gds():
    s3 = add_dir(["s3_bfs_1_1.txt", "s3_dfs_1_1.txt"], phase2_directory)
    traversal = add_dir(["traversal_bfs.txt", "traversal_dfs.txt"], neo_directory)
    gds = add_dir(["gds_bfs.txt", "gds_dfs.txt"], neo_directory)
    pregel = add_dir(["pregel.txt", "pregel.txt"], neo_directory)
    file_names = add_dir(["bfs_hops.png", "dfs_hops.png"], images_directory)

    for i in range(len(file_names)):
        compare_lib(traversal[i], gds[i], pregel[i], s3[i], file_names[i])

def main():
    compare_neo4j()
    compare_gds()

if __name__ == "__main__":
    main()
