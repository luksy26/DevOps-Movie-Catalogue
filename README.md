# Cloud Computing Project

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)

---

## Introduction

This project's theme is a **movie catalogue**.

It mainly focuses on the **DevOps** side of development: containerization with **Docker**, deployment with **Kubernetes** in a **kind** (Kubernetes in Docker) cluster and integration with different services (**Portainer**, **DBeaver**).

All Kubernetes resources are also created using **Terraform**.

---

## Features

**HTTP requests** can be made on the app's exposed **API** pod. These requests include:
- **Sign-up**
- **Login**
- **Getting** the current user's **list of movies**
- **Adding** a movie to the **current user's list**
- **Deleting** a movie from the **current user's list**

---

## Architecture

The foundation of the app lies on a **kind cluster** with a **control plane** and **2 worker** nodes.

On this cluster, there are several resources, among which **3 proprietary pods** and **2 third-party pods** (well, they all are under kubernetes **deployments**, but for the sake of simplicity, we'll just consider them pods here).

The proprietary pods (docker images built in-house) are:
- **api-pod** (what a frontend would communicate with)
- **auth-pod** (middle layer)
- **catalogue-pod** (business logic)

The third-party pods (docker images publicly available) are:
- **postgres-pod** (database)
- **portainer-pod** (cluster and container management)

The **api**, **postgres** and **portainer** pods are also exposed locally, each using a **NodePort** service. The **api** is exposed for obvious reasons, the **postgres** pod is exposed for integration with database tools (e.g. **DBeaver**), and **portainer** is exposed for accessing the portainer web interface.

Intra-cluster communication is done with **ClusterIP** services. **Postgres** and **Portainer** also use some **PersistenVolumes** and **PersistentVolumeClaims**. The latter also needs a **ClusterRole** and  **ClusterRoleBinding** in order to access the cluster's resources.

The entire Kubernetes **architecture** (i.e. pods, deployments, persistentVolumes etc.) is being built with **Terraform**, using the **"kubernetes"** provider.

---

## Installation

### Prerequisites:
- **docker-desktop** (or docker CE for Linux)
- **kind**
- **minikube** (for Windows Non-Pro) or MicroK8s (for Linux). If on Windows Pro or Mac, just **Enable Kubernetes** in the Docker-Desktop settings.
- **terraform**

### Step-by-step guide to set up the project locally:
1. Clone the repo:
    ```bash
   git clone https://github.com/luksy26/DevOps-Movie-Catalogue.git
   ```
2. Create the kind cluster:
   ```bash
   kind create cluster --config 00-cluster-config.yaml
   ```
   If on Windows, you can run the PowerShell script:
   ```bash
   ./restartKindCluster.ps1
   ```
   You can validate that everything worked with:
   ```bash
   kubectl cluster-info --context kind-kind
   ```
3. Create the Kubernetes resources:
    ```bash
   cd terraform-infra
   terraform init
   terraform fmt
   terraform plan
   terraform apply
   ```
   If on Windows, you can run the PowerShell script:
   ```bash
   ./restartClusterTerraform.ps1
   ```
4. That's it! Now you should be able to run:
    ```bash
   kubectl get all -o wide
   ```
5. After you're done, run the following commands to delete the resources and cluster:
    ```bash
    cd terraform-infra
    terraform destroy
    kind delete cluster
   ```
---

## Usage

1. The **API** routes are available via http://localhost:30000/api. Any API client (e.g. **Postman**) can be used to make requests.

2. The **PostgreSQL** database is also available via http://localhost:30001. Any Database Management tool (e.g. **DBeaver**) can be used to gain access. When prompted for credentials, enter the following:
    - **username**: admin
    - **password**: admin
    - **database**: movieApp

3. The **Portainer** web interface can be accessed via http://localhost:30002. If a timeout message happens to be displayed, just **restart** the portainer deployment:
    ```bash
    kubectl rollout restart deployment portainer
    ```
