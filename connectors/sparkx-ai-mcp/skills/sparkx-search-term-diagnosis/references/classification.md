# Classification rules

Every rule here is mechanical. Apply it as code when you can (a reference script is at the
end); never adjust a label by judgement. Same input, same output.

## Inputs

- `TOTAL`: spend, sales, orders of all search terms (data-retrieval call 1).
- `ORDERING`: per search term, spend / sales / clicks / orders, orders > 0 (call 3).
- `ZERO_HIGH`: per search term, orders = 0 and spend >= `T` (call 4).
- `SOURCES`: per search term, the set of match types it had orders under (call 5).
- `EXACT`: enabled exact keywords (call 7); `EXACT_PERF`: their performance (call 8).
- `BRAND`: confirmed brand terms; `WHITELIST`: confirmed never-negate roots; `OWN_ASINS`.
- `TARGET_ACOS`: the confirmed store-wide target, else `STORE_TOTAL.spend / STORE_TOTAL.sales`.
  `STORE_TOTAL` is the same as `TOTAL` only for a whole-store run; a scoped run gets it from
  the separate unfiltered call 1a.
- `TOTAL` is **one** object: call 1 returns a row per ad type - sum them first.
- `STAGE`: mature or new / launch - asked in Step 1, never inferred.
- `DAYS`: period length.

Units - one rule everywhere: **ratios are fractions inside the computation.** A customer's
"35%" and `get_ads_perf`'s `ACOS` value `35` both become `0.35`; `TOTAL.spend / TOTAL.sales`
already is one. Convert back to a percentage only when writing the answer. Mixing the two
inflates `T` a hundredfold.

Derived:

- `AOV` = `TOTAL.sales / TOTAL.orders`. If the period has no orders or no sales, stop: there is
  no order value or ACOS to derive thresholds from - say so instead of classifying.
