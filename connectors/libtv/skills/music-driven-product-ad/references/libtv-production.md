# LibTV Production

Use LibTV for image/video generation, canvas operations, compositing, and export after WorkBuddy has created, recorded, downloaded, and analyzed the final Zen Piano soundtrack of duration D. Use Seedream 5.0 Pro for missing product or protagonist assets, then generate one Seedance 2.5 video of the same duration: a distant wide side-view horizontal cross-section that scrolls through 3–5 connected spaces in one continuous take without cuts or dissolves.

## Preflight

1. Read the workflow digest in the MCP connection's instructions in full for the current route.
2. Run the required LibTV doctor/runtime check.
3. Resolve the exact user, space, project, canvas, and current node context. Never infer project identity from an old URL alone.
4. Reuse the current project when the user is continuing prior work.
5. Target the exact project with the current `target_project` schema, preserve its returned context, and inspect current resources/revision before changes. Check the browser/player and local-script capabilities needed for this workflow before paid generation.

## Canvas Handoff in WorkBuddy

- Open the canvas only when the user requests it or a tool returns `makeVisible=true`. Do not make browser visibility a mandatory production step.
- Use the exact returned handoff URL for the verified project; include a focused node only when the current schema supports it.
- Read the available WorkBuddy browser/computer-tool documentation, reuse the verified same-project tab when possible, and otherwise open the URL through an actually available browser. Do not assume a particular panel, embedded canvas, MCP App, or media-card renderer exists.
- Preserve the returned project, space, launch-surface, focus, and directive parameters.
- Visible canvas handoff does not itself authorize a paid generation.
- If the exact canvas cannot be made visible, return the handoff link and mark visibility unverified. Continue separately authorized typed operations when feasible; do not describe a tool receipt as proof of a visible canvas or playable result.

## Creative Ownership

The creative plan comes from this skill's [SKILL.md](../SKILL.md).

- Do not select a LibTV Canvas Skill for style, rhythm, storyboard, or production planning.
- Prefer typed or deterministic LibTV operations for uploads, nodes, edges, generation, compositing, inspection, and export.
- Use only the current connection's exposed tools and input schemas. Do not start a legacy Canvas Agent or invent Skill-decision arguments to stand in for a missing typed capability. Report the exact capability gap and preserve the plan/assets.

## Assets

Upload and verify exactly these project inputs:

1. `@图片1`: the single canonical product image, reused when valid or generated with Seedream 5.0 Pro from the bundled asset Prompt.
2. `@图片2`: one 3:4 head-and-shoulders protagonist portrait, reused when valid or generated with Seedream 5.0 Pro; it locks face, hair, and skin only and is used at the opening and ending.
3. The verified D-second Zen Piano WAV for post-generation compositing.

Describe the protagonist's full outfit in the Seedance video Prompt rather than relying on the portrait. Do not upload landmark, lighting, room, or city reference images; describe them in text so their original camera angle cannot override the required side-view cross-section.

Verify media IDs, formats, image dimensions, and WAV duration. Preserve the reference ordering so `@图片1` and `@图片2` resolve correctly in the Seedance prompt. Reuse existing verified nodes when resuming.

## Seedance Generation

- Resolve the live complete model name corresponding to Seedance 2.5 and inspect its current schema. Do not guess model keys or parameter names.
- Configure D seconds (20 by default, or the explicit project duration), plus aspect ratio, resolution, and one output in the live parameter fields. Keep those specifications out of the prose Prompt.
- Fill [seedance-2.5-prompt.md](seedance-2.5-prompt.md) with the creative skeleton and continuous visual time ranges derived from the music analysis.
- The Prompt must describe one continuous take with no cuts, blends, dissolves, or semi-transparent overlaps. Do not call its time blocks shots, scenes to be edited together, montage sections, or transitions.
- Attach only the real `@图片1` product node and `@图片2` protagonist node as visual references.
- Require a distant wide shot, no vanishing point, a horizon fixed at the lower quarter, people at 1/4–1/3 of frame height, and a carrier no wider than 1/3 of a person's height and usually near head size.
- Join spaces with an unobstructed vertical hard edge. Never place a pole, tower, bridge structure, vehicle, or other foreground object over the seam. Each landmark appears once in the background and never reappears as a foreground fragment.
- Ask Seedance for no background music, voice, or narration. Retain the named environmental sounds for each space with smooth cross-space transitions.
- If the current schema offers a separate Negative Prompt field, use it for no cuts or dissolves, no reverse motion, no vanishing point or camera changes, no seam obstruction, no duplicated landmarks, no scale drift, no product duplication, deformation, or text leakage, no protagonist drift, no subtitles, and no watermark. Do not invent unsupported fields.
- Validate one virtual generation plan with the exact model, parameters, prompt, group, and references before submission.
- Create and run exactly one video node. Do not make one node per space, generate chunks, variants, or a stitching plan.

## Spend and Retry Boundary

