from pathlib import Path

from compose_health.parser import parse_compose_file
from compose_health.risk_engine import analyze_service

FIXTURES = Path(__file__).parent / "fixtures"


def risk_titles(fixture: str) -> set[str]:
    service = parse_compose_file(FIXTURES / fixture)[0]
    return {risk.title for risk in analyze_service(service)}


def test_detects_no_healthcheck() -> None:
    assert "No healthcheck" in risk_titles("minimal-compose.yml")


def test_detects_missing_restart_policy() -> None:
    assert "Restart policy missing or disabled" in risk_titles("minimal-compose.yml")


def test_detects_privileged_mode() -> None:
    assert "Privileged mode enabled" in risk_titles("risky-compose.yml")


def test_detects_docker_socket_mount() -> None:
    assert "Docker socket mounted" in risk_titles("risky-compose.yml")


def test_detects_broad_gpu_visibility() -> None:
    assert "Broad GPU visibility" in risk_titles("plex-compose.yml")


def test_detects_host_networking() -> None:
    assert "Host networking" in risk_titles("risky-compose.yml")


def test_detects_sensitive_environment_names_without_secret_values() -> None:
    service = parse_compose_file(FIXTURES / "risky-compose.yml")[0]
    risks = analyze_service(service)
    secret_risk = next(risk for risk in risks if risk.title == "Sensitive-looking environment variables")

    assert "API_TOKEN" in secret_risk.detail
    assert "super-secret" not in secret_risk.detail


def test_detects_broad_host_mounts() -> None:
    assert "Broad host mount" in risk_titles("risky-compose.yml")


def test_detects_ports_on_all_interfaces() -> None:
    assert "Ports exposed on all interfaces" in risk_titles("risky-compose.yml")
