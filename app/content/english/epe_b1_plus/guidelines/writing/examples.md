<!--
Project: VWU EPE Telegram Study Bot
Language: English
Purpose: AI guideline draft for task generation/evaluation, not backend code.
Source basis: user-provided EPE sample exam PDF, EPE sample key PDF, user-provided writing rubric photos, and user-confirmed real-exam notes.
Important: Use these files as prompt/context guidelines. Do not copy official sample texts verbatim into generated tasks.
-->

# English EPE Writing — Examples

## 1. Purpose

This file stores examples for the English EPE writing module.

The goal is not to copy official tasks verbatim. Use examples to understand structure, scoring, and feedback style.

## 2. Official sample task patterns

### 2.1 Official sample pattern: blog comment on digital technology

Source pattern:

- A blog/social-media post by a named author.
- The author complains about young people using smartphones and tablets too much.
- The author asks whether people should stop being “glued to the screen”.

Required student actions:

1. Refer to the post and analyse the author's attitude towards digital technology.
2. Discuss reasons why young people spend a lot of time in front of screens.
3. Suggest rules and guidelines for using mobile phones in public.
4. Include interactive elements.
5. Write 250 words.

This official sample demonstrates the core EPE blog-comment format.

### 2.2 User-provided real checked task pattern: modern technology in the classroom

Source pattern:

- A blog post by a student named Sophia.
- Topic: modern technology in school and the risk of focusing too much on gadgets.
- The writer is sceptical about digital tools in education.

Required student actions visible in the task:

1. Summarise the writer's issue in one sentence and comment on it.
2. Discuss the positive effects of technology in education.
3. Suggest ways to use digital learning tools responsibly.
4. Argue from a personal point of view.
5. Include interactive elements.
6. Write 250 words +/- 10%.

Teacher score on the submitted sample was approximately:

| Criterion | Score |
|---|---:|
| T — Task Achievement | 3/5 |
| O — Organisation and Coherence | 2/5 |
| R — Range | 1.5/5 |
| A — Accuracy | 1/5 |
| Word-count penalty | visible penalty applied |
| Total | approximately 7.5/20 |

Use this as a low/mid-performance calibration sample.

## 3. Original generated example task

### Task

**Phones at Family Dinners**  
by Mia (“MiaTalks”); posted yesterday at 8:30 pm

Last Sunday my whole family met for dinner, but half of us were looking at our phones most of the time. My little brother was watching videos, my cousin was answering messages, and even my aunt checked work emails. I think phones are destroying family time. Some people say it is normal because everyone is busy, but I find it sad. Shouldn't we put our phones away when we meet people in real life?

You have read this blog post and decided to respond to it.

In your blog comment you should:

1. summarise Mia's issue in one sentence and comment on it;
2. discuss why people use their phones during family or social meetings;
3. suggest rules for using phones responsibly when meeting other people.

Requirements:

- Argue from a personal point of view.
- Include a range of interactive elements to engage your readers.
- Write 250 words (+/- 10%).

### Strong student answer example

```text
User name: StudyFan21
Date: 10 June 2026

Hi Mia,

I can understand why you were annoyed by that dinner, and I partly agree with you. If people meet in real life but spend the whole evening staring at their phones, the meeting loses its purpose. However, I do not think phones are the real problem. The problem is how and when we use them.

There are several reasons why people check their phones during family meetings. Some people are stressed because of school or work and feel that they must answer messages immediately. Others are simply bored or used to constant entertainment. To be honest, I sometimes check my phone too when a conversation becomes slow. But should that really be normal?

In my opinion, families should create simple rules. For example, phones could stay in another room during dinner, except if somebody is waiting for an important call. Another idea is to agree on a short “phone break” after the meal, so nobody feels completely cut off. Parents should also follow the same rules as children, because otherwise it feels unfair.

What do you think, guys? Maybe we do not need to ban phones completely, but we should remember that real people at the table deserve more attention than a screen.
```

Expected score range: **16–19/20**, depending on accuracy.

Why it is strong:

- clear reference to the post;
- all content points developed;
- personal opinion;
- interactive question;
- coherent paragraphs;
- useful linking;
- B1+ vocabulary without being too artificial.

### Weak student answer example

```text
Hi Mia,

I agree with you. Phones are very bad and people use phones every day. It is a big problem in the world. I think family is important and phones are not good. Many people use phones because they like phones and they are modern. In my country people also use phones.

My suggestion is people should not use phone. It is better to speak. Also parents must say children don't use phone. I think it is good. What do you think?
```

Expected score range: **6–9/20**.

Why it is weak:

- too short;
- content points are only mentioned;
- little development;
- weak range;
- repetitive vocabulary;
- minimal organisation;
- some accuracy issues.

## 4. Example feedback structure

```json
{
  "final_score": 15,
  "max_score": 20,
  "criteria": [
    {"code": "task_achievement", "score": 4, "max_score": 5},
    {"code": "organisation_coherence", "score": 4, "max_score": 5},
    {"code": "range_vocabulary_grammar", "score": 3, "max_score": 5},
    {"code": "accuracy_vocabulary_grammar", "score": 4, "max_score": 5}
  ],
  "content_points": [
    {"id": "cp1", "status": "developed"},
    {"id": "cp2", "status": "developed"},
    {"id": "cp3", "status": "developed"}
  ],
  "errors": [
    {
      "category": "preposition",
      "source_fragment": "depend from phones",
      "corrected_fragment": "depend on phones",
      "severity": "major"
    }
  ]
}
```

## 5. What a generated example must not do

Do not generate writing prompts that:

- are pure essays without blog interaction;
- ask for a formal letter;
- require expert facts;
- have only one content point;
- have content points that all ask the same thing;
- are copied from the official EPE samples;
- use sensitive or unsafe topics.
