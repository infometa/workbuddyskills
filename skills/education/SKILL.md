---
name: education
description: "Generate study plans, quizzes, flashcards, review materials, track learning progress and schedule study sessions. Use when users ask to create study plans, generate quiz questions, make flashcards, track study progress, or schedule review sessions for any topic."
description_zh: "学习助手：生成学习计划、测验、抽认卡、复习材料并跟踪进度"
description_en: "Study assistant: generate plans, quizzes, flashcards, review materials and track progress"
version: 3.4.1
homepage: https://clawhub.ai/skills/education
allowed-tools: Read,Write,Bash
---

# EDUCATION SKILL

Generate study plans, quizzes, flashcards, and review materials for any topic. Track progress and schedule sessions.

## COMMANDS

### 1. PLAN
Generate a structured study plan for a topic.
```bash
bash scripts/script.sh plan <topic> [--weeks <num>] [--level beginner|intermediate|advanced] [--output json|text]
```

### 2. QUIZ
Generate quiz questions on a topic.
```bash
bash scripts/script.sh quiz <topic> [--count <num>] [--type mcq|truefalse|short] [--difficulty easy|medium|hard]
```

### 3. FLASHCARD
Generate flashcards for key concepts.
```bash
bash scripts/script.sh flashcard <topic> [--count <num>] [--format plain|csv|json]
```

### 4. PROGRESS
Track and display learning progress.
```bash
bash scripts/script.sh progress [--topic <topic>] [--mark <milestone>] [--reset]
```

### 5. SCHEDULE
Create a study schedule with time blocks.
```bash
bash scripts/script.sh schedule <topic> [--hours-per-day <num>] [--days <num>] [--start <date>]
```

### 6. REVIEW
Generate a review checklist based on completed topics.
```bash
bash scripts/script.sh review <topic> [--scope all|weak|recent] [--format checklist|summary]
```

## OUTPUT

All commands print to stdout. Use `--output json` for machine-readable output where supported. Progress data is stored in `~/.education/progress.json`.

## REQUIREMENTS

- bash 4+
- python3 (standard library only)
