#!/usr/bin/env python3
import subprocess
import sys

def run_command(command, cwd=None):
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"Error: Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)

def main():
    print("--- Starting Local Deployment to Minikube ---")
    
    print("\n1. Building clusterpulse Controller Image...")
    run_command("docker build -t clusterpulse-controller:latest -f controller/Dockerfile .")
    run_command("minikube image load clusterpulse-controller:latest")
    
    print("\n2. Building Memory Hog Test App Image...")
    run_command("docker build -t memory-hog:latest -f test_apps/memory_hog/Dockerfile test_apps/memory_hog/")
    run_command("minikube image load memory-hog:latest")
    
    print("\n3. Deploying clusterpulse via Helm...")
    run_command("helm upgrade --install clusterpulse ./helm/clusterpulse")
    
    print("\n4. Deploying Memory Hog Test App...")
    run_command("kubectl apply -f k8s/memory-hog-deploy.yaml")
    
    print("\n--- Deployment complete ---")
    print("Monitor pods with: kubectl get pods -w")

if __name__ == "__main__":
    main()
