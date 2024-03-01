import os

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

def copy_results(ip: str, directory: str):
    if not os.path.isdir(directory):
        os.mkdir(directory)
    os.system(f"{scp_prefix} -i {ssh_key} ubuntu@{ip}:{path_to_copy} {directory}")
