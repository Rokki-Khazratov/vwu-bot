<!--
Project: VWU EPE Telegram Study Bot
Language: English
Purpose: AI guideline draft for task generation/evaluation, not backend code.
Source basis: user-provided EPE sample exam PDF, EPE sample key PDF, user-provided writing rubric photos, and user-confirmed real-exam notes.
Important: Use these files as prompt/context guidelines. Do not copy official sample texts verbatim into generated tasks.
-->

# English EPE Reading — Examples

## 1. Purpose

This file provides example structures for English EPE Reading tasks.

Official sample texts are not copied in full. The examples below are shortened or original reconstructions to keep the guideline useful without duplicating the entire sample exam.

## 2. Official sample task types observed

The official sample includes:

1. True/False/Justification.
2. Multiple matching with people/profiles.
3. Text-gap multiple matching with extra options.
4. Multiple choice reading.

The answer key shows exact answers for these formats.

## 3. Example: True/False/Justification

### Task

Read the text and decide if the statement is true or false. Then write the first four words of the sentence that supports your answer.

```text
Creative Job Speed Dating was created by two people from the creative industry.
```

### Answer key structure

```json
{
  "statement_id": "r1",
  "answer": "T",
  "evidence_sentence": "Creative Job Speed Dating is the brainchild of interior and set designer Rikki Wieland, and fashion and advertising photographer Michael Dürr.",
  "first_four_words": "Creative Job Speed Dating"
}
```

## 4. Example: multiple matching with profiles

### Task

Read three short profiles. Find out which person matches each statement.

```text
Find out which person...
1. found that spoken English was different from school English.
2. does not want to return to their country of birth.
3. misses family gatherings or food from their native culture.
```

### Answer key structure

```json
[
  {"item": 1, "answer": "Maika"},
  {"item": 2, "answer": "Mai Hua Ta"},
  {"item": 3, "answer": "Sayeed"}
]
```

## 5. Example: sentence insertion / text-gap matching

### Task

Read the article. Some parts are missing. Choose the best option for each gap. There are extra options.

```json
{
  "gap": 1,
  "options": {
    "A": "from where he caught the last boat out...",
    "B": "so he developed tricks for playing them...",
    "C": "from which he could make a selection..."
  }
}
```

### Answer key structure

```json
{
  "0": "J",
  "1": "G",
  "2": "B",
  "3": "E",
  "4": "A",
  "5": "F",
  "6": "K",
  "7": "C",
  "8": "I"
}
```

## 6. Example: multiple choice reading

### Task

Read a text about the development of a city. Choose A, B, C or D.

```text
1. In the 1950s show business celebrities...
A performed to small audiences.
B visited the city in huge numbers.
C concentrated on comedy mainly.
D always stayed in luxury hotels.
```

### Answer key structure

```json
{
  "0": "D",
  "1": "A",
  "2": "D",
  "3": "C",
  "4": "B",
  "5": "C",
  "6": "D"
}
```

## 7. Original generated mini-example

### Text

```text
When Lina moved to Vienna for her studies, she expected public transport to be complicated. Instead, she found that the city was easier to navigate than she had imagined. The only thing that surprised her was how quiet people were on the underground. In her home city, passengers often talked loudly, but in Vienna many people read, listened to music, or looked out of the window.
```

### True/False items

```json
[
  {
    "statement": "Lina expected Vienna's public transport to be difficult.",
    "answer": "T",
    "first_four_words": "When Lina moved to"
  },
  {
    "statement": "People on the underground in Vienna often talked loudly.",
    "answer": "F",
    "first_four_words": "In her home city"
  }
]
```

## 8. Reading generation warning

Generated reading tasks must have precise evidence. If the generator cannot identify the exact evidence sentence, reject the task. A reading task without reliable evidence is just vibes with punctuation, which is apparently not an exam format yet.
