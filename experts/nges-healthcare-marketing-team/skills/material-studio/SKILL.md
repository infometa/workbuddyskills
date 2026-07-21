---
name: material-studio
description: Render a pharma sales rep's marketing material into a self-contained mobile-portrait HTML page (digital business card + content) with a one-click export-as-long-image button. Use when generating festival greetings, industry news, latest research, or product/disease education materials to forward to a doctor's WeChat. Reads the rep profile from ~/.workbuddy/med-rep-profile.json and a content JSON.
agent_created: true
---

# Material Studio — 医药代表物料渲染 Skill

把"代表名片信息 + 一份内容"渲染成一个**自包含的手机竖版 HTML 单页**，页面内置「一键导出长图」按钮。无后端依赖，浏览器打开即用。

## 文件结构
- `templates/material_template.html` — 简报版式模板（news/research/education 用：名片头 + 简报刊头 + 分板块内容 + 导出按钮）
- `templates/greeting_template.html` — **节日贺卡模板（type=greeting 专用）**：节日氛围主视觉（月夜/红金等按节日配色）+ 祝福语 + 精简名片条 + 导出按钮
- `scripts/render_material.py` — 渲染脚本：读 profile + content JSON → 图片转 base64 → 输出 HTML；**type=greeting 自动走贺卡模板并按节日匹配氛围配色**（中秋月夜蓝金/春节国庆红金/端午青绿/医师节品牌蓝等）
- `references/content-examples.md` — 四种物料类型的 content.json 范例
- `references/source-whitelist.md` — **内容来源范围与合规口径（已审核，取材前必读）**

## 取材边界（强制）
生成 news / research / education 内容前，**必须先读 `references/source-whitelist.md`**，只在批准来源内取材。research/education 白名单制；预印本/厂商内部数据/自媒体禁用；第三方咨询不具名；研究类来源（期刊/会议+年份）必标。节日问候不涉及外部来源。

## 使用流程

### 1. 确保代表名片信息已存在
路径：`~/.workbuddy/med-rep-profile.json`。不存在则先向代表索要并创建，字段：
```json
{
  "name": "李慧",
  "company": "XX医药集团",
  "title": "医药经理",
  "filingNo": "京械备20260408号",
  "phone": "151-011-12345",
  "email": "lihui@example.com",
  "qrcodePath": "/绝对路径/wechat_qr.png",
  "avatarPath": "",
  "brandColor": "#2668EB"
}
```
> `qrcodePath` / `avatarPath` 为本地图片绝对路径；脚本会自动转成 base64 内嵌，导出长图不丢图。`avatarPath` 留空则用姓名首字渲染圆形头像。

### 2. 写内容 JSON（简报版式）
根据物料类型构造 `content.json`（四种类型完整范例见 `references/content-examples.md`）。字段：
- `type`：`card` | `greeting` | `news` | `research` | `education`
  - **`card` 电子名片**：只渲染代表本人名片（无内容板块），content 仅需 `{"type":"card"}`，信息全取自 profile。**一次生成两张**：竖版（`card_template.html` 独立精致卡，文件名 `_竖版`）+ 横版（`card_h_template.html` 简报名片头样式，文件名 `_横版`），供代表按场景挑用、单独导出。
