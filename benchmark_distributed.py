import time
import argparse

import lib.buildUtil
from lib.cfUtil import CfUtil
from lib.sshUtil import SshUtil


general_buckets = {
        "bucket1": "s3graphtest1",
        "bucket10": "s3graphtest10"
        }

onezone_buckets = {
        "bucket1": "s3graphtest1oz--use1-az6--x-s3",
        "bucket10": "s3graphtest10oz--use1-az6--x-s3"
        }

scaling_factors = ["10"]
# scaling_factors = ["1", "10"]

def run_tests(ips: tuple[str,str,str], buckets: dict[str, str], accessor: str):
    # Build and copy the binaries.
    lib.buildUtil.build_graph_access()
    lib.buildUtil.build_graph_algorithm()
    print("Built binaries for graph access and algorithm service")

    lib.buildUtil.copy_algorithm_files(ips[0])
    for i in range(1, len(ips)):
        lib.buildUtil.copy_access_files(ips[i])

    print("Copied required files to the destination servers")

    algo = SshUtil(ips[0])
    access_services = []
    for i in range(1, len(ips)):
        access_services.append(SshUtil(ips[i]))
    for sf in scaling_factors:
        access_pids = []
        for access_service in access_services:
            pid = access_service.run_access_service(buckets["bucket" + sf], accessor)
            access_pids.append(pid)

        time.sleep(10)
        algo.run_dist_algorithm_service(sf, ips[1:], reps=100,
                                        algos=["bfsp"], parallelism=["10", "20", "40"])

        for idx, access_service in enumerate(access_services):
            access_service.kill_access_service(access_pids[idx])

    algo.close()
    for access_service in access_services:
        access_service.close()

def main():
    parser = argparse.ArgumentParser(prog='BenchmarkScript',
                                     description="Creates benchmarks")
    parser.add_argument('-b', '--bucket-type', choices=["general", "onezone"])
    parser.add_argument('-a', '--accessor', choices=["prefetch", "offset", "simple"])
    parser.add_argument('-r', '--remove', action='store_true')
    parser.add_argument('-d', '--directory')

    args = parser.parse_args()
    if args.bucket_type == 'general':
        print("Using general buckets")
        buckets = general_buckets
    else:
        print("Using OneZone buckets")
        buckets = onezone_buckets
    cf = CfUtil()

    if not cf.stack_exists():
        cf.create_dist_stack()
        cf.await_dist_stack_creation()

    ips = cf.get_dist_ips()
    assert len(ips) == 3
    print(f"Created instances with IPs: {ips}")

    # For two instances
    # run_tests(ips, buckets, args.accessor)
    # For single instance
    run_tests(ips[:-1], buckets, args.accessor)

    # Ip 0 is for access service rest are for algo
    lib.buildUtil.copy_results(ips[0], args.directory)

    if args.remove:
        cf.delete_dist_stack()
        cf.await_dist_stack_deletion()

if __name__ == "__main__":
    main()
