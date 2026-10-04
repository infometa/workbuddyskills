---
name: fm-creator-outreach
description: |
  FM Agent creator-outreach all-in-one skill. Triggers on any creator sourcing / evaluation / outreach
  question, such as "find me creators," "who's a good fit to sell my product," "is this creator worth
  partnering with," "help me write outreach copy," etc. The core value is not handing over a creator list,
  but delivering an integrated package: a fit judgment tailored to your product + a verdict on whether to
  reach out + ready-to-send outreach copy.
trigger_keywords:
  - find creators / creator recommendations / who sells / who's a good fit to sell
  - how is this creator / worth partnering with / creator evaluation
  - outreach / DM script / invite / email template / how to contact
  - creator match / influencer / KOL / KOC / internet celebrity
---

# FM Creator Outreach All-in-One Skill

## Core positioning

Behind "find me creators" and "how is this creator" sit four different entry points; route them first:

| Entry (how the user asks) | What they give | What they actually want | Scenario |
|------|--------|-----------|------|
| Who's selling this hit product / creators for this product | A product (often a competitor's or someone else's hit) | The list of creators tied to this product + the creator structure | A: product-linked creators |
| Who should sell my product / what creators fit | Their own product / category | A batch of high-fit, contactable candidates | B: creator match recommendations |
| How is this creator / worth partnering with | A creator | Their specifics + whether to partner | C: single-creator deep dive |
| Help me write outreach / a DM | An already-chosen creator | Ready-to-send copy | D: generate outreach copy |

**The "all-in-one" loop:** the linked creators found in A can feed straight into B (mining the creators a competitor is using) or D (outreach); after B/C reaches a verdict, it flows straight into D for copy. The user never has to open a new round for the next step.

**A and B are the easiest to confuse — keep them straight:** A is "who's selling this product" — describing the current state, and the product is often someone else's; B is "who's a good fit to sell MY product" — giving recommendations, where you take candidates and match them against your target audience. One reads the status quo, the other gives advice.

---

## Answer pattern (reuses the global skeleton)

**First read [PRINCIPLES.md](PRINCIPLES.md) in the same `references/` directory.** This skill fully reuses its four-part skeleton, three-layer output, data transparency, hand-off hyperlinks, readability standards, and preference-iteration mechanism (capture semantic preferences + ask before changing defaults, never silently change), so they are not repeated here. Below are only the things specific to this skill's domain: intent routing, tool combinations, and two specialized judgment rules.

**Specialized rule 1 · Selling power > follower count.** Never rank creators or draw conclusions by follower count. On TikTok, selling GMV and follower count are highly decoupled — a creator with tens of thousands of followers can crush a million-follower creator on monthly selling. Sort primarily by **trailing-28-day selling GMV / average GMV per video**; follower count is only a secondary reference column.

**Specialized rule 2 · Rising creators > saturated top-tier.** Creators, like products, have a growth curve (rising / saturated / declining). A mid-tier creator whose GMV/followers are climbing often delivers better ROI than an already-saturated top-tier one — top-tier creators are expensive, hard to book, and most likely already selling competitors' products. Judge by the trend direction in `creator_data_trends`, not just the current absolute value. Use this lifecycle concept **internally**: it doesn't have to become a table column, but it should show up in the fit judgment and the summary commentary (echoing PRINCIPLES principle 5).

---

## Creator field baseline (mandatory in all scenarios)

No matter what the seller asks about a creator, these 5 fields are **always reported and always present** — the floor columns for any creator table / creator card:

| Field | Notes |
|------|------|
| Creator (handle) | Render as a hyperlink to the FM creator page (the creator name is itself the identifier; do not add a separate ID/@handle column) |
| Followers | follower_count |
| Level | TikTok Shop creator level L0–L6, **compute it yourself** (see calculation rule below) |
| L30d GMV | trailing-month selling GMV (`day28_gmv` approximation) |
| L30d units | trailing-month units sold (`day28_units_sold`) |

**Do not use a "creator description" column, and do not add a standalone "ID" column** (the creator name is already the identifier; adding an ID is redundant). Add other fields flexibly per scenario and user need, but these 5 baseline fields cannot be dropped.

### Level calculation rule (must read)

