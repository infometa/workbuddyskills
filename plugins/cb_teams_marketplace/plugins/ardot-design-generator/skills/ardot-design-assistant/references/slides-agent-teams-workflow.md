# Slides Creation Workflow — Agent Team Collaborative Presentation Design

Produces visually rich, content-dense, stylistically unique slides through a three-member Agent Team workflow. Each member has a dedicated role: **Researcher** handles topic research and material collection, **Designer** generates slides on the ardot canvas, and **Reviewer** audits visual quality and layout correctness. They communicate via `SendMessage` and coordinate through the shared task list.

---

## Mandatory Design Rules

These rules govern the visual quality of every slide and must be followed throughout all phases. Violating any of them will produce slides that look amateurish on a projector or large screen.

### Rule 1: Large Typography — Fill the Container

Slides are viewed on large screens, often from a distance. Small text is unreadable. Every text element must be sized generously and fill its container space rather than floating in emptiness.

| Text Level | Minimum Size | Recommended Range | Usage |
|------------|-------------|-------------------|-------|
| Slide Title | 56px | 56–80px | Main heading per slide |
| Section Heading | 40px | 40–56px | Sub-sections, card titles |
| Body / Description | 28px | 28–36px | Paragraph text, bullet points |
| Caption / Label | 22px | 22–28px | Axis labels, footnotes, tags |
| Large Data Number | 56px | 56–96px | KPI, statistics, hero numbers |

Enforcement:
- No text node may have `fontSize` below 22px — if content requires finer text, summarize or split across slides instead
- Titles should occupy at least 60% of the horizontal width of the slide
- Body text containers should use `width: "fill_container"` to stretch across available space
- Data/KPI numbers should be the visual anchor of their slide — make them dramatically large (72–96px)
- When in doubt, go bigger — oversized text on slides is always better than undersized

### Rule 2: Unified Visual Style — Rich Backgrounds

Every content slide (excluding cover and closing) must share a cohesive visual language. Pure solid-color backgrounds look flat and unprofessional on presentation screens.

Background treatment requirements:
- **Gradient backgrounds**: Use subtle linear or radial gradients as the base layer for content slides. The gradient should be gentle (e.g., a 5–10% brightness shift across the slide) to add depth without distraction
- **Decorative background layer**: Add at least one subtle decorative pattern on every content slide — dot grids, geometric shapes, soft wave lines, diagonal hash, or concentric circles at very low opacity (0.03–0.08)
- **Consistent palette**: All slides must pull from the same color palette obtained via `fetch_style_guide`. Background gradients should use light/tint colors from the style guide
- **Dark accent slides**: 1–2 slides per deck should use a dark/inverted background for rhythm and emphasis (e.g., section breaks, key data reveals)
- **Card surfaces**: When using cards on slides, give them a distinct surface color with subtle shadows to lift them from the background

Forbidden:
- Pure white (`#FFFFFF`) or pure black (`#000000`) backgrounds on content slides
- Each slide using a completely different color scheme from its neighbors
- Overly busy or high-contrast patterns that compete with content for attention

### Rule 3: Decorative Elements & SVG Data Visualization

Slides should feel visually rich and layered, not like text pasted on rectangles. Decorative elements add polish, and SVG charts communicate data far more effectively than text or numbers alone.

**Decorative elements** — every slide should include at least 2–3 of these:
- SVG icons in styled containers (circles, rounded rectangles, hexagons) with background tint fills
- Decorative divider lines, accent bars, or geometric separators between sections
- Subtle background shapes — large circles, rectangles, or blobs at very low opacity as depth elements
- Tag/badge elements for categories, labels, or status indicators
- Numbered step indicators for sequential content
- Accent border or sidebar stripes using the Primary or Accent color

**SVG data visualization** — whenever the slide content involves data, statistics, trends, comparisons, or timelines, generate inline SVG charts rather than just showing numbers:

| Data Type | Recommended Chart | When to Use |
|-----------|------------------|-------------|
| Trends over time | Line chart | Revenue growth, user adoption, progress |
| Part-of-whole | Pie / Donut chart | Market share, budget allocation, composition |
| Category comparison | Bar / Column chart | Feature comparison, survey results |
| Sequential process | Timeline | Project roadmap, history, milestones |
| Distribution | Horizontal bar chart | Rankings, score distributions |
| Relationship | Scatter / Bubble | Correlation, multi-dimensional data |
| Progress | Progress bars / Radial | Completion %, KPI progress |