- `column`：刊头栏目名（缺省按类型默认）
- `issue`：期号（可选，如 `第 12 期`）
- `headline`：大标题
- `gen_date`：**生成日期 `YYYY-MM-DD`，体现新鲜度；缺省自动取今天**
- `fresh_tag`：新鲜度标签（缺省按类型取，如 `报告研读`/`热点速递`），与 gen_date 一起显示在刊头徽标
- `recipient`：发送对象 `{dept, name}`（可选），刊头显示"致：肿瘤科 张三大夫"，内容应据此定向
- `lead`：开场导语（可选，代表口吻，勿用"编者按"）
- `sections[]`：板块数组，每个 `{name, items[]}`；`item` = `{title, rows[]?, text?, src?}`，`row` = `{lbl, val}`（结构化多行，如 研究/发现/临床意义）
- `summary`：本期小结（可选）
- `greeting`：（仅 type=greeting）`{festival, lines[]}`
- `occasion`：（仅 type=greeting）设 `"birthday"` 触发**生日贺卡**子类型（暖色玫瑰粉调）；festival 含"生日"亦自动识别。注：贺卡顶部不放具体图标（月亮/蛋糕已移除），仅渐变背景+光晕氛围
> 追求"简报级"信息密度：开场导语 → 分板块 → 本期小结，条目用 rows 多行展开并**带具体数据**（PFS/OS/HR/ORR/P值/样本量）。research 类每条 item 的 `src` 必填。避免给医生复述其本人领衔的研究。

### 3. 渲染
```bash
python3 scripts/render_material.py \
  --content /tmp/content.json \
  --out "物料_最新研究_20260628.html"
```
> `--profile` 默认 `~/.workbuddy/med-rep-profile.json`，一般无需指定。输出 HTML 写到 `--out` 指定路径（建议当前工作目录）。

### 4. 交付
用 `present_files` 展示输出的 HTML。告诉代表：浏览器打开 → 点右下角「📥 导出长图」→ 下载竖版长图 → 转发给医生。

## 合规要点（渲染前由 Agent 把关）
- 内容已过合规自检后才渲染（不夸大、不超适应症、研究标来源、学术陈述）。
- 模板底部固定声明"仅供医疗卫生专业人士参考"，备案号自动出现在底部。

## 注意
- **html2canvas 已离线内联**：模板用 `{{HTML2CANVAS_INLINE}}` 占位，脚本渲染时把 `templates/html2canvas.min.js` 源码内联进 HTML。产出的 HTML **完全自包含、零外部依赖**，断网/微信内置浏览器/内网都能正常导出长图，无需部署。
- **手机端导出存相册**：导出按钮在手机上不走 `<a download>`（手机不支持），而是弹出全屏浮层显示生成的图片并提示"长按保存到相册"；桌面端仍自动下载 PNG。靠 UA 判断分流。
- **交付方式**：可直接把这个单 HTML 文件发给代表（微信/浏览器打开即用），无需任何服务器或公网链接。
- 主色取 profile 的 `brandColor`，浅色底色由脚本自动派生。

## 合图自动切图（Agent 工作流）

当代表上传的图片是**合并了头像和二维码**的合图（如企业微信名片截图）时，Agent 按以下工作流处理，**自动切出头像和二维码并更新 profile**。

### 工作流

1. **视觉分析**：用 Agent 视觉能力分析图片，识别头像区和二维码区。
2. **输出归一化坐标**（0.0~1.0），格式 `x1,y1,x2,y2`（左上→右下），例如：
   - 头像区：`0.05,0.05,0.25,0.25`
   - 二维码区：`0.70,0.60,0.95,0.95`
3. **裁剪保存**（二选一）：
   - **方式 A（推荐）**：调用 `scripts/crop_card_image.py`：
     ```bash
     python3 scripts/crop_card_image.py <图片路径> \
       --avatar 0.05,0.05,0.25,0.25 \
       --qr 0.70,0.60,0.95,0.95 \
       --out-dir ~/.workbuddy/cropped
     ```
   - **方式 B**：Agent 直接用 Python PIL 裁剪（当前 turn 内完成）。
4. **更新 profile**：将 `avatarPath` 和 `qrcodePath` 指向裁剪后的文件，写回 `~/.workbuddy/med-rep-profile.json`。

### 坐标说明

| 区域 | x1（左） | y1（上） | x2（右） | y2（下） |
|------|----------|----------|----------|----------|
| 头像（通常在左上方） | ~0.05 | ~0.05 | ~0.25 | ~0.25 |
| 二维码（通常在右下方） | ~0.70 | ~0.60 | ~0.95 | ~0.95 |

