FROM docker.io/library/node:22.22.3-bookworm-slim@sha256:16d364eebf6b62da439dc993d9b80940c78b0ca38438452f011ab9a25c752644 AS web-build

WORKDIR /app/apps/web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

FROM docker.io/library/python:3.12.12-slim-bookworm@sha256:2986c55feb36e6cae00fa1fefb454283e4b33f35e75ff8bdd123b134130be301 AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GOLDEN_ROSE_STATIC_ASSETS_PATH=/app/static

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin goldenrose

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY scripts/verify_database_authority.py ./scripts/
COPY alembic.ini ./
COPY --from=web-build /app/apps/web/dist/ ./static/

RUN pip install --no-cache-dir .

USER goldenrose
EXPOSE 8080
ENTRYPOINT ["golden-rose-run"]
