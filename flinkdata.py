import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from dataclasses import dataclass
import re
from typing import Union

numeric = Union[int, float, complex]

directory = "./flinkRunningTimes/"
image_directory = "./flinkRunningTimesImages/"

@dataclass
class QueryResult:
    hops: int
    timeSeconds: int

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

    ax.set_ylabel("Running time seconds")
    ax.set_title("Apache Flink BFS")
    ax.set_xticks(x+width, types)
    ax.legend(loc='upper right', ncols=1)
    plt.savefig(name)

def mapLine(line:str) -> QueryResult:
    splits = line.strip().split(',')
    return QueryResult(int(splits[0]), int(splits[1]))

def read_file(name: str) -> list[QueryResult]:
    with open(directory+name, "r") as f:
        lines = f.read().strip().split('\n')
    return [mapLine(line) for line in lines[1:]]

def main():
    sns.set_theme()
    single_query = read_file("running_time_rep1.csv")
    two_queries = read_file("running_time_rep2.csv")
    types = ["1-hop", "2-hop", "3-hop", "4-hop"]
    times = {
                "OneRepetition": [q.timeSeconds for q in single_query],
                "TwoRepetition": [q.timeSeconds for q in two_queries]
            }
    chart(image_directory + "comparision.png", times, types)

if __name__ == "__main__":
    main()