> 实际坐标由 Agent 视觉分析确定，上表仅为典型参考。企业微信名片截图一般头像在左、二维码在右。

### 提示

- 若代表**分别上传**了头像图和二维码图，无需裁剪，直接更新 profile 对应字段。
- 裁剪后头像建议为正方形，二维码为正方形或略高长方形。
- `crop_card_image.py` 输出 JSON 到 stdout：`{"avatar": "...", "qrcode": "..."}`。
- 每次代表重新上传图片时，重复此工作流。

## 医生画像系统

Agent 维护一个医生画像库，记住每位医生的信息，实现"越用越聪明"。

### 存储
- 路径：`~/.workbuddy/med-rep-doctors.json`
- 管理脚本：`scripts/doctor_profile.py`

### 命令

```bash
# 添加/更新医生
python3 scripts/doctor_profile.py add --name "YY" --dept "肿瘤科" \
  --hospital "上海市胸科医院" --field "非小细胞肺癌,EGFR靶向,免疫治疗" \
  --level "kol" --birthday "1963-05-20"

# 查询医生画像
python3 scripts/doctor_profile.py get --name "YY"

# 列出所有医生
python3 scripts/doctor_profile.py list

# 记录一次触达（生成物料后自动调用）
python3 scripts/doctor_profile.py touch --name "YY" --type "research" --topic "ASCO 2026 NSCLC研究"

# 触达建议（哪些医生该联系了）
python3 scripts/doctor_profile.py suggest

# 7天内生日提醒
python3 scripts/doctor_profile.py birthday-check
```

### Agent 工作流集成

1. **首次提及医生时**：查询画像库，存在则自动填充科室/领域/历史；不存在则在物料生成后自动 `add`。
2. **生成物料后**：自动 `touch` 记录本次触达类型和主题。
3. **每次会话开始时**（可选）：运行 `suggest` 和 `birthday-check`，主动告知代表。
4. **内容定向**：基于 `fields` 字段自动添加联网检索关键词。
5. **防撞车**：基于 `lastTopics` 检查是否短期内发过类似内容。

### 医生 level 与语气映射

| level | 含义 | 语气建议 |
|-------|------|----------|
| `kol` | 学科带头人/KOL | 学术平视，呈现信息增量，不啰嗦背景 |
| `director` | 科主任/副主任 | 专业简洁，可点到临床意义 |
| `attending` | 主治医师 | 可稍多展开背景和解释 |
| `community` | 社区/基层医生 | 偏实操性，贴近指南落地和用药建议 |

## 物料资产库

每份生成的物料自动归档索引，支持回溯、复用、去重。

### 存储
- 路径：`~/.workbuddy/med-rep-materials-index.json`
- 管理脚本：`scripts/materials_index.py`

### 命令

```bash
# 索引新物料（生成后自动调用）
python3 scripts/materials_index.py add --type "research" --recipient "YY教授" \
  --dept "肿瘤科" --headline "ASCO 2026 NSCLC研究" \
  --topics "NSCLC,EGFR,ADC" --filepath "/path/to/file.html"

# 查询某医生的历史物料
python3 scripts/materials_index.py query --recipient "YY"

# 列出最近物料
python3 scripts/materials_index.py list --limit 20

# 检查是否重复（14天内同类型同主题）
python3 scripts/materials_index.py check-dup --recipient "YY" --type "research" --topic "EGFR"
```

### Agent 工作流集成

1. **生成物料后**：自动 `add` 索引。
2. **生成前**：`check-dup` 检查是否短期重复，重复则提醒代表并建议换角度。
3. **复用场景**："把上次给陆教授的研究更新一下" → `query` 找到旧文件 → 更新内容 → 重新渲染。
4. **批量生成**："帮我把这条热点分别发给 3 位医生" → 循环生成个性化版本并逐一索引。

## 内容个性化引擎

Agent 根据医生画像自动调整内容策略和语气。

### 规则

