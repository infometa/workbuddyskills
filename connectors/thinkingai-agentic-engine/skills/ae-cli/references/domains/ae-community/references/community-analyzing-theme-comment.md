# ae-community community-analyzing-theme-comment


In-depth analysis of topic comment areas: Conduct in-depth analysis of the comment areas of specified posts or videos, and generate an in-depth analysis report including comment trends, opinion distribution, and summary.

Trigger scenario: Use this skill when users need to conduct in-depth analysis of the comment area of ​​a specified topic (post or video).

## Analysis process

1. **Identify target post/video**: Get UUID, channelId and resourceType, or search via `+search_posts`
2. **Get comment area data**: Call `+get_post_detail` to obtain the target content details and comment area
3. **Get the complete comment area in paging**: loop through all comments and eliminate meaningless content such as irrigation and pure expressions.
4. **In-depth analysis**:
- Comment trend analysis (time trend, sentiment distribution trend)
- Opinion analysis (extracting positive/negative opinions and representative comments)
- Summary analysis (market data, opinion analysis, ecological analysis)

## Execution process

**Step 1: Identify Target Posts/Videos**
- Check if the user has explicitly specified the post or video to be analyzed (UUID, channelId, resourceType)
- If the user has provided the above information, jump directly to step 2
- If the user does not specify a target, the `+search_posts` tool needs to be used to search for suitable posts

**Step 2: Get comment area data**
- Use the `+get_post_detail` tool to get the details and comments section of the target content
- Get the complete comment area in pagination (pageSize recommended is 100)
- Check the number of comments and the hasMore field in the returned results
- If hasMore is true, continue calling to get the next page

**Comment filtering rules**:
When obtaining and storing comments, the following content that has no analytical significance needs to be eliminated:
- **Spoiled comments**: Repeated posting of the same or similar content, content that swipes the screen
- **Pure emoticons/symbols**: Contains only emoticons and symbol combinations (such as "???", "!!!")
- **No substance**: Comments with less than 3 characters
- **System Message**: Official automatically generated message

**Step 3: In-depth analysis**

**3.1 Comment Trend Analysis**
- Comment time trend: statistics on the time distribution of comments published, summarized by day
- Sentiment distribution trend: Statistics on changes in the proportion of positive, neutral, and negative comments by day

**3.2 Viewpoint analysis**
- Text clustering and topic extraction of all valid comments
- Identify recurring keywords and phrases
- Merge semantically similar views
- Differentiate between positive and negative viewpoints
- Each opinion includes: opinion title, opinion description, number of matching comments, representative comments (up to 10)
- **Handling Opposing Viewpoints**: Allow diametrically opposed positive and negative views on the same thing to exist, and do not merge opposing views.

**3.3 Summary analysis**
- Summary of market data: total number of comments, overall sentiment distribution, peak comment time
- Summary of opinion analysis: main positive opinions, main negative opinions, points of conflict of opinions, core needs of players
- Ecological analysis of the comment area: overall atmosphere, relevance of comments and content, core user group characteristics, potential risks and opportunities

## Output structure (must be complete)

### 1. Basic information
- **Post/Video Title**: Title content
- **Source Channel**: Channel name
- **Published**: Release date
- **Analysis Time Range**: The time period for analysis
- **Number of valid comments**: The number after excluding invalid comments

### 2. Comment trends

**Time Trend**

| Date | Number of comments | Percentage |
|------|--------|------|
| YYYY-MM-DD | Quantity | X% |

**Emotion Distribution**

| Date | Positive | Neutral | Negative |
|------|------|------|------|
| YYYY-MM-DD | X% | X% | X% |

### 3. Viewpoint analysis

**Positive View**

**Viewpoint 1: [Viewpoint Title]**
- **Viewpoint Description**: [Detailed Description]
- **Number of matching comments**: X
- **Representative comments**:
- "[Comment 1]"
- "[Comment 2]"

**Negative opinions (can be multiple)**

**Viewpoint 1: [Viewpoint Title]**
- **Viewpoint Description**: [Detailed Description]
- **Number of matching comments**: X
- **Representative comments**:
- "[Comment 1]"
- "[Comment 2]"

### 4. Summary

**Broad market data summary**:
- Total number of comments, overall sentiment distribution, peak comment time

**Summary of opinion analysis**:
- Mainly positive points
- Mainly negative points
- Points of conflict of opinions
- Players’ core needs

**Ecological Analysis and Suggestions**:
- Overall atmosphere
- Relevance of comments and content
- Characteristics of core user groups
-Potential risks and opportunities

## Example

```bash
# User input example
"Analyze the comment area of ​​this post"
"Help me deeply analyze the user feedback of this video"
```