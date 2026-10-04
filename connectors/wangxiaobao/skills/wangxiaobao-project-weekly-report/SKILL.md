---
name: wangxiaobao-project-weekly-report
description: >
  地产项目营销周报生成器。多数据源聚合（旺小宝API + IMA知识库 + SQL Agent），
  自动拉取来访、成交、客户画像、顾问业绩等数据，生成8大模块结构化HTML周报，
  含柱状图、圆环图、交叉分析表、专家深度洞察，同时生成HTML和PDF两种格式交付。
  触发词：营销周报、项目周报、生成周报、weekly report、本周数据汇总、周度报告。
agent_created: true
---

# 地产项目营销周报生成器（优化版）

## 触发条件
"生成周报"、"营销周报"、"项目周报"、"weekly report"、"本周数据汇总"、"周度报告"

## ⚡ 性能优化（2026-05更新）

| 模式 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 完整（HTML+PDF） | ~10秒 | ~7秒 | **30%** |
| `--html-only`（仅HTML） | ~10秒 | **0.3秒** | **97%** |

**优化措施**：
1. 移除 `html2pdf.py` 中8秒强制等待（图表为静态SVG，无需JS渲染）
2. Chromium 启动参数优化（`--no-sandbox`, `--disable-gpu` 等）
3. 等待策略优化：`domcontentloaded` + 等待 `.card` 元素（最多2秒）
4. 新增 `--html-only` 模式：跳过PDF生成，0.3秒完成

## 输出
- **默认**：HTML + PDF 双格式（~7秒）
- **`--html-only`**：仅HTML（0.3秒），可用浏览器 Ctrl+P 打印为PDF
- 排版样式：深蓝渐变 header、卡片式布局、SVG图表（兼容打印）

通过 `preview_url` 预览 HTML + `deliver_attachments` 交付双文件。

## 执行流程（自动模式 · 推荐）

### 第1步：确认参数
从用户获取或自动推断：项目名、周日期范围。其他参数（tenant_id、project_id、KB_ID）从 `MEMORY.md` 获取。

### 第2步：拉取数据（prepare_data.py）
```bash
# 自动从以下来源拉取数据：
# 1. 旺小宝API（来访、客户、顾问）
# 2. IMA知识库（成交台账xlsx、盘客管理csv）
# 3. 本地JSON缓存（visit_lastweek_filtered.json等）
python3 prepare_data.py
```
输出：`weekly_report_data.json`（所有字段与 template.py 变量名完全匹配）

### 第3步：生成报告（generate_report.py）
```bash
# 默认：生成 HTML + PDF（~7秒）
python3 generate_report.py

# 极速模式：仅生成 HTML（0.3秒）
python3 generate_report.py --html-only
```

## 执行流程（手动模式 · 备用）

### 第1步：确认参数
同上。

### 第2步：拉取数据
同上（运行 `prepare_data.py`）。

### 第3步：修改 template.py（不推荐）
**已废弃**：当前版本通过 `generate_report.py` 自动覆盖变量，无需手动修改 `template.py` DATA区。

如果确需手动修改：
1. 将 `scripts/template.py` 复制到工作目录
2. 编辑 `template.py` 顶部 **DATA区** 的变量值
3. 运行：`python3 template.py`
4. 生成文件：`[项目名]_周报_[开始日期]-[结束日期].html` + `.pdf`

## 数据结构（weekly_report_data.json）

`prepare_data.py` 输出完整的 `weekly_report_data.json`，包含以下变量组：

| 变量组 | 内容 | 数据来源 |
|--------|------|----------|
| `project_name` | 项目全称 | 用户指定 |
| `brand_text` | header副标题 | 如"<项目名>项目 · 周度来访与成交深度分析" |
| `week_label` | 周标签 | 如"W20" |
| `date_start` / `date_end` | 周起始/结束日期 | 自动计算 |
| `data_date` | 数据截至日期 | 如"2026.05.18 23:30" |
| `week_days` | 本周7天来访数据 `[{"date":,"weekday":,"count":}]` | 旺小宝API |
| `last_week_days` | 上周7天来访数据 | 旺小宝API |
| `may_days` | 本月每日来访数据 | 旺小宝API |
| `consultants_this` | 顾问本周接待 `[{"name":,"count":,"pct":}]` | 旺小宝API |
| `first_visit` / `repeat_visit` | 首访/复访（基于visitCount字段） | 旺小宝API |
| `panke_done` / `panke_rate` | 盘客完成 | 旺小宝API |
| `intent_api` / `intent_panke` | 意向等级(双源) | 旺小宝API / 盘客CSV |
| `budgets` / `payments` / `downpay` | 预算/付款/首付 | 盘客CSV |
| `house_types` / `channels` / `resistances` / `purposes` | 户型/渠道/抗性/目的 | 盘客CSV |
| `focus_points` / `cycles` | 关注点/看房周期 | 盘客CSV |
| `deals_*` | 成交相关（total/amount/house_type/channel/cycle） | 成交台账xlsx |
| `visit_target` / `sales_target` | 月度目标 | 用户/配置 |
| `monthly_trend` / `monthly_trend_total` | 月度趋势 | 成交台账xlsx |
| `cross_cycle_intent` / `cross_purpose_intent` / `cross_channel_intent` | 交叉分析表 | 盘客CSV |
| `insight_xxx` | 8个模块的专家洞察文本 | AI根据数据撰写 |
| `suggestions` | 下周建议列表 | AI根据数据撰写 |
| `summary_text` | 总结文本 | AI根据数据撰写 |

