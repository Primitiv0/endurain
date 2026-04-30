# Forgejo Runner for Multi-Arch Docker Images

This directory contains the local Forgejo runner setup used by the Docker publish workflow to build multi-architecture images. The self-hosted runner builds both AMD64 and ARM64 images, then publishes a multi-architecture manifest that points to both images.

## Workflow Logic

The workflow in `.forgejo/workflows/docker-publish.yml` has two jobs:

1. `build-arch-images` builds and pushes architecture-specific images.
  - `linux/amd64` runs on the self-hosted runner label `local-runner`.
  - `linux/arm64` runs on the self-hosted runner label `local-runner`.
2. `publish-manifests` waits for both builds and publishes manifest tags.

Release builds push these architecture images:

```text
codeberg.org/<owner>/<repo>:<release>-amd64
codeberg.org/<owner>/<repo>:<release>-arm64
```

Then the manifest job publishes these multi-arch tags:

```text
codeberg.org/<owner>/<repo>:<release>
codeberg.org/<owner>/<repo>:latest
```

Manual workflow runs push these architecture images:

```text
codeberg.org/<owner>/<repo>:dev-<commit-sha>-amd64
codeberg.org/<owner>/<repo>:dev-<commit-sha>-arm64
```

Then the manifest job publishes this multi-arch tag:

```text
codeberg.org/<owner>/<repo>:dev-<commit-sha>
```

## Requirements

- A machine capable of building Linux ARM64 containers.
- QEMU/binfmt support for `linux/amd64` when the runner host is ARM64, such as Apple Silicon.
- Docker installed and running on that machine.
- A Codeberg runner registration token for this repository, user, or organization.
- The repository secret `TOKEN_FOR_ACTIONS` configured with permission to push packages to Codeberg.

The runner does not need a public IP address. It connects outbound to Codeberg and polls for jobs.

## Create the Runner Config

From this directory, create the local runner data directory and generate the default config:

```bash
mkdir -p data/.cache
chmod -R 775 data

docker run --rm data.forgejo.org/forgejo/runner:12 \
  forgejo-runner generate-config > data/runner-config.yml
```

Get a runner token from Codeberg:

```text
Repository Settings -> Actions -> Runners -> Create new runner
```

Edit `data/runner-config.yml` and configure the Codeberg connection plus the label expected by the workflow:

```yaml
server:
  connections:
    codeberg:
      url: https://codeberg.org/
      uuid: <runner-uuid-from-codeberg>
      token: <runner-token-from-codeberg>

runner:
  capacity: 1 # or 2
  labels:
    - local-runner:docker://node:20-bookworm

container:
  privileged: true
```

`data/runner-config.yml` contains a secret token and must not be committed. The repository `.gitignore` ignores `docker_forgejo_runner/data` for this reason.

## Start the Runner

Create the local compose file from the committed example:

```bash
cp docker-compose.yml.example docker-compose.yml
```

Start the runner:

```bash
docker compose up -d
docker compose logs -f runner
```

The runner should appear as online in Codeberg under the runner settings page where it was registered.

## Enable AMD64 Builds on ARM64 Hosts

On Apple Silicon or another ARM64 host, the ARM64 image builds natively. The AMD64 image requires emulation because the Dockerfile executes architecture-specific binaries during `RUN` steps.

The `docker-in-docker` service exposes Docker on both the normal Unix socket and TCP port `2375`. If the service was already running before this compose file exposed the Unix socket, recreate it first:

```bash
docker compose up -d --force-recreate docker-in-docker runner
```

Test whether AMD64 containers can run inside Docker-in-Docker:

```bash
docker compose exec docker-in-docker \
  docker run --rm --platform linux/amd64 alpine uname -m
```

Expected output:

```text
x86_64
```

If Docker reports that the Unix socket is missing, use the explicit TCP endpoint instead:

```bash
docker compose exec docker-in-docker \
  docker -H tcp://127.0.0.1:2375 run --rm --platform linux/amd64 alpine uname -m
```

If the command cannot execute the AMD64 container, register binfmt in the Docker-in-Docker daemon:

```bash
docker compose exec docker-in-docker \
  docker -H tcp://127.0.0.1:2375 run --privileged --rm tonistiigi/binfmt --install amd64
```

Then rerun the `alpine uname -m` test.

## Stop or Restart the Runner

```bash
docker compose stop
docker compose start
docker compose restart
```

To inspect logs later:

```bash
docker compose logs -f runner
```

## Security Notes

This setup uses Docker-in-Docker. The workflow jobs get access to the dedicated `docker-in-docker` daemon, not the host Docker daemon. Keep `runner.capacity` set to `1` so the AMD64 build, ARM64 build, and manifest job run one after another on the same local runner.

Only register this runner for repositories or organizations you trust. A Forgejo runner executes workflow code from the repositories it is allowed to serve.

If a workflow requires `container.privileged: true` in `data/runner-config.yml`, treat that as a significant security tradeoff rather than a routine fix.

### Risks of Privileged Job Containers

- A privileged workflow container has much weaker isolation from the runner environment than a standard container.
- Malicious or compromised workflow code can interact with kernel features, devices, namespaces, and container runtime behavior that would normally be blocked.
- Container breakout risk is materially higher if a workflow step, dependency, or third-party action is hostile or vulnerable.
- Secrets, runtime state, mounted filesystems, network configuration, and other containers may be easier to inspect or influence.
- Any repository allowed to use the runner effectively gains a higher level of trust, because its workflow code runs with much broader powers.

### Recommended Guardrails

- Prefer a dedicated runner host or VM for privileged workloads instead of using a general-purpose machine.
- Restrict the runner to repositories and organizations you fully trust.
- Keep credentials short-lived and scoped as narrowly as possible, especially registry tokens.
- Pin third-party actions to specific revisions instead of moving references such as `@main`.
- Avoid colocating unrelated services or sensitive data on the same runner host.
- Reevaluate whether the build can be reworked to avoid privileged job containers before enabling them.

## Verifying Published Images

After a release or manual run, inspect the manifest from a machine with Docker or Buildah:

```bash
docker buildx imagetools inspect codeberg.org/<owner>/<repo>:<tag>
```

The output should list both platforms:

```text
linux/amd64
linux/arm64
```