<!--
Project: VWU EPE Telegram Study Bot
Language: English
Purpose: AI guideline draft for task generation/evaluation, not backend code.
Source basis: user-provided EPE sample exam PDF, EPE sample key PDF, user-provided writing rubric photos, and user-confirmed real-exam notes.
Important: Use these files as prompt/context guidelines. Do not copy official sample texts verbatim into generated tasks.
-->

# English EPE Writing — Evaluation Guideline

## 1. Purpose

This file defines how the AI evaluator must grade English EPE writing tasks, especially the **blog comment** task.

The English writing evaluation is based on the VWU-style **TORA** system:

- **T** = Task Achievement
- **O** = Organisation and Coherence
- **R** = Range: Vocabulary and Grammar
- **A** = Accuracy: Vocabulary and Grammar

Each criterion is worth **0–5 points**, for a total of **20 points**.

The evaluator must return structured feedback, not just a paragraph.

## 2. Source confidence

| Rule | Status |
|---|---|
| Writing task is worth 20 points | Official sample / rubric photo |
| Four criteria x 5 points | Rubric photo and checked writing sheet |
| Blog comment task type | Official sample and user-provided real task |
| 250 words +/- 10% | Official sample and task photo |
| Word-count penalty table | Rubric photo + user-confirmed transcription |
| `don't`, `I'm` count as one word | Rubric photo |
| If Task Achievement is 0, all other dimensions also get 0 | Rubric note |

## 3. Evaluation pipeline

The evaluator must follow this order:

1. **Pre-check**
   - Identify task type.
   - Count words.
   - Check hard-zero conditions.
   - Check whether the answer is assessable.
2. **Content point assessment**
   - Assess whether each required content point is missing, mentioned, partly developed, developed, or well developed.
3. **T score**: Task Achievement.
4. **O score**: Organisation and Coherence.
5. **R score**: Range of Vocabulary and Grammar.
6. **A score**: Accuracy of Vocabulary and Grammar.
7. Apply dependency rules.
8. Apply word-count penalties.
9. Return final score and feedback.

The AI may recommend raw criterion scores, but the backend should apply deterministic penalties and dependency rules.

## 4. Word count rules

Target word count: **250 words**.

Soft accepted range: **225–275 words**.

Contracted forms count as one word:

- `don't` = 1 word
- `I'm` = 1 word
- `can't` = 1 word
- `we're` = 1 word

User name and date fields are not included in the word count.

### 4.1 Penalty table

| Word count | Penalty / result |
|---:|---:|
| `> 476` | `-3 points` |
| `376–475` | `-2 points` |
| `276–375` | `-1 point` |
| `225–275` | `0 points` |
| `210–224` | `-1 point` |
| `190–209` | `-2 points` |
| `170–189` | `-3 points` |
| `150–169` | `-4 points` |
| `130–149` | `-5 points` |
| `111–129` | `-6 points` |
| `< 110` | `total score = 0` |

Important: The AI must not invent a different penalty. If the word count is in a listed range, use the exact rule above.

## 5. Hard-zero conditions

The whole writing task should receive **0/20** if:

- the response has fewer than 110 words;
- the response is not in English enough to assess;
- the response does not address the task at all;
- the response is unrelated to the source post and content points;
- the response is copied almost entirely from the prompt;
- the response is empty or contains only fragments;
- the response is not a blog/comment when the task requires one, and the blog task requirements are essentially missing.

## 6. Dependency rule

If **Task Achievement = 0**, then:

```text
Organisation and Coherence = 0
Range = 0
Accuracy = 0
Final score before penalties = 0
```

This rule is mandatory. Do not give language points for a text that fails Task Achievement completely.

## 7. Criterion T: Task Achievement

Task Achievement evaluates whether the student fulfilled the communicative task.

It includes:

- correct text type: blog comment;
- clear reference to the original post;
- interactive elements;
- personal perspective;
- all three content points;
- supporting details;
- relevance to the source post;
- quality of argumentation.

