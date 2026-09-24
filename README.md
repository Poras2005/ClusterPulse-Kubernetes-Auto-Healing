# ClusterPulse — Cloud-Native Kubernetes Auto-Healing Platform

![Kubernetes](https://img.shields.io/badge/Kubernetes-Auto--Healing-326CE5?logo=kubernetes&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-Monitoring-E6522C?logo=prometheus&logoColor=white)
![Helm](https://img.shields.io/badge/Helm-Packaging-0F1689?logo=helm&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white)
![Minikube](https://img.shields.io/badge/Minikube-Local_K8s-FF6F00)

**ClusterPulse** is a proactive, cloud-native Kubernetes auto-healing controller. It acts as a specialized Site Reliability Engineer (SRE) running continuously inside your cluster.

Instead of waiting for a memory leak to exhaust pod limits and trigger a catastrophic `OOMKilled` crash (which causes dropped requests and 3:00 AM alerts), ClusterPulse constantly monitors memory velocity using Prometheus metrics. When it detects a dangerous growth trend, it gracefully executes a rolling restart of the application and emits a Kubernetes Warning event for your audit trail—preventing downtime before it happens.

---

## 📖 Table of Contents
1. [Project Information & Problem Statement](#-project-information--problem-statement)
2. [Why This Tech Stack?](#-why-this-tech-stack)
3. [Architecture & How It Works](#-architecture--how-it-works)
4. [Repository Structure](#-repository-structure)
5. [Security & Best Practices](#-security--best-practices)
6. [Deployment Guide (Step-by-Step)](#-deployment-guide-step-by-step)
7. [Teardown Instructions](#-teardown-instructions)

---

## 💡 Project Information & Problem Statement

### The Problem
Traditional Kubernetes monitoring is strictly **reactive**:
1. An application suffers from a slow memory leak.
2. The pod eventually hits its memory limit and the kernel triggers an `OOMKilled` event.
3. In-flight requests are dropped, users experience errors, and a PagerDuty alert wakes up an engineer.
4. The engineer manually checks the cluster, realizes it was just a memory leak, and goes back to sleep.

### The Solution: ClusterPulse
ClusterPulse introduces a **proactive healing approach**. It calculates the *velocity* of memory usage. If an application's memory is creeping up by 5% per minute and crosses an 80% threshold, ClusterPulse knows a crash is inevitable. It traces the Pod's ownership up to its parent Deployment and triggers a seamless Kubernetes **Rolling Restart**. 

The leak is temporarily "healed" with zero downtime, and an event is logged for developers to investigate the root cause during business hours.

---

## 🛠 Why This Tech Stack?

ClusterPulse was built with purpose-driven technology choices to emulate a production-grade Kubernetes controller:

* **Python 3.12 & Kubernetes Python SDK**: Python allows for rapid iteration and highly readable operational scripts. The official Kubernetes SDK allows us to interact with the API Server securely using in-cluster ServiceAccount tokens without hardcoding credentials.
* **Prometheus & PromQL**: Prometheus is the industry standard for cloud-native metrics. We use complex PromQL range queries (`sum by (pod)`) to aggregate metrics across nested container cgroups, ensuring accurate, real-time memory measurements.
* **Helm**: Helm is used to package ClusterPulse. It allows us to bundle the Deployment, ConfigMaps, and RBAC rules into a single, version-controlled, reproducible installation.
* **Docker**: Used to containerize the controller and the synthetic memory-hog test application, ensuring absolute parity between environments.
* **Minikube**: Chosen as the target environment because it allows any developer to spin up a fully operational Kubernetes cluster locally for testing the auto-healing workflows.

---

## 🏗 Architecture & How It Works

ClusterPulse operates on a continuous, multi-step reconciliation loop (defaulting to every 15 seconds).

### The Auto-Healing Workflow
1. **Dynamic Limits Discovery**: ClusterPulse queries `kube_pod_container_resource_limits` to discover the exact memory limit for every pod. It never uses hardcoded byte thresholds.
2. **Trend Analysis (Slope)**: It queries `container_memory_working_set_bytes` over a 5-minute window. It compares the oldest and newest data points to calculate a **Percentage Growth Rate** (e.g., +6.5% per minute).
3. **Threshold Evaluation**: If a pod exceeds 80% utilization AND is growing at >5% per minute, a leak is declared.
4. **Dynamic Owner Resolution**: ClusterPulse queries the Pod to find its `ownerReferences` (a ReplicaSet). It then queries the ReplicaSet to find *its* owner (a Deployment).
5. **Graceful Remediation**: It patches the parent Deployment with a unique annotation, triggering Kubernetes to perform a zero-downtime rolling restart.
6. **Audit Trail**: ClusterPulse emits a native Kubernetes `Warning` Event directly attached to the Pod, ensuring the action is logged in standard cluster monitoring tools.

### Architecture Diagram

```mermaid
flowchart TD
    App[Application Pods]
    App --> Metrics[/metrics Endpoint]
    Metrics --> Prometheus[Prometheus Server]
    Prometheus --> KG[ClusterPulse Controller]
    
    subgraph ClusterPulse Logic
        KG --> Trend[Percentage Trend Analysis]
        Trend --> Decision{Leak > 5%/min?}
        Decision -->|Yes| Resolve[Resolve OwnerReferences]
    end
    
    Resolve --> K8sAPI[Kubernetes API Server]
    K8sAPI --> Restart[Patch Deployment]
    Restart --> K8sEvents[Emit K8s Warning Event]
    Restart --> NewPod[Rolling Restart Triggered]
```

---

## 📁 Repository Structure

```bash
clusterpulse/
├── controller/                  # Python source code for the controller
│   ├── healers/
│   │   └── memory_leak.py       # Core auto-healing logic & threshold evaluation
│   ├── config.py                # Configuration loading (from ConfigMaps)
│   ├── k8s_client.py            # K8s API interactions & owner resolution
│   ├── main.py                  # Entrypoint and endless reconciliation loop
│   ├── notifier.py              # Emits native Kubernetes Events
│   ├── prometheus_client.py     # PromQL range queries & percentage math
│   └── Dockerfile               # Container build instructions for the controller
├── helm/
│   └── clusterpulse/            # Helm chart for deploying ClusterPulse
│       ├── templates/
│       │   ├── _helpers.tpl     # Helm template helpers
│       │   ├── configmap.yaml   # Injects thresholds to the controller
│       │   ├── deployment.yaml  # Runs the controller pod
│       │   └── rbac.yaml        # ServiceAccount, Roles, and RoleBindings
│       ├── Chart.yaml
│       └── values.yaml          # Default configuration values
├── k8s/
│   └── memory-hog-deploy.yaml   # Test application deployment and service
├── test_apps/
│   └── memory_hog/              # Synthetic memory leak app
│       ├── app.py               # Leaks 1.5MB/s on a background thread
│       └── Dockerfile
├── tests/                       # Pytest unit tests for the controller
│   └── test_memory_healer.py    
├── .github/
│   └── workflows/
│       └── ci.yml               # CI/CD pipelines (testing & linting)
├── config.yaml                  # Global configuration parameters
├── deploy_local.py              # Automated 1-click Minikube deployment script
├── requirements.txt             # Python dependencies
└── README.md                    # This document
```

---

## 🔐 Security & Best Practices

ClusterPulse is engineered with production-grade security and reliability standards:

1. **RBAC Least-Privilege**: The controller does not run as a cluster-admin. It operates under a dedicated ServiceAccount governed by strict ClusterRoles. It is only permitted to `get/list/watch` Pods and ReplicaSets, `get/patch` Deployments, and `create/patch` Events. 
2. **No Hardcoded API Keys**: ClusterPulse relies entirely on standard in-cluster Kubernetes token authentication (`load_incluster_config()`).
3. **Dynamic Object Tracking**: ClusterPulse doesn't guess what to restart. It recursively climbs the Kubernetes ownership tree (`Pod -> ReplicaSet -> Deployment`) to ensure it restarts the exact managing controller.
4. **Cooldown Windows**: To prevent infinite restart loops, ClusterPulse implements a 10-minute cooldown timer for any Deployment it heals.
5. **Zero External Dependencies**: By migrating away from AWS APIs, DynamoDB, and Slack Webhooks, the controller avoids external network latency, IAM credential management, and external points of failure.

---

## 🚀 Deployment Guide (Step-by-Step)

This guide walks you through deploying ClusterPulse and a synthetic memory-leaking application on a local Minikube cluster.

### Prerequisites
* Docker Desktop installed and running
* `minikube` installed
* `kubectl` installed
* `helm` installed
* `python 3.12` (for the automated deploy script)

### Step 1: Start Minikube
We need a slightly larger cluster to run Prometheus and the controller.
```bash
minikube start --cpus=4 --memory=8192 --driver=docker
```

### Step 2: Install the Prometheus Monitoring Stack
ClusterPulse relies on Prometheus and `kube-state-metrics` to gather memory data.
```bash
# Add the prometheus-community Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install the Prometheus stack into the 'monitoring' namespace
helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace
```
*Note: Wait 1-2 minutes for the Prometheus pods to reach the `Running` state before proceeding.*

### Step 3: Deploy ClusterPulse and the Test App
We provide an automated Python script that builds the Docker images locally, loads them into Minikube, deploys the Helm chart, and deploys the synthetic memory leak application.

```bash
# Run the automated deployment script
python deploy_local.py
```
*(If you do not want to use the script, you can manually run `docker build`, `minikube image load`, and `helm upgrade --install clusterpulse ./helm/clusterpulse`)*

### Step 4: Watch the Auto-Healing in Action!
The `memory-hog` test app is designed to leak exactly **1.5MB of RAM per second**. It has a hard limit of 512MB. It will take approximately **4.5 minutes** for the app to cross the 80% threshold.

Open two terminal windows to watch the system work:

**Terminal 1 (Watch ClusterPulse logs):**
```bash
kubectl logs -l app.kubernetes.io/name=clusterpulse -f
```

**Terminal 2 (Watch the Test Pod get restarted):**
```bash
kubectl get pods -l app=memory-hog -w
```

After ~4.5 minutes, you will see a log similar to this in the ClusterPulse logs:
> `[WARNING] clusterpulse.healer.memory_leak: LEAK DETECTED — memory-hog-855d7bd64-qwk5w: Memory at 85.7% (438MB/512MB), growing at 16.5%/min (threshold: 5%/min)`

Immediately after, Terminal 2 will show Kubernetes seamlessly terminating the old pod and spinning up a fresh, healthy replacement!

You can also view the native Kubernetes audit event generated by ClusterPulse:
```bash
kubectl get events --sort-by='.metadata.creationTimestamp'
```

---

## 🧹 Teardown Instructions

To completely remove the project, Prometheus, and reclaim your system resources, execute the following commands:

```bash
# 1. Uninstall the ClusterPulse Helm Chart
helm uninstall clusterpulse

# 2. Delete the Memory Hog test application
kubectl delete -f k8s/memory-hog-deploy.yaml

# 3. Uninstall the Prometheus Monitoring Stack
helm uninstall prometheus --namespace monitoring
kubectl delete namespace monitoring

# 4. Stop and Delete Minikube
minikube stop
minikube delete
```
