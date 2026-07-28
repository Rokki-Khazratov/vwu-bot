<!--
Project: VWU EPE Telegram Study Bot
Language: English
Purpose: AI guideline draft for task generation/evaluation, not backend code.
Source basis: user-provided EPE sample exam PDF, EPE sample key PDF, user-provided writing rubric photos, and user-confirmed real-exam notes.
Important: Use these files as prompt/context guidelines. Do not copy official sample texts verbatim into generated tasks.
-->

# English EPE Writing — Task Generation Guideline

## 1. Purpose

This file defines how an AI generator should create new English EPE writing tasks for the VWU-style study bot.

The current primary writing task type is:

- **Blog comment / social media comment**

The generator must create exam-like tasks, not random writing prompts. The generated task must be suitable for B1+ VWU EPE preparation and must include a clear source post, three content points, personal argumentation, interactive elements, and a 250-word target.

## 2. Source confidence

| Rule | Status |
|---|---|
| EPE written exam has Reading, Language in Use, Text Production | Official sample PDF |
| Writing is worth 20 points | Official sample PDF / rubric photos |
| Blog comment is the observed writing format | Official sample PDF + user-provided real task photo |
| 250 words with +/- 10% target | Official sample PDF / task photos |
| TORA scoring: 4 criteria x 5 points | Rubric photo + checked student task |
| Word count penalties | Rubric photo + user-confirmed table |

## 3. Task family: blog comment

### 3.1 Required task structure

A generated task must contain:

1. **Title of the source post**
2. **Author name / username**
3. **Date and time of post**
4. **A short source post** written in first person or as a personal opinion
5. **Instruction**: the student has read the post and must respond in a blog comment
6. **Three content points** that the student must address
7. **Instruction to argue from a personal point of view**
8. **Instruction to include interactive elements** to engage readers
9. **Word target: 250 words +/- 10%**
10. **Optional starter fields**: user name and date, not counted in the word count

### 3.2 Output JSON structure

The task generator must return structured data, not free prose.

```json
{
  "task_type": "blog_comment",
  "level": "B1+",
  "title": "string",
  "source_post": {
    "post_title": "string",
    "author_display_name": "string",
    "author_username": "string",
    "posted_at": "string",
    "body": "string"
  },
  "student_instruction": "You have decided to comment on this blog post.",
  "content_points": [
    {
      "id": "cp1",
      "text": "string",
      "required": true,
      "expected_function": "summary_or_analysis | discussion | suggestion | recommendation | personal_view"
    },
    {
      "id": "cp2",
      "text": "string",
      "required": true,
      "expected_function": "discussion"
    },
    {
      "id": "cp3",
      "text": "string",
      "required": true,
      "expected_function": "suggestion_or_recommendation"
    }
  ],
  "requirements": {
    "text_type": "blog_comment",
    "word_target": 250,
    "word_min_soft": 225,
    "word_max_soft": 275,
    "interactive_elements_required": true,
    "personal_point_of_view_required": true,
    "register": "semi-informal",
    "include_user_name_and_date_fields": true
  },
  "topic_tags": ["education", "technology"],
  "difficulty_notes": "B1+; clear topic; no specialised knowledge required"
}
```

## 4. Source post generation rules

The source post should be:

- 100–170 words long;
- written in natural blog/social-media style;
- understandable for B1+ students;
- opinionated enough to allow agreement/disagreement;
- not too balanced: it should contain a clear attitude that the student can analyse;
- based on everyday, school, student, society, technology, work, family, travel, environment, or lifestyle topics;
- realistic but not emotionally extreme.

The source post should usually include:

- a personal experience or observation;
- a clear opinion or concern;
- one or two rhetorical questions;
- a final question or challenge to readers.

### Recommended post pattern

```text
[Title]
by [Name] ([Username]); [Date]; [Time]

Yesterday / Recently / In my school / In my neighbourhood / Online, I noticed ...
I think ... because ...
Some people say ..., but I am not convinced.
What do you think? Should we ... instead?
```

## 5. Content point generation rules

Each task must include exactly three content points.

The three points should normally follow this pattern:

1. **Reference / summary / analysis of the source post**
   - Example: summarise the writer's issue in one sentence and comment on it.
   - Example: refer to the post and analyse the writer's attitude.
2. **Discussion of a broader aspect**
   - Example: discuss positive effects of technology in education.
   - Example: discuss why young people spend time online.
3. **Suggestions / recommendation / solution**
   - Example: suggest ways to use digital tools responsibly.
   - Example: give advice to the author.

