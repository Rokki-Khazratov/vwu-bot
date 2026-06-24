# Техническое задание: Backend API учебного Telegram-ассистента

**Статус:** Draft for implementation  
**Версия:** 1.0  
**Дата:** 2026-06-24  
**Связанные документы:**
- `TELEGRAM_BOT_TZ.md`
- `WRITING_ENGINE_ENGLISH_EXAMPLE.md`

---

## 1. Назначение

Backend является центральным слоем учебной системы. Он хранит предметы, экзаменационные профили, структуру заданий, пользовательские сессии, ответы, оценки, статистику, словарь и конфигурации LLM.

Telegram-бот является только клиентом API. Визуализация, кнопки, FSM и Telegram Rich Messages не должны находиться в backend.

---

## 2. Границы первой версии

### 2.1. Входит в MVP

- приватный доступ для заранее разрешённых Telegram-пользователей;
- несколько предметов;
- разные экзаменационные профили внутри предметов;
- конфигурируемые типы заданий;
- генерация заданий через LLM по versioned guidelines;
- банк готовых заданий;
- тренировочные сессии и mock-сессии;
- rule-based и LLM-based проверка;
- отдельный rubric-driven writing engine;
- сохранение ошибок и динамики пользователя;
- базовая статистика;
- словарь DE/EN → RU без LLM;
- личный словарь и базовые флэшкарточки;
- административные операции;
- OpenAPI-контракт.

### 2.2. Не входит в MVP

- публичная регистрация;
- платежи, подписки и лимиты тарифов;
- реферальная система;
- социальные функции;
- Mini App;
- публичный marketplace заданий;
- сложная ролевая модель;
- мобильное приложение;
- OCR рукописных работ;
- автоматическая публикация задания без проверки его структуры.

---

## 3. Технологический принцип

Конкретный stack выбирается позже. Спецификация должна быть реализуема на FastAPI, ASP.NET Core, Spring Boot или другом backend-стеке.

Обязательные технические возможности:

- REST API;
- OpenAPI 3.x;
- реляционная БД;
- миграции;
- JSON/JSONB-поля для динамических конфигураций;
- фоновые задачи;
- HTTP client для LLM и словарных API;
- структурированное логирование;
- контейнеризация;
- тестовый framework.

Рекомендуемый временный stack для прототипа:

- FastAPI;
- PostgreSQL;
- SQLAlchemy/Alembic;
- Pydantic;
- Redis + worker, когда появятся фоновые задачи.

Это рекомендация, а не часть бизнес-контракта.

---

## 4. Архитектурные принципы

1. **Backend независим от Telegram.**
2. **Writing оценивается через конфигурируемые rubrics, а не одним универсальным prompt.**
3. **Простые задания проверяются без LLM.**
4. **LLM-ответы всегда валидируются по JSON Schema.**
5. **Prompts, rubrics, guidelines и output schemas версионируются.**
6. **Старые результаты сохраняют ссылки на использованные версии.**
7. **Любой новый предмет добавляется через конфигурацию и стратегии, а не через каскад `if subject == ...`.**
8. **Backend возвращает смысловые данные, а не Telegram-разметку.**
9. **Write-операции должны быть идемпотентными.**
10. **История завершённых попыток неизменяема без административной корректировки.**

---

## 5. Высокоуровневая структура

```text
Client
  └── Telegram Bot

Backend API
  ├── Access
  ├── Academic Catalog
  ├── Task Generation
  ├── Task Bank
  ├── Training Sessions
  ├── Evaluation Router
  ├── Writing Engine
  ├── Error Analytics
  ├── Statistics
  ├── Dictionary
  ├── Flashcards
  ├── Admin
  └── System

External Services
  ├── LLM providers
  ├── PONS
  ├── Free Dictionary API
  ├── optional Yandex Dictionary
  └── optional self-hosted LanguageTool
```

---

## 6. Академическая модель

### 6.1. Subject

Предмет верхнего уровня.

Поля:

- `id`;
- `code`;
- `name`;
- `description`;
- `is_active`;
- `created_at`;
- `updated_at`.

Примеры кодов:

- `english`;
- `german`;
- `mathematics`;
- `chemistry`.

---

### 6.2. ExamProfile

Конкретная экзаменационная система или программа.

Поля:

- `id`;
- `subject_id`;
- `code`;
- `name`;
- `level`;
- `version`;
- `description`;
- `is_active`;
- `valid_from`;
- `valid_to`;
- `metadata`.

