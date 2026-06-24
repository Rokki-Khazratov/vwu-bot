"""Domain exception hierarchy mapped to API error codes (ТЗ §32)."""

from __future__ import annotations


class AppError(Exception):
    """Base for all domain errors. Maps 1:1 to an API error code."""

    code: str = "INTERNAL_ERROR"
    http_status: int = 500
    message: str = "Internal error."

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict | None = None,
    ) -> None:
        self.message = message or self.message
        self.details = details or {}
        super().__init__(self.message)


# --- Access ---
class AccessDenied(AppError):
    code = "ACCESS_DENIED"
    http_status = 403
    message = "Access denied."


class UserBlocked(AppError):
    code = "USER_BLOCKED"
    http_status = 403
    message = "User is blocked."


# --- Not found ---
class SubjectNotFound(AppError):
    code = "SUBJECT_NOT_FOUND"
    http_status = 404
    message = "Subject not found."


class ExamProfileNotFound(AppError):
    code = "EXAM_PROFILE_NOT_FOUND"
    http_status = 404
    message = "Exam profile not found."


class BlueprintNotFound(AppError):
    code = "BLUEPRINT_NOT_FOUND"
    http_status = 404
    message = "Blueprint not found."


class TaskNotFound(AppError):
    code = "TASK_NOT_FOUND"
    http_status = 404
    message = "Task not found."


class SessionNotFound(AppError):
    code = "SESSION_NOT_FOUND"
    http_status = 404
    message = "Session not found."


class AttemptNotFound(AppError):
    code = "ATTEMPT_NOT_FOUND"
    http_status = 404
    message = "Attempt not found."


# --- Session / attempt lifecycle ---
class SessionInvalidState(AppError):
    code = "SESSION_INVALID_STATE"
    http_status = 409
    message = "Session cannot transition from its current state."


class SessionExpired(AppError):
    code = "SESSION_EXPIRED"
    http_status = 409
    message = "Session has expired."


class InvalidAnswerFormat(AppError):
    code = "INVALID_ANSWER_FORMAT"
    http_status = 422
    message = "Answer format is invalid."


class AttemptDuplicate(AppError):
    code = "ATTEMPT_DUPLICATE"
    http_status = 409
    message = "An attempt already exists for this session task."


class EvaluationInProgress(AppError):
    code = "EVALUATION_IN_PROGRESS"
    http_status = 409
    message = "Evaluation is already in progress."


class EvaluationFailed(AppError):
    code = "EVALUATION_FAILED"
    http_status = 502
    message = "Evaluation failed."


# --- LLM ---
class LLMUnavailable(AppError):
    code = "LLM_UNAVAILABLE"
    http_status = 503
    message = "LLM provider is unavailable."


class LLMSchemaInvalid(AppError):
    code = "LLM_SCHEMA_INVALID"
    http_status = 502
    message = "LLM response did not match the expected schema."


class ProviderQuotaExceeded(AppError):
    code = "PROVIDER_QUOTA_EXCEEDED"
    http_status = 429
    message = "Provider quota exceeded."


# --- Dictionary ---
class DictionaryWordNotFound(AppError):
    code = "DICTIONARY_WORD_NOT_FOUND"
    http_status = 404
    message = "Word not found."


class DictionaryProviderError(AppError):
    code = "DICTIONARY_PROVIDER_ERROR"
    http_status = 502
    message = "Dictionary provider error."


# --- Generic ---
class IdempotencyConflict(AppError):
    code = "IDEMPOTENCY_CONFLICT"
    http_status = 409
    message = "Idempotency key reused with a different payload."


class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    http_status = 422
    message = "Validation error."
