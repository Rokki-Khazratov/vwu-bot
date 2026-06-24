# Техническое задание: Telegram-бот учебного ассистента

**Статус:** Draft for implementation  
**Версия:** 1.0  
**Дата:** 2026-06-24  
**Зависимость:** backend должен соответствовать `BACKEND_TZ.md` и иметь готовую OpenAPI-схему.

---

## 1. Назначение

Telegram-бот является тонким клиентом Backend API.

Он отвечает за:

- Telegram UX;
- навигацию;
- FSM;
- кнопки;
- приём ответов;
- вызовы backend;
- отображение заданий;
- отображение feedback;
- Rich Messages;
- обработку ошибок.

Он не отвечает за:

- генерацию заданий;
- оценивание;
- prompts;
- rubrics;
- штрафы;
- статистические расчёты;
- словарные provider calls;
- хранение академической логики.

---

## 2. Scope

### В MVP

- private users;
- `/start`;
- главное меню;
- выбор предмета;
- выбор exam profile;
- выбор skill;
- выбор task family;
- создание session;
- вывод задания;
- таймер;
- отправка текста;
- ожидание LLM-evaluation;
- Rich Message feedback;
- статистика;
- история;
- словарь;
- личные слова;
- базовые flashcards;
- обработка backend errors.

### Не входит

- платежи;
- публичная регистрация;
- Mini App;
- групповые чаты;
- OCR рукописного текста;
- сложное редактирование текста внутри Telegram;
- собственная бизнес-логика.

---

## 3. Интеграция с backend

Base URL:

```text
BACKEND_BASE_URL/api/v1
```

Headers:

```text
Authorization: Bearer <BOT_SERVICE_TOKEN>
X-Telegram-User-Id: <telegram_user_id>
X-Request-Id: <uuid>
Idempotency-Key: <uuid>  # только write requests
```

Бот должен использовать сгенерированный или типизированный API client по OpenAPI.

---

## 4. Основные endpoints

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
- `DELETE /user-words/{id}`

### Flashcards

- `GET /flashcards/next`
- `POST /flashcards/{user_word_id}/review`
- `GET /flashcards/stats`

---

## 5. Команды

- `/start` — проверка доступа и главное меню;
- `/train` — начать тренировку;
- `/stats` — статистика;
- `/history` — история;
- `/word` — режим словаря;
- `/words` — личный словарь;
- `/review` — flashcards;
- `/cancel` — отменить текущий flow;
- `/help` — краткая справка.

Команды не должны быть единственным способом навигации. Основной UX — inline keyboards.

---

## 6. Главное меню

Кнопки:

- `🎯 Тренировка`
- `📊 Статистика`
- `📚 Словарь`
- `🗂 История`
- `🧠 Повторение слов`

После `/start`:

1. вызвать `/access/me`;
2. при `active` показать меню;
3. при denied показать закрытое сообщение;
4. при blocked показать сообщение о блокировке.

---

## 7. FSM

Минимальные состояния:

```text
IDLE

SELECT_SUBJECT
SELECT_EXAM_PROFILE
SELECT_SKILL
SELECT_TASK_FAMILY
SELECT_MODE
SESSION_CREATED
SESSION_ACTIVE
WAITING_TEXT_ANSWER
WAITING_SIMPLE_ANSWER
SUBMITTING
EVALUATING
RESULT_READY

DICTIONARY_WAITING_WORD
FLASHCARD_REVIEW

ERROR_RECOVERY
```

FSM хранит только UI-state и backend IDs.

Нельзя хранить в FSM:

- rubric;
- правильный ответ;
- score calculation;
- prompt;
- assessment rules.

---

## 8. Training flow

1. `Тренировка`;
2. `GET /subjects`;
3. выбрать subject;
4. `GET /subjects/{code}/exams`;
5. выбрать exam profile;
6. выбрать skill;
7. выбрать task family;
8. выбрать mode;
9. `POST /sessions`;
10. отрендерить TaskInstance;
11. `POST /sessions/{id}/start`;
12. принять ответ;
13. `POST /attempts`;
14. если `202`, перейти в `EVALUATING`;
15. polling или job-status updates;
16. получить result;
17. отрендерить feedback;
18. показать actions.

---

## 9. Callback data

Callback data должна быть короткой и versioned.

Формат:

```text
v1:<action>:<short_id>
```

Примеры:

```text
v1:subject:english
v1:exam:epe_b1
v1:skill:writing
v1:family:blog
v1:start_session:abc123
v1:cancel_session:abc123
v1:next_task:abc123
```

Для длинных payload использовать server-side callback registry.

---

## 10. Получение ответа

### Writing

