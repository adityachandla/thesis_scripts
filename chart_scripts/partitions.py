import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from dataclasses import dataclass
import re
from typing import Union

numeric = Union[int, float, complex]

base_dir = "../data/partTest/"
image_directory = "../images/partitionSizeComparison"

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

def sum_time(l: list[QueryResult]) -> float:
    s = 0
    for qr in l:
        s += qr.time
    return s/1000

def chart(name: str, times: dict[str, list[numeric]], types: list[str], 
          scale: str = "log", ylim_low: int = None, ylim_high: int = None):
    x = np.arange(len(types))
    width = 0.25
    mult = 0

    _, ax = plt.subplots(layout='constrained')
    for fs, time_array in times.items():
        offset = width*mult
        rects = ax.bar(x+offset, time_array, width, label=fs)
        ax.bar_label(rects, padding=3, rotation='vertical')
        mult += 1

    ax.set_ylabel("Running time milliseconds")
    ax.set_title("Average time")
    ax.set_xticks(x+width, types)
    ax.legend(loc='upper right', ncols=1)
    if ylim_low is not None:
        plt.ylim(ylim_low, ylim_high)
    plt.yscale(scale)
    plt.savefig(name)
    plt.close()

def read_file(name: str) -> (list[QueryResult], list[Stats]):
    with open(name) as f:
        lines = f.read().strip().split("\n")
    res = []
    stats = []
    for l in lines:
        if l.startswith('{'):
            stat = Stats(**json.loads(l))
            stats.append(stat)
        else:
            matches = line_format.findall(l)[0]
            res.append(QueryResult(int(matches[0]), int(matches[2]), int(matches[1])))
    return res, stats

def compare_partitioning(bucket: str, algo: str, parallelism: int):
    sixteen_path  = f"{base_dir}part16_{bucket}/s3_{algo}_{parallelism}_10.txt"
    sixtyfour_path = f"{base_dir}part64_{bucket}/s3_{algo}_{parallelism}_10.txt"
    onetwentyeight_path = f"{base_dir}part128_{bucket}/s3_{algo}_{parallelism}_10.txt"

    sixteen_res, _ = read_file(sixteen_path)
    sixtyfour_res, _ = read_file(sixtyfour_path)
    onetwentyeight_res, _ = read_file(onetwentyeight_path)

    # Per query chart
    times = {"16MB": list(), "64MB": list(), "128MB": list()}
    labels = ["Q"+str(i) for i in range(1,8)]
    for i in range(7):
        times["16MB"].append(avg(sixteen_res[20*i:20*(i+1)]))
        times["64MB"].append(avg(sixtyfour_res[20*i:20*(i+1)]))
        times["128MB"].append(avg(onetwentyeight_res[20*i:20*(i+1)]))

    image_dir = f"{image_directory}/cmp_{bucket}_{algo}_{parallelism}.png"
    chart(image_dir, times, labels, ylim_low=1, ylim_high=1_000_000)

    # Total runtime chart
    total_times = {"Total Time": list()}
    labels = ["16MB", "64MB", "128MB"]
    total_times["Total Time"].append(sum_time(sixteen_res))
    total_times["Total Time"].append(sum_time(sixtyfour_res))
    total_times["Total Time"].append(sum_time(onetwentyeight_res))

    image_dir = f"{image_directory}/total_{bucket}_{algo}_{parallelism}.png"
    chart(image_dir, total_times, labels, scale="linear")


def main():
    sns.set_theme()
    # (general/onezone)_(algo)_(parallelism).png

    bucket_types = ["general", "onezone"]
    algorithms  = ["bfs", "dfs", "bfsp", "dfsp"]
    parallelism = [1,2]

    for bucket in bucket_types:
        for algo in algorithms:
            for p in parallelism:
                compare_partitioning(bucket, algo, p)

if __name__ == "__main__":
    main()
