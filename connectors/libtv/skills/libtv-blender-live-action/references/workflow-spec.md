# Workflow specification

Read this file when executing the workflow. It defines the asset prompts, Blender reconstruction checks, camera timing, and Seedance handoff.

## 1. Script breakdown

Create a compact production map before generating:

- scene shell: walls, openings, ceiling, floor, exterior visibility;
- fixed furniture and hero props;
- surface materials, wear, weather, practical lights, color temperatures, and contrast;
- each character's identity, costume, initial position, movement, prop interaction, dialogue, and reaction;
- ordered camera beats and sound events.

Resolve contradictions in favor of the user's latest message. Ask only when a missing choice would materially change the set or blocking.

## 2. Scene views

Choose the image model using the selection rules in [SKILL.md](../SKILL.md), based on current LibTV availability and the needs of each view.

### View 1

Generate one empty cinematic master view. The prompt must specify:

- exact room type and architectural style;
- left/center/right placement of doors, windows, furniture, and hero props;
- camera height, focal length feel, framing, time, weather, light sources, and materials;
- an unobstructed route for the planned camera move;
- `no people, no silhouettes, no reflections of people, no mannequins, no text, no watermark`.

Review view 1 before generating view 2. Do not proceed if the room cannot support the scripted blocking.

### View 2

Reference view 1 directly and request a new angle of the identical room. Choose an angle that reveals geometry hidden in view 1, normally a reverse three-quarter or opposite-corner view. State that this is not a redesign. Lock:

- room dimensions and opening positions;
- furniture count, design, scale, orientation, and spacing;
- prop placement and distinctive wear;
- materials, weather, time, and practical-light positions;
- color palette and exposure.

Reject a result that mirrors the room, adds/removes furniture, moves openings, changes the set style, or introduces people. If regeneration is needed, first check that the retry is within current authorization; do not spend again on a materially different retry without permission.

## 3. Character sheets

Generate one sheet per on-screen character using a model selected under the image rules in [SKILL.md](../SKILL.md). Use a wide horizontal white-background studio layout with three clearly separated depictions and no labels:

- left: frontal facial close-up, neutral expression, shoulders visible;
- center: frontal full body, neutral standing pose, arms relaxed, complete footwear visible;
- right: rear full body, same neutral pose and scale.

Describe age range, ancestry/appearance, facial structure, skin, hair, costume layers, fabrics, footwear, build, and distinguishing features. Require the same person and costume in all three panels. Use even neutral studio light and no environmental shadows, scenery, text, borders, extra limbs, alternate outfits, or props unless a prop is identity-critical.

## 4. Blender reconstruction

First verify a real Blender executable through the local execution capability and obtain its version. Separately verify a visible Blender window and computer-use capability when the user requests to watch the work; do not infer either ability from installation or a background process. Use both scene views as multi-view constraints. Reconstruct a complete navigable set:

- establish floor plan and scale before detail;
- model walls, floor, ceiling, openings, window recesses, fireplace/bookshelves or other architectural anchors;
- place all furniture and hero props at consistent scale;
- add simple materials or neutral value groups sufficient to read forms;
- create practical and window lights matching the reference directions;
- confirm that both reference viewpoints can be approximately reproduced with Blender cameras.

"1:1" means the Blender views should visually match the supplied images in composition, relative proportions, placements, and sightlines. Do not promise metrically exact dimensions when the images provide no measurements; document necessary inferred dimensions and keep them internally consistent.

Represent people with colored body cylinders and gray head spheres. Maintain a visible mapping such as `blue = first entrant`, `red = sofa woman`, `green = bookshelf person`, `yellow = window person`, adjusted to the actual cast. Use simple limb markers only when needed to communicate an action such as opening a door, lowering a glass, replacing a book, or smoking.

Save timeline markers for entrances, camera arrival, prop action, dialogue start/end, reactions, and final settle. Keep the camera collision-free and avoid passing through furniture or walls. Save a real `.blend` with the complete scene, cameras, character mapping and timeline; reopen it and check the rendered preview when local deliverables are in scope. Use low-resolution previews before the final render to avoid spending on an unusable previs. Without a functioning Blender runtime, report the missing dependency and do not fabricate project or render evidence.

## 5. Camera path and performance timing

For each dramatic beat, identify the audience's attention target, the information to reveal, the character action or reaction, the needed angle and shot size, the transition cue, and the duration. Plan these jointly rather than animating a camera tour independently of performance.

