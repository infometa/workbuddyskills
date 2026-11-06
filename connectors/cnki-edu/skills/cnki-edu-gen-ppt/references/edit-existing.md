# 编辑已有 PPTX

上级：[SKILL.md](../SKILL.md)。工具清单：[slide-tools.md](slide-tools.md)。

对已有 `.ppt` / `.pptx` 做改稿（改标题、改某一页、增删页、改文字/形状/图表等），以及 **本 Skill 生成完成后的后续修改**。

## 调用约定

脚本路径必须带 `${CODEBUDDY_SKILL_DIR}`（Bash 的 cwd 是 workspace 根）：

```bash
python3 "${CODEBUDDY_SKILL_DIR}/scripts/edsdk.py" list slide
python3 "${CODEBUDDY_SKILL_DIR}/scripts/edsdk.py" schema <工具名>
python3 "${CODEBUDDY_SKILL_DIR}/scripts/edsdk.py" call <工具名> [k=v ...] [--json '{...}'] [--json-file args.json]
```

未设置 `editor_sdk_port` 时按 39099–39108 探测；鉴权时设 `editor_sdk_token`。

### 强制：先 schema 再调用

对任何 `slide_*`：**用到一个查一个**，不要一次性拉全量 schema。

1. 从 [slide-tools.md](slide-tools.md) 的一句话清单里选出工具
2. `python3 "${CODEBUDDY_SKILL_DIR}/scripts/edsdk.py" schema <工具名>`
3. 确认 `[✓]` 必填项、0-based 索引、pt 单位后再 `call`

未经 `schema` 直接拼参数属于流程违规。不确定参数时，默认你没查过——先 schema，不要凭摘要猜。

调用前自检：

- ☐ 已对**本次要用的工具**跑过 `schema`
- ☐ 已确认全部 `[✓]` 必填字段
- ☐ 已确认 `page_index` / `shape_index` 为 0-based、坐标单位为磅 `pt`

## 工作流：先打开，再编辑，最后保存

本套操作是实时、可视化的。保存用 `save_file`；**不要主动 `close_file`**（会关掉用户正在看的视图）。仅在用户明确要求关闭或确实需要释放资源时才 `close_file`。

### `file_id`

`file_id` 是 pool 里实例的 key，**不一定是路径**。后续 `slide_*` 一律用真实 `file_id`。

要让用户在预览面板看到文档，必须调用宿主的 **`present_files`**，不能只在回复里说「已打开」。`open_file` 只在后台把文件读进内存，预览面板不会出现这份文档。

- `present_files` 返回的是文件地址，**不是** `file_id`，不能直接传给 `slide_*`
- `present_files` 之后用 `get_pool_status` 按**同一路径字符串**拿 UUID `file_id`；不要再默认 fresh `open_file`（会再开一个与预览脱节的实例）
- 上下文已注入 `file_id`（如 `<active_document type="local" ... file_id="..."/>`）时直接用，不要重开
- 仅后台、无需用户预览时，才用 `open_file`；用户已在看文档时不要默认 `open_file`

```bash
# 1. 预览面板呈现（硬约束：必须 present_files）
present_files：把 /abs/a.pptx 打开给用户看

# 2. 从 pool 拿真实 file_id（不要 open_file）
python3 "${CODEBUDDY_SKILL_DIR}/scripts/edsdk.py" call get_pool_status --json '{"file_path":"<同上路径>"}'
#    → editors 里取 file_id（多为 UUID）

# 3. 先 schema，再编辑
python3 "${CODEBUDDY_SKILL_DIR}/scripts/edsdk.py" schema slide_set_text
python3 "${CODEBUDDY_SKILL_DIR}/scripts/edsdk.py" call slide_set_text file_id=<上一步 file_id> ...

# 4. 保存（file_path 省略则覆盖原文件）—— 到此即可，不要主动 close
python3 "${CODEBUDDY_SKILL_DIR}/scripts/edsdk.py" call save_file file_id=<上一步 file_id>
```

`get_pool_status` 未命中时：再 `present_files` 一次并用相同路径查询；仍无则 `open_file file_path=... open_with_existing=true`；再失败与用户确认路径。

编辑后若要基于文档现状继续操作，先重新读取；不要沿用编辑前缓存的页码、形状或文本。

## 入口工具

| 工具 | 说明 |
|---|---|
| `get_pool_status` | `present_files` 之后用它拿 UUID `file_id` |
| `open_file` | 仅后台打开；有预览时不要默认 fresh open |
| `save_file` | 保存到本地 |
| `close_file` | 不要主动调 |
| `create_slide` | 空白 pptx 模板；有内容创作需求时走生成分支，不要用空白模板凑一版 |

选具体 `slide_*` 工具、坐标与层级约定：阅读 [slide-tools.md](slide-tools.md)。
