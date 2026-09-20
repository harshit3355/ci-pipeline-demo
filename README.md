# CI Pipeline Demo

A small Python HTTP service used to learn CircleCI with a GitHub repository. Each pipeline checks out the commit, runs unit tests, records JUnit test results, and—only after the tests pass—builds a Docker image and saves it as a downloadable build artifact.

```text
GitHub push -> CircleCI test job -> CircleCI Docker build job -> image artifact
                         tests must pass before image packaging
```

## Requirements

- Python 3.12 and `pip` for local work
- Docker Engine for local container builds (optional for the first CircleCI run)
- A GitHub repository connected to CircleCI

## Run locally

On Linux or Kali:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
pytest --junitxml=test-results/local.xml
```

Build and run the container if Docker is installed:

```bash
docker build --tag ci-pipeline-demo:local .
docker run --rm --publish 8080:8080 ci-pipeline-demo:local
```

In another terminal, check the endpoints:

```bash
curl http://localhost:8080/
curl http://localhost:8080/health
```

Stop the foreground container with Ctrl+C.

## Set up CircleCI

1. Create a GitHub repository named `ci-pipeline-demo` and push this project to its `main` branch.
2. Sign in to CircleCI with GitHub and create a project for that repository.
3. Authorize the CircleCI GitHub App for this repository. Grant access only to the repositories you want CircleCI to build.
4. Choose the existing `.circleci/config.yml` from the repository when CircleCI asks for the pipeline configuration.
5. Trigger the first pipeline from `main` and inspect both jobs.

The repository configuration starts with a test job. The image job requires the test job, so a failed test prevents packaging. The test job stores JUnit results for the CircleCI Tests view; the image job stores the Docker image tarball under the Artifacts tab. This demo builds the image but does not publish it to a registry.

## Make a change and watch CI run

Change the response message in `src/app.py`, update or add a test in `tests/`, then commit and push:

```bash
git add src tests
git commit -m "Update demo response"
git push
```

Open the project in CircleCI. A push should trigger the workflow. Review the test result view, image build logs, and the downloadable artifact. Also try making a test fail, pushing that change, observing that the image job is skipped, and then fixing the test.

## CI design choices

- Dependencies are pinned in `requirements-dev.txt` for repeatable test runs.
- Jobs are separate so the package step has an explicit dependency on successful tests.
- The container runs as a non-root user and exposes port 8080.
- The app has `/` and `/health` endpoints that can be reused later for monitoring and deployment exercises.
- The image is tagged with the commit SHA so it can be tied back to source.
- The pipeline stores results and the built image for review; it does not contain registry credentials or deploy anywhere.

## Next improvements

1. Add linting and coverage thresholds.
2. Add a CircleCI workflow filter for pull requests and protected branches.
3. Publish images to a container registry using restricted project variables or contexts.
4. Add image vulnerability scanning and generate a software bill of materials.
5. Reuse this app in the Ansible, Prometheus/Grafana, ELK, and Argo CD projects.

Keep tokens and registry credentials in CircleCI project settings or an approved secret store. Never place them in this repository or print them in build logs.
