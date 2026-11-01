---
name: "music-driven-product-ad"
display_name: "LibTV 音乐驱动产品广告"
display_name_en: "LibTV Music-Driven Product Ad"
description: "Create 20-second music-driven product advertisements with a self-contained Zen Piano-to-LibTV workflow: record and verify the soundtrack, lock one product and one protagonist, then generate a fixed side-view horizontal cross-section that scrolls through connected spaces in one continuous Seedance 2.5 take. Use for premium product or fashion ads built around rightward motion and seamless spatial transitions."
description_zh: "先在 Zen Piano 实际演奏、录音并核验配乐，再用 LibTV 制作默认 20 秒的音乐驱动产品广告，锁定唯一产品与主角，以 Seedance 2.5 完成固定侧视横向空间的一镜到底。"
description_en: "Record and verify a Zen Piano soundtrack, then create a 20-second LibTV product or fashion ad with a consistent product and protagonist in one continuous Seedance 2.5 take."
version: "1.0.2"
author: "LiblibAI"
---

# Music-Driven Product Ad

Use the MCP connection's instructions and live schemas for shared identity, project, model, authorization and task-recovery rules. Ordinary media requests do not require a separate basic-creation Skill.

For WorkBuddy's `DeferExecuteTool`, the outer `params` is the complete target-tool argument object; `create_node` model settings belong in its inner `params` dictionary (`params.model`). Keep arrays, numbers and booleans as real JSON types, not `{item: ...}` objects or strings. Verify image-reference modes against the live schema. Before paid generation, prepare with `run=false`, read back the saved model, mode, references and settings, and preflight the same complete parameters before submitting that node. Do not omit rejected constraints or accept a fallback model to proceed.

WorkBuddy's embedded browser and a separate browser session have independent login states. A green connector or successful web login does not override a failed `doctor`; recover through supported authorization controls and stop repeated deletion attempts if revocation fails.

Direct the advertisement in WorkBuddy. By default, create a 20-second soundtrack on Zen Piano before sending the audio and visual plan to LibTV. Generate one matching 20-second Seedance 2.5 video in a fixed side-view horizontal cross-section: the same product or carrier moves right through 3–5 connected spaces while the camera completes one uninterrupted horizontal take. Use the measured music to time the product release, vertical hard-edge crossings, action accents, catch, and camera stop, then composite the verified WAV in post. Treat LibTV as the video-generation and compositing engine, not as a soundtrack generator or the source of the creative method. Use one project duration D for the soundtrack and video, as defined below.

Read the current WorkBuddy browser, computer-control, file, and command-tool documentation before using those capabilities; use only operations actually exposed in this session. Local helpers require Python 3; optional independent key holds and screen capture require the macOS/Chrome/Swift dependencies described in the bundled references. Check those dependencies before paid generation. A missing browser action or media player is a concrete host limitation to report, not permission to replace Zen Piano with synthetic audio or assume an embedded preview works.

## Duration and revisions

- **Default: D = 20 seconds.** An explicit user duration overrides it for the current project; for example, a 25-second request means both the WAV and final video are 25 seconds. This does not rewrite the saved default.
- Carry D through the arrangement, full visual timeline, model parameter, composition clips, and playback-duration checks. References showing 20-second timing are examples for D = 20; rebuild boundaries for another D from the verified music.
- Keep a complete musical phrase and decay inside D. Do not force a whole composition into the ad or cut a sounding cadence. After preserving the complete performance, a short silent tail may fill the remaining duration.
- When the user changes music after a video is submitted, keep monitoring that exact job. Record and verify the replacement cue, then update the composition; do not resubmit the video solely because the soundtrack changed.
- If the user explicitly asks to start video while music is being revised, prepare and submit the authorized visual job from the agreed plan. Revisit timing once the new WAV is verified, and identify any unverified synchronization. Otherwise finish the music before generation.
- Add a Zen Piano screen recording only when requested. Keep site WAV recording as the audio source; deliver the screen capture as a separate video with **no audio track**. Read [screen-recording.md](references/screen-recording.md).

