from pathlib import Path

import pytest

from compose_health.parser import ComposeParseError, parse_compose_file

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_minimal_service_defaults() -> None:
    services = parse_compose_file(FIXTURES / "minimal-compose.yml")

    assert len(services) == 1
    service = services[0]
    assert service.name == "app"
    assert service.image == "nginx:alpine"
    assert service.has_healthcheck is False
    assert service.environment == {}


def test_parse_plex_service_details() -> None:
    service = parse_compose_file(FIXTURES / "plex-compose.yml")[0]

    assert service.name == "plex"
    assert service.has_healthcheck is True
    assert service.restart_policy == "always"
    assert service.ports == ["32400:32400"]
    assert service.environment["NVIDIA_VISIBLE_DEVICES"] == "all"
    assert service.networks == ["media"]


def test_missing_file_raises_useful_error(tmp_path: Path) -> None:
    missing = tmp_path / "docker-compose.yml"

    with pytest.raises(FileNotFoundError, match="Compose file not found"):
        parse_compose_file(missing)


def test_no_services_raises_useful_error(tmp_path: Path) -> None:
    compose = tmp_path / "compose.yml"
    compose.write_text("name: empty\n", encoding="utf-8")

    with pytest.raises(ComposeParseError, match="does not define any services"):
        parse_compose_file(compose)


def test_invalid_yaml_raises_parse_error(tmp_path: Path) -> None:
    compose = tmp_path / "compose.yml"
    compose.write_text("services:\n  app: [unterminated\n", encoding="utf-8")

    with pytest.raises(ComposeParseError, match="Invalid YAML"):
        parse_compose_file(compose)


def test_parse_service_with_empty_deploy_resources(tmp_path: Path) -> None:
    compose = tmp_path / "compose.yml"
    compose.write_text(
        """
services:
  app:
    image: nginx:alpine
    deploy:
      resources:
""",
        encoding="utf-8",
    )

    service = parse_compose_file(compose)[0]

    assert service.gpu_settings == []
