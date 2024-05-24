import common

base_dir_single = "../data/singleService/16m_general/"
base_dir_normal = "../data/partTest/part16_general/"

image_dir = "../images/singleService/"

algorithms = ["bfsp", "dfsp"]
parallelism = [4,6,10,20]

def compare_algo(algo: str):
    running_times_single = []
    running_times_normal = []

    res = {"Single Service": [], "Normal": []}
    for p in parallelism:
        single_res, _ = common.read_file(f"{base_dir_single}s3_{algo}_{p}_10.txt")
        res["Single Service"].append(common.sum_time(single_res))

        normal_res, _ = common.read_file(f"{base_dir_normal}s3_{algo}_{p}_10.txt")
        res["Normal"].append(common.sum_time(normal_res))
    path = f"{image_dir}cmp_{algo}.png"
    common.chart(path, res, [str(i) for i in parallelism], 
                 legend_loc="upper left", ylim_low=10, ylim_high=150, scale="linear")

def main():
    for alg in algorithms:
        compare_algo(alg)

if __name__ == "__main__":
    main()