## Ownership Boundary

- Own the brief, music direction, two-reference identity lock, fixed horizontal cross-section form, rhythm map, continuous movement plan, generation topology, and acceptance criteria in this skill.
- Do not select or delegate creative planning to a LibTV Canvas Skill. Use the typed tools actually returned by the current connection; do not invent legacy Agent routes, Skill-decision fields, or tool parameters.
- Before any LibTV operation, read the MCP connection's instructions for current login, project, spend, monitoring, verification, and browser-handoff rules. This is an operational contract, not the creative workflow.
- Resolve and verify the exact LibTV project before operating on it. Open its canvas only when the user asks to see it or a tool returns `makeVisible=true`; use the exact returned handoff URL through an available WorkBuddy browser or the system browser. Keep an explicitly requested visible canvas accessible. If opening is unavailable, return that URL and mark visibility unverified; visibility is not a precondition for otherwise authorized project operations.
- The soundtrack source is not a user-selectable branch: create, perform, record, and download it from `https://zenpiano.art/play` by following the bundled [Zen Piano production workflow](references/zen-piano-production.md).
- Perform directly on the Zen Piano keyboard with documented browser key actions or permitted native keyboard events. For sustained notes on macOS, use the optional native route in the bundled piano workflow. Do not open the MIDI converter, upload MIDI, or use a conversion/import handoff for performance. Bundled scores may be read locally as note references; they do not add a converter step.
- Do not generate music in LibTV. If Zen Piano cannot be used or its WAV cannot be verified, stop and report the blocker instead of silently substituting another music generator.
- Zen Piano is the required performance platform. Choose an instrument available in its current UI that fits the user and advertisement, including grand piano, electric guitar, or electric bass; do not force every genre onto a piano timbre. Follow an explicit instrument choice. Reuse the bundled **三角钢琴顺滑预设** when requested or suitable.
- Compose original material by default, or arrange a bundled repertoire piece when requested or clearly suited to the brief. Identify the piece and arrangement; a repertoire excerpt is not an original composition. This skill contains the score data, preparation tool, recording workflow, and WAV trimming tool it needs.
- The visual form is fixed unless the user explicitly overrides it: one unchanging product, one carrier moving right, 3–5 spaces sharing a horizon at the lower quarter, one unobstructed vertical hard edge at each join, a fixed wide side-view camera with no vanishing point, and no cuts or dissolves.

## Workflow

### 1. Resolve the advertising brief

Capture or infer:

- product and the visual feature that must remain recognizable;
- objective: awareness, launch, feature proof, conversion, prestige, or social engagement;
- audience, platform, aspect ratio, resolution, locale, and call to action; the default duration is 20 seconds;
- desired brand attributes and forbidden associations;
- available product references, music references, brand assets, copy, and legal constraints;
- product or carrier, its single rightward movement verb, and the physical force that drives it;
- 3–5 connected spaces, a shared horizon at the lower quarter, unobstructed vertical hard-edge seams, wide-shot scale ratios, and the opening/ending action of the same protagonist.

Ask only when a missing choice would materially change the result. Otherwise state a reasonable assumption and continue.

### 2. Define the horizontal scroll system and music

Read [references/music-direction.md](references/music-direction.md) and [references/ad-form-and-rhythm.md](references/ad-form-and-rhythm.md).

The ad form is fixed by [references/ad-form-and-rhythm.md](references/ad-form-and-rhythm.md). Do not choose among montage, product-hero, problem–solution, or other cut-based forms unless the user explicitly requests a different form.

Produce a compact director brief containing:

