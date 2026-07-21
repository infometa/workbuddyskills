#!/usr/bin/env python3
"""
Value-Based Pricing: Pattern Library & Training

A reference library of 10 proven value-based pricing patterns, usable as both
a training tool and a real-time sales assistant.

Usage:
    python3 pricing_pattern_library.py --list
    python3 pricing_pattern_library.py --pattern "anchor-with-data"
    python3 pricing_pattern_library.py --scenario "prospect is a $50M SaaS company spending $15K/mo on marketing"
    python3 pricing_pattern_library.py --quiz
"""

import argparse
import json
import os
import random
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# LLM Integration Stubs
# ---------------------------------------------------------------------------


def _call_llm(prompt: str, system_prompt: str = "") -> str:
    """
    Stub: Call LLM for scenario analysis.

    In production, replace with:
        POST https://api.anthropic.com/v1/messages  (ANTHROPIC_API_KEY)
        POST https://api.openai.com/v1/chat/completions  (OPENAI_API_KEY)
    """
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if anthropic_key:
        # TODO: Implement real Anthropic API call
        # import requests
        # resp = requests.post(
        #     "https://api.anthropic.com/v1/messages",
        #     headers={"x-api-key": anthropic_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        #     json={"model": "claude-sonnet-4-20250514", "max_tokens": 4096, "system": system_prompt, "messages": [{"role": "user", "content": prompt}]},
        # )
        # return resp.json()["content"][0]["text"]
        pass

    if openai_key:
        # TODO: Implement real OpenAI API call
        pass

    return None


# ---------------------------------------------------------------------------
# Pattern Library
# ---------------------------------------------------------------------------
# ALL examples are FULLY ANONYMIZED. No real company names, people, or revenue numbers.

