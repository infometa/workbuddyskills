---
name: weight-management-html
display_name: 体重管理报告生成
category: writing
version: 1.0.1
author: 微脉技术有限公司
description: "Use when the adult weight-management MCP needs to be installed/set up in WorkBuddy (connector) or its result must be rendered as a standalone Chinese HTML plan."
---

# Weight Management HTML

将体重管理 MCP 的结构化结果渲染成产品要求的独立 HTML。MCP 是事实来源，客户端 Skill 负责呈现，不要复用系统已有体重管理智能体或自行改写安全边界。

## MCP 服务端连接

调用工具前先检查 `generate_weight_management_plan` 是否已经可用：

- 已可用时直接调用，不重复安装或覆盖客户端配置。
- MCP 必须调用用户部署的服务端接口，不得运行本地脚本模拟工具、绕过 MCP 协议或直接复刻服务端生成逻辑。
- 服务端地址：`https://ichoice.myweimai.com/weimai-gpt/mcp`（用户提供的公网 Streamable HTTP endpoint）。若用户明确要求本地联调，再以启动日志/`API_PORT` 为准使用本地地址。
- 客户端尚未配置 MCP 地址时，配置为以 `/mcp` 结尾的 Streamable HTTP URL；公网地址只能使用用户提供的真实域名，不得猜测。
- 项目中的 `mcp` Python 依赖只属于服务端部署环境；即使本地存在依赖，也不能把本地脚本作为远程服务不可用时的降级实现。
- 配置后先做 MCP `initialize`、`tools/list`，确认只发现 `generate_weight_management_plan`；再用空的 `user_input` 做无模型 smoke test，确认返回 `need_more_info`。

### 在 WorkBuddy 中安装/配置 MCP 工具

当当前会话工具列表中看不到 `generate_weight_management_plan` 时，引导 WorkBuddy 安装 MCP 连接器（不要跳过；也不要用 curl 或本地脚本替代工具调用）：

1. 读取 `~/.workbuddy/mcp.json`（注意是 `mcp.json`，**不是** `~/.workbuddy/.mcp.json`）。
2. 把以下条目**合并**进 `mcpServers`，保留已有服务器、不得覆盖其他配置：

   ```json
   {
     "mcpServers": {
       "generate_weight_management_plan": {
         "type": "mcp",
         "transport": "streamable_http",
         "url": "https://ichoice.myweimai.com/weimai-gpt/mcp",
         "disabled": false
       }
     }
   }
   ```

   - 默认使用 `https://ichoice.myweimai.com/weimai-gpt/mcp`。
   - 公网地址只能使用用户提供的真实 HTTPS 域名，不得猜测或使用示例地址。
3. 写回后**必须告知用户**：新 MCP 不会自动激活，请用户在连接器管理页右上角「自定义连接器」入口对该服务器点击「信任」启用。
4. 用户确认信任后，重新检查 `generate_weight_management_plan` 是否出现在工具列表；可用后再按下方 Workflow 调用。

## 本地图片转在线 URL（图片床）

用户上传本地餐食图片时，**必须先**调用图片床上传接口把本地路径转成在线 URL，再把 URL 传给 MCP 的 `image_urls`：

1. 上传命令（`<本地图片路径>` 替换为用户提供的本地图片绝对路径）：

   ```bash
   curl --request POST \
     --url https://caregpt-api.myweimai.info/image_bed/upload \
     --header 'Content-Type: multipart/form-data' \
     --header 'x-weimai-business-type: hongfangzi' \
     --header 'x-weimai-origin: Weimai-H5' \
     --form 'file=@<本地图片路径>'
   ```

2. 校验返回 JSON：仅当 `code == 0` 视为上传成功，取 `data.image_url` 作为该图片的在线地址（HTTPS）。
3. 失败处理：`code` 非 0、网络错误或超时时，向用户原样展示 `msg`/错误信息，可在不改动输入的前提下重试一次；不得把本地路径、相对路径或猜测的 URL 传给 MCP。
4. 只上传用户明确作为餐食照片提供的本地图片文件，不要上传其他文件或批量扫描目录。
5. 上传得到的 `image_url` 仅用于本次 MCP 调用，不要持久化保存或复用到其他会话。

## Workflow