- constant product, carrier, rightward movement verb, and physical driver;
- 3–5 spaces, a shared lower-quarter horizon, unobstructed vertical hard seams, explicit side-view geometry, wide-shot scale ratios, carrier dynamics, visual height arc, color-temperature arc, and 2–3 specific near-catch actions;
- opening product-loss action, camera-start moment, ending catch, camera stop, product handling, rightward exit, and final empty-frame hold;
- genre family and reference adjectives, without copying a protected recording;
- BPM range, meter, groove density, and sync strategy;
- musical material: original cue or identified repertoire arrangement;
- how the selected instrument expresses lead, rhythmic pulse, bass motion, and atmosphere;
- energy curve and intended contrast points;
- negative sound constraints;
- Zen Piano timbre and performance plan: register roles, pulse, motif, chord voicing, independent note lengths and overlaps, articulation, dynamics, and sustain; include a short audition when choosing a new sound.

All directional motion points right. The camera remains a distant wide side view, level and unchanged in height, distance, and angle. Every space has no vanishing point, the horizon remains at the lower quarter, people stay at 1/4–1/3 of frame height, and the carrier remains small. Product truth, audience, platform, and brand tone determine the spaces, materials, color, and performance details without altering those structural rules.

### 3. Lock the two visual references

Read [references/product-lock.md](references/product-lock.md).

- Use exactly two visual references for Seedance: `@图片1` is the single canonical product image; `@图片2` is one 3:4 head-and-shoulders protagonist identity image used only at the opening and ending.
- With usable uploaded references, analyze and reuse them. Do not redraw them merely for cleanliness. When either asset is missing or unusable, generate it with Seedream 5.0 Pro using the bundled asset Prompt, inspect it, and only then continue downstream.
- Lock the protagonist's face, hair, and skin texture in `@图片2`. Describe one complete outfit separately in the Seedance video Prompt and keep it identical at the opening and ending; do not rely on the portrait to define full-body scale or clothing.
- Write one concise product definition, prevent product text from appearing on other objects, and define the real contact relationship for the opening and ending. Do not provide landmark, lighting, city, or space reference images.

### 4. Create, perform, and analyze the Zen Piano soundtrack

Read [references/zen-piano-production.md](references/zen-piano-production.md) in full and follow it for instrument setup, browser performance, site recording, WAV download, local verification, and silence trimming. Read [references/repertoire.md](references/repertoire.md) only when using a bundled score.

1. Resolve the musical material and a playable D-second structure from the style, BPM, groove, and energy curve. Use original composition by default; for a saved piece, read the bundled repertoire reference and prepare the selected score with `scripts/score_preset.py`. Arrange a coherent excerpt and ending for the advertisement. Do not squeeze a whole multi-minute piece into D seconds or label its arrangement original. A user-supplied track can guide timbre, rhythm, phrasing, or structure but does not replace the required Zen Piano performance.
2. Choose the most suitable available Zen timbre and register. Match the reference's pulse, accents, articulation, and texture with that instrument. Plan melody and bass roles plus block or broken chords where they serve the arrangement; use sparse voicings on low electric bass to preserve clarity. Do not quantize the music to a fixed edit grid or restrict its rhythm for the video.
3. When comparing a new timbre, register, or smoothness setting, perform about **5 seconds per audition**, unless the user specifies another length. Keep the passage consistent across sound comparisons and use their feedback. Reuse an already accepted direction without asking for the same approval again; a short audition is not the final D-second soundtrack.
4. Prepare actual note onsets, durations, overlaps, and simultaneous chords. Reuse the named grand-piano preset from the bundled workflow when selected. A sustain value or autoplay Release setting does not prove that manual taps or exported notes have the intended length. Verify a short replay for connected tails, rhythmic impact, and harmonic clarity using the current supported playback route.
5. Develop the selected direction into the full D-second cue, with its closing phrase and decay planned inside that duration. Open the canonical Zen Piano page, verify the chosen instrument, directly play its keyboard, record the actual performance, and download it as WAV. Prepared note data alone does not satisfy this step.
6. Verify the local WAV's identity, duration, format, size, and audible note content. Trim only unwanted leading/trailing silence while preserving the source file. Revise the performance if a musical ending would otherwise be cut to meet D seconds.
7. Analyze that verified WAV for duration, downbeats, transients, phrases, energy, breaks, and ending cadence. Do not finalize the continuous movement timeline from a provisional or imagined waveform.

