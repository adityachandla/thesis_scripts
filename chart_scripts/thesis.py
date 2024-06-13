import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import seaborn as sns
import numpy as np
import common

baseline_dir = "../data/final/firstImpl/general"
final_dir = "../data/final/lastImpl/general"
image_dir = "../images/thesis_images"

def pie_chart(name: str, pie_info: dict[str, int]):
    fig, ax = plt.subplots()
    labels = [k for k in pie_info]
    values = [pie_info[k] for k in pie_info]
    ax.pie(values, labels=labels, autopct='%1.1f%%')

    plt.savefig(name)
    plt.close()

def chart(name: str, times: dict[str, list[int]], types: list[str], 
          scale: str = "log", ylim_low: int = None, ylim_high: int = None,
          legend_loc: str = "upper right", xlabel: str = "Queries", 
          title:str = "Average time", ylabel: str= "Running time milliseconds"):
    x = np.arange(len(types))
    width = 0.25
    mult = 0

    _, ax = plt.subplots(layout='constrained')
    for fs, time_array in times.items():
        offset = width*mult
        rects = ax.bar(x+offset, time_array, width, label=fs)
        ax.bar_label(rects, fmt='{:,.0f}', padding=3, rotation='vertical')
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

def get_hits(stats: list[common.Stats]) -> dict[str,int]:
    res = {}
    res["S3 Fetches"] = stats[-1].S3Fetches - stats[0].S3Fetches
    res["Cache hits"] = stats[-1].cacheHits - stats[0].cacheHits
    res["Prefetcher hits"] = stats[-1].inFlightHits - stats[0].inFlightHits
    res["Prefetcher hits"] += stats[-1].prefetcherHits - stats[0].prefetcherHits
    return res

def create_pie_chart():
    _, bfs_stats = common.read_file(f"{final_dir}/s3_bfsp_1_10.txt")
    hits = get_hits(bfs_stats)
    pie_chart(f"{image_dir}/pie_bfs.png", hits)

    _, dfs_stats = common.read_file(f"{final_dir}/s3_dfspe_1_10.txt")
    hits = get_hits(dfs_stats)
    pie_chart(f"{image_dir}/pie_dfs.png", hits)

def create_baseline_comparison():
    parallelism = 1
    for algo in ['BFS', 'DFS']:
        for sf in [1,10]:
            a_base = algo.lower()
            base, _ = common.read_file(f"{baseline_dir}/s3_{a_base}_{parallelism}_{sf}.txt")
            assert len(base) == 140
            a_fin = None
            if algo == "BFS":
                a_fin = "bfsp"
            else:
                a_fin = "dfspe"
            final, _ = common.read_file(f"{final_dir}/s3_{a_fin}_{parallelism}_{sf}.txt")
            assert len(final) == 140

            labels = []
            for query in range(1,8):
                labels.append(f"Q-{query}\n{(query+1)//2}-Hop")

            times = {"Baseline": [], "Final": []}

            for i in range(7):
                times["Baseline"].append(common.avg(base[20*i:20*(i+1)]))

            for i in range(7):
                times["Final"].append(common.avg(final[20*i:20*(i+1)]))

            chart(f"{image_dir}/{algo}_cmp_{sf}.png", times, labels, 
                  title=f"Average time ({algo}) SF-{sf}",
                  ylim_low=1, ylim_high=1_000_000)


def main():
    # create_baseline_comparison()
    create_pie_chart()

if __name__ == "__main__":
    main()
