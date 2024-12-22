import boto3
import time
import subprocess


def create_ami(base_ami, ami_name):
    ec2 = boto3.resource("ec2")
    client = boto3.client("ec2")
    try:
        # Step 1: Launch an EC2 instance from the base AMI
        print("Launching EC2 instance...")
        instance = ec2.create_instances(
            ImageId=base_ami,
            MinCount=1,
            MaxCount=1,
            InstanceType="t2.micro",
            KeyName="your-key-name",  # Replace with your key pair name
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

        # Step 2: Run the initialization script
        print("Running init.sh script...")
        command = f"ssh -o StrictHostKeyChecking=no -i your-key.pem ec2-user@{instance.public_dns_name} 'bash -s' < init.sh"
        subprocess.run(command, shell=True, check=True)

        # Step 3: Stop the instance
        print("Stopping the instance...")
        instance.stop()
        instance.wait_until_stopped()

        # Step 4: Create an AMI
        print("Creating AMI...")
        response = client.create_image(
            InstanceId=instance.id, Name=ami_name, NoReboot=True
        )

        ami_id = response["ImageId"]

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
    import argparse

    parser = argparse.ArgumentParser(description="Create an AMI from a base AMI.")
    parser.add_argument("--base_ami", type=str, required=True, help="The base AMI ID.")
    parser.add_argument(
        "--ami_name", type=str, required=True, help="The name of the new AMI."
    )

    args = parser.parse_args()

    create_ami(args.base_ami, args.ami_name)
