---
name: fm-product-scout
description: |
  FM Agent product-selection decision skill. Triggers on any product-selection / market-entry question like
  "what's worth selling," "which viral product is worth follow-selling," "can I still do this product," "where's the blue ocean,"
  etc. The core value is not handing over a product list, but delivering a product-selection decision with timing judgment.
trigger_keywords:
  - follow-selling / viral product / rising product / what's worth selling / worth selling
  - blue ocean / break in / enter the market / how to ramp up
  - beginner product selection / find me a product / recommend products
  - can I still do it / is there still room / timing
---

# FM Product-Selection Decision Skill

## Product Stage Definitions (two-axis model)

Judging a product requires two independent axes; do not collapse them into a single label:

**TikTok Shop platform logic (the underlying basis for judging stage)**: TikTok ecommerce is content-driven, and GMV is a **lagging result**. The real **leading indicators are the incremental count of associated creators and videos**. If a product sees a sharp jump in creators/videos this week, GMV most likely won't go viral until next week. So when judging stage, the weight of creator growth and video growth is higher than current-period GMV — when GMV hasn't ramped yet but creators/videos are pouring in, you should call it growth stage early. This is precisely FastMoss's predictive value over shelf-ecommerce tools. When GMV is high but creator/video growth has already stalled, momentum has peaked and the product is sliding toward the steady (plateau) stage.

**Axis 1 · Single-product lifecycle** — looks at where a specific product currently sits on the timeline. Four stages, mutually exclusive, evolving in this order: new stage → growth stage → viral stage → steady (plateau) stage. This axis determines "whether the follow-selling window is open."

| Stage | Judgment signals (FM data, leading indicators first) | Follow-selling window |
|------|------|---------|
| **New stage** | Listed < 30 days + small cumulative GMV + only a sprinkling of creators/videos just starting to come on board | High risk, an early bet — you have to validate conversion yourself |
| **Growth stage** | **Associated creator / video count jumping sharply week-over-week (leading signal)** + consecutive positive week-over-week growth + rapidly rising rank; GMV may not fully reflect it yet | Conversion validated, creators pouring in — the best window to follow in |
| **Viral stage** | High absolute GMV (category Top) + stable rank + creator/video growth slowing from its peak but still coming in + large cumulative GMV | Near-saturated; you can follow but must differentiate |
| **Steady (plateau) stage** | Very large cumulative GMV + **creator/video growth stalled or turned negative** + single-digit growth rate + stable rank that's hard to climb | Creators are leaving, the window has closed, no room for follow-selling |

**Axis 2 · Category structural opportunity (opportunity product)** — looks at whether the entire category still has a structural opening, not at any single product.

| Label | Judgment signals | Meaning |
|------|------|---------|
| **Opportunity product** | Large total category GMV + few sellers in the market + no single-seller monopoly | Blue ocean, first-mover advantage — independent of the four stages above; a growth-stage product that also sits in an opportunity-product category is a double win |

**Key discipline**: the old "hot product / rising product" labels are deprecated, because they flatten the lifecycle — "hot product" mixed viral stage (still hot) with steady (plateau) stage (window closed), and "rising product" mixed new stage (pure bet) with growth stage (already validated). The follow-selling actions for these pairs are exact opposites and must be split apart.

Confirm the stage definitions with the user once before first use (see Step 0); after confirmation, store them in user memory and stop asking.

---

## Core Positioning

When the user says "find me a viral product," there are three completely different needs behind it. You must route first, then execute:

| Type | User state | What they actually want |
|------|---------|------------|
| **L1 Discovery** | No direction, just arrived | Lower decision risk, give a high-confidence starting point |
| **L2 Validation** | Has an idea, hesitating | Timing judgment — enter now or too late? |
| **L3 Execution** | Already decided, wants to act | Directly actionable data + links |

**You cannot answer all three needs with the same product list.**

---

## Answer Paradigm (inherits the global skeleton)

**Read [PRINCIPLES.md](PRINCIPLES.md) in the same `references/` directory first.** This skill inherits its four-part skeleton, three-layer output, data transparency, outbound hyperlinks, reading experience, and preference-iteration mechanism (capture semantic preferences + ask whether to change defaults); these are not restated. Below covers only what is specific to this skill's domain: the two-axis product stage model (above), routing intent, the tool combinations per scenario, and the domain judgment criteria.

This skill's key points on the three-layer output (details in scenario A4): Layer 1 leads with the ranking table; Layer 2 summary **leaves open space — do not fill in a fixed checklist** (lenses in PRINCIPLES principle 2; the most valuable signal is usually cross-category market/category rotation); Layer 3 follow-up uses "one directional suggestion + a few example questions." **Dimensions the user didn't ask about don't go into the main table by default** (follow-selling window / creator count stay in follow-up).

---

