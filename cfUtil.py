import boto3

stack_name = "GraphInstanceStack"
instance_type = "c7gn.xlarge"
cf_stack_file = "ec2_cf.yaml"

class CfUtil:
    def __init__(self):
        self.client = boto3.client("cloudformation")

    def _read_file(self, name: str) -> str:
        with open(name, "r") as f:
            return f.read()

    def create_instance_stack(self) -> str:
        instance_parameter = dict()
        instance_parameter["ParameterKey"] = "InstanceTypeParameter"
        instance_parameter["ParameterValue"] = instance_type

        response = self.client.create_stack(StackName=stack_name, 
                                       Parameters=[instance_parameter],
                                       TemplateBody=self._read_file(cf_stack_file),
                                       Capabilities=["CAPABILITY_IAM"])
        print(f"started stack creation with StackID:{response['StackId']}")
        return response['StackId']

    def await_stack_creation(self):
        waiter = self.client.get_waiter("stack_create_complete")
        waiter.wait(StackName=stack_name)

    def stack_exists(self) -> bool:
        statuses = ['CREATE_IN_PROGRESS', 'CREATE_COMPLETE']
        r = self.client.list_stacks(StackStatusFilter=statuses)
        return len(r['StackSummaries']) > 0

    def get_ip_address(self) -> str:
        response = self.client.describe_stacks(StackName=stack_name)
        try:
            return response["Stacks"][0]["Outputs"][0]["OutputValue"]
        except:
            print("Invalid response while trying to get ip address.")
            print(response)
            raise Exception("IP address not found")

    def delete_instance_stack(self):
        self.client.delete_stack(StackName=stack_name)
        print("Triggered deletion")

    def await_stack_deletion(self):
        waiter = self.client.get_waiter("stack_delete_complete")
        waiter.wait(StackName=stack_name)
        print("Stack deleted")
