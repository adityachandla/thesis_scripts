import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import seaborn as sns
import numpy as np
import common

baseline_dir = "../data/final/firstImpl/general"
final_dir = "../data/final/lastImpl/general"
final_oz = "../data/final/lastImpl/onezone"

dist_dir = "../data/final"

old_dir = "../data/phase2ParallelPrefetchOZ"
image_dir = "../images/thesis_images"
part_base_dir = "../data/partTest"

def create_part_chart(bucket: str, algorithm: str):
    # On the x axis we want the parallelism and 
    # on the y axis we want the total running time
    plt.subplots(layout="constrained")

    _, ax = plt.subplots(layout='constrained')
    parallelisms = [1,2,4,6,10,20] 
    for part in [2,16,64,128]:
        running_times = []
        for p in parallelisms:
            file_name = f"{part_base_dir}/part{part}_{bucket}/s3_{algorithm}_{p}_10.txt"
            times, _ = common.read_file(file_name)
            total_running_time = common.sum_time(times)/p
            print(f"At {p} with {part} = {total_running_time}")
            running_times.append(total_running_time)
        ax.plot(parallelisms, running_times, label=f"{part}MB", marker='o')

    ax.set_ylabel("Running time seconds")
    ax.set_xlabel("Parallelism")
    ax.set_title("Partition size impact (BFS)")
    ax.legend(loc='upper right', ncols=1)
    plt.savefig(f"{image_dir}/part_cmp_{bucket}_{algorithm}.png")
    plt.close()

def pie_chart(name: str, pie_info: dict[str, int]):
    fig, ax = plt.subplots()
    labels = [k for k in pie_info]
    values = [pie_info[k] for k in pie_info]
    ax.pie(values, labels=labels, autopct='%1.1f%%')

    plt.savefig(name)
    plt.close()

def create_distributed_chart():
    parallelisms = [10, 20, 40]
    one_instance, two_instances = [], []
    for p in parallelisms:
        times, _ = common.read_file(f"{dist_dir}/distributed_general_one/s3_bfsp_{p}_10.txt")
        one_instance.append(common.sum_time(times)/p)

        times, _ = common.read_file(f"{dist_dir}/distributed_general_two/s3_bfsp_{p}_10.txt")
        two_instances.append(common.sum_time(times)/p)
    times_dict = {"One Instance": one_instance, "Two Instances": two_instances}
    chart(f"{image_dir}/distributed.png", times_dict, [str(i) for i in parallelisms],
          scale="linear", ylim_low = 0, ylim_high=50, xlabel="Parallelism", 
          ylabel="Running time Seconds", title="Total running time SF-10 BFS")

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

def create_onezone_charts():
    parallelism = 1
    for algo in ['BFS', 'DFS']:
        a_name = None
        if algo == "BFS":
            a_name = "bfsp"
        else:
            a_name = "dfspe"
        oz, _ = common.read_file(f"{final_oz}/s3_{a_name}_{parallelism}_10.txt")
        general, _ = common.read_file(f"{final_dir}/s3_{a_name}_{parallelism}_10.txt")

        labels = []
        for query in range(1,8):
            labels.append(f"Q-{query}\n{(query+1)//2}-Hop")

        times = {"General": [], "One-Zone": []}

        for i in range(7):
            times["General"].append(common.avg(general[20*i:20*(i+1)]))
            times["One-Zone"].append(common.avg(oz[20*i:20*(i+1)]))

        chart(f"{image_dir}/{algo}_cmp_oz.png", times, labels, 
              title=f"Average time ({algo})",
              ylim_low=1, ylim_high=1_000_000)

def create_parallelism_charts():
    times_dict = {}
    for algo in ["bfsp", "dfspe"]:
        running_times = []
        for p in [1,4,6,10,20]:
            times, _ = common.read_file(f"{final_dir}/s3_{algo}_{p}_10.txt")
            wall_clock_seconds = common.sum_time(times)/p
            running_times.append(wall_clock_seconds)
        if algo == "bfsp":
            times_dict["BFS"] = running_times
        elif algo == "dfspe":
            times_dict["DFS"] = running_times
        else:
            raise AssertionError()

    chart(f"{image_dir}/parallelism.png", times_dict, 
          [str(i) for i in parallelisms], scale="linear", ylim_low=0, ylim_high=80,
          xlabel="Parallelism", ylabel="Wall clock time (seconds)",
          title="Workload running time")

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

    _, seq_dfs_stats = common.read_file(f"{old_dir}/s3_dfs_1_10.txt")
    hits = get_hits(seq_dfs_stats)
    pie_chart(f"{image_dir}/pie_dfs_seq.png", hits)

    _, seq_bfs_stats = common.read_file(f"{old_dir}/s3_bfs_1_10.txt")
    hits = get_hits(seq_bfs_stats)
    pie_chart(f"{image_dir}/pie_bfs_seq.png", hits)

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
    # create_pie_chart()
    # create_parallelism_charts()
    # create_onezone_charts()
    # create_part_chart("general", "bfsp")
    create_distributed_chart()

if __name__ == "__main__":
    main()
