<!--
Project: VWU EPE Telegram Study Bot
Language: English
Purpose: AI guideline draft for task generation/evaluation, not backend code.
Source basis: user-provided EPE sample exam PDF, EPE sample key PDF, user-provided writing rubric photos, and user-confirmed real-exam notes.
Important: Use these files as prompt/context guidelines. Do not copy official sample texts verbatim into generated tasks.
-->

# English EPE Grammar / Language in Use — Evaluation Guideline

## 1. Purpose

This file defines how to evaluate English EPE Language in Use answers.

Most grammar/LIU tasks should be evaluated **without LLM** using answer keys, accepted alternatives, and deterministic normalisation. LLM may be used only for review of ambiguous open answers, not for standard scoring.

## 2. General scoring principles

- Score each item independently.
- Use exact answer keys for objective tasks.
- Use accepted alternatives where provided.
- Do not penalise irrelevant capitalization unless the task specifically requires it.
- Do penalise spelling if the word is incorrect.
- Do not award points for answers that change the required grammar meaning.
- Do not use partial credit unless the task configuration explicitly allows it.

## 3. Normalisation rules

Before comparing answers:

1. Trim spaces.
2. Convert smart quotes/apostrophes to normal forms where relevant.
3. Normalize Unicode.
4. Collapse multiple spaces.
5. For multiple-choice letters, uppercase input.
6. For text answers, keep original for feedback but compare normalized form.

Do not remove apostrophes from contractions if the answer itself is a contraction.

## 4. Cloze: missing letters

### Evaluation

- The student's completed word must match the answer key.
- If the task asks for missing letters only, support both modes depending on frontend:
  - student submits full word;
  - student submits only missing letters.
- The backend should store which mode is expected.

### Scoring

- Correct word/letters: full item points.
- Incorrect spelling: 0.
- Different grammatical form: 0.
- Extra spaces: ignore.
- Capitalization: ignore unless proper noun.

### Feedback

Return:

- correct answer;
- student's answer;
- short explanation;
- grammar/vocabulary tag.

## 5. Multiple choice LIU

### Evaluation

- Compare selected option letter with correct option letter.
- If frontend sends option text, map it to option ID before scoring.

### Scoring

- Correct option: full item points.
- Wrong option: 0.
- Multiple selected options when one is required: 0.
- Empty answer: 0.

### Feedback

For each wrong answer, return:

- correct option;
- short explanation;
- distractor reason if available.

## 6. Full-word gap / open gap fill

### Evaluation

- Compare normalized answer against `accepted_answers`.
- Some gaps may have multiple valid answers.
- If the answer is semantically possible but not listed, mark as `needs_review` only if the task allows review.

### Scoring

- Accepted answer: full item points.
- Unlisted answer: 0 or review depending on configuration.
- Wrong form: 0.
- Wrong spelling: 0.

### Accepted alternatives

Example from official key style:

```json
{
  "gap": 7,
  "accepted_answers": ["like", "need", "want", "wish"]
}
```

Store all known variants.

## 7. Word formation

### Evaluation

- Answer must match target derived form.
- Plural/singular must match context.
- Verb tense/form must match context.

### Scoring

- Correct derived word: full points.
- Correct root but wrong form: 0.
- Wrong spelling: 0.
- Different word family: 0.

Potential accepted variants are allowed only if explicitly configured.

## 8. Editing

### Evaluation

For each numbered line:

- If line is correct, expected answer is `✓` or equivalent.
- If line contains an extra word, expected answer is that word.

Acceptable checkmark variants:

- `✓`
- `✔`
- `correct`
- `ok`
- empty only if frontend has explicit correct-line option.

### Scoring

- Correct extra word: full item points.
- Correct-line mark for a correct line: full points.
- Wrong word: 0.
- Multiple words when only one is expected: 0.
- Marking incorrect line as correct: 0.

## 9. Multiple matching LIU

### Evaluation

- Compare selected option letter with answer key.
- Each option can usually be used once unless task config says otherwise.
- Extra options must remain unused.

### Scoring

- Correct letter: full item points.
- Wrong letter: 0.
- Duplicate option usage: evaluate per task config; usually duplicate wrong if it violates one-use rule.

## 10. Partial credit

Default: **no partial credit** for LIU items.

Partial credit may be enabled only for custom generated tasks and must be explicit in item config.

Example:

```json
{
  "partial_credit": false
}
```

## 11. Result JSON

```json
{
  "section": "language_in_use",
  "task_type": "open_gap_fill",
  "score": 4,
  "max_score": 5,
  "items": [
    {
      "id": "g1",
      "student_answer": "out",
      "correct": true,
      "points_awarded": 0.5,
      "points_max": 0.5,
      "correct_answers": ["out"],
      "explanation": "The phrasal verb is 'carry out'."
    }
  ]
}
```

## 12. When to use LLM

Use LLM only if:

- the task is open gap fill;
- the student answer is not in accepted alternatives;
- the task config allows ambiguity review;
- deterministic evaluator returns `uncertain`.

Even then, LLM cannot directly award points without validation. It may only propose whether the alternative is acceptable.

## 13. Critical evaluation mistakes to avoid

- Do not accept a grammatically incorrect form just because it is close.
- Do not reject configured accepted alternatives.
- Do not use fuzzy matching for spelling unless explicitly enabled.
- Do not use LLM for simple multiple choice.
- Do not change the official answer key during evaluation.
