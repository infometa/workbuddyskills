# vibeknow-create Command Reference

## Global Flags

| Flag | Description |
|------|-------------|
| `--output string` | Output format: `text\|json\|ndjson` (default `text`; `VIBEKNOW_OUTPUT` sets the default, an explicit flag wins). An unrecognized value exits 2 rather than falling back to text. |
| `--profile string` | Override active profile for this command |
| `--verbose` | Emit request/response summaries (credentials redacted) |

## Environment

| Variable | Effect |
|----------|--------|
| `VIBEKNOW_OUTPUT` | Default `--output` value; an explicit flag wins |
| `VIBEKNOW_EVENTS` | `1`/`on` forces `vk_event=` progress lines onto stderr in any format; `0`/`off` suppresses them. Unset means on for `--output json` only. |
| `VIBEKNOW_ASSUME_YES` | Pre-authorises paid actions, same as `--yes`. Only set it when the user has agreed to the spend in advance. |
| `VIBEKNOW_EXPORT_TIMEOUT` | Local deadline for synchronous export polling (default 15m). Bounds the **local wait only** — it does not cancel the backend render. |

---

## create

Resolve the source to a document, then generate a video via the figlens pipeline.

`--from` accepts:
- A `doc_id` (e.g. `doc_abc12345`) — used directly
- A URL (`http://` or `https://`) — uploaded to vectoria first
- A local file path — uploaded to vectoria first
- `-` — read the source text from stdin

`--text` supplies the text itself, for the case where the user pasted a
passage rather than pointing at a file:

```bash
vibeknow create --text "季度复盘要点…" --async --output json

# For anything long or multi-line, prefer stdin: a quoted heredoc puts the
# text through untouched, where an argument goes through the shell's quoting.
vibeknow create --from - --async --output json <<'EOF'
标题行
带 $VAR、`反引号` 和 "引号" 的正文
EOF
```

The text is uploaded as a document named after its opening line, and
everything downstream behaves exactly as it would for a file — `--script-lock`
included, which is how "照着我这段话念" is expressed.

**This is not a way to generate a video from a topic.** The content has to be
the user's; nothing here invents any, and `--prompt` only steers how the
script is written. A request with no material at all ("做个讲量子计算的视频")
has no command — ask for the source.

```
vibeknow create [flags]
```