Примеры:

- `epe_b1_plus`;
- `epd_2026`;
- `vwu_math`.

---

### 6.3. Skill

Крупный навык или раздел.

Поля:

- `id`;
- `exam_profile_id`;
- `code`;
- `name`;
- `position`;
- `description`;
- `is_active`.

Примеры:

- `writing`;
- `reading`;
- `listening`;
- `grammar`;
- `strukturen`.

---

### 6.4. TaskFamily

Семейство заданий внутри навыка.

Поля:

- `id`;
- `skill_id`;
- `code`;
- `name`;
- `answer_format`;
- `default_evaluator_code`;
- `description`;
- `is_active`.

Примеры:

- `blog_comment`;
- `graph_description`;
- `sentence_transformation`;
- `multiple_choice`;
- `numeric_problem`.

---

### 6.5. TaskBlueprint

Главная конфигурация создания заданий.

Поля:

- `id`;
- `task_family_id`;
- `code`;
- `version`;
- `title`;
- `difficulty`;
- `recommended_minutes`;
- `target_word_count_min`;
- `target_word_count_max`;
- `max_score`;
- `generator_profile_id`;
- `evaluation_profile_id`;
- `rubric_id`, nullable;
- `guideline_id`;
- `content_schema`;
- `answer_schema`;
- `generation_constraints`;
- `is_active`.

Blueprint описывает:

- структуру задания;
- обязательные поля;
- тип медиа;
- количество content points;
- допустимые темы;
- ограничения генерации;
- evaluator;
- rubric;
- ожидаемый формат ответа.

---

### 6.6. Guideline

Versioned instructional context для генератора и evaluator.

Поля:

- `id`;
- `code`;
- `version`;
- `subject_id`;
- `exam_profile_id`;
- `skill_id`;
- `task_family_id`, nullable;
- `frontmatter`;
- `body_markdown`;
- `checksum`;
- `status`;
- `created_at`.

Статусы:

- `draft`;
- `active`;
- `archived`.

Guideline может храниться в Git как Markdown + YAML frontmatter и синхронизироваться в БД.

---

## 7. Rubric-driven scoring

Writing и другие открытые задания должны использовать отдельную модель rubrics.

### 7.1. Rubric

Поля:

- `id`;
- `code`;
- `name`;
- `version`;
- `exam_profile_id`;
- `task_family_id`;
- `max_score`;
- `description`;
- `status`.

---

### 7.2. RubricCriterion

Поля:

- `id`;
- `rubric_id`;
- `code`;
- `name`;
- `position`;
- `min_score`;
- `max_score`;
- `weight`;
- `description`.

---

### 7.3. PerformanceBand

Поля:

- `id`;
- `criterion_id`;
- `score`;
- `descriptor`;
- `machine_rules`;
- `examples`, optional.

Каждый возможный балл должен иметь официальный или утверждённый descriptor.

---

### 7.4. PenaltyRule

Детерминированные штрафы.

Поля:

- `id`;
- `rubric_id`;
- `code`;
- `rule_type`;
- `condition`;
- `action`;
- `priority`;
- `is_active`.

Примеры:

- штраф за количество слов;
- обнуление при слишком коротком тексте;
- ограничение максимального балла при неверном типе текста.

---

### 7.5. DependencyRule

Правила зависимости критериев.

Поля:

- `id`;
- `rubric_id`;
- `condition`;
- `action`;
- `priority`.

Пример:

- если `task_achievement = 0`, установить все критерии в 0.

---

## 8. EvaluationProfile

Профиль определяет, как проверять конкретное семейство заданий.

Поля:

- `id`;
- `code`;
- `version`;
- `task_family_id`;
- `evaluator_code`;
- `rubric_id`, nullable;
- `prompt_template_id`, nullable;
- `output_schema_id`;
- `error_taxonomy_id`;
- `provider_policy`;
- `model_policy`;
- `temperature`;
- `max_retries`;
- `confidence_threshold`;
- `is_active`.

Один и тот же generic writing engine должен работать с разными EvaluationProfile.

---

## 9. PromptTemplate и OutputSchema

### 9.1. PromptTemplate

Поля:

- `id`;
- `code`;
- `purpose`;
- `version`;
- `system_template`;
- `user_template`;
- `provider_hint`;
- `model_hint`;
- `settings`;
- `checksum`;
- `status`.

