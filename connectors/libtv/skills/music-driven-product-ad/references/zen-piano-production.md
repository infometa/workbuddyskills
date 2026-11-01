# Zen Piano Production

Use this bundled workflow to turn the approved advertising music direction into a Zen Piano performance and verified local WAV. For auditions, follow the requested duration; the final advertising cue defaults to 20 seconds and must match the video duration.

## Workflow

1. Read the current WorkBuddy browser/computer-tool documentation, then open `https://zenpiano.art/play` with supported UI control, reusing the verified task-owned piano tab when available. Perform directly with piano-key actions actually exposed by that tool; do not copy another host's API names, open the MIDI converter, or add a file-conversion/import step. Treat pasted links containing prose after `/play` as malformed and use the canonical URL.
2. Follow the user's instrument choice. For one of the bundled repertoire presets below, use **三角钢琴顺滑预设** unless the user or advertising direction calls for another sound. Otherwise choose the available Zen instrument that best fits the approved direction. Wait for the instrument-loading overlay to disappear before playing.
3. If a saved piece is requested, load its score through the repertoire section below and preserve its melody, accompaniment, rhythm, and note lengths. Compose original material by default for advertising. Respect the audition or final-cue duration and identify any repertoire excerpt as an excerpt.
4. Start the site's recorder immediately before the first note. Play the piano keys directly with deliberate rhythm, then stop recording after the final note has decayed. Batch timed key actions when practical so tool-call latency does not create a long silent introduction.
5. Verify the site's recording result before export: the recorder should show a nonzero note count and a plausible duration.
6. Choose **Download recording → Download as WAV / 下载为 WAV**. Treat the site's “recording downloaded” toast as evidence that export was triggered, but still verify the file on disk.
7. Identify the newly created `piano-recording-*.wav` in the user's Downloads folder by modification time captured around the export. Do not assume an older similarly named file is the result.
8. Validate that the file is PCM WAV with a plausible duration and nontrivial size. Copy it to the requested folder with a descriptive `.wav` name. Do not overwrite an existing file; add a numeric suffix when needed.
9. If the website added substantial leading or trailing silence, run `scripts/trim_wav_silence.py SOURCE DEST` from this skill's directory. Keep the downloaded source intact and deliver the cleaned copy. Optional `--target-seconds D` pads a shorter, complete cue with silence; it refuses to cut a longer cue. Inspect a quiet ending before relying on silence thresholds.
10. Report the absolute output path, duration, sample rate, and channel count. Analyze the verified WAV before deriving the video rhythm map. Open it in an available browser/audio player for actual replay; offer an absolute file link and use an inline preview only when WorkBuddy demonstrably supports it. File metadata alone does not verify audible note content or synchronization.

## Saved Preset: 三角钢琴顺滑预设

Use this named preset when the user requests the saved grand-piano sound or asks to reuse this preset. It is a starting point for connected melodies with chords or broken-chord accompaniment. Preserve the user's requested piece, style, and duration; the preset does not impose a youthful mood, chord progression, or tempo. It does not replace an explicitly requested instrument or the general default above.

| Control | Saved value |
| --- | --- |
| Instrument | **Grand Piano / 三角钢琴**, distinct from 古典钢琴 |
| Volume / 音量 | **55%** |
| Sustain duration / Sustain 时长 | **Enabled; displayed total 0.6 seconds** |
| Sustain pedal feature / Sustain 踏板 | **Disabled** |
| Autoplay Release / 自动播放Release | **350 ms** |

Apply and verify the values through the site's instrument and Sound / 声音 controls:

- The Sustain slider is an **adjustment**, not an absolute duration. In the observed UI, a 10.5-second base required **−9.9 seconds** to display a **0.6-second total**. Target the displayed total; recalculate the adjustment if the base changes.
- Sustain duration and the pedal feature are mutually exclusive. Re-read the switches and displayed total after changing them. An adjustment near the lower limit can disable Sustain and leave a 0.0-second total; do not mistake that state for the saved preset.
- The UI labels Release as **autoplay-only** and describes manual key release as a fixed 4-second tail. Keep this distinction explicit and follow the current UI if the implementation changes. Do not assume a Release change affects manual playing or an exported WAV without verification.
- A short key tap may still create a very short recorded note. The 0.6-second control is not proof that the recording stores 0.6-second note durations. For disconnected phrasing, consider actual note holds and overlaps as well as Sustain and Release, and replay a short passage to assess the result. Do not claim smoothness from slider values alone.

### Chords and quick comparison

The saved Zen Piano key mapping assigns `q`, `e`, `t`, and `u` to **F3–A3–C4–E4 (Fmaj7)**. Recheck the current page's mapping and the WorkBuddy tool's documented chord/hold support before using it; do not assume a joined-key string means simultaneous key-down. Use a documented multi-key action for block chords and deliberately timed individual presses for broken chords. Add appropriate lower accompaniment under the melody when a fuller arrangement is requested.

For iterative sound comparisons, this user prefers **about 5 seconds per audition**, unless they give another duration (for example, 10 seconds). Keep the notes and rhythm consistent while testing a sound setting; change the arrangement when requested. Preserve an agreed browser-panel placement while the user listens.

## Sustained notes with native keyboard events on macOS

Use this optional route when the documented browser key API provides short taps and the score needs independent holds. It still plays the actual Zen Piano keyboard and records with the site; it does not import MIDI, call hidden page state, or synthesize audio locally.

