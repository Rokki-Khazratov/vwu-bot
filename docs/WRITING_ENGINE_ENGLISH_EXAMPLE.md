# Техническое задание: конфигурируемый Writing Engine

## Английский EPE B1+ Blog Comment как первый пример

**Статус:** Draft for implementation  
**Версия:** 1.0  
**Дата:** 2026-06-24  
**Связанный документ:** `BACKEND_TZ.md`

---

## 1. Назначение

Writing Engine генерирует и проверяет письменные задания разных экзаменов.

Английский EPE B1+ используется как первый concrete profile. Немецкий EPD может иметь:

- другой тип текста;
- другой уровень;
- другой max score;
- другие критерии;
- другие penalties;
- другой prompt;
- другой error taxonomy;
- graph/media input.

Никакие английские правила не должны быть hardcoded в core engine.

---

## 2. Масштабируемая модель

```text
Subject
  → ExamProfile
    → Skill
      → TaskFamily
        → TaskBlueprint
          → TaskInstance

Rubric
  → RubricCriterion
    → PerformanceBand
  → PenaltyRule
  → DependencyRule

EvaluationProfile
  → PromptTemplate
  → OutputSchema
  → ErrorTaxonomy
```

Для нового writing exam добавляются конфигурации. Core pipeline не переписывается.

---

## 3. Первый профиль

```yaml
subject: english
exam_profile: epe_b1_plus
skill: writing
task_family: blog_comment
blueprint: epe_b1_plus_blog_comment_v1
rubric: epe_b1_plus_writing_20_v1
evaluation_profile: epe_b1_plus_blog_eval_v1
max_score: 20
target_words: 250
```

Источник rubric: предоставленная пользователем фотография  
`B1+ VWU ASSESSMENT SCALE for the writing task (20 pts)`.

---

## 4. Формат задания: Blog Comment

TaskInstance должен содержать:

- автора исходного blog post;
- blog post body;
- коммуникативную дилемму;
- instruction;
- ровно три content points;
- требование выразить личную позицию;
- word target;
- recommended time;
- rubric version;
- optional topic tags.

Пример структуры:

```json
{
  "task_family": "blog_comment",
  "title": "Living with parents or moving out?",
  "source_post": {
    "author": "Jason",
    "body": "I am planning to study in Vienna..."
  },
  "instruction": "Write a blog comment responding to Jason.",
  "content_points": [
    {
      "id": "cp_1",
      "instruction": "Discuss one side of the dilemma.",
      "required": true
    },
    {
      "id": "cp_2",
      "instruction": "Discuss the alternative.",
      "required": true
    },
    {
      "id": "cp_3",
      "instruction": "Give a personal recommendation.",
      "required": true
    }
  ],
  "target_words": 250,
  "max_score": 20,
  "rubric_code": "epe_b1_plus_writing_20_v1"
}
```

---

## 5. Генерация задания

### 5.1. Generator input

- TaskBlueprint;
- Guideline;
- difficulty;
- topic pool;
- recent tasks;
- banned themes;
- JSON Schema.

### 5.2. Generator requirements

LLM должна:

- создать реалистичный B1+ blog post;
- сформулировать понятную дилемму;
- создать три различимых content points;
- не требовать специальных знаний;
- не использовать дискриминационные или чувствительные темы;
- не повторять недавние задачи;
- вернуть только structured output.

### 5.3. Generator output schema

```json
{
  "title": "string",
  "source_post": {
    "author": "string",
    "body": "string"
  },
  "instruction": "string",
  "content_points": [
    {
      "id": "cp_1",
      "instruction": "string",
      "required": true
    }
  ],
  "topic_tags": ["string"],
  "expected_register": "semi_informal",
  "target_words": 250
}
```

Validation:

- content points count = 3;
- unique IDs;
- required fields;
- target words соответствует blueprint;
- source post не содержит ответа;
- task соответствует blog comment.

---

## 6. English rubric

Общий максимум: **20**.

Четыре критерия по **0–5**:

1. `task_achievement`;
2. `organisation_coherence`;
3. `range_vocabulary_grammar`;
4. `accuracy_vocabulary_grammar`.