Назначения:

- `task_generation`;
- `writing_evaluation`;
- `open_answer_evaluation`;
- `error_classification`;
- `task_validation`.

---

### 9.2. OutputSchema

Поля:

- `id`;
- `code`;
- `version`;
- `json_schema`;
- `status`.

Все LLM-операции, используемые программой, обязаны возвращать structured output.

---

## 10. ErrorTaxonomy

Таксономия ошибок зависит от предмета и экзамена.

Поля:

- `id`;
- `code`;
- `name`;
- `version`;
- `subject_id`;
- `categories`;
- `status`.

Категория содержит:

- `code`;
- `name`;
- `parent_code`, optional;
- `severity_levels`;
- `description`.

Примеры для языка:

- `grammar`;
- `word_order`;
- `article`;
- `case`;
- `preposition`;
- `vocabulary`;
- `spelling`;
- `punctuation`;
- `coherence`;
- `register`;
- `task_fulfilment`.

---

## 11. Генерация заданий

### 11.1. TaskGenerator interface

```text
generate(blueprint, guideline, options) -> TaskInstanceDraft[]
```

Вход:

- blueprint;
- guideline;
- тема;
- difficulty;
- количество;
- список запрещённых повторов;
- дополнительные параметры.

Выход:

- структурированные drafts;
- metadata;
- provider usage;
- validation status.

---

### 11.2. Режимы генерации

- одиночная runtime-генерация;
- пакетная генерация в банк;
- генерация по слабой теме;
- генерация полного mock;
- ручной импорт.

Основной экономичный режим: пакетная генерация и повторное использование банка заданий.

---

### 11.3. Validation pipeline

После LLM:

1. JSON Schema validation;
2. проверка обязательных полей;
3. проверка score limits;
4. проверка наличия solution;
5. проверка совместимости с blueprint;
6. поиск точных дублей;
7. similarity check;
8. статус `generated` или `rejected`.

---

## 12. TaskInstance

Конкретное готовое задание.

Поля:

- `id`;
- `blueprint_id`;
- `guideline_id`;
- `guideline_version`;
- `generator_prompt_id`;
- `generator_prompt_version`;
- `generator_model`;
- `difficulty`;
- `title`;
- `content`;
- `content_points`;
- `answer_config`;
- `solution`;
- `explanation`;
- `hints`;
- `max_score`;
- `recommended_minutes`;
- `status`;
- `checksum`;
- `created_at`.

Статусы:

- `draft`;
- `generated`;
- `reviewed`;
- `active`;
- `disabled`;
- `rejected`.

---

## 13. TaskMedia

Поля:

- `id`;
- `task_id`;
- `kind`;
- `storage_key`;
- `public_or_signed_url`;
- `mime_type`;
- `size_bytes`;
- `duration_seconds`, nullable;
- `width`, nullable;
- `height`, nullable;
- `position`;
- `metadata`.

Типы:

- image;
- audio;
- video;
- document;
- chart;
- table.

---

## 14. Тренировочные сессии

### 14.1. TrainingSession

Поля:

- `id`;
- `user_id`;
- `subject_id`;
- `exam_profile_id`;
- `skill_id`, nullable;
- `task_family_id`, nullable;
- `mode`;
- `status`;
- `started_at`;
- `submitted_at`;
- `completed_at`;
- `expires_at`;
- `score_earned`;
- `score_max`;
- `duration_seconds`;
- `metadata`.

Режимы:

- `single`;
- `skill`;
- `topic`;
- `weakness`;
- `mock`;
- `review_errors`;
- `random`.

Статусы:

- `created`;
- `started`;
- `in_progress`;
- `submitted`;
- `evaluating`;
- `completed`;
- `cancelled`;
- `expired`.

---

### 14.2. SessionTask

Поля:

- `id`;
- `session_id`;
- `task_id`;
- `position`;
- `started_at`;
- `submitted_at`;
- `status`.

Backend является источником истины по времени.

---

## 15. Attempts

### 15.1. Attempt

Поля:

- `id`;
- `user_id`;
- `session_id`;
- `task_id`;
- `raw_answer`;
- `normalized_answer`;
- `word_count`, nullable;
- `started_at`;
- `submitted_at`;
- `duration_seconds`;
- `status`;
- `evaluator_code`;
- `evaluation_profile_id`;
- `score_raw`;
- `penalty_total`;
- `score_final`;
- `score_max`;
- `idempotency_key`;
- `created_at`.

