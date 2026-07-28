<!--
Project: VWU EPE Telegram Study Bot
Language: English
Purpose: AI guideline draft for task generation/evaluation, not backend code.
Source basis: user-provided EPE sample exam PDF, EPE sample key PDF, user-provided writing rubric photos, and user-confirmed real-exam notes.
Important: Use these files as prompt/context guidelines. Do not copy official sample texts verbatim into generated tasks.
-->

# English EPE Grammar / Language in Use — Examples

## 1. Purpose

This file provides examples of English EPE Language in Use task types and answer-key structures.

Long official texts are not copied here. The examples below are shortened or original reconstruction examples in the same format.

## 2. Official sample task types observed

The official sample includes:

1. Word formation task.
2. Multiple choice task.
3. Editing task.
4. Cloze task with missing letters.
5. Open gap fill task.
6. Multiple matching task.

The user-confirmed practical exam focus for MVP:

1. Cloze / missing letters — 10 points.
2. Multiple choice — 5 points.
3. Full-word gap / open gap fill / word formation — 5 points.

## 3. Example: word formation

### Task

Read the text. Use the word in brackets to form a word that fits the gap.

```text
Many students find online courses very ___ (use), but they also need good organisation.
```

### Answer key

```json
{
  "gap": 1,
  "answer": "useful",
  "accepted_answers": ["useful"],
  "tag": "word_formation_adjective_suffix",
  "explanation": "The sentence needs an adjective after 'find something'."
}
```

## 4. Example: multiple choice LIU

### Task

Choose the correct answer.

```text
Katy asked if I ___ be interested in having her at the hotel for an internship.

A should
B could
C will
D would
```

### Answer key

```json
{
  "gap": 1,
  "answer": "D",
  "answer_text": "would",
  "tag": "reported_speech_modal",
  "explanation": "Reported polite question: 'asked if I would be interested'."
}
```

## 5. Example: editing

### Task

In most lines there is one word that should not be there. Write the extra word. If the line is correct, write `✓`.

```text
1. This is the place I am calling at home.
2. Vienna is a city with many museums.
```

### Answer key

```json
[
  {
    "line": 1,
    "answer": "at",
    "explanation": "The phrase is 'call home', not 'call at home'."
  },
  {
    "line": 2,
    "answer": "✓",
    "explanation": "The line is correct."
  }
]
```

## 6. Example: cloze missing letters

### Task

Complete the words. One underscore represents one missing letter.

```text
The company announced a new initi_____ to improve sustainability.
```

### Answer key

```json
{
  "gap": 1,
  "answer": "initiative",
  "missing_letters": "ative",
  "accept_full_word": true,
  "accept_missing_letters_only": true,
  "tag": "vocabulary_noun"
}
```

## 7. Example: open gap fill

### Task

Write one word for each gap.

```text
Other duties are carried ___ away from the cameras.
```

### Answer key

```json
{
  "gap": 1,
  "accepted_answers": ["out"],
  "tag": "phrasal_verb",
  "explanation": "The correct phrasal verb is 'carry out'."
}
```

## 8. Example: multiple matching LIU

### Task

Choose the most appropriate word from the list. There are extra words.

```text
Each team tries to (0) ___ by throwing the ball through the basket.
```

Options:

```text
A catch on
B composed
C elevated
D gained
E govern
L score
```

### Answer key

```json
{
  "gap": 0,
  "answer": "L",
  "answer_text": "score",
  "tag": "verb_meaning"
}
```

## 9. Official key patterns

### LIU sample key summary

The official key demonstrates these answer-key styles:

- multiple choice: letters only;
- word formation: exact words, with some alternatives;
- editing: extra word or checkmark;
- cloze: complete words;
- open gap fill: exact word or listed alternatives;
- multiple matching: option letters.

Examples of accepted alternatives in open gap fill:

- `These/these`
- `on/about`
- `arrive/come`
- `like/need/want/wish`
- `takes/lasts/requires`

Therefore, the backend schema must support multiple accepted answers.