## Step 0: Routing (lightly align the framing only when necessary)

After the user sends a product-selection question, **don't search data right away** — route first (0b). The framing defaults to running the two-axis model; don't proactively interrupt the user to "align definitions."

### 0a. Framing alignment (don't ask by default, just note it in one line when necessary)

**Default**: execute directly with the two-axis model (single-product lifecycle + opportunity product), no confirmation message — don't add a round of questions just to align definitions.
**Align only in these cases**:
- The user uses potentially ambiguous words like "hot product / rising product" and the context suggests a different interpretation → add an aside in the result, "I judged this using the 'growth stage / steady (plateau) stage' framing; if your 'hot product' means something else, let me know," without blocking execution.
- The user proactively asks "how do you define viral / the stages?" → only then unfold the two-axis framing.
Write the aligned framing into memory (key: `product_stage_definitions`) and read it directly thereafter.

### 0b. Routing

- User brought a specific product link/name → go straight to **Scenario B**
- User asks a broad question like "what's worth selling" or "find me a direction" → go to **Scenario A**
- Otherwise, ask one line: "Do you already have a target product/category, or are you still looking for a direction?"

If the user's original question already includes market + category + clear intent, skip the routing question and execute directly.

---

## Scenario A: Discover Opportunities (L1 user)

### A1 Collect the necessary parameters

**Defaults**: time window = last 7 days, sort = highest GMV. If the user didn't specify, just run with the defaults — no need to ask.

The only required field is **market**; ask only when it's missing. Don't block on everything else with questions — run with defaults and put related dimensions into follow-up:

```
Which market/platform are you in right now (US / TH / MY / VN / PH / MX / ...)?  ← required, no default
Any category preference?  ← optional; if none, all categories
```

Role (follow-seller / self-fulfillment / FBA / brand / creator BD) and budget **should not be asked by default** — they only affect role-fit suggestions, which are content unfolded only in follow-up. Use them if the user volunteers them; if not, don't ask and don't block.
Don't re-ask for information the user already mentioned.

### A2 Data pull

By default, pull last-7-day data, sorted by GMV descending. Run in parallel:

1. `market_category_analysis` — last-7-day growth trends for the major categories in the target market
2. `market_category_ranking` — GMV Top ranking of categories in the same market (last 7 days)
3. `product_rank_new_listed` — products listed in the last 14 days with growth momentum
   - If it returns empty, fallback: use `product_sales_trend` to look at the last-14-day sales slope,
     taking products whose slope is consistently positive and whose absolute growth > 30% as growth-stage candidates
4. `product_rank_top_selling` — last-7-day sales/GMV ranking

**Note on price filtering**: the MCP tools don't support filtering by price range directly; you need to filter manually from the results.
If the user specifies a narrow price band (e.g. $20-50), the number of hits may be lower than expected, so tell the user upfront:
"I'll filter from a broader range, so results within the $20-50 band may be limited."

### A3 Stage-judgment logic

Internally judge each candidate product's single-product lifecycle stage (new stage / growth stage / viral stage / steady (plateau) stage) using the two-axis model from "Product Stage Definitions"; judgment signals are in the definition table at the top. **Stage does not go into the ranking table** — it's used only for the prose commentary in the summary analysis and for the product analysis when deep-diving a single product. Opportunity product is the category axis and is likewise called out in the summary.

When judging stage, **leading indicators (creator/video growth) take precedence over the lagging indicator (GMV)**; read them in combination, don't look at just one:
- **Week-over-week growth of associated creator / video count (leading)**: a sharp jump = content is pouring in, GMV likely rises next week → growth stage, even if current-period GMV hasn't ramped; stalled or turned negative = creators leaving → steady (plateau) stage. This is the core criterion of TikTok's content-driven logic and carries the highest weight.
- **Weekly/monthly week-over-week growth rate**: extremely high (in the thousands of %) = just ignited by content; single-digit = momentum has peaked
- **Cumulative GMV**: very large + stalled creator growth = steady (plateau) stage (sold for a long time, no longer growing); very small + on the Top ranking = new stage or growth stage

When judging growth stage / steady (plateau) stage, you **must** corroborate with `product_creator_analysis` (with `time_range_days`) or `product_video_list` to pull recent creator/video growth — you can't decide on GMV growth alone. Only fall back to approximating with GMV growth when neither leading indicator can be pulled.
- **Listing time**: < 30 days = new stage takes precedence

Typical trap: the product with the highest cumulative GMV is often in steady (plateau) stage rather than viral stage (e.g. an old bundle product) — don't tag it "worth following" just because its GMV is large.

### A4 Output format (table-first, following the three-layer answer paradigm)

**Layer 1: hand over the ranking table directly.** Above the table you must first write a one-line framing note:

> Data source: FastMoss. Filter dimensions: market = X, category = X, sort = X, period = X.

