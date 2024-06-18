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

line_format = re.compile(r"QueryId=(\d+) Results=(\d+) time=(\d+)ms")
line_format_neo = re.compile(r"Query\w+=(\d+),RunningTime=(\d+),NumRes=(\d+)")
line_format_fabric = re.compile(r"ready to start consuming query after (\d+) ms, results consumed after another (\d+) ms")
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

def read_fabric_file(name: str) -> list[int]:
    with open(name) as f:
        lines = f.read().strip().split("\n")
    res = list()
    for l in lines:
        if not l.startswith("ready"):
            continue
        matches = line_format_fabric.findall(l)[0]
        res.append(int(matches[0]) + int(matches[1]))
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

def chart(name: str, times: dict[str, list[numeric]], types: list[str], 
          scale: str = "log", ylim_low: int = None, ylim_high: int = None,
          legend_loc: str = "upper right", xlabel: str = "Queries", 
          title:str = "Average time", ylabel: str= "Running time milliseconds",
          fmt='{:,.0f}', width=0.25):
    x = np.arange(len(types))
    mult = 0

    _, ax = plt.subplots(layout='constrained')
    for fs, time_array in times.items():
        offset = width*mult
        rects = ax.bar(x+offset, time_array, width, label=fs)
        ax.bar_label(rects, fmt=fmt, padding=3, rotation='vertical')
        mult += 1

    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.set_xticks(x+width, types)
    ax.legend(loc=legend_loc, ncols=1)
    if ylim_low is not None:
        plt.ylim(ylim_low, ylim_high)
    plt.yscale(scale)
    plt.savefig(name)
    plt.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filepath')
    parser.add_argument('-p', '--parallelism')
    global args
    args = parser.parse_args()
    res, stats = read_file(args.filepath)
    print(f"Results for file {args.filepath}")
    print(f"Average running time {avg(res)}")
    print(f"Total running time {sum_time(res)}")
    print(f"Wall clock time {sum_time(res)/int(args.parallelism)}")
    print()



if __name__ == "__main__":
    main()
