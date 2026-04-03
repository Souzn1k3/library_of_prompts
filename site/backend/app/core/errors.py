from typing import Any


class AppError(Exception):
    """Application-level error with HTTP mapping."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppError):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            code="not_found",
            message=f"{resource} not found: {identifier}",
            status_code=404,
            details={"resource": resource, "id": identifier},
        )


class ConflictError(AppError):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(code="conflict", message=message, status_code=409, details=details)