1. **领域定向**：基于画像 `fields`，联网检索时自动叠加关键词限定（如"EGFR耐药""MET扩增"）。
2. **语气匹配**：按 `level` 字段选择语气（见上方映射表）。
3. **历史去重**：读取画像 `lastTopics[]` + 资产库 `check-dup`，避免重复内容。
4. **PI规避**：若医生是某研究的 PI/通讯作者，不详细复述其本人研究。
5. **关联推荐**：基于上次物料主题，建议本次跟进方向（如上次发 EGFR 靶向，本次建议发耐药后方案）。

## 多轮迭代机制

支持代表对已生成物料进行快速微调，不必从头重做。

### 支持的微调指令

| 代表说 | Agent 动作 |
|--------|-----------|
| "换第二条研究" | 只替换 sections[x].items[1]，重新渲染 |
| "语气再正式一点" | 调整 lead + 各 item.rows 的措辞 |
| "加个数据/加条研究" | 在对应 section 追加 item |
| "删掉第三板块" | 移除 sections[2]，重新渲染 |
| "出个简版" | 每板块只保留 1 条核心 item |
| "出个朋友圈卡片" | 提取 headline + 1 句 summary，生成正方形卡片 |

### 实现方式

- Agent 保存上一份 content.json（在对话上下文中）
- 微调时只修改对应字段，调用 `render_material.py` 重新渲染
- 不需要重新联网（除非代表要求"换一条研究"）

## 模板沉淀与复用

每次生成物料后自动将 content.json 保存为可复用模板。

### 模板存储
- **路径**：`~/.workbuddy/med-rep-templates/`
- **文件命名**：`{type}_{场景关键词}.json`（如 `greeting_建党节.json`、`research_NSCLC.json`）
- **内容**：完整 content.json，但 `recipient` 留空

### 复用命令
```bash
# 列出所有模板
ls ~/.workbuddy/med-rep-templates/

# 复用模板（Agent 加载模板 → 替换 recipient → 渲染）
python3 scripts/render_material.py --content /tmp/reused_content.json --out "物料_XX.html"
```

### 触发场景
- "再做一张建党节贺卡" → 加载 `greeting_建党节.json`，替换 recipient 后直接渲染
- "用上次的模板" → 列出匹配模板，复用
- "看看我有哪些模板" → 列出已有模板

## 触达时机建议

Agent 可主动建议代表何时、给谁发什么。

### 触发场景

1. **代表说"帮我看看该给谁发了"** → 运行 `doctor_profile.py suggest`
2. **代表说"最近有什么可以发的"** → 结合时事（大会/政策）+ 画像中的 fields 推荐内容方向
3. **生日临近** → 运行 `birthday-check`，主动提示
4. **超过 14 天未触达** → 在 suggest 结果中标记

### 节奏管理原则

- 每位医生建议每月 2-3 次触达（含节日问候）
- 同一类型连续发不超过 2 次（如连续 2 次都是 research，建议下次换 news 或 greeting）
- KOL 频率可适当降低（月 1-2 次），关系维护型医生可更频繁

## 视觉增强

### 品牌模板配色

除默认腾讯健康蓝外，profile 中 `brandColor` 可设为药企品牌色，脚本自动派生浅色系：

| 药企 | 建议 brandColor |
|------|----------------|
| 阿斯利康 | `#830051`（紫红） |
| 辉瑞 | `#0093D0`（辉瑞蓝） |
| 恒瑞 | `#E31937`（恒瑞红） |
| 默沙东 | `#00857C`（绿松石） |
| 罗氏 | `#0066CC`（罗氏蓝） |
| 诺华 | `#0460A9`（诺华蓝） |

### 朋友圈卡片（规划中）

正方形 1:1 比例的单条摘要卡，含 headline + 1 句核心结论 + 名片精简条。适合朋友圈分享场景。

### 贺卡 CSS 动效（规划中）

节日贺卡可选开启轻量动画（飘落雪花/升起光点），通过 `@media (prefers-reduced-motion)` 尊重用户偏好。
