---
name: sparkx-search-term-diagnosis
description: >-
  Diagnose where ad spend goes at the search-term level: tag every search term (keyword vs
  ASIN, branded vs non-branded, order tier), then report spend distribution, brand vs
  non-brand, zero-order waste with negative candidates, harvest candidates for exact match,
  and fragmented exact keywords - with fixed, reproducible rules and thresholds derived from
  the store's own order value and target ACOS. Read-only; execution goes to sparkx-edit-ads.
  Use when the user asks "上个月钱花哪了", "帮我找一批该否的词", "自动广告里哪些词值得单独投",
  "search term analysis", "negative keyword candidates", "harvest keywords". Not for
  trend recaps (sparkx-weekly-ads-report / sparkx-monthly-ads-report), campaign-type /
  marketplace structure (sparkx-ads-structure-analysis) or ASIN health
  (sparkx-product-diagnosis).
metadata:
  version: 1.0.4
---

# Search Term Diagnosis (搜索词流量结构诊断)

## Scope: a read-only orchestration skill

No MCP tool of its own. It reads with three tools and hands execution to one skill:

| What | Tool | Owning skill - read it first |
|---|---|---|
| Search terms, keyword performance, totals | `get_ads_perf` | [sparkx-query-ads-performance](../sparkx-query-ads-performance/SKILL.md) |
| Exact keywords and existing negatives, campaigns, managed groups, brand names | `get_entity_metadata` | [sparkx-query-entity-metadata](../sparkx-query-entity-metadata/SKILL.md) |
| Keyword creation/change history and recent campaign/ad-group changes | `get_operation_log` | [sparkx-query-operation-log](../sparkx-query-operation-log/SKILL.md) |
| Adding negatives / exact keywords, pausing a keyword | `batch_update_ads` | [sparkx-edit-ads](../sparkx-edit-ads/SKILL.md) |

> **Dependency - install the four skills above alongside this one.** Skills install as
> sibling directories under your agent's skills root (see the
> the installation notes in [README](../README.md)); the `../sparkx-.../` links resolve against it.
> Auth, errors, pagination, date limits and currency rules are in the query skills'
> `references/platform-notes.md` - read it once.

| Reference | Read it when |
|---|---|
| [`references/data-retrieval.md`](references/data-retrieval.md) | Pulling data: which calls, in what order, and the gotchas (filter semantics, field names, paging) |
| [`references/classification.md`](references/classification.md) | Tagging and the five views: exact rules, thresholds, tie-breaks, the reference script |

## Output language

Examples are in Chinese because most customers are. Answer in the user's language and pass
`language` to `get_ads_perf` to match.

## Principles

1. **Classification is computation, not judgement.** Labels and thresholds are fixed rules
   (see `classification.md`). Run them as code when you can; never re-label a term by feel.
   The same data must produce the same lists and totals every time.
2. **Thresholds come from the customer's own numbers** - average order value and one
   store-wide target ACOS - never a fixed dollar amount.
3. **Describe, then prescribe.** Spend distribution and brand share are descriptions. Only
   the zero-order list, harvest list and fragments carry actions.
4. **Brand terms are an input.** Pre-fill them, never decide them: a brand name can be a
   common word.
5. **Don't fight the AI, don't hide from it.** Terms in managed groups that already run
   automatic negation or harvesting are still listed - labelled, not skipped.
6. **Read-only.** Every change goes through `sparkx-edit-ads` with its own preview and
   confirmation.
7. **Current state beats historical spend.** Before proposing a negative, check current
   negative keyword/target coverage at every source campaign or ad group. Historical spend
   does not prove a term is still leaking after a negative was added.
8. **Protect proven terms and young experiments.** A currently weak exact keyword that
   converted in the immediately preceding equal-length period is a diagnostic case, not a
   direct pause. A young or low-click exact keyword is insufficient evidence, not a
   consolidation candidate.

## Workflow

### Step 1 - Scope and three inputs

Resolve the store with `get_user_authorized_context`. **One store per run** - thresholds
are in the store's currency and order value.

- **Period**: default the 30 days ending **3 days before today** (e.g. asked on 10/12 ->
  9/10-10/9). The last few days' orders may not be attributed yet, which would make
  zero-order judgements too harsh. Say so in the answer. Other periods are fine; order
  thresholds are scaled to 30 days (`classification.md`).
