from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy.engine import Engine

from golden_rose.api.environment import router as environment_router
from golden_rose.api.errors import install_exception_handlers
from golden_rose.api.health import router as health_router
from golden_rose.api.staff.employers import router as staff_employers_router
from golden_rose.config import Settings
from golden_rose.database import create_database_engine
from golden_rose.demo_access import DemoAccessMiddleware
from golden_rose.static_app import create_static_assets_router


def create_app(
    engine_factory: Callable[[], Engine] = create_database_engine,
) -> FastAPI:
    settings = Settings()  # type: ignore[call-arg]

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = engine_factory()
        app.state.db_engine = engine
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(lifespan=lifespan)
    if settings.environment == "develop":
        if (
            not settings.demo_access_enabled
            or settings.demo_access_password is None
            or settings.demo_access_expires_at is None
        ):
            raise RuntimeError("validated develop demo access configuration is missing")
        app.add_middleware(
            DemoAccessMiddleware,
            password=settings.demo_access_password,
            expires_at=settings.demo_access_expires_at,
        )
    install_exception_handlers(app)
    app.include_router(health_router)
    if settings.environment == "develop":
        app.include_router(environment_router)
    app.include_router(staff_employers_router)
    if settings.static_assets_path is not None:
        app.include_router(create_static_assets_router(Path(settings.static_assets_path)))
    return app


app = create_app()
