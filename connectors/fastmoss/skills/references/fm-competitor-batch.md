---
name: fm-competitor-batch
description: |
  FM Agent rapid batch competitor-diagnosis skill. Triggers on any competitor-comparison /
  viral-product-attribution / benchmarking-diagnosis question: "analyze these competitors,"
  "how did this shop/product suddenly go viral," "compare me against my competitors,"
  "who is my biggest threat," etc.
  The core value is NOT handing back competitor data, but delivering the so-what:
  side-by-side comparison + viral-product attribution + "what should I copy / what should I defend against."
trigger_keywords:
  - competitor / rival / opponent / peer / fellow vendor
  - analyze these shops / compare / side-by-side / who is stronger
  - how did it suddenly go viral / why is it selling well / viral-product attribution / where did the GMV come from
  - me vs. competitors / where am I behind / benchmark / threat
---

# FM Rapid Batch Competitor-Diagnosis Skill

## Core Positioning

There are three kinds of competitor questions, fundamentally different — route them first:

| Entry point | What's given | What they actually want | Scenario |
|------|--------|-----------|------|
| Analyze these competitors / who's stronger | Multiple competitors (shops/products) | Side-by-side comparison + who is the real threat, shared playbooks | A Batch side-by-side comparison |
| How did this competitor suddenly go viral | A single competitor | Attribution of where the GMV came from + whether it's replicable | B Viral-product attribution |
| Where am I behind my competitors | My shop + competitors | The gap + what to fix first | C Benchmarking diagnosis |

**The soul of this skill is the so-what.** Competitor data on its own has no value; what the user wants is "so what should I copy, what should I defend against, which soft spot should I attack." In every scenario's output, conclusion weight > data weight.