- Use paid generation only for the single planned advertisement and any separately authorized creation of the two canonical reference images.
- Before the paid run, establish the user's authorization or rely on authorization already explicit in the conversation.
- Track the exact job/run ID and monitor it. Do not submit a duplicate because a poll is unchanged.
- A transport timeout is not proof that generation failed. Read the exact persisted node/task before deciding the state; a job can complete after the waiting call times out.
- If credits are insufficient, stop, preserve the session and assets, and report the exact state.
- A failed or defective result does not authorize a paid retry. Diagnose the prompt or reference issue and obtain renewed authorization before another full run.

## Post-Generation Compositing

- Keep the generated environmental sound bed when it is clean and relevant.
- Add the verified Zen Piano WAV as the background music after video generation.
- Align the first strong musical event with the product leaving the protagonist and the camera starting to move.
- Align phrase boundaries with the product crossing unobstructed vertical hard edges, without creating edits.
- Align the final cadence with the catch, camera stop, product handling, and rightward exit.
- Balance environmental sounds beneath the music; remove accidental generated music, voice, or narration if present.
- Check soundtrack start offset, gain, fades, ending, and the final 1–2 second empty-frame hold.
- Save the graph/composition state before final render or export.

### Deterministic composition and observed mute behavior

- Resolve the current typed timeline schema. Include real `sourceNodeId`, clip `type`, `startTime`, `duration`, `sourceOffset`, and valid `sourceDuration` for each clip. Set both final clips to D where appropriate.
- Plan the edit, apply against the returned revision, and read back the result. If the revision changed, re-read the current timeline and preserve intervening user edits.
- In a tested LibTV route, `videoAudioMuted: true` and `videoAudioVolume: 0` were persisted but did not mute the rendered original audio. If rendered evidence confirms this on the current route, set the video clip's gain directly (for example `decibel: -60`) when the original sound should be effectively muted. A finite gain is attenuation, not mathematical silence. Keep clean, relevant environmental sound when possible; if it cannot be separated from unwanted generated music, state its removal instead of claiming to preserve it.
- Lower the music gain only as the actual mix needs. Values such as -2 dB are starting points, not mandatory defaults. Decode or listen to the rendered output to confirm the intended soundtrack and ending; configuration alone is not evidence.
- Running a `video-clip` composition may create a separate final video node. Follow the returned output node and task ID; do not expect the editable clip node to acquire the final URL.

### Bounded visual review

For character, one-take motion, or product continuity review, inspect the current `inspect_media` schema and use only the bounded, non-generative inspection it actually supports. Use the returned playable artifact in an available browser/player to review the full sequence and audio. If the tool returns only metadata or the host cannot expose playback evidence, state the missing visual/audio check instead of inventing an analysis tool or treating a result card as acceptance. Treat a visible character and a physically continuous one-take camera as separate checks; a vertical split-screen wipe does not satisfy the latter. Sampled frames may not prove hand-to-fabric contact or uninterrupted motion. Report unresolved limitations without automatically paying for another generation.

If the user changes only the score while the video is running, keep that exact video job and replace the verified WAV in composition. Timing planned from a previous cue is not automatically synchronized to its replacement.

## Verification

Inspect the final canvas state and rendered/player output.

- **Continuity:** one uninterrupted take, no cuts, dissolves, flashes, semi-transparent overlaps, or stitched transitions.
- **Camera:** distant wide side view with no vanishing point; constant height, distance, lower-quarter horizon, scale, and horizontal angle.
- **Direction:** camera, carrier, people, gaze, traffic, animals, and exit all move or face right; only the background scrolls left as a result of camera motion.
- **Space joins:** every neighboring pair coexists briefly in the same frame, separated only by a straight, unobstructed vertical hard edge; both horizons align and no landmark fragment covers the seam.
- **Scale:** people stay at 1/4–1/3 of frame height; the carrier stays small and consistent across every space.
- **Identity:** exactly one product remains faithful to `@图片1`, and its text appears nowhere else; the opening and ending protagonist remain faithful to `@图片2` and wear the same Prompt-defined outfit.
- **Audio:** the Zen Piano soundtrack is audible, environmental sounds are subordinate and continuous, and no unintended music, voice, narration, silence, or truncation remains.
- **Metadata:** correct project, D-second playback duration, aspect ratio, resolution, model/version, node wiring, asset IDs, job status, timestamps, and export state.

Configuration proves intent, not perception. Verify the rendered result itself before claiming continuity, product fidelity, protagonist identity, or audible sync.

## Handoff

Return the exact project/canvas reference, generated output, verified format and duration, soundtrack identity, and any failed or provisional checks. Supply the actual artifact URL or absolute local file link, use previews only when WorkBuddy demonstrably supports them, and report browser/player verification separately from configuration and persistence. Describe revision options in terms of product lock, protagonist consistency, rightward motion, camera invariance, space joins, pacing, environmental sound, or music mix.