- бот ожидает обычное текстовое сообщение;
- минимальная длина проверяется только для UX;
- backend выполняет официальную validation;
- Telegram entities не должны искажать raw text;
- сохраняется plain Unicode text.

### Simple answers

- inline keyboard;
- текст;
- numeric input;
- selected options.

### Фото рукописи

Не поддерживается в MVP. Бот сообщает, что нужен печатный текст.

---

## 11. Таймер

Backend является source of truth.

Бот:

- показывает recommended time;
- отправляет команду start;
- может показывать локальное elapsed time;
- не рассчитывает официальный duration;
- при reconnect получает время из backend.

---

## 12. Evaluation state

После writing submission:

1. отправить status message;
2. получить `attempt_id`;
3. обновлять status;
4. не принимать повторный ответ;
5. после результата заменить status финальным feedback;
6. при timeout предложить `Обновить статус`.

Нельзя показывать chain of thought модели.

---

## 13. Telegram Bot API Rich Messages

Использовать Bot API 10.1+.

Основные методы:

- `sendRichMessage`;
- `sendRichMessageDraft`;
- `editMessageText` с `rich_message`.

`InputRichMessage` должен содержать ровно одно поле:

- `html`; или
- `markdown`.

Для проекта предпочтителен **Rich HTML**, потому что он легче генерируется deterministic renderer-ом.

---

## 14. Официальные ограничения Rich Messages

Renderer обязан учитывать:

- до 32768 UTF-8 символов;
- до 500 blocks;
- до 16 уровней вложенности;
- до 50 media attachments;
- до 20 колонок таблицы;
- table cells содержат только inline formatting;
- media blocks используют HTTP/HTTPS URLs;
- formulas используют raw LaTeX;
- `<tg-thinking>` допустим только в draft;
- `sendRichMessageDraft` является временным preview на 30 секунд;
- после draft обязательно вызвать `sendRichMessage` для постоянного сообщения.

При превышении лимита разбивать output на несколько Rich Messages.

---

## 15. Renderer layer

Создать отдельный модуль:

```text
SemanticBlockRenderer
  ├── render_task
  ├── render_writing_feedback
  ├── render_statistics
  ├── render_dictionary
  ├── render_history
  └── render_error
```

Вход: client-neutral semantic blocks backend.

Выход:

```json
{
  "html": "...",
  "reply_markup": {}
}
```

---

## 16. Semantic block mapping

| Backend block | Telegram Rich HTML |
|---|---|
| `heading` | `<h1>`–`<h6>` |
| `paragraph` | `<p>` |
| `score_table` | `<table>` |
| `criteria_table` | `<table>` |
| `content_point_list` | `<ul>` / `<ol>` |
| `error_list` | nested `<ul>` |
| `quote` | `<blockquote>` |
| `details` | `<details><summary>` |
| `formula` | `<tg-math-block>` |
| inline formula | `$...$` or math inline entity |
| `media.image` | `<img src="https://...">` block |
| `media.audio` | `<audio src="https://...">` block |
| `status` | paragraph or draft `<tg-thinking>` |
| `divider` | `<hr>` |

---

## 17. Rendering TaskInstance

Writing task Rich Message:

1. heading: предмет + exam;
2. subheading: task family;
3. source post/context;
4. instruction;
5. content points;
6. word target;
7. recommended time;
8. optional media;
9. buttons.

Buttons:

- `▶️ Начать`
- `❌ Отмена`
- `💡 Подсказка`, только если backend разрешает.

---

## 18. Rendering writing feedback

Порядок:

1. heading;
2. final score;
3. score table;
4. penalty note;
5. content point assessment;
6. strengths;
7. errors by category;
8. corrected fragments;
9. recommendations;
10. actions.

Крупные секции ошибок и corrections помещать в `<details>`.

Пример структуры:

```html
<h1>Writing Result</h1>

<table>
  <tr><th>Criterion</th><th>Score</th></tr>
  <tr><td>Task Achievement</td><td>4/5</td></tr>
</table>

<details>
  <summary>Ошибки и исправления</summary>
  ...
</details>
```

---

## 19. Draft streaming

Использовать только для долгой writing evaluation.

Flow:

1. создать non-zero `draft_id`;
2. `sendRichMessageDraft`;
3. обновлять draft не чаще установленного throttle;
4. показывать короткие статусы:
   - `Проверяю структуру`;
   - `Сопоставляю с rubric`;
   - `Формирую feedback`;
5. не показывать внутренние рассуждения LLM;
6. вызвать `sendRichMessage` с final message;
7. draft не считать permanent history.

Если streaming недоступен, использовать обычное status message + edit.

---

## 20. Statistics rendering

`/stats`:

- период;
- number of sessions;
- study time;
- average score;
- критерии;
- слабые темы;
- частые ошибки.

Использовать:

- headings;
- table;
- ordered list;
- details для расширенной статистики.

Графики не обязательны в MVP.

---

## 21. Dictionary rendering

Пользователь может:

- вызвать `/word`;
- написать `word: Voraussetzung`;
- отправить отдельное слово в dictionary state.

Rich Message:

- lemma;
- part of speech;
- translation;
- forms;
- pronunciation;
- examples;
- synonyms;
- provider attribution;
- actions.

Buttons:

- `➕ Сохранить`
- `🧠 В повторение`
- `🔎 Новое слово`

---

## 22. Flashcards

Бот получает следующую карточку из backend.

UI:

- front side;
- `Показать ответ`;
- back side;
- buttons:
  - `❌ Не знаю`;
  - `🤔 Сомневаюсь`;
  - `✅ Знаю`.

Бот не рассчитывает next review date.

---

## 23. History

`/history`:

- список последних sessions;
- pagination;
- callback на session detail;
- score;
- date;
- duration;
- mode.

Session detail:

- task;
- answer;
- result;
- feedback;
- button `Повторить ошибки`.

---

## 24. Error handling

Mapping:

| Backend error | Bot reaction |
|---|---|
| `ACCESS_DENIED` | закрытое сообщение |
| `USER_BLOCKED` | доступ заблокирован |
| `SESSION_EXPIRED` | предложить начать заново |
| `SESSION_INVALID_STATE` | обновить state с backend |
| `LLM_UNAVAILABLE` | сохранить attempt, предложить обновить позже |
| `DICTIONARY_WORD_NOT_FOUND` | предложить исправить слово |
| `PROVIDER_QUOTA_EXCEEDED` | показать cached/fallback response |
| `VALIDATION_ERROR` | объяснить ожидаемый формат |
| unknown 5xx | request ID + повтор |

Пользователю не показывать stack trace и технические payloads.

---

## 25. Resilience

- HTTP timeout;
- retry только для safe requests;
- idempotency для write requests;
- circuit breaker optional;
- восстановление FSM по active session;
- duplicate Telegram updates игнорировать по update_id;
- callback query всегда acknowledge;
- при рестарте бот должен продолжить active session.

---

## 26. Библиотечная совместимость

Если выбранная Telegram library ещё не поддерживает Bot API 10.1:

- создать прямой HTTP adapter;
- не ждать обновления wrapper;
- сохранить общий TelegramClient interface;
- заменить adapter позже без изменения handlers.

---

## 27. Security

- Bot token только в secret storage;
- backend service token отдельно;
- webhook secret token;
- allowed updates;
- private chat only;
- no group processing;
- Telegram ID берётся только из Update;
- user input экранируется перед Rich HTML;
- запрет HTML injection;
- URLs из backend валидируются;
- callback ownership проверяется.

---

## 28. Logging

Логировать:

- update ID;
- Telegram user ID;
- handler;
- backend request ID;
- session ID;
- attempt ID;
- callback action;
- duration;
- error code.

Не логировать полный writing text в обычный application log.

---

## 29. Tests

### Unit

- callback parser;
- FSM transitions;
- HTML escaping;
- semantic renderer;
- rich message splitting;
- error mapping.

### Integration

- mocked backend;
- start flow;
- writing flow;
- evaluation polling;
- dictionary flow;
- flashcards;
- session recovery.

### Snapshot

- task Rich Message;
- writing feedback;
- statistics;
- dictionary entry;
- error message.

---

## 30. Acceptance criteria

1. Только allowlisted user получает меню.
2. Полный catalog flow работает без hardcoded subjects.
3. Writing session создаётся через backend.
4. Text answer отправляется один раз с idempotency key.
5. Evaluation status отображается без chain of thought.
6. Final result отображается Rich Message с таблицей и details.
7. Message splitter соблюдает Telegram limits.
8. Dictionary result отображается и сохраняется.
9. FSM восстанавливается после restart.
10. Bot не содержит scoring logic.
11. Все backend calls типизированы по OpenAPI.
12. Core renderer покрыт snapshot tests.

---

## 31. Официальная документация Telegram

- Telegram Bot API:  
  https://core.telegram.org/bots/api
- Rich Message Formatting Options:  
  https://core.telegram.org/bots/api#rich-message-formatting-options
- `sendRichMessage`:  
  https://core.telegram.org/bots/api#sendrichmessage
- `sendRichMessageDraft`:  
  https://core.telegram.org/bots/api#sendrichmessagedraft
- `InputRichMessage`:  
  https://core.telegram.org/bots/api#inputrichmessage