SVG chart construction rules:
- Build charts as frame nodes containing SVG path/line/rect/circle children — not as images
- Use the style guide's color palette for chart colors (Primary, Accent 1, Accent 2)
- Include axis labels (≥22px), data labels on key points, and a clear legend
- Charts should occupy at least 40% of the slide area when they are the main content element
- Keep SVGs clean: use `strokeWidth: 2–3`, rounded line joins, and adequate spacing between elements
- For pie/donut charts, use distinct colors from the palette and label each segment
- For line/bar charts, include gridlines at low opacity (0.1) for readability

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│  Team Lead (Main Agent)                                      │
│  - Creates the team and spawns 3 members                     │
│  - Orchestrates phases: Setup → Research → Generation+Review │
│  - Performs canvas setup (Phase 2)                            │
│  - Monitors progress via task list                           │
│  - Shuts down team when complete                             │
├──────────────────────────────────────────────────────────────┤
│  Team Members                                                │
│                                                              │
│  A: slide-researcher                                         │
│     - Phase 1: Clean workspace, research topic, collect      │
│       images, create slide plan                              │
│     - Output: .slide-task/{search-data.md, plan.md, images/} │
│     - Terminates after completion                            │
│                                                              │
│  B: slide-designer                                           │
│     - Phase 3a: Generate all slides on ardot canvas          │
│     - Reads plan + research data, calls batch_edit           │
│     - Does NOT call capture_screenshot or capture_layout     │
│     - After each slide, notifies C (fire-and-forget) and     │
│       immediately moves to the next slide — does NOT wait    │
│     - Phase 3b: After all slides are generated, reads        │
│       `.slide-task/fix-list.md` and fixes issues per slide   │
│                                                              │
│  C: slide-reviewer                                           │
│     - Phase 3: Review slides generated by B asynchronously   │
│     - Calls capture_screenshot and capture_layout            │
│     - Checks Mandatory Design Rules compliance               │
│     - Writes all issues to `.slide-task/fix-list.md`         │
│       (does NOT send fixes back to B immediately)            │
│     - After all slides are reviewed, notifies B to begin     │
│       the fix phase                                          │
└──────────────────────────────────────────────────────────────┘
```

**Data flow**: A writes files → Team Lead reads plan, sets up canvas → B generates slides sequentially, sending frame IDs to C without waiting → C reviews each slide asynchronously and records issues in `.slide-task/fix-list.md` → after B finishes all slides and C finishes all reviews, C notifies B → B reads fix-list.md and applies fixes slide by slide (max 3 revision rounds per slide).

---

## Phase 0: Team Setup (Team Lead)

The Team Lead (main agent) creates the team and spawns all three members.

### 0.1 Create the Team

Use `TeamCreate` to create a team named `slide-team`.

### 0.2 Spawn Team Members

Spawn three teammates using the `Agent` tool with the following configurations. All members use the same model as the main conversation (do NOT specify a different model).

**Member A — `slide-researcher`**:
```
name: "slide-researcher"
team_name: "slide-team"
max_turns: 50
```

**Member B — `slide-designer`**:
```
name: "slide-designer"
team_name: "slide-team"
max_turns: 200
```

**Member C — `slide-reviewer`**:
```
name: "slide-reviewer"
team_name: "slide-team"
max_turns: 100
```

### 0.3 Create Initial Tasks

Before spawning members, create tasks in the shared task list:

1. **"Clean workspace and research topic"** — assigned to `slide-researcher`
2. **"Create slide plan"** — assigned to `slide-researcher`, blocked by task 1
3. **"Canvas setup and frame creation"** — assigned to Team Lead, blocked by task 2
4. **"Generate all slides"** — assigned to `slide-designer`, blocked by task 3
5. **"Review all slides"** — assigned to `slide-reviewer`, blocked by task 3 (starts when canvas is ready, works in parallel with designer)

---

## Phase 1: Research & Preparation (slide-researcher)

### Prompt for slide-researcher

```
You are a presentation research specialist on the `slide-team`. Your job is to research and plan a slide presentation. You will NOT generate any slides — only prepare all the materials needed. Do not include any style decisions, content preprocessing, or layout planning in `.slide-task/plan.md` — only produce the outline and image resource index.

