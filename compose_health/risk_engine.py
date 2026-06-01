"""Static Docker Compose risk checks."""

from __future__ import annotations

import re
from typing import Any

from compose_health.models import ComposeService, Risk, ServiceReport

SECRET_NAME_RE = re.compile(r"(PASSWORD|TOKEN|SECRET|KEY|API_KEY|PRIVATE)", re.IGNORECASE)
RISKY_HOST_PATHS = ("/", "/etc", "/var", "/home", "/mnt", "/root", "/usr", "/opt")


def analyze_services(services: list[ComposeService]) -> list[ServiceReport]:
    """Run the risk engine against all services."""

    return [ServiceReport(service=service, risks=analyze_service(service)) for service in services]


def analyze_service(service: ComposeService) -> list[Risk]:
    """Run all risk checks for one service."""

    risks: list[Risk] = []
    if not service.has_healthcheck:
        risks.append(
            Risk(
                "No healthcheck",
                "service has no container-level health signal",
                "Add a healthcheck where possible.",
            )
        )

    if service.restart_policy is None or service.restart_policy.lower() == "no":
        risks.append(
            Risk(
                "Restart policy missing or disabled",
                "service may not recover automatically",
                "Use unless-stopped or another intentional restart policy.",
            )
        )

    if service.privileged:
        risks.append(
            Risk(
                "Privileged mode enabled",
                "container has broad host access",
                "Avoid privileged mode unless strictly required.",
                severity="high",
            )
        )

    if any("/var/run/docker.sock" in _volume_source(volume) for volume in service.volumes):
        risks.append(
            Risk(
                "Docker socket mounted",
                "container can control the Docker host",
                "Avoid socket mounts or isolate them carefully.",
                severity="high",
            )
        )

    if _env_value(service, "NVIDIA_VISIBLE_DEVICES") == "all":
        risks.append(
            Risk(
                "Broad GPU visibility",
                "NVIDIA_VISIBLE_DEVICES=all gives broad GPU visibility",
                "Scope GPU access to specific devices where possible.",
            )
        )

    if service.network_mode == "host":
        risks.append(
            Risk(
                "Host networking",
                "container bypasses normal Docker network isolation",
                "Use explicit port mappings unless host networking is required.",
                severity="high",
            )
        )

    secret_names = sorted(name for name in service.environment if SECRET_NAME_RE.search(name))
    if secret_names:
        risks.append(
            Risk(
                "Sensitive-looking environment variables",
                f"secrets may be stored directly in compose file: {', '.join(secret_names)}",
                "Use .env, Docker secrets, or external secret management.",
                severity="high",
            )
        )

    broad_mounts = [_volume_source(volume) for volume in service.volumes]
    broad_mounts = [source for source in broad_mounts if _is_risky_host_path(source)]
    if broad_mounts:
        risks.append(
            Risk(
                "Broad host mount",
                f"container has broad host filesystem access: {', '.join(sorted(set(broad_mounts)))}",
                "Narrow volume permissions and paths.",
                severity="high",
            )
        )

    exposed_ports = [str(port) for port in service.ports if _binds_all_interfaces(port)]
    if exposed_ports:
        risks.append(
            Risk(
                "Ports exposed on all interfaces",
                f"service may be reachable from a broader network: {', '.join(exposed_ports)}",
                "Bind to 127.0.0.1 when local-only, or document intended exposure.",
            )
        )

    return risks


def _env_value(service: ComposeService, key: str) -> str | None:
    value = service.environment.get(key)
    return value.lower() if isinstance(value, str) else value


def _volume_source(volume: Any) -> str:
    if isinstance(volume, str):
        return volume.split(":", 1)[0]
    if isinstance(volume, dict):
        source = volume.get("source") or volume.get("src") or volume.get("host")
        return str(source) if source is not None else ""
    return str(volume)


def _is_risky_host_path(source: str) -> bool:
    if not source.startswith("/"):
        return False
    normalized = source.rstrip("/") or "/"
    return any(normalized == path or normalized.startswith(f"{path}/") for path in RISKY_HOST_PATHS)


def _binds_all_interfaces(port: Any) -> bool:
    if isinstance(port, int):
        return True
    if isinstance(port, dict):
        host_ip = port.get("host_ip")
        return host_ip in (None, "", "0.0.0.0", "::")

    text = str(port)
    if text.startswith(("127.0.0.1:", "localhost:", "[::1]:")):
        return False
    if text.startswith(("0.0.0.0:", "::")):
        return True
    parts = text.split(":")
    return len(parts) == 2 and all(parts)
