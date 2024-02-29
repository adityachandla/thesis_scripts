import time
import os
from cfUtill import CfUtil
from sshUtil import SshUtil

access_dir = "../graph_access_service"
algorithm_dir = "../graph_algorithm_service"

bucket10 = "s3graphtest10oz--use1-az6--x-s3"
bucket1 = "s3graphtest1oz--use1-az6--x-s3"

scp_prefix = "scp -o StrictHostKeyChecking=accept-new"

def copy_to_server(ip:str, path_to_copy: str):
    os.system(f"{scp_prefix} -i {ssh_key} {path_to_copy} ubuntu@{ip}:~/")

def build_graph_access():
    os.system("rm -f {access_dir}/access")
    os.system(f"(cd {access_dir} && GOARCH=arm64  make access)")
    os.system(f"mv {access_dir}/access .")

def copy_access_files(ip: str):
    copy_to_server(ip, "./access")

def build_graph_algorithm():
    os.system("rm -f {algorithm_dir}/algo")
    os.system(f"(cd {algorithm_dir} && GOARCH=arm64 make algo)")
    os.system(f"mv {algorithm_dir}/algo .")

def copy_algorithm_files(ip: str):
    copy_to_server(ip, "./algo")
    files = ["run_variations_s3.sh", "*.csv","queries.txt"]
    for file in files:
        copy_to_server(ip, f"{algorithm_dir}/{file}")

def copy_results(ip: str):
    os.system(f"{scp_prefix} -i {ssh_key} ubuntu@{ip}:{path_to_copy} .")

def main():
    cf = CfUtil()
    cf.create_instance_stack(cf_client)

    cf.await_stack_creation(cf_client)

    ip = cf.get_ip_address(cf_client)
    print(f"Created instance with IP: {ip}")

    # Build and copy the binaries.
    build_graph_access()
    build_graph_algorithm()
    print("Built binaries for graph access and algorithm service")

    copy_access_files(ip)
    copy_algorithm_files(ip)
    print("Copied required files to the destination")

    ssh = SshUtil(ip)
    pid = ssh.run_access_service(ssh, bucket10)
    time.sleep(2)
    ssh.run_algorithm_service("10")
    ssh.kill_access_service( pid)
    ssh.close()

    copy_results(ip)

    cf.delete_instance_stack(cf_client)
    cf.await_stack_deletion(cf_client)

if __name__ == "__main__":
    main()
