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

def run_tests(ip: str, buckets: dict[str, str], accessor):
    # Build and copy the binaries.
    lib.buildUtil.build_graph_algorithm()
    print("Built binaries for graph algorithm service")

    lib.buildUtil.copy_algorithm_files(ip)
    print("Copied required files to the destination")

    algorithms = ["bfsp", "dfsp"]
    parallelisms = ["4", "6", "8"]
    ssh = SshUtil(ip)
    sf = "10"
    ssh.run_single_service(sf, buckets["bucket" + sf], accessor,
                              algorithms, parallelisms)
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
