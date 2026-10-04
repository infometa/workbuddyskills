# Clarification Prompts

Use these prompts only when the target, time range, or symptom cannot be
discovered safely with public MCP tools. Ask one concise question at a time.

## Select the Analysis Mode

### Mode A: Single-Equipment RCA (Default)

Use for a fault or performance anomaly on one specific asset. Required
information is an `element_id` or an unambiguous name/path, an incident time or
range, and an observed symptom.

### Mode B: Equipment-Class Survey

Use for fleet statistics, common failure patterns, or comparison across a class
of equipment. Required information is an equipment class or template, an
analysis range, and a symptom, failure mode, or metric of interest.

## Prompt Templates

### The Mode Is Ambiguous

> Should I investigate one specific asset in depth, or compare a class of
> similar assets? For example: "Analyze the vibration anomaly on EM-001" or
> "Compare recent failure patterns across all centrifugal fans."

### Mode A Has No Identifiable Element

> Which asset should I investigate? Provide its element ID, name, path, or a
> location precise enough to find it, such as
> `Plant A/Workshop 1/Fan Group/FAN-001`.

If discovery returns multiple plausible matches, show the minimal distinguishing
details and ask the user to choose. Do not select one silently.

### Time Information Is Missing

> When did the issue occur? Provide an approximate timestamp, a range such as
> "last week," or a relative time such as "started three days ago." If the
> incident time is unknown, I can begin with the most recent seven days.

### The Symptom Is Missing

> What did you observe? Examples include a 50% power drop, excessive vibration,
> steadily rising temperature, a trip, reduced product quality, or repeated
> alarms. Include any operating condition that appears to trigger it.

### Confirm the Scope

> I will analyze **[asset or equipment class]** for **[symptom]** over
> **[time range]**, using **[baseline range or peers]** for comparison.

Do not narrate the whole internal workflow unless the user asks for it.

## Time-Window Rules

- For an exact incident timestamp, use an incident window appropriate to the
  process dynamics and a broader baseline window. The original workflow uses
  up to 10 days on either side when data volume permits.
- For a supplied time range, preserve the requested range and select a separate
  representative baseline when possible.
- With no time information, default to the latest seven days and disclose that
  assumption.
- Do not request a narrower timestamp when available event or attribute data can
  determine it safely.

## Multi-Turn Rules

- Reuse a target, symptom, or time range already verified in the conversation.
- If a supplied value was rejected by a tool, request a corrected value rather
  than silently reusing it.
- Never invent an element ID, timestamp, symptom, unit, or failure detail.
- If the user changes the target or range, restate the new scope before
  interpreting earlier evidence.
