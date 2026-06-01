"""Internal data models for compose-health."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ComposeService:
    """Normalized service data extracted from a Docker Compose file."""

    name: str
    image: str | None = None
    build_context: str | None = None
    has_healthcheck: bool = False
    restart_policy: str | None = None
    ports: list[Any] = field(default_factory=list)
    volumes: list[Any] = field(default_factory=list)
    environment: dict[str, str | None] = field(default_factory=dict)
    networks: list[str] = field(default_factory=list)
    devices: list[Any] = field(default_factory=list)
    privileged: bool = False
    gpu_settings: list[str] = field(default_factory=list)
    network_mode: str | None = None


@dataclass(frozen=True)
class Risk:
    """A detected operational or exposure risk."""

    title: str
    detail: str
    suggestion: str
    severity: str = "medium"


@dataclass(frozen=True)
class ServiceReport:
    """A complete report for a single Compose service."""

    service: ComposeService
    risks: list[Risk]

    @property
    def suggestions(self) -> list[str]:
        """Return de-duplicated suggestions in detection order."""

        seen: set[str] = set()
        values: list[str] = []
        for risk in self.risks:
            if risk.suggestion not in seen:
                values.append(risk.suggestion)
                seen.add(risk.suggestion)
        return values
