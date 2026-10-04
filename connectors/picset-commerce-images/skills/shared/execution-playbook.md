# Picset 共享执行手册

本手册定义电商图片生成流程中报价、上传、生成、轮询、交付与画布承接的标准操作。电商 Skill 按本手册执行；单图按专属手册执行，不借用此处电商报价与生成工具。跨能力费用授权统一遵循 [共享积分确认规则](./credit-confirmation-playbook.md)。

调用 MCP 工具前，必须使用 `tool_search` 按工具名获取完整参数定义，再按取回的定义发起调用。禁止凭工具名猜测参数结构。

---

## 一、执行总流程

方案确认后，按以下顺序执行：

1. **只读报价**：调用 `quote_commerce_image_credits`，展示主图/详情图的数量、比例、分辨率、单价、小计和总计。该回合不上传、不登记、不生成。
2. **积分确认**：先读取 `__SKILL_DIR__/user_preferences.json`。若 `confirm_credits` 为 `false`，展示预估积分后直接进入下一步，不等待确认；否则向用户明确询问是否接受预估积分，说明最终按提交时实时积分扣除，可能与预估不同，等待用户新的明确确认消息。首次无偏好文件时，在报价后询问用户是否以后跳过积分确认。详见第七节。
3. **余额校验**：费用授权完成后、上传前，调用 `get_user_credits`，将 `available_credits` 与最新报价总计比较。余额不足则立即打开充值面板并停止，不上传、不生成。细则见 [连接器充值手册](./connector-pricing-playbook.md)。
4. **上传登记**：余额足够后，对每个本地素材执行 `get_reference_image_upload_token` → `picset_client.py upload` → `register_reference_image`。
5. **提交生成**：素材全部登记后，按主图/详情图/A+ 商品图分批调用 `generate_commerce_images`，保存返回的 `task_id`。
6. **静默轮询**：固定 30 秒间隔调用 `get_generation_task_status`，直到所有批次进入终态。
7. **结果交付**：按稳定编号恢复结果，将成功图片下载到本地，通过 `present_files` 展示本地路径。
8. **画布自动承接**：有成功图时，按 [Agent Canvas 共享手册](./agent-canvas-playbook.md) 第三节**打开 → 校验 → 缺图再 insert**；不等待用户要求。

不探索其他脚本、工具或服务。任一阶段失败时，保留已完成状态，不自动重建已提交任务。

---

## 二、报价

### 工具

`quote_commerce_image_credits`

### 用途

对已确认的套图方案执行只读报价，返回预估积分。不上传、不登记、不生成、不锁定积分。

### 前置条件

- 方案草稿已完整，没有阻塞事实
- 用户已明确确认方案
- 已按主图/详情图/A+ 商品图建立执行批次

### 入参

```json
{
  "batches": [
    {"image_type": "main", "image_count": 5},
    {"image_type": "detail", "image_count": 6}
  ]
}
```

- `image_type`：`main`、`detail` 或 `aplus`
- `image_count`：1-16 的整数，每批不超过 16 张
- 每个批次只能包含 `image_type` 和 `image_count` 两个字段，不得传入 `batch_id`、`stable_ids`、`request_id`、比例、分辨率或其他展示字段

### 返回与展示

返回每批的单价、小计和总计。向用户展示时必须逐行列出（下方为默认配置示例，用户指定了自定义比例或分辨率时按实际值展示）：

> 主图：5 张（1:1 / 2K，默认），单价 X 积分 → 小计 Y 积分
> 详情图：6 张（3:4 / 2K，默认），单价 X 积分 → 小计 Y 积分
> 总计：Z 积分

用户指定自定义比例或分辨率时，按实际值展示，例如：

> 主图：3 张（9:16 / 4K），单价 X 积分 → 小计 Y 积分

不包含某类图片时省略该行，不得编造零数量报价。

### 约束

- 只有方案确认后才能调用
- 只读报价，不锁定积分
- 报价后，若用户偏好为跳过积分确认则直接继续；否则必须结束当前回复，等待用户新的明确积分确认
- 用户修改平台、数量、比例、卖点或风格后，原报价失效，需回到方案确认
- `batch_id`、`stable_ids` 和 `request_id` 只保留在本地上下文，不发送给报价工具