- **Scope**: whole store by default; named campaigns, or a product (ASIN / parent ASIN) -
  for a product the result is the search terms of the ad groups that contain it, not traffic
  attributed to the ASIN (`data-retrieval.md` -> Narrowing the scope).

Pull data-retrieval calls 1, 3 and 9 first - the pre-fills below come from them. Then confirm
three inputs, the first two **pre-filled by you**:

1. **Brand terms.** Pre-fill the brand from `get_entity_metadata(entity='asin')` ->
   `asinBrand`, then list candidates found in the period's search terms: sub-brands and
   product-line names that appear in the store's own `asinTitle`s, other spellings of the
   brand (spacing, other scripts), and close misspellings. Let the customer tick them and
   add more, including competitor brand terms if they want. Never treat an unconfirmed
   candidate as a brand term.
2. **Target ACOS** - one number for the whole store: "你整店希望 ACOS 控制在多少？". If the
   customer has none, use the **unfiltered whole-store ACOS** for the period and say in the first line of the
   answer that the thresholds use it and can be recomputed. **Do not use managed-group
   target ACOS as the threshold** - stores have dozens of groups with targets that vary
   widely and are often set high on purpose; managed groups are only used to label switches.
   A product/campaign-scoped run therefore needs a separate unfiltered store-total call for
   this fallback; never derive the fallback from the scoped total.

3. **Product stage** - mature, or new / in launch. It sets the harvest threshold (4 vs 2
   orders in 30 days). Ask; do not infer it from listing dates.

Optional: a **negative whitelist** of word roots that must never be proposed as negatives
(e.g. brand / model / year roots for compatibility products). Ask once; reuse the inputs in
later runs in the same conversation.

### Step 2 - Pull the data

Full call plan and gotchas: [`references/data-retrieval.md`](references/data-retrieval.md).
In short: scoped totals plus an unfiltered store total for the fallback target; search terms
with orders; zero-order terms above the threshold; source match types; exact keywords in use
and their current/prior performance; current negative coverage; candidate keyword age/change
history; brand data; managed-group switches for the listed terms only. **Do not page through every search term** - the zero-order small
terms are derived from totals.

### Step 3 - Classify and save

Apply [`references/classification.md`](references/classification.md) and **save the result to
a file first** (one row per search term with its labels and numbers, plus the totals). The
answer and any export are built from that file, never from a fresh query or a recomputation,
so the conversation and the file always agree.

### Step 4 - Answer

Lead with the scope line, then five short parts:

1. **钱花在哪 (V1)**: a small table - core (≥3 orders), potential (1-2), zero-order above the
   one-order target spend, zero-order small terms - with spend, share and ACOS; keyword and
   ASIN traffic shown separately where it matters. Zero-order small terms are one line with
   their amount; never list them term by term. Then add **where small unconverted spend comes
   from**, measured at search term x match type (`data-retrieval.md`) and named as such -
   e.g. "没出单的小额流量（按搜索词 × 匹配方式计）里，48% 来自自动广告的宽泛匹配" - plus the top
   campaigns when search-term x campaign detail was pulled. Point to where to look (harvest the
   good terms there, check its negatives, split it out to watch it); don't recommend pausing a
   match type on this number alone.
2. **品牌 / 公域 (V2)**: brand share of the listed keyword spend (say "已列出的关键词花费"), brand
   ACOS, non-brand ACOS and the ratio,
   and the direction (`classification.md` -> V2). Skip V2 with a reason if the customer
   declined to give brand terms.
3. **零单浪费 (V3)**, in three groups (`classification.md` -> V3):
   - **zero-order exact keywords** - your own exact keywords with no orders and spend above
     the threshold. Pause only when the immediately preceding equal-length period also had
     zero orders. If it previously converted, label it **historically proven, investigate**
     and show the prior performance, relevant changes, and any other enabled exact keyword
     carrying the same normalized text;
   - **negative candidates** - count, spend, top 10, each with its action (negative exact for
     keywords, negative product targeting for ASINs) and a label when the managed group
     already has automatic negative targeting on. Subtract current negative coverage first:
     fully covered terms are **already handled**, partially covered terms list only the
     uncovered source campaigns/ad groups, and only uncovered destinations remain actionable;
   - **zero-order terms you also target as exact keywords** - not proposed as negatives;
     say where the spend came from and leave it to the customer.

   Brand terms, the store's own ASINs and whitelisted roots are held back and counted at the
   end.
4. **扶正候选 (V4)**: count, orders, top 10 with source match type. Mention managed groups whose
   harvesting is off.
