"""SQLAdmin web panel mounted at /admin.

Gives the private-beta administrator a real UI over the catalog, versioned
config, generated tasks, attempts/results, corrections and observability —
backed by the same SQLAlchemy models. Auth is a single admin credential from
settings (hardened in Phase 6).
"""

from __future__ import annotations

from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.core.config import get_settings
from app.core.database import engine
from app.modules.access.models import User
from app.modules.catalog.models import (
    ExamProfile,
    Guideline,
    Skill,
    Subject,
    TaskBlueprint,
    TaskFamily,
)
from app.modules.dictionary.models import DictionaryEntry
from app.modules.evaluation.models import (
    Attempt,
    DependencyRule,
    ErrorTaxonomy,
    EvaluationProfile,
    EvaluationResult,
    OutputSchema,
    PenaltyRule,
    PerformanceBand,
    PromptTemplate,
    Rubric,
    RubricCriterion,
    ScoreCorrection,
)
from app.modules.flashcards.models import FlashcardReview, UserWord
from app.modules.llm.models import LLMCall
from app.modules.system.models import AuditLog
from app.modules.tasks.models import TaskInstance
from app.modules.training.models import TrainingSession


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        settings = get_settings()
        if (
            form.get("username") == settings.admin_username
            and form.get("password") == settings.admin_password
        ):
            request.session.update({"admin": settings.admin_username})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return bool(request.session.get("admin"))


# --- Catalog ---
class SubjectAdmin(ModelView, model=Subject):
    category = "Catalog"
    column_list = [Subject.code, Subject.name, Subject.is_active]
    column_searchable_list = [Subject.code, Subject.name]


class ExamProfileAdmin(ModelView, model=ExamProfile):
    category = "Catalog"
    column_list = [ExamProfile.code, ExamProfile.name, ExamProfile.level, ExamProfile.is_active]


class SkillAdmin(ModelView, model=Skill):
    category = "Catalog"
    column_list = [Skill.code, Skill.name, Skill.position, Skill.is_active]


class TaskFamilyAdmin(ModelView, model=TaskFamily):
    category = "Catalog"
    column_list = [TaskFamily.code, TaskFamily.name, TaskFamily.answer_format, TaskFamily.is_active]


class TaskBlueprintAdmin(ModelView, model=TaskBlueprint):
    category = "Catalog"
    column_list = [TaskBlueprint.code, TaskBlueprint.version, TaskBlueprint.title,
                   TaskBlueprint.max_score, TaskBlueprint.is_active]


class GuidelineAdmin(ModelView, model=Guideline):
    category = "Catalog"
    column_list = [Guideline.code, Guideline.version, Guideline.status]


# --- Evaluation config ---
class RubricAdmin(ModelView, model=Rubric):
    category = "Config"
    column_list = [Rubric.code, Rubric.version, Rubric.max_score, Rubric.status]


class RubricCriterionAdmin(ModelView, model=RubricCriterion):
    category = "Config"
    column_list = [RubricCriterion.code, RubricCriterion.name, RubricCriterion.max_score]


class PerformanceBandAdmin(ModelView, model=PerformanceBand):
    category = "Config"
    column_list = [PerformanceBand.score, PerformanceBand.descriptor]


class PenaltyRuleAdmin(ModelView, model=PenaltyRule):
    category = "Config"
    column_list = [PenaltyRule.code, PenaltyRule.rule_type, PenaltyRule.is_active]


class DependencyRuleAdmin(ModelView, model=DependencyRule):
    category = "Config"
    column_list = [DependencyRule.id, DependencyRule.priority]


class EvaluationProfileAdmin(ModelView, model=EvaluationProfile):
    category = "Config"
    column_list = [EvaluationProfile.code, EvaluationProfile.evaluator_code,
                   EvaluationProfile.is_active]


class PromptTemplateAdmin(ModelView, model=PromptTemplate):
    category = "Config"
    column_list = [PromptTemplate.code, PromptTemplate.purpose, PromptTemplate.version,
                   PromptTemplate.status]


class OutputSchemaAdmin(ModelView, model=OutputSchema):
    category = "Config"
    column_list = [OutputSchema.code, OutputSchema.version, OutputSchema.status]