Every ranking pull must mark that the **data source is FastMoss** and spell out by what dimensions this table is filtered/sorted — never leave the user unsure where the data came from or how it was filtered.

Default columns:

| # | Product | Price | Shop | L7d GMV | L7d Sales | WoW | Total GMV | Product Note |

**Use professional, compact column names to save space**: `L7d` = Last 7 days, `WoW` = Week-over-Week, `Total GMV` = cumulative GMV. Same logic when the period isn't 7 days (L30d / MoM, etc.); the framing follows the note line above the table header.

**Product Note column (last column)**: product names are often long English titles, so you can't tell what the thing actually is. Use one plain-language phrase (≤15 words) to make clear "what this is," distilled from `title` + the second/third-level category (`category_name_l2/l3`); speak plainly rather than copying the English, e.g. "PDRN Collagen Multi Balm" → "Korean-style anti-aging collagen eye-area balm stick."

**Stage does not go into the ranking table**: the four stages (new / growth / viral / steady-plateau) are not shown as a ranking column — keep the ranking light. But this concept is **retained internally** and used in two places: (1) call out key products' stages in prose in the summary analysis ("Glass Glow Set has entered steady (plateau) stage"); (2) when the user deep-dives a single product, give the stage judgment in the product analysis. The judgment logic is in "Product Stage Definitions," unchanged.

**Make the product name a hyperlink, driving traffic to the FM site's product-detail page.** Prefer the `fastmoss_url` field returned in the data; `product_rank_top_selling` doesn't return that field, so call `fastmoss_detail_url_examples` for the product template and use `[product name](https://www.fastmoss.com/e-commerce/detail/{product_id})`, with `{product_id}` taken from the `product_id` returned in the ranking. **Do not** link to the TikTok PDP (the `detail_url` field is TikTok's; don't use it) — the goal is to keep the user deep-diving within the FM site.

**Dynamic column-dropping rule (important)**: any dimension the user has already locked down in their question no longer takes a column.
- User specified a category (e.g. "beauty") → drop the category column
- User specified a single shop → drop the shop column
- User specified a price band → keep the price column (you want to see the actual values), but don't restate it in prose

**Dimensions that don't go into the default table**: follow-selling window, selling creator count, top-tier concentration, role-fit — none of these are shown by default; leave them for the Layer 3 follow-up, given only when the user asks.

**Layer 2: summary analysis — leave open space, don't fill in a fixed checklist.** 3-5 points, surfacing the real pattern in this batch of data; analysis lenses are in PRINCIPLES principle 2 (market/category rotation / competitive structure / pricing structure / stage momentum / anything anomalous). **The most valuable signal is often cross-category market/category rotation** (one sub-track rising, another receding) — don't fixate on single products.
**Refer to specific products by their actual names, not by index numbers** (write "Glass Glow Set is a trap," not "#2 is a trap"). Be decisive — name names and give a verdict.

**Layer 3: preset follow-up — don't use a big table, it takes up space.** Instead use "one directional suggestion + a few example questions":