---

## 三、上传登记

### 用途

把本地商品素材上传到 OSS 并登记为服务端可用的参考图 URL。

### 前置条件

- 用户已明确确认积分，或用户偏好设置为跳过积分确认
- 已按 [连接器充值手册](./connector-pricing-playbook.md) 完成生成前余额校验，且 `available_credits` 不低于最新预估
- 素材有本地路径，尚未登记

### 固定链路

对每个素材依次执行以下三步，不得跳过或替换：

```
get_reference_image_upload_token
→ scripts/picset_client.py upload
→ register_reference_image
```

#### 第一步：获取上传凭证

调用 MCP 工具 `get_reference_image_upload_token`，获取短期 OSS STS 凭证。

#### 第二步：本地上传

使用单引号定界的 heredoc 把 token 和文件路径通过标准输入交给公共上传器：

```bash
python3 __SKILL_DIR__/../../scripts/picset_client.py upload <<'EOF'
{"token":"<工具返回的 structuredContent>","file_path":"<本地图片绝对路径>"}
EOF
```

- 跨平台兼容：Windows 下 `python3` 可能不可用，可改用 `python` 执行同一命令
- `__SKILL_DIR__` 解析为当前子 Skill 文件所在目录，不得从会话工作目录猜测脚本位置
- 不得把包含 `content`、`isError`、`resultType` 的 MCP 外层结果当作 token
- 不得使用 `--file`、`--token` 等命令行参数承载 STS
- 仅允许使用单引号定界的 heredoc（`<<'EOF'`）传递 STS，禁止双引号定界的 heredoc 以防止变量展开；禁止 echo、临时文件、环境变量传递 STS
- 不得使用 curl、内联 Python、第三方 OSS SDK 或自建替代上传流程
- 不得安装 `requests`、`oss2`、Pillow 或任何第三方依赖

上传成功返回 `oss_path`、`file_type`、`file_size`。

#### 第三步：登记素材

调用 MCP 工具 `register_reference_image`，传入上传结果，获取服务端登记的参考图 URL。

把返回的 URL 写入原素材记录，不创建第二份素材记录。

### 约束

- 只处理当前已确认的素材
- 服务最多接收 9 张参考图；超过时保留全部素材记录，每次只问一个选择问题，不静默丢弃
- 服务端支持上传的参考图最大不超过 20M
- 任一步失败都停止该素材的后续登记和生成，保留已完成素材，只报告可恢复的失败步骤
- 脚本不存在或无法读取时，立即报告"本地 Skill 安装不完整"，不得创建替代脚本

---

## 四、生成提交

### 工具

`generate_commerce_images`

### 用途

素材全部登记后，按批次提交生成任务。

### 前置条件

- 所有素材已完成上传登记，有参考图 URL
- 用户已确认积分，或用户偏好设置为跳过积分确认
- 生成前余额校验已通过；提交前若距上次校验已隔较长时间或用户刚充值回来，可再次调用 `get_user_credits` 确认

### 分批规则

- 按图片类型分批：主图一批、详情图一批、A+ 商品图一批
- 每批最多 16 张；同类超过 16 张时继续切分
- 每个批次在建立时生成并保存一个 UUID v4 `request_id`，提交和重试时复用同一个 `request_id`，不得换新值
- 分批只改变执行结构，不改变用户要求的数量或稳定编号

### 入参

每个批次调用一次，关键参数：

- `image_type`：`main`、`detail` 或 `aplus`
- `image_count`：该批图片数量
- `reference_image_urls`：已登记的参考图 URL 数组
- `requirements`：逐图要求，包含每张图的标题、商业任务、主要画面和文案方向
- `request_id`：本地保存的 UUID
- `confirmed`：必须为 `true`

具体参数结构以 `tool_search` 返回的 schema 为准。

### 返回

保存服务返回的 `task_id`，并把该批图片标记为 `submitted`。

### 约束