Do not create content points that are too similar. Each point must require a different communicative function.

## 6. Expected student text format

A strong answer should usually include:

1. Greeting or direct reference to the author/post.
2. Short summary of the author's issue or attitude.
3. Personal position: agreement, partial agreement, or disagreement.
4. Development of all three content points.
5. Supporting details or examples.
6. Interactive blog-comment elements, such as:
   - direct address to the author/readers;
   - rhetorical questions;
   - short conversational phrases;
   - invitation for other readers to comment;
   - hashtags, if appropriate and not excessive.
7. Final recommendation or closing question.

## 7. Register and style

The target style is **semi-informal blog comment**.

Allowed:

- first person (`I think`, `In my opinion`);
- direct address (`Hi Sophia`, `What do you think?`);
- rhetorical questions;
- moderate contractions (`don't`, `I'm`);
- conversational transitions;
- short interactive closing.

Avoid generating tasks that require:

- formal academic essays;
- business email conventions;
- heavy statistics;
- specialised factual knowledge;
- political, religious, traumatic, violent, or sexual content;
- personal medical advice;
- culture-war topics where moderation is hard.

## 8. Suitable topic pool

Good topic types:

- digital technology in school;
- phones in public spaces;
- online learning;
- living with parents vs moving out;
- part-time jobs for students;
- public transport and student life;
- healthy lifestyle at university;
- social media and friendship;
- studying abroad;
- learning languages;
- school rules;
- environmental habits;
- volunteering;
- online shopping;
- sports and mental health.

Bad topic types:

- war, extremist politics, terrorism;
- explicit religion debates;
- real named politicians;
- self-harm;
- medical diagnoses;
- highly specialised science;
- adult content;
- hate speech;
- topics that require exact legal knowledge.

## 9. Difficulty rules

The generated task should be hard enough to test B1+ writing, but not C1.

The task should test:

- ability to understand an opinionated post;
- ability to address required content points;
- ability to organise a 250-word response;
- ability to use linking devices;
- ability to express opinion and advice;
- vocabulary range and grammatical control.

Do not make the source post linguistically harder than the expected student answer.

## 10. Generation prompt requirements

The prompt for the task generator must include:

- target exam profile: `VWU EPE English B1+`;
- task type: `blog comment`;
- required output schema;
- instruction not to copy official examples;
- instruction to create original source post and content points;
- prohibited topics;
- B1+ difficulty target;
- exactly three content points;
- 250-word target requirement.

## 11. Quality checklist before saving generated task

A generated writing task is valid only if:

- it has a source post;
- the author and post context are clear;
- the source post has a strong attitude;
- there are exactly three content points;
- the content points are distinct;
- at least one content point requires personal argumentation;
- at least one content point requires suggestions or advice;
- the task asks for interactive elements;
- word target is 250;
- no prohibited topic is used;
- no official sample is copied.

## 12. Original generator example

```json
{
  "task_type": "blog_comment",
  "level": "B1+",
  "title": "Phones at Family Dinners",
  "source_post": {
    "post_title": "Nobody talks anymore",
    "author_display_name": "Mia",
    "author_username": "MiaTalks",
    "posted_at": "yesterday at 8:30 pm",
    "body": "Last Sunday my whole family met for dinner, but half of us were looking at our phones most of the time. My little brother was watching videos, my cousin was answering messages, and even my aunt checked work emails. I think phones are destroying family time. Some people say it is normal because everyone is busy, but I find it sad. Shouldn't we put our phones away when we meet people in real life?"
  },
  "student_instruction": "You have read this blog post and decided to respond to it. In your blog comment you should:",
  "content_points": [
    {
      "id": "cp1",
      "text": "summarise Mia's issue in one sentence and comment on it",
      "required": true,
      "expected_function": "summary_or_analysis"
    },
    {
      "id": "cp2",
      "text": "discuss why people use their phones during family or social meetings",
      "required": true,
      "expected_function": "discussion"
    },
    {
      "id": "cp3",
      "text": "suggest rules for using phones responsibly when meeting other people",
      "required": true,
      "expected_function": "suggestion_or_recommendation"
    }
  ],
  "requirements": {
    "text_type": "blog_comment",
    "word_target": 250,
    "word_min_soft": 225,
    "word_max_soft": 275,
    "interactive_elements_required": true,
    "personal_point_of_view_required": true,
    "register": "semi-informal",
    "include_user_name_and_date_fields": true
  },
  "topic_tags": ["technology", "family", "communication"],
  "difficulty_notes": "B1+; everyday topic; no specialised knowledge required"
}
```
