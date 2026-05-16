# KubeGuard — Cloud-Native Kubernetes Auto-Healing Platform

![Kubernetes](https://img.shields.io/badge/Kubernetes-Auto--Healing-326CE5?logo=kubernetes&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-Monitoring-E6522C?logo=prometheus&logoColor=white)
![Helm](https://img.shields.io/badge/Helm-Packaging-0F1689?logo=helm&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI/CD-2088FF?logo=githubactions&logoColor=white)
![PromQL](https://img.shields.io/badge/PromQL-Slope_Detection-orange)
![SRE](https://img.shields.io/badge/SRE-Auto_Healing-success)
![RBAC](https://img.shields.io/badge/Security-RBAC-critical)
![Minikube](https://img.shields.io/badge/Minikube-Local_K8s-FF6F00)
![Observability](https://img.shields.io/badge/Observability-Prometheus_+_Grafana-blueviolet)

KubeGuard is a cloud-native Kubernetes auto-healing platform built using Python, Kubernetes SDK, Prometheus, Helm, and Docker.

The platform continuously monitors Kubernetes workloads using Prometheus metrics and automatically remediates memory leak patterns before applications crash or require manual intervention.

KubeGuard demonstrates practical Site Reliability Engineering (SRE), Kubernetes automation, observability, and cloud-native operational engineering concepts.

---

# Project Highlights

* Kubernetes auto-healing platform
* Prometheus-based memory leak detection
* Trend-based anomaly detection using PromQL
* Automated Kubernetes rolling restarts
* Python Kubernetes SDK integration
* Helm-packaged deployment
* RBAC least-privilege security model
* Structured operational logging
* Slack alert integration
* Minikube local development workflow
* AWS EKS-ready architecture
* Dockerized test applications
* Unit-tested healing logic

---

# Problem Statement

Traditional Kubernetes monitoring systems are reactive.

They:

* detect failures after outages occur
* generate alerts
* require human intervention

KubeGuard introduces a proactive healing approach.

Instead of waiting for a pod to crash due to memory exhaustion:

1. Prometheus continuously collects memory metrics
2. KubeGuard analyzes memory growth trends
3. Memory leak patterns are detected using slope analysis
4. The Kubernetes API is called automatically
5. A rolling restart is triggered before outage occurs

This reduces:

* downtime
* manual operational work
* production incidents

---

# Core Engineering Concept

The most important concept in KubeGuard is:

# Trend-Based Memory Leak Detection

Instead of using:

```python
if memory > threshold:
    restart()
```

KubeGuard calculates:

```text
memory growth rate (MB/min)
```

using Prometheus range queries.

This prevents false positives.

Example:

| Pod State                  | Result            |
| -------------------------- | ----------------- |
| Stable 900MB memory usage  | No restart        |
| Memory increasing 25MB/min | Restart triggered |

This demonstrates practical observability engineering and SRE thinking.

---

# System Architecture

## High-Level Workflow

```text
flowchart TD

    App[Application Pods]

    App --> Metrics[Prometheus Metrics Collection]

    Metrics --> KG[KubeGuard Controller]

    KG --> Analysis[PromQL Trend Analysis]

    Analysis --> SDK[Kubernetes Python SDK]

    SDK --> Restart[Rolling Restart Trigger]

    Restart --> Slack[Slack Notification]
```

---

# Mermaid Architecture Diagram

```mermaid
flowchart TD

    App[Memory Hog Application Pod]

    App --> Metrics[/metrics Endpoint]

    Metrics --> Prometheus[Prometheus Server]

    Prometheus --> KG[KubeGuard Controller]

    KG --> Trend[Memory Trend Analysis]

    Trend --> Decision{Leak Detected?}

    Decision -->|Yes| K8sAPI[Kubernetes API Server]

    K8sAPI --> Restart[Rolling Restart Deployment]

    Restart --> NewPod[Healthy Replacement Pod]

    KG --> Slack[Slack Alert]

    KG --> Logs[Structured JSON Logs]

    subgraph Kubernetes Cluster
        App
        Prometheus
        KG
    end
```

---

# Technology Stack

| Category                   | Technologies                                                    |
| -------------------------- | --------------------------------------------------------------- |
| Kubernetes & Cloud-Native  | Kubernetes, Minikube, Helm, RBAC, Kubernetes Python SDK, Docker |
| Monitoring & Observability | Prometheus, Grafana, PromQL                                     |
| Backend & Automation       | Python, Flask, GitHub Actions                                   |
| Cloud & Deployment         | AWS EKS, Terraform                                              |

---

# Repository Structure

```bash
kubeguard/
│
├── controller/
│   ├── main.py
│   ├── config.py
│   ├── k8s_client.py
│   ├── prometheus_client.py
│   ├── notifier.py
│   ├── audit.py
│   ├── Dockerfile
│   └── healers/
│       └── memory_leak.py
│
├── k8s/
│   └── memory_hog-deploy.yaml
│
├── test_apps/
│   └── memory_hog/
│       ├── app.py
│       └── Dockerfile
│
├── helm/
│   └── kubeguard/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
│
├── tests/
│   └── test_memory_healer.py
│
├── config.yaml
├── deploy.py
├── requirements.txt
└── README.md
```

---

# Key Components Explained

# 1. KubeGuard Controller

The controller continuously watches Kubernetes workloads.

Responsibilities:

* query Prometheus metrics
* detect memory leak trends
* trigger Kubernetes remediation
* send alerts
* log healing actions

The controller runs inside Kubernetes as a Deployment.

---

# 2. Prometheus Integration

Prometheus scrapes metrics from application pods.

KubeGuard queries Prometheus using PromQL.

Example metric:

```text
container_memory_working_set_bytes
```

KubeGuard calculates:

```text
(last_memory - first_memory) / elapsed_minutes
```

to determine memory growth rate.

---

# 3. Kubernetes Python SDK

KubeGuard directly interacts with the Kubernetes API using the official Python SDK.

Key operations:

* list pods
* patch deployments
* trigger rolling restarts
* read deployment replica counts

This demonstrates practical Kubernetes controller behavior.

---

# 4. Rolling Restart Automation

When a memory leak is detected:

KubeGuard automatically performs:

```bash
kubectl rollout restart deployment/<name>
```

using Kubernetes API patch operations.

This replaces unhealthy pods before crashes occur.

---

# 5. RBAC Security Model

KubeGuard follows least-privilege access principles.

The controller only receives permissions required for:

* reading pods
* patching deployments
* monitoring workloads

This prevents unnecessary cluster-wide permissions.

---

# 6. Helm Packaging

KubeGuard is packaged as a Helm chart.

Benefits:

* one-command deployment
* reusable configuration
* easier Kubernetes management
* production-style deployment workflow

Deployment example:

```bash
helm install kubeguard ./helm/kubeguard
```

---

# 7. Structured Logging

KubeGuard generates structured operational logs for:

* memory leak detection
* healing actions
* restart events
* alert delivery
* Prometheus queries

This improves:

* debugging
* observability
* operational visibility

---

# 8. Slack Notifications

When healing occurs:

* Slack alerts are sent automatically
* affected pod information is included
* memory metrics are included

This simulates real incident response workflows.

---

# Memory Leak Detection Workflow

## Step 1

Prometheus scrapes memory metrics every few seconds.

## Step 2

KubeGuard queries recent memory history.

## Step 3

Slope calculation determines growth rate.

## Step 4

If growth exceeds configured threshold:

```text
20 MB/min
```

healing is triggered.

## Step 5

Rolling restart replaces unhealthy pod.

## Step 6

Slack notification + logs generated.

---

# Test Application

KubeGuard includes a memory leak simulation application.

## memory_hog

The application continuously allocates memory:

```python
leak.append('x' * 1000)
```

This intentionally creates memory growth patterns for testing.

The app also exposes:

```text
/metrics
```

for Prometheus scraping.

---

# Deployment Workflow

# Step 1 — Start Minikube

```bash
minikube start --cpus=4 --memory=8192 --driver=docker
```

---

# Step 2 — Install Monitoring Stack

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring
```

---

# Step 3 — Create Secrets (Required for Helm)

```bash
# Create AWS credentials secret
kubectl create secret generic kubeguard-aws-creds \
  --from-literal=access_key_id="YOUR_AWS_KEY" \
  --from-literal=secret_access_key="YOUR_AWS_SECRET"

# Create Alerts secret (Slack)
kubectl create secret generic kubeguard-alerts \
  --from-literal=slack_webhook="YOUR_SLACK_WEBHOOK"
```

---

# Step 4 — Deploy Test App

```bash
kubectl apply -f k8s/memory-hog-deploy.yaml
```

---

# Step 5 — Run Controller Locally (Development)

```bash
# 1. Required for local dev — port-forward Prometheus in background
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090 &
export PROMETHEUS_URL=http://localhost:9090

# 2. Run the controller
python3 controller/main.py
```

# Step 6 — Verify It's Working

1. **Check controller is running (if deployed via Helm):**
   ```bash
   kubectl get pods -l app.kubernetes.io/name=kubeguard
   ```

2. **Watch controller logs live:**
   ```bash
   kubectl logs -l app.kubernetes.io/name=kubeguard -f
   ```

3. **Observe auto-healing:**
   After `memory-hog` is deployed and running for a few minutes, watch for this log line in the controller:
   `LEAK DETECTED — memory-hog-xxx: Memory 820MB, growing at 25MB/min`

   Then verify the deployment is restarting:
   ```bash
   kubectl get pods -l app=memory-hog -w
   ```

---

# CI/CD Pipeline

# CI/CD Pipeline

GitHub Actions automates:

* unit testing
* linting
* Docker image builds
* deployment validation

This improves:

* automation
* code quality
* deployment reliability

---

# Unit Testing

The project includes unit tests for healing logic.

Tests validate:

* slope detection
* restart triggering
* cooldown handling
* negative scenarios

This demonstrates engineering maturity and testing discipline.

---
