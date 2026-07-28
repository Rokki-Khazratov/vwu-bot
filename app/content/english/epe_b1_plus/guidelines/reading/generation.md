<!--
Project: VWU EPE Telegram Study Bot
Language: English
Purpose: AI guideline draft for task generation/evaluation, not backend code.
Source basis: user-provided EPE sample exam PDF, EPE sample key PDF, user-provided writing rubric photos, and user-confirmed real-exam notes.
Important: Use these files as prompt/context guidelines. Do not copy official sample texts verbatim into generated tasks.
-->

# English EPE Reading — Task Generation Guideline

## 1. Purpose

This file defines how AI should generate English EPE Reading Comprehension tasks.

The official sample shows several reading task types. The user-confirmed practical target format for the bot is:

1. True/False + justification — 5 points
2. Matching with extra options — 10 points
3. Sentence insertion / text-gap matching — 5 points

Total: **20 points**.

The official sample contains examples with different point values, so the backend must keep point distribution configurable.

## 2. Source confidence

| Rule | Status |
|---|---|
| Reading is worth 20 points | Official sample PDF |
| Reading time is 50 minutes | Official sample PDF |
| True/False/Justification format exists | Official sample PDF |
| Multiple matching format exists | Official sample PDF |
| Multiple choice format exists | Official sample PDF |
| User-confirmed practical structure: 5 + 10 + 5 | User-confirmed |

## 3. Supported reading task types

### 3.1 True/False with justification

Student must:

1. decide whether each statement is true or false;
2. provide the first four words of a supporting sentence from the text.

Generation requirements:

- create a reading text;
- create statements that can be clearly verified;
- each statement must have an evidence sentence;
- evidence must be a full sentence from the text;
- store the first four words of the evidence sentence;
- allow more than one correct evidence sentence only if configured.

### 3.2 Multiple matching: person/text matching

Student matches statements to people, sections, or texts.

Generation requirements:

- create 3–5 short texts or profiles;
- create 8–10 statements;
- each statement has one correct match;
- statements should test specific detail, opinion, or comparison;
- avoid statements that could fit multiple profiles.

### 3.3 Sentence insertion / text-gap matching

Student inserts missing sentences/clauses into gaps.

Generation requirements:

- create one coherent text;
- remove 5–8 sentences/parts;
- provide more options than gaps;
- include 1–3 distractors;
- each correct option must fit grammatically and logically;
- test cohesion, reference, pronouns, chronology, and topic flow.

### 3.4 Multiple choice reading

Student answers A/B/C/D questions about one text.

Generation requirements:

- create one reading text;
- create 5–8 questions;
- one correct answer per question;
- distractors must be plausible but clearly wrong according to text;
- test inference and detail, not world knowledge.

## 4. Reading text requirements

A reading text should be:

- B1+/B2 accessible;
- 450–900 words for longer tasks;
- shorter for matching profiles;
- coherent and exam-like;
- factual or semi-journalistic;
- not requiring specialised knowledge;
- free of offensive, graphic, or highly political content.

Recommended genres:

- article;
- blog-style informational post;
- short biography;
- student life text;
- history/culture article;
- technology/society article;
- profiles/interviews;
- public information text.

## 5. Output JSON structure

```json
{
  "section": "reading",
  "task_type": "true_false_justification",
  "title": "string",
  "level": "B1+",
  "instructions": "string",
  "text": "string",
  "items": [
    {
      "id": "r1",
      "statement": "string",
      "answer": "T",
      "evidence_sentence": "string",
      "first_four_words": "string",
      "points": 1,
      "tags": ["detail", "evidence"]
    }
  ],
  "total_points": 5
}
```

## 6. Generation quality checklist

Before saving a reading task:

- all answers are in the text;
- all justifications are exact first four words;
- no answer requires outside knowledge;
- distractors are plausible but wrong;
- matching items are not ambiguous;
- gap options fit only one best location;
- text length matches configuration;
- point total is correct;
- no official sample text is copied.

## 7. Topics

Good reading topics:

- work and career;
- student life;
- culture;
- migration and identity;
- technology;
- history of places;
- biographies;
- sports;
- environmental initiatives;
- education;
- public life;
- travel.

Avoid:

- war/current conflict;
- extremist politics;
- sexual content;
- self-harm;
- detailed medical advice;
- content requiring niche expert knowledge.