- `T` (one order's target spend) = `AOV x TARGET_ACOS`.
- `SCALE` = `30 / DAYS`; order **thresholds** compare `orders x SCALE`. Whether a term has
  orders at all is always decided on the raw count.

## Three labels per search term

| Label | Values | Rule |
|---|---|---|
| Entry | keyword / ASIN | ASIN when the whole term matches `^b0[0-9a-z]{8}$` (case-insensitive) |
| Brand | brand / non-brand | Keyword entry only. Brand when the term contains any confirmed brand term. A brand term written in Latin letters (accents, hyphens and apostrophes allowed) must match as a whole word or phrase - `pro` matches "acme pro filter", not "protein"; a brand term in another script matches as a substring, ignoring spaces |
| Order tier | core / potential / zero-high / zero-small | raw orders = 0: **zero-high** if spend >= `T`, else **zero-small** (not listed, see data-retrieval). Raw orders > 0: **core** if orders x SCALE >= 3, else **potential** |

## V1 - where the money goes

Spend, share of `TOTAL.spend`, orders and ACOS per tier, keyword and ASIN entry shown
separately; zero-small as one line with its amount. Then, as a separate line, the small
unconverted spend by source (data-retrieval -> the zero-order small terms) - a different,
finer measure; never present its shares as "the source of the zero-small terms". Description
only - a large long tail is not a finding on its own.

## V2 - brand vs non-brand

Keyword-entry terms in the listed tiers (core, potential, zero-high) - zero-small terms are
not listed, so they can't be tagged. Report the brand share **of the listed keyword spend**
(say it that way), brand ACOS, non-brand ACOS, and non-brand ACOS / brand ACOS. Direction, no
score:

- **Brand share high and non-brand ACOS several times brand**: a brand-led store. Ask what
  the customer wants - only to capture branded demand (defend brand terms), or to grow
  non-branded traffic (accept higher non-brand ACOS for a while).
- **Brand share low**: growth depends on non-branded traffic, so price and product decide;
  keep brand terms profitable, don't push volume there.

Skip V2 and say why when the customer gave no brand terms. Backtests showed the answer flips
with the brand list (5.6% with the brand name only vs about 27% with sub-brands added), so
never guess the list.

## V3 - zero-order waste, in three groups

**V3a - zero-order exact keywords, with a history guard.** From `EXACT_PERF`: enabled exact
keywords with raw orders = 0 and their **own** spend >= `T`. Join the same Amazon keyword id
to the immediately preceding equal-length period (call 13):

- prior raw orders = 0: **pause candidate** (no bid advice);
- prior raw orders > 0: **historically proven, investigate** - do not propose a pause. Show
  both periods, relevant operation history, and every other enabled exact keyword with the
  same normalized text. Another keyword with the same text is evidence of overlap, not proof
  that traffic was deliberately migrated.

Each row names the keyword, campaign and internal `keywordId` (call 7 joined on
`amazonKeywordId`). A missing prior row is unknown history, not zero; label it insufficient
history and do not promote it to a direct pause.

**V3b - negative candidates.** Zero-high search terms, sorted by spend, minus:

- brand terms, own ASINs, terms containing a whitelisted root → **held back**, counted at the
  end ("品牌词 / 自家 ASIN / 白名单拦截 N 条");
- terms whose text equals an enabled exact keyword → group V3c.

Action: ASIN entry → negative product targeting; keyword entry → negative exact. Each row
also carries the campaign type, campaign and ad group the spend came from (call 10), which
decide how `sparkx-edit-ads` can add it (see SKILL.md Step 5).

Before the row is actionable, subtract current coverage from calls 14-15 at each source
destination. Fully covered rows become **already handled** and leave the action list. Partially
covered rows retain only uncovered destinations and explicitly list both sets. Match the exact
negative action being proposed: a different match type does not prove exact-negative coverage.

**V3c - zero-order terms you also target as exact keywords.** The customer chose to target
these, so they are not proposed as negatives. Show where the zero-order spend came from (the
exact keyword itself, which V3a already covers when it crossed `T`, or other campaigns'
broad / phrase / auto); negating the term in those other campaigns is the customer's call.

Then the managed-group label (data-retrieval calls 10-12) on V3b rows: "托管组已开自动否定"
when every campaign the term spent in is in a group with automatic negative targeting on.
Labelled rows stay in the list.

**Root negation is optional** - only when the customer asks: a token that appears in at least
3 V3b keyword terms, never in any ordering keyword term, with combined spend >= `T`, is a
phrase-negative candidate. In both backtest stores this produced nothing, so it is not a
default view.

Backtest (2026-10, store ACOS as target): manual store - V3a 9 keywords ($238), V3b 175
terms ($3,102), V3c 11 terms ($190); AI-managed store - V3a 26 ($1,403), V3b 107 ($3,306),
V3c 61 ($2,800).

## V4 - harvest candidates

Keyword-entry terms where all of the following hold:

- orders x SCALE >= **4** when `STAGE` is mature, >= **2** when new / launch;
- ACOS <= `TARGET_ACOS`;
- the term had orders under an open match type (`LOOSE-MATCH`, `CLOSE-MATCH`, `broad`,
  `phrase`);
- the term is not already an enabled exact keyword;
- the term is not a pasted product title: more than 8 words or containing a comma.

Sort by orders. Mark brand terms (they go into a brand exact group). Add "托管组未开定向收割"
when the term's managed groups all have harvesting off.

## V5 - fragmented exact keywords

From `EXACT_PERF`, enabled exact keywords with orders x SCALE <= 3: count, how many have zero
orders, spend, and their share of all exact-keyword spend. Also say how many enabled exact
keywords had no data at all in the period: count **keyword entities** - `EXACT` rows whose
`amazonKeywordId` has no `targetId` in `EXACT_PERF` - not distinct texts (the same text often
exists in several ad groups).
Split this population by evidence sufficiency. A keyword is eligible for a mature-product
fold-back review only when it has **at least 14 complete observed days and at least 10 clicks**.
Both gates must pass. Creation-event history is preferred; first observed daily performance is
only a lower bound. Unknown age, fewer than 14 days, or fewer than 10 clicks means **insufficient
sample - continue observing**, not fold back. Never substitute campaign age for keyword age.

## Reference script

Inputs are the saved query results; output is the file the answer and export are built from.
Managed-group labels, campaign/ad-group destinations and negative coverage are added afterwards
from calls 10-15. `exact_evidence` comes from call 16 and is keyed by Amazon keyword id.

```python
import re

def norm_rows(rows):
    """Response keys -> bare names: 'campaign.campaignId_' / 'campaignId_' / 'campaignId' -> 'campaignId'."""
    return [{k.rsplit('.', 1)[-1].rstrip('_'): v for k, v in r.items()} for r in rows]

def sum_total(call1_rows):
    keys = ('Spend', 'Sales', 'Clicks', 'Conversions')
    return {k: sum((r.get(k) or 0) for r in call1_rows) for k in keys}

def as_fraction(acos):
    """'35%' -> 0.35, '0.5%' -> 0.005 (a % sign always means percent);
    35 (get_ads_perf ACOS) -> 0.35; 0.35 -> 0.35. A bare number <= 1 is read as a fraction -
    if the customer typed a bare '1' meaning 1%, ask."""
    s = str(acos).strip()
    if s.endswith('%'):
        return float(s[:-1]) / 100
    v = float(s)
    return v / 100 if v > 1 else v

LATIN = re.compile(r"[a-z0-9 '\-À-ɏ]+")

def has_term(q, terms):
    ql = q.lower()
    for t in (t.lower().strip() for t in terms):
        if LATIN.fullmatch(t):
            if re.search(r"(?<![a-z0-9À-ɏ])" + re.escape(t) + r"(?![a-z0-9À-ɏ])", ql):
                return True
        elif t.replace(' ', '') in ql.replace(' ', ''):
            return True
    return False

def diagnose(total, ordering, zero_high, sources, exact_texts, exact_ids, exact_perf,
             brand, whitelist, own_asins, target_acos=None, store_total=None,
             prior_exact_perf=None, exact_evidence=None, days=30, mature=True):
    """All row lists already passed through norm_rows; total from sum_total.
    exact_texts, own_asins: lower-cased sets; exact_ids: set of str(amazonKeywordId) (call 7).
    sources: {lower-cased term: set of match types}.
    exact_perf rows: targetId, targetText, targetState, Spend, Sales, Conversions (call 8)."""
    if not total['Conversions'] or not total['Sales']:
        raise ValueError('no orders or no sales in the period - cannot derive thresholds')
    aov = total['Sales'] / total['Conversions']
    fallback = store_total or total
    if target_acos is None and not fallback.get('Sales'):
        raise ValueError('whole-store sales are zero - cannot derive fallback target ACOS')
    tacos = (as_fraction(target_acos) if target_acos is not None
             else fallback['Spend'] / fallback['Sales'])
    T, scale = aov * tacos, 30 / days
    is_asin = lambda q: re.fullmatch(r'b0[0-9a-z]{8}', q.lower()) is not None

    rows = []
    for x in ordering + zero_high:
        q, n = x['query'], x['Conversions']
        if n == 0 and x['Spend'] < T:
            continue                                   # zero-small: measured, not listed
        tier = ('core' if n * scale >= 3 else 'potential') if n > 0 else 'zero-high'
        rows.append(dict(query=q, spend=x['Spend'], sales=x['Sales'], orders=n, tier=tier,
                         entry='ASIN' if is_asin(q) else 'keyword',
                         brand=(not is_asin(q)) and has_term(q, brand)))

    for r in rows:
        q = r['query'].lower()
        r['v3'] = None
        if r['tier'] == 'zero-high':
            if r['brand'] or q in own_asins or has_term(q, whitelist):
                r['v3'] = 'held'
            elif q in exact_texts:
                r['v3'] = 'V3c'
            else:
                r['v3'] = 'negative product target' if r['entry'] == 'ASIN' else 'negative exact'

    th = 4 if mature else 2
    open_types = {'LOOSE-MATCH', 'CLOSE-MATCH', 'broad', 'phrase'}
    pasted = lambda q: len(q.split()) > 8 or ',' in q
    for r in rows:
        q = r['query'].lower()
        r['v4'] = bool(r['entry'] == 'keyword' and r['orders'] * scale >= th and r['sales'] > 0
                       and r['spend'] / r['sales'] <= tacos and q not in exact_texts
                       and sources.get(q, set()) & open_types and not pasted(q))

    enabled = [k for k in exact_perf if k['targetState'] == 'enabled']
    prior = {str(k['targetId']): k for k in (prior_exact_perf or [])}
    v3a = []
    for k in enabled:
        if k['Conversions'] != 0 or k['Spend'] < T:
            continue
        old = prior.get(str(k['targetId']))
        action = ('investigate' if old and old.get('Conversions', 0) > 0 else
                  'pause' if old is not None else 'insufficient-history')
        v3a.append({**k, 'prior': old, 'action': action})

    evidence = exact_evidence or {}
    frag = [k for k in enabled if k['Conversions'] * scale <= 3]
    for k in frag:
        ev = evidence.get(str(k['targetId']), {})
        observed_days = ev.get('observedDays')
        enough = observed_days is not None and observed_days >= 14 and (k.get('Clicks') or 0) >= 10
        k['sampleStatus'] = 'eligible-for-review' if enough else 'insufficient-sample'
        k['observedDays'] = observed_days
    exact_spend = sum(k['Spend'] for k in enabled)
    with_data = {str(k['targetId']) for k in exact_perf}
    return dict(threshold=T, target_acos=tacos, rows=rows,
                zero_small_spend=total['Spend'] - sum(r['spend'] for r in rows),
                v3a=v3a,
                v5=dict(n=len(frag), zero=sum(k['Conversions'] == 0 for k in frag),
                        spend=sum(k['Spend'] for k in frag),
                        share=sum(k['Spend'] for k in frag) / exact_spend if exact_spend else 0,
                         eligible=sum(k['sampleStatus'] == 'eligible-for-review' for k in frag),
                         insufficient=sum(k['sampleStatus'] == 'insufficient-sample' for k in frag),
                        no_data=len(exact_ids - with_data)))
```
