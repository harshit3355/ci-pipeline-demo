# CI Pipeline Demo

A production-oriented CI learning project for a small Python HTTP service. CircleCI runs independent quality, dependency, and test gates on every push. Container packaging begins only after those gates pass; the image is smoke-tested, scanned, and saved with its reports and CycloneDX SBOM.

```text
GitHub push / pull request
  ├── static analysis: Ruff + Bandit
  ├── dependency audit: pip-audit
  └── unit tests: pytest + coverage gate
          all three must pass
              ↓
      build + smoke-test container
              ↓
      Trivy scan + SBOM + image artifact
```

This is an **enterprise-oriented CI baseline**, not a complete enterprise release system. It does not publish to a registry or deploy. Those steps need protected environments, least-privilege identity, approval policy, and repository-specific infrastructure.

## What the pipeline enforces

- **Quality:** Ruff lint and format checks; Bandit static security analysis.
- **Dependency security:** `pip-audit` checks the pinned Python development tool requirements against published vulnerability advisories.
- **Tests:** pytest produces JUnit results and a coverage report; the job fails below 80% coverage.
- **Gating:** image build waits for static analysis, dependency audit, and tests to pass.
- **Container:** the image uses a specific Python patch tag, runs as a non-root user, exposes a health check, and is tagged with the source commit SHA.
- **Smoke test:** CI starts the built image and checks `/health` before proceeding.
- **Supply chain:** Trivy's pinned release archive is SHA-256 checked before use; the pipeline scans source/config and the container for high or critical findings and emits a CycloneDX SBOM.
- **Evidence:** CircleCI stores test results, coverage, scanner reports, the SBOM, and the image tarball as job artifacts.
- **Dependency updates:** Dependabot proposes weekly updates for pinned Python tools and the Docker base image. Updates still pass through the same gates.
- **No CI secrets:** these jobs have no registry or deployment credentials, so untrusted code does not need access to secrets.

The project pins direct Python tool versions, the Python patch tag, and CircleCI's dated monthly base image. For strict reproducibility in a production organization, also lock transitive Python dependencies with hashes and pin executor/base images by digest. Update those locks and digests through reviewed dependency update pull requests.

## Service endpoints

- `GET /` returns the service message and `APP_VERSION`.
- `GET /health` returns `{"status":"ok"}` for container/orchestrator health checks.
- Other paths return a JSON 404 response.
- The app defaults to loopback (`127.0.0.1`) when run directly. The Docker image explicitly sets `APP_HOST=0.0.0.0` so published container ports can reach the service.

The service uses Python's standard library at runtime. Test and security tools are isolated in `requirements-dev.txt` and are not copied into the runtime image.

## Requirements

- Python 3.12 and pip for local development
- Docker Engine for local container builds (optional for CircleCI)
- A GitHub repository connected to CircleCI

## Run checks locally

On Kali or another Linux machine:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --disable-pip-version-check -r requirements-dev.txt
ruff check --output-format=full .
ruff format --check .
bandit --recursive src --severity-level medium --confidence-level medium
pip-audit --requirement requirements-dev.txt
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

Build and run the container locally:

```bash
docker build --build-arg APP_VERSION=local --tag ci-pipeline-demo:local .
docker run --rm --publish 8080:8080 ci-pipeline-demo:local
```

In another terminal:

```bash
curl http://localhost:8080/
curl http://localhost:8080/health
```

Stop the foreground container with Ctrl+C.

## Connect GitHub to CircleCI

1. Create a GitHub repository and push this project to `main`.
2. Sign in to CircleCI with GitHub, select **Create Project**, and choose the repository.
3. Authorize the CircleCI GitHub App for this repository only where possible.
4. Select the existing `.circleci/config.yml` and start a pipeline.
5. Confirm the three validation jobs run first and `build-scan-package` starts only after they pass.
6. Inspect the CircleCI **Tests** view, then download artifacts from the package job: SARIF reports, `sbom.cdx.json`, coverage data, and the commit-tagged image tarball.

CircleCI's GitHub App setup connects a repository and can use its committed `.circleci/config.yml` to configure the project. [CircleCI project setup](https://circleci.com/docs/guides/getting-started/create-project/)

## GitHub repository controls to configure

After the first CircleCI run, protect `main` in GitHub:

1. Require pull requests before merging and require at least one approving review when collaborators are involved.
2. Require the CircleCI checks for `static-analysis`, `dependency-audit`, `unit-tests`, and `build-scan-package`.
3. Require branches to be up to date before merging if that matches your workflow.
4. Restrict direct pushes to `main` and disallow force pushes/deletion.
5. Keep the GitHub CircleCI App as the source for required check statuses.

GitHub branch protection supports required reviews and status checks. Select the exact CircleCI check names shown in your repository after the first run. [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)

## Secrets and future release jobs

This pipeline deliberately has no secrets or deploy job. When adding registry publishing or deployment:

- Put credentials in a restricted CircleCI context, never in `.circleci/config.yml`, source, or logs.
- Restrict that context to the project, protected branch, and smallest authorized team.
- Prefer CircleCI OIDC with short-lived cloud credentials over long-lived access keys where the provider supports it.
- Attach the restricted context only to the release job, after all validation gates and an approval step.
- Publish images by digest and promote the same tested artifact between environments; do not rebuild separately for production.
- Record image digest, source commit, SBOM, scanner result, and approver with the release.

CircleCI contexts can restrict secret access, and its OIDC tokens can authenticate jobs to compatible cloud services without storing long-lived cloud credentials in CircleCI. [CircleCI contexts](https://circleci.com/docs/guides/security/contexts/) · [CircleCI OIDC](https://circleci.com/docs/guides/permissions-authentication/openid-connect-tokens/)

## Scheduled security refresh

Image and dependency advisories change even when source code does not. After setting up the project, configure a scheduled pipeline on `main` in CircleCI to rerun the same validation and image scan weekly. This provides a fresh scan against updated advisory data; keep the schedule free of deployment contexts.

## Make a change and observe the gates

1. Change the message in `src/app.py` and add or update a test.
2. Run the local checks above.
3. Create a topic branch, commit, push, and open a pull request.
4. Observe all three validation jobs run in parallel.
5. Make a test fail temporarily and confirm packaging is blocked; then fix it and confirm the pipeline produces the image and SBOM.

## Troubleshooting

- **Ruff or Bandit fails:** read the job output and fix the issue; do not suppress a finding just to make the gate green.
- **Coverage gate fails:** add meaningful tests for the uncovered behavior rather than lowering the threshold without review.
- **`pip-audit` fails:** identify the vulnerable dependency and update the pinned version through a reviewed change.
- **Trivy finds a high/critical vulnerability:** inspect the SARIF report, update the base image or dependency, and rebuild. `--ignore-unfixed` means only vulnerabilities with an available fix are blocking.
- **Docker build fails:** inspect build logs and the base-image pull status.
- **CircleCI cannot see the repo:** check the selected CircleCI organization and GitHub App repository access.

## Project scope and next improvements

This repo establishes CI gates and a traceable image artifact. Production rollout would additionally need full dependency lockfiles with hashes, executor and image digest pinning, registry publication with OIDC, image signing/attestation, required branch checks, SBOM/vulnerability retention policy, and a protected deployment workflow with approval and rollback. Those controls depend on the target registry, cloud, and organization policy, so they should be added when those are chosen.
