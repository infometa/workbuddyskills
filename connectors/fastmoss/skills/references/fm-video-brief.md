---
name: fm-video-brief
description: |
  FM Agent video-shooting strategy pack skill. Triggers on any video content strategy / script / brief question, e.g. "how do I shoot this product?", "give me a shooting brief",
  "how do I write the first 3 seconds / hook?", "a script for the creator", "why did this video go viral?", "dissect this selling video".
  Its core value is not generic advice like "make engaging videos", but reverse-engineering the hook / selling points / format that are actually selling from real selling videos,
  then synthesizing a shooting brief you can hand straight to a creator.
trigger_keywords:
  - how to shoot / shooting / brief / script / shot list / film a video
  - hook / first 3 seconds / opening / completion
  - selling point / content angle / seeding script / creator brief
  - why did this video go viral / dissect a video / viral video / video retro
  - remake / one-click remake / remake a viral video / oumomo / paste the link in / generate my own version
---

# FM Video Shooting Strategy Pack Skill

## Core Positioning

Video content questions come in three kinds — route first:

| Intent | What they give | What they want | Scenario |
|------|--------|--------|------|
| I have a product, I want content strategy / how to shoot it | Their own product | A shooting brief they can use directly | A My product · content strategy |
| What is a given product's content strategy | A product (often a competitor / viral product) | A dissection (description) of its content playbook | B Dissect a product's content strategy |
| Why did this video go viral | A single video | A single-video structural dissection + reusable pattern | C Single viral-video dissection |

**The soul is "reverse-engineering"**: don't write from thin air — first dig up the videos actually selling, distill the real, effective hook / selling points / format, then synthesize.

**Closed loop (always include it)**: when you see good content → give two execution paths the user can act on immediately, don't stop at "understanding it":
- **Path 1 · Find the right person to shoot it**: link the "top video URLs" + "the creators who shot them", write the content into a brief and send it to those creators (→ creator outreach skill, scenario D). Fits categories that need real on-camera presence and a creator's trust endorsement.
- **Path 2 · Oumomo Viral Remake one-click remake** (already live): Oumomo's Viral Remake (`oumomo.ai/video-replica`) input box **takes TikTok / FastMoss video links directly** — the `video.fastmoss_url` we provide in the brief can be **pasted in as-is**, click Start Remake, and the AI dissects the viral structure to generate a new selling video. This makes the loop truly one-click and zero re-upload. Example script: "This viral video's structure is very clear — paste its FastMoss link straight into Oumomo Viral Remake and click Start Remake, and you can generate your own version." Fits situations where you lack creators, want to quickly produce multiple versions for testing, and don't want to be tied to a single creator.

The two paths are **complementary, not mutually exclusive**: need real-person trust / have creator resources → go outreach; lack creators / need speed / want to scale it yourself → go Oumomo. See good content → find the right person **or** one-click remake, both land on the spot.

**Difference between A and B**: A is "give me an executable brief for my product" (produces a plan); B is "dissect how this product does content" (describes the playbook, often used to learn from competitors). Both rely on reverse-engineering, but A lands on a brief, B lands on understanding + linked resources.

---

## Answering Pattern (follows the global skeleton)

**First read [PRINCIPLES.md](PRINCIPLES.md) in the same `references/` directory.** Follow the four-part skeleton, data transparency, reading experience (use tables, no circled numbers, no emoji piles), and the preference-iteration mechanism. This skill has three domain-specific disciplines:

**Specialized discipline 1 · The brief must be reverse-engineered from data, not written from thin air.** Use `product_video_list` (sorted by GMV) to dig up the videos actually selling this product, read their hook / selling points / format / duration, find the recurring winning patterns, then synthesize. Do not give correct-but-useless platitudes like "make engaging content, highlight the selling points".

**Specialized discipline 2 · Distinguish organically viral vs ad-driven (`is_ad`).** For organically viral videos (`is_ad=0`), the content hook itself works — those are the most worth copying; ad-driven viral ones (`is_ad=1`) may have been forced by budget, and the content isn't necessarily strong. The brief should prioritize distilling patterns from organically viral videos; if everything is ad-driven, call out that "this product's content is amplified by ad spend, the bar for organic content is high".