class ErrorTaxonomyAdmin(ModelView, model=ErrorTaxonomy):
    category = "Config"
    column_list = [ErrorTaxonomy.code, ErrorTaxonomy.version, ErrorTaxonomy.status]


# --- Tasks & attempts ---
class TaskInstanceAdmin(ModelView, model=TaskInstance):
    category = "Content"
    column_list = [TaskInstance.title, TaskInstance.difficulty, TaskInstance.status,
                   TaskInstance.created_at]
    column_searchable_list = [TaskInstance.title]


class TrainingSessionAdmin(ModelView, model=TrainingSession):
    category = "Activity"
    column_list = [TrainingSession.id, TrainingSession.mode, TrainingSession.status,
                   TrainingSession.score_earned, TrainingSession.created_at]


class AttemptAdmin(ModelView, model=Attempt):
    category = "Activity"
    column_list = [Attempt.id, Attempt.status, Attempt.score_final, Attempt.score_max,
                   Attempt.word_count, Attempt.created_at]


class EvaluationResultAdmin(ModelView, model=EvaluationResult):
    category = "Activity"
    column_list = [EvaluationResult.id, EvaluationResult.final_score, EvaluationResult.max_score,
                   EvaluationResult.confidence, EvaluationResult.created_at]


class ScoreCorrectionAdmin(ModelView, model=ScoreCorrection):
    category = "Activity"
    column_list = [ScoreCorrection.id, ScoreCorrection.kind, ScoreCorrection.reason,
                   ScoreCorrection.created_at]


# --- Observability ---
class LLMCallAdmin(ModelView, model=LLMCall):
    category = "Observability"
    column_list = [LLMCall.purpose, LLMCall.provider, LLMCall.model, LLMCall.status,
                   LLMCall.input_tokens, LLMCall.output_tokens, LLMCall.created_at]
    can_create = can_edit = can_delete = False


class AuditLogAdmin(ModelView, model=AuditLog):
    category = "Observability"
    column_list = [AuditLog.action, AuditLog.entity_type, AuditLog.entity_id,
                   AuditLog.reason, AuditLog.created_at]
    can_create = can_edit = can_delete = False


class UserAdmin(ModelView, model=User):
    category = "Access"
    column_list = [User.telegram_id, User.username, User.status, User.last_seen_at]


# --- Vocabulary ---
class DictionaryEntryAdmin(ModelView, model=DictionaryEntry):
    category = "Vocabulary"
    column_list = [DictionaryEntry.normalized_word, DictionaryEntry.source_language,
                   DictionaryEntry.target_language, DictionaryEntry.fetched_at]
    column_searchable_list = [DictionaryEntry.normalized_word]


class UserWordAdmin(ModelView, model=UserWord):
    category = "Vocabulary"
    column_list = [UserWord.id, UserWord.knowledge_level, UserWord.interval_days,
                   UserWord.next_review_at, UserWord.created_at]


class FlashcardReviewAdmin(ModelView, model=FlashcardReview):
    category = "Vocabulary"
    column_list = [FlashcardReview.grade, FlashcardReview.interval_days,
                   FlashcardReview.reviewed_at]


_VIEWS = [
    SubjectAdmin, ExamProfileAdmin, SkillAdmin, TaskFamilyAdmin, TaskBlueprintAdmin,
    GuidelineAdmin, RubricAdmin, RubricCriterionAdmin, PerformanceBandAdmin,
    PenaltyRuleAdmin, DependencyRuleAdmin, EvaluationProfileAdmin, PromptTemplateAdmin,
    OutputSchemaAdmin, ErrorTaxonomyAdmin, TaskInstanceAdmin, TrainingSessionAdmin,
    AttemptAdmin, EvaluationResultAdmin, ScoreCorrectionAdmin, LLMCallAdmin,
    AuditLogAdmin, UserAdmin, DictionaryEntryAdmin, UserWordAdmin, FlashcardReviewAdmin,
]


def setup_admin(app: FastAPI) -> Admin:
    settings = get_settings()
    admin = Admin(
        app,
        engine,
        title="VWU Admin",
        authentication_backend=AdminAuth(secret_key=settings.session_secret),
    )
    for view in _VIEWS:
        admin.add_view(view)
    return admin
