# English Resume Template (Markdown · US Letter / A4)

> Used by Step 7 output assembler to produce `resume-en.md`.
> Placeholders `{{VAR}}`, optional fields `{{?VAR}}`.
> Design: 1-page hard cap for <5 yrs experience; 2-page OK for senior.
> Font suggestion: 10-11pt serif body (Garamond / Times / EB Garamond) / 12-13pt bold headers.
>
> **Compliance notes (MUST follow):**
> - NO age, gender, marital status, photo, ethnicity, political affiliation (US/EU legal norm)
> - NO soft-skill phrases like "hard-working", "obedient", "diligent" (cultural mismatch)
> - YES bullet-starting action verbs (past tense for past roles, present for current)
> - YES XYZ formula: `Accomplished [X] as measured by [Y], by doing [Z]`

---

# {{NAME_EN}}

{{CITY}} · {{PHONE}} · {{EMAIL}}
{{?GITHUB_LINE}}{{?LINKEDIN_LINE}}{{?PERSONAL_SITE_LINE}}

{{?SUMMARY_SECTION}}

---

## EDUCATION

{{#each EDUCATION}}
**{{SCHOOL}}** — {{DEGREE_EN}} in {{MAJOR}}
*{{START_DATE_EN}} – {{END_DATE_EN}}*
{{?GPA_LINE_EN}}{{?HONORS_LINE_EN}}{{?RELEVANT_COURSES_LINE}}

{{/each}}

---

{{#if WORK_EXPERIENCE_EXISTS}}
## WORK EXPERIENCE

{{#each WORK_EXPERIENCE}}
**{{TITLE}}**, {{COMPANY}} {{?DEPARTMENT_INLINE}} — {{CITY}}
*{{START_DATE_EN}} – {{END_DATE_EN}}*
{{#each BULLETS}}
- {{TEXT}}
{{/each}}
{{?TECH_STACK_LINE_EN}}

{{/each}}
{{/if}}

---

## PROJECTS

{{#each PROJECTS}}
**{{NAME}}** — {{ROLE_EN}} {{?LINKS_INLINE}}
*{{START_DATE_EN}} – {{END_DATE_EN}}*
{{#each BULLETS}}
- {{TEXT}}
{{/each}}
**Tech stack**: {{TECH_STACK_CSV}}

{{/each}}

---

## SKILLS

{{#if SKILLS.programming_languages}}
- **Languages**: {{SKILLS.programming_languages_csv}}
{{/if}}
{{#if SKILLS.frameworks}}
- **Frameworks / Tools**: {{SKILLS.frameworks_csv}}
{{/if}}
{{#if SKILLS.databases}}
- **Databases**: {{SKILLS.databases_csv}}
{{/if}}
{{#if SKILLS.cloud}}
- **Cloud / Infra**: {{SKILLS.cloud_csv}}
{{/if}}
{{#if SKILLS.languages}}
- **Languages (spoken)**: {{SKILLS.languages_formatted_en}}
{{/if}}
{{#if SKILLS.certifications}}
- **Certifications**: {{SKILLS.certifications_csv}}
{{/if}}

---

{{#if PUBLICATIONS}}
## PUBLICATIONS

{{#each PUBLICATIONS}}
- {{ITEM}}
{{/each}}
{{/if}}

{{#if AWARDS}}
## AWARDS & HONORS

{{#each AWARDS}}
- {{ITEM}}
{{/each}}
{{/if}}

---

<!--
【English resume rules (internal, strip before rendering)】

1. Section order (US/EU standard):
   Summary (optional, senior only) → Education → Work → Projects → Skills → Publications → Awards

2. Action verb bullet patterns (past tense for past, present for current):
   GOOD starters: Architected, Built, Designed, Implemented, Launched, Led, Optimized,
                  Owned, Reduced, Scaled, Shipped, Spearheaded
   AVOID:         Participated in, Helped with, Was responsible for

3. XYZ formula (Google resume rule):
   "Accomplished [X] as measured by [Y], by doing [Z]"
   e.g. "Reduced P99 latency by 40% (500ms → 300ms) by rewriting the sharding layer in Go."

4. NEVER include:
   - Age, date of birth
   - Gender, marital status
   - Photo
   - Ethnicity, religion, political affiliation
   - Salary expectation (put in cover letter, not resume)
   - Soft-skill claims: "hard-working", "obedient", "fast learner", "great team player"
     → Show via metrics & action verbs instead.

5. Length:
   - < 5 yrs experience: 1 page HARD CAP
   - 5-15 yrs: 2 pages OK
   - >15 yrs (executive): 2-3 pages OK, usually with separate "Highlights" section

6. Phone number format:
   - US jobs: +1 (555) 123-4567
   - UK jobs: +44 7... 
   - APAC / global: +86 138-0013-8000

7. Date format: "Sep 2020 – Jun 2024" (NOT "2020.09 – 2024.06"; that looks foreign)

8. City: "Beijing, China" (include country for non-US city); "San Francisco, CA" for US.
-->
