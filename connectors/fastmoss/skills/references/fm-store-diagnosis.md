---
name: fm-store-diagnosis
description: |
  FM Agent full-picture store diagnosis skill. Triggers on any single-store full-picture diagnosis / problem-area-finding question, such as "how is this store doing", "what are its core strengths", "break this store down for me in one click", "my store has been slipping lately, where's the problem", "give my store a checkup".
  The core value is not handing over store data, but delivering "a full picture of scale + structure + concentration risk + strengths/weak spots/problem areas + what to do about it".
trigger_keywords:
  - store diagnosis / checkup / full picture / one-click breakdown / break down this store
  - how is this store doing / core strengths / moat / where is it strong
  - my store / slipping lately / dropped / where's the problem / problem area
  - sales trend / store structure / bestseller dependence
---

# FM Full-Picture Store Diagnosis Skill

## Core Positioning

Store diagnosis comes in two intents with different framing — split them up front:

| Intent | User state | What they want | Scenario |
|------|---------|--------|------|
| Break down a benchmark/competitor store | Wants to see how others do it | Its winning structure + what I can learn, and where its weak spots are | A Benchmark store breakdown |
| Check up on their own store | Their store dropped / wants to optimize | Where the problem areas are + what to fix first | B Own-store checkup |

**The soul of this skill is so-what + concentration risk.** Don't just list store metrics — deliver "strengths/weak spots/problem areas + what to do about it", and always check the three concentrations (bestseller / creator / channel) — high concentration = fragile.

**Division of labor with the competitor quick-diagnosis skill**: this skill = **single-store full-picture diagnosis** (a complete checkup of one store: six-dimension structure + three concentrations + problem areas). If the user wants a **side-by-side comparison of multiple competitor stores**, or attribution for why a single product/store "suddenly blew up", route to `fm-competitor-batch.md`. Simple rule: drilling vertically into one store → here; comparing multiple stores horizontally / dissecting a bestseller playbook → competitor quick-diagnosis.

---

## Answer Pattern (follow the global skeleton)

**First read [PRINCIPLES.md](PRINCIPLES.md) in the same `references/` directory.** Follow the four-part skeleton, three-layer output, data transparency, soft-referral hyperlinks, reading experience (**tabular, scale-snapshot table leads**, see the B2 format in the competitor quick-diagnosis skill), and the preference-iteration mechanism. This skill has three domain-specific rules:

**Specialized rule 1 · Diagnosis must land on "strengths/weak spots/problem areas + what to do about it".** Just giving "store GMV $X, Y creators" is not diagnosis. For own stores give Fix First; for competitor stores give "what to learn / what weak spot to attack".

**Specialized rule 2 · Must check the three concentrations (the unique lens of store diagnosis).**
- **Bestseller concentration**: how much of total store GMV do the Top1 / Top3 products account for? One product carrying the whole store = hanging by a thread.
- **Creator concentration**: how much GMV do the Top3 creators contribute? Relying on one top-tier creator = if they leave, it collapses.
- **Channel concentration**: is it all ad-driven / all livestream? A single channel = one policy or cost shift and it caves.
For high-concentration stores, no matter how pretty the GMV, you must flag "this is a fragile point".

**Specialized rule 3 · Distinguish own-store vs competitor-store intent.** Own store = find problem areas, shore up weaknesses, give executable actions; competitor store = learn the winning structure, find the weak spot you can counter-attack. Same data, different wording and landing point.

---

## Six-Dimension Store Diagnosis Framework

Lift the five-layer sales-strategy framework up to the store level, **plus two dimensions unique to stores** (product structure, concentration risk):

| Dimension | What to look at | Tool |
|------|--------|------|
| **1 Scale & trend** | GMV/sales volume, country/category ranking, recently rising/flat/declining | `shop_base_info` `shop_data_trends` |
| **2 Sales/channel structure** | video/livestream/product card + paid/organic + creator/self-run share | `shop_sale_analysis` |
| **3 Product structure** | hero products, bestseller concentration, price bands, new-launch cadence, single-product dependence | `shop_product_analysis` `shop_rank_top_selling` |
| **4 Creator matrix** | creator count, top-tier concentration, mid-/long-tail volume spread, whether they cultivate in-house creators | `shop_creator_analysis` |
| **5 Livestream/self-run capability** | output share and efficiency of self-run short videos / livestreams | `shop_video_analysis` `shop_live_analysis` |
| **6 Concentration risk** | the three concentrations: bestseller/creator/channel (specialized rule 2) | aggregated from 2/3/4 |

---

## Step 0: Triage
- The user gives **someone else's store**, wants to learn from / benchmark it → Scenario A
- The user says **my store / our store**, wants a checkup or to find problems → Scenario B
- Only a store name with no stated intent → ask: "Is this your own store for a checkup, or do you want to break down someone else's playbook?"

If only a store name is given → first run `shop_search` to resolve the seller_id.

