import paramiko

ssh_key = "/home/aditya/Downloads/graphDbVirginia.pem"

default_algos = ["bfs", "dfs", "bfsp", "dfsp"]
default_parallelism = ["1", "2"]

class SshUtil:

    def __init__(self, ip):
        key = paramiko.RSAKey.from_private_key_file(ssh_key)
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(ip, username="ubuntu", pkey=key)

    def run_access_service(self, bucket: str, accessor: str) -> int:
        command = f"./access --bucket {bucket} --accessor {accessor} --nolog"
        self.ssh.exec_command(f"nohup {command} > server.log 2>&1< /dev/null &")

        _, out, _ = self.ssh.exec_command(f"ps -C access -o pid=")
        print("Started access service")
        return int(out.read().decode().strip())

    def run_algorithm_service(self, sf: str, 
                              algos: list[str] = default_algos, parallelism: list[str] = default_parallelism):
        reps = 20
        for p in parallelism:
            for a in algos:
                command = f"./algo --parallelism {p} --repetitions {reps} --algorithm {a} "
                command += f"--nodeMap nodeMap{sf}.csv "
                command += f">> s3_{a}_{p}_{sf}.txt 2>&1"
                _, out, _ = self.ssh.exec_command(command)
                out.channel.recv_exit_status()
                print(f"Finished {a} with parallelism={p}")

    def run_single_service(self, sf: str, bucket: str, accessor: str,
                              algos: list[str] = default_algos, parallelism: list[str] = default_parallelism):
        reps = 20
        for p in parallelism:
            for a in algos:
                command = f"./algo --parallelism {p} --repetitions {reps} --algorithm {a} "
                command += f"--nodeMap nodeMap{sf}.csv "
                command += f"--bucket {bucket} --accessor {accessor} "
                command += f">> s3_{a}_{p}_{sf}.txt 2>&1"
                _, out, _ = self.ssh.exec_command(command)
                out.channel.recv_exit_status()
                print(f"Finished {a} with parallelism={p}")

    def kill_access_service(self, pid: int):
        _, out, _ = self.ssh.exec_command(f"kill {pid}")
        out.channel.recv_exit_status()

    def clean_files(self):
        _, out, _ = self.ssh.exec_command(f"rm -rf ~/s3*.txt")
        out.channel.recv_exit_status()

    def close(self):
        self.ssh.close()

