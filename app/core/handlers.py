"""Map exceptions to safe JSON error responses (no stack traces or input echoes)."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import AirDataUnavailableError, LocationNotFoundError

logger = logging.getLogger(__name__)

RETRY_AFTER_SECONDS = "60"


def error_body(code: str, message: str) -> dict[str, str]:
    """Return the standard error payload."""
    return {"error": code, "message": message}


async def _validation(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)  # noqa: S101 - registered for this type
    details = [
        {"field": ".".join(str(part) for part in err["loc"] if part != "body"), "issue": err["msg"]}
        for err in exc.errors()
    ]
    body = error_body("validation_error", "Some inputs are invalid.") | {"details": details}
    return JSONResponse(status_code=422, content=body)


async def _not_found(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=error_body("location_not_found", "We couldn't find that place. Try another name."),
    )


async def _unavailable(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content=error_body(
            "air_data_unavailable", "Live air data is unavailable right now. Please try again."
        ),
    )


async def _rate_limited(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content=error_body("rate_limited", "Too many requests. Please wait a minute."),
        headers={"Retry-After": RETRY_AFTER_SECONDS},
    )


async def _http_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)  # noqa: S101 - registered for this type
    code = "not_found" if exc.status_code == 404 else "bad_request"
    return JSONResponse(status_code=exc.status_code, content=error_body(code, str(exc.detail)))


async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error", exc_info=exc)
    return JSONResponse(
        status_code=500, content=error_body("internal_error", "Something went wrong.")
    )


def register_error_handlers(app: FastAPI) -> None:
    """Attach all error handlers to the app."""
    app.add_exception_handler(RequestValidationError, _validation)
    app.add_exception_handler(LocationNotFoundError, _not_found)
    app.add_exception_handler(AirDataUnavailableError, _unavailable)
    app.add_exception_handler(RateLimitExceeded, _rate_limited)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(Exception, _unexpected)
