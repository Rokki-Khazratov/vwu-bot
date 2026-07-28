<!--
Project: VWU EPE Telegram Study Bot
Language: English
Purpose: AI guideline draft for task generation/evaluation, not backend code.
Source basis: user-provided EPE sample exam PDF, EPE sample key PDF, user-provided writing rubric photos, and user-confirmed real-exam notes.
Important: Use these files as prompt/context guidelines. Do not copy official sample texts verbatim into generated tasks.
-->

# English EPE Reading — Evaluation Guideline

## 1. Purpose

This file defines how reading answers should be checked.

Most reading tasks must be evaluated without LLM. The answer key and evidence fields are sufficient.

## 2. General principles

- Use answer key first.
- Do not use outside knowledge.
- Do not let a plausible answer override the text.
- Score item-by-item.
- Support configurable point values.
- Use accepted alternatives only where explicitly stored.

## 3. True/False with justification

### Required answer parts

Each item requires:

1. T/F decision.
2. First four words of a supporting sentence.

### Scoring options

The backend should support configurable scoring. Recommended modes:

#### Strict mode

- T/F correct + first four words correct = full point.
- T/F correct but justification wrong/missing = 0.
- T/F wrong = 0.

#### Split mode

- T/F correct = 0.5.
- justification correct = 0.5.
- T/F wrong but evidence sentence supports the opposite = 0 or manual review depending on config.

For VWU-like exam simulation, strict mode is safer unless teacher confirms split scoring.

### Justification normalisation

Accept:

- exact first four words;
- same first four words with punctuation differences;
- case-insensitive match;
- minor quote mark differences.

Reject:

- wrong sentence;
- paraphrase instead of first four words;
- fewer/more words if strict exam mode requires exactly four;
- first four words from irrelevant sentence.

## 4. Multiple matching

### Evaluation

- Compare selected option/person/letter with key.
- One answer per item.
- If one option can be used multiple times, task config must specify it.

### Scoring

- correct match = full item points;
- wrong match = 0;
- empty = 0;
- multiple answers where one is required = 0.

## 5. Sentence insertion / text-gap matching

### Evaluation

- Compare selected option letter with key.
- Check one-use rule.
- Extra options must remain unused.

### Scoring

- correct option = full item points;
- wrong option = 0;
- duplicate use = wrong unless task config allows duplicates;
- empty = 0.

## 6. Multiple choice reading

### Evaluation

- Compare letter with key.
- Each question has one correct answer.

### Scoring

- correct = full item points;
- wrong = 0;
- multiple selected = 0;
- empty = 0.

## 7. Result JSON

```json
{
  "section": "reading",
  "task_type": "true_false_justification",
  "score": 4,
  "max_score": 5,
  "items": [
    {
      "id": "r1",
      "student_answer": {
        "tf": "T",
        "justification": "The idea grew out"
      },
      "correct": true,
      "points_awarded": 1,
      "points_max": 1,
      "correct_answer": {
        "tf": "T",
        "first_four_words": "The idea grew out"
      },
      "explanation": "The supporting sentence confirms the statement."
    }
  ]
}
```

## 8. When to use LLM

Reading evaluation should not normally use LLM.

Use LLM only for:

- optional explanation generation after scoring;
- checking if a student's justification is a valid alternative sentence not in the key;
- creating easier explanations for wrong answers.

LLM must not override the official answer key automatically.

## 9. Feedback rules

Feedback should show:

- correct/wrong status;
- correct answer;
- evidence location or first four words;
- short explanation;
- task type strategy tip.

For practice mode, feedback can be detailed. For exam simulation mode, feedback should appear only after the task is submitted.