## 专家洞察撰写要求

- **视角**：地产营销总监/操盘手视角
- **风格**：精炼有力、结论先行、数据支撑，80-150字/模块
- **禁止**：编造数据、过度乐观/悲观、堆砌专业术语
- **必须包含**：具体数字引用、可执行建议、风险预警

## 日期处理
- 使用 `datetime.weekday()` 计算，禁止硬编码星期
- 来访数据用 `visitTime` 字段做日期过滤
- 周报默认范围：上周一至上周日
- **首访/复访判断**：使用 `visitCount` 字段（=1首访，>1复访），不使用 `visitType` 字符串

## 使用方法

### AI 自动生成（推荐）
直接向 AI 说：**"生成 <项目名> 周报"**，AI 会自动：
1. 确认日期范围（或自动推断）
2. 运行 `prepare_data.py` 从旺小宝API + IMA知识库拉取最新数据
3. 根据数据生成专家洞察文本（`insight_xxx` 变量）
4. 运行 `generate_report.py` 渲染并输出 HTML + PDF
5. 预览 + 交付双文件

### 手动生成（备用）
1. 将 `scripts/template.py`、`scripts/generate_report.py`、`scripts/prepare_data.py` 复制到工作目录
2. 运行 `python3 prepare_data.py` 生成 `weekly_report_data.json`
3. 运行 `python3 generate_report.py` 生成 HTML + PDF
4. 用 `preview_url` 预览 HTML，或用 `deliver_attachments` 交付双文件

### 极速模式（--html-only）
```bash
python3 generate_report.py --html-only  # 0.3秒生成HTML，无PDF
```
适用场景：需要调整模板样式、预览效果、或不需要PDF时。

## PDF生成说明

`generate_report.py` 调用 `html2pdf_fast.py`（优化版）将HTML转为PDF：

1. **依赖**：`playwright` + Chromium（需预先安装：`pip install playwright && playwright install chromium`）
2. **优化**：移除8秒强制等待，Chromium启动参数优化，~7秒完成
3. **质量**：与HTML排版样式完全一致（A4横向，保留背景色和CSS样式）
4. **降级**：如PDF生成失败，脚本会继续运行并输出错误信息，不会中断HTML生成
5. **极速替代**：使用 `--html-only` 跳过PDF，用浏览器Ctrl+P打印（用户侧控制）

## 注意事项

- Logo文件：`logo_wangai.png`、`logo_wangxiaobao.png` 需与生成的HTML同目录
- 若 `generate_report.py` 报错，检查Python版本（需3.8+）和 `weekly_report_data.json` 是否存在
- 洞察文本支持HTML标签（如 `<strong>`、`<span class="tag">`）
- 数据解读每次需根据新数据重新撰写，禁止直接复制上期文本
- **首访/复访字段**：已修复为 `visitCount` 判断（之前错误使用 `visitType` 字符串）
- **交叉表数据**：`cross_cycle_intent`/`cross_purpose_intent`/`cross_channel_intent` 由 `prepare_data.py` 自动生成，无需手动填写

## 文件清单（scripts/目录）

| 文件 | 用途 |
|------|------|
| `template.py` | HTML模板+CSS+图表生成函数+生成器 |
| `generate_report.py` | 报告生成器（读取JSON，覆盖变量，调用PDF） |
| `prepare_data.py` | 数据准备脚本（拉取API，解析xlsx/csv，输出JSON） |
| `html2pdf_fast.py` | 优化版HTML→PDF转换器（Playwright，无8秒等待） |
| `logo_wangai.png` | WangAI Logo（Header左侧） |
| `logo_wangxiaobao.png` | 旺小宝Logo（备用） |
