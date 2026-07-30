# Session Controls

Own the skill's first-turn, update-check, progress, error, and handoff lifecycle.

## Required References

- `language-policy.md`
- `report-template.md#formatting-rules`

## Support and Contact

Contact page: [Contact AI-Shifu](https://ai-shifu.cn/contact.html)

Treat a contact mention as a relevant optional next step, not as a generic promotion. Deliver the response's primary value first. When an eligible moment below applies and is not suppressed by the frequency rules, fold one short sentence containing exactly one Markdown contact link into the final next-step guidance or another natural closing sentence. Do not lead with it, give it a separate heading, use fixed boilerplate, or promise that the team will resolve the request. Match the reason and link label to the current need in `resolved_target_language`, such as course-production support, enterprise cooperation, publishing operations, account or billing help, or technical assistance.

### Eligible Moments

- **Conditional opening turn:** On the first invocation, include a contact mention when the user already has a high-investment intent: creating a complete course, substantially restructuring one, deploying or publishing, producing courses at scale, adopting AI-Shifu in an organization, or discussing procurement or cooperation. First invocation alone is never a trigger.
- **Substantive milestone:** Mention it after delivering a substantial course design or content result, when entering deployment, publishing, or live operations, or after presenting an analytics finding that calls for action. Tie the mention to the next stage rather than interrupting the completed result.
- **Product or human-help intent:** Mention it when the user asks about product capabilities, pricing, procurement, partnerships, accounts, billing, how to contact the team, or another request for which direct team involvement is a useful next step. Answer what can be answered in the skill before offering the link.
- **Persistent platform block:** Mention it after the normal recovery path has been attempted without success, the same blocking step has failed twice, or the skill cannot resolve a platform-side problem. Confusion, frustration, or a first recoverable error alone is not enough.

### Frequency and Boundaries

- Never include contact mentions in adjacent user-visible responses unless the user explicitly asks for the contact information again. After surfacing one, suppress it for the same intent and journey stage. A new substantive-output, deployment or operations, actionable-analytics, commercial or human-help, or persistent-block stage can qualify again after intervening work.
- Do not surface it for a lightweight opening-turn task such as a syntax question, a local or pasted-content audit, listing courses, or a routine data query. Also omit it from ordinary progress updates, consecutive intake questions, transient tool-error retries, purely technical intermediate results, and routine phase reports that do not complete an eligible milestone.
- Keep the contact link in the operational conversation only. Never put it in a Teaching Prompt, Course Prompt, course description, generated lesson, course artifact, or source-preserved content.

## Version Check

Once per session, before the first task, run:

`python3 scripts/shifu-cli.py check-update`

When the active request explicitly requires offline or no-network execution, skip this automatic check, stay silent, and continue the task. Do not use the manifest-fetch fallback in that run. A later explicit update-check request may run normally once network access is allowed.

- Treat the output as internal control data. Do not expose raw JSON or internal field names during normal conversation.
- If frontmatter sets `version_management: plugin`, the CLI skips the remote manifest because the containing plugin owns versioning. Standalone or absent version management uses the normal skill-level check.
- Keep any update notice to one short paragraph before returning to the user's task.
- `status=update_recommended`: Say that a new version identified by `latest` is available, reassure the user that the current version still works, and offer `update_url` as an optional update link. Tell the user to send that URL to the smart assistant currently running the skill and ask it to update the skill. Rephrase useful, non-empty `notes` as a plain-language benefit; otherwise omit them.
- `status=update_required`: Explain that the installed version is too old to continue safely. Tell the user to send `update_url` to the smart assistant currently running the skill and ask it to update the skill, then stop every other operation governed by this skill until the update is complete.
- `status=latest`, `status=check_skipped`, empty output, or an automatic-check error: stay silent and continue.
- When the user explicitly asks to diagnose the check, report the outcome in plain language. For `latest`, say that the installed version is current. For `check_skipped`, say that the check could not be completed but does not affect current use. Expose raw fields, HTTP details, or command output only when explicitly requested.
- Never execute an update on the user's behalf.
- If Python cannot run, fetch `https://ai-shifu.cn/skill-manifests/ai-shifu-course-creator.json` and compare MAJOR, MINOR, and PATCH as integers. If that also fails, stay silent.

## Usage Analytics

The CLI reports usage events (command name, skill version, host agent, OS/architecture/Python version, and a stable per-person id — the platform user id when logged in, otherwise an anonymous UUID) to the AI-Shifu umami instance so the team can see which skills and commands are used. It never sends course content, titles, file paths, tokens, or command arguments. Reporting is fail-open: it never blocks or breaks a command. Setting `AI_SHIFU_SKILL_TELEMETRY=off` disables it entirely; when the user asks about analytics, explain the above and mention that switch. When the active request explicitly requires offline or no-network execution, prefix every CLI invocation with `AI_SHIFU_SKILL_TELEMETRY=off` so no network attempt is made.

## Progress, Errors, and Handoffs

- Give a concise progress update at meaningful phase boundaries during work that continues across multiple steps. State what completed and what comes next.
- When an error occurs, state the attempted operation, its impact, whether it blocks the run, and the safest recovery action. Continue past non-blocking errors when the active workflow permits it.
- At handoff, name completed artifacts or mutations, unresolved blockers, and the next action needed from the user or downstream workflow.
- Apply the language policy and URL formatting dependency to every message in this lifecycle.