Статусы:

- `pending`;
- `evaluating`;
- `evaluated`;
- `failed`;
- `manual_review`.

---

## 16. Evaluation Router

```text
evaluate(task, attempt) -> EvaluationResult
```

Router выбирает evaluator из TaskFamily/EvaluationProfile.

Поддерживаемые evaluator:

- `ExactMatchEvaluator`;
- `AcceptedAnswersEvaluator`;
- `MultipleChoiceEvaluator`;
- `MatchingEvaluator`;
- `NumericEvaluator`;
- `SymbolicEvaluator`;
- `KeywordRubricEvaluator`;
- `LanguageRuleEvaluator`;
- `LLMWritingEvaluator`;
- `HybridEvaluator`.

Правила:

- multiple choice, true/false, matching и numeric не используют LLM;
- writing всегда использует LLM;
- sentence transformation использует rule-based проверку и LLM только при низкой уверенности;
- штрафы и dependency rules применяются backend-кодом после LLM.

---

## 17. EvaluationResult

Поля:

- `id`;
- `attempt_id`;
- `status`;
- `raw_score`;
- `penalty_total`;
- `final_score`;
- `max_score`;
- `summary`;
- `strengths`;
- `recommendations`;
- `confidence`;
- `raw_provider_response`;
- `provider_metadata`;
- `created_at`.

---

### 17.1. CriterionScore

Поля:

- `evaluation_result_id`;
- `criterion_code`;
- `score`;
- `max_score`;
- `selected_band`;
- `explanation`;
- `evidence`.

---

### 17.2. ContentPointAssessment

Поля:

- `evaluation_result_id`;
- `content_point_id`;
- `status`;
- `evidence`;
- `comment`.

Статусы:

- `missing`;
- `mentioned`;
- `partly_developed`;
- `developed`;
- `well_developed`.

---

### 17.3. ErrorEvent

Поля:

- `id`;
- `attempt_id`;
- `evaluation_result_id`;
- `category`;
- `subcategory`;
- `severity`;
- `source_fragment`;
- `corrected_fragment`;
- `explanation`;
- `criterion_code`;
- `content_point_id`, nullable;
- `start_offset`, nullable;
- `end_offset`, nullable;
- `tags`.

---

## 18. Writing engine

Подробные требования находятся в `WRITING_ENGINE_ENGLISH_EXAMPLE.md`.

Backend обязан:

1. выполнить deterministic pre-check;
2. вызвать LLM с TaskInstance, rubric и response schema;
3. валидировать результат;
4. применить PenaltyRule;
5. применить DependencyRule;
6. рассчитать final score;
7. сохранить criteria, content points и errors;
8. обновить статистику.

LLM не должна самостоятельно рассчитывать окончательные штрафы.

---

## 19. LLM Provider Layer

### 19.1. Interface

```text
generate_structured(
  purpose,
  prompt_template,
  variables,
  output_schema,
  provider_policy
) -> StructuredLLMResult
```

### 19.2. Требования

- минимум два заменяемых provider adapter;
- structured outputs;
- timeout;
- retry;
- fallback;
- model routing;
- token usage;
- estimated cost;
- latency;
- request/response logging с редактированием чувствительных данных;
- prompt caching, когда provider поддерживает.

### 19.3. Retry policy

- network/5xx: exponential backoff;
- schema violation: один повтор с deterministic repair instruction;
- timeout: fallback provider;
- content refusal: статус `manual_review`;
- повторная отправка с тем же idempotency key не создаёт второй вызов.

### 19.4. LLMCall

Хранить:

- provider;
- model;
- purpose;
- prompt template/version;
- output schema/version;
- input tokens;
- output tokens;
- cached tokens;
- estimated cost;
- latency;
- status;
- error code;
- request checksum;
- raw response.

---

## 20. Статистика

Статистика должна быть generic и агрегировать динамические criterion codes.

### 20.1. Overview

- количество сессий;
- количество заданий;
- total study time;
- средний процент;
- результаты по Subject/ExamProfile/Skill;
- последние mock results;
- streak, optional.

### 20.2. Criterion trends

- среднее значение по каждому criterion_code;
- изменение по периодам;
- количество оценённых текстов;
- confidence.

### 20.3. Error trends

