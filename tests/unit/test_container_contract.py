from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_docker_contract_uses_non_root_runtime_and_excludes_secret_surfaces() -> None:
    dockerfile = _read("Dockerfile")
    dockerignore = _read(".dockerignore")
    container_readme = _read("deploy/container/README.md")

    assert "FROM node:" in dockerfile
    assert "FROM python:" in dockerfile
    assert "useradd" in dockerfile
    assert "USER goldenrose" in dockerfile
    assert "COPY src/ ./src/" in dockerfile
    assert "COPY migrations/ ./migrations/" in dockerfile
    assert "COPY --from=web-build" in dockerfile
    assert "GOLDEN_ROSE_STATIC_ASSETS_PATH" in dockerfile
    assert "ENTRYPOINT" in dockerfile
    assert "golden-rose-run" in dockerfile
    assert "COPY tests" not in dockerfile
    assert "COPY . ." not in dockerfile
    assert "ARG GCP" not in dockerfile
    assert "SECRET" not in dockerfile

    for ignored_path in [
        ".env",
        ".env.*",
        "tests/",
        ".pytest_cache/",
        ".coverage",
        "htmlcov/",
        "node_modules/",
        "apps/web/node_modules/",
        "apps/web/dist/",
        ".hermes/",
        ".git/",
    ]:
        assert ignored_path in dockerignore

    assert "local-only" in container_readme
    assert "No image push" in container_readme
    assert "No GCP" in container_readme
    assert "fictional synthetic" in container_readme


def test_docker_contract_pins_base_images_by_digest() -> None:
    dockerfile = _read("Dockerfile")

    assert (
        "FROM node:22.22.3-bookworm-slim@sha256:16d364eebf6b62da439dc993d9b80940c78b0ca38438452f011ab9a25c752644 AS web-build"
        in dockerfile
    )
    assert (
        "FROM python:3.12.12-slim-bookworm@sha256:2986c55feb36e6cae00fa1fefb454283e4b33f35e75ff8bdd123b134130be301 AS runtime"
        in dockerfile
    )
    assert "FROM node:22.22.3-bookworm-slim AS web-build" not in dockerfile
    assert "FROM python:3.12.12-slim-bookworm AS runtime" not in dockerfile
