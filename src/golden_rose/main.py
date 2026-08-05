from fastapi import FastAPI

from golden_rose.api.errors import install_exception_handlers
from golden_rose.api.staff.employers import router as staff_employers_router
from golden_rose.config import Settings


def create_app() -> FastAPI:
    Settings()  # type: ignore[call-arg]
    app = FastAPI()
    install_exception_handlers(app)
    app.include_router(staff_employers_router)
    return app


app = create_app()