Record a timestamp map with musical role as well as time, for example: `00:03.240 — first strong downbeat — product release and camera start`. Preserve this precision in the internal analysis artifact, but do not expose millisecond-level timing or musical language in the model-facing video Prompt.

### 5. Design the continuous scroll for D seconds

Read [references/ad-form-and-rhythm.md](references/ad-form-and-rhythm.md) and [references/seedance-2.5-prompt.md](references/seedance-2.5-prompt.md).

Fill the creative skeleton in [references/ad-form-and-rhythm.md](references/ad-form-and-rhythm.md). Derive the product-release moment, camera-start moment, vertical hard-edge crossings, internal action accents, catch, camera stop, and ending hold from the verified Zen Piano WAV. Music controls the movement timing without introducing cuts.

Keep exact timestamps as source evidence, then round the model-facing visual time blocks to whole seconds. Make adjacent ranges continuous and cover `00:00–D` exactly (for example `00:00–00:25` when D = 25). If two boundaries collapse to the same second, redistribute seconds and simplify internal action beats without removing any planned space. Do not mention music, beats, or sync points in the Seedance Prompt.

For the complete one-take plan specify:

- one unchanging product, one carrier, one movement verb, and one physical driver;
- 3–5 spaces sharing a horizon fixed at the lower quarter and one unobstructed vertical hard edge between each pair;
- a wide shot with people at 1/4–1/3 of frame height and the carrier no wider than 1/3 of a person's height, usually near head size;
- one explicit visible side-view geometry sentence per space, no vanishing point, each landmark appearing once in the background, at most one extra rightward-moving object per space, and 2–3 concrete near-catch actions;
- 3–4 visible carrier dynamics plus material behavior, while its overall direction remains rightward;
- start-static → constant rightward scroll → final stop behavior, with neighboring spaces coexisting at an unobstructed hard-edge seam and no blend or dissolve;
- the exact opening loss and closing catch, product handling, rightward exit, and final 1–2 second empty-frame hold;
- one specific environmental sound for each space and a smooth environmental transition between spaces.

Place hard-edge crossings and major actions on verified structural events in the Zen Piano WAV. Use secondary transients for carrier motion, lighting, or environmental action while keeping the camera speed constant.

### 6. Write one Seedance 2.5 one-take prompt

- Write the prompt in Chinese unless the user explicitly requests English.
- Use the fixed section order in [references/seedance-2.5-prompt.md](references/seedance-2.5-prompt.md): two image-reference declarations, generation goal, framing and scale, carrier motion, direction rules, continuous timeline, consistency rules, and environmental audio.
- Keep the Prompt around 1500–2000 Chinese characters and give each sentence one job.
- Bind the product to `@图片1`. Bind only the protagonist's face, hair, and skin to `@图片2`; specify the full outfit in the video Prompt and repeat it unchanged at the opening and ending.
- When the product contains text, state that it appears only on the product and nowhere else. Give every space a concrete geometry sentence rather than relying on the phrase “side view.”
- Do not put model, duration, aspect ratio, or resolution in the prose specification; set them in the live interface. Whole-second timeline ranges remain in the Prompt to control the continuous action.
- Do not mention Zen Piano, music, beats, or card points. Request no generated background music, voice, or narration; name the environmental sound of each space and ask for smooth transitions.
- Generate one continuous-take video lasting D seconds. Do not create separate per-space nodes, chunks, alternates, internal cuts, or a stitching plan.

### 7. Produce in LibTV

