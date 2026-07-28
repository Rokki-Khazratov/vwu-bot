<!--
Project: VWU EPE Telegram Study Bot
Language: English
Purpose: AI guideline draft for task generation/evaluation, not backend code.
Source basis: user-provided EPE sample exam PDF, EPE sample key PDF, user-provided writing rubric photos, and user-confirmed real-exam notes.
Important: Use these files as prompt/context guidelines. Do not copy official sample texts verbatim into generated tasks.
-->

# English EPE Grammar / Language in Use — Notes

## 1. Practical focus

For MVP, prioritise:

1. Cloze missing letters.
2. Multiple choice.
3. Full-word gap / word formation / open gap.

Support editing and multiple matching later because they appear in official sample materials.

## 2. Common topics

- tenses;
- passive;
- conditionals;
- relative clauses;
- articles;
- prepositions;
- word order;
- collocations;
- phrasal verbs;
- word formation;
- modal verbs;
- gerund/infinitive;
- pronouns;
- linking words;
- quantifiers;
- spelling;
- lexical choice.

## 3. Evaluation warning

Language in Use is mostly objective. Do not waste LLM tokens on answer-key tasks. Humanity has committed enough crimes without asking an LLM whether `would` equals `would`.

## 4. Backend recommendation

Each generated item should store:

- answer;
- accepted answers;
- explanation;
- tags;
- points;
- case sensitivity flag;
- punctuation sensitivity flag;
- ambiguity review flag.
