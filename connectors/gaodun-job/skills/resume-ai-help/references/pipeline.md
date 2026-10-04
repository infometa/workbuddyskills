# Resume AI Help 本地运行协议

只在准备 MCP 资源、执行单字段命令或运行整份编排时读取。

## 资源物化

建议每次任务使用独立临时资源目录，例如 `.qa/tmp/resume-ai-help/resources/`。

默认路径固定为一次 `resume_resource_bundle_get` + 一次 `materialize_resources.py ingest-bundle`。MCP 响应由宿主原样保存到资源目录的同级临时文件；Python 再复制到 `raw/bundle-response.json`。不得逐资源落盘、逐字符改写、通过 shell 内联大 JSON，或生成临时 Python 文件。

### 1. 聚合工具调用

| 模式 | 唯一 MCP 调用参数 | Python 参数 |
|---|---|---|
| 单字段 | `{"prompt_ids":["<promptOneId>","<promptTwoId>"]}` | `--mode single --prompt-ids <两ID>` |
| 整份优化 | `{"include_all_prompts":true,"include_module_config":true,"theme":"default"}` | `--mode full` |
| 仅排版 | `{"include_module_config":true,"theme":"default"}` | `--mode layout` |

### 2. 一次物化

```bash
python scripts/materialize_resources.py ingest-bundle \
  --input <bundle-response.json> --out-dir <资源目录> --mode <single|full|layout> \
  [--prompt-ids <promptOneId,promptTwoId>]
```

该命令一次完成 schema/模式校验、Prompt ID 对账、模板转换、全部文件及 manifest hash 写入、完整性检查和事务替换。成功后不要再启动独立 `verify`。

### 3. 兜底判定

仅在 `tools/list` 没有 `resume_resource_bundle_get`，或调用返回协议级“未知工具/方法/能力不支持”时，整项任务改走旧的三个工具。连接失败、超时、服务不可用、`isError=true`、响应 schema/ID 不匹配、转换/写盘/hash/校验失败都必须直接报告，不得兜底。开始兜底后不得与聚合资源混用。

- 单字段：旧索引 → 两个 Prompt → `verify --prompt-ids`。
- 整份：旧索引 → 模块配置 → default 模板 → runner `init` → 根据 `requiredPromptIds` 取 Prompt → `verify --prompt-ids`。
- 仅排版：模块配置 → default 模板 → `verify --layout-only`。

旧的 `init`、`ingest-prompt-index`、`ingest-prompt`、`ingest-module-config`、`ingest-template`、`verify` 命令只为此兜底和诊断保留。

### 4. 标准目录

```text
<资源目录>/
├─ raw/                              MCP 原始响应
├─ prompts-index.json
├─ prompts/prompt-<id>.txt
├─ resume-module-config.json
├─ templates/source/personal_resume_onepage_<theme>.html
├─ templates/converted/personal_resume_onepage_<theme>.html
└─ manifest.json                     路径与 SHA-256，不含资源正文和用户数据
```

## 单字段文件协议

`fields.json` 是对象，key 必须来自 `field-config.json.variableMappings` 左侧。`qa.json` 是最多 3 条的数组：

```json
[
  {"question": "追问内容", "answer": "用户答案"},
  {"question": "追问内容", "answer": ""}
]
```

模型原始输出分别保存为 `ask-response.json` 和 `optimization-response.json`。落盘只走 `scripts/save_response.py`（响应经 stdin 传入，脚本校验 UTF-8/JSON/字面量 `\n` 后写盘）；禁止 shell `>` 重定向（Windows 下会写 UTF-16 BOM）、禁止把响应硬编码进临时脚本转写、禁止将多行正文改写成字面量 `\\n` 后拼入命令：

```bash
<LLM 原始响应> | python scripts/save_response.py --out optimization-response.json
```

## 整份编排

### 意向岗位门禁

`position` 是所有 12 类优化 Prompt 的公共 `job` 变量。runner 的卡点是“必须完成一次确认”，不是“岗位值绝对必填”：

| `init` 结果 | 进入条件 | 命令 / 动作 | 输出与后续 |
|---|---|---|---|
| `positionMissing=false` | 简历已有岗位 | 不重复询问 | 可进入 `next` |
| `positionMissing=true` | 用户尚未确认 | 单独询问一次并停止 | 暂不得进入 `next` |
| 用户给出岗位 | 已收到明确岗位 | `set-position --position "<目标岗位>"` | 回填全部队列项后进入 `next` |
| 用户明确不填/要求通用优化 | 已收到明确跳过决定 | `set-position --skip` | 岗位变量按空值规则填“无”，然后进入 `next` |

仅排版不执行内容优化，因此不需要岗位门禁。用户只提供岗位名称即可定向优化，JD 不是默认必填；只有用户明确要求按具体 JD 匹配时，缺失 JD 才需要停止询问。

初始化：

```bash
python scripts/full_resume_runner.py init \
  --finalized finalized.json --state runner-state.json \
  --overrides overrides.json --resources-dir <资源目录>
```

循环动作：

```bash
python scripts/full_resume_runner.py next --state runner-state.json
python scripts/full_resume_runner.py answers --state runner-state.json --qa-file qa.json
python scripts/full_resume_runner.py skip-questions --state runner-state.json --confirmed-by-user
python scripts/full_resume_runner.py no-questions --state runner-state.json   # 追问响应零问题（parse-ask questions=[]）时
python scripts/full_resume_runner.py complete --state runner-state.json \
  --response-file optimization-response.json
python scripts/full_resume_runner.py skip-item --state runner-state.json --confirmed-by-user
python scripts/full_resume_runner.py status --state runner-state.json   # 只读进度概览
```

只有 `next` 返回 `render_html` 后才能执行：

```bash
python scripts/full_resume_runner.py render-html --state runner-state.json \
  --resume-name "<姓名的简历>" --out resume.html
```

`skip-questions` 只跳过追问，仍会优化；`skip-item` 才跳过当前字段，两者均必须由用户明确决定。`no-questions` 是系统路径：仅当追问 prompt 响应零问题时使用，无需用户确认。

## 失败处理

- MCP 返回 `isError=true`：报告工具错误，不保存为有效资源。
- Prompt ID 或模板 theme 不匹配：拒绝物化。
- 资源不完整：`verify` 一次列出全部缺项。
- 模板转换残留 Freemarker 语法：停止 HTML 生成，不手改模板绕过。
- Runner 状态已存在：继续 `next`，不重复初始化覆盖进度。