### T = 5

Give 5 if:

- the text clearly and successfully functions as a blog comment;
- the student refers to the source post naturally;
- interactive elements are used successfully;
- the personal point of view is clear and convincing;
- all three content points are fully developed;
- each content point has relevant supporting details;
- the answer is strongly relevant to the blog post;
- the argumentation is relatable, effective, and convincing.

Typical signs:

- the student responds directly to the writer;
- the student analyses the writer's attitude, not only repeats it;
- the student gives concrete reasons and examples;
- suggestions are practical and connected to the topic;
- the conclusion invites further discussion.

### T = 4

Give 4 if:

- the blog comment format is clearly observed;
- all three content points are developed;
- at least some supporting details are included;
- the personal view is clear;
- argumentation is effective or mostly effective;
- relevance to the original blog post is clear.

Weaknesses allowed at 4:

- one content point may be less detailed than the others;
- interactive elements may be present but not very natural;
- examples may be basic but relevant.

### T = 3

Give 3 if:

- the blog comment format is sufficiently observed;
- all three content points are addressed but not fully developed, **or** two content points are developed well;
- the student's position is comprehensible;
- the response has noticeable relevance to the blog post;
- some supporting detail exists but is limited.

Typical 3-level weaknesses:

- one content point is thin or only mentioned;
- the response is understandable but not very persuasive;
- the student summarises more than analyses;
- examples are general.

### T = 2

Give 2 if:

- the blog comment requirements are only partly observed;
- only two content points are addressed;
- supporting details are missing, weak, irrelevant, or not developed;
- the student's point of view is not always convincing;
- the answer is sometimes vague or not directly to the point;
- some parts are only loosely related to the blog post.

This is the level seen when the text has the right general topic but fails to complete the task properly.

### T = 1

Give 1 if:

- the blog comment format is mostly missing;
- there is no meaningful reference to the blog post;
- interactive elements are missing;
- personal perspective is missing or unclear;
- only one content point is developed, or content is mostly irrelevant;
- argumentation is incomprehensible at times;
- ideas are too vague or unrelated to the blog post;
- user name and date may be missing if the exam requires them.

### T = 0

Give 0 if:

- the performance fails to address the task;
- the response is below the hard minimum word count;
- language is insufficient for assessment;
- the answer is not assessable;
- the answer is unrelated to the prompt.

Then apply the dependency rule: all other criteria are 0.

## 8. Criterion O: Organisation and Coherence

Organisation and Coherence evaluates whether ideas are logically arranged and connected.

It includes:

- paragraphing;
- logical order;
- links between ideas;
- links between content points;
- reference words;
- pronouns;
- linking devices;
- overall readability.

### O = 5

Give 5 if:

- the text has very clear overall coherence;
- ideas follow a logical order;
- content points are smoothly connected;
- paragraphs are well controlled;
- linking devices and reference words are used naturally;
- pronouns are clear;
- the reader never has to reconstruct the structure.

### O = 4

Give 4 if:

- coherence is clear;
- ideas and content points are linked successfully;
- paragraphing is mostly effective;
- linking devices are used well;
- references and pronouns are mostly clear.

Weaknesses allowed:

- some simple linking;
- minor repetition of connectors;
- one transition may be mechanical.

### O = 3

Give 3 if:

- the text is sufficiently coherent;
- the reader can follow the main structure;
- there are clear attempts to link ideas and content points;
- reference words, linking devices, and pronouns are sufficiently clear;
- paragraphing is present or understandable.

Typical 3-level issues:

- some weak transitions;
- overuse of `firstly`, `also`, `on the other hand`;
- paragraphs are uneven;
- some ideas feel listed rather than developed.

### O = 2

Give 2 if:

- the text shows difficulty producing clearly intelligible continuous writing;
- links between ideas and content points are often unclear or missing;
- linking devices are limited or sometimes inadequate;
- reference words are sometimes unclear;
- paragraphing is inadequate;
- text structure is weak.