Topic: [USER_TOPIC]
Slide count: [USER_SPECIFIED or "auto (10–20 based on research richness)"]
Additional requirements: [ANY_USER_CONSTRAINTS]
Workspace path: [WORKSPACE_PATH]

Execute the following tasks in order. Use the shared task list to track progress.

## Task 1: Clean Workspace & Research

1. Check if `.slide-task/` directory exists under the workspace, if exists, delete it then Create a fresh empty `.slide-task/` directory and Create `.slide-task/images/` subdirectory for resource images.
2. Use web search to gather comprehensive materials related to the presentation topic:
   - Analyze the topic — identify key themes, subtopics, data points needed
   - Search and collect information, save organized research data to `.slide-task/search-data.md`
   - Don't search too many sources, reference only 5-10 sources is enough, and make sure not spend too much time on searching
3. Collect images — Use web search to find relevant images(preferred) or generate images using `image_gen` tool, save to `.slide-task/images/`. If the `image_gen` tool is unavailable and no suitable images can be found on the web, mark them in the Task 2 image index for later generation via the `batch_edit` G("ai") operation, and provide the image prompt. At least 8 images for all slides. Make sure all images fit the main theme and rename them to clean filenames.

## Task 2: Create Slide Plan

1. Determine slide count:
   - If user specified a count → use that (cap at 100)
   - If not specified → based on research richness, produce 10–20 slides
2. Save the plan to `.slide-task/plan.md` with this structure:

```markdown
# Slide Outline

## Topic: [Main Topic]
## Total Slides: [N]
## Narrative Flow: [Brief description of the story arc]

---

## Outline

1. **Cover** — [Main title and subtitle direction]
2. **[Section Name]** — [What this slide should convey, key message]
...
N. **Closing** — [Closing message direction]

---

## Image Index

| # | Filename | Description | Recommended Slide(s) | Usage Suggestion |
|---|----------|-------------|----------------------|------------------|
| 1 | `images/photo1.jpg` | [Brief description] | Slide 2, 5 | Background image or split-layout visual |
...

### Slide Design Notes
- Every fontSize must be larger than 22px
- Every slide must have a clear title, subtitle, and page number
- Plan which slides should include SVG charts and what data they visualize
- Note which data points from research are best presented as charts vs. text
```

3. After finishing, send a message to the team lead confirming all files are ready:
   - `.slide-task/search-data.md` — research data
   - `.slide-task/plan.md` — slide plan
   - `.slide-task/images/` — resource images
4. Mark your tasks as completed in the task list

### Completion

When slide-researcher finishes, it sends a message to the Team Lead confirming all preparation files are ready, then the Team Lead proceeds to Phase 2.

---

## Phase 2: Canvas Setup & Frame Creation (Team Lead)

After slide-researcher completes, the Team Lead performs canvas setup directly (not delegated).

### 2.1 Get Editor State

Call `fetch_editor_state` with `includeSchema: false` to get the current page ID.

### 2.2 Read the Plan

Read `.slide-task/plan.md` to determine the total slide count N.

### 2.3 Allocate Canvas Space

Calculate total space needed:
- Each slide frame: **1920 × 1080** px
- Grid layout: **max 5 slides per row**
- Horizontal gap between slides: **100px**
- Vertical gap between rows: **100px**

For N slides:
- Rows = ceil(N / 5)
- Columns per row = min(N remaining, 5)
- Total width = columns × 1920 + (columns - 1) × 100
- Total height = rows × 1080 + (rows - 1) × 100

Call `locate_available_space` with the calculated total dimensions to find placement.

### 2.4 Create All Slide Frames

Use `batch_edit` (max 25 ops per call) to create all slide frames at once.

For slide at grid position (row, col):
- x = space.x + col × (1920 + 100)
- y = space.y + row × (1080 + 100)

