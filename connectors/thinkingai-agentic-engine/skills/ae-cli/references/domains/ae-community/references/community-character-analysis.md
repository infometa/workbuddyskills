# ae-community community-character-analysis


Role-specific in-depth analysis: In-depth diagnosis for a single role, instead of regular daily/weekly reports, the "Role-specific in-depth analysis report" is output.

Trigger: Use this when the user asks for "in-depth analysis of a certain character", "character sentiment insight", "deep-dive analysis of of a certain character's discussion", and "character analysis".

## Analysis process

1. **`+get_sentiment_overview`**: Get the core word cloud of the character under positive and negative discussions to set the tone of the current overall reputation
2. **`+get_hot_topics`**: Confirm whether the character has formed a hot topic in the community
3. **`+search_posts`**: Search for recent hot posts using "character name + core controversial words"
4. **`+get_post_detail` & `+get_comments_summary`**: Extract the core views of the post and emotional feedback in the comment area

## Entity extraction and deduction rules

- [Core Analysis Role] must be extracted from user input (such as "Role", "Role A")
- If the user doesn't say anything, please clearly ask "Which character do you want to analyze in depth?"
- If the user does not specify a time, **automatically push forward 7-14 days from the current system time as the query period**

## Core Constraints

- **Reject fake claims**: Must explain "why" and give evidence of posts/comments.
- **Strictly distinguish between early warning and risk control**:
- Alerts: experience risks (mechanics, numerical values, plot, art, performance)
-Risk Control: risk of violation (causing war, illegal production, leakage, rumors)

## Output structure

### 1. Character’s current ecology and community impression
Use a very insightful paragraph to summarize the character’s current true position in the player’s mind.

### 2. Discussion popularity and emotional portrait matrix

| Dimensions | Data/Description |
|------|----------|
| Emotional fundamentals | Positive/neutral/negative ratio |
| Main forum for sentiment | Main discussion channel |
| High frequency word co-occurrence | Core keywords |

### 3. In-depth deep-dive analysis of of players’ core needs and focus

**✨ Core Values ​​and Highlight Experience**
- **Extraction of player voices**: [Summary]
- **Typical original voice/support case**: "[Real comments]"

**🧨 Analysis of core pain points**
- **Dismantling of deep demands**: [Analysis]
- **Typical original voice/support case**: "[Real comments]"

### 4. Operation strategy
- **Public Opinion Direction Guidance**: Specific Suggestions
- **Version/Optimization Forward Planning**: Direction for improvement

### 5. Warning content

**⚠️ Warning content**

| Danger level | Warning triggers | Community spread | Core performance | Suggested follow-up actions |
|---------|-----------|-----------|---------|-------------|
| High/medium/low | Specific problems | Scope of impact | Specific performance | Handling suggestions |

## Example

```bash
# User input example
"A deep analysis of the role"
"Help me break down the discussion of character A"
"Analyze the sentiment of XX character"
```