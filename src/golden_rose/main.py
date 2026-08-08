from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.engine import Engine

from golden_rose.api.errors import install_exception_handlers
from golden_rose.api.staff.employers import router as staff_employers_router
from golden_rose.config import Settings
from golden_rose.database import create_database_engine


def create_app(
    engine_factory: Callable[[], Engine] = create_database_engine,
) -> FastAPI:
    Settings()  # type: ignore[call-arg]

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = engine_factory()
        app.state.db_engine = engine
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(lifespan=lifespan)
    install_exception_handlers(app)
    app.include_router(staff_employers_router)
    return app


app = create_app()
