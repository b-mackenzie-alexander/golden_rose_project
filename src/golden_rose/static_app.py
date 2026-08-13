from pathlib import Path

from fastapi import APIRouter, HTTPException
from starlette.responses import FileResponse

_BLOCKED_SUFFIXES = {".ts", ".tsx"}


def create_static_assets_router(dist_path: Path) -> APIRouter:
    root = dist_path.resolve()
    router = APIRouter(tags=["static-assets"], include_in_schema=False)

    def resolve_public_file(requested_path: str) -> Path:
        candidate = (root / requested_path).resolve()
        if not candidate.is_relative_to(root):
            raise HTTPException(status_code=404)
        relative_parts = candidate.relative_to(root).parts
        if any(part.startswith(".") for part in relative_parts):
            raise HTTPException(status_code=404)
        if candidate.suffix in _BLOCKED_SUFFIXES:
            raise HTTPException(status_code=404)
        if not candidate.is_file():
            raise HTTPException(status_code=404)
        return candidate

    def no_store_file_response(path: Path) -> FileResponse:
        return FileResponse(path, headers={"Cache-Control": "no-store"})

    @router.get("/index.html")
    def get_index() -> FileResponse:
        return no_store_file_response(resolve_public_file("index.html"))

    @router.get("/{asset_path:path}")
    def get_asset(asset_path: str) -> FileResponse:
        if asset_path == "api" or asset_path.startswith("api/"):
            raise HTTPException(status_code=404)
        try:
            return no_store_file_response(resolve_public_file(asset_path))
        except HTTPException:
            path = Path(asset_path)
            if path.suffix or any(part.startswith(".") for part in path.parts):
                raise
            return no_store_file_response(resolve_public_file("index.html"))

    return router
