# ae-community community-hottopic-insight


Topic analysis: Automatically collect corpus, intelligently identify industry attributes, and output a structured Topic Analysis that includes a core summary, an overview of sentiment and the context of events, core hot discussions, sentiment slices, social media channel insights, and operational recommendations.

Triggering scenario: Triggered when the user requests "Analyze topic", "Generate topic analysis report" or "Topic analysis".

# # Analysis process

1. * * `+get_hot_topics` * *: Get topic information (topicId, startTime, endTime)
2. * * `+search_posts` * *: Search related posts by topic ID, * * Focus on recording the time, total number and distribution of posts by channel * *
3. * * `+get_post_detail` * *: Grab high-profile content details (up to 10)

# # Entity and Time Rules

- [Topic name] must be extracted from user input
- If the user does not provide it, the user must ask the core analysis object
- If the user does not specify a specific time, * * the current system time is automatically pushed forward by 7-14 days as the query cycle * *

Core Requirements

- * * Dynamic traceability authenticity * *: must be strongly dependent on the post's real publishing time
- * * Evolutionary chains of "Time - Events - Topics - Emotions" must be clearly identified * *
- In chronological order, extract "what happened at what time, what was mainly discussed at that time, what was the emotion"
- If you can't catch the timestamp, please truthfully explain that "due to data limitations, it is impossible to generate an accurate timeline", and it is strictly forbidden to fabricate a false history of development

# # Output structure

* *⚠️ Mandatory: The report must be output in strict accordance with the structure of the following six parts, no parts may be omitted, and the order or format may not be changed. * *

# # # I. Summary of Core Content
- Event Overview: Summarize what everyone is talking about in one sentence
- The evolution of sentiment: such as "experienced a sharp reversal from the positive expectation of the previous period to the collapse of the reputation of the factor value problem after the launch"

# # # II. Overview of Public Opinion Data and Dynamic Evolution

* * Quantitative📊 sentiment statistics * *:
- Total number of current topics
- Overview of the number of content in each channel
- Overall Sentiment Ratio

* * Trends in🔥 popularity * *: Describe popularity trends

* * * Dynamic Public Opinion Evolution Vein (🔴Core must be itemized, not omitted) * *:
- * * `[MM-DD]` | Phase 1: [Phase naming, e.g. prospective warm-up period - expecting to be full] * *
- * * Trigger Node * *: [What happened at that time, ex: the official release of the live demo PV]
- * * Core Focus * *: [What players are talking about, e.g., motion fluency, fine art modeling]
- * * Emotional direction * *: [ex:🟢 extremely positive expectations, players are highly rated]
- * * `[MM-DD]` | Phase 2: [Phase name, e.g. live/new story launch] * *
- * * Trigger Node * *: [ex: Core mechanism was tampered with after update]
- * * Core Focus * *: [ex: Accusation of official misinformation, request for refund of deposit]
- * * Emotional direction * *🔴: [ex: Negative outburst]
- * * `[MM-DD]` | Phase 3: [Phase Naming, e.g. Current Status/Official Response] * *
- * * Trigger Node * *: [ex: official apology blue sticker description]
- * * Core Focus * *: [ex: Is the compensation plan justified in a tug-of-war?]
- * * Emotional direction * *: [ex:🟡 Negative emotions ease slightly, turn to wait and see for confirmation]

* Note: The number of stages increases or decreases according to the actual discussion escalation process *

# # # III. Summary of Core Hotspot Discussions
Objectively distill the 2-3 core specific issues that are currently the loudest and most controversial, regardless of emotions

# # # IV. Emotional Slicing and Opinion Analysis

* *🔴 Negative Emotional Slice * *
- * * Focus Issue * *: [Specific Issue]
- * * High frequency word cloud * *: [keyword list]
- * * Typical Player Soundtrack * *:
- "[True Comment 1]"
- "[True Comment 2]"

* *🟡 Neutral Emotion Slice * *
- * * Focus Issue * *: [Specific Issue]
- * * High frequency word cloud * *: [keyword list]
- * * Typical Player Soundtrack * *:
- "[True Comment 1]"
- "[True Comment 2]"

* *🟢 Positive Emotional Slice * *
- * * Focus Issue * *: [Specific Issue]
- * * High frequency word cloud * *: [keyword list]
- * * Typical Player Soundtrack * *:
- "[True Comment 1]"
- "[True Comment 2]"

* *⚠️ Note: The player's soundtrack must use "" to quote authentic reviews, and fabrication is strictly forbidden. * *

# # # V. Content insights across social media platforms
Compare of detailed data from different channels and characteristics of sentiment

# # # VI. Suggestions for Operation and Response from an Industry Perspective

* *⚡ Emergency Intervention (Firefighting Strategies for Crisis Response) * *
- Risk Assessment: [Specific Risks]
- Suggested action: [Specific action]

* 🚀 * Homeostasis (amplification strategy for operational activation) * *
- Opportunity Point Identification: [Specific Opportunity]
- Suggested Tactics: [Specific Tactics]

# # User input example

```bash
"Analyze the topic of # new UI redesign #"
"Generate the analysis report for the XX version of the comprehensive review topic"
"Analyze XX topics for me"
```

# # Execute Checklist

- Typical soundtracks must be traced back to real posts/comments.
- Channel insights must reflect platform differences, not just data.
- Suggestions are divided into “emergency intervention” and “homeopathic guidance”.