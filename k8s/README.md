# Deploying to EKS

Prerequisites: `terraform apply` in `../terraform/` has completed (cluster,
ECR repos, RDS, SQS all exist), `kubectl` is pointed at the cluster
(`terraform output configure_kubectl`), and the [AWS Load Balancer
Controller](https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html)
is installed cluster-wide (one-time, not part of this repo's manifests).

## First-time setup

1. Fill in the placeholders (`<ACCOUNT_ID>`, `<ECR_..._REPO_URL>`,
   `<ACM_CERTIFICATE_ARN>`, `<DOMAIN_NAME>`) using `terraform output` values.
2. Build a real `03-secret.yaml` from `03-secret.example.yaml` -- don't
   commit it. In a real pipeline this comes from CI/CD secrets or [External
   Secrets Operator](https://external-secrets.io/) synced from the
   `aws_secretsmanager_secret.db_password` Terraform already created, not a
   hand-maintained file.

## Every deploy

```bash
kubectl apply -f 00-namespace.yaml
kubectl apply -f 01-serviceaccounts.yaml
kubectl apply -f 02-configmap.yaml
kubectl apply -f 03-secret.yaml   # your filled-in copy, not the .example

# Substitute the real image tag, then run migrations and WAIT for success
# before rolling out new pods -- this is why RUN_MIGRATIONS_ON_BOOT=false in
# prod (02-configmap.yaml): nobody else applies the schema.
sed "s/<TAG>/$IMAGE_TAG/g; s#<ECR_BACKEND_REPO_URL>#$ECR_BACKEND_URL#g" \
  06-migrate-job.yaml | kubectl apply -f -
kubectl wait --for=condition=complete job/portal-migrate-$IMAGE_TAG -n vcode-fr-hc --timeout=120s

kubectl apply -f 04-deployment-backend.yaml
kubectl apply -f 05-deployment-worker.yaml
kubectl apply -f 07-deployment-frontend.yaml
kubectl apply -f 08-hpa.yaml
kubectl apply -f 09-ingress.yaml
```

Image tags in the Deployment manifests should also be substituted (or
templated via `kustomize edit set image`, or run through Helm if this grows
into a chart -- plain `sed`/kustomize is enough at this stage; don't reach for
Helm until the raw YAML actually gets unwieldy).

## Verifying a rollout

```bash
kubectl get pods -n vcode-fr-hc -w
kubectl logs -n vcode-fr-hc -l app=sync-worker --tail=50
kubectl get hpa -n vcode-fr-hc
```

## Scaling notes

- `backend-api` and `frontend` scale on request-driven CPU load -- normal HPA behavior.
- `sync-worker` scaling on CPU is a placeholder, not the right long-term
  signal: a worker sits idle between jobs, so CPU-based scaling reacts late
  and coarsely. Once sync volume actually matters, replace `08-hpa.yaml`'s
  worker HPA with [KEDA's SQS scaler](https://keda.sh/docs/latest/scalers/aws-sqs/)
  to scale on queue depth directly -- more workers exactly when the backlog
  grows, not after CPU catches up.
- Node-level capacity comes from the EKS managed node group's own
  autoscaler (`terraform/eks.tf`, bounded by `eks_node_max_size`). Raise that
  var before raising HPA `maxReplicas` values, or pods go `Pending` with
  nowhere to schedule.
