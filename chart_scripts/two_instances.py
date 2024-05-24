import common

base_dir_multi_one = "../data/twoInstances_16m/one_general/"
base_dir_multi_two = "../data/twoInstances_16m/two_general/"

base_dir_normal = "../data/partTest/part16_general/"

image_dir = "../images/twoInstances/"

algorithms = ["bfsp"]
parallelism = [4,6,10,20]

def compare_algo(algo: str):
    running_times_single = []
    running_times_normal = []

    res = {"Two Instance (Avg)": [], "Normal": []}
    for p in parallelism:
        s = 0
        two_res_one, _ = common.read_file(f"{base_dir_multi_one}s3_{algo}_{p}_10.txt")
        s += common.sum_time(two_res_one)
        two_res_two, _ = common.read_file(f"{base_dir_multi_two}s3_{algo}_{p}_10.txt")
        s += common.sum_time(two_res_two)
        res["Two Instance (Avg)"].append(s/2)


        normal_res, _ = common.read_file(f"{base_dir_normal}s3_{algo}_{p}_10.txt")
        res["Normal"].append(common.sum_time(normal_res))
    path = f"{image_dir}cmp_{algo}.png"
    common.chart(path, res, [str(i) for i in parallelism], 
                 legend_loc="upper left", ylim_low=10, ylim_high=80, scale="linear")

def main():
    for alg in algorithms:
        compare_algo(alg)

if __name__ == "__main__":
    main()
