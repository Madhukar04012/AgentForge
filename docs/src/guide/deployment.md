# Deployment

Deploy your agent to a development environment or production with a CI/CD pipeline.

![Prototype to Production](../assets/prototype_to_prod.png)

---

## Infrastructure vs Deployment

**Infrastructure** (`agentforge infra`) provisions the cloud resources your agent needs — service accounts, IAM bindings, APIs, telemetry buckets, and Terraform state. It sets the stage but doesn't run your agent.

**Deployment** (`agentforge deploy`) takes your agent code and puts it on the provisioned infrastructure — building a container, pushing it to a registry, and starting the service.

The typical flow: provision infrastructure first, then deploy on top of it.

---

## Deploy to a Dev Environment

The simplest path to a running deployment:

**1. Set your dev project:**

```bash
gcloud config set project YOUR_DEV_PROJECT_ID
```

**2. Deploy the agent:**

```bash
agentforge deploy
```

The command reads your `deployment_target` from `agentforge-manifest.yaml` (under `create_params`) and dispatches to the right flow:

| `deployment_target`  | What happens                                  |
|----------------------|-----------------------------------------------|
| `agent_runtime`      | Agent Runtime deployment (fully managed)       |
| `cloud_run`          | `gcloud beta run deploy` (container on Cloud Run) |
| `gke`                | Terraform + Docker build + `kubectl apply`     |

The deployment target is set when you create your project:

```bash
agentforge create my-agent -d cloud_run    # or agent_runtime, gke
```

To change the deployment target for an existing project, use `scaffold enhance`:

```bash
agentforge scaffold enhance -d cloud_run
```

Run `agentforge scaffold enhance --help` to see all available options.

!!! tip
    To enable observability features (prompt-response logging, content logs), run `agentforge infra single-project` after deploying. Terraform provisions the telemetry resources and updates your service to use them. See the [Observability Guide](observability/index.md) for details.

**Verify it works:**

```bash
agentforge deploy --list    # List deployments
agentforge deploy --status  # Check deployment status
```

---

## Deployment Targets

### Agent Runtime

*Selected with `agentforge create my-agent -d agent_runtime`, or `create_params.deployment_target: agent_runtime` in `agentforge-manifest.yaml`.*

Fully managed runtime: you provide a `Dockerfile` (scaffolded for you) and Agent Engine builds and runs the container — no cluster or service to operate:

```bash
agentforge deploy --project my-gcp-project --region us-east1
```

Pass Docker build args or a container port; a prebuilt `--image` is not supported (Agent Runtime always builds from the Dockerfile):

```bash
agentforge deploy --build-args KEY=VALUE --port 8080
```

Check on an async deployment:

```bash
agentforge deploy --no-wait     # Start and return immediately
agentforge deploy --status      # Check progress later
```

### Cloud Run

*Selected with `agentforge create my-agent -d cloud_run`, or `create_params.deployment_target: cloud_run` in `agentforge-manifest.yaml`.*

Builds a container from source and deploys as a Cloud Run service:

```bash
agentforge deploy --project my-gcp-project --region us-east1
```

Override resource limits:

```bash
agentforge deploy --memory 8Gi --port 8080
```

Deploy a pre-built image instead of building from source:

```bash
agentforge deploy --image gcr.io/my-project/my-agent:v1
```

!!! tip
    If you need more advanced Cloud Run deployment features not exposed via `agentforge` flags, use `--dry-run` (or `-n`) to print the full `gcloud` command. You can then copy it and add additional arguments as needed.

### GKE

*Selected with `agentforge create my-agent -d gke`, or `create_params.deployment_target: gke` in `agentforge-manifest.yaml`.*

Deploys to a GKE cluster using Terraform and kubectl:

```bash
agentforge deploy --cluster-name my-cluster --project my-gcp-project
```

---

## Next Steps

- [CI/CD & Production](cicd.md) — set up automated pipelines for staging and production
- [Observability](observability/index.md) — monitor your deployed agent
