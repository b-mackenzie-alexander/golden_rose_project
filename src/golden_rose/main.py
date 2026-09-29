from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy.engine import Engine

from golden_rose.api.environment import router as environment_router
from golden_rose.api.errors import install_exception_handlers
from golden_rose.api.health import router as health_router
from golden_rose.api.intake_transport import IntakeTransportMiddleware, intake_problem
from golden_rose.api.staff.canonical_corrections import router as canonical_corrections_router
from golden_rose.api.staff.canonical_reviews import router as canonical_reviews_router
from golden_rose.api.staff.contact_details import router as staff_contact_details_router
from golden_rose.api.staff.employer_outputs import router as staff_employer_outputs_router
from golden_rose.api.staff.employers import router as staff_employers_router
from golden_rose.api.staff.intake_workflows import router as staff_intake_workflows_router
from golden_rose.api.staff.intakes import router as staff_intakes_router
from golden_rose.api.staff.operator_readiness import router as staff_operator_readiness_router
from golden_rose.api.staff.staff_accounts import router as staff_accounts_router
from golden_rose.api.staff.staff_session import router as staff_session_router
from golden_rose.api.staff.workers import router as staff_workers_router
from golden_rose.application.intake_errors import IntakeError
from golden_rose.application.presentation_demo_seed import seed_presentation_demo_data
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
        seed_presentation_demo_data(engine, settings)
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
    # Also normalize new-namespace authentication denials from the demo gate.
    app.add_middleware(IntakeTransportMiddleware)
    install_exception_handlers(app)

    @app.exception_handler(IntakeError)
    async def handle_intake_error(request, exc: IntakeError):
        return intake_problem(exc.code, exc.status, missing_fields=exc.missing_fields)

    app.include_router(health_router)
    if settings.environment == "develop":
        app.include_router(environment_router)
    app.include_router(staff_employers_router)
    app.include_router(staff_employer_outputs_router)
    app.include_router(staff_contact_details_router)
    app.include_router(staff_intakes_router)
    app.include_router(staff_intake_workflows_router)
    app.include_router(staff_operator_readiness_router)
    app.include_router(staff_session_router)
    app.include_router(staff_accounts_router)
    app.include_router(staff_workers_router)
    app.include_router(canonical_corrections_router)
    app.include_router(canonical_reviews_router)
    if settings.static_assets_path is not None:
        app.include_router(create_static_assets_router(Path(settings.static_assets_path)))
    return app


app = create_app()