Read [references/libtv-production.md](references/libtv-production.md), then:

1. Verify runtime, login, exact project, and canvas context.
2. Target that exact project using the current schema and retain its returned identity/context. Open the returned canvas URL only on a user request or `makeVisible=true`, using WorkBuddy's available browser handoff.
3. Reuse or create `@图片1` and `@图片2` with Seedream 5.0 Pro, inspect them, then upload those two assets and the verified Zen Piano WAV. Reuse the same verified nodes when resuming, and do not upload scene or landmark reference images.
4. Resolve the live complete model name and schema corresponding to Seedance 2.5; do not ask the user to select a model. Configure D seconds, the selected aspect ratio and resolution, and exactly one output using the live schema.
5. Validate one virtual generation plan and prepare exactly one video node with `run=false`, using the full one-take prompt and the two real visual reference nodes. Read back its saved model, mode, references and output settings, then submit that same verified node through the supported route.
6. Never create a LibTV music-generation job. Obtain or respect the user's authorization only for the single paid video run and any separately authorized reference-image work.
7. Monitor the exact job; do not launch duplicate attempts or per-space generations.
8. Preserve usable generated environmental sounds, composite the verified Zen Piano WAV as background music, then inspect the saved graph and rendered/player output. Use the current `inspect_media` schema for supported inspection and an actual browser/player for playback; do not infer visual or audible acceptance from metadata. Return verified artifact and canvas URLs without assuming WorkBuddy renders embedded media cards.

### 8. Verify and report

Separate three evidence types:

- visual evidence: uninterrupted one-take continuity, distant wide side-view camera without a vanishing point, lower-quarter horizon, unobstructed vertical hard seams without blending, consistent scale, rightward motion, single-use background landmarks, product identity and text containment, and protagonist identity;
- audible evidence: Zen Piano soundtrack presence, environmental-sound continuity and balance, movement alignment, ending, and no unintended silence, generated music, voice, or narration;
- metadata evidence: durations, timestamps, node configuration, model/job IDs, and project identity.

Do not claim audible sync from an `audioVolume` field or claim product fidelity from prompt text. Inspect the relevant output.

Deliver the final artifact or project link, the music/movement rationale, verified duration and format, known limitations, and the smallest useful revision options.

## Critical Gates

- Complete and verify the Zen Piano WAV before video generation unless the user explicitly requests parallel dispatch as described in Duration and revisions. A verified site WAV remains mandatory before final composition and delivery.
- Match the genre and available instrument to the brief; reuse the bundled sound and score presets. Preserve musical note lengths and verify the audible result rather than assuming smoothness from controls.
- Do not ask the user to choose a music-generation source.
- Do not generate or replace the soundtrack in LibTV.
- Use Seedance 2.5 by default without asking the user to choose a model. Deviate only on an explicit user override; if the live Seedance 2.5 route is unavailable, stop and report it.
- Video duration defaults to 20 seconds and must match the Zen Piano recording. The actual recording determines the release, vertical hard-edge crossings, action accents, catch, camera stop, and ending cadence.
- Use Seedream 5.0 Pro for a missing or unusable `@图片1` or `@图片2`, and Seedance 2.5 for the video. Reuse valid user-provided assets instead of regenerating them.
- The fixed visual form is one distant wide side-view horizontal cross-section, 3–5 connected spaces, one lower-quarter horizon, rightward motion, unobstructed vertical hard-edge seams, no vanishing point, consistent small carrier scale, and no cuts or dissolves. Generate it in one video job; do not split or stitch it.
- Bind every LibTV operation to the verified exact project. Canvas opening follows only the user's request or `makeVisible=true`; unavailable opening must be reported separately from tool, persistence, playback, and export results.
- No paid retry after insufficient credits or a failed job without renewed user authorization.
- No silent substitution of a missing product, soundtrack, project, or platform requirement.
- No “completed” claim until the output has been checked at the evidence level available.
