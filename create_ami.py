import boto3
import time
import subprocess
import os
from typing import Any
import argparse


def create_ami(
    base_ami: str,
    ami_name: str,
    region: str,
    subnet_id: str,
    security_group: str,
    key_name: str,
    key_path: str,
) -> None:
    ec2 = boto3.resource("ec2", region_name=region)
    client = boto3.client("ec2", region_name=region)

    try:
        # Step 1: Launch an EC2 instance in the specified subnet
        print("Launching EC2 instance...")
        instance = ec2.create_instances(
            ImageId=base_ami,
            MinCount=1,
            MaxCount=1,
            InstanceType="t2.micro",
            KeyName=key_name,
            NetworkInterfaces=[
                {
                    "SubnetId": subnet_id,
                    "DeviceIndex": 0,
                    "AssociatePublicIpAddress": False,  # Ensure no public IP
                    "Groups": [security_group],
                }
            ],
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": f"Temp instance to create: {ami_name}"}
                    ],
                }
            ],
        )[0]

        # Wait for the instance to be running
        print("Waiting for the instance to run...")
        instance.wait_until_running()
        instance.load()

        # Use the private IP address for the SSH connection
        target_ip = instance.private_ip_address
        print(f"Connecting to instance at private IP: {target_ip}")

        # Step 2: Run the initialization script
        print("Running init.sh script...")
        if not os.path.exists(key_path):
            raise FileNotFoundError(
                f"The private key file '{key_path}' does not exist."
            )

        command: str = (
            f"ssh -o StrictHostKeyChecking=no -i {key_path} ec2-user@{target_ip} 'bash -s' < init.sh"
        )
        subprocess.run(command, shell=True, check=True)

        # Step 3: Stop the instance
        print("Stopping the instance...")
        instance.stop()
        instance.wait_until_stopped()

        # Step 4: Create an AMI
        print("Creating AMI...")
        response: Any = client.create_image(
            InstanceId=instance.id, Name=ami_name, NoReboot=True
        )

        ami_id: str = response["ImageId"]

        # Wait for the AMI to become available
        print(f"Waiting for the AMI {ami_id} to become available...")
        waiter = client.get_waiter("image_available")
        waiter.wait(ImageIds=[ami_id])

        # Step 5: Terminate the instance
        print("Terminating the instance...")
        instance.terminate()
        instance.wait_until_terminated()

        print(f"AMI: {ami_id}")

    except Exception as e:
        print(f"ERROR: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an AMI from a base AMI.")
    parser.add_argument("--base_ami", type=str, required=True, help="The base AMI ID.")
    parser.add_argument(
        "--ami_name", type=str, required=True, help="The name of the new AMI."
    )
    parser.add_argument(
        "--region", type=str, required=True, help="The AWS region to use."
    )
    parser.add_argument(
        "--subnet_id", type=str, required=True, help="The Subnet ID to use."
    )
    parser.add_argument(
        "--security_group", type=str, required=True, help="The Security Group ID."
    )
    parser.add_argument(
        "--key_name", type=str, required=True, help="The AWS Key Pair name."
    )
    parser.add_argument(
        "--key_path", type=str, required=True, help="Path to the private key file."
    )

    args = parser.parse_args()

    create_ami(
        args.base_ami,
        args.ami_name,
        args.region,
        args.subnet_id,
        args.security_group,
        args.key_name,
        args.key_path,
    )