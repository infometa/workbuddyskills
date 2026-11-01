# 曲谱预设：选择、准备与演奏

Read only when using one of the bundled pieces. The sound controls remain in [zen-piano-production.md](zen-piano-production.md); do not duplicate or silently revise the saved smooth preset here.

## Local resources and exact versions

`assets/scores/catalog.json` is the catalog of Chinese names, aliases, source URLs, attribution, tempo settings, duration, note count, range, and transformations. Each piece has an unchanged source `.mid` and an expanded `.score.json` with integer note-on and duration ticks. Source track/channel fields retain voice provenance, but are not a guaranteed right-hand/left-hand label. All voices are performed using the user's selected instrument.

| Preset | Saved quarter-note BPM | Approximate saved sequence | Source and version |
| --- | ---: | ---: | --- |
| C大调前奏曲 | 68 | 2:04 | [Bach BWV 846, Prelude only](https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=5), typeset by Tobias Erbsland |
| 小狗圆舞曲 | 240 | 1:45 | [Chopin Op. 64 No. 1](https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=483), Peters source, Magnus Lewis-Smith |
| 雨滴前奏曲 | 72 | 4:57 | [Chopin Op. 28 No. 15](https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=471), Peters source, Magnus Lewis-Smith |
| 裸体歌舞 No.1 | 60 | 3:54 | [Satie Gymnopédie No. 1](https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=37), Dover source, Evin Robertson |
| 致爱丽丝 | 80 | 2:20 | [Beethoven WoO 59](https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=931), Breitkopf & Härtel 1888 source, Stelios Samelis |
| 婚礼进行曲 | 120 | 6:14 | [Mendelssohn Op. 61, Wedding March](https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=2198), Théodore Dubois organ transcription; typeset by Alexander Brock |
| G大调小步舞曲 | 120 | 0:48 | [Christian Petzold, BWV Anh.114](https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=75); 32-bar source sequence, no added repeats |
| 悲怆奏鸣曲第二乐章 | 36 | 4:03 | [Beethoven Op.13, II. Adagio cantabile](https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=295); Chris Sawer edition, updated by Javier Ruiz-Alma |

The tempos above are saved audition choices, not claims about mandatory composer metronome marks. They use **quarter notes per minute**; 240 BPM in the waltz is 80 three-beat measures per minute. A title such as “Minute Waltz” is not an instruction to compress the piece to one minute. “Full sequence” means this identified source arrangement; the wedding preset is not an orchestral score or a two-hand piano edition.

## Prepare a score locally

Use Python 3; no third-party packages are required. Run from this skill's directory so the commands remain portable after installation. First set `score_output_dir` to a fresh local output directory selected for this task:

```sh
python3 scripts/score_preset.py list
python3 scripts/score_preset.py build '雨滴前奏曲' --seconds 10 --format events --output "$score_output_dir/raindrop-10s-events.json"
python3 scripts/score_preset.py build '致爱丽丝' --format events --output "$score_output_dir/fur-elise-full-events.json"
python3 scripts/score_preset.py build 'C大调前奏曲' --seconds 5 --format events --output "$score_output_dir/bach-5s-events.json"
```

Choose a fresh output filename: the helper refuses to overwrite. Its output report identifies the exact work, scope, duration, note count, effective tempo, and any notes outside the observed keyboard range. Preparing a file does not mean the website has played or recorded it.

- Omit `--seconds` for the remaining saved sequence. `--start` is measured in seconds at the preset's default tempo. `--seconds` is the attack-window length after speed scaling. A note held across the start is included with its remaining duration.
- `--speed 0.8` slows both note onsets and note durations together. `--transpose 2` raises every pitch by two semitones only when requested.
- `--tail natural` retains the last notes' written durations, so a five-second audition may have a slightly longer ending. `--tail clip` enforces the requested time boundary, but can audibly cut a phrase. Prefer musical endings for listening.
- `--format events` (default) creates readable local note data with `metadata` and `notes`. Each note contains `note`, `timestamp`, `duration`, and `velocity`; timestamps/durations are milliseconds and velocity is 0–1. Use these values to plan direct piano-key actions; do not import the file into the site.
- Original controller/pedal messages remain in the bundled source scores. The helper preserves written note lengths and overlaps but does **not** bake CC64/CC67 into releases. The note data is not a claim of exact original pedalling or expressive interpretation.

