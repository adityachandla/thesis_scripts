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

def run_tests(ip: str, buckets: dict[str, str], accessor: str):
    # Build and copy the binaries.
    lib.buildUtil.build_graph_access()
    lib.buildUtil.build_graph_algorithm()
    print("Built binaries for graph access and algorithm service")

    lib.buildUtil.copy_access_files(ip)
    lib.buildUtil.copy_algorithm_files(ip)
    print("Copied required files to the destination")

    ssh = SshUtil(ip)
    for sf in scaling_factors:
        pid = ssh.run_access_service(buckets["bucket" + sf], accessor)
        time.sleep(5)
        ssh.run_algorithm_service(sf, algos=["bfsp"], parallelism=["20"])
        ssh.kill_access_service(pid)

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
        cf.create_instance_stack()
        cf.await_stack_creation()

    ip = cf.get_ip_address()
    print(f"Created instance with IP: {ip}")

    run_tests(ip, buckets, args.accessor)
    lib.buildUtil.copy_results(ip, args.directory)

    if args.remove:
        cf.delete_instance_stack()
        cf.await_stack_deletion()

if __name__ == "__main__":
    main()
