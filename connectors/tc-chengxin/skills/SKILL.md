---
name: tc-chengxin
description: '同程旅行官方旅游查询 Skill。用于机票、火车票、酒店、景区、汽车票、度假产品、行程规划、综合交通等实时查询，并提供 PC 预订入口、手机打开入口和微信扫码二维码。'
description_zh: '同程程心自然语言查询机票酒店景点行程等旅行资源服务'
description_en: 'Natural-language travel search for Tongcheng Chengxin resources'
version: '1.0.0'
metadata:
  author: 同程网络科技股份有限公司
  homepage: https://www.ly.com
---

# 同程旅行 WorkBuddy Skill

本 Skill 通过同程旅行 CLI 连接器查询实时旅行资源。脚本会生成两类结果：

- 对话内 Markdown：手机端和文本端可直接阅读。
- 本地 HTML 文件：PC 端用 `present_files` 打开侧边栏预览，支持链接点击和二维码放大。

## 触发条件

当用户表达以下任一需求时，必须调用本 Skill：

| 意图 | 典型说法 | 脚本 |
| --- | --- | --- |
| 机票 | 北京到上海机票、明天飞广州、特价机票 | `scripts/flight-query.js` |
| 火车票 | 北京到上海高铁、苏州到南京火车票 | `scripts/train-query.js` |
| 酒店 | 上海外滩附近酒店、北京五星级酒店 | `scripts/hotel-query.js` |
| 景区/门票 | 苏州园林、杭州亲子景点、迪士尼门票 | `scripts/scenery-query.js` |
| 汽车票 | 苏州到南京大巴、长途汽车票 | `scripts/bus-query.js` |
| 度假/行程 | 三亚自由行、云南旅游团、北京三日游 | `scripts/travel-query.js` |
| 综合交通 | 北京到上海怎么走、去苏州有哪些交通方式 | `scripts/traffic-query.js` |

路由规则：

- 用户明确说机票、火车票、酒店、景区、汽车票、度假时，优先使用对应专用脚本。
- 用户说“规划行程/玩几天/三日游/自由行安排”时，使用一次 `travel-query.js` 获取交通、酒店、景点和行程规划，不要拆成多个脚本分别调用。
- 用户只问“怎么走/交通方式”且未指定交通工具时，使用 `traffic-query.js`。
- 参数不足时先让用户补齐关键参数，不要调用不匹配的脚本替代。

## 输入契约

执行脚本前必须先注入本机同程授权令牌和 WorkBuddy 展示契约：

macOS/Linux shell：

```bash
export CHENGXIN_WORKBUDDY_OUTPUT_DIR="$PWD/outputs"
export CHENGXIN_API_KEY="$(tc-chengxin token)"
export CHENGXIN_OUTPUT_GUARD=display_contract
```

Windows PowerShell：

```powershell
$env:CHENGXIN_WORKBUDDY_OUTPUT_DIR = Join-Path (Get-Location).Path "outputs"
$env:CHENGXIN_API_KEY = (tc-chengxin token)
$env:CHENGXIN_OUTPUT_GUARD = "display_contract"
```

令牌处理：

- `tc-chengxin token` 无输出或失败时，提示用户在 WorkBuddy「连应用」中重新连接「同程旅行」。
- 不要要求用户手动输入 API Key。

参数提取：

- `--departure`：出发城市或出发地。
- `--destination`：目的城市、目的地、酒店/景区所在城市。
- `--flight-number` / `--train-number`：用户给出明确航班号或车次号时使用。
- `--departure-station` / `--arrival-station`：用户给出精确火车站时使用。
- `--low-price`：用户表达特价、低价、便宜机票时使用。
- `--extra`：保留所有修饰性需求，包括日期、时间、人数、星级、酒店位置、亲子、早餐、直飞、高铁优先、价格偏好等。

重要规则：

- 不要丢弃用户修饰性需求；结构化参数以外的内容都放入 `--extra`。
- WorkBuddy 渠道不要额外传 `--channel webchat --surface webchat`；脚本会自动注入 `channel=workbuddy`、`surface=desktop`、`outputProfile=workbuddy_visual`、`renderMode=visual_json`。
- `CHENGXIN_WORKBUDDY_OUTPUT_DIR` 推荐设置为当前工作区的 `outputs` 目录，让 HTML 产物直接生成到 WorkBuddy 可展示的工作区内。
- Windows 必须使用原生盘符路径，例如 `D:\...\outputs`；不要把 Bash/MSYS 风格 `/d/...`、`\d\...` 或字面量 `$PWD/outputs` 作为输出目录。

