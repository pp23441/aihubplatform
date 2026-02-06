import boto3
from botocore.exceptions import NoCredentialsError, ClientError

# -----------------------------
# AWS Identity (STS)
# -----------------------------
def get_identity():
    try:
        sts = boto3.client("sts")
        return sts.get_caller_identity()
    except NoCredentialsError:
        return None
    except ClientError:
        return None


# -----------------------------
# List EC2 Instances
# -----------------------------
def list_ec2(region="us-east-1"):
    instances = []

    try:
        ec2 = boto3.client("ec2", region_name=region)
        response = ec2.describe_instances()

        for reservation in response["Reservations"]:
            for inst in reservation["Instances"]:
                instances.append({
                    "id": inst["InstanceId"],
                    "type": inst["InstanceType"],
                    "az": inst["Placement"]["AvailabilityZone"],
                    "state": inst["State"]["Name"]
                })

    except NoCredentialsError:
        return []
    except ClientError as e:
        print("AWS Error:", e)
        return []

    return instances