```javascript
// Example: creating slide frames in a batch
slide1=I(document, {type: "frame", name: "Slide 1 - Cover", width: 1920, height: 1080, fill: "#FFFFFF", padding: {left: 48, right: 48, top: 36, bottom: 16}, clipsContent: true, x: X1, y: Y1})
slide2=I(document, {type: "frame", name: "Slide 2 - [Title]", width: 1920, height: 1080, fill: "#FFFFFF", clipsContent: true, x: X2, y: Y2})
// ... continue for all slides
```

### 2.5 Record Frame IDs

Append all created frame IDs to `.slide-task/plan.md` in a new section:

```markdown
## Frame IDs

| Slide # | Frame ID |
|---------|----------|
| 1 | abc123 |
| 2 | def456 |
...
```

### 2.6 Unblock Designer and Reviewer

Mark the "Canvas setup" task as completed. Send a message to `slide-designer` with the frame ID mapping and instructions to begin generation. Send a message to `slide-reviewer` that canvas is ready and to stand by for review requests from `slide-designer`.

---

## Phase 3: Slide Generation & Review (slide-designer + slide-reviewer)

### Prompt for slide-designer

```
You are a presentation design specialist on the `slide-team`. Your job is to generate visually rich slides on the ardot canvas. You work alongside a reviewer (`slide-reviewer`) who asynchronously audits your work and records issues to a shared fix list. Don't forget to follow the Mandatory Design Rules, and NEVER call `capture_screenshot` or `capture_layout` — that is the reviewer's job.

Workspace path: [WORKSPACE_PATH]

IMPORTANT — Before generating ANY slides, you MUST:
1. Read `references/design-rules.md` carefully — understand all ardot design constraints
2. Read `references/ardot-workflow.md` — understand batch_edit operation syntax, binding rules, and all tool parameters
3. Call `fetch_editor_state` with `includeSchema: false` — obtain the ardot editor state and batch_edit tool description
4. Call `fetch_guidelines` with topic "slides" — obtain slide-specific design rules
5. Read `rules/style-guide-tags.md` to see the available tags (static list — do **not** call `fetch_style_guide_tags`), select 5–10 fitting tags, then call `fetch_style_guide` with those tags — obtain visual style inspiration (color palette, typography, spacing, decorative patterns)
   - If the returned style guide is not suitable for the topic, discard it and request a new one
6. Read `.slide-task/plan.md` and `.slide-task/search-data.md` into context

## Your Responsibilities

You operate in two distinct phases — the Generation Phase first, then the Fix Phase.

### Phase 3a — Generation (fire-and-forget notification to reviewer)

- Generate slides using `batch_edit` (max 25 ops per call)
- Use `upload_images` to set images from `.slide-task/images/` to slide frames, must use all images.
- Follow the Mandatory Design Rules strictly:
  - Title fontSize ≥ 56px, body fontSize ≥ 28px, no text below 22px
  - Apply gradient + decorative pattern backgrounds (no flat solid colors)
  - Include 2–3 decorative elements per slide
  - Generate SVG charts for any data/statistics instead of plain text numbers
- DO NOT call `capture_screenshot` or `capture_layout` — that is the reviewer's job
- After completing each slide's generation, send a single fire-and-forget message to `slide-reviewer` with:
  - The slide frame ID
  - The slide number and title
  - A brief description of what was generated
- DO NOT wait for a response — immediately proceed to the next slide
- Continue until all slides in `.slide-task/plan.md` are generated
- After generating the last slide, send a completion message to `slide-reviewer` indicating "all slides generated, waiting for fix-list"

### Phase 3b — Fix (driven by fix-list.md)

- Wait for a message from `slide-reviewer` saying all reviews are complete
- Read `.slide-task/fix-list.md` into context
- For each slide entry in the fix-list (skip entries marked PASS):
  1. Apply the fixes using `batch_edit` (and other needed edit operations)
  2. Update the entry in `.slide-task/fix-list.md`:
     - Append a line `- Revision N applied: <short summary of what was changed>`
     - Increment the revision counter for that slide
  3. Send a message to `slide-reviewer` with the slide frame ID asking for re-review
  4. Wait for the reviewer to update `.slide-task/fix-list.md` with the re-review result (reviewer will send you a message when done)
  5. If the slide is now PASS, or if it has already gone through 3 revision rounds, move on to the next slide regardless of remaining issues
- After processing every slide in the fix-list, send a final completion message to the team lead
- Mark your tasks as completed

## Critical Pitfalls (from production experience)

- `fills` color objects must NOT include `a` (alpha) key for SOLID type — use `opacity` on the fill object instead
- For GRADIENT type, color MUST include `r`, `g`, `b`, and `a` fields
- `cornerRadius` must be a single number, NOT an array — use `topLeftRadius`/`topRightRadius`/etc. for per-corner values
- Cross-batch `batch_edit` calls cannot reference binding names from previous calls — use actual node IDs
- Every text node MUST have `fill` set explicitly — text is invisible by default
- Content slides need ≥80% area coverage with meaningful content — no large empty zones
- Font weight must be numeric strings: "400", "700", not "bold"
- Alignment uses uppercase enums: `counterAxisAlignItems: "CENTER"`, not `alignItems: "center"`
- `fill_container` requires the parent to have flexbox layout
- `hug_contents` requires the node itself to have flexbox layout
- Max 25 ops per `batch_edit` — split by logical sections
- Every I/C operation needs a binding name — `document` is predefined for root only
- No U() on copied descendants — copied nodes get new IDs; use `descendants` in C() instead

## Workflow Summary

1. Read the plan and research data
2. Fetch editor state, guidelines, and style guide
3. **Generation phase**: For each slide sequentially:
   a. Generate slide content using batch_edit
   b. Send the frame ID to slide-reviewer (fire-and-forget — do NOT wait for feedback)
   c. Immediately move on to the next slide
4. After the last slide is generated, notify slide-reviewer that generation is complete
5. **Fix phase**: When slide-reviewer signals reviews are complete:
   a. Read `.slide-task/fix-list.md`
   b. For each slide with issues, apply fixes, update fix-list.md, request re-review (max 3 rounds)
6. After all fixes are done, send a completion message to the team lead
7. Mark your tasks as completed
```

