# Alibaba Cloud Deployment Handoff

Deploy only after the local release gate in
[submission_readiness.md](submission_readiness.md) is green. This handoff
lists the external resources and approvals required; it contains no secrets.

## Freeze point

Before provisioning any cloud resource:

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

## Deployment sequence

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

## Evidence capture checklist

Capture only after the checks above pass:

- signed-out public frontend URL;
- public `/health` response with no credentials exposed;
- ECS/FC/ACK console proof of the running backend;
- Tablestore table with non-sensitive memory rows;
- OSS bucket with redacted artifacts;
- memory persistence before and after a backend restart;
- final benchmark JSON for the exact deployed SHA;
- public, English, under-three-minute demo video;
- final deck with verified public links.

Update [SUBMISSION.md](../SUBMISSION.md) and
[submission_readiness.md](submission_readiness.md) only after each item is
verified. Do not label deployment evidence as complete beforehand.