---

## 7. Criterion: Task Achievement

Проверяет:

- соблюдение типа `blog comment`;
- reference to source post;
- interactive elements;
- personal perspective;
- раскрытие трёх content points;
- supporting details;
- ясность и релевантность позиции.

### Band summaries

#### 5

- blog text type успешно применён;
- все три content points достаточно развиты;
- есть supporting details;
- позиция эффективная, релевантная и убедительная.

#### 4

- blog format ясно соблюдён;
- все content points развиты;
- есть supporting details;
- позиция ясная и релевантная.

#### 3

- требования в целом соблюдены;
- все три content points затронуты, но не все достаточно развиты, или полноценно развиты два;
- позиция понятна и связана с исходным post.

#### 2

- blog requirements соблюдены частично;
- раскрыты только два content points или поддержка недостаточно релевантна;
- позиция местами неубедительна, расплывчата или не по теме.

#### 1

- отсутствуют важные признаки blog comment;
- развит один или ни одного content point;
- позиция трудно понимается, слишком общая или нерелевантная;
- возможны обязательные format omissions.

#### 0

- работа не отвечает заданию;
- язык недостаточен для оценки;
- текст ниже hard minimum;
- handwriting illegible, если позднее появится OCR/manual upload.

---

## 8. Criterion: Organisation and Coherence

Проверяет:

- overall coherence;
- logical order;
- links between ideas and content points;
- paragraphs;
- linking devices;
- reference words;
- pronouns;
- readability.

### Band summaries

#### 5

- очень ясная общая coherence;
- успешные логические связи;
- уверенное использование linking/reference devices.

#### 4

- ясная coherence;
- идеи связаны;
- linking devices используются успешно.

#### 3

- достаточная coherence;
- попытки связать идеи заметны;
- некоторые переходы неясны;
- devices в целом понятны.

#### 2

- связи часто неясны;
- ограниченный набор devices;
- paraphrasing недостаточен;
- структура слабая.

#### 1

- идеи расположены почти случайно;
- мало или нет эффективных связей;
- paragraphing не работает.

#### 0

- текст не демонстрирует организации.

---

## 9. Criterion: Range — Vocabulary & Grammar

Проверяет:

- разнообразие vocabulary;
- разнообразие grammatical structures;
- способность выражать идеи;
- repetitions;
- awkward expressions;
- prompt lifting.

### Band summaries

#### 5

- очень хороший диапазон vocabulary и grammar;
- нет заметных ограничений выражения.

#### 4

- хороший диапазон;
- почти нет заметных ограничений.

#### 3

- достаточный диапазон;
- ограничения иногда заметны;
- возможны awkward expressions и repetitions.

#### 2

- недостаточный диапазон;
- язык слишком простой;
- много ограничений выражения.

#### 1

- очень примитивный язык;
- автор часто не способен ясно выразить мысль;
- много repetition и prompt lifting.

#### 0

- отсутствует оцениваемый lexical/structural range.

---

## 10. Criterion: Accuracy — Vocabulary & Grammar

Проверяет:

- grammar;
- basic vocabulary;
- spelling;
- punctuation;
- effect on communication;
- reader effort;
- interference from other languages.

### Band summaries

#### 5

- очень хороший контроль;
- ошибки не мешают пониманию.

#### 4

- хороший контроль;
- ошибки редко мешают коммуникации.

#### 3

- достаточный контроль;
- ошибки иногда мешают, особенно в сложных идеях.

#### 2

- серьёзные lapses;
- ошибки часто мешают;
- читатель регулярно вынужден восстанавливать смысл.

#### 1

- повторяющиеся ошибки вызывают misunderstanding или breakdown;
- reader repeatedly stops to re-read;
- заметна системная интерференция.

#### 0

- ошибки вызывают breakdown коммуникации на протяжении текста.

---

## 11. Word-count rules

Word count считается backend-кодом.

Contracted forms, например `don't`, `I'm`, считаются одним словом.

Нейтральный диапазон:

```text
225–275 words → no penalty
```

Penalty table по предоставленной rubric:

| Word count | Penalty |
|---:|---:|
| `>= 476` | `-3` |
| `376–475` | `-2` |
| `276–375` | `-1` |
| `225–275` | `0` |
| `210–224` | `-1` |
| `190–209` | `-2` |
| `170–189` | `-3` |
| `150–169` | `-4` |
| `130–149` | `-5` |
| `111–129` | `-6` |
| `< 110` | total score `0` |

Перед production данные должны быть вручную сверены с оригинальной rubric ещё раз.

---

## 12. Dependency rule

Обязательное правило rubric:

```text
If Task Achievement = 0,
all other criteria = 0.
```

Backend применяет это после LLM evaluation.

LLM не должна сама решать, применять ли dependency.

---

## 13. Pre-check pipeline

До LLM:

1. проверить, что текст не пустой;
2. Unicode normalization;
3. посчитать word count;
4. определить hard-zero conditions;
5. найти технические format markers, если они обязательны;
6. сформировать deterministic penalties;
7. сохранить pre-check result.

Pre-check не ставит основные rubric scores.

---

## 14. LLM evaluation input

Передавать:

- exact TaskInstance;
- source post;
- instruction;
- три content points;
- user text;
- rubric criteria;
- full band descriptors;
- output JSON Schema;
- language of feedback;
- explicit instruction not to invent penalties.

Не передавать:

- всю историю пользователя;
- нерелевантные старые работы;
- Telegram metadata;
- секреты;
- chain-of-thought request.

---

## 15. Evaluation order

LLM обязана выполнять оценку в логическом порядке:

1. определить text type compliance;
2. оценить каждый content point;
3. выбрать Task Achievement band;
4. оценить Organisation and Coherence;
5. оценить Range;
6. оценить Accuracy;
7. извлечь strengths;
8. извлечь error events;
9. сформировать corrections;
10. сформировать recommendations.

LLM возвращает результаты, но не скрытые внутренние рассуждения.

---

## 16. LLM output schema

```json
{
  "rubric_code": "epe_b1_plus_writing_20_v1",
  "criteria": [
    {
      "code": "task_achievement",
      "score": 4,
      "selected_band": 4,
      "explanation": "string",
      "evidence": ["short quote"]
    }
  ],
  "content_points": [
    {
      "id": "cp_1",
      "status": "developed",
      "evidence": "short quote",
      "comment": "string"
    }
  ],
  "strengths": ["string"],
  "errors": [
    {
      "category": "grammar",
      "subcategory": "verb_form",
      "severity": "major",
      "source_fragment": "string",
      "corrected_fragment": "string",
      "explanation": "string",
      "criterion_code": "accuracy_vocabulary_grammar"
    }
  ],
  "corrected_fragments": [
    {
      "before": "string",
      "after": "string",
      "reason": "string"
    }
  ],
  "recommendations": ["string"],
  "confidence": 0.0
}
```

Validation:

- ровно четыре criteria;
- score integer 0–5;
- unique criterion codes;
- ровно три content point assessments;
- quotes должны существовать в user text;
- confidence 0–1.

---

## 17. Backend post-processing

После LLM:

1. schema validation;
2. проверить criterion count;
3. проверить score ranges;
4. проверить evidence quotes;
5. применить DependencyRule;
6. применить word-count PenaltyRule;
7. вычислить raw total;
8. вычислить final total;
9. ограничить score диапазоном 0–20;
10. сохранить result;
11. обновить statistics;
12. создать semantic blocks для clients.

---

## 18. Final result model

```json
{
  "raw_score": 14,
  "penalties": [
    {
      "code": "word_count",
      "value": -1,
      "details": "280 words"
    }
  ],
  "final_score": 13,
  "max_score": 20,
  "criteria": [],
  "content_points": [],
  "strengths": [],
  "errors": [],
  "corrected_fragments": [],
  "recommendations": [],
  "confidence": 0.86
}
```

---

## 19. Error taxonomy for English profile

Минимальные категории:

