#!/usr/bin/env python3
import time
import json
import subprocess
import sys

def run(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error executing: {cmd}\n{res.stderr}")
    return res.stdout.strip()

print("===============================================")
print("  Launching AWS Free-Tier Kubernetes Instance")
print("===============================================")

# 1. Userdata script for EC2
user_data = """#!/bin/bash
apt-get update && apt-get install -y curl docker.io
curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
"""

with open("/tmp/userdata.sh", "w") as f:
    f.write(user_data)

ami_id = "ami-06e78a71af43ef21a"
sg_id = "sg-03ae0f0bce6895ac3"

# 2. Check if an instance with tag Name=cats-dogs-k8s-node already exists
check_cmd = 'aws ec2 describe-instances --filters "Name=tag:Name,Values=cats-dogs-k8s-node" "Name=instance-state-name,Values=running,pending" --query "Reservations[0].Instances[0].InstanceId" --output text'
existing_id = run(check_cmd)

if existing_id and existing_id != "None":
    instance_id = existing_id
    print(f"Found existing instance: {instance_id}")
else:
    print("Launching new t3.small/t2.micro EC2 instance...")
    launch_cmd = f'''aws ec2 run-instances \
      --image-id {ami_id} \
      --instance-type t3.small \
      --security-group-ids {sg_id} \
      --user-data file:///tmp/userdata.sh \
      --tag-specifications 'ResourceType=instance,Tags=[{{Key=Name,Value=cats-dogs-k8s-node}}]' \
      --block-device-mappings '[{{"DeviceName":"/dev/sda1","Ebs":{{"VolumeSize":20,"VolumeType":"gp3"}}}}]' \
      --query "Instances[0].InstanceId" \
      --output text'''
    instance_id = run(launch_cmd)

print(f"Instance ID: {instance_id}")

# 3. Wait for instance running
print("Waiting for instance to reach running state...")
run(f"aws ec2 wait instance-running --instance-ids {instance_id}")

# 4. Get Public IP
public_ip = run(f'aws ec2 describe-instances --instance-ids {instance_id} --query "Reservations[0].Instances[0].PublicIpAddress" --output text')
print(f"Instance Public IP: {public_ip}")

print("\nWaiting 45 seconds for K3s initialization...")
time.sleep(45)

print("\n===============================================")
print("  AWS Kubernetes Instance Ready!")
print(f"  Public IP: {public_ip}")
print("===============================================")