1. 调用已配置的 Streamable HTTP MCP Server 的 `generate_weight_management_plan` 工具。
   - 必传 `user_input`：保留用户原始请求；用户补充资料时，把原始请求和补充内容一起发送。
   - 可选 `image_urls`：只传 HTTPS 餐食照片 URL 列表。用户提供在线 URL 时直接使用；提供本地图片时，必须先按「本地图片转在线 URL」上传，使用返回的 `data.image_url`，不要把本地路径直接传给 MCP。不要下载后持久化，也不要把照片当作非餐食内容猜测。
2. 若客户端支持 MCP progress notification，实时展示消息中的逐段方案正文；最终以工具返回的完整 `structuredContent` 为准。
3. 按状态处理：
   - `ready`：把 `data` 保存为临时 JSON，运行 `scripts/render_plan.py --input <json> --output <html>`。
   - `need_more_info` / `clarify`：原样呈现 `questions`，向用户补问；不补默认值，不生成完成版 HTML。收到补充后重新调用 MCP。
   - `refused`：原样呈现 `safe_message` 和 `next_step`；不得绕过拒绝或自行提供减重方案。
   - `error`：呈现稳定错误文案；必要时在不改变输入的前提下重试一次。
4. 渲染成功后检查 HTML 无 `{{...}}` 未替换占位符、包含 `<!doctype html>`、`<style>`、`<script>` 和 13 个产品章节，并确认体重记录器区域含 `id="historyBody"` 历史表格与「清空全部记录」按钮、各章节「本次个性化建议」中的表格已渲染为 `<table>`；完成后用 `present_files` 打开绝对路径预览。

## Rendering rules

- 必须使用 [assets/template.html](assets/template.html) 作为视觉基线：保留响应式 CSS、指标卡片、三阶段内容、每周清单、体重记录器、本地 `localStorage` 和安全边界。
- `scripts/render_plan.py` 只把 `ready.data` 的 profile、metrics、timeline、phases、sections、checklist、weekly_review、safety_boundary 和可选 `meal_analysis` 注入模板；模型正文按章节作为“本次个性化建议”追加，不能覆盖程序计算的 BMI、BMR、热量区间和周期。
- **数值占位符强制校验（防 script 注入与除零）**：render_plan.py 对所有数值占位符（体重、BMI、BMR、热量区间等）执行严格数值校验，非数值/非有限数直接抛 `RenderError` 拒绝渲染，不做 HTML 转义降级（HTML 转义对 `<script>` 上下文无效）；`planned_loss_kg`、`current_weight_kg` 必须为大于 0 的有限数值（进度条 JS 计算依赖），`{{CURRENT}}`/`{{LOSS}}` 以无千分位纯数值字面量注入，模板侧对 `plannedLoss <= 0` 另有兜底。渲染报错时原样向用户展示错误并按 MCP 状态处理规则重试或重新调用，不要手工改写 HTML 绕过校验。
- **体重记录器（`weight_tracker`）是模板内置的交互式组件，不注入模型示例表格**：render_plan.py 对 `key == "weight_tracker"` 的章节跳过“本次个性化建议”注入；该区域自带日期/体重输入、「保存本次记录」按钮（保存后立即刷新历史列表）、进度条、历史记录表格（日期/体重/较上一条/删除）、最近 5 条平均统计和「清空全部记录」按钮，数据只存浏览器 `localStorage`。
- **模型正文的 Markdown 渲染器（`_render_markdown_fragment`）支持**：`|` 开头的表格（含 `|---|` 对齐行，渲染为 `<table>`，自动包 `.table-wrap` 以支持横向滚动）、`- ` 列表、`###`/`##`/`#` 标题、`**加粗**` 与 `` `行内代码` ``；正文必须按安全 HTML 转义后再放入页面，不要直接执行或插入模型生成的 HTML/JavaScript。
- 有餐食照片时保留热量范围、不确定的油/酱汁/糖/坚果/乳制品/分餐因素和低摩擦调整；不要写补偿性断食或惩罚性运动。
- 页面明确标注这是健康教育建议，不是诊断、处方或医疗承诺；急症、诊断、用药变化和需要医生监督的情况交给合格专业人员。
- 页面中的打卡和体重记录只使用浏览器本地 `localStorage`，不要上传或写回 MCP Server。

## Supporting resources

- [assets/template.html](assets/template.html)：产品 HTML/CSS/交互基线；只在渲染或视觉检查需要时读取。
- [scripts/render_plan.py](scripts/render_plan.py)：确定性 JSON→HTML 渲染和结构校验；优先运行脚本，不要手工重写模板。
- [references/mcp_setup.md](references/mcp_setup.md)：仅在服务端 MCP 未配置或需要联调时阅读。
