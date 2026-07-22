# digest_spec schema（agent 产出契约）

agent 做完「去重 / AI 摘要 / 热议话题」后，**只产出一份符合本 schema 的 JSON**（称为 `digest_spec`），写入文件后交给 `scripts/render_digest.py` 渲染成最终推送，再交给 `scripts/validate_digest.py` 校验。

> 核心原则：**agent 不手写最终推送正文**。版式（分隔线 / emoji / 万粉换算 / 时间 / 千分位 / 标题截断 / 空平台隐藏）全部由渲染器代码保证，agent 只负责填本 schema 里「算不出的」字段。

## 顶层结构

```json
{
  "game_name": "NIKKE",
  "digest_time": "2026-04-22 09:00",
  "summary": {
    "sentiment": {"pos": 0.33, "neu": 0.42, "neg": 0.25},
    "topics": [["新卡池", 7], ["剧情更新", 4], ["外观皮肤", 3]]
  },
  "platforms": [
    {
      "display": "🔥 Reddit · r/NIKKE",
      "merged_note": "同一话题 4 条相关讨论已合并展示 2 条",
      "posts": [
        {
          "rank": 1,
          "title": "The new banner is actual P2W scam",
          "author": "u/player123",
          "followers": 28000,
          "time": "2026-04-22T21:00:00Z",
          "engagement": 1240,
          "sentiment": "负面",
          "summary": "吐槽新卡池出货率过低，认为是付费陷阱",
          "url": "https://reddit.com/r/NIKKE/..."
        }
      ]
    }
  ]
}
```

## 字段说明

### 顶层

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `game_name` | ✅ | string | 游戏名，用于标题 `📰 {game_name} 每日热帖` |
| `digest_time` | ✅ | string | 推送时刻 `YYYY-MM-DD HH:MM`（取数锚点）。与 `time` 同时区（默认 **UTC+8**，与 feeds 数据一致），可用 env `DIGEST_TZ_OFFSET_HOURS` 调整 |
| `summary` | ✅ | object | 顶部概况，见下 |
| `platforms` | ✅ | array | 分平台榜，见下。**0 帖平台可不放进来或放空 posts**，渲染器自动隐藏 |
| `detail_url` | | string | 可选；底部「在 DataBrain 查看完整列表」链接 |
| `subscribe_url` | | string | 可选；底部「调整订阅 / 取消订阅」链接 |

> 注意：**热帖总数与各平台计数不需要 agent 填**，渲染器从 `platforms[].posts` 自动统计，避免口径不一致。

### summary

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `sentiment` | | object | `{pos, neu, neg}` 三个 0~1 的占比（由取数脚本的整体情感分布得来）。缺失则不渲染该行 |
| `topics` | | array | 热议话题 `[[标签, 帖数], ...]` 最多 3 个，agent 通读全部入选帖归纳。缺失/空则不渲染该行 |

### platforms[]

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `display` | ✅ | string | 平台展示名，如 `🔥 Reddit · r/NIKKE`（emoji 前缀建议保留，与模板一致） |
| `posts` | ✅ | array | 该平台 Top N 帖子（去重后，已按互动降序），见下 |
| `merged_note` | | string | 去重合并提示，如 `同一话题 4 条相关讨论已合并展示 2 条`。无合并则省略 |

### platforms[].posts[]（每帖 8 必选字段，对应需求 §4.4.1）

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `rank` | ✅ | int | 排名 1/2/3... |
| `title` | ✅ | string | **原文标题全文，不翻译、不截断**（截断由渲染器按显示宽度做） |
| `author` | ✅ | string | 用户名（如 `u/player123` / `@jp_nikke_player`） |
| `followers` | ✅ | int | 粉丝/订阅数（渲染器换算 `万/亿`）；无则填 0 |
| `time` | ✅ | string | 发布时间（即 feeds 的 `comment_time`，原样回填）。**实为 UTC+8 墙钟**（入库被误标 `+00`，勿做时区换算）；与 `digest_time` 同时区，渲染器 naive 比对算 `Xh 前` |
| `engagement` | ✅ | int | 互动总量（渲染器加千分位） |
| `sentiment` | ✅ | string | 只能是 `正面` / `中性` / `负面`（单词级，不给分数） |
| `summary` | ✅ | string \| null | AI 一句话摘要，≤30 字中文；**失败/无法生成时填 `null`**，渲染器不显示摘要行 |
| `url` | ✅ | string | 原帖永久链接（http/https）；渲染器过滤非法 url |

## agent 填字段时的规则（对应需求）

- **title**：传原文全文。截断（超 20 中文字等效宽度显示 `...`）交渲染器，agent 不要自己截。
- **summary**（§4.4.2）：基于标题 + 正文 snippet（已按信息量归一：中文≈200字 / 拉丁≈400字符）生成，≤30 字中文，只描述不评价，原文非中文也输出中文；生成不了就填 `null`。
- **sentiment**：从候选数据的 `sentiment_rating` 映射（4-5→正面 / 3→中性 / 1-2→负面）。
- **posts 去重**（§4.3.3）：同平台同事件最多 2 条，挤出位由下一候选补齐到 Top N，并在 `merged_note` 标注合并条数。
- **topics**（§4.5）：通读所有平台入选帖，归纳 Top 3 话题标签 + 命中帖数。

## 校验

填好后务必跑：

```bash
python scripts/validate_digest.py --input spec.json --top_n 5
```

不通过会列出错误，按提示修正后再渲染。校验项见 `validate_digest.py`。
