"""Docker Compose YAML parsing and normalization."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from compose_health.models import ComposeService


class ComposeParseError(ValueError):
    """Raised when a compose file cannot be parsed into services."""


def parse_compose_file(path: Path | str) -> list[ComposeService]:
    """Parse a Docker Compose YAML file into normalized service summaries."""

    compose_path = Path(path)
    if not compose_path.exists():
        raise FileNotFoundError(f"Compose file not found: {compose_path}")
    if not compose_path.is_file():
        raise ComposeParseError(f"Compose path is not a file: {compose_path}")

    try:
        raw = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ComposeParseError(f"Invalid YAML in {compose_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ComposeParseError("Compose file must contain a mapping at the top level.")

    services = raw.get("services")
    if not isinstance(services, dict) or not services:
        raise ComposeParseError("Compose file does not define any services.")

    parsed: list[ComposeService] = []
    for name, config in services.items():
        if not isinstance(config, dict):
            raise ComposeParseError(f"Service {name!r} must be a mapping.")
        parsed.append(_parse_service(str(name), config))
    return parsed


def _parse_service(name: str, config: dict[str, Any]) -> ComposeService:
    build = config.get("build")
    build_context = _build_context(build)
    environment = _parse_environment(config.get("environment"))
    gpu_settings = _gpu_settings(config, environment)

    return ComposeService(
        name=name,
        image=_string_or_none(config.get("image")),
        build_context=build_context,
        has_healthcheck=_has_healthcheck(config),
        restart_policy=_string_or_none(config.get("restart")),
        ports=_list_value(config.get("ports")),
        volumes=_list_value(config.get("volumes")),
        environment=environment,
        networks=_parse_networks(config.get("networks")),
        devices=_list_value(config.get("devices")),
        privileged=bool(config.get("privileged", False)),
        gpu_settings=gpu_settings,
        network_mode=_string_or_none(config.get("network_mode")),
    )


def _build_context(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return _string_or_none(value.get("context"))
    return None


def _has_healthcheck(config: dict[str, Any]) -> bool:
    healthcheck = config.get("healthcheck")
    if not isinstance(healthcheck, dict):
        return False
    if healthcheck.get("disable") is True:
        return False
    return bool(healthcheck)


def _parse_environment(value: Any) -> dict[str, str | None]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return {str(key): None if val is None else str(val) for key, val in value.items()}
    if isinstance(value, list):
        parsed: dict[str, str | None] = {}
        for item in value:
            text = str(item)
            if "=" in text:
                key, val = text.split("=", 1)
                parsed[key] = val
            else:
                parsed[text] = None
        return parsed
    raise ComposeParseError("Service environment must be a mapping or list.")


def _parse_networks(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, dict):
        return [str(item) for item in value.keys()]
    raise ComposeParseError("Service networks must be a mapping or list.")


def _gpu_settings(config: dict[str, Any], environment: dict[str, str | None]) -> list[str]:
    settings: list[str] = []
    for key, value in environment.items():
        if key.startswith("NVIDIA_") or key.startswith("CUDA_"):
            settings.append(f"{key}={value}" if value is not None else key)
    for key in ("gpus", "runtime"):
        if key in config:
            settings.append(f"{key}: {config[key]}")
    deploy = config.get("deploy")
    resources = deploy.get("resources", {}) if isinstance(deploy, dict) else {}
    reservations = resources.get("reservations", {}) if isinstance(resources, dict) else {}
    if isinstance(reservations, dict) and "devices" in reservations:
        settings.append(f"deploy.resources.reservations.devices: {reservations['devices']}")
    return settings


def _list_value(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
