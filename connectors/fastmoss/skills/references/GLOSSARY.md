# FastMoss Domain Reference (judgment method + tool-selection + term mapping)

> On-demand reference for FM Agent skills, offloaded from the always-resident MCP instruction to save context.
> Load `references/GLOSSARY.md` when you need: the core judgment method, the
> tool-selection-by-intent map, or any FastMoss / TTS term, metric, stage label, or L0-L6 tier definition.
> Sub-skills remain authoritative for their own domain; this file is the shared fallback and glossary.

## Core judgment method (after understanding the user's terminology, query and judge by this method)

- **Leading indicators first**: TikTok e-commerce is content-driven. GMV is a lagging result; the increment in associated creators/videos is the leading indicator, typically leading GMV by about one week. To judge whether a product is rising or declining and whether it is worth following, first look at the recent creator/video increment (use `product_creator_analysis` with `time_range_days`, and `product_video_list`), not just current-period GMV. Creators/videos flooding in = likely still rising; increment stalling or turning negative = momentum has peaked and is declining.
- **Channel attribution entry point**: to judge "how it sold / ad-driven vs organically viral / channel structure", use `product_overview`'s (or `shop_sale_analysis`'s) `ads_distribution`, `channel_distribution`, and `content_distribution` — giving the shares of ad vs organic, creator vs shop-own vs product card, and short video vs livestream vs product card respectively. A bestseller's "sudden ramp" can almost always be explained within these three blocks.
- **Creator Level must be computed yourself**: L0-L6 is not returned directly by the analysis tools. Use `creator_search` to get the creator's `day28_gmv` (trailing-28-day GMV, approximately monthly GMV), then apply the monthly-GMV tier table (see the L-series definition below) to derive the Level. `creator_search` also returns `has_email`, so you can judge email-outreach reachability. `total_gmv` is cumulative/historical and must not be used for tiering.

## Tool selection by intent

- When the user only gives a creator nickname, shop name, product name, livestream title, or video title, first use the search tools to resolve the UID / seller_id / product_id / room_id / video_id, then call the detail or analysis tools.
- When the user asks "who is selling / which creators are promoting / which videos or livestreams are pushing it", prefer the list or analysis tools over plain detail tools. Distinguish two intents: "who is selling this product" describes the status quo (directly view the product's associated creators/videos); "who is a good fit to sell MY product" is a recommendation (find comparable products' selling creators by category, audience, and price, then match) — the two need different tool combinations.
- When the user asks judgment questions like "bestseller / potential / blue ocean / new product / worth follow-selling / worth partnering", prefer the ranking, trend, product-analysis, creator-analysis, and category-analysis tools; interpret the terms via the term mapping below, then conclude using the core judgment method above.
- When the user asks about "organic / product card / short-video selling / livestream selling / ad promotion / VSA / LSA / PSA / how it went viral", prefer the channel and ad breakdown data from `product_overview` / `shop_sale_analysis`.
- When the user uses slang, jargon, abbreviations, or business labels, first map them to standard FastMoss concepts (term mapping below), then decide on tools, filters, and answer framing.

## Term mapping (query_interpretation)

### product_status (single products use the "four lifecycle stages"; categories use "opportunity product" — two independent systems)

- A single product's lifecycle splits into four mutually exclusive stages along a timeline, judged mainly by creator/video increment (leading) + GMV + launch time + ranking:
  - **New stage**: listed within 30 days + small cumulative GMV + only sporadic creators/videos just starting. The follow-selling window is unvalidated — it is a gamble.
  - **Growth stage**: associated creator/video counts surging period-over-period + consecutive positive period-over-period growth + ranking climbing fast (GMV may not fully reflect it yet). Conversion is validated and creators are flooding in — the best follow-selling window.
  - **Viral stage**: GMV is top of category + stable ranking + creator/video increment slowing from its peak but still incoming + large cumulative GMV. Near saturation — can follow but needs differentiation.
  - **Steady (plateau) stage**: very large cumulative GMV + creator/video increment stalled or turned negative + single-digit growth rate + ranking stable and hard to climb. Window closed — follow-selling means being the bag-holder.
