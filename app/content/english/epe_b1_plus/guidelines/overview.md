<!--
Project: VWU EPE Telegram Study Bot
Language: English
Purpose: AI guideline draft for task generation/evaluation, not backend code.
Source basis: user-provided EPE sample exam PDF, EPE sample key PDF, user-provided writing rubric photos, and user-confirmed real-exam notes.
Important: Use these files as prompt/context guidelines. Do not copy official sample texts verbatim into generated tasks.
-->

# English EPE — Overall Guideline for VWU Bot

## 1. Exam structure

The written English supplementary examination contains three written parts:

1. Reading Comprehension (RC)
2. Language in Use (LIU)
3. Text Production (TP)

Each part is worth **20 points**, total **60 points**.

For a positive written result:

- at least **9/20** in each of the three parts;
- at least **36/60** total.

Working time:

- **150 minutes total**;
- Reading Comprehension: **50 minutes**;
- Language in Use + Text Production: **100 minutes combined**.

Dictionaries are not allowed.

## 2. Bot content structure

```text
content_drafts/
  english/
    overview.md
    writing/
      generation.md
      evaluation.md
      examples.md
      notes.md
    grammar/
      generation.md
      evaluation.md
      examples.md
      notes.md
    reading/
      generation.md
      evaluation.md
      examples.md
      notes.md
```

## 3. AI usage policy

| Section | Generate with AI | Evaluate with AI | Notes |
|---|---:|---:|---|
| Writing | Yes | Yes | Rubric-driven LLM evaluation required |
| Grammar / LIU | Yes | Usually no | Evaluate with answer keys |
| Reading | Yes | Usually no | Evaluate with answer keys and evidence |

## 4. MVP priority

1. Writing evaluation.
2. Grammar generation/evaluation/examples.
3. Reading generation/evaluation/examples.
4. Writing generation.
5. Notes and calibration datasets.

## 5. Do not copy official samples

Use official sample materials to understand formats and scoring rules. Generated tasks must be original.