### O = 1

Give 1 if:

- the text has little or no coherence;
- ideas are random or not logically connected;
- linking devices are lacking or inadequate;
- reference words are frequently unclear;
- paragraphing is illogical or absent.

### O = 0

Give 0 if:

- the performance fails to show any text organisation.

## 9. Criterion R: Range — Vocabulary and Grammar

Range evaluates how much lexical and grammatical variety the student can use.

It is not primarily about correctness. Correctness belongs mainly to Accuracy.

Range includes:

- vocabulary variety;
- grammatical structure variety;
- ability to express ideas without constant simplification;
- avoidance of repetition;
- avoidance of prompt lifting;
- ability to form complex but understandable sentences.

### R = 5

Give 5 if:

- vocabulary range is very good for B1+;
- grammar structures are varied;
- the student can express ideas flexibly;
- there are no real signs of limitation of expression;
- the text does not rely on repeated basic phrases.

### R = 4

Give 4 if:

- vocabulary and grammar range are good;
- the student uses more than only basic structures;
- limitations are rare;
- repetition is minimal;
- the language is appropriate for the task.

### R = 3

Give 3 if:

- vocabulary and grammar range are sufficient;
- the student can fulfil the task;
- some limitations are visible;
- there may be awkward expressions;
- there may be some repetition;
- structures are mostly simple but not too limited.

### R = 2

Give 2 if:

- vocabulary and grammar range are insufficient;
- the language is simplistic;
- limitations of expression are apparent;
- awkward expressions are frequent;
- repetition is common;
- some phrases may be lifted from the prompt.

### R = 1

Give 1 if:

- language is very simplistic;
- the student frequently fails to express themselves clearly;
- there are numerous awkward expressions;
- repetition is heavy;
- there is repeated prompt lifting.

### R = 0

Give 0 if:

- the performance fails to show any structural or lexical range.

## 10. Criterion A: Accuracy — Vocabulary and Grammar

Accuracy evaluates correctness and whether errors block communication.

It includes:

- grammar control;
- vocabulary control;
- spelling;
- punctuation;
- basic structures;
- frequent structures;
- whether errors impede understanding;
- whether the reader must re-read.

### A = 5

Give 5 if:

- control of frequent grammatical structures is very good;
- basic vocabulary is accurate;
- spelling and punctuation are very good;
- errors never impede understanding;
- errors are rare and minor.

### A = 4

Give 4 if:

- control of frequent grammatical structures is good;
- vocabulary, spelling, and punctuation are generally good;
- errors rarely impede communication;
- mistakes exist but do not disturb reading.

### A = 3

Give 3 if:

- control of frequent grammatical structures is sufficient;
- basic vocabulary, spelling, and punctuation are sufficient;
- errors sometimes impede communication, especially when the student tries to express complex ideas;
- the reader can still understand the text without major effort.

### A = 2

Give 2 if:

- there are severe lapses in frequent grammar structures;
- basic vocabulary, spelling, or punctuation are often problematic;
- errors occur frequently, even in basic ideas;
- the reader often has to make an effort to understand sections.

### A = 1

Give 1 if:

- mistakes repeatedly cause misunderstanding or communication breakdown;
- elementary errors are frequent;
- the reader repeatedly has to stop and re-read;
- systematic interference from another language is visible.

### A = 0

Give 0 if:

- errors cause a breakdown of communication throughout the text.

## 11. Content point assessment

For each content point, return one of:

- `missing`
- `mentioned`
- `partly_developed`
- `developed`
- `well_developed`

### Definitions

| Status | Meaning |
|---|---|
| `missing` | The content point is not addressed. |
| `mentioned` | The point appears only as a phrase or sentence, without real development. |
| `partly_developed` | The point is addressed but lacks detail, example, or clear relevance. |
| `developed` | The point is clearly answered with relevant support. |
| `well_developed` | The point is answered clearly, with strong support and relevance to the post. |

## 12. Interactive elements

Blog comments should include interactive elements. These can include:

