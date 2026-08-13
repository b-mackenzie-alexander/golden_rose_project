# Local-only container contract

This directory documents the Slice B container build contract for the Golden Rose staff tracer.

## Scope

- local-only build and inspection evidence for the runtime image
- fictional synthetic data only
- no real staff, employer, worker, client, or production data
- no credentials in source, build args, image layers, logs, or chat

## Explicit non-scope

- No image push to Artifact Registry or any registry
- No GCP provisioning, API calls, service identity creation, or Cloud Run deployment
- No Cloud SQL connection
- No billing linkage
- No public access
- No production work

## Runtime contract

The image uses the `golden-rose-run` entrypoint from `golden_rose.runtime`.
It expects configuration through environment variables at runtime, including `PORT`.
The entrypoint binds Uvicorn to `0.0.0.0:$PORT` and returns a nonzero configuration status before startup when port or settings validation fails.

The Dockerfile builds React/Vite assets, copies them into `/app/static`, and sets `GOLDEN_ROSE_STATIC_ASSETS_PATH=/app/static` so FastAPI can serve the staff workspace and API from the same origin.

The runtime stage runs as the non-root `goldenrose` user and avoids copying tests, local evidence, secret files, `.hermes`, `.git`, node_modules, coverage output, and developer caches.
