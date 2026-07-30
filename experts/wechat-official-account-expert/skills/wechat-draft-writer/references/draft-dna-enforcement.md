# Draft DNA Enforcement

Use this file as hard constraints during draft generation.

## Required Inputs
- Confirmed outline and article objective.
- Reference materials (links, notes, reports, docs).
- Voice transcript draft (user spoken raw material).
- Style DNA card from `wechat-style-profiler`.
- Target reader action.

## Default Style DNA File
- Preferred path:
  Generate a personal Style DNA via `wechat-style-profiler` before drafting.
- Recommended handoff:
  Copy your generated DNA file into `wechat-draft-writer/references/author-style-dna.md`.
- If user does not provide a Style DNA file explicitly, load this default:
  `references/author-style-dna.md`
- If user provides a personal DNA file, user file overrides default.
- If `references/author-style-dna.md` does not exist, fallback to:
  `references/style-dna-default-template.md`
- The fallback template is for temporary demo/testing only, and should not be used as final publishing baseline.

## Hard Rules
- Keep paragraphs short, default 1-3 sentences.
- Keep exactly one blank line between paragraphs.
- Use specific claims with concrete details when possible.
- Use natural transitions, avoid mechanical connectors.
- Avoid padding and generic preamble.
- Use digits for numbers.
- Add spaces around standalone English words and numbers when it improves readability.
- Do not use em dashes.
- Keep factual claims anchored to provided references where possible.
- Preserve spoken-language signatures from voice transcript without copying filler words.

## Banned Phrases (case-insensitive)
- in today's
- it's important to note that
- it's worth noting
- delve
- dive into
- unpack
- harness
- leverage
- utilize
- landscape
- realm
- robust
- game-changer
- cutting-edge
- straightforward
- i'd be happy to help
- in order to
- furthermore
- additionally
- moreover
- moving forward
- at the end of the day
- to put this in perspective
- what makes this particularly interesting is
- the implications here are
- in other words
- it goes without saying
- let that sink in
- read that again
- full stop
- this changes everything
- are you paying attention
- you're not ready for this
- supercharge
- unlock
- future-proof
- 10x your productivity
- the ai revolution
- in the age of ai
- here's the part nobody's talking about
- what nobody tells you

## Fatal Pattern
Fail output if any sentence follows negation-frame template:
- this isn't X, this is Y
- not X, Y
- forget X, this is Y
- less X, more Y

Rewrite as direct positive claim.

## Required Compliance Report
Include a compact report at the end:
- banned phrase hits: `0` required
- fatal pattern hits: `0` required
- em dash count: `0` required
- paragraphs over 3 sentences: should be `0` unless requested
