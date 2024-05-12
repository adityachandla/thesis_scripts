import time
import os
import argparse

import lib.buildUtil
from lib.cfUtil import CfUtil
from lib.sshUtil import SshUtil


GENERAL_BUCKET = "s3graphtest10"
ONEZONE_BUCKET = "s3graphtest10oz--use1-az6--x-s3"

ACCESSOR = "prefetch"
SCALING_FACTOR = "10"

#PARTITION_SIZES = ["16", "64", "128"]
PARTITION_SIZES = ["64", "128"]
ALGOS = ["bfsp", "dfsp"]
PARALLELISMS = ["4", "6"]

def run_tests(ssh: SshUtil, ip: str, bucket: str):
    # Build and copy the binaries.
    lib.buildUtil.build_graph_access()
    lib.buildUtil.build_graph_algorithm()
    print("Built binaries for graph access and algorithm service")

    lib.buildUtil.copy_access_files(ip)
    lib.buildUtil.copy_algorithm_files(ip)
    print("Copied required files to the destination")

    pid = ssh.run_access_service(bucket, ACCESSOR)
    time.sleep(10)
    ssh.run_algorithm_service(SCALING_FACTOR, algos=ALGOS, parallelism=PARALLELISMS)
    ssh.kill_access_service(pid)

def main():
    parser = argparse.ArgumentParser(prog='Partition size benchmarks', 
                                     description="Runs tests with different partition sizes")
    parser.add_argument('-d', '--directory')

    args = parser.parse_args()
    cf = CfUtil()

    if not cf.stack_exists():
        cf.create_instance_stack()
        cf.await_stack_creation()

    ip = cf.get_ip_address()
    print(f"Using instance with IP: {ip}")

    for part in PARTITION_SIZES:
        os.system(f"(cd ../ldbc_converter ;"
                  f"go run cmd/copier/main.go -src sf10/partTest/ocsr{part} -dest general)")
        print("Copied to general bucket")
        ssh = SshUtil(ip)
        ssh.clean_files()
        # Test with general bucket
        run_tests(ssh, ip, GENERAL_BUCKET)
        lib.buildUtil.copy_results(ip, f"{args.directory}/part{part}_general/")
        ssh.clean_files()

        # Test with onezone bucket
        os.system(f"(cd ../ldbc_converter ;" 
                  f"go run cmd/copier/main.go -src sf10/partTest/ocsr{part} -dest onezone)")
        print("Copied to onezone bucket")
        run_tests(ssh, ip, ONEZONE_BUCKET)
        lib.buildUtil.copy_results(ip, f"{args.directory}/part{part}_onezone/")
        ssh.clean_files()

        print(f"Finished tests for partition of size {part}Mb")
        ssh.close()

    cf.delete_instance_stack()
    cf.await_stack_deletion()

if __name__ == "__main__":
    main()