PATTERNS = {
    "anchor-with-data": {
        "name": "Anchor With Data",
        "tagline": "Open with their competitive data, not your pitch. Let the gap sell the urgency.",
        "description": (
            "Before you say a single word about what you do or what you charge, show the prospect "
            "their own competitive landscape. Pull their keyword rankings, traffic data, and "
            "competitor positions. When they see the gap between where they are and where their "
            "competitor is, the urgency sells itself. You're not pitching; you're diagnosing."
        ),
        "when_to_use": [
            "First call with any prospect who has meaningful organic competition",
            "When you need to justify a large deal size",
            "When the prospect thinks they're doing fine (they often don't know the gap)",
            "Especially effective with data-driven or technical decision makers",
        ],
        "example_dialogue": [
            "Rep: 'Before we talk about anything, I pulled some data I thought you'd find interesting. Mind if I share my screen?'",
            "Prospect: 'Sure, go ahead.'",
            "Rep: 'So here's where you rank for your top 10 money keywords. And here's where TechStart Inc ranks for those same keywords. Notice anything?'",
            "Prospect: '...they're ahead on almost all of them.'",
            "Rep: 'Right. And here's what that gap means in traffic. They're getting roughly 45,000 visits per month from these keywords alone. You're getting about 8,000. That's 37,000 visits per month that could be yours.'",
            "Prospect: 'I didn't realize the gap was that big.'",
            "Rep: 'Most people don't until they see it. Want me to walk through what closing that gap would look like?'",
        ],
        "common_mistakes": [
            "Showing data AFTER pitching your services (loses the anchoring effect)",
            "Using data that's not relevant to their specific business goals",
            "Overwhelming with too many data points instead of focusing on 3-5 killer gaps",
            "Not connecting the data to dollar values (traffic alone doesn't motivate; traffic value does)",
        ],
        "success_rate_notes": "Highest-converting opener in our playbook. Calls that lead with competitive data close at 2.3x the rate of calls that lead with capabilities.",
    },
    "tiered-packaging": {
        "name": "Tiered Packaging (S/M/L + Performance)",
        "tagline": "Always present 3-4 options. Anchor high. Land in the middle.",
        "description": (
            "Never present a single price. Always offer 3-4 tiers: a premium anchor (Powerhouse), "
            "your target tier (Value), a stripped-down floor (Baseline), and a performance option "
            "(skin in the game). The premium makes the target look reasonable. The baseline creates "
            "a floor. The performance option catches prospects who stall on fixed pricing."
        ),
        "when_to_use": [
            "Every proposal presentation, without exception",
            "Especially when moving from a small engagement to a larger one",
            "When competing against agencies that only present one price",
            "When the prospect's budget is unclear",
        ],
        "example_dialogue": [
            "Rep: 'Based on what you've told me, I've put together four options. Let me walk you through them.'",
            "Rep: 'Option 1 is our Powerhouse package at $110,000 per month. This is the full-service, senior-strategist-involved, aggressive-growth option. Everything we talked about plus dedicated executive alignment.'",
            "Rep: 'Option 2 is our Value package at $80,000 per month. This covers all the critical growth levers we discussed. It's where most of our successful clients land.'",
            "Rep: 'Option 3 is our Baseline at $35,000 per month. This focuses on the top 2-3 priorities. Good for proving the model before scaling.'",
            "Rep: 'And Option 4 is our Performance package. Lower base at $28,000 per month, but with bonus triggers tied to traffic and revenue outcomes. We put skin in the game.'",
            "Prospect: 'Tell me more about Option 2.'",
            "(This is the expected response. The anchor worked.)",
        ],
        "common_mistakes": [
            "Starting with the cheapest option (kills the anchor effect)",
            "Making tiers too similar (if they can't tell the difference, they'll pick the cheapest)",
            "Not having clear 'what's not included' for lower tiers (scarcity drives upgrades)",
            "Presenting more than 4 options (decision paralysis)",
        ],
        "success_rate_notes": "Deals presented with tiered options average 40% higher closed value vs. single-price proposals. The Value tier is selected ~55% of the time when the anchor is presented first.",
    },
    "competitive-ego-trigger": {
        "name": "Competitive Ego Trigger",
        "tagline": "'Your competitor ranks #1 for [keyword]. You're #14.' Works on every competitive CEO.",
        "description": (
            "Competitive business leaders can't stand losing. When you show them specific, "
            "concrete data about where a competitor is beating them, it triggers an emotional "
            "response that bypasses rational objections. This isn't manipulation; it's showing "
            "them reality they didn't have access to. The key is specificity."
        ),
        "when_to_use": [
            "When the decision maker is a CEO, founder, or other competitive leader",
            "When you have clear data showing competitor advantages",
            "When the prospect thinks they're 'doing okay' with their current approach",
            "NOT when the prospect is already anxious (don't pile on)",
        ],
        "example_dialogue": [
            "Rep: 'I looked at your keyword landscape vs. NovaPay. For the keyword \"enterprise payment processing,\" NovaPay ranks #1. You're #14.'",
            "Prospect: 'We're #14? That can't be right.'",
            "Rep: 'I double-checked. Here's the screenshot from today. And for \"B2B payment solutions,\" they're #2. You're not in the top 50.'",
            "Prospect: '...how is that possible? We have a better product.'",
            "Rep: 'I hear that a lot. Better product doesn't automatically mean better search presence. The good news is, these gaps are closeable. Want me to show you what it would take?'",
        ],
        "common_mistakes": [
            "Being vague ('your competitors are ahead') instead of specific ('#1 vs #14 for [keyword]')",
            "Using this pattern when the competitor is a 10x larger company (makes the gap feel insurmountable)",
            "Not having a solution ready (trigger without a path forward just causes frustration)",
            "Overusing it (pick 2-3 killer examples, not 20)",
        ],
        "success_rate_notes": "Triggers a strong emotional response in ~80% of CEO/founder calls. Follow-up meeting request rate increases by 60% when competitive data is presented vs. generic capability pitches.",
    },
    "strategic-involvement-upsell": {
        "name": "Strategic Involvement Upsell",
        "tagline": "CEO/senior involvement is the premium lever. Same team, add strategy = 3-5x price.",
        "description": (
            "The biggest pricing lever isn't more deliverables. It's senior strategic involvement. "
            "A team executing SEO is worth $15-25K/mo. That same team with a dedicated senior "
            "strategist who joins leadership meetings, aligns marketing with business strategy, "
            "and provides executive-level guidance is worth $60-100K/mo. Same execution, different value layer."
        ),
        "when_to_use": [
            "When moving a prospect from a mid-tier to premium engagement",
            "When the prospect values strategic guidance over tactical execution",
            "When you're competing against cheaper agencies (you can't win on execution cost; win on strategic value)",
            "When the prospect's CEO or C-suite is involved in the buying process",
        ],
        "example_dialogue": [
            "Prospect: 'What's the difference between your $30K and $80K packages? Is it just more content?'",
            "Rep: 'Great question. The execution team is actually very similar. The difference is strategic involvement. At $80K, you get a dedicated senior strategist who joins your leadership team calls, aligns our work with your quarterly business objectives, and provides the kind of strategic guidance that turns marketing from a cost center into a growth engine.'",
            "Rep: 'Think of it this way: at $30K, we're executing a playbook. At $80K, we're building the playbook WITH your leadership team and adapting it in real-time as the business evolves.'",
            "Prospect: 'That makes sense. Our current agency just executes what we tell them.'",
            "Rep: 'And that's exactly the gap we'd fill.'",
        ],
        "common_mistakes": [
            "Positioning the upsell as 'more stuff' instead of 'different level of involvement'",
            "Not having genuine senior talent to back the claim (this falls apart fast if you oversell)",
            "Jumping to the strategic pitch before establishing execution credibility",
            "Not quantifying the value of strategic alignment (tie it to business outcomes, not just marketing metrics)",
        ],
        "success_rate_notes": "The strategic involvement lever is the #1 driver of deals moving from $10-20K/mo to $50-100K/mo range. Average deal size increases 3.2x when strategic involvement is successfully positioned.",
    },
    "bridge-offer": {
        "name": "Bridge Offer",
        "tagline": "'You'll miss Q1 if you hire internally. We bridge the gap.' Creates urgency without being pushy.",
        "description": (
            "When a prospect says they want to build in-house, don't fight it. Agree, then show "
            "them the timeline reality. Hiring takes 3-6 months. Onboarding takes 2-3 more. "
            "Meanwhile, their competitors aren't waiting. Position yourself as the bridge: start "
            "now, build momentum, and hand off when their team is ready (or just keep going because "
            "the results are too good to stop)."
        ),
        "when_to_use": [
            "When the prospect says 'we want to build this capability in-house'",
            "When there's a clear time-sensitive opportunity (seasonal, competitive, market window)",
            "When the prospect is comparing your cost to a hire's salary (reframe the comparison)",
            "Works especially well in tight labor markets",
        ],
        "example_dialogue": [
            "Prospect: 'We're actually thinking about hiring a Head of SEO internally.'",
            "Rep: 'That's smart. Good SEO leadership is valuable. Quick question: when are you hoping to have that person fully ramped and producing results?'",
            "Prospect: 'Ideally by Q2.'",
            "Rep: 'Here's what I typically see: the search takes 2-3 months, then 2-3 months to ramp. So realistically, you're looking at Q3 or Q4 before they're fully contributing. Meanwhile, CloudRetail and your other competitors are investing heavily right now. We can bridge that gap. Start immediately, build the foundation, and either hand off to your new hire or keep working alongside them.'",
            "Prospect: 'Hm, I hadn't thought about the ramp time.'",
            "Rep: 'Most people don't. The bridge model de-risks it for you.'",
        ],
        "common_mistakes": [
            "Arguing against in-house (makes you seem threatened)",
            "Not acknowledging that in-house is a valid long-term strategy",
            "Failing to quantify the cost of delay (make it concrete: 'every month without action is X in lost traffic value')",
            "Not offering a genuine transition plan (if you promise to hand off, have a plan for it)",
        ],
        "success_rate_notes": "Converts ~35% of 'we want to hire in-house' objections into bridge engagements. Average bridge engagement lasts 8+ months (vs. the expected 3-4) because results create retention.",
    },
    "performance-skin-in-game": {
        "name": "Performance Skin-in-Game",
        "tagline": "Lower base + bonus on outcomes. Shows confidence. Often closes deals that stall on fixed pricing.",
        "description": (
            "When a prospect stalls on a fixed monthly fee, offer a performance structure: lower "
            "base price + bonus triggers tied to specific outcomes. This shows confidence in your "
            "ability to deliver and aligns your incentives with theirs. It also reframes the "
            "conversation from 'how much does this cost' to 'what are we both willing to bet on.'"
        ),
        "when_to_use": [
            "When the prospect says 'I love the plan but the price is too high'",
            "When you're confident in your ability to deliver measurable results",
            "When the prospect is risk-averse or has been burned by agencies before",
            "When competing against cheaper agencies (you're not cheaper; you're more confident)",
        ],
        "example_dialogue": [
            "Prospect: 'I like everything you've shown me but $80K per month is a big commitment given our past experience with agencies.'",
            "Rep: 'I hear you. And I respect that you've been burned before. Here's what I'd suggest: we do a performance structure. Base of $35K per month covers our team and core execution. Then we set bonus triggers: if organic traffic increases 50% from baseline, that's a 15% bonus. If revenue attributed to organic exceeds 3x the monthly investment, that's another 20%.'",
            "Rep: 'So if we don't deliver, you're at $35K. If we crush it, we're closer to $55K, but you're making multiples of that in return. We only win big when you win big.'",
            "Prospect: 'That's actually fair. You're putting your money where your mouth is.'",
            "Rep: 'Exactly. And frankly, we set the triggers where we expect to hit them. We wouldn't offer this if we didn't believe in the plan.'",
        ],
        "common_mistakes": [
            "Setting bonus triggers that are easy to game (use business outcomes, not vanity metrics)",
            "Making the base too low (you still need to be profitable at the base)",
            "Not defining measurement methodology upfront (this causes disputes later)",
            "Offering performance pricing when you're not confident in results (it will backfire)",
        ],
        "success_rate_notes": "Closes ~45% of deals that stall on fixed pricing. Average deal value ends up within 10% of the original fixed proposal because bonuses are typically hit.",
    },
    "value-math-on-screen": {
        "name": "Value Math on Screen",
        "tagline": "'If we move this keyword from #14 to #3, that's $X/mo in traffic value.' Make the ROI visual and obvious.",
        "description": (
            "Don't just tell them the ROI. Show them the math. On screen. In real-time. "
            "Pull up their keywords, show the current position, the target position, the search "
            "volume, the CPC, and calculate the traffic value live. When the prospect watches "
            "the number build up keyword by keyword, they're selling themselves."
        ),
        "when_to_use": [
            "During any pricing discussion (make the value visible before discussing cost)",
            "When the prospect asks 'what kind of results can we expect?'",
            "When you need to justify a large deal size",
            "When competing against cheaper alternatives (show what the cheap option misses)",
        ],
        "example_dialogue": [
            "Rep: 'Let me show you the math on just your top 5 keywords. [shares screen]'",
            "Rep: 'Keyword 1: \"enterprise analytics platform.\" You're #14, getting roughly 200 visits/mo. If we move you to #3, that's 1,800 visits/mo. At a CPC of $18.50, that's $33,300/mo in paid equivalent value. Just from one keyword.'",
            "Rep: 'Keyword 2: \"business intelligence software.\" You're #22, getting about 50 visits/mo. Position #3 would be 2,400 visits. At $22 CPC, that's $52,800/mo.'",
            "Rep: 'Just these 5 keywords represent $X/mo in traffic value. Your total keyword universe is much larger.'",
            "Prospect: 'When you put it that way, the investment makes a lot more sense.'",
        ],
        "common_mistakes": [
            "Using unrealistic targets (don't promise #1 for everything; #3-5 is more credible)",
            "Forgetting to mention this is paid equivalent value, not guaranteed revenue",
            "Not accounting for the time it takes to achieve these rankings",
            "Showing the math without connecting it to business outcomes (traffic value → leads → revenue)",
        ],
        "success_rate_notes": "Deals where value math is shown on screen close at 2.1x the rate of deals where ROI is just mentioned verbally. Average deal size is 35% higher when the math is visible.",
    },
    "compound-effect-close": {
        "name": "Compound Effect Close",
        "tagline": "'SEO + CRO + content compound on each other. Doing one without the others leaves money on the table.' Justifies the full package.",
        "description": (
            "When a prospect wants to cherry-pick individual services, show them how the services "
            "compound on each other. SEO drives traffic, CRO converts it, content fuels both. "
            "Doing SEO without CRO means you're driving traffic to a leaky funnel. Doing CRO "
            "without SEO means you're optimizing a trickle. The math only works when they compound."
        ),
        "when_to_use": [
            "When the prospect wants 'just SEO' or 'just paid' (they're leaving money on the table)",
            "When justifying a multi-service package over a single-service engagement",
            "When the prospect is comparing your multi-service price to a single-service competitor",
            "When you need to prevent scope reduction during negotiation",
        ],
        "example_dialogue": [
            "Prospect: 'Can we start with just the SEO piece? We'll add content and CRO later.'",
            "Rep: 'You can, and here's what that looks like. SEO alone will move your rankings, but without optimized content, the rankings plateau. And without CRO, you're driving more traffic to a funnel that converts at the same rate.'",
            "Rep: 'Here's the compound math: SEO alone might give you a 40% traffic increase. Add content, and it's 80% because you're feeding the SEO engine. Add CRO, and even though traffic is the same, leads might double because conversion rate improves. The total impact of all three is roughly 4x what SEO alone delivers. Not 3x, 4x, because they compound.'",
            "Prospect: 'I see your point. What does the combined package look like?'",
        ],
        "common_mistakes": [
            "Not having the math to back up the compounding claim (be specific, not hand-wavy)",
            "Refusing to do single services at all (some clients need to start small; offer a path to scale)",
            "Overselling the compound effect (4x is realistic; 10x is not credible)",
            "Not having case study data showing compound vs. single-service results",
        ],
        "success_rate_notes": "Multi-service proposals using the compound effect framing have a 28% higher close rate and 2.2x average deal value vs. single-service proposals.",
    },
    "reference-customer-drop": {
        "name": "Reference Customer Drop",
        "tagline": "'One of our clients ranks #1 for [hard keyword]. Happy to connect you.' Social proof at the right moment.",
        "description": (
            "The most powerful form of social proof in B2B sales isn't a logo wall or a case study "
            "PDF. It's a specific, verifiable result dropped at exactly the right moment in the "
            "conversation, followed by an offer to connect directly. It turns abstract credibility "
            "into concrete confidence."
        ),
        "when_to_use": [
            "When the prospect expresses skepticism ('can you really do that?')",
            "When discussing a specific outcome and you have a matching reference",
            "After showing the value math (proof that the math converts to reality)",
            "When competing against established agencies (proof beats reputation)",
        ],
        "example_dialogue": [
            "Prospect: 'Those numbers look great on paper, but can you actually get us to page 1 for these keywords?'",
            "Rep: 'Fair question. One of our clients, a mid-market SaaS company similar to yours, ranks #1 for \"enterprise workflow automation.\" That keyword alone drives over 3,000 visits per month for them. They started at #18.'",
            "Prospect: 'How long did that take?'",
            "Rep: 'About 7 months to break into the top 3, 11 months to hit #1. Happy to connect you with their marketing director if you'd like to hear it firsthand.'",
            "Prospect: 'That would be great, actually.'",
        ],
        "common_mistakes": [
            "Dropping references too early (before the prospect cares about the specific outcome)",
            "Being vague ('we have great clients') instead of specific ('ranks #1 for [keyword]')",
            "Not having the reference customer prepped and willing to take the call",
            "Using the same reference for every prospect (match the reference to the prospect's industry/size)",
        ],
        "success_rate_notes": "Deals where a reference call happens close at 3.4x the rate of deals without reference engagement. The key is timing: reference drops work best after value math, not before.",
    },
    "in-house-team-framing": {
        "name": "In-House Team Framing",
        "tagline": "'Think of us as your in-house team, not a vendor.' Reframes the relationship and justifies premium pricing.",
        "description": (
            "When a prospect compares your fee to another agency's fee, you're in a commodity "
            "conversation you can't win. Reframe: you're not a vendor, you're their in-house "
            "marketing team, without the overhead of recruiting, salaries, benefits, management, "
            "and ramp time. This changes the comparison from 'agency A vs. agency B' to 'build "
            "internally vs. deploy a ready-made team.'"
        ),
        "when_to_use": [
            "When the prospect compares your pricing to cheaper agencies",
            "When the prospect is considering building in-house as an alternative",
            "When you need to justify premium pricing vs. commodity competition",
            "When the prospect values integration and strategic alignment over task execution",
        ],
        "example_dialogue": [
            "Prospect: 'You're quite a bit more expensive than the other agencies we've talked to.'",
            "Rep: 'I appreciate the transparency. Let me reframe the comparison. The other agencies will execute tasks you assign. We integrate as your marketing team. Think about what it would cost to hire a senior SEO lead, a content strategist, a CRO specialist, and a paid media manager in-house. You're looking at $500-700K per year in fully loaded salary, plus 3-6 months to recruit and ramp each one.'",
            "Rep: 'For $80K per month, you get that entire team, already trained, already working together, with systems and processes built from working with dozens of companies like yours. No recruiting. No ramp time. No management overhead. And if it's not working, you can walk away. Try doing that with four full-time hires.'",
            "Prospect: 'When you put it against hiring costs, it's actually not that different.'",
            "Rep: 'It's usually less. And you get results faster because we're not starting from zero.'",
        ],
        "common_mistakes": [
            "Using this framing when you can't actually deliver at an in-house team level",
            "Not knowing the actual salary benchmarks for the roles you're replacing (do the math for their market)",
            "Comparing to junior hires (compare to the senior talent you're actually providing)",
            "Not backing it up with integration practices (slack channels, meeting cadences, shared dashboards)",
        ],
        "success_rate_notes": "The in-house team framing shifts the prospect's mental comparison from 'agency cost' to 'team cost,' typically increasing acceptable price range by 40-60%. Most effective with companies that have recently struggled to hire marketing talent.",
    },
}


