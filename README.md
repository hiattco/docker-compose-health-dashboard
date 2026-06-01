# docker-compose-health-dashboard

A fast, practical Python CLI for homelab users and small teams that reads a static
`docker-compose.yml` file and prints a local terminal dashboard summarizing each
service's health signals, exposure, configuration, and risk indicators.

The MVP intentionally analyzes compose files only. It does not call the Docker
API, inspect live containers, store data, authenticate, or sync with cloud
services.

## Install

From a local checkout:

```bash
python -m pip install -e ".[dev]"
```

Or with `uv`:

```bash
uv sync --extra dev
uv run compose-health ./docker-compose.yml
```

## Usage

```bash
compose-health ./docker-compose.yml
compose-health ./docker-compose.yml --format table
compose-health ./docker-compose.yml --format detail
compose-health ./docker-compose.yml --json
```

`detail` is the default format. The JSON output is designed for future
automation and web UI reuse.

## Example Output

```text
Service: plex
Image: plexinc/pms-docker
Healthcheck: yes
Restart policy: always
Ports: 32400:32400
Volumes: 2
Environment: 2 variables
Risks:
  - Broad GPU visibility: NVIDIA_VISIBLE_DEVICES=all gives broad GPU visibility
  - Broad host mount: container has broad host filesystem access: /mnt/media
  - Ports exposed on all interfaces: service may be reachable from a broader network: 32400:32400
Suggestions:
  - Scope GPU access to specific devices where possible.
  - Narrow volume permissions and paths.
  - Bind to 127.0.0.1 when local-only, or document intended exposure.
```

Secret-looking environment variable names are reported, but secret values are not
printed.

## Risk Checks

The current engine detects:

- Missing or disabled healthchecks
- Missing or disabled restart policies
- Privileged containers
- Docker socket mounts
- Broad GPU visibility with `NVIDIA_VISIBLE_DEVICES=all`
- Host networking
- Sensitive-looking environment variable names
- Broad bind mounts to host paths such as `/etc`, `/var`, `/home`, and `/mnt`
- Ports exposed on all interfaces

## Project Structure

```text
compose_health/
  cli.py
  models.py
  parser.py
  renderer.py
  risk_engine.py
tests/
  fixtures/
```

Parsing, risk detection, and rendering are separated so a future FastAPI web UI
can reuse the parser and risk engine without depending on terminal output code.

## Development

```bash
python -m pip install -e ".[dev]"
pytest
```

## MVP Scope

This release focuses on static analysis of a Docker Compose YAML file. It is a
local CLI for quickly spotting missing health signals, risky host access,
network exposure, and secret-handling smells before or during homelab and small
team deployments.

## Roadmap

- SARIF or structured policy output for CI use
- Severity filtering and configurable ignore rules
- More Compose schema coverage for advanced networking and deploy keys
- Optional FastAPI web UI using the same parser and risk engine
- Example checks for common images and homelab stacks
