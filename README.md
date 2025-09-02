# Kubernetes-as-a-Service (KaaS) Platform

This project implements a simplified Kubernetes-as-a-Service (KaaS) platform that allows users to deploy, manage, and monitor containerized applications through custom APIs and Helm charts.

## Key Features
- **Microservices for Kubernetes Management**
  - Deploy new applications and register container images.
  - Retrieve status of specific Deployments or all Deployments in the cluster.
  - Support for Ingress, Secrets, ConfigMaps, and resource allocation.
- **Helm Integration**
  - Package applications into Helm Charts for easy deployment and versioning.
- **Monitoring & Health Checks**
  - Expose `/healthz` and `/health/{app_name}` endpoints for status checks.
  - Integrate Prometheus for metrics collection and Grafana for visualization.
- **Cloud-Native Approach**
  - Implements Kubernetes best practices with scalability (HPA), probes, and resource management.

## Tech Stack
- **Platform:** Kubernetes, Minikube  
- **Deployment Tools:** Helm, Ingress-Nginx  
- **Monitoring:** Prometheus, Grafana  
- **Programming Languages:** Python / Go (for Kubernetes client)  
- **Container Registry:** Docker  

