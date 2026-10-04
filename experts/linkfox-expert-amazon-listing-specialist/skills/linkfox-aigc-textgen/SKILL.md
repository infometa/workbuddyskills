---
name: linkfox-aigc-textgen
description: AI生文工具，根据提示词生成文本内容，支持图、视频和文本结合理解。提供快速与高质量两种服务档位。用户说"AI生文"、"AI写作"、"文本生成"、"帮我写一段"、"text generation"、"generate text"、"用AI写"、"AI分析图片内容"、"图片识别"、"视频分析"时触发。
---

# AI 生文

使用大语言模型根据提示词生成文本内容，支持传入图片, 视频等进行图文结合，视频文本理解和分析。

## 核心特点

- **双档位选择**：快速响应和高质量复杂分析。
- **图文/视频内容结合**：`imageUrls` 同时支持图片与视频 URL；图片最多 10 张，视频通常传 1 个。
- **思考深度可控**：4 级 thinkingLevel 控制推理深度。
- **异步两步调用**：创建任务后立即返回 taskId，客户端轮询查询结果，避免长耗时同步超时。

## 服务档位

| 服务别名（model） | 说明 | 适用场景 |
|------|------|----------|
| LF_GEM_1 | 快速响应 | 常规文案、简单分析、翻译 |
| LF_GEM_2 | 高质量复杂分析（默认） | 深度分析、长文写作、复杂推理 |

## 思考等级

| thinkingLevel | 说明 |
|------|------|
| minimal | 接近无思考（仅 `LF_GEM_1` 支持） |
| low | 低思考 |
| medium | 平衡 |
| high | 最大推理深度 |

## 参数概览

- **必填字段**：`prompt`、`imageUrls`（无图片且无视频时传空数组 `[]`）
- **兼容规则**：`model` 空值或无法匹配时服务端使用 `LF_GEM_2`；`LF_GEM_2` 收到 `minimal` 或未传 `thinkingLevel` 时自动使用 `low`
- **媒体 URL 约定**：图片与视频 URL **均通过 `imageUrls` 传递**（如视频分析传 `["https://example.com/ref.mp4"]`）；勿使用未文档化字段（如 `videoUrl`、`videoUrls`）

完整参数表、响应字段结构与错误码，见 [`references/api.md`](references/api.md)。

## 调用方式

采用异步两步模式（与 imagegen 一致）：

1. **创建任务**：`POST /aigc/textGenAsync` → 返回 `taskId`
2. **轮询查询**：`POST /aigc/textTaskQuery` → 返回 `PROCESSING` / `SUCCESS` / `FAILED`

- **Python 脚本**（内部已封装创建+轮询，传参方式不变）：
  - `python scripts/aigc_textgen.py --stdin` — **推荐**，从 stdin 读取 JSON 参数，避免 shell 转义问题（如 `python scripts/aigc_textgen.py --stdin < params.json`）
  - `python scripts/aigc_textgen.py --stdin --content-only` — 只输出 content 文本（同样已是单行）
  - `python scripts/aigc_textgen.py '<JSON 参数>' [--inline]` — 简单场景直传（**prompt 含换行符时禁用**）

> **轮询策略**：单次 HTTP 超时 150 秒；轮询间隔从 10 秒起递减至 5 秒；总轮询时长最长 600 秒。完整参数/响应/错误码见 `references/api.md`。

> **换行符压平默认开启（无需任何 flag）**：所有输出模式下，content 的换行都会自动替换为单字符 `⏎`（U+23CE），整段 content 变成单行；`--content-only` 只是改变"输出 content 文本 vs 完整 JSON"，不影响该压平行为。

### 输出契约（其他 agent 按此解析）

- **stdout 只放机器数据，始终可 `json.loads`**（`--content-only` 例外，其 stdout 是纯文本 content）：
  - 默认（小结果）/ `--inline`：stdout = 完整响应 JSON
  - 大结果：stdout = JSON 信封 `{"ok":bool, "truncated":true, "savedPath":"<路径>", "bytes":int, "content":"<单行文本>"}`
- **所有提示/摘要/诊断（CHAIN-HINT、Saved full response、summarize）一律走 stderr**，不污染 stdout。
- **退出码**：成功 `0`；失败（网络错误 / `errcode` 非 200 / `status==FAILED`）非 `0` —— agent 应优先用退出码判错。

**读数据建议**：小结果直接 `json.loads(stdout)` 取 `content`；大结果读 stdout 信封的 `content`（或按 `savedPath` 用 `jq` 抽完整字段），避免整份 JSON 进入上下文。

## 解决认证和积分问题
发生以下异常情况时，采用 references/onboarding.md 引导解决问题：

### 异常情况
- **未配置API Key**：环境变量未配置 `LINKFOX_AGENT_API_KEY`，也未配置 `LINKFOXAGENT_API_KEY`。
- **响应401或402状态码**
- **响应提示积分或余额不足**：消息含"积分余额不足/计费不足/余额不足/quota exceeded/insufficient balance/套餐到期/需充值/请充值"，或类似含义的内容。

## 自动链式调用决策规则

> **Agent 必须遵循以下决策树**，读到规则即自动执行，无需用户逐步指令。

```
用户需求后续是否涉及 作图 / 生图 / 换模特 / 视频 / imagegen / videogen？
│
├─ YES ──→ 使用 --content-only 模式（换行符已压平为单字符 ⏎，可安全内联拼接）
│           捕获 stdout → 内联拼进下游参数 JSON → 调用下游 Skill
│
└─ NO  ──→ 使用默认模式
            小结果 → json.loads(stdout) 取 content
            大结果 → 读 stdout JSON 信封的 content，或按 savedPath 用 jq 提取
```

