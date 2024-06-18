import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import seaborn as sns
import numpy as np
import common

baseline_dir = "../data/final/firstImpl/general"
final_dir = "../data/final/lastImpl/general"
final_oz = "../data/final/lastImpl/onezone"
neo4j_dir = "../data/neo4jData"
neo4j_fabric_dir = "../data/neo4jFabricData"

dist_dir = "../data/final"

old_dir = "../data/phase2ParallelPrefetchOZ"
image_dir = "../images/thesis_images"
part_base_dir = "../data/partTest"

def avg(l: list[float]) -> float:
    return sum(l)/len(l)

def compare_n(low_level: str, traversal: str, cypher: str, s3_file: str, image_file: str):
    low_level_times = common.read_neo_file(low_level)
    traversal_times = common.read_neo_file(traversal)
    cypher_times = common.read_neo_file(cypher)
    s3_times, _ = common.read_file(s3_file)

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
    common.chart(image_file, values, labels, ylim_low=0.01, ylim_high=100_000,
                 title="Average time", fmt="{:,.1f}", width=0.2)

def add_dir(filenames: list[str], directory: str) -> list[str]:
    return [directory+"/"+i for i in filenames]

def create_neo4j_charts():
    s3 = add_dir(["s3_bfsp_1_1.txt", "s3_dfspe_1_1.txt"], final_oz)
    low_level = add_dir(["ll_bfs.txt", "ll_dfs.txt"], neo4j_dir)
    traversal = add_dir(["traversal_bfs.txt", "traversal_dfs.txt"], neo4j_dir)
    cypher = add_dir(["cypher.txt", "cypher.txt"], neo4j_dir)
    file_names = add_dir(["neo4j_bfs_query.png", "neo4j_dfs_query.png"], image_dir)

    for i in range(len(file_names)):
        compare_n(low_level[i], traversal[i], cypher[i], s3[i], file_names[i])

def compare_fabric(fabric: str, s3_oz_file: str, s3_general_file: str, image_file: str):
    fabric_times = common.read_fabric_file(fabric)
    s3_oz_times, _ = common.read_file(s3_oz_file)
    s3_general_times, _ = common.read_file(s3_general_file)

    labels = ["Q"+str(i) for i in range(1,8)]
    values = {"Neo4J Fabric": list(), "S3 OZ": list(), "S3 General": list()}
    for i in range(7):
        fab_avg = avg(fabric_times[(20*i)+1:20*(i+1)])
        values["Neo4J Fabric"].append(fab_avg)

        s3_oz_avg = avg([res.time for res in s3_oz_times[20*i:20*(i+1)]])
        values["S3 OZ"].append(s3_oz_avg)

        s3_gen_avg = avg([res.time for res in s3_general_times[20*i:20*(i+1)]])
        values["S3 General"].append(s3_gen_avg)

    # TODO change title and stuff
    common.chart(image_file, values, labels, width=0.22)

def create_neo4j_fabric_charts():
    s3_oz = add_dir(["s3_bfsp_1_1.txt", "s3_dfspe_1_1.txt"], final_oz)
    s3_general = add_dir(["s3_bfsp_1_1.txt", "s3_dfspe_1_1.txt"], final_dir)
    fabric = neo4j_fabric_dir + "/res_alternate.txt"
    file_names = add_dir(["fabric_bfs_cmp.png", "fabric_dfs_cmp.png"], image_dir)

    compare_fabric(fabric, s3_oz[0], s3_general[0], file_names[0])
    compare_fabric(fabric, s3_oz[1], s3_general[1], file_names[1])

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
    # For xlarge
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

    # For 2x large
    one_instance, two_instances = [], []
    for p in parallelisms:
        times, _ = common.read_file(
                f"{dist_dir}/distributed_general_one_2xlarge/s3_bfsp_{p}_10.txt")
        one_instance.append(common.sum_time(times)/p)

        times, _ = common.read_file(
                f"{dist_dir}/distributed_general_two_2xlarge/s3_bfsp_{p}_10.txt")
        two_instances.append(common.sum_time(times)/p)

    times_dict = {"One Instance": one_instance, "Two Instances": two_instances}
    common.chart(f"{image_dir}/distributed_large.png", times_dict, [str(i) for i in parallelisms],
          scale="linear", ylim_low = 0, ylim_high=50, xlabel="Parallelism", 
          ylabel="Running time Seconds", title="Total running time SF-10 BFS")

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

        common.chart(f"{image_dir}/{algo}_cmp_oz.png", times, labels, 
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

    common.chart(f"{image_dir}/parallelism.png", times_dict, 
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

            common.chart(f"{image_dir}/{algo}_cmp_{sf}.png", times, labels, 
                  title=f"Average time ({algo}) SF-{sf}",
                  ylim_low=1, ylim_high=1_000_000)


def main():
    # create_baseline_comparison()
    # create_pie_chart()
    # create_parallelism_charts()
    # create_onezone_charts()
    # create_part_chart("general", "bfsp")
    # create_distributed_chart()
    create_neo4j_charts()
    create_neo4j_fabric_charts()

if __name__ == "__main__":
    main()
