# Picset 风格复刻共享手册

供 [复刻 Skill](../picset-style-replicate/SKILL.md) 使用。一次复刻生成 1 张图片；产品素材数量不是生成数量。明确复刻意图优先于用途，“复刻一张淘宝主图”也使用本手册。

调用前通过 `tool_search` 获取完整 live schema。工具不可用不切换普通电商/单图。凭据不进入提示词、日志或交付内容，不用直接 HTTP 或自写协议替代 MCP。

## 一、素材与规格

- `reference_image`：1 张风格参考图，必填。
- `product_images`：1–6 张商品图，必填数组。
- 两类均须为当前用户已获准使用、已登记审核通过的 Picset OSS 相对路径或授权 CDN URL。普通可访问外链不等于复刻素材已获授权。
- 先确认角色，不能把所有图塞到无角色的参考图数组，也不能默认第一张是风格图。
- 按已有素材记录的规范 OSS 路径检查重复：风格图与任一商品图不得是同一对象，商品图之间也不能重复；同对象的相对路径/CDN URL 视为重复。不能确认映射时先核对登记结果，不猜测，不通过重传同一张图绕过角色要求。
- 超过数量上限时保留原素材记录，请用户选择；不静默丢弃或拆成多次收费任务。
- `requirements` 可省略或为空，最多 4000 字符。仅写用户确认的用途、参考方向、调整和可靠商品事实。超长先精简并确认，不截断关键需求。
- 默认模型 `nova-2.0`、分辨率 `2K`、比例 `1:1`、速度 `fast`；报价与提交显式传相同规格。
- 模型选项与合法规格按 live schema；`nova-2.0-lite` 固定 `1K`，极端比例 `1:8 / 1:4 / 4:1 / 8:1` 只用于 `nova-2.0 / nova-2.0-lite`。不支持的组合先说明并确认替代，不静默修改。
- 不单独开放 `quality` 选项：复刻工具无该参数。不得传 `count`、`image_count`、`outputCount`、`image_type`、`target_language`、`style_intensity` 或 `keep_product_color` 给复刻生成工具。

## 二、报价与确认

方案已确认且素材角色明确后，调用 `quote_image_credits`，仅按本次物理规格报价：

```json
{
  "model": "nova-2.0",
  "resolution": "2K",
  "aspect_ratio": "1:1",
  "speed_mode": "fast",
  "count": 1
}
```

- `count` 永远为 1，不按商品图数量计价，不同时传别名 `image_count`；不向报价工具传素材、业务类型、提示词、请求 ID 或确认状态。
- 使用返回 `items[].credit_cost_per_image`、`items[].subtotal_credits`、顶层 `estimated_credits` 展示单价、小计、总计及实际规格；缺少可靠费用或报价错误时停止，不将缺失当作 0。
- 提示最终按提交时实时积分扣除，可能与预估不同。
- 完整执行 [共享积分确认规则](./credit-confirmation-playbook.md)。已明确授权自动确认时仍展示报价，但不等重复回复；否则等待本次费用确认。与电商、单图使用同一偏好文件，恢复确认统一生效。
- 费用授权完成后、上传或提交前，必须按 [连接器充值手册](./connector-pricing-playbook.md) 调用 `get_user_credits`，将 `available_credits` 与本次 `estimated_credits` 比较；余额不足则打开充值面板并停止。
- 修改方案或规格后重新报价；旧的单次确认失效，跨能力自动确认偏好仍按共享规则读取。

## 三、上传登记

