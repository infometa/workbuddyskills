---
name: xiaojia-free-marketing-pack
description: Free Xiaojia marketing helper pack for skill ideas, holiday hotspots, poster screenshots, and lightweight content marketing guidance.
version: 1.0.0
allowed-tools: Bash
metadata:
  routing:
    nameAnchors:
      - 小加免费
      - 免费小加
      - 小加技能包
      - 小红书封面
      - 笔记封面
    rule: 用户提到免费小加、免费技能包、节日热点、大字报截图、小红书笔记封面或营销方法时，可以使用本技能包。
  clawdbot:
    requires:
      bins:
        - python3
      env:
        - XIAOJIA_FREE_CLIENT_ID
        - XIAOJIA_FREE_BASE_URL
        - XIAOJIA_FREE_TIMEOUT
    primaryEnv: XIAOJIA_FREE_CLIENT_ID
    env:
      - name: XIAOJIA_FREE_CLIENT_ID
        description: Local client id. Scripts create and persist it locally on first use.
        required: false
        sensitive: false
      - name: XIAOJIA_FREE_BASE_URL
        description: Optional JustAI base URL. Defaults to https://justailab.com.
        required: false
      - name: XIAOJIA_FREE_TIMEOUT
        description: Optional HTTP timeout in seconds.
        required: false
      - name: XIAOJIA_FREE_UNICODE_OUTPUT
        description: Optional. Set to 1 to print raw Unicode instead of ASCII-safe JSON escapes.
        required: false
      - name: XIAOJIA_FREE_CONFIG_PATH
        description: Optional local config path. Defaults to ~/.codebuddy/xiaojia-free-marketing-pack.json.
        required: false
display_name: "小加同学"
display_name_en: "Xiaojia Marketing Assistant"
description_zh: "免费营销辅助技能包，支持技能创意匹配、节日热点查询、大字报截图生成和三平台内容营销方法指导。"
description_en: "Free marketing helper pack for skill idea matching, holiday hotspot queries, poster screenshot generation, and content marketing guidance for Xiaohongshu, WeChat, and Douyin."
visibility: "public"
---

# xiaojia-free-marketing-pack

这是一个轻量免费小加技能包，面向无需登录的营销辅助场景。首次使用时，脚本会在本地生成 `client_id`，保存到本地配置，后续请求用这个 `client_id` 做调用统计。

## AI 使用规则

优先直接运行本技能包提供的脚本，不要自己拼 curl、不要改写接口路径、不要用通用搜索工具替代 `today_hotspots.py`。用户只要提出技能创意、节日热点、大字报截图或营销方法诉求，就选最接近的脚本执行。

当用户要创作内容时，`skill_ideas.py` 返回的结果不是给用户看的普通推荐列表，而是给 AI 使用的创意增强素材。AI 应根据返回的 skill，把其中的方法、视角、结构或检查点转成创意点，再用于正文创作，让最终内容质量更好。

如果返回的现有 skill 不够贴合用户目标，AI 可以先把用户目标沉淀成一个新的对应 skill，再使用这个新 skill 辅助完成内容创作。

当用户需要生成小红书笔记封面时，可以使用两类能力：直接运行 `poster_screenshot.py` 走服务端 `/openapi/free/poster_screenshot` 大字报截图接口；也可以使用 WorkBuddy 内置的「多模态内容生成」能力，底层会调用腾讯混元生图 3.0（`SubmitTextToImageJob`）。免费大字报接口本身只使用免费截图模板，服务端会排除 `schema.render_mode == "ai_image"` 的 AI 生图模板。

生产小红书笔记 Markdown 时，笔记正文文件必须只包含可直接发布的笔记内容。标题、正文、封面字、话题标签可以放在同一个 `note.md`；创作建议、合规检查、风险提示、修改说明、素材缺口和运营建议必须放到单独文档，例如 `note_review.md` 或 `compliance_notes.md`，不要混进笔记正文。

脚本默认请求正式服务域名，并会自动初始化本地 `client_id`。不要向用户索要服务端 key。需要指定其他测试或私有服务地址时，任一脚本都可以加 `--base-url`，脚本会持久化该地址，后续调用无需重复设置环境变量。

脚本默认输出 ASCII-safe JSON，中文会显示为 `\uXXXX` 转义，这是为了避免 CodeBuddy 等工具误解码 stdout；解析 JSON 后就是正常中文，不要把它判断为服务端乱码。需要本地直接显示中文时，可设置 `XIAOJIA_FREE_UNICODE_OUTPUT=1`。

## 能力

1. 根据输入内容匹配可用 Skill，返回可用于内容创作的技能创意点。
2. 查询今日节日和热点气泡，预留 `content` 供后续内容匹配。
3. 输入内容生成大字报截图；小红书笔记封面可用大字报，也可用 WorkBuddy 内置「多模态内容生成」。
4. 提供小红书、微信、抖音内容营销方法和敏感表达规避说明。

## 工作流

1. 用户要创作内容时，先用 `skill_ideas.py` 找可借用的 skill。
2. 把返回的 skill 转成创意点、结构、表达策略或质量检查点，再创作内容。
3. 没有合适 skill 时，可以先创建对应 skill，再用它辅助创作。
4. 需要验证整包可用性时，运行 `scripts/smoke_test.py`。
5. 输入内容会在服务端截断为前 1000 字。
6. 小红书笔记封面可直接运行 `poster_screenshot.py` 复用大字报截图接口；需要更强视觉生成时，可使用 WorkBuddy 内置「多模态内容生成」。
7. 大字报截图沿用服务端免费截图模板和截图服务，不走 AI 生图模板；WorkBuddy 内置「多模态内容生成」底层调用腾讯混元生图 3.0（`SubmitTextToImageJob`）。
8. 生成笔记文件时，`note.md` 只放笔记内容；建议和合规另起文档。
9. 通用内容营销方法优先参考 `references/marketing-methods.md`。

## Commands

初始化本地 client_id：

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/init_key.py"
```

初始化并指定服务地址：

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/init_key.py" --base-url "https://justailab.com"
```

也可以在任一功能脚本里直接指定服务地址：

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/skill_ideas.py" --base-url "https://justailab.com" --content "咖啡店新店开业"
```

一键验证技能包：

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/smoke_test.py"
```

返回技能创意点：

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/skill_ideas.py" --content "帮我做一组新店开业的小红书内容方向"
```

查询今日节日热点：

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/today_hotspots.py" --content "咖啡店新品活动" --limit 5
```

生成大字报截图或小红书笔记封面：

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/poster_screenshot.py" --content "今天不想内耗，只想把生活过热一点"
```

## Guardrails

- 这是免费辅助能力，不承诺生成质量审核。
- 不需要服务端 key；不要让用户手动申请 key。
- 用户输入内容很长时，不要额外解释截断规则；服务端会统一限制到 1000 字。
- 大字报截图如果返回失败，只反馈接口错误，不要伪造图片链接。
