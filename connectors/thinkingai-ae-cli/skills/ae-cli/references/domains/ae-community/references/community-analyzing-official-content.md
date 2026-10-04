# ae-community community-analyzing-official-content


Official content analysis: Analyze recently published official content for a specified game in the community module, then classify and summarize it using the predefined categories.

Trigger scenario: Use this skill when the user wants to know the official release content of the specified game in the near future.

## Analysis process

1. **Confirm analysis time**: Get the start date and end date (recommended not to exceed 30 days)
2. **Query official content**: Call `+search_posts` and set the `official: true` parameter
3. **Content Classification Analysis**: Classified by four categories: game announcements, community activities, linkages, and promotional materials
4. **Formatted output**: Generate a structured official content analysis report

## Execution process

**Step 1: Confirm analysis time**
- **If the user has specified the analysis time**: Record the time range (start time, end time) and enter step 2
- **If the user does not specify the analysis time**: Inform the user to provide the following information before proceeding:
- Start date of analysis
- The end date of the analysis
- ⚠️ The time range is recommended to be no more than 30 days to ensure query efficiency and content readability

**Step 2: Check official content**
Use the `+search_posts` tool to query official published content within a specified time range.
- Calling parameters: `gameId`, `startTime`, `endTime`, `official: true`, `pagerHeader`
- Focus on recording the total number of topics, channel distribution and timestamp of each post

**Step 3: Content Classification and Analysis**
Classification analysis according to the following four categories

## Content classification criteria

| Category | Definition | Information to be extracted |
|------|------|----------------|
| **Game Announcement** | Announcement and introduction of new game content such as new versions and new activities | Activity/version/new card pool content, game elements, duration (resident activities return to "Resident") |
| **Community Activities** | Activities that promote players to post, reply, and create in the community, usually with physical rewards or community titles | Publishing platform, activity requirements, duration, and reward content |
| **Linkage** | Announcement of linkage activities outside the game | Linkage brand/IP, linkage time, linkage form (in-game linkage ownership game announcement) |
| **Promotional Materials** | General promotional materials (pictures, comics, character quotes, etc.) | Related characters/content, material form |

## Cross-platform merge rules

- **Game announcements, linkages, and promotional materials**: If the same content is released on multiple platforms and the content is consistent, merge it into one, and indicate "multi-platform release" in the summary
- **Community Activities**: Each platform is listed separately and is not merged (because the activity rules of different platforms may be different)

## Output structure

### 1. Analysis summary
- **Game**: Game name
- **Analysis time**: start date - end date
- **TOTAL OFFICIAL CONTENT**: Total quantity

### 2. Game Announcement
Contents list (sorted by time)

### 3. Community activities
Content list (sorted by platform and time)

### 4. Linkage
Contents list (sorted by time)

### 5. Promotional materials
Contents list (sorted by time)

## Example

```bash
# User input example
"Analyze the official releases of the past week"
"Help me sort out this month's official announcements"
```