## 执行流程

1. 判断意图并选择唯一脚本。
2. 设置 `CHENGXIN_WORKBUDDY_OUTPUT_DIR` 为当前工作区 `outputs` 目录；macOS/Linux 用 `$PWD/outputs`，Windows PowerShell 用 `Join-Path (Get-Location).Path "outputs"`。
3. 注入 `CHENGXIN_API_KEY` 和 `CHENGXIN_OUTPUT_GUARD=display_contract`。
4. 执行脚本，传入结构化参数和 `--extra`。
5. 只解析 `WORKBUDDY_VISUAL_JSON_START` 与 `WORKBUDDY_VISUAL_JSON_END` 之间的 JSON。
6. 将 JSON 中的 `markdown` 字段逐字原样作为最终回复正文输出；不要只输出 `summaryMarkdown`，也不要自行写“已完成”摘要替代 Markdown。
   - 如果 JSON 含 `responsePolicy.finalAnswerField=markdown`，必须遵守。
   - 如果 JSON 含 `finalAnswerInstruction`，按该字段执行；它优先于你自己的总结习惯。
   - 如果 JSON 含 `responsePolicy.mustDisplayInChat=true`，最终对话正文必须显示 `markdown` 字段，不能只展示 HTML 文件卡片。
   - 如果 JSON 含 `responsePolicy.presentFilesIsSupplementOnly=true`，`present_files` 只是补充展示，不是最终回答正文。
   - 如果 JSON 含 `responsePolicy.finalAnswerMustStartWith`，最终回复正文必须以该字符串开头。
   - 如果 JSON 含 `responsePolicy.requiredFinalAnswerSections`，最终回复必须包含这些章节/关键词。
   - 如果 JSON 含 `responsePolicy.requiredTransportMarkdownHeaders`，交通/机票/火车/汽车表格必须按对应业务保留表头顺序。
   - 不得根据 `markdown`、`summaryMarkdown`、HTML 或自己的理解重新生成表格。
   - 交通/机票/火车/汽车表格的 `预订` 列是强制列，并且必须在最后一列；缺失或改名都视为输出失败，必须重新输出脚本 `markdown` 原文。
   - 如果为了读取完整输出使用 `cat`、`sed`、`python` 等方式提取了 `markdown` 字段，提取结果只能作为最终回复原文，不得再压缩、重排或改写。
7. 检查 `htmlFilePath`：
   - 如果路径在当前工作区内，直接使用。
   - 如果路径在工作区外，复制到 `$PWD/outputs/` 后使用复制后的路径。
8. 用最终路径调用 `present_files` 展示该 HTML 文件。

示例：

macOS/Linux shell：

```bash
export CHENGXIN_WORKBUDDY_OUTPUT_DIR="$PWD/outputs"
export CHENGXIN_API_KEY="$(tc-chengxin token)"
export CHENGXIN_OUTPUT_GUARD=display_contract
node scripts/hotel-query.js --destination "上海" --extra "外滩附近 明天入住 五星级"
```

Windows PowerShell：

```powershell
$env:CHENGXIN_WORKBUDDY_OUTPUT_DIR = Join-Path (Get-Location).Path "outputs"
$env:CHENGXIN_API_KEY = (tc-chengxin token)
$env:CHENGXIN_OUTPUT_GUARD = "display_contract"
node scripts/hotel-query.js --destination "上海" --extra "外滩附近 明天入住 五星级"
```

脚本成功输出示例结构：

```json
{
  "type": "workbuddy_present_files",
  "version": "2.0",
  "summaryMarkdown": "...",
  "markdown": "...",
  "htmlFilePath": "$PWD/outputs/20260701-180000-上海外滩附近酒店推荐/上海外滩附近酒店推荐.html",
  "htmlFileName": "上海外滩附近酒店推荐.html",
  "presentFilesInstruction": "调用 present_files 展示文件：...",
  "stats": { "total": 8, "hasQr": true, "hasPcUrl": true },
  "fallbackReason": ""
}
```