# ---------------------------------------------------------------------------
# Quiz Mode
# ---------------------------------------------------------------------------

QUIZ_SCENARIOS = [
    {
        "scenario": "A prospect says: 'We like what you're proposing, but your price is about 30% higher than the other agency we're talking to. Can you match their price?'",
        "best_pattern": "in-house-team-framing",
        "also_applicable": ["tiered-packaging", "performance-skin-in-game"],
        "explanation": "Don't compete on price. Reframe the comparison from agency-vs-agency to agency-vs-hiring. If they're comparing you to a cheaper agency, they're thinking about vendors. Shift them to thinking about a team.",
    },
    {
        "scenario": "You're 10 minutes into a first call with the CEO of a mid-market SaaS company. She seems interested but hasn't expressed any specific pain. How do you create urgency?",
        "best_pattern": "anchor-with-data",
        "also_applicable": ["competitive-ego-trigger", "value-math-on-screen"],
        "explanation": "Lead with data. Show her competitive landscape before pitching. The data will surface pain she didn't know she had. Follow up with competitive triggers if she's the competitive type.",
    },
    {
        "scenario": "A prospect on a $15K/mo engagement asks: 'What would it look like to do more with you?' They're happy with results.",
        "best_pattern": "strategic-involvement-upsell",
        "also_applicable": ["compound-effect-close", "tiered-packaging"],
        "explanation": "Don't just offer more deliverables. Offer a different level of engagement: senior strategic involvement, executive alignment, integrated planning. Same team, higher value layer.",
    },
    {
        "scenario": "The VP of Marketing says: 'We've been burned by agencies before. Last one promised the world and delivered nothing. How are you different?'",
        "best_pattern": "performance-skin-in-game",
        "also_applicable": ["reference-customer-drop", "value-math-on-screen"],
        "explanation": "They're risk-averse for good reason. Performance pricing puts your money where your mouth is. Follow with a reference customer who can vouch for results.",
    },
    {
        "scenario": "A prospect wants to hire you for SEO only, even though you know their conversion rate is terrible. They'd get more traffic to a broken funnel.",
        "best_pattern": "compound-effect-close",
        "also_applicable": ["value-math-on-screen", "tiered-packaging"],
        "explanation": "Show the compound math. SEO alone = 40% lift. SEO + CRO = 4x the business impact. Make it clear that doing one without the other leaves money on the table.",
    },
    {
        "scenario": "The prospect says: 'We're planning to hire a Head of Content and a senior SEO manager. We think we can do this in-house for less.'",
        "best_pattern": "bridge-offer",
        "also_applicable": ["in-house-team-framing", "strategic-involvement-upsell"],
        "explanation": "Don't fight the in-house plan. Agree it's smart, then show the timeline reality. Hiring + ramp = 6-9 months. Bridge the gap now, build momentum, and hand off (or keep going because results are too good to stop).",
    },
    {
        "scenario": "You're presenting a $75K/mo proposal. The prospect says: 'We can see the value, but we only have $40K/mo approved for this quarter.'",
        "best_pattern": "tiered-packaging",
        "also_applicable": ["performance-skin-in-game", "bridge-offer"],
        "explanation": "This is exactly why you have tiers. Present the Baseline at ~$35K with a clear path to scale. Or offer Performance pricing with a lower base and bonus triggers. Never just discount.",
    },
    {
        "scenario": "The prospect is skeptical that you can rank for a highly competitive keyword in their industry. 'Everyone says they can do SEO. Nobody delivers.'",
        "best_pattern": "reference-customer-drop",
        "also_applicable": ["value-math-on-screen", "anchor-with-data"],
        "explanation": "Don't argue. Prove. Drop a specific, verifiable reference: 'One of our clients ranks #1 for [similar hard keyword]. Started at #22. Took 9 months. Happy to connect you with them.'",
    },
]