---

## Scenario A: Benchmark/Competitor Full-Picture Breakdown (learn the playbook)

### A1 Data Pull
Pull in parallel along the six-dimension framework: `shop_base_info` + `shop_data_trends` (scale & trend), `shop_sale_analysis` (channel), `shop_product_analysis` + `shop_rank_top_selling` (product structure, bestseller concentration), `shop_creator_analysis` (creator matrix), `shop_video_analysis` / `shop_live_analysis` (self-run capability), `shop_investment_analysis` (ad spend).

### A2 Output Format (tabular, scale-snapshot table leads)
Follow the B2 layout of competitor quick-diagnosis: **scale-snapshot table → six dimensions (table whatever can be tabled) → core strengths / weak spots → so-what**.

**1. Scale snapshot (metric/value table)**: store GMV, sales volume, category/country ranking, trend direction, store age, primary category. Below it one sentence on the trend characteristic (rising/flat/declining, whether there's a big-promo pulse).

**2. Six-dimension breakdown**: channel structure (dimension/share table), product structure (including **bestseller concentration**: Top1/Top3 share of total store %), creator matrix (including **creator concentration**), self-run/livestream capability. Each dimension: quantitative on a table, qualitative in bullets.

**3. Core strengths & weak spots**:
- Strengths: what is its moat (exclusive supply chain / in-house creator matrix / ingredient story / ad-spend muscle)
- Weak spots: which of the three concentrations runs high, whether growth is slipping, whether the channel is single — this is what you can counter-attack

**4. so-what**: what you can learn (which part is copyable) and what you can attack (its weak spot).

---

## Scenario B: Own-Store Checkup (find problem areas + Fix First)

### B1 Data Pull
Same as A1 but on your own store. If the user supplies a benchmark competitor, pull it in parallel for the delta (close to competitor quick-diagnosis Scenario C).

### B2 Output Format (conclusion-first, problem-area-driven)

**1. Scale snapshot + trend**: first gauge how big your own snapshot is and whether it's rising or declining.

**2. Problem-area diagnosis (ranked by severity, not laid out flat)**: sweep the six dimensions for problems. Typical problem areas:
- Total store GMV rides on a single bestseller (bestseller concentration too high) → once the bestseller fades, the whole store collapses
- All ad-driven, low organic share → profit eaten by ads, fragile ROI
- Creators rely on a few top-tier ones → low bargaining power, contact-loss risk
- New-launch gap / no second growth curve → can't catch the baton when old products fade
- Zero livestream/self-run capability → all bet on creators, no home turf
For each problem area: phenomenon (data) → why it's a problem → impact.

**3. Fix First (1–3 highest-leverage actions)**: rank by "fastest to show results when fixed", don't list a pile. Give concrete actions, not "suggest optimizing".

**4. Benchmark reference (when a competitor exists)**: same dimensions — me / competitor / gap, with the deadliest gap up front.

---

## Universal Rules

### Must do
- Diagnosis must give "strengths/weak spots/problem areas + what to do about it", not just list metrics
- Every time, check the three concentrations (bestseller/creator/channel); where high, flag the fragility
- Lead with the scale-snapshot table, table everything that can be tabled (don't pile up inline bold)
- Mark the source FastMoss + the framing period each time data is pulled
- Cite products/creators by real names; reference stores by market

### Must not do
- Must not just hand over a pile of store metrics with no diagnostic conclusion
- Must not ignore concentration — if the GMV is pretty but it's propped up by a single product / single creator / single channel, you must call it out
- Own-store checkup must not lay out a flat pile of problems — rank by severity, give Fix First
- Must not cross-diagnose across markets (don't judge a US store's snapshot by a TH standard)

### Output length control
- Scenario A: scale snapshot + six-dimension table + strengths/weak spots + so-what
- Scenario B: scale snapshot + problem areas (ranked) + Fix First (1–3)

---

## Common Pitfalls

**Pitfall 1: assuming a big store GMV means it's healthy**
Handling: check concentration first. GMV riding entirely on one bestseller / one top-tier creator / all ad-driven is glossy on the surface but brittle underneath. Healthy = spread across many products, many creators, many channels.

**Pitfall 2: an own-store checkup that lists a long string of problems**
Handling: rank problem areas by "damage to GMV", give only 1–3 Fix First items, the rest as follow-up. The user wants "which one to do first", not a problem list.

**Pitfall 3: breaking a store down as if it were a single product**
Handling: the unique value of store diagnosis is in "structure" — whether the product mix is healthy, whether there's a second curve, whether concentration is risky. A single-product lens can't see these; you must look at the whole store.

**Pitfall 4: copying a competitor store's strengths onto your own store**
Handling: first judge whether the strength is replicable (ad-spend scale / in-house creator matrix are often un-copyable), distinguish "what's learnable" from "what's unique to them", and hand the user only what's actionable.
