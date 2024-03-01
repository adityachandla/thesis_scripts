import time
import argparse

import buildUtil
from cfUtil import CfUtil
from sshUtil import SshUtil

access_dir = "../graph_access_service"
algorithm_dir = "../graph_algorithm_service"

general_buckets = {
        "bucket1": "s3graphtest1",
        "bucket10": "s3graphtest10"
        }

onezone_buckets = {
        "bucket1": "s3graphtest1oz--use1-az6--x-s3",
        "bucket10": "s3graphtest10oz--use1-az6--x-s3"
        }

scaling_factors = ["1", "10"]

def run_tests(ip: str, buckets: dict[str, str]):
    # Build and copy the binaries.
    buildUitl.build_graph_access()
    buildUitl.build_graph_algorithm()
    print("Built binaries for graph access and algorithm service")

    buildUtil.copy_access_files(ip)
    buildUtil.copy_algorithm_files(ip)
    print("Copied required files to the destination")

    ssh = SshUtil(ip)
    for sf in scaling_factors:
        pid = ssh.run_access_service(ssh, buckets["bucket" + sf], args.accessor)
        time.sleep(2)
        ssh.run_algorithm_service(sf)
        ssh.kill_access_service(pid)

    ssh.close()

def main():
    parser = argparse.ArgumentParser(prog='BenchmarkScript', 
                                     description="Creates benchmarks")
    parser.add_argument('-b', '--bucket-type', choices=["general", "onezone"])
    parser.add_argument('-a', '--accessor', choices=["prefetch", "offset", "simple"])
    parser.add_argument('-d', '--directory')

    args = parser.parse_args()
    if args.bucket_type == 'general':
        print("Using general buckets")
        buckets = general_buckets
    else:
        print("Using OneZone buckets")
        buckets = onezone_buckets
    cf = CfUtil()

    if not cf.stack_exists()
        cf.create_instance_stack()
        cf.await_stack_creation()

    ip = cf.get_ip_address()
    print(f"Created instance with IP: {ip}")

    run_tests(ip, buckets)
    buildUtil.copy_results(ip, dir)

    cf.delete_instance_stack()
    cf.await_stack_deletion()

if __name__ == "__main__":
    main()
