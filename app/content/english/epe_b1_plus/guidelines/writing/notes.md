<!--
Project: VWU EPE Telegram Study Bot
Language: English
Purpose: AI guideline draft for task generation/evaluation, not backend code.
Source basis: user-provided EPE sample exam PDF, EPE sample key PDF, user-provided writing rubric photos, and user-confirmed real-exam notes.
Important: Use these files as prompt/context guidelines. Do not copy official sample texts verbatim into generated tasks.
-->

# English EPE Writing — Notes

## 1. Practical exam notes

The writing task is very important because it cannot be evaluated only with exact answer keys. The bot must use LLM evaluation for writing, but the scoring rules must be deterministic where possible.

## 2. Text type

Current observed text type:

- blog comment / social media comment

Expected tone:

- semi-informal;
- personal;
- interactive;
- clear but not academic C1;
- more developed than A2.

## 3. Typical student traps

- forgetting to refer to the source post;
- writing a general essay instead of a blog comment;
- missing interactive elements;
- not addressing one content point;
- giving too little supporting detail;
- writing under 225 words;
- overusing simple phrases;
- repeating `I think` too often;
- weak connectors;
- serious article/preposition/word order mistakes;
- copying phrases from the prompt;
- missing final reader question.

## 4. Preferred structure for students

Recommended paragraph structure:

1. Greeting and reference to post.
2. Short comment on writer's issue/attitude.
3. First developed argument.
4. Second developed argument.
5. Suggestion/recommendation.
6. Closing interactive question.

## 5. Useful interactive elements

- `Hi [name],`
- `I can understand your point, but ...`
- `What do you think?`
- `Have you ever noticed this too?`
- `In my experience, ...`
- `Maybe the best solution is ...`
- `Do you guys agree?`

## 6. Calibration

For production-quality feedback, store real checked writings with:

- task prompt;
- student answer;
- teacher TORA scores;
- teacher annotations;
- AI score;
- score difference;
- prompt version;
- model version.

Do not trust the LLM blindly. It will look confident even when it grades like a sleepy substitute teacher.
