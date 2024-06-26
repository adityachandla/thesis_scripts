import boto3

stack_name = "GraphInstanceStack"
instance_type = "c7gn.xlarge"
cf_stack_file = "config/ec2_cf.yaml"

dist_stack_name = "GraphInstanceStackDist"
dist_instance_type = "c7gn.xlarge"
dist_cf_stack_file = "config/ec2_multi_cf.yaml"

neo_stack_name = "NeoInstancesStack"
neo_stack_file = "config/ec2_neo4j.yaml"
neo_instance_type = "t4g.medium"


class CfUtil:
    def __init__(self):
        self.client = boto3.client("cloudformation")

    def _read_file(self, name: str) -> str:
        with open(name, "r") as f:
            return f.read()

    def create_instance_stack(self) -> str:
        return self._create_stack(stack_name, cf_stack_file, instance_type)

    def create_neo_stack(self) -> str:
        return self._create_stack(neo_stack_name, neo_stack_file, neo_instance_type)

    def create_dist_stack(self) -> str:
        return self._create_stack(dist_stack_name, dist_cf_stack_file, dist_instance_type)

    def _create_stack(self, s_name: str, file: str, inst_type: str) -> str:
        instance_parameter = dict()
        instance_parameter["ParameterKey"] = "InstanceTypeParameter"
        instance_parameter["ParameterValue"] = inst_type

        response = self.client.create_stack(StackName=s_name, 
                                       Parameters=[instance_parameter],
                                       TemplateBody=self._read_file(file),
                                       Capabilities=["CAPABILITY_IAM"])
        print(f"started stack creation with StackID:{response['StackId']}")
        return response['StackId']

    def await_stack_creation(self):
        waiter = self.client.get_waiter("stack_create_complete")
        waiter.wait(StackName=stack_name)

    def await_dist_stack_creation(self):
        waiter = self.client.get_waiter("stack_create_complete")
        waiter.wait(StackName=dist_stack_name)

    def await_neo_stack_creation(self):
        waiter = self.client.get_waiter("stack_create_complete")
        waiter.wait(StackName=neo_stack_name)

    def stack_exists(self) -> bool:
        statuses = []
        r = self.client.list_stacks(StackStatusFilter=['CREATE_COMPLETE'])
        if len(r['StackSummaries']) > 0:
            return True
        r = self.client.list_stacks(StackStatusFilter=['CREATE_IN_PROGRESS'])
        if len(r['StackSummaries']) > 0:
            self.await_stack_creation()
            return True
        return False

    def get_ip_address(self) -> str:
        response = self.client.describe_stacks(StackName=stack_name)
        try:
            return response["Stacks"][0]["Outputs"][0]["OutputValue"]
        except:
            print("Invalid response while trying to get ip address.")
            print(response)
            raise Exception("IP address not found")

    def get_neo_ips(self) -> tuple[str,str]:
        response = self.client.describe_stacks(StackName=neo_stack_name)
        try:
            return (response["Stacks"][0]["Outputs"][0]["OutputValue"],
                    response["Stacks"][0]["Outputs"][1]["OutputValue"])
        except:
            print("Invalid response while trying to get ip address.")
            print(response)
            raise Exception("IP address not found")

    def get_dist_ips(self) -> tuple[str,str,str]:
        response = self.client.describe_stacks(StackName=dist_stack_name)
        try:
            return (response["Stacks"][0]["Outputs"][0]["OutputValue"],
                    response["Stacks"][0]["Outputs"][1]["OutputValue"],
                    response["Stacks"][0]["Outputs"][2]["OutputValue"])
        except:
            print("Invalid response while trying to get ip address.")
            print(response)
            raise Exception("IP address not found")

    def delete_instance_stack(self):
        self.client.delete_stack(StackName=stack_name)
        print("Triggered deletion")

    def delete_dist_stack(self):
        self.client.delete_stack(StackName=dist_stack_name)
        print("Triggered deletion")

    def await_stack_deletion(self):
        waiter = self.client.get_waiter("stack_delete_complete")
        waiter.wait(StackName=stack_name)
        print("Stack deleted")

    def await_dist_stack_deletion(self):
        waiter = self.client.get_waiter("stack_delete_complete")
        waiter.wait(StackName=dist_stack_name)
        print("Stack deleted")
