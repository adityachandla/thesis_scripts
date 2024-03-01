import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from dataclasses import dataclass
import re
from typing import Union

numeric = Union[int, float, complex]

directory = "./phase2Queue/"
image_directory = "./phase2QueueImages/"
oldDir = "./phase1/"
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
        ax.bar_label(rects, padding=3)
        mult += 1

    ax.set_ylabel("Running time milliseconds")
    ax.set_title("Average time")
    ax.set_xticks(x+width, types)
    ax.legend(loc='upper right', ncols=1)
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

def compare_results(algo: str, parallelism: str, scaling_factor: str):
    phase1Path = f"{oldDir}s3_{algo}_{parallelism}_{scaling_factor}.txt"
    ## Right now phase1 does not have stats but if I run it again in the future, then
    ## it will.
    phase1Res, phase1Stat = read_file(phase1Path)

    phase2Path = f"{directory}s3_{algo}_{parallelism}_{scaling_factor}.txt"
    phase2Res, phase2Stat = read_file(phase2Path)

    assert len(phase2Res) == len(phase1Res)

    times = {"phase1": list(), "phase2": list()}
    labels = ["Q"+str(i) for i in range(1,8)]
    print(f"====Algorithm {algo}====Paralleism {parallelism}=====")
    for i in range(7):
        times["phase1"].append(avg(phase1Res[20*i:20*(i+1)]))
        times["phase2"].append(avg(phase2Res[20*i:20*(i+1)]))
    chart(f"{image_directory}cmp_{algo}_{parallelism}_{scaling_factor}", times, labels)
    firstStat = phase2Stat[1]
    lastStat = phase2Stat[-1]
    print(f"S3Fetches: {lastStat.S3Fetches-firstStat.S3Fetches}")
    print(f"Cache hits: {lastStat.cacheHits-firstStat.cacheHits}")
    print(f"In Flight hits: {lastStat.inFlightHits-firstStat.inFlightHits}")
    print(f"Prefetch cache hits: {lastStat.prefetcherHits-firstStat.prefetcherHits}")
    print(f"======================================")

def compare_scaling(algo: str):
    sf1Res, _ = read_file(f"{directory}s3_{algo}_1_1.txt")
    sf10Res, _ = read_file(f"{directory}s3_{algo}_1_10.txt")
    times = {"SF1": list(), "SF10": list()}
    labels = ["Q"+str(i) for i in range(1,8)]
    for i in range(7):
        times["SF1"].append(avg(sf1Res[20*i:20*(i+1)]))
        times["SF10"].append(avg(sf10Res[20*i:20*(i+1)]))
    chart(f"{image_directory}scaling_{algo}", times, labels)
    print(f"Created scaling chart for {algo}")

def main():
    sns.set_theme()
    scaling_factors = ["10", "1"]
    for sf in scaling_factors:
        compare_results("bfs", "1", sf)
        compare_results("bfs", "2", sf)
        compare_results("dfs", "1", sf)
        compare_results("dfs", "2", sf)
    compare_scaling("bfs")
    compare_scaling("dfs")

if __name__ == "__main__":
    main()