**Division of labor with the store-diagnosis skill**: this skill = **multi-competitor side-by-side comparison + viral-product attribution** (comparing several shops, or "why did this single product/shop go viral"). If the user wants a **full-scope deep checkup of a single shop** (one shop's complete structure / concentration / pain points), route to `fm-store-diagnosis.md`. Simple rule: comparing several shops horizontally / dissecting a viral product → here; drilling deep vertically into one shop → store diagnosis. Scenario C (me vs. competitor benchmarking) is a lightweight delta comparison; if the user wants a thorough checkup of their own shop, switch to store diagnosis.

---

## Answer Paradigm (reuse the global skeleton)

**Read [PRINCIPLES.md](PRINCIPLES.md) in the same `references/` directory first.** Reuse the four-part skeleton, three-layer output, data transparency, drive-to-product hyperlinks, reading experience, and preference-iteration mechanism — don't restate them. This skill adds two domain-specific rules:

**Specialized rule 1 · Analysis must land on the so-what.** Every block of competitor comparison/attribution must answer "what does this mean for the user" — the playbook to copy, the threat to defend against, the soft spot to attack. Giving only "competitor GMV $X, Y creators" without a judgment = task not done (this is the root cause of users asking again and again).

**Specialized rule 2 · Approach viral-product attribution from the content/creator engine.** TikTok GMV is the result of content-driven selling. When a competitor "suddenly goes viral," it's almost always because: they seeded a batch of creators / one video went viral / they went live / they spent on ads. Attribution must first break down the **channel structure** (video selling vs. livestream vs. product card vs. ads) and the **creator engine**, not just note that the GMV curve went up.

---

## Competitor Field Baseline (mandatory in all scenarios)

No matter what is asked about a competitor, for shop-type competitors these fields are **required**:

| Field | Note |
|------|------|
| Shop (name) | Make it a hyperlink to the FM shop page (URL per the note below) |
| Main category | l1/l2 category |
| L30d GMV | trailing-30-day GMV |
| L30d units | trailing-30-day units sold |
| MoM | month-over-month growth (tells whether it's growing or declining) |
| Lead channel | the structure mix of video / livestream / product card / ads (this is the competitor's playbook fingerprint) |

For product-type competitors, reuse the product-selection skill's fields (price / GMV / units / MoM / stage). Add others flexibly per scenario.

### Product / shop / creator detail-page hyperlinks

Product / shop / creator names **must always be made into FM-site hyperlinks**, taking the `fastmoss_url` field from the returned data (product pages from `shop_product_analysis` etc. already return it, e.g. `https://www.fastmoss.com/e-commerce/detail/{product_id}`). When the data doesn't carry `fastmoss_url` (shop and creator pages don't), call `fastmoss_detail_url_examples` and fill the matching template with the ID the tool returned (shop -> seller_id `https://www.fastmoss.com/shop-marketing/detail/{seller_id}`, creator -> uid `https://www.fastmoss.com/influencer/detail/{uid}`). Don't fall back to plain text. None of the links should point to TikTok.

---

## Step 0: Routing

- **Multiple** competitors (shops/products) given → Scenario A
- A **single** competitor given + asking "why is it selling well / how did it go viral" → Scenario B
- **Their own shop** mentioned, to be compared against competitors → Scenario C
- A single competitor given but no stated intent → ask one question: "Do you want to see how it went viral (dissect the playbook), or compare it against others / against yourself?"

Competitor given by name only → resolve the ID first with `shop_search` / `product_search`.

---

## Scenario A: Batch Side-by-Side Comparison

### A1 Collect parameters
Required: the **competitor list** to compare (2+ shops or products) + market. If incomplete, run with what the user gave and prompt that the missing ones can be added.

### A2 Data pull (same metrics for every competitor, so they're comparable)
For each competitor shop, pull the same set in parallel:
1. `shop_base_info` — category, base snapshot
2. `shop_sale_analysis` — L30d GMV/units, **channel structure (video/livestream/product card/ads mix)**
3. `shop_data_trends` — recent trend (growing or declining)
4. `shop_creator_analysis` — creator count, top-tier concentration (relying on top-tier vs. mid-tier ramp-up)
5. (as needed) `shop_product_analysis` — hero products, new-launch cadence

### A3 Output format (three layers)

**Layer 1: side-by-side comparison table.** Data-source line + table (shop name hyperlinked, sorted by L30d GMV):

> Source: FastMoss. Comparison basis: trailing 30 days, same dimensions side by side.

| # | Shop | Main category | L30d GMV | L30d units | MoM | Lead channel | Creators | Top-tier concentration |

**Layer 2: so-what analysis (leave free space, but a judgment is mandatory).** Don't just describe differences — call out:
- **Who is the real threat**: judged on growth + size + channel efficiency together, not just who has the largest GMV
- **The shared winning playbook**: the pattern several of them use (e.g. all ramping up with mass mid-tier creator videos, all anchoring high commission) — this is what's copyable
- **Each one's soft spot**: who depends on a single top-tier creator (collapses if that creator leaves), whose growth is fading, whose channel mix is too narrow
- Cross-competitor structural signals (e.g. all migrating toward livestream, or a price band collectively left empty)

**Layer 3: follow-up (direction suggestions + example questions):**
- "Want to dig into how one of them went viral?" → Scenario B
- "Want to compare your own shop against these?" → Scenario C
- Example questions: "Which creators did shop X ramp up with?" / "Of these, whose playbook should I copy most?"

---

## Scenario B: Sales-Strategy Breakdown / Viral-Product Attribution (how this product/shop sells)

Answer "what is its whole playbook, what made it sell, and can it be replicated." Break it down with the **five-layer framework** below; **causal attribution always comes first**. This framework is the standard dissection of a single product's / single shop's sales strategy, and the product-selection skill's "sales strategy" deep-dive uses it too.

### B0 Five-layer breakdown framework for a product's sales strategy

**Layer 1 · Causal attribution (do this first, most critical)**: what action actually drove the GMV increment? Take the point where GMV took off and align it against the timing of changes in each lever; the one whose timing matches is the cause:

| Possible cause | How to verify (FM data) |
|---------|------------------|
| Short-video count↑ | `product_video_list` / `shop_video_analysis` for video count over time |
| Creators / creator videos↑ | `product_creator_analysis` for linked-creator count, linked-video increment (leading indicator) |
| Price discount | `product_sku` / `product_detail_info` original vs. current price, timing of the markdown |
| Commission↑ | `product_detail_info` `commission_rate` change |
| Went live / ran ads / hit a chart | `shop_live_analysis` / `shop_investment_analysis` |

→ Applying TikTok's leading-indicator logic: creator/video increments usually lead GMV, so whichever moved first is most likely the cause. Don't treat "GMV went up" as attribution.

**Layer 2 · Channel strategy**: which channel does the GMV come from?
- Creator channels: creator short-video selling / creator livestream selling
- Brand-owned channels: brand-owned short video / brand-owned livestream
- Product card: viral products ride organic mall traffic; new products rely on product-card placement
- Tools: `shop_sale_analysis` / product `video_gmv` vs. `live_gmv` split

**Layer 3 · Creator matrix strategy**: creator count + the structure of top-tier creators vs. tail KOC
- `product_creator_analysis`: total count, tier distribution, top-tier concentration. Judge whether a few top-tier creators carry it, or mass tail KOC ramp it up.

**Layer 4 · Content strategy**: selling points / content breakdown / shooting style / volume
- `product_video_list` / `video_detail_analysis` / `video_script_info`: recurring selling points, content formats (review/skit/voiceover/comparison/unboxing), video volume, typical hook. For a deeper dig, connect to the Skill 5 video-strategy package.

**Layer 5 · Price strategy**: pricing / promotion / commission
- `product_sku` / `product_detail_info`: price band, cross-platform pricing comparison (vs. the same item on other platforms), promotion forms like discount / BOGO, and the `commission_rate` commission level.

### B1 Data pull
Pull in parallel along the five layers: `shop_sale_analysis` (channel), `product_creator_analysis` or `shop_creator_analysis` (creator matrix), `product_video_list` + `video_detail_analysis` (content), `product_sku` / `product_detail_info` (price & commission), `product_sales_trend` / `shop_data_trends` (align the timeline for attribution), `shop_investment_analysis` (ads).

### B2 Output format (tabular; don't pile up inline bold + arrows)

Keep the layout clean: **lead with a scale-snapshot table → a one-line attribution → the five levers layer by layer (table anything that fits a table) → close with the so-what**. If a two-column table works (metric/value, dimension/share), don't write it as line after line of inline bold.

**1. Scale and curve (look at the snapshot first)** — a "metric / value" table so the user first sees how big a snapshot this is:
| Metric | Value |
|------|------|
| Cumulative GMV | (time since listing) |
| Trailing-28-day GMV / units | |
| Trailing-7-day GMV | |
| Selling creators | |
| AOV | (vs. original price) |
| Rating | |

Below the table, one line of "curve characteristics" prose: is it a one-shot spike or a steady plateau, are there big-promo/livestream pulses, which stage is it in now.

**2. Core playbook breakdown (five levers)** — a subheading per lever, table for the quantitative, 2-3 bullets for the qualitative:
1. **Product / hook** (bullet): which ingredient/trend it rode, how many content angles the product theme can spin off (the "why it could seed so many creators" of the causal attribution)
2. **Traffic structure** ("dimension / share" table): paid vs. organic, short video/livestream/product card, creator/brand-owned — see at a glance whether it's ad-driven
3. **Creator matrix** ("metric / value" table): active creator count/video count, tier structure, key accounts
4. **Content strategy** (bullet): core hook/selling point, content format, typical length, language/audience
5. **Price strategy** ("item / value" table): original price → main price (discount), promotion forms, commission, AOV extension

**Make the causal attribution clear inside "curve characteristics" and levers 1-2**: which action (ads/big promo/creator seeding/discount) matches the GMV timeline.

**3. Can it be replicated (so-what)** — always close with this: which part of this playbook is copyable, which part is a barrier (ad budget / creator resources / supply chain), and which layer a small/mid seller should copy.

Data sources: scale snapshot + causal attribution from `product_overview` (the three distributions ads/channel/content + `chart_list` daily increments); creator matrix from `product_creator_analysis`; content from `product_video_list` (`is_ad` + `video_desc`); price from `product_detail_info` / `product_sku`.

---

## Scenario C: Benchmarking Diagnosis (me vs. competitors)

Answer "where am I behind, what do I fix first."

### C1 Data pull
For **the user's own shop** + **the benchmark competitor**, pull the same set (same as Scenario A's A2), and do a delta on each dimension.

### C2 Output format

**Conclusion first**: one line on which dimension holds the biggest gap. Then give:

```
[Benchmark table] Dimension × (me / competitor / gap): GMV, channel structure, creator count and quality, AOV, new-launch cadence
[Where the gap is] Sorted by gap size, most fatal gap first
[Fix First] 1-3 highest-leverage actions, sorted by "fastest to show results when fixed," don't list a pile
[Their soft spot] Competitors aren't flawless either; point out what you can counterattack
```

Don't lay out every dimension flat and make the user find the gap themselves — proactively sort and give a Fix First.

---

## General Rules

### Must do
- Land every block of analysis on a so-what (copyable / defendable / attackable), not just describe data
- Competitor comparison must be **same-basis** (same period, same dimensions); if the basis isn't aligned it isn't comparable — flag it
- Approach viral-product attribution from channel structure + creator engine, not just noting GMV went up
- Each time you pull data, flag the source FastMoss + comparison basis
- Refer to competitors by real shop/product names, not by index numbers
- Group competitors by market; don't mix-compare across markets

### Must not do
- Don't give only competitor data without "so what should I do"
- Don't treat "its GMV went up" as attribution — break down what drove the rise
- Don't lay out a pile of dimensions and make the user find the key point — sort, give a judgment
- Don't force a comparison across mismatched bases (A on 7 days, B on 30 days)

### Output-length control
- Scenario A: comparison table + so-what summary + follow-up
- Scenario B: attribution report, conclusion first, channel breakdown + replicability judgment
- Scenario C: benchmark table + Fix First (1-3 actions)

---

## Common Pitfalls

**Pitfall 1: user hands over a pile of competitors and wants a "comprehensive analysis"**
Handling: don't write a long dossier paragraph per competitor. Use one side-by-side comparison table + one so-what passage to make "who's the threat, shared playbook, each one's soft spot" clear; leave deep digs to follow-up.

**Pitfall 2: asked "how did it go viral," only answers "it sold $X, grew Y%"**
Handling: that's the phenomenon, not the attribution. You must break down the channel structure + find the ignition engine (which batch of creators / which video / which livestream / whether there were ads), and give a replicability judgment.

**Pitfall 3: benchmarking diagnosis lists 10 gaps**
Handling: sort gaps by how fatal they are, give only 1-3 Fix First, leave the rest to follow-up. Information overload = the user doesn't know what to do first.

**Pitfall 4: a competitor that's a brand official shop vs. a third-party creator shop, compared together**
Handling: distinguish the type first, then compare; brand-owned and reselling shops run different playbooks, and mix-comparing them yields wrong conclusions — group them when necessary.
