from __future__ import annotations


class BackendError(Exception):
    """A backend error envelope entry or transport failure (ТЗ §24)."""

    def __init__(
        self,
        code: str,
        message: str = "",
        details: dict | None = None,
        http_status: int | None = None,
    ) -> None:
        self.code = code
        self.message = message or code
        self.details = details or {}
        self.http_status = http_status
        super().__init__(f"{code}: {self.message}")


class BackendUnavailable(BackendError):
    def __init__(self, message: str = "backend unavailable") -> None:
        super().__init__("BACKEND_UNAVAILABLE", message)
