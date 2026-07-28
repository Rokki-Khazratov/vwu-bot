<!--
Project: VWU EPE Telegram Study Bot
Language: English
Purpose: AI guideline draft for task generation/evaluation, not backend code.
Source basis: user-provided EPE sample exam PDF, EPE sample key PDF, user-provided writing rubric photos, and user-confirmed real-exam notes.
Important: Use these files as prompt/context guidelines. Do not copy official sample texts verbatim into generated tasks.
-->

# English EPE Reading — Notes

## 1. Practical target structure

User-confirmed reading structure for the bot:

1. True/False + justification — 5 points.
2. Matching with extra options/letters — 10 points.
3. Sentence insertion / matching sentences to text gaps — 5 points.

The official sample includes additional examples and different point values. Keep all point values configurable.

## 2. Main traps for students

- choosing T/F correctly but giving wrong first four words;
- giving a paraphrase instead of the first four words;
- ignoring `there are extra options`;
- using outside knowledge;
- matching a statement to a person because of general topic, not exact evidence;
- missing negative wording such as `not`, `never`, `doesn't`;
- confusing similar names or profiles;
- choosing an option that is grammatically possible but logically wrong.

## 3. Generation notes

For generated reading tasks, always store evidence.

For each item, store:

- correct answer;
- evidence sentence;
- explanation;
- item tag;
- difficulty;
- distractor rationale.

This makes feedback possible without sending everything to LLM every time.
