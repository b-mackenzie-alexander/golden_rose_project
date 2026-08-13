FROM node:22.22.3-bookworm-slim AS web-build

WORKDIR /app/apps/web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

FROM python:3.12.12-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GOLDEN_ROSE_STATIC_ASSETS_PATH=/app/static

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin goldenrose

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini ./
COPY --from=web-build /app/apps/web/dist/ ./static/

RUN pip install --no-cache-dir .

USER goldenrose
EXPOSE 8080
ENTRYPOINT ["golden-rose-run"]
