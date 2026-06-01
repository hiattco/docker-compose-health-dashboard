"""Rich and JSON output rendering."""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from compose_health.models import ServiceReport


def render_table(reports: list[ServiceReport], console: Console) -> None:
    """Render a compact one-row-per-service table."""

    table = Table(title="Docker Compose Health Dashboard")
    table.add_column("Service", style="bold")
    table.add_column("Image/Build")
    table.add_column("Health")
    table.add_column("Restart")
    table.add_column("Ports")
    table.add_column("Risks")

    for report in reports:
        service = report.service
        source = service.image or (f"build: {service.build_context}" if service.build_context else "-")
        table.add_row(
            service.name,
            source,
            "yes" if service.has_healthcheck else "no",
            service.restart_policy or "-",
            _count_or_join(service.ports),
            str(len(report.risks)),
        )
    console.print(table)


def render_detail(reports: list[ServiceReport], console: Console) -> None:
    """Render detailed service sections."""

    for report in reports:
        service = report.service
        body = Table.grid(padding=(0, 1))
        body.add_column(style="bold")
        body.add_column()
        body.add_row("Image", service.image or "-")
        body.add_row("Build context", service.build_context or "-")
        body.add_row("Healthcheck", "yes" if service.has_healthcheck else "no")
        body.add_row("Restart policy", service.restart_policy or "-")
        body.add_row("Ports", _count_or_join(service.ports))
        body.add_row("Volumes", str(len(service.volumes)))
        body.add_row("Environment", f"{len(service.environment)} variables")
        body.add_row("Networks", _count_or_join(service.networks))
        body.add_row("Devices", _count_or_join(service.devices))
        body.add_row("Privileged", "yes" if service.privileged else "no")
        body.add_row("GPU settings", _count_or_join(service.gpu_settings))

        risks = Text()
        if report.risks:
            for risk in report.risks:
                risks.append(f"- {risk.title}: {risk.detail}\n", style=_risk_style(risk.severity))
        else:
            risks.append("- No risks detected\n", style="green")

        suggestions = Text()
        if report.suggestions:
            for suggestion in report.suggestions:
                suggestions.append(f"- {suggestion}\n")
        else:
            suggestions.append("- No suggestions\n", style="green")

        console.print(
            Panel(
                Group(body, Text("\nRisks", style="bold"), risks, Text("Suggestions", style="bold"), suggestions),
                title=f"Service: {service.name}",
                expand=False,
            )
        )


def render_json(reports: list[ServiceReport]) -> str:
    """Render reports as machine-readable JSON."""

    payload = []
    for report in reports:
        service = report.service
        payload.append(
            {
                "service": {
                    "name": service.name,
                    "image": service.image,
                    "build_context": service.build_context,
                    "has_healthcheck": service.has_healthcheck,
                    "restart_policy": service.restart_policy,
                    "ports": service.ports,
                    "volumes_count": len(service.volumes),
                    "environment_count": len(service.environment),
                    "networks": service.networks,
                    "devices": service.devices,
                    "privileged": service.privileged,
                    "gpu_settings": service.gpu_settings,
                    "network_mode": service.network_mode,
                },
                "risks": [
                    {
                        "title": risk.title,
                        "detail": risk.detail,
                        "suggestion": risk.suggestion,
                        "severity": risk.severity,
                    }
                    for risk in report.risks
                ],
                "suggestions": report.suggestions,
            }
        )
    return json.dumps(payload, indent=2)


def _count_or_join(values: list[Any]) -> str:
    if not values:
        return "-"
    return ", ".join(str(value) for value in values)


def _risk_style(severity: str) -> str:
    return "red" if severity == "high" else "yellow"
