# ae-community community-activity-analysis


Event-specific operation insight analysis: In-depth evaluation of the exposure effect, community reputation, second-generation ecology and long-tail impact of in-game activities or marketing events, and output a standard "Event-Specific Operation Insight Report".

Trigger scenario: When the user asks to "analyze a certain activity", "generate activity review", "see feedback from XX activity" or "evaluate marketing effectiveness".

## Analysis process

1. **Basic market and trend analysis**: Call `+get_overview_metrics` and `+get_daily_summary` to obtain the overall volume and sentiment before and after the event
2. **Drill down on topics and hot searches**: Call `+get_hot_topics` and `+get_topic_detail` to deeply analyze the sentiment distribution of a specific topic
3. **Word-of-mouth and pain points deep-dive analysis of**: Call `+get_sentiment_overview` to analyze positive and negative high-frequency keywords
4. **Fixed-point blasting evidence collection**: Call `+search_posts` -> `+get_post_detail` -> `+get_comments_summary` to obtain real player cases
5. **Risk Control and Red Line Checking**: Call `+get_risk_content` to check compliance risk content

## Core Constraints

- **Reject false claims**: You must write down the specific reasons and attach supporting posts or comments.
- **Strictly distinguish between early warning and risk control**:
- Early Warning: Event experience issues (mechanism, bugs, rewards, liveliness)
- Risk control: Risks of violations (black/gray-market activity, leaks, wars, advertising, etc.)

## Output structure

### 1. Activity overview and core data
- Set the tone for the event
- Core sound volume and exposure indicators (including tables)

### 2. Insights into community feedback and sentiment highlights
- **Activity Highlights and Highlights** (with typical acoustic support)
- **Core slots and experience pain points** (including typical original sound support)

### 3. Content dissemination and secondary innovation ecological mining
- Core out-of-circle topics/meme culture
- Inventory of secondary innovation output potential

### 4. Impact on community ecology
-Activity pulling effect
- Player structure/genre evolution

### 5. Inspiration and optimization suggestions for operational strategies
- Design pitfalls in follow-up activities
- Long-tail marketing strategies
- Livestream/publicity side review

### 6. Activity warning and compliance risk control

**⚠️ Event sentiment and experience warning**

| Warning level | Warning trigger items | Community spread | Core performance | Suggested follow-up actions |
|---------|-----------|-----------|---------|-------------|
| High/medium/low | Specific problems | Scope of impact | Specific performance | Handling suggestions |

**⛔ Community compliance and risk control interception**

| Risk control level | Violation type | Discovery channels | Violation facts | Disposal suggestions |
|---------|---------|---------|-------------|---------|
| Serious/General | Violation type | Channel name | Specific facts | Handling suggestions |

## Example

```bash
# User input example
"Help me analyze the feedback on such and such activities"
"Generate an activity review report for the half-anniversary celebration"
"Evaluate the effectiveness of this marketing campaign"
```