from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from golden_rose.main import create_app
from golden_rose.static_app import create_static_assets_router


def test_static_app_serves_only_configured_vite_dist_directory(tmp_path: Path) -> None:
    workspace_secret = tmp_path / ".env"
    workspace_secret.write_text("GOLDEN_ROSE_SECRET=do-not-serve", encoding="utf-8")
    dist_path = tmp_path / "dist"
    asset_path = dist_path / "assets"
    asset_path.mkdir(parents=True)
    (dist_path / "index.html").write_text("<div id='root'></div>", encoding="utf-8")
    (asset_path / "app.js").write_text("console.log('fictional asset');", encoding="utf-8")
    (dist_path / ".env").write_text("DIST_SECRET=do-not-serve", encoding="utf-8")
    (dist_path / "source.tsx").write_text("export const secret = true;", encoding="utf-8")

    app = FastAPI()
    app.include_router(create_static_assets_router(dist_path))

    with TestClient(app) as client:
        asset_response = client.get("/assets/app.js")
        index_response = client.get("/index.html")
        dist_dotfile_response = client.get("/.env")
        source_response = client.get("/source.tsx")
        traversal_response = client.get("/../.env")
        missing_response = client.get("/assets/missing.js")

    assert asset_response.status_code == 200
    assert asset_response.text == "console.log('fictional asset');"
    assert asset_response.headers["Cache-Control"] == "no-store"
    assert index_response.status_code == 200
    assert "root" in index_response.text
    assert dist_dotfile_response.status_code == 404
    assert source_response.status_code == 404
    assert traversal_response.status_code == 404
    assert missing_response.status_code == 404


def test_create_app_mounts_configured_static_assets_directory(
    monkeypatch,
    tmp_path: Path,
) -> None:
    dist_path = tmp_path / "dist"
    dist_path.mkdir()
    (dist_path / "index.html").write_text("<main>Golden Rose staff app</main>", encoding="utf-8")

    class FakeEngine:
        def dispose(self) -> None:
            pass

    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv(
        "GOLDEN_ROSE_DATABASE_URL",
        "postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
    )
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")
    monkeypatch.setenv("GOLDEN_ROSE_STATIC_ASSETS_PATH", str(dist_path))

    fake_engine: Any = FakeEngine()
    app = create_app(engine_factory=lambda: fake_engine)

    with TestClient(app) as client:
        response = client.get("/index.html")

    assert response.status_code == 200
    assert "Golden Rose staff app" in response.text
    assert response.headers["Cache-Control"] == "no-store"


def test_api_paths_are_not_swallowed_by_frontend_fallback(tmp_path: Path) -> None:
    dist_path = tmp_path / "dist"
    dist_path.mkdir()
    (dist_path / "index.html").write_text("<main>Golden Rose staff app</main>", encoding="utf-8")

    app = FastAPI()
    app.include_router(create_static_assets_router(dist_path))

    with TestClient(app) as client:
        frontend_response = client.get("/employers/unknown-client-route")
        api_response = client.get("/api/staff/v1/not-a-real-api-route")
        api_method_response = client.post("/api/staff/v1/not-a-real-api-route")

    assert frontend_response.status_code == 200
    assert "Golden Rose staff app" in frontend_response.text
    assert frontend_response.headers["Cache-Control"] == "no-store"
    assert api_response.status_code == 404
    assert api_response.json() == {"detail": "Not Found"}
    assert "Golden Rose staff app" not in api_response.text
    assert api_method_response.status_code == 405
    assert api_method_response.headers["Allow"] == "GET"
    assert "Golden Rose staff app" not in api_method_response.text


def test_bare_api_paths_are_reserved_from_spa_fallback(tmp_path: Path) -> None:
    dist_path = tmp_path / "dist"
    dist_path.mkdir()
    (dist_path / "index.html").write_text("<main>Golden Rose staff app</main>", encoding="utf-8")

    app = FastAPI()
    app.include_router(create_static_assets_router(dist_path))

    with TestClient(app) as client:
        bare_api_response = client.get("/api")
        bare_api_query_response = client.get("/api?client=misconfigured")
        api_slash_response = client.get("/api/")

    assert bare_api_response.status_code == 404
    assert bare_api_response.json() == {"detail": "Not Found"}
    assert "Golden Rose staff app" not in bare_api_response.text
    assert bare_api_query_response.status_code == 404
    assert bare_api_query_response.json() == {"detail": "Not Found"}
    assert "Golden Rose staff app" not in bare_api_query_response.text
    assert api_slash_response.status_code == 404
    assert api_slash_response.json() == {"detail": "Not Found"}


def test_static_router_does_not_replace_api_method_semantics(
    monkeypatch,
    tmp_path: Path,
) -> None:
    dist_path = tmp_path / "dist"
    dist_path.mkdir()
    (dist_path / "index.html").write_text("<main>Golden Rose staff app</main>", encoding="utf-8")

    class FakeEngine:
        def dispose(self) -> None:
            pass

    monkeypatch.setenv("GOLDEN_ROSE_ENVIRONMENT", "local")
    monkeypatch.setenv("GOLDEN_ROSE_AUTH_MODE", "synthetic")
    monkeypatch.setenv(
        "GOLDEN_ROSE_DATABASE_URL",
        "postgresql+psycopg://test:test@127.0.0.1:55432/golden_rose",
    )
    monkeypatch.setenv("GOLDEN_ROSE_SYNTHETIC_STAFF_ID", "22222222-2222-4222-8222-222222222222")
    monkeypatch.setenv("GOLDEN_ROSE_STATIC_ASSETS_PATH", str(dist_path))

    fake_engine: Any = FakeEngine()
    app = create_app(engine_factory=lambda: fake_engine)

    with TestClient(app) as client:
        response = client.post("/api/staff/v1/employers/not-a-uuid")

    assert response.status_code == 405
    assert response.headers["Allow"] == "GET"
    assert response.headers["Cache-Control"] == "no-store"
    assert "Golden Rose staff app" not in response.text
