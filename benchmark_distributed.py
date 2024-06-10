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

scaling_factors = ["1", "10"]

def run_tests(ips: tuple[str,str,str], buckets: dict[str, str], accessor: str):
    # Build and copy the binaries.
    lib.buildUtil.build_graph_access()
    lib.buildUtil.build_graph_algorithm()
    print("Built binaries for graph access and algorithm service")

    lib.buildUtil.copy_access_files(ip[1])
    lib.buildUtil.copy_access_files(ip[2])
    lib.buildUtil.copy_algorithm_files(ip[0])
    print("Copied required files to the destination servers")

    access1 = SshUtil(ip[1])
    access2 = SshUtil(ip[2])
    algo = SshUtil(ip[0])
    for sf in scaling_factors:
        pid1 = access1.run_access_service(buckets["bucket" + sf], accessor)
        pid2 = access2.run_access_service(buckets["bucket" + sf], accessor)

        time.sleep(5)
        algo.run_algorithm_service(sf, algos=["bfsp", "dfspe"], parallelism=["1", "4", "6", "10", "20"])

        access1.kill_access_service(pid1)
        access2.kill_access_service(pid2)

    ssh.close()

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
    print(f"Created instances with IPs: {ip}")

    run_tests(ips, buckets, args.accessor)
    # Ip 0 is for access service rest are for algo
    lib.buildUtil.copy_results(ip[0], args.directory)

    if args.remove:
        cf.delete_dist_stack()
        cf.await_dist_stack_deletion()

if __name__ == "__main__":
    main()
