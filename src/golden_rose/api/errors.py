from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from golden_rose.application.create_draft_employer import (
    IdempotencyConflictError,
    SafePersistenceError,
)


class InvalidIdempotencyKeyError(ValueError):
    pass


def problem_response(*, status_code: int, title: str, detail: str, type_: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "type": type_,
            "title": title,
            "detail": detail,
            "status": status_code,
        },
    )


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(InvalidIdempotencyKeyError)
    async def handle_invalid_idempotency_key(
        request: Request, exc: InvalidIdempotencyKeyError
    ) -> JSONResponse:
        return problem_response(
            status_code=400,
            title="Bad Request",
            detail="invalid idempotency key",
            type_="https://golden-rose.local/problems/invalid-idempotency-key",
        )

    @app.exception_handler(IdempotencyConflictError)
    async def handle_idempotency_conflict(
        request: Request, exc: IdempotencyConflictError
    ) -> JSONResponse:
        return problem_response(
            status_code=409,
            title="Conflict",
            detail=str(exc),
            type_="https://golden-rose.local/problems/idempotency-conflict",
        )

    @app.exception_handler(PermissionError)
    async def handle_permission_error(request: Request, exc: PermissionError) -> JSONResponse:
        return problem_response(
            status_code=403,
            title="Forbidden",
            detail="forbidden",
            type_="https://golden-rose.local/problems/forbidden",
        )

    @app.exception_handler(SafePersistenceError)
    async def handle_safe_persistence_error(
        request: Request, exc: SafePersistenceError
    ) -> JSONResponse:
        return problem_response(
            status_code=503,
            title="Service Unavailable",
            detail="service unavailable",
            type_="https://golden-rose.local/problems/service-unavailable",
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return problem_response(
            status_code=422,
            title="Unprocessable Entity",
            detail="request validation failed",
            type_="https://golden-rose.local/problems/request-validation",
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        return problem_response(
            status_code=500,
            title="Internal Server Error",
            detail="internal server error",
            type_="https://golden-rose.local/problems/internal-error",
        )