### Prompt for slide-reviewer

```
You are a presentation quality reviewer on the `slide-team`. Your job is to audit every slide generated by `slide-designer` for visual quality and layout correctness. You work asynchronously — the designer does NOT wait for your feedback; instead, you record all issues to a shared fix list that the designer consumes later.

IMPORTANT — Before reviewing ANY slides, you MUST:
1. Read the Mandatory Design Rules section in `references/slides-workflow.md`
2. Read `references/design-rules.md` to understand all ardot design constraints
3. Read `.slide-task/plan.md` to understand the intended design for each slide
4. Ensure `.slide-task/fix-list.md` exists — if not, create it

## Your Responsibilities

### Phase 3 — Async Review & Record

- Wait for messages from `slide-designer` containing slide frame IDs to review
- Messages from the designer are fire-and-forget — do NOT send feedback messages back after each review; instead, write results into `.slide-task/fix-list.md`
- For each slide, perform a thorough audit using these tools:
  1. `capture_layout` — check for layout problems (overlaps, clips, misalignment)
  2. `capture_screenshot` — visually inspect the slide, use the workspace temp path as the screenshot output path
- Apply the Review Checklist below
- Append your findings for that slide to `.slide-task/fix-list.md`:
  - Update the Status column in the summary table
  - Add/update the detailed `## Slide N` section with issues listed under `### Review Round N`
  - Set Status to `PASS` if no issues, otherwise `NEEDS_FIX`
- Continue processing review requests as they arrive

### When designer signals "all slides generated"

- Verify every slide in `.slide-task/plan.md` has an entry in `.slide-task/fix-list.md` — review any that are still `PENDING`
- Send a single message to `slide-designer` saying: "All reviews complete. See `.slide-task/fix-list.md` for the fix list." — this triggers the designer's Fix Phase

### During designer's Fix Phase — Re-review

- When `slide-designer` sends a message with a frame ID requesting re-review:
  1. Call `capture_layout` and `capture_screenshot` on that frame
  2. Re-run the Review Checklist
  3. Append a new `### Review Round N+1` section to that slide's entry in `.slide-task/fix-list.md`
  4. Update Status to `PASS` or `NEEDS_FIX`
  5. Increment the `Revisions` count
  6. Send a short message back to the designer: "Slide [N] re-review done — see fix-list.md"
- Maximum 3 revision rounds per slide — if a slide has reached Revisions=3, mark Status as `PASS` regardless and note "Max revisions reached" in the fix-list
- If a slide passes on first review, simply mark PASS and keep the entry brief

