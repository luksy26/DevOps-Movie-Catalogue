provider "kubernetes" {
  config_path = "C:/Users/Lucas/.kube/config"
}

# Get all YAML manifest files from the KubernetesConfigs folder
locals {
  # List all YAML files in the KubernetesConfigs folder
  manifest_files = fileset("../KubernetesConfigs", "*.yaml")
}

# Apply each manifest using the kubernetes_manifest resource
resource "kubernetes_manifest" "all_manifests" {
  for_each = toset(local.manifest_files)

  # Load and decode each manifest file dynamically
  manifest = yamldecode(file("../KubernetesConfigs/${each.value}"))
}