def list_patterns() -> str:
    """List all patterns with descriptions."""
    lines = ["# Value-Based Pricing Pattern Library", ""]
    lines.append(f"**{len(PATTERNS)} patterns available**")
    lines.append("")
    for i, (key, p) in enumerate(PATTERNS.items(), 1):
        lines.append(f"## {i}. {p['name']}")
        lines.append(f"*{p['tagline']}*")
        lines.append("")
        lines.append(f"**When to use:** {p['when_to_use'][0]}")
        lines.append(f"**Key insight:** {p['success_rate_notes'][:100]}...")
        lines.append(f"**Details:** `python3 pricing_pattern_library.py --pattern \"{key}\"`")
        lines.append("")
    return "\n".join(lines)


def get_pattern(pattern_key: str) -> str:
    """Get detailed breakdown of a specific pattern."""
    # Try exact match first, then fuzzy
    key = pattern_key.lower().replace(" ", "-").replace("_", "-")
    if key not in PATTERNS:
        # Try partial match
        matches = [k for k in PATTERNS if key in k or key in PATTERNS[k]["name"].lower()]
        if len(matches) == 1:
            key = matches[0]
        elif len(matches) > 1:
            return f"Multiple matches: {', '.join(matches)}. Be more specific."
        else:
            return f"Pattern not found: '{pattern_key}'. Use --list to see all patterns."

    p = PATTERNS[key]
    lines = [f"# {p['name']}", f"*{p['tagline']}*", ""]
    lines.append("## Description")
    lines.append(p["description"])
    lines.append("")

    lines.append("## When to Use")
    for w in p["when_to_use"]:
        lines.append(f"- {w}")
    lines.append("")

    lines.append("## Example Dialogue")
    for d in p["example_dialogue"]:
        lines.append(f"> {d}")
    lines.append("")

    lines.append("## Common Mistakes")
    for m in p["common_mistakes"]:
        lines.append(f"- ❌ {m}")
    lines.append("")

    lines.append("## Success Rate Notes")
    lines.append(p["success_rate_notes"])

    return "\n".join(lines)