- When the user says "bestseller/viral product", they usually mean the viral stage, but use creator/video increment to tell whether it is a "still-hot viral stage" or a "window-closed steady stage" — the product with the highest cumulative GMV is often in the steady stage, so do not judge it worth following just because GMV is large.
- When the user says "potential product", they usually mean the growth stage (validated and scaling up); distinguish it from the "new stage" (pure gamble, unvalidated).
- When the user says "blue-ocean / opportunity product", read it as a category-structure opportunity: large total category GMV but few entering merchants and no top-tier monopoly; it is strategic guidance — judge together with category growth, merchant count, and concentration.
- When the user says "new / newly listed", use FM's definition of listed within 30 days (not the industry-common 90 days), and proactively flag this definitional difference in your answer.
- When the user says "worth follow-selling", read it as the product being in the growth or viral stage + current creator competition not too high; give a "for reference only" composite judgment.
- When the user says "follow-sell product", read it primarily as a "same/similar competing product" — products that heavily overlap with the target bestseller in category, price band, or use case.
- When the user mentions L0-L6, read it as magnitude labels tiered by monthly GMV: L0 < $1K, L1 $1K-$5K, L2 $5K-$25K, L3 $25K-$60K, L4 $60K-$150K, L5 $150K-$400K, L6 > $400K. For products take their monthly GMV; for creators take `day28_gmv` (see core judgment method; must be computed yourself — the tools do not return this label directly).

### creator_collaboration

- When the user says "selling creator", read it as a creator with TikTok Shop e-commerce authorization enabled, not gated on whether they have already generated sales.
- A creator's selling power is based mainly on "trailing-30-day selling GMV / average GMV per video", not on follower count — follower count and selling GMV are highly decoupled, so do not rank or conclude by followers.
- When the user says "selling efficiency", read it as video selling-conversion efficiency, assessable from total video units sold vs total views.
- When the user says "publish rate", map it primarily to "fulfillment rate" = videos actually published / SKUs of samples received.
- When the user says "order rate", read it as videos with actual sales / total selling videos.
- When the user says "worth partnering", combine: whether there were sales in the last 28 days, whether engagement rate is above the peer median, whether fulfillment rate meets the bar, plus Level (current activity). High cumulative GMV for this product but low current Level = a past mainstay now gone cold, so outreach value is discounted.
- When the user says "high-ROI creator", read it as a creator whose selling GMV is high relative to acquisition cost; when cost data is missing, state that the conclusion depends on sampling and commission assumptions.
- When the user says "collaboration decision report", structure it to cover basic profile, last-28-day selling data, follower-profile match, and a final partnership recommendation.
- When the user says "showcase", read it as the product display area within a creator's account; "creator invitation" is a merchant initiating a collaboration invite via the TikTok Shop seller backend.

### time_and_growth

- Default time window: when the user says "recent / lately / current", interpret it as the last 28 days by default; if they explicitly say last 7 / 14 / 90 days, pass that literally. "Last week" = the previous natural week; "yesterday" = the T-1 natural day in the target market's time zone.
- When the user says "month-over-month", read it as this month vs last month, or the last 30 days vs the prior 30 days on the same basis; "day-over-day" is yesterday vs the day before.
- When the user says "ramp up", read it as units growing continuously from near zero, often describing a new product breaking out of cold start.
- When the user says "period-over-period growth", read it as the rate of change vs the previous same-length period; prefer trend tools to verify.

### traffic_and_content

- When the user says "short-video creator selling", read it as sales from creator short videos with attached product links; prefer video analysis or a product's associated video list.
- When the user says "livestream selling", read it as real-time sales from livestreams with attached products and voiceover; prefer livestream analysis, livestream detail, or livestream product list.
- When the user says "product card", read it as sales from entering the product page directly via TikTok Shop search or recommendation, not triggered by creator videos.
- When the user says "organic", read it as exposure and sales not relying on paid promotion, which may include product card and algorithmic-recommendation traffic.
- When the user says "creator-matrix saturation", read it as the same product collaborating with many creators simultaneously to post videos, forming scaled distribution.
- "TTS" = TikTok Shop; "Affiliate Marketplace" = the affiliate platform within TikTok Shop where creators self-select products to sell.
- "FYP" = For You Page recommendation feed, a content-distribution context, not a standalone tool object.

### store_types

- "Cross-border store" = a store not registered in the target market, usually shipping direct from China; "local store" = registered locally in the target market with local fulfillment.
- "ACCU store" = a local-store form registered as a US company controlled by a Chinese entity, generally treated as a local store but with an added compliance-risk context.
- "Business store" = a store registered under a corporate legal entity, with relatively more complete qualifications and credit backing.

### ads_and_metrics

- For "GMV / sales", standardize on "sales (GMV)" phrasing to avoid ambiguity.
- "Daily sales" = actual orders transacted in a single day.
- "TTAM" = TikTok Ads Manager; "TSP" = TikTok official certified service provider.
- "VSA / LSA / PSA" = Video Shopping Ads / Live Shopping Ads / Product Shopping Ads respectively; map them to an ad-placement or channel-breakdown context (use the ad breakdown from `product_overview` / `shop_sale_analysis`).
- "ROAS" = return on ad spend (revenue / spend); when spend data is missing, note that it cannot be computed precisely.
- "oCPM" = optimized cost per mille; "CPA" = cost per action/conversion.
- "ad creative" = ad creative content; "runaway spend" = an out-of-control state where budget burns too fast but conversion is weak.
