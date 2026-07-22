# New Course Deployment

## Required References

- `authentication.md`
- `course-target.md`
- `language-policy.md#language-audit`
- `cli/cli-reference.md#query-commands`
- `cli/cli-reference.md#bulk-import`
- `cli/cli-reference.md#state-management`
- `cli/course-directory-spec.md`
- `report-template.md`

## Conditional References

- When a standalone course directory lacks a Course Prompt: `course-prompt.md`
- When a non-empty course description is required but absent: `course-description.md`
- When an explicitly selected platform attribute must be set before first publication: `course-management.md#operations`

## Boundary

Use this workflow only after `course-target.md` resolves a **new course**. It turns an already-authored course directory into a new live platform course:

`write directory → build → import --new → publish → verify`

When an explicitly selected attribute must be set on the new course, insert that management operation after import and before the first publish.

Existing-course edits and standalone platform-management operations are outside this workflow.

## Preconditions

- Complete `authentication.md`.
- Confirm the resolved target is `new`.
- Provide a course directory that conforms to `cli/course-directory-spec.md`, including lesson files. Require a completed `course-prompt.md` for a content-complete deployment; when it is missing, complete the applicable conditional authoring reference before building. A missing course description keeps the CLI's existing empty-description fallback unless the author requests non-empty listing copy. This workflow consumes final artifacts; it does not define their content.
- Complete the source-file checks in `language-policy.md#language-audit` before the first platform mutation.

## Deploy and Publish

1. Write the final authoring artifacts into the course directory without changing their defined filenames.
2. Run `build --course-dir <dir>` to generate `<dir>/shifu-import.json` locally.
3. Complete the payload checks in `language-policy.md#language-audit` against the generated import file. Stop before import if the payload fails.
4. Run `import --new --json-file <dir>/shifu-import.json` and capture the returned Shifu BID. `import --new --course-dir <dir>` remains an equivalent one-step build-and-import CLI form, but a separate build is required when the payload must be inspected before mutation.
5. Before first publication, apply only explicitly selected platform-attribute operations through the conditional management reference. This includes enabling Listen Mode when Course Design Intake selected it; leave every unspecified attribute unchanged.
6. Run `publish <shifu_bid>` to make the current draft available at the public learner URL.

`import --new` creates the platform course but does not publish it. The public URL is expected to work only after `publish` succeeds.

## Verify

1. Copy the verification URLs and their following Chinese `# ...` hints exactly from CLI output; do not reconstruct URLs. Format them according to `report-template.md`.
2. Run `show <shifu_bid>` and compare the platform title, description, chapter structure, lesson count, and lesson titles with the local course directory. Run `export <shifu_bid>` and compare the exported Course Prompt with `course-prompt.md`.
3. For each lesson, use its returned `outline_bid` with `show <shifu_bid> <outline_bid>` and confirm that the deployed Teaching Prompt, variables, and interaction syntax match the local file.
4. Confirm both the preview URL and, after publication, the public learner URL are reachable.

## Completion Criteria

- `build`, `import --new`, and `publish` complete without errors.
- The platform structure and content match the source directory.
- Preview and public verification succeed.
- The final report contains the exact Shifu BID and CLI-produced URLs.