def analyze_scenario(scenario: str) -> str:
    """Analyze a scenario and recommend patterns (uses LLM if available, else rule-based)."""
    # Try LLM first
    pattern_summaries = "\n".join(
        f"- {key}: {p['name']} - {p['tagline']}" for key, p in PATTERNS.items()
    )

    llm_prompt = f"""Given this sales scenario:

"{scenario}"

And these available value-based pricing patterns:
{pattern_summaries}

Recommend which 2-3 patterns to apply, in priority order. For each:
1. Which pattern and why it fits
2. Specific dialogue to use in this scenario
3. What to watch out for

Be specific and actionable. Use the pattern names exactly."""

    llm_result = _call_llm(llm_prompt, system_prompt="You are an expert B2B sales coach specializing in value-based pricing.")

    if llm_result:
        return f"# Scenario Analysis\n\n**Scenario:** {scenario}\n\n{llm_result}"

    # Fallback: keyword-based pattern matching
    scenario_lower = scenario.lower()
    scored_patterns = []

    keywords_map = {
        "anchor-with-data": ["data", "first call", "discovery", "don't know", "competitive", "landscape", "research"],
        "tiered-packaging": ["budget", "price", "options", "tiers", "proposal", "packages", "how much"],
        "competitive-ego-trigger": ["competitor", "behind", "losing", "rival", "beating", "ceo", "founder"],
        "strategic-involvement-upsell": ["expand", "more", "grow", "strategy", "strategic", "upsell", "upgrade"],
        "bridge-offer": ["in-house", "hire", "internal", "build", "recruit", "team"],
        "performance-skin-in-game": ["risk", "burned", "skeptic", "trust", "prove", "guarantee", "performance"],
        "value-math-on-screen": ["roi", "results", "expect", "numbers", "value", "worth", "justify"],
        "compound-effect-close": ["just seo", "just one", "single", "cherry pick", "only", "one service"],
        "reference-customer-drop": ["proof", "results", "show me", "example", "case study", "who else"],
        "in-house-team-framing": ["expensive", "cheaper", "agency", "compare", "cost", "other agencies"],
    }

    for key, keywords in keywords_map.items():
        score = sum(1 for kw in keywords if kw in scenario_lower)
        if score > 0:
            scored_patterns.append((key, score))

    scored_patterns.sort(key=lambda x: x[1], reverse=True)
    top_patterns = scored_patterns[:3] if scored_patterns else list(PATTERNS.keys())[:3]

    lines = [f"# Scenario Analysis", "", f"**Scenario:** {scenario}", ""]
    lines.append("*Analysis: rule-based (set ANTHROPIC_API_KEY or OPENAI_API_KEY for LLM-powered analysis)*")
    lines.append("")
    lines.append("## Recommended Patterns (in priority order)")
    lines.append("")
    for i, (key, score) in enumerate(top_patterns, 1):
        p = PATTERNS[key]
        lines.append(f"### {i}. {p['name']}")
        lines.append(f"*{p['tagline']}*")
        lines.append("")
        lines.append(f"**Why this fits:** {p['when_to_use'][0]}")
        lines.append("")
        lines.append("**Key dialogue:**")
        for d in p["example_dialogue"][:3]:
            lines.append(f"> {d}")
        lines.append("")
        lines.append(f"**Watch out for:** {p['common_mistakes'][0]}")
        lines.append("")

    return "\n".join(lines)


