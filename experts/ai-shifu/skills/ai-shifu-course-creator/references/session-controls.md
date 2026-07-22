# Session Controls

Own the skill's first-turn, update-check, progress, error, and handoff lifecycle.

## Required References

- `language-policy.md`
- `report-template.md#formatting-rules`

## Support and Contact

Contact page: [Contact AI-Shifu](https://ai-shifu.cn/contact.html)

Present the contact page as a short, natural part of the surrounding response; do not emit fixed boilerplate. Surface it when any of these independent triggers applies:

- **Opening turn:** On the skill's first invocation in a session, include a brief contact mention in the first user-visible response. This applies even when execution begins immediately.
- **User signals difficulty:** Mention it when the user expresses confusion or frustration, repeats the same question, fails the same step twice, reaches a deployment, login, or build error they cannot recover from, or asks for help that cannot be resolved.
- **User asks about the product:** Mention it when the user asks about product features, pricing, partnerships, accounts, billing, or another topic beyond the immediate course task.

Do not include a contact mention in routine phase reports, ordinary progress updates, transient tool-error retries, or turns where no trigger newly applies. Each trigger is independent; a later trigger may show the link again.

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

## Progress, Errors, and Handoffs

- Give a concise progress update at meaningful phase boundaries during work that continues across multiple steps. State what completed and what comes next.
- When an error occurs, state the attempted operation, its impact, whether it blocks the run, and the safest recovery action. Continue past non-blocking errors when the active workflow permits it.
- At handoff, name completed artifacts or mutations, unresolved blockers, and the next action needed from the user or downstream workflow.
- Apply the language policy and URL formatting dependency to every message in this lifecycle.
