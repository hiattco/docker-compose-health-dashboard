"""Command line interface for compose-health."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from compose_health.parser import ComposeParseError, parse_compose_file
from compose_health.renderer import render_detail, render_json, render_table
from compose_health.risk_engine import analyze_services

app = typer.Typer(
    add_completion=False,
    help="Summarize Docker Compose service health, exposure, configuration, and risk signals.",
)


@app.command()
def main(
    compose_file: Annotated[Path, typer.Argument(help="Path to docker-compose.yml")],
    output_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: table or detail"),
    ] = "detail",
    as_json: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
) -> None:
    """Analyze a static Docker Compose YAML file."""

    console = Console(stderr=True if as_json else False)
    if output_format not in {"table", "detail"}:
        raise typer.BadParameter("--format must be table or detail")

    try:
        services = parse_compose_file(compose_file)
        reports = analyze_services(services)
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except ComposeParseError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    if as_json:
        typer.echo(render_json(reports))
    elif output_format == "table":
        render_table(reports, Console())
    else:
        render_detail(reports, Console())


if __name__ == "__main__":
    app()
