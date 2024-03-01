import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from dataclasses import dataclass
import re
from typing import Union

numeric = Union[int, float, complex]

directory="./phase1/"
image_directory = "./phase1Images/"
line_format = re.compile(r"QueryId=(\d+) Results=(\d+) time=(\d+)ms")
num_queries = 7

@dataclass
class QueryResult:
    idx: int
    time: int
    results: int


def avg(l: list[QueryResult]) -> float:
    s = 0
    for qr in l:
        s += qr.time
    return s/len(l)

def chart(name: str, tarr: list[tuple[numeric]]):
    types = ["Q"+str(i) for i in range(1,8)]
    times = dict()
    times["local"] = list()
    times["s3"] = list()
    for t in tarr:
        times["local"].append(t[0])
        times["s3"].append(t[1])
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
    if "95" in name:
        ax.set_title("p95 time")
    else:
        ax.set_title("Average time")
    ax.set_xticks(x+width, types)
    ax.legend(loc='upper right', ncols=1)
    plt.yscale("log")
    plt.savefig(name)

def p95(l: list[int]) -> int:
    l = sorted(l, key=lambda x : x.time)
    return l[int(len(l)*0.95)].time

def read_file(name: str) -> list[QueryResult]:
    with open(name) as f:
        lines = f.read().strip().split("\n")
    res = list()
    for l in lines:
        matches = line_format.findall(l)[0]
        res.append(QueryResult(int(matches[0]), int(matches[2]), int(matches[1])))
    return res

def compare_results(algo: str, parallelism: str, scaling_factor: str):
    localpath = f"{directory}local_{algo}_{parallelism}_{scaling_factor}.txt"
    localres = read_file(localpath)

    s3path = f"{directory}s3_{algo}_{parallelism}_{scaling_factor}.txt"
    s3res = read_file(s3path)

    assert len(s3res) == len(localres)
    
    print(f"====Algorithm {algo}====Paralleism {parallelism}=====")
    averages = []
    p95s = []
    for i in range(num_queries):
        start = i*20
        end = (i+1)*20

        s3avg = avg(s3res[start:end])
        localavg = avg(localres[start:end])
        averages.append((localavg, s3avg))

        s395 = p95(s3res[start:end])
        local95 = p95(localres[start:end])
        p95s.append((local95, s395))
        print(f"Query: {i+1}")
        print(f"Local: avg={localavg} p95={local95}")
        print(f"S3: avg={s3avg} p95={s395}")
        print()
    average_name = f"{image_directory}{algo}_{parallelism}_{scaling_factor}_avg.png"
    chart(average_name, averages)
    p95_name = f"{image_directory}{algo}_{parallelism}_{scaling_factor}_95.png"
    chart(p95_name, p95s)
    print(f"======================================")

def main():
    sns.set_theme()
    scaling_factors = ["10", "1"]
    for sf in scaling_factors:
        compare_results("bfs", "1", sf)
        compare_results("bfs", "2", sf)
        compare_results("dfs", "1", sf)
        compare_results("dfs", "2", sf)


if __name__ == "__main__":
    main()
