# Cats vs Dogs MLOps Pipeline

**MLOps Assignment 2 | End-to-End Production Pipeline**

Binary image classification for a pet adoption platform - built with MobileNetV2, FastAPI, Django, Docker, Kubernetes, MLflow, Prometheus, and Grafana.

---

## Architecture

```
GitHub Push
    │
    ▼
GitHub Actions CI/CD
    ├── Unit Tests (pytest)
    ├── Model Training (MobileNetV2 + MLflow)
    ├── Docker Build & Push (Docker Hub)
    └── Kubernetes Deploy
            ├── FastAPI Backend (port 8000)
            ├── Django Frontend (port 8080)
            ├── MLflow Tracker (port 5000)
            ├── Prometheus (port 9090)
            └── Grafana (port 3000)
```

---

## Project Structure

```
cats-vs-dogs-mlops/
├── backend/
│   ├── src/
│   │   ├── data/preprocess.py      # M1: Data versioning & preprocessing
│   │   ├── models/
│   │   │   ├── model.py            # M1: MobileNetV2 architecture
│   │   │   └── train.py            # M1: MLflow experiment tracking
│   │   └── utils/metrics.py        # Confusion matrix, loss curves
│   ├── tests/
│   │   ├── test_preprocess.py      # M3: Unit tests - preprocessing
│   │   └── test_api.py             # M3: Unit tests - inference API
│   ├── main.py                     # M2: FastAPI inference service
│   ├── Dockerfile                  # M2: Containerization
│   ├── requirements.txt            # M2: Version-pinned dependencies
│   ├── params.yaml                 # M1: DVC hyperparameter tracking
│   └── dvc.yaml                    # M1: DVC pipeline stages
├── frontend/
│   ├── webapp/                     # Django app views, templates
│   ├── dj_frontend/                # Django settings, URLs
│   └── Dockerfile
├── k8s/                            # M4: Kubernetes manifests
│   ├── backend/
│   ├── frontend/
│   ├── monitoring/
│   └── common/ingress.yml
├── monitoring/                     # M5: Prometheus + Grafana config
├── aws/                            # AWS cluster setup scripts
│   └── setup_k3s_aws_ec2.sh
├── .github/workflows/deploy.yml   # M3/M4: CI/CD pipeline
├── docker-compose.yml              # Local development stack
└── smoke_test.sh                   # M4: Post-deploy validation
```

---

## Quick Start (Local)

### 1. Train the model locally

```bash
cd backend
pip install -r requirements.txt
# Start MLflow server first
mlflow server --host 0.0.0.0 --port 5000 &
python -m src.models.train
```

### 2. Run with Docker Compose

```bash
# First train the model to get model.h5
docker-compose up --build
```

Services available at:
| Service | URL |
|---|---|
| Frontend | http://localhost:8080 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| MLflow UI | http://localhost:5000 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

### 3. Test API via curl

```bash
# Health check
curl http://localhost:8000/health

# Predict (with an image file)
curl -X POST http://localhost:8000/api/predict \
  -F "file=@/path/to/cat.jpg"
```

### 4. Run unit tests

```bash
cd backend
pip install -r unit-test-requirements.txt
pytest tests/ -v
```

---

## DVC - Data Versioning

```bash
cd backend
dvc init
dvc add data/raw        # Track raw dataset
dvc push                # Push to remote storage
dvc repro               # Reproduce preprocess + train pipeline
```

---

## Kubernetes Deployment on AWS

### Option A: AWS Free Tier (EC2 + K3s) - 100% Free
1. Launch an AWS EC2 `t2.micro` or `t3.small` instance (Ubuntu 22.04).
2. SSH into your instance and run the setup script:
   ```bash
   chmod +x aws/setup_k3s_aws_ec2.sh
   ./aws/setup_k3s_aws_ec2.sh
   ```
3. Get the encoded kubeconfig for GitHub Secrets (`KUBECONFIG_BASE64`):
   ```bash
   cat /etc/rancher/k3s/k3s.yaml | base64 -w 0
   ```
   *(Replace `127.0.0.1` inside `k3s.yaml` with your EC2 Public IP before base64 encoding).*

### Option B: AWS Managed Kubernetes (EKS)
1. Create an EKS cluster using `eksctl` or AWS Console:
   ```bash
   eksctl create cluster --name cats-dogs-cluster --region us-east-1 --nodegroup-name standard-workers --node-type t3.medium --nodes 2
   ```
2. Add the following Secrets to your GitHub Repository:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION` (e.g., `us-east-1`)
   - `AWS_EKS_CLUSTER_NAME` (`cats-dogs-cluster`)

### Option C: Manual kubectl Apply
```bash
kubectl apply -f k8s/common/
kubectl apply -f k8s/backend/
kubectl apply -f k8s/frontend/
kubectl apply -f k8s/monitoring/
```

---

## Modules Coverage

| Module | Requirement | Status |
|--------|------------|--------|
| M1 | Git versioning | Completed |
| M1 | DVC dataset versioning | Completed |
| M1 | MobileNetV2 model | Completed |
| M1 | MLflow tracking | Completed |
| M2 | FastAPI REST API | Completed |
| M2 | /health + /predict endpoints | Completed |
| M2 | requirements.txt (pinned) | Completed |
| M2 | Dockerfile + local test | Completed |
| M3 | pytest unit tests | Completed |
| M3 | GitHub Actions CI | Completed |
| M3 | Docker image push | Completed |
| M4 | Kubernetes manifests | Completed |
| M4 | CD auto-deploy on main | Completed |
| M4 | Smoke tests post-deploy | Completed |
| M5 | Request/response logging | Completed |
| M5 | Prometheus metrics | Completed |
| M5 | Grafana dashboards | Completed |

---

## Team

MLOps Assignment 2 - Cats vs Dogs Classification
