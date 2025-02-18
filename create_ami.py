import boto3
import time
import subprocess
import os
from typing import Any
import argparse


def wait_for_ssh(
    target_ip: str, key_path: str, retries: int = 10, delay: int = 10
) -> None:
    """
    Waits for the SSH service on the instance to become available.

    :param target_ip: Private IP of the instance.
    :param key_path: Path to the SSH private key.
    :param retries: Number of retry attempts.
    :param delay: Delay between retries in seconds.
    """
    print(f"Waiting for SSH to become available on {target_ip}...")
    for attempt in range(retries):
        try:
            command = [
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=5",
                "-i",
                key_path,
                f"ec2-user@{target_ip}",
                "true",
            ]
            result = subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            print("SSH is now available.")
            return
        except subprocess.CalledProcessError as e:
            print(f"Attempt {attempt + 1}/{retries} failed: {e.stderr.strip()}")
            time.sleep(delay)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            time.sleep(delay)

    raise TimeoutError(
        f"SSH did not become available on {target_ip} after {retries * delay} seconds."
    )


def create_ami(
    base_ami: str,
    ami_name: str,
    region: str,
    subnet_id: str,
    security_group: str,
    key_name: str,
    key_path: str,
    volume_size: int,
) -> None:
    ec2 = boto3.resource("ec2", region_name=region)
    client = boto3.client("ec2", region_name=region)

    instance = None

    try:
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
                    "AssociatePublicIpAddress": False,
                    "Groups": [security_group],
                }
            ],
            BlockDeviceMappings=[
                {
                    "DeviceName": "/dev/xvda",
                    "Ebs": {
                        "VolumeSize": volume_size,
                        "DeleteOnTermination": True,
                        "VolumeType": "gp3",
                    },
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

        print("Waiting for the instance to run...")
        instance.wait_until_running()
        instance.load()

        print("Waiting for the instance to pass status checks...")
        instance_id = instance.id
        waiter = client.get_waiter("instance_status_ok")
        waiter.wait(InstanceIds=[instance_id])

        target_ip = instance.private_ip_address
        print(f"Instance private IP: {target_ip}")

        wait_for_ssh(target_ip, key_path)

        print("Running init.sh script...")
        command = f"ssh -o StrictHostKeyChecking=no -i '{key_path}' ec2-user@{target_ip} 'bash -s' < init.sh"
        subprocess.run(command, shell=True, check=True)

        print("Stopping the instance...")
        instance.stop()
        instance.wait_until_stopped()

        print("Creating AMI...")
        response = client.create_image(
            InstanceId=instance.id, Name=ami_name, NoReboot=True
        )
        ami_id = response["ImageId"]

        print(f"Waiting for AMI {ami_id} to become available...")
        waiter = client.get_waiter("image_available")
        waiter.wait(ImageIds=[ami_id])

        print(f"AMI created: {ami_id}")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise

    finally:
        if instance:
            instance.reload()
            if instance.state["Name"] != "terminated":
                print("Ensuring the instance is terminated...")
                instance.terminate()
                instance.wait_until_terminated()
                print("Instance terminated.")


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
    parser.add_argument(
        "--volume_size",
        type=int,
        required=False,
        default=30,
        help="Size of the root EBS volume in GB.",
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
        args.volume_size,
    )
