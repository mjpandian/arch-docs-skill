# YAML, Kubernetes & Infrastructure as Code (IaC) Reference

Guidelines for scanning, analyzing, and documenting configuration, Kubernetes manifests, and Infrastructure as Code.

## Detect

- **Configuration Files**: `*.yaml`, `*.yml`, `*.json`, `*.toml`, `*.xml`, `*.ini`.
- **Kubernetes Markers**: `kustomization.yaml`, `Chart.yaml`, `values.yaml`, manifests with `apiVersion:` and `kind:`.
- **Terraform / OpenTofu**: `*.tf`, `*.tfvars`, `*.hcl`, `.terraform.lock.hcl`.
- **Container Markers**: `Dockerfile`, `Containerfile`, `docker-compose.yml`, `compose.yaml`.
- **CI/CD Pipelines**: `.github/workflows/*.yml`, `.gitlab-ci.yml`, `azure-pipelines.yml`, `Jenkinsfile`.

## Entry Points

- **Kubernetes Ingress & Gateways**: `kind: Ingress`, Gateway API HTTPRoute manifests defining hostnames, TLS termination, and path-based routing.
- **Service Declarations**: `kind: Service` (ClusterIP, NodePort, LoadBalancer).
- **Scheduled Workloads**: `kind: CronJob` scheduling periodic batch workloads.
- **Continuous Deployment Triggers**: GitHub Actions workflow triggers (`on: push`, `on: schedule`), GitLab pipeline stages.

## Hidden Wiring

- **Kustomize Overlays**: Base manifests patched by overlays (`kustomization.yaml` with `bases` or `resources` and `patchesStrategicMerge`).
- **Helm Value Interpolation**: Template expressions (`{{ .Values.global.database.host }}`) injected from hierarchical `values.yaml` files.
- **Service Mesh Policies**: Istio `VirtualService`, `DestinationRule`, and Envoy sidecar injection annotations routing internal network traffic.
- **Terraform State References**: Remote state lookups (`data "terraform_remote_state"`) coupling infrastructure across different repository workspaces.

## Config and Secrets

- **Kubernetes Secrets & ConfigMaps**: `kind: ConfigMap`, `kind: Secret` (base64 encoded or external secret references).
- **Secret Operators**: External Secrets Operator (`kind: ExternalSecret`), SealedSecrets, HashiCorp Vault Agent Injector annotations.
- **Terraform Variable Files**: `terraform.tfvars`, environment variables (`TF_VAR_*`).
- **Risks**: Plaintext base64 secrets committed to git; cloud provider access keys hardcoded in Terraform variables.

## Data Access

- **Persistent Volumes**: `kind: PersistentVolume`, `kind: PersistentVolumeClaim`, StorageClasses (AWS EBS, GCP Persistent Disk, NFS).
- **Stateful Workloads**: `kind: StatefulSet` managing stateful database or cache pods with ordered volume claim templates.
- **Database Provisioning**: Cloud SQL, AWS RDS, or managed databases provisioned via Terraform modules.

## Concurrency

- **Replica Scaling**: `kind: Deployment` (`spec.replicas`), Horizontal Pod Autoscalers (`kind: HorizontalPodAutoscaler`) scaling on CPU, memory, or custom metrics.
- **Job Parallelism**: `kind: Job` with `spec.parallelism` and `spec.completions` for batch parallel tasks.
- **Locking in IaC**: Terraform state locking via Amazon DynamoDB or Terraform Cloud preventing concurrent state mutations.

## Performance

- **Resource Limits & Requests**: Container `resources.requests` and `resources.limits` preventing CPU throttling or Out-Of-Memory (OOM) kills.
- **Autoscaling & Cold Starts**: HPA scaling thresholds and startup probe definitions preventing traffic routing to unready replicas.
- **Network Latency**: Cross-AZ traffic costs and latency in multi-region Terraform VPC configurations.

## Security

- **Pod Security Standards**: `securityContext` (`runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, `capabilities.drop: ["ALL"]`).
- **Network Policies**: `kind: NetworkPolicy` enforcing zero-trust ingress and egress isolation between pod namespaces.
- **RBAC**: `kind: Role`, `kind: ClusterRole`, `kind: RoleBinding`, `kind: ServiceAccount` adhering to principle of least privilege.
- **Container Vulnerabilities**: Base images running as root; outdated package vulnerabilities in Dockerfiles.

## Exclusions

- **Generated & Local State**: `.terraform/*`, `*.tfstate`, `*.tfstate.backup`, `.terraform.lock.hcl`, `.helm/*`, `charts/*.tgz`.
- **Test Manifests**: `tests/*`, `fixtures/*`, mock values files (`*test*.yaml`).

## Tools

Export findings to SARIF 2.1.0 using these verified command options:

- **Kube-Linter** (Kubernetes manifest static analyzer):
  ```bash
  kube-linter lint . --format sarif > kubelinter.sarif
  ```

- **Trivy** (IaC and container configuration scanner):
  ```bash
  trivy config . --format sarif -o trivy.sarif
  ```

- **Checkov** (Static analysis for Terraform, Kubernetes, Dockerfile):
  ```bash
  checkov -d . -o sarif --output-file-path .
  ```