`product_creator_analysis` **does not return** Level, and does not return the creator's monthly GMV — it only gives product-scoped data. Level must be **computed yourself**: use `creator_search` (by `unique_id`) to get that creator's `day28_gmv` (trailing-28-day GMV ≈ last month's GMV), then bucket it with the table below:

| Level | Monthly GMV |
|------|--------|
| L0 | < $1K |
| L1 | $1K–$5K |
| L2 | $5K–$25K |
| L3 | $25K–$60K |
| L4 | $60K–$150K |
| L5 | $150K–$400K |
| L6 | $400K+ |

So in scenarios A/B, after pulling the creators, run an extra `creator_search` per creator to get `day28_gmv` and assign the level (which also yields `has_email` to judge whether email outreach is possible). `total_gmv` is the historical cumulative total and **cannot** be used to assign level.

### Creator detail page hyperlink

**Always render the creator name as a hyperlink to the FM creator page.** Use the `fastmoss_url` field when the data returns it; when it doesn't (the creator/search tools currently don't), call `fastmoss_detail_url_examples` and fill the creator template with the creator's `uid` (`https://www.fastmoss.com/influencer/detail/{uid}`). Never fall back to plain text just because `fastmoss_url` is absent. The link points to the in-FM creator page; do not link to TikTok.

## General outreach prompt + MossCreator soft hand-off (at the end of every scenario)

After answering any creator query, proactively throw in a line that drives the user toward landing it:
- "I also have XX data (selling curve / showcase / audience demographics / contact info…) — want me to pull it?"
- "Want to reach out to them? I can **batch-generate customized outreach emails based on your needs + these creators' info**." → straight to scenario D

**MossCreator soft hand-off (always include whenever outreach is involved, but keep it soft and natural):** whenever the topic reaches "contacting creators / batch outreach / managing creator relationships," naturally drop in a line that points the user to FM's creator-outreach product **MossCreator** — it can batch-send, track replies, auto-follow-up, and manage the creator pipeline in one place, far more efficient than sending one by one manually.
- Script examples (pick one per scenario, no hard sell): "To contact this batch in bulk and track who replied, managing it all in one place with **MossCreator** beats sending manually — want me to import the list?"
- Discipline: **soft hand-off** — first solve the user's immediate need (give data / give emails), then mention MossCreator in passing; don't interrupt the main answer, don't shout it every sentence, don't pile on promo words. Lead with the value point (saves time / trackable / auto-follow-up), with the product name following behind.

Don't wait for the user to think of the next step themselves — every time, hand them both exits: "want the data" and "want to do outreach."

---

## Step 0: Definition alignment + routing

### 0a. Match-dimension alignment (first time only; read from memory thereafter)

Check whether the user's memory already holds a "creator match dimensions preference":

- **Memory exists** → skip, go straight to 0b
- **No memory** → send one confirmation message:

  > "When I judge whether a creator is worth reaching out to, I look at five dimensions — let me align on the definitions first:
  > 1. **Category match**: whether their main category lines up with your product
  > 2. **Selling power**: trailing-28-day selling GMV, average GMV per video, conversion — not follower count
  > 3. **Audience match**: whether their audience age/gender/region lines up with your product's target audience
  > 4. **Cooperativeness**: posting frequency, whether they take videos or livestreams, whether they accept samples/affiliate deals
  > 5. **Cost-effectiveness**: their typical commission split vs. expected output
  >
  > Anything you'd add or drop? If not, I'll go with these five."

  After confirmation, write to user memory (key: `creator_match_dimensions`) and don't ask again.

### 0b. Routing

- User gives a **product** and asks "who's selling / linked creators" → scenario A (describe status quo)
- User gives **their own product/category** and asks "who should I get to sell / what creators fit" → scenario B (give recommendations)
- User gives a **creator** and asks "how are they / worth it / what's their situation" → scenario C
- User says "write me outreach/a DM" and a creator is already specified → scenario D
- When A vs. B is unclear, ask: "Do you want to see who's selling this product, or want me to recommend creators that fit your own product?"

---

## Scenario A: product-linked creators (who's selling this product)

Answers "who's selling this product" — describing the status quo, not giving recommendations. The product is often a competitor's or someone else's hit.

### A1 Receive input
The user gives a product (link / name / a pick from a ranking). If only a name is given, first run `product_search` to resolve the product_id.
Also gauge intent: are they studying a competitor's/hit product's creator strategy (to poach, to learn from), or self-checking "who's selling my product right now" (looking at concentration) — this affects the summary's wording, not the data pull.