费用授权且生成前余额校验通过后，对尚未登记的本地素材复用 [电商执行手册的上传登记操作](./execution-playbook.md#三上传登记)：

`get_reference_image_upload_token` → 公共 `picset_client.py upload` → `register_reference_image`

这里只复用凭证处理、上传脚本与登记操作，不继承电商报价、素材数量上限或生成批次规则。复刻仍是风格 1 张＋商品 1–6 张。

- 用已有公共脚本，不新增上传实现或依赖。STS仅按原手册安全标准输入传递，不写日志/文件/命令行参数。
- `__SKILL_DIR__` 为复刻子 Skill 目录，打包后的公共脚本位于 `__SKILL_DIR__/../../scripts/picset_client.py`。若脚本不存在报告安装不完整，不自行拼凑替代脚本。
- 把 `oss_path` 与登记返回的授权 URL 写回对应原素材记录，保留角色。无法确认归属或审核状态时，不直接使用普通外链提交。
- 已完成登记的合法素材可复用；失败只处理该素材，不重传全部。凭证过期需确认用户仍要继续后再获取新凭证。
- 按既有上传器的单文件大小/MIME等限制处理，不从生成 schema 推断上传大小无限制。

## 四、提交复刻

素材全部登记、费用已获授权且生成前余额校验已通过后，为本次请求保存 UUID v4 `request_id`，调用 `generate_style_replicate`：

```json
{
  "reference_image": "<已登记风格图 OSS 路径或授权 URL>",
  "product_images": ["<已登记商品图 OSS 路径或授权 URL>"],
  "requirements": "按参考图风格制作淘宝主图，替换为我的商品",
  "confirmed": true,
  "request_id": "<本次请求保存的 UUID v4>",
  "model": "nova-2.0",
  "resolution": "2K",
  "aspect_ratio": "1:1",
  "speed_mode": "fast"
}
```

这里淘宝主图作为 `requirements` 用途要求，不传电商类型参数，不调用 `generate_commerce_images` 或 `generate_agent_canvas_image`。

提交结果字段：`task_id`、`job_id`（同值）、`status`（提交返回 `processing`）、`model`、`resolution`、`aspect_ratio`、`speed_mode`、`charged_credits`。保存原请求参数、ID、任务标识和首次有效费用记录；不要用返回的内部模型名覆盖原公开模型参数。

- `task_id`/`job_id` 缺失或不一致时保留完整响应并报告异常，不编造任务标识或宣称生成成功。
- 同一请求重放仍可能返回 `processing`，即使任务已完成或失败；真实状态以查询工具为准。
- `charged_credits` 在重放时也会返回计算值，不是又发生一次扣款的证明；已有首次费用记录时不覆盖、不累加。若只有重放响应，可注明“本次响应费用”，不能断言它是最初实际扣款。

## 五、查询与交付

使用 `get_generation_task_status`，不是 `get_agent_canvas_image_status`：

```json
{"task_id": "<提交返回的 task_id>"}
```

固定 30 秒间隔静默轮询；期间不读写本地文件。不向用户逐次播报，达到宿主执行时限则保存状态后停止等待。

响应结构：
- `task_id`：原任务。
- `status`：`processing` / `success` / `failed`。
- `image_count`：1；`completed_count` 与 `failed_count` 表示终态数量。
- `items`：一项，`index` 为 0；成功含 `image_url`，失败含 `error_code`、`error_message`。

成功必须同时有成功状态和非空图片 URL。索引不是0、结果数量异常、缺URL或未知状态时，不猜测映射，不把不完整响应当成功。

用预存 `stable_ids[0]` 恢复 `R1` 等编号。复用 [公共交付流程](./execution-playbook.md#六交付) 的安全下载和 `present_files` 展示，传复刻编号：

```bash
mkdir -p "<当前工作目录绝对路径>/picset_output/<task_id>"
python3 __SKILL_DIR__/../../scripts/picset_client.py deliver <<'EOF'
{"items":[{"id":"R1","image_url":"<成功结果的 image_url>"}],"output_dir":"<当前工作目录绝对路径>/picset_output/<task_id>"}
EOF
```

- Windows可用 `python` 替代 `python3`；不转码、压缩或修改图片字节。
- 使用返回的本地绝对路径通过 `present_files` 展示，不在对话中贴图片URL或内部任务标识。
- 下载失败只恢复下载；图片已生成时不要重建付费任务。`present_files` 不可用时说明生成/下载状态及展示阻塞，不假装已交付。
- **交付成功后必须自动打开画布**：按 [Agent Canvas 手册](./agent-canvas-playbook.md)「交付后打开 + 校验 + 兜底插入」：无 `initial_images` 打开 → `get_agent_canvas_state` → 缺本批图再 `insert`。解析失败时跳过画布步骤并说明，本地交付仍有效；全部失败不打开画布。
- 状态查询不返回最终扣费/退款明细；不能根据 `failed` 宣称退款到账。只报告真实结果与可确认费用。

## 六、幂等与错误恢复

| 情况 | 操作 |
| --- | --- |
| 提交网络中断、结果不明 | 保存原参数与 request_id；有任务ID先查询，无任务ID可原样重放最多一次，不自动换ID |
| 返回原 job_id/status=processing | 查询原任务，不当成新图，不累计重复费用 |
| 轮询超时 | 保留原 task_id 后续继续查询，不重新生成 |
| 已终态失败，用户要重新生成 | 新请求：保留原稳定编号，重新确认方案、报价和授权，用新 request_id，结果放新任务目录 |
| 用户修改素材、提示词或规格 | 新方案/新请求，不用旧幂等键携带新内容 |
| 素材未授权/重复/超限 | 解决素材问题，先检查是否已有任务；不得用换工具或复制同一素材绕过 |
| 积分不足 | 生成前余额不足或提交/执行返回不足时：立即停止上传/生成与轮询，立即调用 open_agent_pricing，不以询问代替；不展示URL/ticket |

除相同请求的安全重放外不自动重试收费任务。错误响应、空响应、部分响应不能当作成功。跨轮次恢复遵循 [公共交接协议](./handoff-protocol.md)，不能只保留图片URL而丢失请求/任务标识。
