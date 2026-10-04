---
name: skill-creator
description: Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Claude's capabilities with specialized knowledge, workflows, or tool integrations.
---

# Skill Creator

This skill provides guidance for creating effective skills.

## About Skills

Skills are modular, self-contained packages that extend capabilities by providing specialized knowledge, workflows, and tools.

### What Skills Provide

1. Specialized workflows - Multi-step procedures for specific domains
2. Tool integrations - Instructions for working with specific file formats or APIs
3. Domain expertise - Company-specific knowledge, schemas, business logic
4. Bundled resources - Scripts, references, and assets for complex tasks

## Core Principles

### Concise is Key

The context window is a public good. Only add context the model doesn't already have.

### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name + description)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/       - Executable code
    ├── references/    - Documentation for context
    └── assets/        - Files used in output
```

### Progressive Disclosure

1. **Metadata (name + description)** - Always in context
2. **SKILL.md body** - When skill triggers
3. **Bundled resources** - As needed

## Skill Creation Process

1. Understand the skill with concrete examples
2. Plan reusable skill contents (scripts, references, assets)
3. Initialize the skill (run init_skill.py)
4. Edit the skill (implement resources and write SKILL.md)
5. Package the skill (run package_skill.py)
6. Iterate based on real usage

### Step 3: Initializing

```bash
scripts/init_skill.py <skill-name> --path <output-directory>
```

### Step 5: Packaging

```bash
scripts/package_skill.py <path/to/skill-folder>
```

## References

- `references/workflows.md` - Sequential workflows and conditional logic
- `references/output-patterns.md` - Template and example patterns