5. **投放碎片 (V5)**: enabled exact keywords with ≤3 orders in 30 days - count, zero-order
   count and spend. Split them into **eligible for review** versus **insufficient sample**.
   A fold-back suggestion for a mature product requires at least 14 complete observed days and
   10 clicks; unknown age is insufficient evidence. Never use campaign age as keyword age.

End with: "要完整清单文件吗？要执行哪些？"

### Step 5 - Export and hand-off

- **Export** (only if asked): four sheets from the saved file - all tagged search terms,
  negative candidates, harvest candidates, fragmented keywords. Counts and spend must match the
  answer exactly.
- **Execution**: this skill writes nothing. For "把这些否了" / "这些加成精准" / "暂停这个词",
  hand the rows - with campaign type, campaign and ad group from data-retrieval call 10 - to
  `sparkx-edit-ads` and follow its resolution, preview and confirmation rules. Its route
  limits decide what is possible:
  - SP keyword negatives: `negativeKeyword + create` (campaign level, SP only);
  - SB keyword negatives: `negativeKeyword + copy` to the ad group (SB accepts ad-group level
    only);
  - ASIN negatives: `negativeTarget + create` at ad-group level, and only into a
    product-targeting ad group - edit-ads refuses others;
  - harvest: `keyword + create` (SP / SB); pause: `keyword + updateStatus`.

  Suggest re-running in about 30 days.

## Example

> **客户**：看看上个月搜索词，钱花哪了。
>
> **AI**：先确认口径：① 品牌词：商品信息里的品牌名是 “Acme”，搜索词里还出现了 “acme pro”“akme”——这两个算你们的品牌词吗？② 目标 ACOS：你整店希望 ACOS 控制在多少？没有的话，我先按店铺近 30 天的实际 ACOS 32% 算。③ 产品是成熟期还是新品推广期？
>
> **客户**：都算；目标按 35%；成熟期。
>
> **AI**：9/10–10/9（最近 3 天的订单可能还没归因完，未计入）搜索词花费 $18,420：
> - **钱花在哪**：出单 ≥3 的核心词占 41%、ACOS 22%；零单、且已花超过一单目标花费（$14）的词占 13%；另有 24% 花在大量零单小词上，其中 52% 来自自动广告的宽泛匹配。
> - **品牌 / 公域**：品牌词占关键词花费 12%、ACOS 9%；非品牌 ACOS 是品牌的 3.4 倍——主要靠公域。
> - **零单浪费**：你在投的精准词里有 7 个 0 单、合计 $260，例如 “water jug” 花了 $41 → 建议暂停；否词候选 63 个、$2,410，例如 “replacement filter cartridge” 花了 $96、0 单 → 精准否定，其中 21 个在已开“添加否定定向”的托管组里，已标出；另有 4 个零单词本身也是你在投的精准词，没有列为否词。
> - **扶正候选 18 个**：例如 “water filter pitcher” 在自动广告里 30 天 6 单、ACOS 24%，还没有单独精准投放。
> - **投放碎片**：启用中的精准词 310 个，30 天 ≤3 单的 190 个，合计只花 $640。
>
> 要完整清单文件吗？要执行哪些？

## Data boundaries

- **Search-term report only covers what it covers.** SP and SB search terms are both in it
  (verified 2026-10 on a store with SB: 99.8% of SB spend). SD has no search terms.
- **Attribution lag.** The default period stops 3 days before today; if the user insists on
  including recent days, warn that zero-order counts will be overstated.
- **Totals vs listed rows.** Zero-order small terms are derived as total minus listed parts,
  so they have an amount and a source split but no term list.
- **No bids.** This skill never suggests bid values or bid changes, including "lower the bid";
  a zero-order exact keyword gets "pause", not "bid down".
- **Not covered**: keyword-ranking feasibility, cannibalisation between variants, listing /
  stock / price attribution.

## Error handling

| Situation | Handling |
|---|---|
| A metric filter returns `unknown field` | The metric must also be in `metrics` (see `data-retrieval.md`) |
| A grouped query with a metric filter returns nothing | Metric filters apply after grouping - see `data-retrieval.md` |
| `hasNextPage` stays true | Keep paging; never classify on a partial page set |
| Very little spend in the period (a few hundred in store currency) | Say the sample is thin and the lists are indicative |
| Customer declines brand terms | Skip V2 and say why; keep the other views |