## 输出契约

必须执行：

- 对用户直接输出 `markdown` 字段原文，保留所有标题、分组、表头、表格列、链接和客服支持。
- `summaryMarkdown` 仅用于兼容，不得替代 `markdown` 作为最终回复。
- `markdown` 顶部包含脚本生成的「推荐建议」或「行程安排建议」，这是基于接口结果、用户偏好和通用旅行经验生成的建议性回答，必须保留。
- 当用户询问“规划行程/玩几天/自由行/路线/攻略”时，脚本会输出 Day 1 / Day 2 / Day 3 形式的行程安排；必须原样输出，不要压缩成普通资源列表或一句总结。
- `markdown` 末尾包含「客服支持」段落，必须保留。
- 机票/火车/汽车 Markdown 表格必须保留脚本原始 `预订` 列；该列里的 PC 端预订、手机打开、二维码链接不得删除。
- 机票 Markdown 表格的表头必须保持脚本原文顺序：`序号 | 航班 | 出发到达 | 日期 | 时间 | 时长 | 价格 | 预订`。
- 火车 Markdown 表格的表头必须保持脚本原文顺序：`序号 | 车次 | 出发到达 | 日期 | 时间 | 历时 | 票价/席别 | 预订`。
- 汽车 Markdown 表格的表头必须保持脚本原文顺序：`序号 | 班次 | 出发到达 | 日期 | 时间 | 车程 | 票价 | 预订`。
- 如果 `htmlFilePath` 非空，调用 `present_files`：

```json
{
  "files": ["<htmlFilePath>"],
  "explanation": "同程旅行查询结果 HTML 页面"
}
```

产物路径处理：

- 优先让脚本直接输出到 `$PWD/outputs`。
- Windows 下优先让脚本直接输出到当前工作区原生 `outputs` 路径，例如 `D:\...\outputs`。
- 如果 `htmlFilePath` 不在当前工作区内，先复制到 `$PWD/outputs/<htmlFileName>`，再调用 `present_files`。
- 不要把工作区外的旧路径直接作为最终展示路径。

禁止执行：

- 不展示脚本原始 JSON。
- 不只输出一句完成摘要；最终回复必须包含脚本 `markdown` 中的分组表格、预订入口和客服支持。
- 不只展示 HTML 文件或只说“点击右侧 HTML 页面查看完整列表”。
- 不使用“已为你查到……点击右侧 HTML 页面……”这类摘要替代脚本 `markdown`。
- 不自行改写资源名称、价格、链接、排序和二维码。
- 不自行生成新的表格、亮点总结或二次推荐结论；不得把脚本 Markdown 表格重排成另一个表格。
- 不因为列宽、移动端显示或美观原因删除 `预订` 列。
- 不删除脚本 Markdown 中的 PC 链接、手机链接和二维码链接。
- 不删除 Markdown 末尾的同程旅行客服支持信息。

## 失败降级

| 场景 | 处理 |
| --- | --- |
| 未登录/令牌失效 | 提示用户在 WorkBuddy「连应用」中重新连接「同程旅行」 |
| 参数不足 | 只询问缺失的关键参数 |
| 无结果 | 输出脚本给出的无结果提示，并建议调整日期、城市、位置或偏好 |
| HTML 生成失败 | 输出 `markdown`，并说明 `fallbackReason` |
| 二维码缺失 | 保留 PC 预订和手机打开链接，不编造二维码 |
| 网关失败 | 输出脚本错误信息，不补充未返回的价格/余票/开放时间 |

## 验收标准

一次成功查询必须满足：

- Markdown 在对话中可完整阅读，手机端可用。
- Markdown 末尾包含同程旅行 7×24 小时客服支持信息。
- PC 端有中文命名 HTML 文件，例如 `上海外滩附近酒店推荐.html`。
- `present_files` 打开 HTML 后，PC 预订链接可点击。
- 有二维码时，HTML 支持悬浮查看和点击放大扫码。
- 不暴露原始 JSON，不丢失接口返回的资源条目。

## 参考文档

- `references/config.md`
- `references/workbuddy-output-contract.md`
- `references/workbuddy-routing.md`
- `references/workbuddy-errors.md`
- `references/workbuddy-acceptance.md`