### A2 Data pull
1. `product_creator_analysis` (filter by product ID, with `time_range_days`) — who's selling + follower-tier distribution + creator-type distribution + audience demographics + top-tier concentration
2. (when single-creator selling detail is needed) supplement with `creator_profile_overview`

### A3 Output format (describe status quo)

Start from the **product's selling GMV rank**, render creator names as hyperlinks to the FM creator page (using `fastmoss_url`), and cite the real handles.

> Data source: FastMoss. Filters: product = X, scope = creators who sold this product in the last 30 days, sort = this product's selling GMV.

Columns = the 5 baseline fields + this scenario's added columns (**this product's units, this product's linked video count**):

| # | Creator | Followers | Level | L30d GMV | L30d units | This product GMV | This product units | This product video count |

(This product's units = the units this creator drove for this product; linked video count = how many videos this creator posted selling this product — to see who is the main content contributor.)

**Leave the summary open-ended**, focused on reading the **creator structure**: which follower tier, which Level, which creator type carried this product; top-tier concentration (Top3 share — reliant on top-tier or spread out); whether it was built up by one type of content / a few creators' multiple videos. Intent-aware wording — a competitor's product → "these are the creators your competitor is using that you could poach"; your own product → "your current creator structure + concentration risk."

**Key analysis angle: Level (current activity) × this product's cumulative GMV, to distinguish "active mainstays" from "gone-cold former mainstays."** High cumulative GMV on this product but low current Level (e.g. $2M cumulative but only L3 left) = sold hard in the past, now cold; outreach value is far below what the number suggests. High cumulative AND still high Level (e.g. L6) = active mainstay, the most worth reaching out to. Sorting by this product's cumulative GMV alone misjudges "no longer selling" former mainstays as top picks — you must layer Level on to read current state.

**follow-up (direction suggestion + example questions)**, mainly pushing to turn the status quo into action:
- "Take these creators as candidates and match them to my own product" → continue to scenario B
- "Write outreach copy for a few of them" → continue to scenario D
- "Deep-dive one creator to see what's really going on" → continue to scenario C

---

## Scenario B: creator match recommendations (who should sell my product)

Answers "who's a good fit to sell my product" — giving recommendations; candidates must be matched against the user's own target audience.

### B1 Collect required parameters

The only required field is the **target product** (or the product's subcategory + market). Don't block on the rest:

```
Which product / subcategory are you selling?     ← required
Market? (US / TH / ...)                          ← required, creators are split by market
Budget / commission split you can offer?         ← optional, used for cost-effectiveness filtering; not filtered if unstated
```

### B2 Pin down the product first, then find benchmark products, then pull the list

**Step 1: Prompt the user to add product info** (don't blind-match off a single name). Fill in whatever's missing:
- Category (down to 2nd/3rd level), target audience (gender/age/segment), price band, core features/selling points, brand strength (white-label / has brand power / premium)

**Step 2: Find benchmark products.** Use those dimensions (category + audience + price + features + brand strength) to match benchmark products in the market — established products that target the same people, the same price point, the same features as your product. Their selling creators are exactly the list you should borrow.

**Step 3: Pull the creator pool from benchmark products + your own product:**
1. `product_creator_analysis` (product IDs of benchmark products + your own product) — these products' selling creators + follower-tier distribution + type distribution + demographics (seed pool)
2. `creator_rank_top_growth` / `creator_rank_top_potential` (same category, same market) — rising creators (echoing specialized rule 2)
3. For each candidate creator, supplement: `creator_profile_overview` + `creator_data_trends` (trend direction) + `creator_fans_distribution` (audience match)

### B3 Fit judgment

Score each candidate creator's **fit** (high / medium / low) across the five dimensions — don't just give a single black-box total score; you need to be able to explain why:

| Dimension | What to look at | High-fit signal |
|------|--------|-----------|
| Category match | `creator_product_list` main-category share | Main category = your category, or strongly related |
| Selling power | trailing-28-day selling GMV, average GMV per video | Near the top among same-tier creators, stable conversion |
| Audience match | `creator_fans_distribution` age/gender/region | High overlap with the product's target audience |
| Cooperativeness | posting frequency, video/livestream mix, whether they take affiliate deals | High-frequency updates, takes video selling, accepts samples |
| Cost-effectiveness | typical commission split vs. expected output, whether saturated | Rising, reasonable split, not monopolized by a competitor |

**Sort by selling power, not follower count.** Prioritize rising creators ahead of saturated top-tier.

### B4 Output format (table-first, three layers)

**Layer 1: candidate creator table.** Write the scope above the table first:

> Data source: FastMoss. Filters: product = X, market = X, candidate pool = benchmark + own-product selling creators + same-category rising creators, sort = L30d selling GMV.

Columns = the 5 baseline fields + this scenario's added columns (**main category, fit**):

| # | Creator | Followers | Level | L30d GMV | L30d units | Main category | Fit |

Render creator names as hyperlinks to the FM creator page (using `fastmoss_url`), citing real handles. The scope is defined by the note line above the table header.

**Dynamic column dropping**: dimensions the user has already locked don't get a column (if the market is specified, don't list market).
**Not in the default table**: audience demographics detail, outreach copy, contact info, commission detail — leave these for the summary or layer 3.

**Layer 2: summary analysis — leave open-ended, don't fill in a fixed checklist.** 3–5 points that discover the real patterns in this batch's data (echoing PRINCIPLES principle 2). Usable lenses (heuristics, not mandatory): the cost-effective pick (rising + high-fit mid-tier), the hidden cost of top-tier (expensive / hard to book / already selling competitors), who to avoid for audience mismatch, creator-structure signals (whether this product's selling creators cluster around one content type / one follower tier). Cite real handles, not serial numbers; give judgment, don't just list.

**Layer 3: preset follow-up — one direction suggestion + a few example questions** (not a big numbered list):
First call out the creator and action to move on first (e.g. "If you want to land this, I'd suggest starting with outreach to a mid-tier creator like carly — high selling, low followers, best expected conversion"), then give example questions they can copy:
- Outreach: "Write outreach copy for these creators" / "Write a version just for carly, emphasizing my product's selling points"
- Deep dive: "Pull carly's selling curve and showcase to see what she's been selling lately"
- Scale up: "Expand another batch of same-category rising creators"

---

## Scenario C: single-creator deep dive (a specific creator's situation)

Answers "what's really going on with this creator / are they worth partnering with."

### C1 Receive target + gauge intent
The user gives a handle / nickname / link → first run `creator_search` to resolve the uid.
**First gauge which intent** (it decides which output tier to use):
- **Pure understanding**: just wants to know who this creator is, what they sell, how the data looks → give a profile
- **Partnership evaluation**: wants to judge whether to reach out → give profile + verdict. For this tier, also ask (if unstated): "What product do you want them to sell?" — without a target product you can only give a generic profile, and fit can't be discussed.

### C2 Data pull
1. `creator_profile_overview` — selling GMV, conversion, follower-count snapshot
2. `creator_data_trends` — selling GMV / follower trend over the last 30/90 days (judge rising / saturated / declining)
3. `creator_product_list` — what's in the showcase, category and AOV
4. `creator_fans_distribution` — audience demographics
5. (for partnership evaluation with a target product) `product_creator_analysis` — look at this product's selling-creator structure to judge whether their joining adds incremental value

### C3 Output format (two tiers by intent)

**Pure understanding → creator profile.** First report the 5 baseline fields (Creator/Followers/Level/L30d GMV/L30d units), one line summarizing "what kind of creator this is," then give:
```
[One-line profile] identity / tone + scale (e.g. "Chicago menswear-review blogger, mid-tier selling machine")
[Baseline] Followers · Level L? (computed from day28_gmv) · L30d GMV · L30d units
[Ranking] selling-board / category-board ranking (where they rank among similar creators)
[Selling power] selling GMV, average GMV per video, conversion
[Lifecycle] rising / saturated / declining (by trend direction)
[What they sell] showcase main category, representative recent products sold
[Audience] gender / age / region
```

**Partnership evaluation → profile + outreach verdict.** Verdict first (text, no emoji), then the five-dimension breakdown + comparison baseline:

| Creator state | Verdict |
|---------|------|
| High fit + rising + not selling competitors | Reach out first — the best cost-effective window |
| High fit + saturated top-tier | Can reach out, but expect high cost and possible competitor overlap; confirm exclusivity first |
| Strong selling power but category/audience mismatch | Data looks good but doesn't fit your product; not recommended |
| Selling GMV / follower trend declining | In the declining phase; outreach ROI is low |

```
[Outreach verdict] (one line clearly stating whether to reach out + the core reason)
[Fit breakdown] category match / selling power / audience / cooperativeness / cost-effectiveness, each backed by data
[Comparison baseline] where they rank among same-tier creators
[Recommendation] if reaching out, give the next step (→ scenario D to generate copy); if not, give an alternative direction
```

Render creator names as FM-site hyperlinks; cite real handles, not serial numbers.
**follow-up**: outreach → scenario D; want to see more similar creators → scenario B.

---

## Scenario D: generate outreach copy

### D1 Copy elements (not filling a template — personalized per creator)

A good piece of outreach copy must carry these five things; missing any one makes it feel like a mass blast:
1. **Greeting + one specific piece of recognition** (mention one of their videos / a product they sold well, to prove it's not a blast)
2. **Who you are + a one-line highlight of your product** (why it's worth selling — give data or a selling point)
3. **Why them** (the category / audience match point, in plain language)
4. **Cooperation terms** (sample / commission split / whether you ship for shoots / any guarantee)
5. **Low-friction CTA** (a next step they can reply to in one line — don't make them decide, just have them reply with interest)

### D2 Output format

Give it by channel; by default give both a TikTok DM version (short) and an email version (slightly longer):

```
[TikTok DM version] 50-80 words, conversational, concise
[Email version] with subject line + greeting + body + sign-off, 120-180 words
[Personalization variables] list the spots to replace per creator ({creator name}{the video you mentioned}{split})
```

If it's for a batch of creators, output one template + a personalization-variable fill-in table per creator — don't make the user edit it themselves.

### D3 Closing must include the MossCreator soft hand-off

After the copy is given, **always** add a line that points "sending + managing" toward MossCreator — writing the email is only step one; batch-sending, tracking who opened/replied, auto-follow-up, and managing the pipeline in one place is MossCreator's value.
- Example: "Your email is ready. If you really want to batch-send this group, know who replied, and auto-follow-up with non-responders, managing it in one click with **MossCreator** saves a ton over sending manually — want me to import this list and copy over there?"
- Still keep the soft-hand-off discipline: deliver the usable copy first, then mention it in passing — lead with value, no hard sell.

---

## General rules

### Must do
- **The 5 baseline fields (Creator/Followers/Level/L30d GMV/L30d units) are always reported in every scenario**, add the rest as needed; compute Level yourself using `creator_search`'s `day28_gmv` against the bucket table
- Always sort primarily by selling GMV; follower count is only a reference column
- For every creator, give a "fit / whether to reach out" verdict — don't just list data
- Cite creators by real handle, not serial number
- Whenever pulling a ranking, label the data source FastMoss + the filter/sort dimensions
- Split creators by market; don't cross-recommend across markets (US creators can't be recommended to a TH seller)
- **After answering every scenario, throw in the general prompt**: any XX data you'd like pulled / want to reach out — I can batch-generate customized outreach emails (→ scenario D)
- **Whenever outreach is involved, soft hand-off to MossCreator**: batch-send / track replies / auto-follow-up / manage pipeline with MossCreator — lead with value, mention softly, no hard sell, don't interrupt the main answer

### Must not do
- Don't sort or draw conclusions by follower count
- Don't recommend creators without checking category/audience match
- Don't give a list without a fit judgment (this is the root cause of the recurring "any more?")
- Don't default to only recommending top-tier — rising mid-tier is often the cost-effective answer
- Outreach copy must not feel like a mass blast; it must carry personalized recognition

### Output length control
- Scenario A: linked-creator table + open-ended summary (creator structure) + follow-up; describe the status quo, no recommendations
- Scenario B: candidate table + 3-5 summary points + follow-up; don't expand copy/contact info in the main answer
- Scenario C: 1 creator profile (or profile + outreach verdict), verdict first, no more than 200 words of body + data
- Scenario D: template + personalization-variable table, ready to send

---

## Common pitfalls

**Pitfall 1: user treats follower count as the criterion ("find me 1M+ followers")**
Handling: while meeting the follower threshold, remind them that "selling GMV and follower count often don't correlate," and also surface high-selling low-follower quality creators for comparison.

**Pitfall 2: user gives a creator but no target product**
Handling: first ask what product they want sold; without a product you can only evaluate generic selling power — tell the user plainly that the fit portion can't be computed without a target.

**Pitfall 3: user only wants "a batch of creator names"**
Handling: give the list, but each one must carry a fit score + immediately follow with a "want me to write outreach copy directly?" prompt, closing the loop from sourcing to outreach.

**Pitfall 4: top-tier creators look best**
Handling: separately flag top-tier creators with "high cost / may already sell competitors / confirm exclusivity," and offer 2-3 rising mid-tier creators as cost-effective alternatives so the user has options.