For a quick Satie melody audition, `--start 12 --seconds 10` starts just before the melody after its four-bar accompaniment introduction. A whole-piece request starts from zero. The wedding source has a brief written rest before its first pickup; preserve it unless intentionally preparing an excerpt.

## Perform through Zen Piano

Use the verified task-owned `https://zenpiano.art/play` tab and preserve any placement the user requested. Read the current WorkBuddy browser/computer-tool documentation, apply the named sound preset, read the prepared note events locally, and perform directly on the piano keyboard using supported key actions. Do not assume a specific host panel or key API. Do not open the MIDI converter or use a file-upload, notation-conversion, or import handoff.

Map pitches to the current keyboard, group simultaneous notes into chords, and preserve the planned rhythm. Use supported holds and releases when available. If the browser controls cannot reproduce required long notes or overlapping voices, explain that limitation and identify any feasible arrangement as an adaptation. Do not detour through the converter, invoke hidden application state, or replace the site sound with local synthesis.

For independent note holds on macOS, follow the optional native keyboard route in [zen-piano-production.md](zen-piano-production.md). `score_preset.py` event output declares milliseconds; the native helper validates this unit explicitly before playing.

An unqualified “悲怆奏鸣曲” names the sonata, not one specific movement. Identify or clarify the movement before performing. The bundled score is the second movement only; it must not replace an explicit first- or third-movement request.

### Optional 25-second Pathétique theme adaptation

`assets/scores/beethoven-pathetique-ii-25s.keys.json` is the tested opening-theme arrangement at quarter-note 40 BPM. It contains 105 key events with independent holds. Two bass notes below C2 are raised one octave; the passage leading into the next section is replaced by an A-flat tonic closing chord. Key release finishes at 23.5 seconds, leaving room for the site's measured decay. Use this identified adaptation when a 25-second second-movement excerpt fits the request; it does not change the skill's default D = 20 or replace the full source score.

Play it afresh through Zen Piano and verify that the downloaded ending fits 25 seconds with the current instrument. Its presence in the package is not a recording or proof of a new performance.

Use a short direct performance and site replay to verify the result before a longer run. Batch note actions against an absolute clock. Respect independent note durations and simultaneous chords; a sequence of uniform short key taps cannot reproduce long bass notes or overlapping voices. Refer to the smooth-preset caveats about sustain and autoplay Release. Do not claim the bundled pieces have been auditioned merely because their data validated.

The observed keyboard is C2–C7 (MIDI 36–96). Bach and the wedding source fit; the other full sequences contain a few notes outside it. Preserve the original source data. Inspect the current site's extended-range or octave controls before deciding an adaptation. `--range-policy error` checks strict compatibility; `--range-policy octave` moves only out-of-range notes by octaves and reports the number changed. Use octave fitting only as an identified adaptation, and preserve the requested key otherwise. Default `keep` does not authorize dropping unsupported notes.

## Provenance, repeat expansion, and licensing

The Mutopia editions above except the wedding edition are marked **Public Domain**. The wedding edition is **Creative Commons Attribution-ShareAlike 4.0**, typeset © 2017 Alexander Brock, based on the Dubois transcription published by Durand & Cie., plate D. & F. 9516. Preserve [its attribution and license](https://creativecommons.org/licenses/by-sa/4.0/) when distributing the source or derived wedding score; the derived `mendelssohn-wedding-march.score.json` is provided under the same license. This does not change the license of unrelated skill code or scores. Transformations below were prepared on 2026-09-10.

The catalog records MIDI SHA-256 hashes and the changes used to create the note sequences. Satie and Beethoven source MIDI contain alternate endings without replaying their corresponding repeat bodies; their `.source.ly` files are included to document expansion:

- Satie: concatenate source quarter-beat intervals `[0,117)`, `[0,93)`, `[117,141)` → 234 quarter beats / 78 measures. Source MIDI has two unmatched F#4 release messages at quarter beat 36; non-sounding orphan releases were ignored. Shared-pitch accompaniment re-articulation otherwise follows that MIDI.
- Beethoven: `[0,12)`, `[0,11)`, `[12,13.5)`, `[13.5,34.5)`, `[13.5,33)`, `[34.5,156.5)` → 187 quarter beats, retaining the pickup and both alternative endings in the repeated sections.

For the other pieces, note order follows the downloaded MIDI. Timing and pitch checks validate data preparation, not every engraving choice, ornament, or an end-to-end website rendition. Use the linked source score when a user identifies a musical discrepancy.