- частота категорий;
- повторяемость;
- последняя дата;
- доля исправленных повторных ошибок;
- слабые темы.

### 20.4. Weakness score

Формула должна учитывать:

- accuracy;
- severity;
- recency;
- repetition;
- task difficulty.

Формула хранится как versioned policy.

---

## 21. Словарный модуль

### 21.1. Назначение

Поиск немецких и английских слов с переводом на русский без LLM.

### 21.2. Provider strategy

1. **PONS API** — основной источник DE/EN → RU.
2. **Free Dictionary API** — enrichment для английского: definition, pronunciation, audio, senses.
3. **Yandex Dictionary** — optional fallback под feature flag.
4. **Wiktionary/Wikimedia** — optional fallback, если будет реализован parser.
5. **LanguageTool** — не словарь; может использоваться для spelling/lemma assistance.

### 21.3. DictionaryProvider interface

```text
lookup(word, source_lang, target_lang) -> ProviderDictionaryResult
```

### 21.4. Merge policy

- canonical translation: PONS;
- English definition/audio: Free Dictionary;
- убрать дубли;
- сохранить источник каждого поля;
- не смешивать части речи без группировки;
- stale cache лучше полного отказа.

### 21.5. DictionaryEntry

Поля:

- `id`;
- `source_language`;
- `target_language`;
- `original_query`;
- `normalized_word`;
- `lemma`;
- `part_of_speech`;
- `translations`;
- `definitions`;
- `examples`;
- `phonetics`;
- `audio_urls`;
- `forms`;
- `synonyms`;
- `provider_sources`;
- `raw_provider_responses`;
- `fetched_at`;
- `expires_at`.

Cache key:

```text
source_language:target_language:normalized_word
```

PONS free quota должна контролироваться метрикой и кешем.

---

## 22. Личный словарь и флэшкарточки

### 22.1. UserWord

Поля:

- `id`;
- `user_id`;
- `dictionary_entry_id`;
- `knowledge_level`;
- `source`;
- `notes`;
- `created_at`;
- `archived_at`.

Уровни:

- `new`;
- `learning`;
- `known`.

### 22.2. FlashcardReview

Поля:

- `id`;
- `user_word_id`;
- `grade`;
- `reviewed_at`;
- `next_review_at`;
- `interval_days`;
- `algorithm_version`.

Оценки:

- `no`;
- `maybe`;
- `yes`.

Алгоритм повторения должен быть отдельной стратегией.

---

## 23. Пользователи и доступ

### 23.1. User

Поля:

- `id`;
- `telegram_id`;
- `username`;
- `display_name`;
- `interface_language`;
- `status`;
- `created_at`;
- `last_seen_at`.

Статусы:

- `active`;
- `blocked`;
- `inactive`.

### 23.2. Private access

- публичной регистрации нет;
- пользователь заранее создаётся администратором;
- Telegram ID должен находиться в allowlist;
- бот обращается к backend с service token;
- Telegram ID передаётся отдельным заголовком или подписанным auth context;
- backend не доверяет произвольному `telegram_id` без service authentication.

---

## 24. API convention

Base URL:

```text
/api/v1
```

Формат успеха:

```json
{
  "data": {},
  "meta": {
    "request_id": "..."
  },
  "errors": []
}
```

Формат ошибки:

```json
{
  "data": null,
  "meta": {
    "request_id": "..."
  },
  "errors": [
    {
      "code": "SESSION_INVALID_STATE",
      "message": "Session cannot be submitted from the current state.",
      "details": {}
    }
  ]
}
```

---

## 25. Public bot-facing endpoints

### Access

- `GET /access/me`

### Catalog

- `GET /subjects`
- `GET /subjects/{subject_code}/exams`
- `GET /exam-profiles/{exam_code}/skills`
- `GET /skills/{skill_id}/task-families`
- `GET /task-families/{id}/blueprints`

### Sessions

- `POST /sessions`
- `GET /sessions/{id}`
- `POST /sessions/{id}/start`
- `POST /sessions/{id}/cancel`
- `GET /sessions/{id}/next-task`
- `POST /sessions/{id}/submit`
- `GET /sessions/{id}/result`
- `GET /sessions/history`

### Attempts

- `POST /attempts`
- `GET /attempts/{id}`
- `POST /attempts/{id}/evaluate`
- `GET /attempts/{id}/result`

### Statistics

