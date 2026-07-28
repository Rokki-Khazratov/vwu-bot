<!--
Project: VWU EPE Telegram Study Bot
Language: English
Purpose: AI guideline draft for task generation/evaluation, not backend code.
Source basis: user-provided EPE sample exam PDF, EPE sample key PDF, user-provided writing rubric photos, and user-confirmed real-exam notes.
Important: Use these files as prompt/context guidelines. Do not copy official sample texts verbatim into generated tasks.
-->

# English EPE Grammar / Language in Use — Task Generation Guideline

## 1. Purpose

This file defines how the AI should generate English EPE Language in Use tasks.

The official sample calls this section **Language in Use (LIU)**. The user's practical target structure is:

1. Cloze / missing letters — 10 points
2. Multiple choice word/grammar selection — 5 points
3. Full-word gap fill / word formation / open gap fill — 5 points

Total: **20 points**.

The official sample also contains additional task types such as editing and multiple matching. They should be supported as extension types, even if the MVP focuses on the three practical types.

## 2. Source confidence

| Rule | Status |
|---|---|
| LIU is worth 20 points | Official sample PDF |
| Sample contains word formation, multiple choice, editing, cloze, open gap fill, multiple matching | Official sample PDF / key |
| User-confirmed practical format: cloze 10 + multiple choice 5 + full-word gap 5 | User-confirmed |
| Answer keys are exact or variant-based | Official key |

## 3. Supported task types

### 3.1 Cloze: missing letters

The student sees a text with incomplete words. Each underscore represents one missing letter.

Example pattern:

```text
The company has announced a new initi_ _ _ _ _ (1).
```

Expected answer:

```text
initiative
```

Generation requirements:

- 10–20 gaps depending on exercise configuration;
- each gap must be a complete English word with missing internal or final letters;
- the visible letters must make the word recoverable from context;
- avoid obscure vocabulary;
- include answer key;
- one letter per underscore;
- do not create ambiguous words unless alternatives are explicitly listed.

### 3.2 Multiple choice LIU

The student chooses A/B/C/D or A/B/C depending on configuration.

The official sample uses A–D with 10 gaps worth 5 points. User notes mention a three-option version. The generator must support both, but the default backend profile can choose one.

Typical tested areas:

- relative pronouns;
- collocations;
- phrasal verbs;
- verb patterns;
- modal verbs;
- determiners;
- tense/aspect;
- idiomatic expressions;
- prepositions;
- word choice.

Each item must have exactly one best answer.

### 3.3 Full-word gap fill / open gap fill

The student writes one complete word per gap. No options are given.

Generation requirements:

- each gap requires exactly one word;
- answer must be inferable from grammar and context;
- acceptable alternatives may exist and must be stored;
- avoid gaps where many unrelated words fit;
- include answer key and accepted variants.

### 3.4 Word formation

The student receives a base word in brackets and must form the correct word.

Example:

```text
They provide ___ (condition) love.
```

Expected answer:

```text
unconditional
```

Generation requirements:

- base word must be given;
- target word must be a derived form;
- test prefixes, suffixes, noun/adjective/adverb/verb forms;
- context must clearly require one form.

### 3.5 Editing

The student sees numbered lines. In most lines, one extra word should not be there. Some lines are correct.

Generation requirements:

- 10 assessed lines;
- 2–4 lines correct;
- one extra word maximum per incorrect line;
- include checkmark answer for correct lines;
- extra word must create a clear grammar/collocation issue.

### 3.6 Multiple matching LIU

The student chooses the most appropriate word from a list, with extra options.

Generation requirements:

- 10 gaps;
- 14 options recommended;
- 4 extra words;
- options should include plausible distractors;
- each correct answer must fit grammatically and semantically.

## 4. Recommended MVP task composition

For the bot's first English LIU profile:

| Task type | Items | Points |
|---|---:|---:|
| Cloze missing letters | 10 or 20 | 10 |
| Multiple choice | 5 or 10 | 5 |
| Full-word gap / word formation | 5 or 10 | 5 |
| Total | configurable | 20 |

The exact number of items can vary as long as point mapping is explicit.

## 5. General generation rules

Generated LIU tasks must:

- be B1+ level;
- use coherent texts, not isolated random sentences unless task type requires it;
- include a clear title;
- avoid copyrighted source text;
- include answer key;
- include accepted alternatives where relevant;
- include item-level grammar tags;
- include item-level difficulty;
- include explanations for feedback;
- avoid trick questions with multiple equally correct answers;
- avoid highly specialised topics.

## 6. Output JSON structure

```json
{
  "section": "language_in_use",
  "task_type": "cloze_missing_letters",
  "title": "string",
  "level": "B1+",
  "instructions": "string",
  "text": "string with numbered gaps",
  "items": [
    {
      "id": "g1",
      "gap_number": 1,
      "prompt_fragment": "initi_____",
      "answer": "initiative",
      "accepted_answers": ["initiative"],
      "points": 1,
      "tags": ["vocabulary", "noun_suffix"],
      "explanation": "The sentence requires a noun meaning a new plan or action."
    }
  ],
  "total_points": 10,
  "source_notes": "original generated task"
}
```

## 7. Topic pool

Good LIU topics:

- education;
- internships and careers;
- Vienna/student life;
- sustainability;
- animals and society;
- sports;
- daily routines;
- technology;
- travel;
- culture;
- health habits;
- public transport;
- work experience.

Avoid:

- politics requiring exact facts;
- traumatic news;
- war;
- adult topics;
- very technical science;
- legal advice;
- medical claims.

## 8. Grammar topic tags

Use tags such as:

- `tenses`
- `passive`
- `conditionals`
- `relative_clauses`
- `articles`
- `prepositions`
- `word_order`
- `collocations`
- `phrasal_verbs`
- `word_formation`
- `prefixes`
- `suffixes`
- `modal_verbs`
- `gerund_infinitive`
- `pronouns`
- `linking_words`
- `quantifiers`
- `spelling`
- `lexical_choice`

## 9. Quality checklist

Before saving a generated grammar task:

- all gaps have answers;
- numbering is consistent;
- total points are correct;
- answer key is complete;
- alternatives are listed if needed;
- no item has two equally correct unlisted answers;
- explanations are short and useful;
- topic is safe and B1+;
- task type matches instructions.
