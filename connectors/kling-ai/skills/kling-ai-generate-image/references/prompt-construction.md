# Image prompt construction

## Prompt order

Write prompts in this order:

1. Destination and medium: product photo, editorial portrait, poster, thumbnail, campaign still.
2. Subject and locked facts: identity, product geometry, exact colors, official logo or copy.
3. Action or visual idea.
4. Environment, time, weather, and atmosphere.
5. Composition: ratio, framing, camera height, lens feel, focal hierarchy, negative space.
6. Lighting and palette.
7. Materials, texture, surface detail, and realism/stylization level.
8. Constraints: subject count, forbidden changes, no extra text/watermark, safe-space requirements.

## Reference manifest

When multiple inputs are used, state their roles before the creative prompt:

```text
REFERENCE 1 = primary subject identity
REFERENCE 2 = product geometry and label
REFERENCE 3 = official logo; preserve exact shape and colors
```

Do not use a style reference as an identity reference. Describe the transferable characteristics instead.

## Exact text

- Preserve user copy character-for-character.
- Prefer generating a text-free base with deliberate copy-safe space when typography can be added by a deterministic design tool later.
- If the user explicitly wants baked text, state the exact text once, request no other readable text, and warn that generated typography may need review.

## Controlled variants

Generate separate prompts rather than requesting a batch of near-duplicates. Keep locked facts identical and vary one axis:

- concept: literal / human / metaphorical
- camera: macro / medium / environmental wide
- composition: centered / power-third / overhead
- mood: bright commercial / premium restrained / energetic saturated
- expression or action

## Avoid

- Empty praise such as “beautiful” without visual evidence.
- Contradictory directions such as minimal and densely layered, or macro and full environmental wide.
- Long negative lists that repeat the positive brief.
- Unverified product claims, medical outcomes, prices, awards, certifications, or statistics.
- Assuming a particular model or argument exists without checking the live schema.