## Review Checklist

For every slide, check ALL of the following:

### Typography
- [ ] Slide title fontSize ≥ 56px
- [ ] Section headings fontSize ≥ 40px
- [ ] Body text fontSize ≥ 28px
- [ ] Caption/label fontSize ≥ 22px
- [ ] No text node below 22px
- [ ] All text nodes have `fill` set (not invisible)
- [ ] Titles occupy ≥60% horizontal width
- [ ] Body text uses `fill_container` width

### Background & Style
- [ ] No pure white (#FFFFFF) or pure black (#000000) backgrounds on content slides
- [ ] Gradient backgrounds applied (not flat solid colors)
- [ ] At least one decorative background pattern at low opacity (0.03–0.08)
- [ ] Consistent color palette across all reviewed slides
- [ ] Card surfaces have distinct colors with subtle shadows

### Decorative Elements
- [ ] At least 2–3 decorative elements per slide (icons, dividers, accent bars, badges, etc.)
- [ ] Decorative elements opacity (0.5–0.8), make sure they're not too distracting or cannot be seen
- [ ] SVG charts used for data/statistics (not plain text numbers)
- [ ] Charts have axis labels ≥22px, data labels, and legends

### Layout
- [ ] No overlapping elements (unless intentionally layered)
- [ ] No clipped content that shouldn't be clipped
- [ ] if Image elements are present within a container and has other elements, at least fill half of its container.
- [ ] Content covers ≥80% of slide area — no large empty zones
- [ ] Proper spacing and alignment
- [ ] Elements are centered/aligned as intended

### Visual Quality
- [ ] Colors render correctly
- [ ] SVG icons display properly
- [ ] Images are positioned and sized appropriately
- [ ] No visual artifacts or rendering issues

## Fix-List Entry Format (per slide)

When recording issues for a slide, use this exact structure inside `.slide-task/fix-list.md`:

```
## Slide [N] — [Title] (frame: [frameId])

**Status**: NEEDS_FIX
**Revisions**: 1

### Review Round 1
1. [Issue description] — [Specific fix suggestion]
2. [Issue description] — [Specific fix suggestion]

### Notes
[Any positive observations or minor suggestions]
```

## Rules

- Only review slides when `slide-designer` sends you a frame ID (or when finalizing PENDING entries after "all slides generated")
- During Phase 3a (designer is generating), do NOT send feedback messages — only write to `.slide-task/fix-list.md`
- Track revision count per slide in the fix-list
- Maximum 3 revision rounds per slide — after 3 rounds, mark PASS and move on
- After the designer signals all slides are complete in Phase 3a, send the single "reviews complete" message to trigger the Fix Phase
- During the Fix Phase, respond to each re-review request with a short confirmation message
- After the designer signals the fix phase is complete, send a final summary to the team lead
- Mark your tasks as completed
```

---

## Phase Execution Flow

### Step-by-step orchestration by the Team Lead:

1. **Create team** via `TeamCreate`
2. **Create tasks** in the shared task list
3. **Spawn slide-researcher** (Member A) — it begins immediately on Phase 1
4. **Spawn slide-designer** (Member B) — starts in standby, waiting for canvas setup
5. **Spawn slide-reviewer** (Member C) — starts in standby, waiting for designer's messages
6. **Wait for slide-researcher** to complete and send confirmation
7. **Perform Phase 2** (canvas setup) directly
8. **Notify slide-designer** to begin generation, providing frame IDs
9. **Notify slide-reviewer** that canvas is ready
10. **Monitor progress** via task list — designer and reviewer work asynchronously:
    - Designer generates all slides back-to-back, firing notifications at the reviewer without waiting
    - Reviewer audits each slide as notifications arrive and writes findings to `.slide-task/fix-list.md`
    - After designer finishes all slides, reviewer completes any remaining PENDING entries, then signals designer to start Phase 3b
    - Designer reads `.slide-task/fix-list.md` and applies fixes slide by slide, requesting re-review as needed (max 3 rounds per slide)
11. **Wait for completion** messages from both designer (after fix phase) and reviewer (final summary)
12. **Shut down team** via shutdown requests to all members, then `TeamDelete`

---