- `GET /statistics/overview`
- `GET /statistics/criteria`
- `GET /statistics/errors`
- `GET /statistics/weaknesses`

### Dictionary

- `GET /dictionary/lookup`
- `POST /user-words`
- `GET /user-words`
- `PATCH /user-words/{id}`
- `DELETE /user-words/{id}`

### Flashcards

- `GET /flashcards/next`
- `POST /flashcards/{user_word_id}/review`
- `GET /flashcards/stats`

### Privacy

- `GET /privacy/export`
- `DELETE /privacy/me/data`

---

## 26. Admin endpoints

### Access

- `POST /admin/users`
- `PATCH /admin/users/{id}`
- `GET /admin/users`

### Academic catalog

- CRUD `/admin/subjects`
- CRUD `/admin/exam-profiles`
- CRUD `/admin/skills`
- CRUD `/admin/task-families`
- CRUD `/admin/task-blueprints`

### Configuration

- CRUD `/admin/guidelines`
- CRUD `/admin/rubrics`
- CRUD `/admin/evaluation-profiles`
- CRUD `/admin/prompts`
- CRUD `/admin/output-schemas`
- CRUD `/admin/error-taxonomies`

### Tasks

- `POST /admin/tasks/batch-generate`
- `GET /admin/tasks`
- `PATCH /admin/tasks/{id}`
- `POST /admin/tasks/{id}/activate`
- `POST /admin/tasks/{id}/reject`

### Attempts

- `GET /admin/attempts`
- `PATCH /admin/attempts/{id}/score`
- `PATCH /admin/attempts/{id}/feedback`

### Observability

- `GET /admin/llm-calls`
- `GET /admin/provider-calls`
- `GET /admin/audit-logs`

---

## 27. Создание session

`POST /sessions`

Пример request:

```json
{
  "subject_code": "english",
  "exam_profile_code": "epe_b1_plus",
  "skill_code": "writing",
  "task_family_code": "blog_comment",
  "mode": "single",
  "options": {
    "difficulty": "b1_plus",
    "prefer_new_task": true
  }
}
```

Response должен содержать:

- session;
- первый TaskInstance;
- ожидаемый answer format;
- recommended time;
- available actions.

---

## 28. Отправка writing attempt

`POST /attempts`

```json
{
  "session_id": "...",
  "task_id": "...",
  "answer": {
    "type": "text",
    "text": "..."
  }
}
```

Response:

- `200` при синхронной локальной проверке;
- `202` при LLM-evaluation;
- attempt ID;
- evaluation status;
- poll URL или result endpoint.

---

## 29. Semantic response blocks

Backend может дополнительно возвращать client-neutral semantic blocks.

Допустимые типы:

- `heading`;
- `paragraph`;
- `score_table`;
- `criteria_table`;
- `content_point_list`;
- `error_list`;
- `correction_list`;
- `recommendation_list`;
- `details`;
- `quote`;
- `formula`;
- `media`;
- `status`.

Это не Telegram HTML. Клиент сам выбирает renderer.

---

## 30. Идемпотентность и concurrency

Для write-endpoints использовать `Idempotency-Key`.

Требования:

- повторный запрос с тем же key и payload возвращает прежний результат;
- тот же key с другим payload возвращает `IDEMPOTENCY_CONFLICT`;
- одна активная evaluation на attempt;
- один активный attempt на session task;
- session finalization выполняется транзакционно.

---

## 31. Background jobs

Фоновые операции:

- writing evaluation;
- batch generation;
- provider retry;
- dictionary cache refresh;
- statistics aggregation;
- task deduplication;
- cleanup expired sessions;
- data export;
- account deletion.

Требования:

- retry with backoff;
- deduplication;
- dead-letter state;
- observable job status;
- safe re-execution.

---

## 32. Коды ошибок

Минимум:

- `ACCESS_DENIED`;
- `USER_BLOCKED`;
- `SUBJECT_NOT_FOUND`;
- `EXAM_PROFILE_NOT_FOUND`;
- `BLUEPRINT_NOT_FOUND`;
- `TASK_NOT_FOUND`;
- `SESSION_NOT_FOUND`;
- `SESSION_INVALID_STATE`;
- `SESSION_EXPIRED`;
- `INVALID_ANSWER_FORMAT`;
- `ATTEMPT_DUPLICATE`;
- `EVALUATION_IN_PROGRESS`;
- `EVALUATION_FAILED`;
- `LLM_UNAVAILABLE`;
- `LLM_SCHEMA_INVALID`;
- `DICTIONARY_WORD_NOT_FOUND`;
- `DICTIONARY_PROVIDER_ERROR`;
- `PROVIDER_QUOTA_EXCEEDED`;
- `IDEMPOTENCY_CONFLICT`;
- `VALIDATION_ERROR`.

