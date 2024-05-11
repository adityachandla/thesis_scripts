import json
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from dataclasses import dataclass
import re
from typing import Union

numeric = Union[int, float, complex]
args = None

oz_directory = "../data/phase2ParallelPrefetchOZ/"
image_directory = "../images/phase2ParallelPrefetchOZImages/"

line_format = re.compile(r"QueryId=(\d+) Results=(\d+) time=(\d+)ms")
num_queries = 7

@dataclass
class QueryResult:
    idx: int
    time: int
    results: int

@dataclass
class Stats:
    S3Fetches: int
    cacheHits: int
    inFlightHits: int
    prefetcherHits: int


def avg(l: list[QueryResult]) -> float:
    s = 0
    for qr in l:
        s += qr.time
    return s/len(l)

def chart(name: str, times: dict[str, list[numeric]], types: list[str]):
    x = np.arange(len(types))
    width = 0.25
    mult = 0

    fig, ax = plt.subplots(layout='constrained')
    for fs, time_array in times.items():
        offset = width*mult
        rects = ax.bar(x+offset, time_array, width, label=fs)
        ax.bar_label(rects, padding=3, rotation='vertical')
        mult += 1

    ax.set_ylabel("Running time milliseconds")
    ax.set_title("Average time")
    ax.set_xticks(x+width, types)
    ax.legend(loc='upper right', ncols=1)
    plt.ylim(1, 1_000_000)
    plt.yscale("log")
    plt.savefig(name)
    plt.yscale("linear")

def read_file(name: str) -> (list[QueryResult], list[Stats]):
    with open(name) as f:
        lines = f.read().strip().split("\n")
    res = list()
    stats = list()
    for l in lines:
        if l.startswith('{'):
            stat = Stats(**json.loads(l))
            stats.append(stat)
        else:
            matches = line_format.findall(l)[0]
            res.append(QueryResult(int(matches[0]), int(matches[2]), int(matches[1])))
    return res, stats

def compare_results(algo1: str, algo2: str, parallelism: str, scaling_factor: str):
    one_results, _ = read_file(f"{oz_directory}s3_{algo1}_{parallelism}_{scaling_factor}.txt")
    two_results, _ = read_file(f"{oz_directory}s3_{algo2}_{parallelism}_{scaling_factor}.txt")

    times = {algo1: list(), algo2: list()}
    labels = ["Q"+str(i) for i in range(1,8)]
    for i in range(7):
        times[algo1].append(avg(one_results[20*i:20*(i+1)]))
        times[algo2].append(avg(two_results[20*i:20*(i+1)]))
    chart(f"{image_directory}cmp_{algo1}_{algo2}_{parallelism}_{scaling_factor}", times, labels)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--chart', action='store_true')
    global args
    args = parser.parse_args()
    sns.set_theme()
    scaling_factors = ["10", "1"]

    sequential = ["bfs", "dfs"] 
    parallel = ["bfsp", "dfsp"]

    parallelism = [1,2]
    for sf in scaling_factors:
        for i in range(2):
            for p in parallelism:
                compare_results(sequential[i], parallel[i], p, sf)

if __name__ == "__main__":
    main()