1. Select a starting frame that establishes the relevant action, person, or geography.
2. Choose a view that makes the beat readable: face for expression, hands or prop for an important interaction, a wider frame for relationships, or a listener for a meaningful reaction.
3. Synchronize camera arrival, blocking, gaze, action, dialogue, and pauses. Establish the framing before key information is delivered when required; allow deliberate overlapping movement and dialogue when the scene benefits from it.
4. Motivate each shift of attention through action, gaze, sound, a line, a reaction, or a reveal. Choose travel, reframing, a hold, or a cut according to the brief and the set.
5. Shape speed, acceleration, proximity, and holds to the emotional rhythm. End with a framing and duration that make the final beat register.

For face-led dialogue, front or three-quarter views are a useful default, not a mandatory angle for every line. Profiles, backs, off-screen speech, and reaction shots can be intentional. Preserve the script's ordering of action and dialogue instead of forcing all actions before speech. A continuous take is required only when the brief specifies one.

Example only: following an entrance, circling to see the speaker's face, shifting to another character, showing a prop action, and then hearing a line demonstrates coordinated attention and timing. It does not prescribe doors, sofas, bookshelves, windows, four characters, drinking, or smoking for future projects.

Before final render, preview at low resolution and check that each important beat is visible at the right time, intended expressions and actions are readable, camera and characters clear the set, screen direction and geography remain understandable, movement transitions are deliberate, and timing fits the requested duration.

## 6. Seedance 2.5 handoff

Use the exact bound project for uploading the real white-model video and creating a new video node; do not overwrite a prior failed or approved result. Discover the current model schema and use Seedance 2.5 video-editing mode with its supported reference fields. Prefer the model's source-duration/auto setting for a full-length white-model reference when the schema offers it; otherwise resolve an explicitly supported duration and preserve the user's requested timing. If the current schema cannot support all required references, mode or duration, report that gap before generation. Connect:

- white-model video: motion, blocking, action timing, camera path, and shot duration reference only;
- scene view 1: primary set appearance, materials, palette, and lighting reference;
- scene view 2: secondary spatial-consistency and hidden-geometry reference.
- character sheets: identity, face, hair, costume, body proportion, and rear-view continuity references; do not copy the white studio background into the scene.

The final prompt must explicitly separate those responsibilities and forbid inheriting white-model geometry, cylinders, spheres, proxy colors, flat shading, or simplified furniture.

Include:

- stable mapping from each proxy color to the corresponding photoreal character, using the approved character-sheet details;
- time-coded performance beats, including the intended relationship between camera framing, character movement, prop action, dialogue, and reactions;
- room architecture, furnishings, hero props, weather, practical lights, color temperature, contrast, lens feel, texture, and film treatment;
- exact dialogue language and lines when dialogue generation is requested;
- diegetic ambience and effects;
- exclusions for duplicate people, identity drift, malformed anatomy, unwanted text, subtitles, logos, watermarks, narration, and music when not requested.

Run a read-only generation preflight first. Confirm that the resolved model is Seedance 2.5, mode remains video editing, all intended video/image references and node identities are usable, duration follows the white-model source, and requested resolution/sound settings are effective. Bind every call to the exact project and retain the accepted task identity and stable idempotency key. Generate once under current authorization, then follow the same accepted task rather than submitting duplicates. Use the task and long-call rules in [SKILL.md](../SKILL.md): respect disabled inline execution, continue the original running call, and only recover status after it ends or disconnects. Read back the persisted output node, all reference connections, generation state, output URL and available media metadata before delivery.

## 7. Review and correction loop

Provide the verified canvas node and playable result through WorkBuddy's available presentation or file capabilities. Open the canvas only on the user's request or a tool's `makeVisible=true`; an ordinary verified delivery link does not claim the canvas has been displayed. If no embedded player exists, provide a verified resource link or real local file. Actually view the reference and output frames and play the videos before judging quality; report any unavailable visual or audio inspection. Review in this order:

1. set fidelity to both scene views;
2. camera path and timing against Blender previs;
3. character identity and costume consistency;
4. framing and timing make each intended narrative beat readable;
5. performance and prop actions;
6. lighting, weather, continuity, lip sync, and sound.

Record the user's correction in the narrowest relevant stage. Rebuild Blender only for geometry, blocking, or camera-path defects; revise Seedance prompt/reference weighting for appearance or performance defects. Never regenerate merely because technical metadata is unknown.
