---
name: mibao
description: 当用户要实际盘点影像目录、严格哈希识别重复项、建立本地索引与报告，或检索已有秘宝项目时使用；专家不安装或连接本地 MCP。
allowed-tools: Write, Bash, Read
---

# 秘宝执行主方法

`execution_core_v1` 是零 MCP 的真实执行范围。实际任务必须通过包内一次性闭合入口生成项目、索引或报告；任务书和建议只能辅助执行，不能替代结果。

## 当前 operation

1. `inventory_build`：只读扫描 → 类型识别 → 严格 SHA-256 → Asset/FileInstance 与精确重复组 → SQLite FTS5 → HTML/CSV/JSONL/manifest 盘点报告；
2. `inventory_search`：已有项目内只读 FTS 检索 → 相对路径、稳定 ID、命中摘要与证据引用。

除此以外的转换、缩略图、联系表、OCR、ASR、语义识别、片段/素材包导出和发布均保持 `not-run` 或 `blocked`。

## 执行前门

- 明示一个绝对源目录和一个互不包含的绝对项目目录；
- 明示源目录只读、项目目录可写、零网络/零外发/零 MCP/零连接器；
- 取得用户对精确目录和边界的确认；
- 不把工作空间、磁盘或用户主目录自动扩成扫描范围。

## 请求与命令

使用 WorkBuddy 原生文件写入能力创建闭合请求。请求根只能是当前会话系统上下文明确给出的绝对 Workspace Folder 下 `.workbuddy`，作用域固定为 `session-workspace`，请求使用 `<ABSOLUTE_WORKSPACE_FOLDER>/.workbuddy/mibao/expert-request.json`。禁止为定位路径运行 Bash/PowerShell、读环境变量、遍历 `.workbuddy`、扫描源码/Schema 或探测 Python 版本；本 Skill 的绝对目录必须由 WorkBuddy 在加载时通过 `${CODEBUDDY_SKILL_DIR}` 解析，不能由模型发现 plugin root。宿主上下文不能直接提供绝对 Workspace Folder、请求根、请求路径、已解析 Skill 目录或托管 Python 时失败关闭。禁止通过 Shell echo、重定向或插值写请求。

随后通过原生命令工具只允许一次固定 one-shot，且请求根、作用域与实际写入路径必须精确一致：

```text
# session-owned fallback variant
python "${CODEBUDDY_SKILL_DIR}/../../bin/mibao-expert.py" execute --request "<ABSOLUTE_WORKSPACE_FOLDER>/.workbuddy/mibao/expert-request.json" --request-root "<ABSOLUTE_WORKSPACE_FOLDER>/.workbuddy" --request-scope session-workspace
```

`${CODEBUDDY_SKILL_DIR}` 必须在本 Skill 加载时替换为当前 `skills/mibao` 绝对目录；若仍是字面量则失败关闭，不得用 registry、Glob、Skill 列表或目录搜索补救。Workspace Folder placeholder 只能由当前会话系统上下文直接提供。用户数据只能在请求 JSON 内。不得增加其他 argv、改用任意脚本、安装 Python、启动后台服务或查找 `mibao-local`。若 WorkBuddy 自带 Python 不可解析，失败关闭。严格有效的固定路径请求会在访问源目录或项目目录前被消费；失败时按 `requestDisposition` 与 `recovery` 决定是否重写请求，可能残留时转人工处理。

每项 operation 的宿主预算是一次原生 Write 加一次固定 one-shot。原生命令工具只可执行这条精确 Python argv；禁止任意 Shell、`-c`/`-Command`、管道、重定向、命令拼接和路径发现。build 后只读结果点名的 manifest/HTML，全部验收后最多一次 `present_files`；禁止 `ls/find/rg`、环境/版本/网络/进程探针、源码审计及其他诊断命令。WorkBuddy 系统强制的 session-local daily memory 只能在完成后由宿主执行并单独披露；专家不得主动创建长期 memory、Skill 或跨项目记录。

请求的默认有界参数：

- `scanBatchSize=128`
- `hashBatchSize=64`
- `maxEntries=100000`
- `maxDepth=32`
- `htmlPreviewRows=1000`
- `inventory_search.limit=20`

用户可以要求更小的预算；不得超过 schema 上限。

## 完成门

完成必须同时具备：

- 单个、闭合、schema-valid 的结果 JSON；
- 实际项目与 SQLite 数据库；
- 严格哈希和当前精确重复统计；
- FTS 索引数量；
- 可回读的报告 manifest 和 HTML；
- 检索结果的相对路径、稳定 ID、摘要与非空 evidence refs；
- 检索结果的 `privacyMode=local-private`；
- 零网络、零外发、零 MCP、零常驻进程边界。

闭合路径策略拒绝的单个文件名和 reparse 条目只进入 `scan.issues`，不得读取、跟随、哈希或索引；只要其余扫描完整，结果以 `partial` 交付。不可读条目、离线源、身份漂移、扫描中断和预算超限仍整体失败关闭。已有但完全为空的项目目录允许初始化；非空非项目目录仍拒绝。

任何一项缺失都不得使用 `completed`。运行失败时保留可恢复项目，报告 `partial` 或 `blocked`，不靠顾问文稿补足。

## 结果表达

先给状态与实际数量，再给项目目录及报告相对路径，然后列异常、未执行能力和人工复核项。未知保持 `unknown`；不得把旧版、完整插件、仓库测试或诊断 probe 当作当前用户任务证据。

文件名中的点只作为安全检索 token 分隔符，例如 `normal.jpg` 等价于同时匹配 `normal` 和 `jpg`；引号、通配符、FTS 操作符、路径符和连续/首尾点仍拒绝。重复组以 `content.exactDuplicateGroupCount` 和报告 `strict_as_of_exact_duplicate_group_count` 表达本次/token 时点结果；报告 `current_exact_duplicate_group_count=0` 是保守实时语义。

## 方法路由

- 盘点、索引与检索：`mibao-index-policy`
- 原件保护与验收：`mibao-safety-qa`

格式转换、视觉、OCR 与 ASR 没有随本专家激活方法 Skill；直接说明当前未开放。
