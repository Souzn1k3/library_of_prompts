from typing import Any


class AppError(Exception):
    """Application-level error with HTTP mapping."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
        message_key: str | None = None,
        message_params: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.message_key = message_key
        self.message_params = message_params or {}


class NotFoundError(AppError):
    def __init__(self, resource: str, identifier: str) -> None:
        message_key = f"errors.not_found.{resource}"
        super().__init__(
            code="not_found",
            message=f"The requested {resource} was not found.",
            status_code=404,
            details={"resource": resource, "id": identifier},
            message_key=message_key,
            message_params={"resource": resource, "id": identifier},
        )


class ConflictError(AppError):
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        message_key: str | None = None,
        message_params: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="conflict",
            message=message,
            status_code=409,
            details=details,
            message_key=message_key,
            message_params=message_params,
        )