def run_quiz():
    """Interactive quiz mode."""
    print("# 🎯 Value-Based Pricing Pattern Quiz")
    print("I'll present scenarios. You identify the best pattern to apply.")
    print(f"({len(QUIZ_SCENARIOS)} scenarios available)")
    print()

    # Shuffle scenarios
    scenarios = list(QUIZ_SCENARIOS)
    random.shuffle(scenarios)

    correct = 0
    total = 0

    pattern_names = {k: PATTERNS[k]["name"] for k in PATTERNS}
    name_list = "\n".join(f"  {i+1}. {name} ({key})" for i, (key, name) in enumerate(pattern_names.items()))

    for i, quiz in enumerate(scenarios):
        print(f"---")
        print(f"## Scenario {i + 1}/{len(scenarios)}")
        print()
        print(f"  {quiz['scenario']}")
        print()
        print(f"Which pattern would you apply? (type the number or name)")
        print(name_list)
        print()

        try:
            answer = input("Your answer: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n\nQuiz ended early.")
            break

        # Match answer
        matched_key = None
        # Try number
        try:
            idx = int(answer) - 1
            keys = list(PATTERNS.keys())
            if 0 <= idx < len(keys):
                matched_key = keys[idx]
        except ValueError:
            pass

        # Try name/key match
        if not matched_key:
            for key in PATTERNS:
                if answer in key or answer in PATTERNS[key]["name"].lower():
                    matched_key = key
                    break

        total += 1
        if matched_key == quiz["best_pattern"]:
            correct += 1
            print(f"\n✅ Correct! {PATTERNS[quiz['best_pattern']]['name']}")
        elif matched_key in quiz["also_applicable"]:
            correct += 0.5
            print(f"\n🟡 Good choice! {PATTERNS[matched_key]['name']} works here.")
            print(f"   Best pattern: {PATTERNS[quiz['best_pattern']]['name']}")
        else:
            print(f"\n❌ Not the best fit.")
            print(f"   Best pattern: {PATTERNS[quiz['best_pattern']]['name']}")

        print(f"\n**Why:** {quiz['explanation']}")
        print()

        if i < len(scenarios) - 1:
            try:
                cont = input("Continue? (y/n): ").strip().lower()
                if cont == "n":
                    break
            except (EOFError, KeyboardInterrupt):
                break
            print()

    # Score
    print(f"\n---")
    print(f"## Final Score: {correct}/{total}")
    pct = (correct / total * 100) if total > 0 else 0
    if pct >= 80:
        print("🏆 Expert level. You know the playbook.")
    elif pct >= 60:
        print("👍 Solid. Review the patterns you missed.")
    elif pct >= 40:
        print("📚 Getting there. Run `--list` and study the patterns.")
    else:
        print("🔄 Time to study. Run `--pattern <name>` for deep dives on each pattern.")


