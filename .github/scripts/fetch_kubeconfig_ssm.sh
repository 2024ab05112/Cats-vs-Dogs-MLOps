#!/usr/bin/env bash
# Fetches a fresh kubeconfig from the cats-dogs-k8s-node EC2 instance via
# AWS Systems Manager (no SSH key / stored kubeconfig secret required).
# The instance's IAM instance profile grants SSM access; this only needs
# the AWS credentials already configured in the calling shell.
set -euo pipefail

TAG_NAME="${K3S_INSTANCE_TAG:-cats-dogs-k8s-node}"
TIMEOUT_SECS=120

INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=${TAG_NAME}" "Name=instance-state-name,Values=running" \
  --query "Reservations[0].Instances[0].InstanceId" --output text)

if [[ -z "$INSTANCE_ID" || "$INSTANCE_ID" == "None" ]]; then
  echo "No running EC2 instance tagged Name=${TAG_NAME} found." >&2
  exit 1
fi

PUBLIC_IP=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" \
  --query "Reservations[0].Instances[0].PublicIpAddress" --output text)

if [[ -z "$PUBLIC_IP" || "$PUBLIC_IP" == "None" ]]; then
  echo "Instance $INSTANCE_ID has no public IP." >&2
  exit 1
fi

echo "Fetching kubeconfig from $INSTANCE_ID ($PUBLIC_IP) via SSM..."

CMD_ID=$(aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters "commands=[\"sed -e s/127.0.0.1/${PUBLIC_IP}/ /etc/rancher/k3s/k3s.yaml\"]" \
  --query "Command.CommandId" --output text)

elapsed=0
status="Pending"
while [[ "$status" != "Success" && "$status" != "Failed" && "$status" != "Cancelled" && "$status" != "TimedOut" ]]; do
  if [[ "$elapsed" -ge "$TIMEOUT_SECS" ]]; then
    echo "Timed out waiting for SSM command $CMD_ID after ${TIMEOUT_SECS}s." >&2
    exit 1
  fi
  sleep 5
  elapsed=$((elapsed + 5))
  status=$(aws ssm get-command-invocation \
    --command-id "$CMD_ID" --instance-id "$INSTANCE_ID" \
    --query "Status" --output text 2>/dev/null || echo "Pending")
  echo "  [$elapsed s] status: $status"
done

if [[ "$status" != "Success" ]]; then
  echo "SSM command did not succeed (status: $status)." >&2
  aws ssm get-command-invocation --command-id "$CMD_ID" --instance-id "$INSTANCE_ID" \
    --query "StandardErrorContent" --output text >&2 || true
  exit 1
fi

mkdir -p ~/.kube
aws ssm get-command-invocation --command-id "$CMD_ID" --instance-id "$INSTANCE_ID" \
  --query "StandardOutputContent" --output text > ~/.kube/config

if ! grep -q "apiVersion" ~/.kube/config; then
  echo "Fetched kubeconfig does not look valid:" >&2
  cat ~/.kube/config >&2
  exit 1
fi

echo "Kubeconfig fetched successfully via SSM ($(wc -c < ~/.kube/config) bytes)."