| Flag | Description |
|------|-------------|
| `--from string` | doc_id, URL, local file path, or `-` for stdin. Required unless `--text` is given |
| `--text string` | Use this text as the source document. Mutually exclusive with `--from`; refused when empty or over 512 KB |
| `--preset string` | Saved bundle of style options: a name under `<config>/presets/` or a path to a `.yaml` file. Supplies defaults only — anything also given on the command line wins. See **Presets** below. |
| `--mode string` | `replica` (PPT 讲解, page-by-page; PDF/PPT sources only), `image` (图解视频, AI illustration per page), `handdraw` (手绘动画). Omit for 灵活创作 (the default line). |
| `--script-lock` | 原稿锁定: narrate the document verbatim instead of writing a script. Orthogonal to `--mode` — combines with any of them. |
| `--engine string` | `pipeline` (default, v=3) or `agent` (v=2, 一键成片). The agent engine has no mode/theme/language branches; combining them exits 2. |
| `--theme string` | Style ID from `vibeknow theme list --mode <mode>` (must match the mode's catalog; default auto-select) |
| `--language string` | Output language for script + narration: `zh-CN`, `en-US`, `es-ES`, `fr-FR`, `pt-BR`, `ja-JP`, `ko-KR` (default: account locale) |
| `--voice string` | Voice: a `#` or `speech_voice_id` from `vibeknow voice list`; pick one matching `--language` |
| `--avatar string` | Talking-head presenter: `sys_<id>` (public, `vibeknow avatar list`) or `ua_<id>` (your own activated avatar). Not with `--mode handdraw` or `--engine agent` (exit 2). |
| `--avatar-position string` | Corner: `top-left`, `top-right`, `bottom-left`, `bottom-right` (default: saved preference, else top-left) |
| `--avatar-size float` | Circle diameter in px at 1080p base, 120–480 (default: saved preference, else 240) |
| `--aspect string` | `horizontal` (16:9, default) or `vertical` (9:16); `16:9` / `9:16` accepted as aliases |
| `--bgm` | Enable background music (default off) |
| `--pages int` | `--mode image` only: exact page count, 1–20 (image-gen cost scales with it; omit for auto) |
| `--images string` | Mandatory image_index picks from `vibeknow doc images`, e.g. `1,3,5` (not for `--mode replica`) |
| `--kb-id string` | Knowledge base owning `--from <doc_id>` (printed by `vibeknow doc upload`) |
| `--async` | Print task_id/session_id and exit without waiting |
| `--preview-dir string` | Write cover/MP4 artifacts here and announce each as a `resource_ready` event |
| `--confirm string` | `action_id` from a previously blocked `--export`, once the user has agreed to the spend |

**Sync mode (default):**
- TTY: colored progress bar showing current stage, elapsed time, ETA. Prints video URL on completion.
- Non-TTY / `--output ndjson`: NDJSON event stream, one JSON object per line.

**Async mode (`--async`):**
- Waits until the backend confirms the run started (seconds), then detaches and exits 0. A run rejected at submit time — bad input, no credits — exits non-zero here instead of handing back a `task_id` for a run that never began.
- `--output json`: outputs `{"task_id":42,"session_id":"s_yyy","schema_version":"1"}` (`task_id` is a number).
- `--output ndjson`: one `{"event":"task.submitted",...}` line.
- Cannot be combined with `--export`: export only starts once the preview is done, which `--async` does not wait for. The combination exits 2.
- The pair is also written to the local run ledger, so `vibeknow video wait` with no arguments reattaches to it.

### Presets

A preset is a YAML file holding a reusable combination of *style* flags, so a
team that has settled on how its videos look does not re-type a dozen options
on every run.

```yaml
# ~/.config/vibeknow/presets/brand-explainer.yaml
schema_version: "1"
name: brand-explainer
description: how our explainers look
create:
  mode: image
  aspect: horizontal
  language: zh-CN
  bgm: true
  voice: "12"
  pages: 8
  images: [1, 3, 5]     # a list, or the string "1,3,5"
```

```
vibeknow create --from deck.pdf --preset brand-explainer
vibeknow create --from deck.pdf --preset ./team/shorts.yaml
```

`--preset <name>` (no separator, no `.yaml`) is looked up in
`<config>/presets/`; anything else is a path. A name that does not exist
exits 2 and lists the names that do — there is no `preset list` command.

**Precedence.** A preset only supplies defaults. Every flag also given on the
command line wins, including an explicit `--bgm=false`. A preset can never
contradict what you typed.

**Keys.** Underscores and dashes are interchangeable (`script_lock` =
`script-lock`). Allowed: `mode`, `script-lock`, `aspect`, `bgm`, `engine`,
`pages`, `images`, `theme`, `language`, `voice`, `prompt`, `avatar`,
`avatar-position`, `avatar-size`.

**Refused, with the reason named:**

| Key | Why |
|-----|-----|
| `export`, `yes`, `confirm` | Authorise a charge. Consent that arrives inside a file someone forwarded to you is not consent — pass these on the command line. |
| `from`, `kb-id` | Identify one run's input, not a reusable style. |
| `async`, `preview-dir`, `output` | Describe one invocation, not the style. |

Any unknown key, unsupported `schema_version`, empty `create:` block, or
value the flag itself rejects (`pages: many`) exits 2 **before** anything is
uploaded, so a broken preset costs nothing. Nothing is ever silently dropped.

Every run says which preset it applied and which keys took effect: a
`preset.applied` event on the structured channel, or one stderr line in text
mode.

## video status

Get current status of a video task.

```
vibeknow video status <task_id> [flags]
```

| Flag | Description |
|------|-------------|
| `--session-id string` | Session ID (default: resolved from the local run ledger; see `vibeknow jobs list`) |
| `--preview-dir string` | Write whatever artifacts exist here and announce each as a `resource_ready` event |

`--preview-dir` on `status` matters for a caller that did not start the run:
the cover exists from the moment the preview does, and the MP4 from the
moment an export has produced one, but only the process that started the run
ever held them. Taken mid-render it delivers nothing and costs nothing.

## video wait

Stream progress for a video task, blocking until terminal state (succeeded/failed/cancelled).

```
vibeknow video wait <task_id> [flags]
```

| Flag | Description |
|------|-------------|
| `--session-id string` | Session ID (default: resolved from the local run ledger; see `vibeknow jobs list`) |
| `--preview-dir string` | Write the cover still here and announce it as a `resource_ready` event |
| `--for duration` | Stop waiting after this long and report where the run got to (e.g. `90s`). Omit to wait for the run to finish |

Behavior is identical to sync-mode `create` once the task is already submitted. Useful after `create --async` or to recover from exit code 6 (stream interrupted).

Exiting 0 from `wait` always means the task genuinely reached a terminal
state. A stream that closes without one exits 6 and carries the
`resend_safe` verdict — see [errors.md](errors.md#exit-6-errordetail).

### `--for`: waiting in bounded steps

A generation takes minutes, and a caller whose own tool times out sooner than
that cannot use an unbounded wait. Polling `video status` instead answers only
`ready: false` — the work row carries no progress until the export stage — so
a caller that checks every ten seconds has nothing new to say each time.

`--for` keeps the event stream, which does carry the stage, and hands it back
when the budget runs out:

```bash
vibeknow video wait 42 --session-id s_x --for 90s --output json
# exit 6, and on stderr:
#   "error": { "detail": {
#     "status": "running", "reason": "wait_budget_expired",
#     "stage": "tts / tts_generate", "waited_ms": 90000,
#     "next_actions": [{ "command": "vk video wait 42 --session-id s_x --for 90s" }] } }
```

Call it again to keep waiting. Nothing is lost between calls and nothing is
billed twice — the run belongs to the backend, not to the process watching it.

Exit **6**, not 0, because 0 on `wait` means the task succeeded, and
`wait && download` must not be sent after a video that is still being made.
`reason` separates a spent budget from the other two things exit 6 covers:

| `reason` | What happened | What to do |
|---|---|---|
| `wait_budget_expired` | The budget ran out; the run is fine | Run the `next_actions` command |
| *(absent)*, stream ended | State unknown — see `resend_safe` | See [errors.md](errors.md#exit-6-errordetail) |
| *(absent)*, task paused | A `task.paused` event arrived | `vibeknow video resume` |

`stage` is the last position on the wire, so it advances between calls. What
it can say, verified against each line:

| Shape | Meaning |
|---|---|
| `outline / script_writing` | Inside that node |
| `past script_writing` | That node finished and nothing has been reported since |
| `past script_writing; drawing (…)` | Same, on the hand-drawn line, where the gap is expected and long |
| `no stage reported yet` | The first seconds of a run, before anything has been emitted |

None is a fault, and none says the run is healthy — silence is not evidence
either way. What they rule out is the mistake that costs money: concluding a
quiet run has died and starting a second one.

**The same `stage` two calls running is normal**, and on the slower lines it
is usual: a single step can outlast several budgets. It is not a signal to
shorten the budget, to poll harder, or to start over.

`message` carries the free-form line that accompanies a node. It is omitted
when it would repeat `stage` — on `--engine agent` there are no nodes, so the
free-form line *is* the stage.

Which nodes actually arrive, per line:

| `--mode` | Reported nodes |
|---|---|
| *(default)* and `--script-lock` | `big_director` `script_writing` `storyboard_plan` `tts_generate` `scene_filling` `bg_images` `cover` `bgm` `video_package` |
| `image` | `style_select` `image_storyboard` `image_gen`, plus `script_writing` `tts_generate` `bgm` `video_package` |
| `replica` | `doc_dissect` `doc_replica_plan` `doc_replica_shoot`, plus `tts_generate` `bgm` `video_package` |
| `handdraw` | `script_writing` `tts_generate` `bgm` `video_package` only. The middle — style, storyboard, drawing, vectorising — emits nothing, and that is where most of the time goes |
| `--engine agent` | No node names at all; free-form progress lines only |

## video export

Render the MP4 for a work. Takes several minutes and **costs credits**.

```
vibeknow video export [task_id] [flags]
```

| Flag | Description |
|------|-------------|
| `--session-id string` | Session ID (default: resolved from the local run ledger, then from the account's most recent run) |
| `--async` | Submit and return; do not wait |
| `--yes`, `-y` | Skip the confirmation gate — only when the user has already authorised this spend |
| `--confirm string` | `action_id` from a previously blocked run |
| `--preview-dir string` | Write the rendered MP4 here and announce it as a `resource_ready` event |
| `--timeout duration` | Local deadline for the sync wait. Does **not** cancel the backend render. |
| `--poll-interval duration` | Fixed poll interval (overrides exponential backoff) |

**The confirmation gate.** With a terminal attached you get a `[y/N]`
prompt. Without one — an agent, CI — the command does not decide for you:
it exits **8** and writes the decision to stdout as `pending_actions`. Show
the user what it costs, then run the action's `resume_command`. See
[errors.md](errors.md#exit-8-blocked-on-a-decision).

**Exit codes.** `0` the MP4 exists; `7` the preview is fine but the render
failed; `6` the local wait was interrupted or timed out (the backend keeps
going — reattach with `vibeknow video export-status`); `8` blocked on the
spend decision.

## video download

Download the rendered video file for a completed task.

```
vibeknow video download <task_id> [flags]
```

| Flag | Description |
|------|-------------|
| `--session-id string` | Session ID (default: resolved from the local run ledger; see `vibeknow jobs list`) |
| `--dest string` | Destination file path (default: `<session_id>.mp4`) |
| `--overwrite` | Overwrite existing output file |

**Note:** The file path is `--dest`. Until 0.8 it was `--output`, which shadowed the global format flag; `--output` now means format here as it does on every other command. Passing a path to `--output` fails with exit 2 and a message pointing at `--dest`.

Supports HTTP Range (resume). If download is interrupted, re-run the same command to resume.

## voice list

List voices: public templates grouped by language, plus the signed-in
user's cloned voices (cloned voices are language-independent).

```
vibeknow voice list [flags]
```

| Flag | Description |
|------|-------------|
| `--language string` | Only show public voices for one locale (e.g. `zh-CN`, `en-US`); cloned voices always show |

**JSON output shape:**
```json
{
  "templates": [{"id": 1, "name": "…", "category": "…", "language": "zh-CN", "speech_voice_id": "sv_…"}],
  "languages": [{"language": "zh-CN", "voices": [{"id": 1, "…": "…"}]}],
  "cloned":    [{"id": 9, "name": "…", "speech_voice_id": "sv_…"}]
}
```

`templates` is the flat view (every public voice, catalog order); pass
either a listed `id` or a `speech_voice_id` to `create --voice`.

## theme list

List visual themes/styles for one creation mode. Theme IDs feed
`create --theme` and must come from the catalog of the mode you create
with (the backend rejects cross-mode themes).

```
vibeknow theme list [--mode default|image|handdraw|replica] [flags]
```

`default` and `replica` share one catalog (the design suite); `image` and
`handdraw` each have their own. Hand-drawn themes include `preview` URLs
(webp/poster, horizontal + vertical).

**JSON output shape:**
```json
{"mode": "image", "themes": [{"id": "…", "name": "…", "desc": "…", "tags": ["…"]}]}
```

## subtitle fonts

List the font families `video set --subtitle-font` accepts. Free, needs no
work, changes nothing.

```
vibeknow subtitle fonts [--output json]
```

This is the complete set, not a sample: the backend validates against the same
catalog it serves here, so a family in this list is accepted and one that is
not is refused. Faces unreadable at subtitle size are already filtered out.

**JSON output shape:**
```json
{"fonts": [{"n": 1, "family": "Noto Sans SC", "label": "黑体 (Noto Sans)"}]}
```

`--subtitle-font` takes either `n` or `family`. `family` is the value the
backend stores and compares byte for byte; `n` is a display index and is the
easier thing to pass.

The catalog records which numeric weights each family ships, but the endpoint
does not return them, so `--subtitle-font-weight` cannot be checked against
the family. Asking for a weight a family lacks is **not** an error — the
renderer falls back to one it has, silently.

## subtitle presets

List the ready-made subtitle looks for `video set --subtitle-preset`. Free,
needs no work, changes nothing.

```
vibeknow subtitle presets [--output json]
```

**JSON output shape:**
```json
{"presets": [{
  "n": 1,
  "name": "白字·黑底",
  "patch": {"color": "#ffffff", "backgroundColor": "rgba(8,8,12,0.68)", "strokeWidth": 0},
  "sets": ["color", "backgroundColor", "strokeWidth"]
}]}
```

`patch` is what applying the preset writes; `sets` names the same fields as a
flat list. **What a preset omits matters as much as what it sets** — omitted
fields keep the work's current value. Note `"strokeWidth": 0` above: that is
the preset actively removing an outline, not a field left unset.

Names are Chinese and contain a middle dot (`·`), which is awkward to type and
worse to get through a shell. Pass `n` instead.

## avatar list

List talking-head presenters: public presets (`sys_<id>`) merged with the
signed-in user's own trained avatars (`ua_<id>`, all states — only
`active` ones are usable). Public presets carry a paired `voice_id`
(the voice their demo uses); pass it to `create --voice` to keep face and
voice matched.

```
vibeknow avatar list [flags]
```

**JSON output shape:**
```json
{
  "public": [{"id": "sys_7", "name": "…", "style": "3d", "gender": "female", "voice_id": "sv_…"}],
  "mine":   [{"id": "ua_12", "name": "…", "status": "active", "usable": true}]
}
```

## video avatar-retry

Retry a work's **failed** avatar scenes. Failed scenes are terminal and
block `video export` permanently until retried; the retry re-renders only
those scenes (script/images/TTS untouched) and bills nothing.

```
vibeknow video avatar-retry [task_id] [flags]
```

| Flag | Description |
|------|-------------|
| `--session-id string` | Session ID (default: resolved from the local run ledger) |
| `--scene int` | Retry only this scene index (default: every failed scene) |

`retry_count: 0` in the output means nothing was failed — if export is
still refused, the scenes are *pending* (still rendering); wait instead of
retrying.

## video pause / video resume

Stop a run that is generating, and continue it later — or retry a *failed*
run from its last checkpoint instead of paying for a whole new one.

```
vibeknow video pause  [task_id] [flags]
vibeknow video resume [task_id] [flags]
```

| Flag | Description |
|------|-------------|
| `--session-id string` | Session ID (default: resolved from the local run ledger) |

Pause keeps the work already done; resume picks up from there rather than
starting over. Reach for pause the moment a run turns out to be wrong —
letting it finish means paying for a video nobody asked for.

`resume` reports which of two things it did:

| `mode` | Meaning |
|--------|---------|
| `paused_resume` | Continued a run the user had paused |
| `failed_checkpoint_retry` | Retried a failed run from its checkpoint; the backend reopens the original bill, so this costs far less than creating the video again |

Three refusals exit **5** and no retry clears them: the run used
`--engine agent` (that line keeps no checkpoint), it was stopped by the
provider's content policy (the same inputs would be stopped again), or it
is neither paused nor failed. Exit **4** (`session busy`) is the one worth
retrying — another pause/resume is in flight on the same session.

## video script

Read what a finished work says, shot by shot. Read-only and free — it
queries stored rows, re-runs nothing, and bills nothing.

```
vibeknow video script [task_id] [flags]
```

| Flag | Description |
|------|-------------|
| `--session-id string` | Session ID (default: resolved from the local run ledger) |

Until this existed, everything readable about a finished work described the
container — title, duration, cover, share link. The narration lived only
inside the generation stream, whose progress events carry a character
*count*, so "what does this video say" had no answer once the run ended.

JSON output:

| Field | Meaning |
|-------|---------|
| `script` | The whole narration stitched in shot order — what "show me the script" wants |
| `scenes[]` | Per shot: `scene_index`, `name`, `script_text`, `duration_sec`, `layout_type`, `status` |
| `scenes[].tts_url` / `srt_url` / `bg_image_url` | Narration audio / subtitles / still for that shot; **omitted entirely when absent**, so a missing key means "not rendered yet" rather than a broken link |
| `scene_count` / `duration_sec` | Totals |

A work with no shots never returns an empty result; it exits non-zero, and
which code says whether waiting will help:

| Exit | Cause | What to do |
|---|---|---|
| 6 | No shots **yet** — usually still generating | Check `video status`, then read again |
| 5 | The work was made with `--engine agent` (一键成片), which renders without a storyboard | Nothing to read, ever. Say so — do not retry |
| 5 | The run failed or was deleted, so it never got that far | Check `video status`; a failed run may be resumable with `video resume` |

The distinction matters because exit 6 tells a caller to come back, and for
the two exit-5 cases there is nothing to come back for.

Run this before `video edit`: the shot numbers it prints are what `--scene`
takes, and the text it prints is what the edit will replace.

## video edit

Replace what one shot says and regenerate it. **Costs credits.**

```
vibeknow video edit [task_id] --scene N --script "…" [flags]
```

| Flag | Description |
|------|-------------|
| `--scene int` | Which shot to change, numbered as `video script` prints them, **from 1** |
| `--script string` | The new narration for that shot |
| `--script-only` | Regenerate the voice-over only; leave layout and background image alone (cheaper) |
| `--yes`, `-y` | Skip the confirmation gate — only when the user has already authorised this spend |
| `--confirm string` | `action_id` from a previously blocked run |
| `--session-id string` | Session ID (default: resolved from the local run ledger) |
| `--preview-dir string` | Write the refreshed preview here and announce it as a `resource_ready` event |

One shot per call. Editing three shots is three calls, three confirmations
and three charges.

**Which regeneration to ask for.** Everything billable on this path is
downstream of the narration actually changing, so the choice is entirely
about how much gets rebuilt:

| | What regenerates | When it is right |
|---|---|---|
| `--script-only` | Voice-over, timeline, presenter | The new text is about as long as the old |
| *(default)* | All of the above **plus** layout, content cards and background image | The new text is a different length, or says something different enough that the visuals no longer match |

`--script-only` is cheaper. It is the wrong choice when the new text is much
longer than the old: nothing re-flows, so the words can overrun the card
they sit in.

**The confirmation gate.** Same mechanism as `video export`, different
boundary. Without a terminal the command exits **8** and writes
`pending_actions` to stdout. The payload carries **both** `from` (what the
shot says now) and `to` (what it would say), because that diff is what the
user is being asked to approve — show them both, not just the replacement.

The `action_id` is bound to that exact diff, plus `script_only`. So:

- Changing a single character of `--script` invalidates the token. An agent
  iterating on wording gets a fresh block for each version — deliberately.
- Approving `--script-only` does **not** authorise the full regeneration.
- If someone else edits the shot between the block and the resume, `from`
  no longer matches and the token stops verifying, rather than silently
  overwriting an edit nobody asked to discard.

Re-run without `--confirm` to get current terms and a current token.

**The rendered MP4 is not withdrawn.** Unlike `video set`, the backend
leaves the old file in place, so `video download` keeps returning a video of
the *previous* narration until the next `video export`. The JSON response
says so as `export_stale: true` with a `next_actions` entry. The preview and
share link show the edit immediately.

**There is no undo.** No endpoint returns a previous version of a shot. Read
the current text with `video script` first if it is worth keeping.

**Exit codes.** `0` the shot was changed; `8` blocked on the spend;
`4` another edit holds the lock on this work (transient — wait and retry);
`5` out of credits; `2` the command line is wrong, and nothing was sent.

Four mistakes are caught locally, before anything is billed or sent —
`--scene` outside the shot range (the message names the range), narration
identical to what the shot already says, empty narration, and a missing
`--scene` or `--script`. All are exit 2 even with `--yes`.

**Not covered by this command.** Changing images, swapping a layout,
deleting a shot, and editing several shots in one charge all exist on the
backend and are not wired up yet.

## video set

Change what a finished video *presents* — music, subtitles, title — without
regenerating it. Free and immediate.

```
vibeknow video set [task_id] [flags]
```

| Flag | Description |
|------|-------------|
| `--bgm on\|off` | Background music |
| `--bgm-volume float` | Music level, 0.1–2.0 (1.0 = unchanged) |
| `--subtitle on\|off` | Subtitles |
| `--subtitle-preset string` | Ready-made look: the `#` or the name from `subtitle presets` |
| `--subtitle-size int` | Subtitle font size in px |
| `--subtitle-color string` | Subtitle text colour, e.g. `#FFFFFF` |
| `--subtitle-font string` | Font family: the `#` or the exact family from `subtitle fonts` |
| `--subtitle-font-weight int` | 100–900 (400 regular, 700 bold) |
| `--subtitle-bg-color string` | Plate behind the subtitle; `transparent` for none |
| `--subtitle-bottom float` | Height above the bottom edge, as a fraction of frame height, 0.02–0.98 |
| `--subtitle-stroke-color string` | Outline colour; only visible with a stroke width above 0 |
| `--subtitle-stroke-width float` | Outline width in px, 0–12 (0 = no outline) |
| `--subtitle-animation string` | Per-line entry animation (12 values; see below) |
| `--title string` | Rename the task |
| `--session-id string` | Session ID (default: resolved from the local run ledger) |

Several can be combined in one call. Only the flags you pass are touched:
subtitle style is read, modified and written back, because the backend stores
the style wholesale and a write-only change would clear the font, weight,
colour, outline and animation along with whatever was being adjusted.

### Prefer `--subtitle-preset` over the individual style flags

Reach for a preset first. Subtitle readability is a *combination*, not a set of
independent settings, and the individual flags let you build combinations that
do not work:

- The outlined looks also set `backgroundColor: transparent`. An outline
  behind a solid plate is invisible.
- The plated looks also set `strokeWidth: 0`. A plate under an outline is
  muddy.

Set one half without the other and the command still exits 0 — nothing on the
wire is wrong, the video just looks bad. A preset carries both halves.

A preset sets only the fields that make up its look. Size, vertical position
and entry animation belong to the video rather than to the look, so they are
left as the work had them. **Individual flags apply on top of a preset**, so
`--subtitle-preset 2 --subtitle-size 52` means "that look, but bigger".

The result is reported back in `applied.subtitle_style` — the complete style
as stored — and the preset's name in `applied.subtitle_preset`.

### Values checked before anything is sent

These are refused locally with exit **2** and no request made, even though the
backend would accept them:

| Flag | Rule | Why locally |
|------|------|-------------|
| `--subtitle-bottom` | 0.02–0.98 | The backend **clamps** instead of refusing. Ask for 1.5 and the call succeeds having stored 0.98, with nothing reporting the substitution. |
| `--subtitle-stroke-width` | 0–12 | Clamped the same way. |
| `--subtitle-font-weight` | 100–900 | The backend does not check it at all; a typo would render at some fallback weight with no error anywhere. |
| `--subtitle-animation` | one of the 12 | Refused server-side with a message that does not name the alternatives. |
| `--subtitle-font` | in the catalog | Refused server-side as `fontFamily not allowed`, which names neither what is allowed nor where to look. |
| `--subtitle-preset` | in the catalog | Same. |

Animation values: `none`, `fade`, `fadeup`, `fadedown`, `slideleft`,
`slideright`, `scale`, `blur`, `pop`, `springup`, `rotate`, `karaoke`. Case is
folded for you. There is no endpoint for this list — it is a copy of a
server-side constant — so an animation added server-side is unusable until the
CLI catches up; the error says "not one this CLI recognises" rather than
"invalid" for that reason.

**Every change except `--title` discards the rendered MP4.** The change has to
be baked into the file, so the old one no longer matches the work. Preview and
share link keep working; the download does not, until the next `video export`
— which bills and asks for confirmation. The response reports this as
`export_invalidated`, with a `next_actions` entry naming the export command.

Exit **5** means this work cannot take that setting (an engine without BGM
volume, a renderer that cannot carry styled subtitles). No value fixes it.

This changes presentation only, and costs nothing. Narration is changed with
`video edit`, which bills. Images and layout still have no command.
