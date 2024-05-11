import time
import os
import argparse

import buildUtil
from cfUtil import CfUtil
from sshUtil import SshUtil


GENERAL_BUCKET = "s3graphtest10"
ONEZONE_BUCKET = "s3graphtest10oz--use1-az6--x-s3"

ACCESSOR = "prefetch"
SCALING_FACTOR = "10"

PARTITION_SIZES = ["16", "64", "128"]

def run_tests(ip: str, bucket: str, accessor: str):
    # Build and copy the binaries.
    buildUtil.build_graph_access()
    buildUtil.build_graph_algorithm()
    print("Built binaries for graph access and algorithm service")

    buildUtil.copy_access_files(ip)
    buildUtil.copy_algorithm_files(ip)
    print("Copied required files to the destination")

    ssh = SshUtil(ip)
    pid = ssh.run_access_service(bucket, accessor)
    time.sleep(2)
    ssh.run_algorithm_service(SCALING_FACTOR)
    ssh.kill_access_service(pid)

    ssh.clean_files()
    ssh.close()

def prepare_partition(size: str):
    # Copy the csr to both buckets
    os.system(f"(cd ../ldbc_converter ;" 
              f"go run cmd/copier/main.go -src sf10/partTest/ocsr{size} -dest onezone)")
    print("Copied to general bucket")
    os.system(f"(cd ../ldbc_converter ;"
              f"go run cmd/copier/main.go -src sf10/partTest/ocsr{size} -dest general)")
    print("Copied to onezone bucket")

def main():
    parser = argparse.ArgumentParser(prog='Partition size benchmarks', 
                                     description="Runs tests with different partition sizes")
    parser.add_argument('-d', '--directory')

    args = parser.parse_args()
    cf = CfUtil()

    if not cf.stack_exists():
        cf.create_instance_stack()

    ip = cf.get_ip_address()
    print(f"Created instance with IP: {ip}")

    for part in PARTITION_SIZES:
        prepare_partition(part)
        print(f"Prepared partitoin of size {part}Mb")
        
        cf.await_stack_creation()

        # Test with general bucket
        run_tests(ip, GENERAL_BUCKET, ACCESSOR)
        buildUtil.copy_results(ip, f"{args.directory}/part{part}_general/")

        # Test with onezone bucket
        run_tests(ip, ONEZONE_BUCKET, ACCESSOR)
        buildUtil.copy_results(ip, f"{args.directory}/part{part}_onezone/")

        print(f"Finished tests for partition of size {part}Mb")

    cf.delete_instance_stack()
    cf.await_stack_deletion()

if __name__ == "__main__":
    main()
