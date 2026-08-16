#!/usr/bin/env bash
# AWS EC2 Free-Tier Lightweight Kubernetes (K3s) Setup Script
# This script runs on an AWS EC2 Ubuntu instance to install lightweight K3s Kubernetes.

set -euo pipefail

echo "=================================================="
echo "  AWS EC2 K3s Kubernetes Cluster Setup (Free Tier)"
echo "=================================================="

# 1. Update system packages
sudo apt-get update && sudo apt-get install -y curl git docker.io

# 2. Install K3s (Lightweight production Kubernetes for AWS EC2 Free Tier)
echo "Installing K3s lightweight Kubernetes..."
curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644

# 3. Create symlink for kubectl if needed
sudo snap install kubectl --classic || true

# 4. Verify K3s installation
echo "Verifying cluster status..."
sudo k3s kubectl get nodes

echo ""
echo "=================================================="
echo "  K3s Setup Completed Successfully!"
echo "  To get your kubeconfig for GitHub Secrets:"
echo "  cat /etc/rancher/k3s/k3s.yaml | base64 -w 0"
echo "  (Remember to replace 127.0.0.1 with your AWS EC2 Public IP)"
echo "=================================================="
