# KubeGuard: Proactive Kubernetes Auto-Healing Controller

**"Detecting and remediating memory leaks before they trigger OOMKills."**

[![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)](https://prometheus.io/)

## 🚀 The Core Problem
Most Kubernetes monitoring setups are **reactive**. They alert you *after* a pod has crashed or hit a memory limit (OOMKill). By then, the user experience is already degraded. 

**KubeGuard is proactive.** Instead of waiting for a threshold breach, it uses **slope-based detection (linear regression)** to identify pods with consistent memory growth. It predicts a crash before it happens and performs a controlled rolling restart to clear the leak while maintaining service availability.

---

## 🏗️ Architecture
KubeGuard runs as a deployment within your cluster, acting as a custom controller that bridges the gap between monitoring and action.

1. **Observe:** Queries Prometheus metrics (`container_memory_working_set_bytes`) every 15 seconds.
2. **Analyze:** Calculates the **memory growth slope** over a 5-minute window.
3. **Decide:** If `slope > 20MB/min` and `memory > 800MB`, it identifies a leak.
4. **Act:** Uses the **Python Kubernetes SDK** to trigger a `rollout restart` of the owning Deployment.
5. **Audit:** Logs the event to **AWS DynamoDB** and sends real-time alerts to **Slack/SNS**.

---

## 🧠 The "Clever Part": Slope vs. Threshold
> **"Why not just use a standard alert?"**

A simple threshold like *'restart if memory > 800MB'* is flawed. A stable Java application might legitimately use 850MB indefinitely. A threshold-only approach would cause infinite, unnecessary restart loops.

KubeGuard looks at the **trend**:
- **Pod A:** Uses 850MB, but growth is 0MB/min → **Healthy** (Stable).
- **Pod B:** Uses 400MB, but growth is 30MB/min → **Leak Detected** (Will crash soon).

**Formula used:** `(last_value - first_value) / elapsed_minutes`

---

## 🛠️ Tech Stack
- **Language:** Python 3.12 (Kubernetes SDK, Boto3)
- **Monitoring:** Prometheus, Grafana
- **Infrastructure:** AWS EKS, Terraform, Minikube
- **Packaging:** Helm (RBAC Least Privilege)
- **Database:** AWS DynamoDB (Audit Trail)

---

## 🏁 Getting Started

### 1. Local Development (Minikube)
```bash
# Start Minikube
minikube start --cpus=4 --memory=8192

# Install Monitoring Stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack

# Deploy KubeGuard
helm install kubeguard ./helm/kubeguard \
  --set aws.accessKeyId=$AWS_ID \
  --set aws.secretAccessKey=$AWS_KEY
```

### 2. Testing the Healer
Deploy the included `memory-hog` app to see KubeGuard in action:
```bash
kubectl apply -f k8s/memory-hog-deploy.yaml
```

---

