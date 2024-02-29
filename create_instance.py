import time
import os
import boto3
import paramiko
from cfUtill import CfUtil

stack_name = "GraphInstanceStack"
instance_type = "c7gn.large"
access_dir = "../graph_access_service"

bucket10 = "s3graphtest10oz--use1-az6--x-s3"
bucket1 = "s3graphtest1oz--use1-az6--x-s3"

algorithm_dir = "../graph_algorithm_service"
ssh_key = "/home/aditya/Downloads/graphDbVirginia.pem"

scp_prefix = "scp -o StrictHostKeyChecking=accept-new"

def copy_to_server(ip:str, path_to_copy: str):
    os.system(f"{scp_prefix} -i {ssh_key} {path_to_copy} ubuntu@{ip}:~/")

def copy_from_server(ip:str, path_to_copy: str):
    os.system(f"{scp_prefix} -i {ssh_key} ubuntu@{ip}:{path_to_copy} .")

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

def get_connection(ip: str) -> paramiko.SSHClient:
    key = paramiko.RSAKey.from_private_key_file(ssh_key)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username="ubuntu", pkey=key)
    return ssh

def copy_results(ip: str):
    copy_from_server(ip, "s3*.txt")

def run_access_service(ssh_client, bucket) -> int:
    command = f"./access --bucket {bucket} --nolog"
    ssh_client.exec_command(f"nohup {command} > server.log 2>&1< /dev/null &")

    _, out, _ = ssh_client.exec_command(f"ps -C access -o pid=")
    return int(out.read().decode().strip())

def run_algorithm_service(ssh_client, sf):
    algos = ["bfs", "dfs"]
    parallelism = ["1", "2"]
    reps = 20
    for p in parallelism:
        for a in algos:
            command = f"./algo --parallelism {p} --repetitions {reps} --algorithm {a} "
            command += f"--nodeMap nodeMap{sf}.csv "
            command += f">> s3_{a}_{p}_{sf}.txt 2>&1"
            _, out, _ = ssh_client.exec_command(command)
            out.channel.recv_exit_status()
            print(f"Finished {a} with parallelism={p}")

def kill_access_service(ssh_client, pid):
    ssh_client.exec_command(f"kill {pid}")

def main():
    cf = CfUtil()
    stack_id = create_instance_stack(cf_client)

    print(f"started stack creation with StackID:{stack_id}")
    await_stack_creation(cf_client)

    ip = get_ip_address(cf_client)
    print(f"Created instance with IP: {ip}")

    # Build and copy the binaries.
    build_graph_access()
    build_graph_algorithm()
    print("Built binaries for graph access and algorithm service")

    copy_access_files(ip)
    copy_algorithm_files(ip)
    print("Copied required files to the destination")

    ssh = get_connection(ip)
    pid = run_access_service(ssh, bucket10)
    time.sleep(2)
    run_algorithm_service(ssh, "10")
    kill_access_service(ssh, pid)
    ssh.close()

    copy_results(ip)

    delete_instance_stack(cf_client)
    print("Triggered deletion")
    await_stack_deletion(cf_client)
    print("Stack deleted")

if __name__ == "__main__":
    main()
