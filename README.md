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

DVC is initialized in `backend/` with an S3 remote (`s3://cats-dogs-mlops-dvc-725397331485/dvcstore`,
private bucket). `data/raw.dvc` and `dvc.lock` are committed to git and point at the versioned
dataset in the remote; the actual image bytes live in S3, not in git.

```bash
cd backend
dvc pull                 # Fetch versioned dataset from the S3 remote
dvc repro                # Reproduce preprocess + train pipeline
# After changing the dataset:
dvc add data/raw
dvc push
git add data/raw.dvc dvc.lock
git commit -m "data: update dataset version"
```

Note: `data/raw` currently holds a small representative sample used to exercise the DVC
pipeline end-to-end (`dvc add`/`push`/`pull` + `preprocess.py` -> `data/processed`). Actual
model training uses the full public Cats vs Dogs dataset pulled via `tensorflow-datasets`
in `src/models/train.py`, independent of this sample.

---

## Kubernetes Deployment on AWS

### Option A: AWS Free Tier (EC2 + K3s) - 100% Free
1. Launch the instance with `aws/launch_ec2_k3s.py` (attaches the `cats-dogs-k8s-ssm-profile`
   IAM instance profile so it's reachable via AWS Systems Manager - no SSH key needed), or
   launch manually and run the setup script:
   ```bash
   chmod +x aws/setup_k3s_aws_ec2.sh
   ./aws/setup_k3s_aws_ec2.sh
   ```
2. The CI/CD pipeline fetches a fresh kubeconfig from the instance automatically on every
   deploy via SSM (`.github/scripts/fetch_kubeconfig_ssm.sh`) - no manual secret to keep in
   sync. If SSM is ever unavailable, it falls back to the `KUBECONFIG_BASE64` GitHub secret;
   to set that manually:
   ```bash
   cat /etc/rancher/k3s/k3s.yaml | base64 -w 0
   ```
   *(Replace `127.0.0.1` inside `k3s.yaml` with your EC2 Public IP before base64 encoding).*
3. Services are exposed via NodePort on the instance's public IP:

   | Service | NodePort URL |
   |---|---|
   | Backend API | `http://<EC2_PUBLIC_IP>:30800` |
   | Frontend | `http://<EC2_PUBLIC_IP>:30880` |
   | MLflow | `http://<EC2_PUBLIC_IP>:30500` |
   | Prometheus | `http://<EC2_PUBLIC_IP>:30909` |
   | Grafana | `http://<EC2_PUBLIC_IP>:30300` |

   Set the `APP_BASE_URL` GitHub secret to the backend URL above (used by `smoke_test.sh`
   and the post-deploy performance tracking step).

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
| M5 | Post-deployment performance tracking | Completed |

---

## Team

MLOps Assignment 2 - Cats vs Dogs Classification
