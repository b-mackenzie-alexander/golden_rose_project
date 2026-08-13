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
