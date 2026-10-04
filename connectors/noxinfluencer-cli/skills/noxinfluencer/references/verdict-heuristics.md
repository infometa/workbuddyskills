# Verdict Heuristics Reference

Detailed heuristic rules and output structure for creator due-diligence verdicts.

## Verdict Levels

### 1. High-priority collaboration candidate

All of the following hold:

- No meaningful dispute signal
- Audience quality is healthy (authenticity status is positive, no suspicious audience dominance)
- Performance is competitive for the niche (benchmark rank is above median)
- Pricing and cooperation signals do not show obvious friction (reasonable response time, acceptable pricing range)

### 2. Viable, but with clear risks

Overall profile is workable, but one or two notable concerns exist:

- Weak cooperation signals (low cooperation score, few brand partnerships)
- Performance volatility (high wave value, inconsistent engagement)
- Questionable pricing efficiency (large gap between first and final price)
- Audience demographic mismatch for the stated campaign goal

### 3. Needs manual review before proceeding

The evidence is mixed and a firm recommendation would be misleading:

- Commercial reasonableness cannot be judged confidently from available data
- One critical dimension is unclear or data is incomplete
- Conflicting signals across dimensions (strong performance but poor audience quality, or vice versa)

### 4. Not a priority collaboration candidate

Multiple weak signals appear:

- Disputes or negative cooperation history
- Poor audience quality (low authenticity, suspicious audience types)
- Below-benchmark performance across multiple metrics
- Creator is clearly a poor fit for the stated collaboration goal

## Due-Diligence Output Structure

After the verdict, organize evidence into these sections:

### 1. Data Performance

- Average views and engagement rate
- Stability: wave value and views change ratio
- Benchmark position: rank and percentile vs. peers
- Content-type splits if relevant (normal vs. shorts/reels)
- Level indicators (1-5 scale): avg_views_level, wave_level, engagement_rate_level

### 2. Audience Quality

- Audience authenticity (value, status, ratio range)
- Audience type distribution (real, suspicious, inactive)
- Demographic fit: region, language, age, gender distributions
- Marketing indicators: positive_audience_pct, promo_interested_audience_pct, promo_attractiveness, promo_professionalism

### 3. Cooperation Risk

- Dispute types (if any)
- Cooperation score and tendency
- Cooperation pros and cons lists
- Ad video ratio and frequency

### 4. Commercial Reasonableness

- Estimated price range (avg, min, max)
- First price vs. final price gap
- Response speed (avg_response_hours)
- Collaboration efficiency (avg_contact_days, avg_contact_chats, avg_collaboration_days)
- Active period and communication patterns
- Existing brand partnerships (brand names, video counts, engagement rates)

### 5. Final Recommendation

- Whether to continue toward outreach
- What should be double-checked manually
- Whether the next step should be contact retrieval or shortlist replacement

## Interpretation Principles

- Dispute history and negative cooperation signals are decision-critical — always surface them prominently.
- Benchmark position provides context but is not the sole determinant.
- Pricing reasonableness should be evaluated relative to performance, audience quality, and cooperation signals, not in isolation.
- When evidence is mixed, prefer "Needs manual review" over false confidence.
- When two or more critical dimensions are missing or platform-limited, do not force a confident verdict.
- When only one dimension was checked, present the answer as a scoped judgment, not a full verdict.
