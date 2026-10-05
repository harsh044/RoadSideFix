# app/core/exceptions.py

import logging

from fastapi import (
    Request,
    status,
)

from fastapi.exceptions import (
    RequestValidationError,
)

from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation error",
            "errors": exc.errors(),
        },
    )