- 不得先调用 `generate_commerce_images` 试探或校验 `request_id`
- 某一批提交失败时，保留已成功提交的批次及其任务，只重试未提交或失败批次
- 生成前余额不足或提交返回积分不足时，停止后续生成和轮询，调用 `open_agent_pricing` 打开连接器统一充值面板，不得向用户展示 URL

---

## 五、轮询

### 工具

`get_generation_task_status`

### 用途

跟踪已提交任务的状态，直到进入终态。

### 节奏

- 固定 30 秒间隔调用一次
- 不临时决定等待时长
- 不向用户输出逐次进度消息
- 轮询期间不读写本地文件

### 状态处理

- `processing`：继续轮询
- `success`：该批次完成，记录结果
- `failed`：该批次失败，记录失败项
- 部分成功：保留成功结果，记录失败项

### 编号恢复

服务返回批内 `index`、`status` 和成功项的 `image_url`。使用保存的 `stable_ids[index]` 恢复 `M1`、`D1` 等稳定编号：

- `id = stable_ids[item.index]`
- 不得按完成顺序、成功顺序或返回顺序重新编号
- 索引越界、重复稳定编号或成功项缺少 `image_url` 时，停止该项交付并报告数据错误

### 超时处理

- 累计等待达到合理上限时停止轮询
- 保留原 `task_id`，告知用户任务仍可能在后台处理
- 不得自动新建任务或重新提交
- 用户后续可凭 `task_id` 恢复查询

---

## 六、交付

### 用途

把生成结果按稳定编号交付给用户。生成完成后，agent 通过公共交付器 `picset_client.py deliver` 将成功图片从服务端返回的 `image_url` 下载到本地，再通过 `present_files` 工具以本地路径展示给用户。本地交付完成后，有成功图时还必须按 [Agent Canvas 共享手册](./agent-canvas-playbook.md) **打开画布并校验**；宿主推送未到位时兜底 `insert`。不输出图片链接。

### 成功项条件

- `status == "success"`
- `image_url` 非空

### 下载到本地

下载时机：轮询确认该批次进入终态后，立即对所有成功项执行下载。

下载命令（先建立输出目录，再通过单引号定界 heredoc 把交付清单交给公共交付器）：

```bash
mkdir -p "<当前工作目录绝对路径>/picset_output/<task_id>"
python3 __SKILL_DIR__/../../scripts/picset_client.py deliver <<'EOF'
{"items":[{"id":"M1","image_url":"<image_url>"},{"id":"D1","image_url":"<image_url>"}],"output_dir":"<当前工作目录绝对路径>/picset_output/<task_id>"}
EOF
```

- `<task_id>` 用服务端返回的任务 ID
- `<稳定编号>` 用 `M1`、`D2` 等，与用户看到的编号一致
- `output_dir` 必须为绝对路径，指向当前工作目录下的 `picset_output/<task_id>/`
- 跨平台兼容：Windows 下 `python3` 可能不可用，可改用 `python` 执行同一命令
- 交付器内置安全校验：HTTPS 校验（含重定向后）、Content-Type 校验、30 MiB 文件大小上限、原子写入、稳定编号格式校验；校验失败时报错并停止该项交付
- 文件名由交付器按实际 Content-Type 生成（如 `M1.png`、`D1.jpg`、`D2.webp`），不修改、不转码、不压缩图片字节
- 同一编号在重新生成或局部返工时使用新的 `task_id` 输出目录，天然隔离，不覆盖历史文件
- 某张图下载失败不阻塞其他图，记录失败项后续处理

下载约束：
- 仅下载 `status == "success"` 且 `image_url` 非空的图片
- 下载路径使用当前工作目录绝对路径下的 `picset_output/<task_id>/`，不写入系统目录或 skill 目录
- 脚本不存在或无法读取时，立即报告"本地 Skill 安装不完整"，不得创建替代脚本

### present_files 展示

展示时机：当前批次所有成功图片下载完成后。

调用方式：同一批次的成功图片共享一次 `present_files` 调用，`artifacts` 数组传入每张图的本地绝对路径（交付器返回的 `path`），`name` 用稳定编号（如 `M1`、`D2`）。

部分失败时：只展示成功下载的图片，失败项在对话中说明编号和原因。