- `task_type`;
- `content_point`;
- `argumentation`;
- `organisation`;
- `cohesion`;
- `grammar`;
- `word_order`;
- `verb_form`;
- `tense`;
- `article`;
- `preposition`;
- `vocabulary`;
- `collocation`;
- `spelling`;
- `punctuation`;
- `register`;
- `repetition`;
- `prompt_lifting`.

Severity:

- `minor`;
- `major`;
- `critical`.

---

## 20. Feedback language

В private MVP:

- объяснения на русском;
- original/corrected fragments на английском;
- официальные criterion names можно хранить на английском;
- frontend labels локализуются отдельно.

---

## 21. Reliability

### Настройки

- low temperature;
- structured outputs;
- fixed prompt version;
- fixed rubric version;
- static instructions в начале prompt для provider caching.

### Retry

- schema invalid: one retry;
- missing criterion: one repair retry;
- provider timeout: fallback;
- confidence ниже threshold: manual review или second evaluation;
- contradictory result: second deterministic pass.

---

## 22. Calibration

Создать golden dataset:

- original task;
- user writing;
- teacher score;
- teacher annotations;
- AI score;
- difference;
- prompt/model version.

Метрики:

- mean absolute score error;
- criterion-level error;
- over-scoring rate;
- under-scoring rate;
- error detection precision;
- consistency on repeated runs.

Целевой ориентир для beta:

- total score deviation обычно не больше 2 points;
- major rubric contradictions отсутствуют;
- JSON schema pass rate > 99%.

---

## 23. Human correction

Admin может:

- изменить criterion score;
- изменить final score;
- исправить error category;
- удалить false-positive;
- добавить teacher note.

Хранить:

- original AI result;
- corrected result;
- actor;
- timestamp;
- reason.

---

## 24. Statistics

Не хранить только `13/20`.

Агрегировать:

- Task Achievement trend;
- Organisation/Coherence trend;
- Range trend;
- Accuracy trend;
- content point completion;
- word-count discipline;
- error categories;
- time spent;
- repeated weaknesses.

---

## 25. Semantic feedback blocks

Writing Engine возвращает:

```text
heading
score_table
penalty_notice
criteria_details
content_point_list
strength_list
error_list
correction_list
recommendation_list
```

Telegram-бот преобразует их в Rich Messages.

---

## 26. German expansion

Для German EPD создать:

- новый ExamProfile;
- новый TaskFamily, например `graph_description`;
- новый TaskBlueprint;
- новый Rubric;
- новые criteria;
- новые band descriptors;
- новые penalties;
- новый DependencyRule set;
- новый EvaluationProfile;
- новый PromptTemplate;
- новый OutputSchema при необходимости;
- новую ErrorTaxonomy;
- graph media schema.

Core writing pipeline остаётся тем же.

Пример German TaskInstance может содержать:

```json
{
  "task_family": "graph_description",
  "chart_media": {},
  "instruction": "string",
  "required_aspects": [],
  "word_target": {},
  "rubric_code": "epd_writing_..."
}
```

English content points и English 0–20 scoring не должны применяться к German profile.

---

## 27. Acceptance criteria

1. Generator создаёт валидный B1+ blog comment task с тремя content points.
2. Task сохраняет blueprint/rubric/prompt versions.
3. User text проходит deterministic word count.
4. LLM возвращает четыре criterion scores 0–5.
5. Backend применяет word-count penalties.
6. Backend применяет `Task Achievement = 0 → all = 0`.
7. Final score всегда 0–20.
8. Content point assessment сохраняется отдельно.
9. Errors классифицируются structured taxonomy.
10. Повторная evaluation сохраняет model/prompt version.
11. Human correction не удаляет original result.
12. Новый German profile можно добавить без изменения core evaluator.

---

## 28. Implementation deliverables

- English TaskBlueprint;
- English Guideline;
- Rubric JSON/YAML;
- PerformanceBand data;
- PenaltyRule data;
- DependencyRule data;
- EvaluationProfile;
- generation prompt;
- evaluation prompt;
- output JSON Schema;
- error taxonomy;
- golden dataset fixture;
- unit tests;
- integration tests;
- sample result;
- admin calibration view or endpoints.