- direct greeting;
- direct address to author/readers;
- rhetorical question;
- question to readers at the end;
- short conversational aside;
- hashtag, if appropriate;
- explicit reference to the blog post.

Do not reward random hashtags or emojis if they do not support the blog-comment style.

## 13. Error taxonomy

Return errors using categories:

- `task_type`
- `content_point`
- `argumentation`
- `organisation`
- `cohesion`
- `grammar`
- `word_order`
- `verb_form`
- `tense`
- `article`
- `preposition`
- `vocabulary`
- `collocation`
- `spelling`
- `punctuation`
- `register`
- `repetition`
- `prompt_lifting`

Severity:

- `minor`: local issue, does not block understanding;
- `major`: repeated or noticeable issue, affects score;
- `critical`: blocks communication or task achievement.

## 14. Required evaluation JSON

```json
{
  "word_count": 248,
  "hard_zero": false,
  "word_count_penalty": 0,
  "raw_score": 15,
  "final_score": 15,
  "max_score": 20,
  "criteria": [
    {
      "code": "task_achievement",
      "label": "Task Achievement",
      "score": 4,
      "max_score": 5,
      "band_reason": "All three content points are developed, but one lacks detail.",
      "evidence": ["short quote from student text"]
    },
    {
      "code": "organisation_coherence",
      "label": "Organisation and Coherence",
      "score": 4,
      "max_score": 5,
      "band_reason": "Clear structure with mostly successful linking.",
      "evidence": ["short quote"]
    },
    {
      "code": "range_vocabulary_grammar",
      "label": "Range: Vocabulary and Grammar",
      "score": 3,
      "max_score": 5,
      "band_reason": "Sufficient range, but some repetition and simple structures.",
      "evidence": ["short quote"]
    },
    {
      "code": "accuracy_vocabulary_grammar",
      "label": "Accuracy: Vocabulary and Grammar",
      "score": 4,
      "max_score": 5,
      "band_reason": "Errors rarely impede communication.",
      "evidence": ["short quote"]
    }
  ],
  "content_points": [
    {
      "id": "cp1",
      "status": "developed",
      "comment": "The student summarises and comments on the issue clearly.",
      "evidence": "short quote"
    }
  ],
  "strengths": ["string"],
  "errors": [
    {
      "category": "word_order",
      "severity": "major",
      "source_fragment": "Although there is many advantages",
      "corrected_fragment": "Although there are many advantages",
      "explanation": "Subject-verb agreement error.",
      "criterion_code": "accuracy_vocabulary_grammar"
    }
  ],
  "corrected_fragments": [
    {
      "before": "string",
      "after": "string",
      "reason": "string"
    }
  ],
  "recommendations": ["string"],
  "confidence": 0.86
}
```

## 15. Feedback style

Feedback should be useful, direct, and exam-focused.

It should include:

- final score;
- criterion table;
- content point table;
- word-count penalty;
- 3–7 most important errors;
- corrected fragments;
- concrete next-step recommendations.

Do not list every tiny typo if the text has many larger problems. Prioritise errors that affect TORA score.

## 16. Scoring guardrails

The evaluator must not:

- give 5 in Task Achievement if any content point is missing;
- give 5 in Organisation if the text is one unstructured paragraph with weak links;
- give 5 in Accuracy if errors sometimes impede communication;
- punish a text heavily for one minor spelling error;
- give high Range for repeated basic phrases;
- ignore word-count penalties;
- reward copied prompt phrases as original range;
- evaluate an essay as if it were a blog comment if the task requires interactive elements.

## 17. Calibration note from checked student work

A checked student writing sample on “Modern Technology in the Classroom” received approximately:

- T = 3/5
- O = 2/5
- R = 1.5/5
- A = 1/5
- Total after penalty: about 7.5/20

The teacher annotations indicate many accuracy issues, weak range, organisation problems, and incomplete development of content points. This sample should be treated as a calibration example for low/mid performance, not as a model answer.