### 换行符占位符约定（核心机制）

`content` 通常含真实换行符，直接进 shell 变量或拼接 JSON 会断行。脚本**默认**（任何模式，无需 flag）
把 content 的换行符统一替换为单字符 `⏎`（U+23CE），同时覆盖真实换行控制符与字面量 `\n` 两种形态：

- `⏎` 在 shell 单引号与 JSON 字符串中**均无需转义**，整段 content 变成单行，可被变量安全捕获、内联拼接；
- 下游 AIGC 脚本（imagegen / videogen / videogen-multi）解析参数后会**自动把 `⏎` 还原为换行符**
  （各 AIGC 脚本内联的 `decode_nl_in_obj`），因此文本无损传递；
- 整段 content 变为单行后，可直接捕获进 shell 变量并内联拼接进下游参数 JSON，无需中间文件。

### 标准两步链式调用（imagegen / videogen / 任意 AIGC Skill）

```bash
# ── Step 1：生文，--content-only 直接拿到单行 content（换行已是 ⏎），捕获进变量 ──────
PROMPT=$(python scripts/aigc_textgen.py --stdin --content-only < textgen_params.json)

# ── Step 2：内联拼接进下游参数并调用下游 Skill（jq 负责正确的 JSON 转义） ───────────
PARAMS=$(jq -nc --arg p "$PROMPT" \
  '{prompt:$p, imageUrls:["https://example.com/ref.jpg"], provider:"LF_BN_3", outputNum:1, resolution:"1K", aspectRatio:"1:1"}')
python ../linkfox-aigc-imagegen/scripts/aigc_imagegen.py "$PARAMS"
# 下游脚本接收后自动把 ⏎ 还原为换行符
```

> 没有 `jq` 时，可直接把 `$PROMPT` 内联进单引号 JSON：因 `⏎` 无需转义且已无真实换行，
> 也能安全拼接（前提是 content 内不含双引号；含双引号时优先用 `jq`）。

### 各下游 Skill 的关键参数参考

| 下游 Skill | 关键字段（按需调整，prompt 由上游注入） |
|---|---|
| linkfox-aigc-imagegen | `{"imageUrls":[...],"provider":"LF_BN_3","outputNum":1,"resolution":"1K","aspectRatio":"1:1"}` |
| linkfox-aigc-videogen | `{"imageUrls":[...],"model":"WAN2_1","outputNum":1,"resolution":"720P","duration":5}` |
| linkfox-aigc-imagegen-cloth | `{"imageUrls":[...],"outputNum":1,"aspectRatio":"1:1"}` |
| linkfox-aigc-imagegen-product | `{"imageUrls":[...],"outputNum":1,"aspectRatio":"1:1"}` |

## 使用指引

1. **档位选择**：简单任务可用 `LF_GEM_1`；复杂分析、长文写作或未指定时使用 `LF_GEM_2`。
2. **提示词**：最大 10 万字符，描述越具体效果越好。
3. **图片/视频输入**：通过 `imageUrls` 传入媒体 URL。纯文本用 `[]`；图片理解传 1–10 张图；视频理解通常传 1 个视频 URL（如 `.mp4`）。复杂视频分镜/内容分析建议 `LF_GEM_2` + `thinkingLevel: low`。
4. **思考等级**：需要快速响应选 `minimal`/`low`；需要深度推理选 `high`。
5. **视频失败兜底**：若返回视频不可读、媒体访问失败、`10005` 或内容为空，应抽帧为图片后再传入 `imageUrls`（参见下游业务 skill 的抽帧流程）。

### 示例

**1. 基础文本生成**
```json
{"prompt": "Write a compelling product description for a wireless bluetooth speaker, highlighting portability and sound quality", "imageUrls": [], "model": "LF_GEM_1", "thinkingLevel": "minimal"}
```

**2. 图片 + 文本结合分析**
```json
{"prompt": "分析这张商品主图的构图和卖点表达", "imageUrls": ["https://example.com/product-main.jpg"], "model": "LF_GEM_2", "thinkingLevel": "high"}
```

**3. 视频 + 文本结合分析**
```json
{"prompt": "分析该参考视频的镜头节奏、卖点表达与可复刻的分镜结构", "imageUrls": ["https://example.com/reference.mp4"], "model": "LF_GEM_2", "thinkingLevel": "low"}
```

**4. 快速翻译**
```json
{"prompt": "Translate to German: 'Wireless Bluetooth Speaker with LED Light'", "imageUrls": [], "model": "LF_GEM_1", "thinkingLevel": "low"}
```

## 展示规则

- 直接展示生成的文本内容。

## 限制

- 提示词最大 10 万字符。
- `imageUrls` 最多 10 个 URL；视频分析通常只传 1 个视频 URL，不建议与图片 URL 混传。
- `LF_GEM_2` 不支持 `minimal` 思考等级；服务端会自动兼容为 `low`。
- 失败时最多重试 3 次。

## 适用与不适用

**适用**：
- 商品文案/标题/五点描述生成
- 图片内容分析和描述
- 文本翻译
- 数据分析总结
- 视频分析

**不适用**：
- 图片生成 → `linkfox-aigc-imagegen`
- 视频生成 → `linkfox-aigc-videogen`
- 报告格式输出 → `linkfox-report-generator`

## 反馈

参见 `references/api.md`。