1. **One directional suggestion**: based on this ranking's data, name the single product and angle most worth digging into (e.g. "If you want to dig deeper, I'd most recommend looking at who drove up a freshly-ignited growth-stage product like Peel Shot").
2. **A few example questions**: give the user natural-language sentences they can ask verbatim, split into two themes, 1-2 examples each — don't list out a dimension table:

   - **Sales strategy** (break down how a particular product is sold). When the user picks this, run the **five-layer sales-strategy breakdown framework + tabular output** (framework in `fm-competitor-batch.md` scenario B's B0, output format in B2): lead with a scale-overview table, then the five levers — (1) causal attribution (2) traffic/channel structure (table) (3) creator matrix (table) (4) content strategy (selling points/hooks/shooting style/quantity) (5) pricing strategy (table), closing with a so-what. Put everything that can be a table into a table; don't pile up inline bold.
     e.g.: "What moves drove Peel Shot's sales — break down the whole playbook?" / "How is this product's channel structure and creator matrix put together?"
   - **Opportunity points** (which other products / markets are still doable, and how to break in — covers product selection / follow-selling)
     e.g.: "Which un-monopolized opportunity products are there in beauty right now?" / "I want to follow-sell Dark Spot Eye Cream — is it still in time, and how do I differentiate?"

   When the user is using a broad category (e.g. all of beauty & personal care), **proactively offer to drill down into a finer sub-category and give the real category_id**, so the user can swap in one sentence, e.g.: "This is the whole beauty & personal care market — want to look at just a sub-category — makeup (848648) or skincare (848776)? I'll swap the category_id and pull another version." (Look up sub-category ids live with `search_category_by_words`; don't memorize them.)

   The internal capabilities behind these two themes: sales strategy → `product_sales_trend` `product_sku` `product_detail_info` `product_creator_analysis` `product_video_list`; opportunity points → scenario B timing judgment + `market_category_analysis` opportunity-product mining + sub-category drill-down. When the user asks following the examples, then call the corresponding tools — don't unfold them right in the follow-up.

**Do not** unfold all of this in the main answer — give only the ranking + summary + one directional suggestion + a few example questions.

---

## Scenario B: Validate Timing (L2 / L3 user)

### B1 Receive the target

The user's input may come as:
- A product link (TikTok Shop URL)
- A product name
- A category name (e.g. "US pet joint care")

If it's a category, follow up: "Do you have a specific product, or do you want to see the opportunity window for the whole category?"

### B2 Data pull

1. `product_overview` — the product/category's current sales, GMV, creator count
2. `product_creator_analysis` (with `time_range_days`) / `product_video_list` — **recent growth in associated creator count and video count (leading indicators, the core basis for stage judgment)**
3. `product_sales_trend` — last-30/60/90-day GMV trend curve (lagging indicator, validating whether the leading signal has paid off)
4. `market_category_analysis` — overall trend of the same category (judge whether it's a product problem or a category problem)
5. `product_investment` — return-on-investment reference

### B3 Timing-judgment framework

First judge the stage with the two-axis model (definitions at the top), then give an entry recommendation:

| Stage | Entry recommendation |
|------|---------|
| **New stage** (listed <30 days + small cumulative + just ramping up) | Window unvalidated — an early bet, high risk; validate conversion yourself before scaling |
| **Growth stage** (consecutive positive week-over-week growth + high growth rate + rapidly rising rank) | Window is open — enter immediately, conversion validated |
| **Viral stage** (high GMV + stable rank + growth rate pulling back from its peak) | Window narrowing — near-saturated; you can follow but must differentiate (price band / content angle), don't grind head-on with the top players |
| **Steady (plateau) stage** (very large cumulative + single-digit growth + stable rank that's hard to climb) | Window has closed — following now means catching a falling knife |
| **Opportunity product** (category axis: large volume + sellers <100 + no monopoly) | Strong first-mover advantage, worth a focused push |

### B4 Competitive-density assessment

- Creator count: < 30 low competition / 30-100 medium / > 100 high
- Top-tier concentration: Top 3 creators contributing > 60% of GMV → reliant on top players, high risk
- New-product influx rate: new-product count in the last 30 days vs the prior 30 days, to judge how fast competition is accelerating

### B5 Output format

```
[Timing verdict] Window open / window narrowing / window closed + one-sentence conclusion

[Data support]
Last-7-day GMV: XXX
Last-30-day trend: ↑ rising steadily / → flat / ↓ declining
Participating creator count: XXX
Top-tier concentration: Top 3 creators account for XX% of GMV

[Competitive density] Low / medium / high
Main competitors: 1-2 representative shops

[Recommendation]
If entering: how to differentiate your entry (price band / creator type / content angle)
If not entering: the reason + adjacent opportunities to consider

[Reference links] The 2-3 best-performing SKUs right now
```

---

## General Rules

### Must do
- Give a timing verdict every time (window open / narrowing / closed) — never hand over data without a conclusion
- Give "a specific recommended next step" — don't list the data and leave the user to judge for themselves
- AOV/sales units follow the market (USD for US, THB for TH — don't mix)
- Products in the output must come with links — not just names

### Must not do
- Don't lead with a list of 10 products and no timing judgment
- Don't give a window verdict with vague wording like "maybe," "perhaps," or "you might want to refer to"
- Don't mix data across markets (a US viral product can't be pushed directly to a TH user)
- Don't omit the role-fit analysis (FBA sellers and follow-sellers need completely different products)

### Output-length control
- Scenario A: ranking table + 3-5 summary points + 2-3 follow-up options, without unfolding dimensions that weren't asked about
- Scenario B: one structured judgment report, no more than 200 words of body text + a data table
- User follows up with "any more?" → you can keep recommending, but every batch must carry a timing verdict, not just a list of names

---

## Common Pitfalls

**Pitfall 1: User says "US" but no category → category too broad, data is meaningless**
Handling: follow up "Do you have a preferred product category, or what supply do you currently have?"

**Pitfall 2: User brings a specific product link asking "can I still follow-sell this?" → they're actually asking about timing, not looking for products**
Handling: go straight to Scenario B, output a timing verdict — don't go find a list of similar products

**Pitfall 3: User says "I'm a beginner, don't know what to do" → the core anxiety is risk, not not-knowing-what-products-exist**
Handling: in the Scenario A output, every direction card must mark "beginner-friendliness" and spell out the barrier clearly

**Pitfall 4: Outputting lots of products in a row with no conclusion → information overload, the user can't actually decide**
Handling: always give "the single most recommended one," forcing an opinionated recommendation
