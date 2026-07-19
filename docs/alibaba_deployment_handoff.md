# Alibaba Cloud Deployment Handoff

The submitted build is deployed on Alibaba Cloud ECS in `ALIBABA_CLOUD_MODE`.
See the [public proof gallery](alibaba_cloud_proof.md). This handoff now lists
the release controls to apply to a future deployment or material release; it
contains no secrets.

## Future release freeze point

Before deploying a new version or provisioning another cloud resource:

1. Record the exact `main` commit SHA.
2. Confirm backend tests, frontend production build, dependency audit, Docker
   configuration, and the local Qwen-backed demo all pass on that SHA.
3. Confirm the README, demo script, deck, and Devpost description use the same
   terminology and current-stack claims.
4. Do not start a cloud benchmark or record the final video against an
   uncommitted build.

## User-provided resources and approval

The project owner must approve the following billable or account-scoped work
before deployment:

- Alibaba Cloud account and target region;
- an ECS instance with public IP, or an approved Function Compute/ACK target;
- DashScope/Qwen API key;
- RAM principal with least-privilege access to one Tablestore instance and one
  OSS bucket;
- Tablestore endpoint and instance name;
- OSS bucket and endpoint;
- DNS name and TLS certificate decision, if a custom domain is wanted;
- budget ceiling and expected lifetime through the judging period.

Never paste any of these values into Git, screenshots, browser code, or chat.

## Deployment or release sequence

1. Create the ECS/Function Compute/ACK target in the selected Alibaba region.
2. Provision Tablestore and OSS, then grant only the required RAM permissions.
3. Copy `deploy/.env.production.example` to an untracked production env file
   on the deployment target; set `APP_MODE=alibaba` and `MEMORY_STORE=alibaba`.
4. Deploy the frozen commit using [deploy/README.md](../deploy/README.md) or
   [deployment_alibaba.md](deployment_alibaba.md).
5. Configure production CORS to the actual frontend origin, enable HTTPS, and
   restrict inbound access to the required ports.
6. Verify `/health` reports `qwen_configured: true`, Alibaba cloud mode, and
   the actual persistent-store configuration.
7. Create a memory, restart the backend, and prove it is still retrievable.
8. Run the final model-backed benchmark once and save the raw JSON with commit
   SHA, model, UTC timestamp, and provider status.

## Remaining evidence to capture

The public app, automatic creation, and cross-session Tablestore recall are
already captured in [the proof gallery](alibaba_cloud_proof.md). Before the
final submission, also capture or verify:

- memory persistence before and after a backend restart (verified by the
  cross-session proof and subsequent container redeployments);
- final benchmark JSON for the exact deployed SHA (committed under
  `assets/evaluation/`);
- public, English, under-three-minute demo video;
- final deck with verified public links.

Update [SUBMISSION.md](../SUBMISSION.md) with the public video URL after it is
uploaded. Do not add credentials or private account details to any evidence.
