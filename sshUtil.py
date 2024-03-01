import paramiko

ssh_key = "/home/aditya/Downloads/graphDbVirginia.pem"

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
        return int(out.read().decode().strip())

    def run_algorithm_service(self, sf: str):
        algos = ["bfs", "dfs"]
        parallelism = ["1", "2"]
        reps = 20
        for p in parallelism:
            for a in algos:
                command = f"./algo --parallelism {p} --repetitions {reps} --algorithm {a} "
                command += f"--nodeMap nodeMap{sf}.csv "
                command += f">> s3_{a}_{p}_{sf}.txt 2>&1"
                _, out, _ = self.ssh_client.exec_command(command)
                out.channel.recv_exit_status()
                print(f"Finished {a} with parallelism={p}")

    def kill_access_service(self, pid: int):
        self.ssh.exec_command(f"kill {pid}")

    def close(self):
        self.ssh.close()