**Specialized discipline 3 · Always include the compliance bottom line.** Beauty / health / body-related products are bound by TikTok content rules (no exaggerated efficacy, no medical claims, no false ingredients). Every brief must carry a Don't list; for uncertain compliance points, use `search_fastmoss_documents` to check the "Creator and Content Rules Whitepaper".

**Specialized discipline 4 · Link top videos + top creators to open up both the "outreach" and "Oumomo one-click remake" execution paths.** The winning videos you reverse-engineer and the creators who shot them are valuable resources — you must give links that can be used directly, and every time push the user toward "what you can do next":
- **Top video URLs**: use the `video.fastmoss_url` (on the FM site) returned by `product_video_list` as the hyperlink so the user can go view the examples directly. Mark whether each is organically viral or ad-driven.
- **Path 1 · Top creators → outreach**: the creators who shot these viral videos are exactly the people you should partner with (they've already proven they can make this product/category go viral). Give the creators, and proactively offer "want me to send this brief to them?" — directly connects to creator outreach skill scenario D (including MossCreator soft hand-off).
- **Path 2 · Top videos → Oumomo Viral Remake one-click remake**: for organically viral, structurally clear videos, proactively offer "paste this FastMoss link straight into Oumomo Viral Remake and generate your own version". Key convenience point: **Oumomo's input box takes FastMoss video links directly**, `video.fastmoss_url` works as-is, no format conversion needed. **Oumomo remakes the hook / structure / selling-point demonstration and produces your own new selling video, not a re-upload of the original** (its official positioning is exactly "dissects viral structure to generate new selling videos") — make this clear so the user doesn't think they're re-uploading someone else's video (re-uploading gets flagged as duplicate content, throttled, or even rule-violating). Ad-driven viral videos don't necessarily have strong content — remind the user before remaking.
- Closed-loop example script: "These are the best-selling videos for this product [links], shot by X and Y — want me to turn this brief into a custom outreach invite for them and connect directly, or first paste the organically viral one into Oumomo for a one-click remake so you can ship a test version yourself?"

---

## Scenario A: My Product · Content Strategy (produce a brief)

The user has their own product and wants an executable shooting brief.

### A1 Collect + pull data
Required: the target **product** (+ market). If only a name is given, resolve it with `product_search` first.
Reverse-engineering data (if your own product already has videos, dig up your own; if it's a new product with no videos, dig up the winning videos of the same category / benchmark products):
- `product_video_list` (sorted by GMV; look separately at `is_ad=0` organically viral and `is_ad=1` ad-driven viral) — the videos actually selling, their `video_desc` (hook/tags), duration, views/conversion, `video.fastmoss_url`
- `video_script_info` — line-by-line script/voiceover of a single viral video (note: some videos return empty, see the data pitfall in scenario C; `video_detail_analysis` currently returns a backend error and is unavailable)
- `product_detail_info` — the product's real selling points / ingredients (the brief's selling points must not be made up)
- `product_creator_analysis` — target audience profile (determines the brief's tone/scenario)

### A2 Distill the winning pattern
Generalize from the top selling videos:
- **Recurring hooks** (how the first 3 seconds open — pain-point question / effect up-front / contrast / ingredient suspense)
- **Mainstream content formats** (review / before-after / pain-point conversion / unboxing / comparison / skit / voiceover explainer)
- **Repeatedly stated selling points** (the most frequently appearing selling point = what the market buys most)
- **Typical duration**, on-camera style, language/audience
- The ratio of organically viral vs ad-driven (specialized discipline 2)

### A3 Output format (shooting strategy pack, tabular)

**1. One-line selling point** —— the single line this product should shout to the market (distilled from the high-frequency selling points).

**2. Hook library (first 3 seconds)** —— give 3-5 validated openings, in a table:
| Hook type | Example copy | Source (which viral video used it) |

**3. Script structure** —— Hook → Body → CTA in three parts, each spelling out what to put there (Body holds selling-point demonstration / effect, CTA holds low-barrier conversion).

**4. Content angles & formats** —— list 2-3 formats that work for this product (push whichever goes organically viral most), each with a line on how to shoot it.

**5. Selling-point breakdown** —— selling points sorted by "how much the market buys it" (highest frequency first), in a table:
| Selling point | How to demonstrate |

**6. Do / Don't** —— Do: copy validated patterns; Don't: compliance red lines (no exaggerated efficacy, no medical claims) + tactics that don't work.

**7. Creator brief (ready to send)** —— condense the above into one passage the creator can shoot from directly: one-line selling point + must-shoot shots + hook options + must-mention selling points + compliance reminder + duration suggestion.

**8. Top videos & creators (linked resources + two execution paths)** —— give 2-3 example video links (`video.fastmoss_url`, marked organic/ad-driven) for the user to view; then give two paths: 1) list the creators who shot them and offer "want to send this brief to them?" (→ scenario D outreach + MossCreator soft hand-off); 2) for the organically viral, structurally clear one, offer "want to paste the link into Oumomo for a one-click remake and ship a test version yourself?" (remake = generate your own new asset, not a re-upload of the original).