---

## 33. Security

- HTTPS only;
- service-to-service token;
- отдельный admin credential;
- Telegram allowlist;
- rate limiting;
- request size limits;
- file MIME validation;
- secrets только в environment/secret storage;
- no stack traces в production;
- prompt injection defence: пользовательский текст всегда помещается в отдельное поле, а не склеивается с system rules;
- LLM не получает секреты и лишние пользовательские данные;
- audit log для admin mutations.

---

## 34. Privacy

Даже для private beta:

- data minimisation;
- экспорт пользовательских данных;
- удаление аккаунта и истории;
- ограничение срока хранения raw LLM payloads;
- чувствительные тексты не дублируются в обычных логах;
- настройки retention должны быть конфигурируемыми.

---

## 35. Logging и monitoring

### Логи

- request ID;
- user ID без лишних PII;
- endpoint;
- duration;
- status;
- evaluator;
- provider;
- job ID;
- error code.

### Метрики

- API p50/p95;
- session completion rate;
- evaluation latency;
- evaluation failure rate;
- schema violation rate;
- LLM tokens/cost/cache;
- PONS quota usage;
- dictionary cache hit ratio;
- background queue depth;
- error frequency.

### Health endpoints

- `/health/live`;
- `/health/ready`;
- `/health/providers`, admin-only.

---

## 36. Тестирование

### Unit

- evaluator strategies;
- penalty rules;
- dependency rules;
- word counting;
- session transitions;
- weakness score;
- dictionary merge;
- flashcard scheduling.

### Integration

- session lifecycle;
- attempt submission;
- async evaluation;
- provider fallback;
- idempotency;
- admin correction;
- data deletion.

### Contract

- OpenAPI validation;
- LLM output schema;
- PONS adapter;
- Free Dictionary adapter;
- Telegram-facing response examples.

### Golden dataset

Создать набор работ с ручными оценками преподавателя для calibration writing engine.

---

## 37. Seed data

Минимальные seeds:

- private admin;
- private test user;
- English subject;
- EPE B1+ exam profile;
- Writing skill;
- Blog Comment task family;
- English writing blueprint;
- English rubric;
- evaluation profile;
- sample guideline;
- sample prompt;
- несколько tasks.

---

## 38. Deliverables

- исходный код;
- OpenAPI spec;
- DB migrations;
- seed command;
- sample `.env`;
- Docker configuration;
- admin instructions;
- guideline loader;
- provider adapters;
- tests;
- backup/restore guide;
- architecture diagram;
- API examples;
- changelog.

---

## 39. Acceptance criteria MVP

1. Неавторизованный Telegram ID не получает данные.
2. Пользователь может выбрать предмет, экзамен, skill и task family.
3. Backend создаёт writing session и возвращает задание.
4. Пользователь отправляет текст.
5. Writing engine возвращает структурированную оценку.
6. Backend применяет rubric penalties и dependency rules.
7. Результат сохраняется и отображается в истории.
8. Criterion trends и error trends обновляются.
9. Dictionary lookup DE/EN → RU работает через cache + provider.
10. Повторный idempotent request не создаёт дублей.
11. OpenAPI полностью описывает bot-facing endpoints.
12. Все core flows покрыты автоматическими тестами.

---

## 40. Официальные источники для интеграций

- OpenAI Structured Outputs:  
  https://developers.openai.com/api/docs/guides/structured-outputs
- OpenAI Prompt Caching:  
  https://developers.openai.com/api/docs/guides/prompt-caching
- Gemini Structured Outputs:  
  https://ai.google.dev/gemini-api/docs/structured-output
- Gemini Context Caching:  
  https://ai.google.dev/gemini-api/docs/caching
- PONS API documentation:  
  https://en.pons.com/assets/docs/api_dict.pdf
- PONS API terms/free quota:  
  https://de.pons.com/p/agb-api
- Free Dictionary API:  
  https://freedictionaryapi.com/
- LanguageTool public API limitations:  
  https://dev.languagetool.org/public-http-api.html