展示约束：
- 必须使用 `present_files` 交付图片，不得用 Markdown 图片链接或对话内贴图替代
- 不在对话中重复输出 `image_url` 或本地文件路径
- 对话中只输出文字总结：成功数量、失败编号、实际扣费

### 部分失败

- 先将成功图片下载到本地并通过 `present_files` 展示
- 对话中说明失败编号和原因
- 仅将成功图走画布打开+校验+必要时兜底插入；失败项不推画布
- 不自动补建失败图片
- 支持用户按编号单张重试，重试后同样下载、`present_files` 展示，并走同一画布承接流程

### 画布自动承接

`present_files` 完成后、最终文字总结前执行（至少一张成功图时）：

1. 按 [Agent Canvas 共享手册](./agent-canvas-playbook.md)「宿主 conversation_id 解析」取得真实 ID；仍缺失则说明无法打开画布并跳过本步，不虚构。
2. 调用 `open_agent_canvas`（**`initial_images` 省略或 `[]`**），保存返回的 `agentCanvasSessionId`。
3. 调用 `get_agent_canvas_state`，读取 `imageIds` / `imageCount`。
4. 若本批成功稳定编号**已全部**出现在 `imageIds`：不再插入。
5. 若有缺失：对每张缺失图调用 `insert_agent_canvas_image`（`image.url`=服务端 `image_url`，`image.id`=稳定编号，`request_id`=**新** UUID v4）；可再 `get_agent_canvas_state` 确认。
6. 若尚未 `panelActive: true`，可再调用一次无图的 `open_agent_canvas`。

细则见 [Agent Canvas 共享手册](./agent-canvas-playbook.md)「交付后打开 + 校验 + 兜底插入」。

### 约束

- 不分析图片质量，不输出主观评价
- 不按完成顺序重排编号
- 图片本地下载和展示由 agent 侧 `picset_client.py deliver` + `present_files` 完成；画布承接是交付后的必做步骤，不替代 `present_files`
- 禁止用 `initial_images` 在打开时批量塞本批图；已在 `imageIds` 中的编号禁止再 `insert`
- 本地下载的图片持久化在 `picset_output/<task_id>/`，用户后续可凭编号或 task_id 找到文件

---

## 七、用户偏好管理

完整授权规则以 [共享积分确认规则](./credit-confirmation-playbook.md) 为准，本节保留电商原有路径与操作索引。此处 `__SKILL_DIR__` 仅指电商子 Skill 目录；单图及风格复刻也读取同一个电商偏好文件，不在各自目录另存授权。恢复确认后各能力统一恢复。

### 偏好文件

`__SKILL_DIR__/user_preferences.json`

### 用途

存储用户是否需要每次确认积分的偏好，避免重复询问。仅存储在本地，不上传任何服务端。

### 首次设置

- 首次报价后，若偏好文件不存在，在展示预估积分的同时追加询问："以后电商、单图和复刻都自动确认积分吗？（回复'不用确认'可启用，随时可恢复）"
- 用户回复"不用确认""以后不用问了"等明确意图时，设置 `{"confirm_credits": false}`，保留已有其他字段；本次报价已展示后直接继续生成
- 用户回复"需要确认"或未明确选择时，不创建偏好文件，保持每次确认

### 读取逻辑

- 每次报价后、进入上传登记前，读取偏好文件
- 若文件存在且 `confirm_credits` 为 `false`，展示积分后直接继续，不等待用户确认
- 若文件不存在、解析失败、不是 JSON 对象或 `confirm_credits` 不为布尔值 `false`，按原流程等待用户确认；字符串 `"false"` 不算授权

### 恢复确认

- 用户随时说"恢复积分确认""以后都要确认积分"等，将唯一偏好文件的 `confirm_credits` 改为 `true` 并保留其他字段，或删除仅含该偏好的文件，告知三项能力均已恢复；持久化失败时按共享规则阻止旧授权继续生效

### 安全边界

- 跳过的仅为积分确认停点，方案确认（停点一）始终保留
- 即使跳过确认，每次仍展示预估积分数额，保持透明
- 写入或删除偏好文件属于本地常规操作，不需要额外向用户确认
