---
name: find-skills
description: Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill.
description_zh: "发现和安装新技能，扩展智能体能力"
description_en: "Discover and install new skills"
---

# Find Skills

This skill helps you discover and install skills from the open agent skills ecosystem.

## When to Use This Skill

Use this skill when the user:

- Asks "how do I do X" where X might be a common task with an existing skill
- Says "find a skill for X" or "is there a skill for X"
- Asks "can you do X" where X is a specialized capability
- Expresses interest in extending agent capabilities
- Wants to search for tools, templates, or workflows
- Mentions they wish they had help with a specific domain (design, testing, deployment, etc.)

## How to Help Users Find Skills

### Step 1: Understand What They Need

When a user asks for help with something, identify:

1. The domain (e.g., React, testing, design, deployment)
2. The specific task (e.g., writing tests, creating animations, reviewing PRs)
3. Whether this is a common enough task that a skill likely exists

### Step 2: Search SkillHub (Primary Source)

SkillHub (`https://lightmake.site`) is the primary skill registry. Use its **semantic search API** to find relevant skills:

```bash
curl -s "https://lightmake.site/api/v1/search?q=<URL-encoded query>&limit=10"
```

For example:

- User asks "how do I make my React app faster?" -> `curl -s "https://lightmake.site/api/v1/search?q=react+performance&limit=10"`
- User asks "can you help me with PR reviews?" -> `curl -s "https://lightmake.site/api/v1/search?q=pr+review&limit=10"`
- User asks "I need to create a changelog" -> `curl -s "https://lightmake.site/api/v1/search?q=changelog&limit=10"`

The response is JSON with a `results` array. Each result includes:

- `slug` — unique identifier for the skill
- `name` / `displayName` — display name
- `description` / `description_zh` — English/Chinese description
- `score` — relevance score (0~1, higher is better)
- `homepage` — link to the skill's page
- `downloads`, `installs`, `stars` — popularity metrics

Filter results by `score` (ignore results with very low relevance, e.g. < 0.05). Present the top matches to the user.

If SkillHub returns no relevant results, proceed to Step 2b (Fallback).

### Step 2b: Fallback Search Sources

If SkillHub has no relevant results, try these in order:

**Vercel Skills CLI:**

```bash
npx skills find [query]
```

Returns results like `vercel-labs/agent-skills@vercel-react-best-practices`. Browse at https://skills.sh/

**ClawHub (OpenClaw registry):**

```bash
npx clawhub search [query]
```

Browse at https://clawhub.com/

### Step 3: Present Options to the User

When you find relevant skills, present them with:

1. The skill name and what it does (use `description_zh` for Chinese-speaking users, `description` otherwise)
2. Popularity info (downloads / installs / stars) to help them choose
3. The install command (see Step 5)
4. A link to learn more (the `homepage` field)

Example response:

```
I found a skill that might help!

**Weather** by steipete — Get current weather and forecasts (no API key required).
  Downloads: 161K | Installs: 17K | Stars: 295
  Homepage: https://clawhub.ai/steipete/weather

Would you like me to install it?
```

If multiple results are relevant, list the top 3-5 and let the user choose.

### Step 4: Detect Current Client

Before installing, detect which client is running by checking the `__CFBundleIdentifier` environment variable:

```bash
echo $__CFBundleIdentifier
```

Determine the target skills directory based on the result:

| `__CFBundleIdentifier` contains | Client    | Target skills dir        |
| ------------------------------- | --------- | ------------------------ |
| `codebuddy`                     | CodeBuddy | `~/.codebuddy/skills/`   |
| anything else / empty / unset   | WorkBuddy | `~/.workbuddy/skills/`   |

**Default to WorkBuddy**: If the variable is empty, unset, or contains any value other than `codebuddy`, treat the current client as WorkBuddy.

### Step 5: Check the Local Skills Marketplace First (Required)

Before downloading from the network, you **must** check if the skill already exists locally:

**Local marketplace folder:** `~/.workbuddy/skills-marketplace/skills`

1. List or inspect that directory and identify a skill subfolder that matches the user's need (by folder name, `SKILL.md`, or metadata).
2. If a match exists, **copy** the entire skill folder into the **target skills directory** from Step 4 (do not remove the original marketplace copy).