1. Select the exact task-owned piano tab in Chrome and identify the running Chrome PID through current native inspection. A global foreground key event can land in another app when focus changes; the helper targets the verified Chrome PID instead. Revalidate the active piano tab before a run. This helper requires local macOS, Google Chrome, a Swift compiler with AppKit/ApplicationServices, and existing event-post permission; it is not a Windows or remote-browser implementation.
2. Compile `scripts/zen_key_events_macos.swift` to a fresh temporary build path. Existing Accessibility/event-post permission is required for playback. The helper checks permission and refuses an unrelated process; it does not grant permission or select a browser tab.
3. Use `python3 scripts/score_preset.py build PIECE --format events --output PLAN.json` to prepare a plan with explicit `time_unit: milliseconds`. Alternatively, an arranged key plan uses `time_unit: seconds` and notes with `key`, `timestamp`, and `duration`. Do not mix units. The helper also accepts pitch names such as `C4` and `G#3` in `note` fields.
4. Run `zen-key-events PLAN.json CHROME_PID --dry-run` first. It validates key range, finite positive durations, and incompatible same-key overlaps without sending any events. Resolve re-articulation in the arrangement; do not drop a voice silently.
5. Start the site recorder, then run the same command without `--dry-run`. It schedules independent key-down/up events against an absolute clock and prints start/end timestamps. Shift flags plus explicit Unicode characters preserve black-key inputs such as `(`. Verify the current key map with a short passage before a long take.
6. Export both site WAV and optional site JSON. Match recorded notes by **pitch and onset**, not JSON list order: held notes/chords can be serialized in release order. Compare actual onset spacing and durations; do not infer long notes from Sustain settings. This event route does not reproduce per-note velocity control, pedal performance, or a concert interpretation.

The tested keyboard spans C2–C7; preserve the original key and identify any octave adaptation. If native events are unavailable, use supported browser controls and state the articulation limitation of any short-touch arrangement. Do not substitute imported or locally synthesized music.

For a screen recording requested alongside the performance, use [screen-recording.md](screen-recording.md). The screen file remains silent; the soundtrack comes only from the site WAV.

## Saved Repertoire / 曲谱预设

These presets include local source scores and note sequences with independent onsets, durations, velocities, and simultaneous chords. Read [repertoire.md](repertoire.md) when a piece is requested; use [../scripts/score_preset.py](../scripts/score_preset.py) with `--format events` to select the score, prepare an excerpt or full sequence, and preserve timing when changing speed. Read the note data locally and perform it directly on the Zen Piano keyboard.

| User-facing name | Preset ID | Exact work |
| --- | --- | --- |
| C大调前奏曲 | `bach-c-major-prelude` | Bach, BWV 846, WTC I Prelude No. 1 |
| 小狗圆舞曲 / 一分钟圆舞曲 | `chopin-minute-waltz` | Chopin, Op. 64 No. 1 |
| 雨滴前奏曲 | `chopin-raindrop-prelude` | Chopin, Op. 28 No. 15 |
| 裸体歌舞 No.1 / Gymnopédie No.1 | `satie-gymnopedie-1` | Satie, Gymnopédie No. 1 |
| 致爱丽丝 | `beethoven-fur-elise` | Beethoven, WoO 59 |
| 婚礼进行曲 | `mendelssohn-wedding-march` | Mendelssohn, Op. 61 No. 9; Dubois organ transcription played with piano sound |
| G大调小步舞曲 | `petzold-minuet-g` | Christian Petzold, BWV Anh.114 |
| 悲怆奏鸣曲第二乐章 | `beethoven-pathetique-ii` | Beethoven, Op.13, II. Adagio cantabile |

For this saved library, an unqualified “婚礼进行曲” means the Mendelssohn preset; identify the composer when using it. Do not resolve an explicit request for Wagner's Bridal Chorus to this file. Preserve original pitch by default and inspect the helper's range report before using the observed C2–C7 keyboard. Never silently discard out-of-range notes or call an octave-adapted performance an unchanged original score.

## Useful Key Map

The central white keys are sequential:

`t=C4`, `y=D4`, `u=E4`, `i=F4`, `o=G4`, `p=A4`, `a=B4`, `s=C5`.

Lower white keys include `8=C3`, `9=D3`, and `0=E3`. Shifted symbols and uppercase letters address black keys; use them only when the harmony benefits from accidentals.

A compact C-major contour that can be adapted rather than copied mechanically is:

`C–E–G–E | D–F–A–F | E–G–C5–B | A–G–E–D | C–D–E–G | A–G–E–D | F–E–D–B3 | C`

## Operational Constraints

- A request to record and download authorizes the inbound download; it does not authorize logging in, uploading files, publishing the performance, or deleting prior recordings.
- Prefer shell-based local copying over Finder UI. Preserve the original download when trimming or renaming.
- Do not claim completion from a browser click alone. Confirm the local file exists and inspect its media metadata.
- If WAV export is temporarily disabled, wait for rendering to finish and retry once. If no new local file appears after the site reports success, inspect the Downloads directory and browser state before changing browsers or re-recording.
- If the current browser cannot deliver a verified WAV, use an available WorkBuddy browser/computer tool to select a task-owned Chrome piano tab and record/export there. Preserve a canvas tab only when the user or a `makeVisible=true` handoff requested it. Do not reuse another task's existing recording or assume identical URLs identify the same piano tab.
