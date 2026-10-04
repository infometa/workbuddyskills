# 资产报修

## 什么时候读取

用户要提交资产报修时读取本文件。流程是：先查询报修候选（只读）→ 展示候选并附 AI 维修建议 → 用户确认目标（复述确认）→ 执行报修（需确认链）。

## Operation

| Operation | 风险 | 说明 |
| --- | --- | --- |
| `asset.repair.query` | read-before-write | 查询报修候选，按 `asset_name` 过滤；不写数据、不返回 continuation |
| `asset.repair.create` | high-risk-write | 执行报修，需 `confirm:true` + `continuation` |

## 输入要点

`asset.repair.query`：`detail1`（按 `asset_name` 过滤的候选列表，每条 `asset_name` 必填）。

`asset.repair.create`：必填 `detail1`（至少一条；每条 `asset_id`、`fault_desc` 必填，`fault_time` 可选但**必须为 `YYYY-MM-DD HH:mm`（强制带时分，纯日期会被创建动作流拒绝）**，用户未说明时由 Agent 取当前时间）。可选 `repail_name`（未给时由 Agent 生成，≤15 字）、`repail_remark`。需 `prepare -> apply`。

## 展示候选与 AI 维修建议（query 之后、create 之前必做）

`asset.repair.query` 返回候选后，**不要直接进入 create**，按顺序完成：

1. **展示候选**：逐条列出资产名称、资产编号、规格型号与数据 ID（数据 ID 仅内部使用，展示用中文字段含义）；多条时必须交由用户挑选，不自行取第一条。
2. **AI 维修建议**：对每条候选结合用户给出的故障描述，给出简要维修建议（可能原因 / 排查方向 / 处理建议）。该建议由 AI 基于故障描述推理生成，**不是接口返回**，必须明确标注「维修建议由 AI 生成，仅供参考，最终以维修人员判定为准」，不得伪装成系统权威结论；故障描述缺失时说明无法给出针对性建议并请用户补充。**0 条候选时同样要给出维修建议**，并请用户确认资产名称 / 编号是否准确。
3. **复述确认**：进入 create 前向用户复述——报修资产名称 / 编号、故障描述、故障发生时间（`YYYY-MM-DD HH:mm`）——用户明确确认后再执行 `asset.repair.create` 的 prepare/apply 确认链。

## 示例

Windows PowerShell：

```powershell
# 1) 只读查询候选
weaver-work-cli --profile eteams --json asset run asset.repair.query --input-json '{"detail1":[{"asset_name":"EXAMPLE_ASSET"}]}'
# 1.5) 展示候选 + AI 维修建议（标注仅供参考）+ 复述确认（Agent 行为，非命令）
# 2) prepare（返回 continuation）
weaver-work-cli --profile eteams --json asset run asset.repair.create --input-json '{"detail1":[{"asset_id":"EXAMPLE_ASSET_ID","fault_desc":"EXAMPLE_FAULT","fault_time":"2026-09-07 09:30"}]}'
# 3) apply（用户确认后）
weaver-work-cli --profile eteams --json asset run asset.repair.create --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

macOS/Linux（bash/zsh）：

```bash
# 1) 只读查询候选
weaver-work-cli --profile eteams --json asset run asset.repair.query --input-json '{"detail1":[{"asset_name":"EXAMPLE_ASSET"}]}'
# 1.5) 展示候选 + AI 维修建议（标注仅供参考）+ 复述确认（Agent 行为，非命令）
# 2) prepare（返回 continuation）
weaver-work-cli --profile eteams --json asset run asset.repair.create --input-json '{"detail1":[{"asset_id":"EXAMPLE_ASSET_ID","fault_desc":"EXAMPLE_FAULT","fault_time":"2026-09-07 09:30"}]}'
# 3) apply（用户确认后）
weaver-work-cli --profile eteams --json asset run asset.repair.create --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

## 返回

`repair.query` 返回候选：统一含 `resultCode`、`resultMsg`、`mainTable`、`customData`、`responseData`（业务数据在 `mainTable`，等价于 `responseData.customData.mainTable`）。

`repair.create` 成功返回同样的统一结构，关键字段在 **`mainTable`**：

| 业务含义 | 字段 | 用途 |
| --- | --- | --- |
| 报修流程 ID | `lcID` | **作为「查看详情」链接（scene=`asset_repail`）的 dataID** |
| 流程标题 | `lcbt` | 回报给用户；常见为空 |
| 报修单号 | `repail_no` / `bxdh`（具体 key 以运行时返回为准，不臆造） | 报修单号，回报给用户的关键标识 |

字段名来自源资料实测记录（`references/repair-apply.md`）+ 通用约定（`_common.md`：所有资产域动作流业务值挂在 `actionData.responseData.customData.mainTable`，响应字段 `lcID` / `lcbt` / `lybh` 等）。

建单后按 `asset.viewlink` 的 `asset_repail` 场景拼链接：

```powershell
weaver-work-cli --profile eteams --json asset run asset.viewlink --input-json '{"scene":"asset_repail","ids":["<上一步返回的 lcID>"]}'
```

要点：
- `lcID` / `repail_no` 常在建单时**尚未回填**（单号由流程内流水号在提交后生成）。此时不要判定失败、不要重试建单；可先用 `weaver-e10-workflow-connector` 读回补齐，或如实说明「报修单号生成中、链接暂不可用」。
- 链接解析失败只说明「链接暂不可用」，**不影响报修单本身**，绝不因此重试 `repair.create`。

## 注意

- `asset_id` 应为已确认的资产数据 ID；先用 `asset.repair.query` 或 `asset.detail` 取得。
- **维修建议是 Agent 行为，不是命令**：候选展示与 AI 维修建议发生在 `repair.query` 与 `repair.create` 之间，由 Agent 按上文「展示候选与 AI 维修建议」执行，不消耗额外 CLI 调用。
- `fault_time` 传纯日期（如 `2026-09-07`）会被 schema 拒绝；用户只给日期未给时间时，补成该日某时刻或与用户确认，不要原样传入。
- 出现 `partial/write_uncertain` 时停止，先做一次只读回查，不要重复提交 apply。