```bash
ls ~/.workbuddy/skills-marketplace/skills
# WorkBuddy target:
cp -r ~/.workbuddy/skills-marketplace/skills/<skill-folder-name> ~/.workbuddy/skills/<skill-folder-name>
# CodeBuddy target:
cp -r ~/.workbuddy/skills-marketplace/skills/<skill-folder-name> ~/.codebuddy/skills/<skill-folder-name>
```

3. If no suitable skill exists locally, continue with Step 6 (remote install).

Always confirm the copied skill is present under the target directory before reporting success. If the user already has that skill name in the target dir, resolve the conflict (skip, replace, or rename) explicitly.

### Step 6: Install from SkillHub (Remote)

If the skill was found on SkillHub (Step 2), download and install it:

```bash
# 1. Create a temp directory
TMPDIR=$(mktemp -d)

# 2. Download the skill zip from SkillHub
curl -L -o "$TMPDIR/skill.zip" "https://lightmake.site/api/v1/download?slug=<slug>"

# 3. Ensure the target skill folder exists, then unzip into it
#    The zip contains files directly (SKILL.md, _meta.json, etc.) without a wrapper folder,
#    so we must unzip into a named subdirectory.
mkdir -p <target-skills-dir>/<slug>
unzip -o "$TMPDIR/skill.zip" -d <target-skills-dir>/<slug>

# 4. Clean up
rm -rf "$TMPDIR"
```

Where:
- `<target-skills-dir>` is `~/.workbuddy/skills` (default) or `~/.codebuddy/skills` (from Step 4)
- `<slug>` is the skill's slug from the search results

The installed skill will end up at `~/.workbuddy/skills/<slug>/SKILL.md` (or `~/.codebuddy/skills/<slug>/SKILL.md`), matching the standard skill directory layout.

To install a specific version:

```bash
curl -L -o "$TMPDIR/skill.zip" "https://lightmake.site/api/v1/download?slug=<slug>&version=<version>"
```

**For skills found via Vercel Skills CLI (fallback):**

```bash
npx skills add <owner/repo@skill> -g -y
```

**For skills found via ClawHub (fallback):**

```bash
# For WorkBuddy:
npx clawhub install <slug> --workdir ~ --dir .workbuddy/skills
# For CodeBuddy:
npx clawhub install <slug> --workdir ~ --dir .codebuddy/skills
```

### Step 7: Verify Installation

After installing, verify the skill exists in the target directory:

```bash
ls -la <target-skills-dir>/<skill-name>
```

For Vercel Skills CLI installs (which install to `~/.agents/skills/`), if the skill is missing from the target dir, create a symlink or copy:

```bash
# If installed at ~/.agents/skills/<skill-name>
ln -s ../../.agents/skills/<skill-name> ~/.workbuddy/skills/<skill-name>
```

Always confirm the skill is accessible at the target directory before reporting success to the user.

## SkillHub Additional Features

### Browse by Category

You can help users explore skills by category:

```bash
# Get all categories
curl -s "https://lightmake.site/api/v1/categories"
```

Available categories: AI Intelligence, Developer Tools, Productivity, Data Analysis, Content Creation, Security & Compliance, Communication & Collaboration.

```bash
# Browse skills in a category, sorted by popularity
curl -s "https://lightmake.site/api/skills?category=developer-tools&sortBy=score&order=desc&page=1&pageSize=10"
```

### Top Skills

Show the most popular skills:

```bash
curl -s "https://lightmake.site/api/skills/top"
```

### Skill Details

Get full details about a specific skill:

```bash
curl -s "https://lightmake.site/api/v1/skills/<slug>"
```

## Tips for Effective Searches

1. **Use specific keywords**: "react testing" is better than just "testing"
2. **Try both Chinese and English**: SkillHub supports semantic search in both languages
3. **Try alternative terms**: If "deploy" doesn't work, try "deployment" or "ci-cd"
4. **Browse by category** if keyword search doesn't yield good results

## When No Skills Are Found

If none of the registries (SkillHub, Vercel Skills, ClawHub) have relevant results:

1. Acknowledge that no existing skill was found
2. Offer to help with the task directly using your general capabilities
3. Suggest the user could create their own skill with `npx skills init`

Example:

```
I searched for skills related to "xyz" in SkillHub, Vercel Skills, and ClawHub
but didn't find any good matches.
I can still help you with this task directly! Would you like me to proceed?

If this is something you do often, you could create your own skill:
npx skills init my-xyz-skill
```