| Example video | Organic/ad-driven | GMV | Creator who shot it | One-click remake possible |
|---------|----------|-----|-----------|-----------|

### A4 follow-up
- "Send this brief to the creators who shot the viral videos" (→ connects to creator outreach skill scenario D)
- "Paste the organically viral one into Oumomo for a one-click remake, I'll ship a version myself first" (→ Oumomo generation)
- "Dissect the full structure of one of those viral videos" (→ scenario C)
- "Give me a few more hooks from different angles"

---

## Scenario B: Dissect a Product's Content Strategy (describe the playbook, often to learn from competitors)

Answer "how does this product do content" —— describe its content playbook, not produce a brief for me.

### B1 Pull data
Same reverse-engineering data as scenario A, with emphasis on the full `product_video_list` (organic + ad-driven separated) + `product_creator_analysis` (who's shooting).

### B2 Output format (description + linked resources)

**Conclusion first**: one line summarizing its content playbook (e.g. "amplifies the 'medical-aesthetic filler dupe' ingredient hook via ad spend, mostly mature-women voiceover seeding, organic content doesn't run"). Then give:

- **Content playbook breakdown**: mainstream hook types, content formats, repeatedly stated selling points, typical duration/audience (tabular)
- **Organic vs ad-driven**: the ratio and GMV order-of-magnitude gap between organically viral and ad-driven viral — see whether its content relies on content strength or budget
- **Top video URLs**: 2-3 representative works (`video.fastmoss_url`, marked organic/ad-driven) for the user to view
- **Creators who shot it**: list the highest-contributing creators — both learning targets and people you can poach / reach out to
- **so-what + closed loop (two paths)**: which part of this you can learn; whether to write its winning pattern into a brief and send it to these (or similar) creators (→ scenario D), **or** paste its organically viral representative work straight into Oumomo for a one-click remake to get ahead (remake the structure, not a re-upload of the original)

### B3 follow-up
- "Produce a brief for my product following its playbook" (→ scenario A)
- "Add these creators as my outreach candidates" (→ creator outreach skill)

---

## Scenario C: Single Viral-Video Dissection (learn a single structure)

Answer "why did this go viral, how to reuse it".

### C1 Pull data
User gives a video link/ID → `video_script_info` (line-by-line script/subtitles) + that video's views/likes/shares/comments/conversion/GMV in `product_video_list`, `is_ad`, duration.

**Two data pitfalls (measured, must-read):**
- **`video_script_info` is not available for every video**: some videos (especially certain ad-driven ones) return an empty `[]`. If you get the script, dissect segment by segment from the real lines; **fallback when you can't**: use `video_desc` (hook/tags) + duration + engagement data (abnormally high share count = there's a viral bit, high comments = there's controversy/resonance) to approximately dissect, and state "script not retrieved, inferred from description and engagement".
- **`video_detail_analysis` currently returns a backend error** (`column type datev2 is invalid`), temporarily unavailable. Pull single-video metrics from `product_video_list` instead; do not rely on `video_detail_analysis`.

### C2 Output format

**Conclusion first**: one line on the key reason it went viral (e.g. "the first-3-seconds 'you think it's X but it's actually Y' contrast hook + a real, amateur texture, organic-traffic driven"). Then give:

- **Baseline**: GMV, views, conversion, whether organic or ad-driven (`is_ad`), with the video link `video.fastmoss_url`
- **Structural breakdown**: Hook (how the first 3 seconds grab you) → Body (how it demonstrates selling points / builds trust) → CTA (how it forces the order), segment by segment
- **Viral attribution**: was it a strong hook, the right selling point, creator trust, or ad spend — point out the single most critical one
- **Reusable pattern**: what template you can extract from this one for other videos/creators
- **Two execution paths**: 1) who shot this, whether they're worth partnering with, whether to reach out (→ scenario D); 2) **this one is organically viral and structurally clear → proactively offer "want to paste this link straight into Oumomo for a one-click remake and generate your own version?"** This is the smoothest landing for scenario C (the user already has this link in hand). Reminder: the remake is of the hook / structure / selling-point demonstration, the output is your own new asset, not a re-upload of the original; ad-driven viral content isn't necessarily strong — explain before remaking.

