# Existing Course Sync

## Required References

- `authentication.md`
- `course-target.md`
- `language-policy.md#language-audit`
- `cli/cli-reference.md#version-sync-pull--status`
- `cli/cli-reference.md#create-commands`
- `cli/cli-reference.md#update-commands`
- `cli/cli-reference.md#delete-commands`
- `cli/cli-reference.md#bulk-import`
- `cli/course-directory-spec.md#shifu-syncjson`

## Boundary

Use this workflow only after `course-target.md` resolves an **existing course**. It owns cloud-to-local pull, divergence status, lesson-content pushes, and the retry loop that converges after concurrent edits. The platform draft is the source of truth.

This workflow does not resolve the target, author content, publish the course, or manage metadata and attributes.

## Pull Before Editing

1. Run `pull <shifu_bid> --course-dir <dir>` before reading or changing local course files. This writes the cloud draft and `.shifu-sync.json` baseline.
2. Edit the freshly pulled files in place.
3. Complete `language-policy.md#language-audit` before pushing changed content.
4. Run `status --course-dir <dir>` to inspect cloud and local divergence.

Never hand-edit `.shifu-sync.json`. Always pass `--course-dir` to a version-aware push so the CLI can compare the recorded revision. Without the manifest baseline, concurrent-edit protection is degraded.

## Push Existing Course Content

Choose the narrowest command that represents the content change:

- `update-lesson <bid> <outline_bid> --teaching-prompt-file <file> --course-dir <dir>` updates one lesson and preserves its BID.
- `add-chapter`, `add-lesson`, `rename-lesson`, and `delete-lesson` apply the corresponding structural content change.
- `import <bid> --course-dir <dir>` pushes the whole directory. This operation deletes and recreates every outline, regenerates lesson BIDs, and gives recreated lessons the platform-default permission. Use it only when that destructive whole-course effect is intended.

The four structural commands do not accept `--course-dir` and do not refresh `.shifu-sync.json`. Immediately after each successful `add-chapter`, `add-lesson`, `rename-lesson`, or `delete-lesson`, run `pull <shifu_bid> --course-dir <dir>` before another local, status, or version-aware operation. Use the fresh pull to capture platform-assigned BIDs, outline mappings, and revisions; never continue from the pre-mutation sync baseline.

Course name, description, Course Prompt, publication, and other platform attribute writes are outside this workflow.

## Conflict Convergence

All version-aware content and management writes use this exit-code loop:

- Exit `0`: the push succeeded; the local sync baseline is refreshed.
- Exit `1`: a hard error occurred; stop and report it.
- Exit `2`: the cloud advanced since the recorded baseline. Treat this as a retry signal, not a terminal failure.

On exit `2`, the CLI backs up the unpushed work, pulls the latest cloud course over the local directory, and prints who changed it and when. Then repeat:

1. Read the freshly pulled files as the new baseline.
2. Reapply the intended change on top of that baseline. The agent performs this merge; the CLI never merges content automatically.
3. Run the same version-aware command again with `--course-dir`.
4. Repeat until exit `0`, stop on exit `1`, or stop after three consecutive exit-`2` responses for the same intended change.

After the third consecutive conflict, stop automatic retries, report the repeated convergence failure and current conflict details, and require explicit user confirmation before attempting the write again.

Do not force the stale local copy over the cloud. Backup locations and exact command side effects are defined in `cli/cli-reference.md`.