def main():
    parser = argparse.ArgumentParser(
        description="Value-Based Pricing: Pattern Library & Training",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 pricing_pattern_library.py --list
  python3 pricing_pattern_library.py --pattern "anchor-with-data"
  python3 pricing_pattern_library.py --pattern "tiered-packaging"
  python3 pricing_pattern_library.py --scenario "prospect is a $50M SaaS company spending $15K/mo on marketing"
  python3 pricing_pattern_library.py --quiz
        """,
    )
    parser.add_argument("--list", action="store_true", help="List all patterns with descriptions")
    parser.add_argument("--pattern", help="Get detailed breakdown of a specific pattern")
    parser.add_argument("--scenario", help="Analyze a scenario and recommend patterns")
    parser.add_argument("--quiz", action="store_true", help="Interactive training mode")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format (default: markdown)")

    args = parser.parse_args()

    if not any([args.list, args.pattern, args.scenario, args.quiz]):
        parser.print_help()
        sys.exit(0)

    if args.quiz:
        run_quiz()
        return

    if args.list:
        if args.format == "json":
            output = {k: {"name": v["name"], "tagline": v["tagline"], "when_to_use": v["when_to_use"][0]} for k, v in PATTERNS.items()}
            print(json.dumps(output, indent=2))
        else:
            print(list_patterns())

    elif args.pattern:
        if args.format == "json":
            key = args.pattern.lower().replace(" ", "-").replace("_", "-")
            if key in PATTERNS:
                print(json.dumps(PATTERNS[key], indent=2))
            else:
                matches = [k for k in PATTERNS if key in k]
                if matches:
                    print(json.dumps(PATTERNS[matches[0]], indent=2))
                else:
                    print(json.dumps({"error": f"Pattern not found: {args.pattern}"}))
        else:
            print(get_pattern(args.pattern))

    elif args.scenario:
        if args.format == "json":
            # For JSON, just return the pattern recommendations
            scenario_lower = args.scenario.lower()
            keywords_map = {
                "anchor-with-data": ["data", "first call", "discovery", "competitive"],
                "tiered-packaging": ["budget", "price", "options", "tiers"],
                "competitive-ego-trigger": ["competitor", "behind", "losing", "ceo"],
                "strategic-involvement-upsell": ["expand", "more", "grow", "strategy"],
                "bridge-offer": ["in-house", "hire", "internal", "build"],
                "performance-skin-in-game": ["risk", "burned", "skeptic", "prove"],
                "value-math-on-screen": ["roi", "results", "numbers", "value"],
                "compound-effect-close": ["just seo", "single", "only", "one service"],
                "reference-customer-drop": ["proof", "show me", "example", "case study"],
                "in-house-team-framing": ["expensive", "cheaper", "agency", "compare"],
            }
            scored = []
            for key, keywords in keywords_map.items():
                score = sum(1 for kw in keywords if kw in scenario_lower)
                if score > 0:
                    scored.append({"pattern": key, "name": PATTERNS[key]["name"], "relevance_score": score})
            scored.sort(key=lambda x: x["relevance_score"], reverse=True)
            print(json.dumps({"scenario": args.scenario, "recommended_patterns": scored[:3]}, indent=2))
        else:
            print(analyze_scenario(args.scenario))


if __name__ == "__main__":
    main()