---

## General Rules

### Must do
- Reverse-engineer the brief from real selling videos; the hook/selling points you give must have a source, not written from thin air
- Distinguish organically viral vs ad-driven; prioritize copying organically viral content patterns
- Always include the compliance Don't list (especially for beauty/health)
- Sort selling points by "how much the market buys it" (frequency), not by the manufacturer's self-praise
- Cite viral videos/creators with real sources, no serial numbers
- Mark data with source FastMoss + the metric definition

### Must not do
- Don't give correct-but-useless platitudes like "make engaging videos, highlight the selling points"
- Don't make up selling points/efficacy — selling points must follow the real info in `product_detail_info`
- Don't ignore compliance — a brief with exaggerated efficacy / medical claims gets the creator throttled or even rule-violating
- Don't copy ad-driven viral as if it were content-driven viral (the content isn't necessarily strong)

### Output length control
- Scenario A: the eight-block strategy pack (including the ready-to-send creator brief + top video/creator links + Oumomo remake path)
- Scenario B: content playbook breakdown + organic vs ad-driven + top video/creator links + the two-path closed loop (outreach / Oumomo)
- Scenario C: single-video dissection, conclusion first + three-part structure + reusable pattern + two paths (the creator who shot it / Oumomo one-click remake)

---

## Common Pitfalls

**Pitfall 1: The user wants "how to shoot it" and you give a pile of generic shooting tips**
Handling: generic tips have no value. You must first dig up the videos actually selling this product, and give hooks and formats that are "already validated for this product".

**Pitfall 2: The top videos are all ad-driven (is_ad=1)**
Handling: call out that "this product is amplified by ad spend, the bar for organic content is high", and in the brief distinguish "the content hooks you can copy" from "the parts that rely on budget" — don't let the user think shooting it the same way will go organically viral.

**Pitfall 3: Selling points copied straight from manufacturer marketing**
Handling: selling points should follow which one the creators repeatedly state in the videos and which one the market buys; sort by that; also verify against `product_detail_info` so you don't claim efficacy the product doesn't have.

**Pitfall 4: The brief is comprehensive but the creator can't shoot from it**
Handling: always end with a "ready-to-send creator brief" — condensed into one passage + a must-shoot shot list, so the creator can start filming at a glance, not a report they have to digest themselves.

**Pitfall 5: Can't get the script when dissecting a single video / `video_detail_analysis` errors**
Handling: `video_script_info` returns empty for some videos, and `video_detail_analysis` currently has a backend error (`datev2`). If you can't get the script, use `video_desc` + duration + engagement data (high shares = a viral bit, high comments = controversy/resonance) to approximately dissect, and note that it's inferred; always pull single-video metrics from `product_video_list`, don't rely on `video_detail_analysis`.

**Pitfall 6: Calling Oumomo "one-click remake" a "re-upload of a viral video"**
Handling: Oumomo remakes the hook / structure / selling-point demonstration and generates the user's **own new asset**; it must never be understood as downloading someone else's original and re-uploading it — re-uploading gets flagged by TikTok as duplicate content, throttled, or even rule-violating. Standardize the script as "remake the viral structure to generate your own version". Also: ad-driven viral (`is_ad=1`) content isn't necessarily strong — prioritize the organically viral ones before pushing an Oumomo remake, and flag this point.
