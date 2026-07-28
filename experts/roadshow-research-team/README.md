# Roadshow Research Team

由 1 位研究主编统筹 10 位专业分析师，为单一上市/未上市公司自动生成近 3 年全维度资本市场路演研究报告（.docx）。

## 类型

Team 型（多角色协作团队）

## 功能

围绕「资本市场路演」这一主题，按 4 阶段 SOP（Phase 0 标的与时间范围确认 → Phase 1 材料解析 → Phase 1b 六位分析师并行研究 → Phase 2 事件关联 → Phase 3 报告合成）产出结构化研究报告，覆盖 8 大维度：

1. 公司识别与业务概况
2. 所属行业与竞争格局
3. 财务三表分析（近 3 年）
4. 路演/投资者调研活动时间线
5. 卖方研报评级与观点梳理
6. 资本运作事件（增发/回购/并购/股权激励等）
7. 股价走势与事件关联分析
8. 投资亮点与风险提示

数据源按标的市场自动路由：**A 股优先 `a-stock-data`，港美股用 `westock-data`，`Wind` 作为权威补充**；仅采集公开数据，报告附免责声明（⚠️ 以上内容由 AI 基于公开信息整理生成，仅供参考，不构成任何投资建议或个股推荐）。支持单维度直调（如只问股价）以节省成本，也支持基于用户上传材料或模板填充生成。

## 使用示例

- 帮我做一份贵州茅台近三年的资本市场路演研究报告
- 分析招商银行（A+H）过去三年的投资者调研和研报评级情况
- 只看一下宁德时代最近一年的股价走势和重大事件关联

## 头像

头像已自动生成在 `avatars/` 目录下。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB

## 安装

### 安装方式

本专家包由 expert-publisher 统一上架，无需手动放置目录。

### 数据依赖

`a-stock-data` skill 需要以下 Python 依赖：

```bash
pip install mootdx requests pandas stockstats
```

另需配置环境变量以启用 iwencai 接口：

```bash
export IWENCAI_API_KEY="<your_key>"
export IWENCAI_BASE_URL="<your_url>"  # 可选
```

### Skill 依赖

本专家包的 skill 依赖分三类：**① 已随包打包**、**② 平台内置**（WorkBuddy 自带，无需安装）、**③ 可选增强**（缺失时按主理人「三级降级 SOP」自动降级，不影响核心交付）。

| Skill | 用途 | 类型 | 缺失时的降级行为 |
|-------|------|------|------------------|
| `a-stock-data` | A 股行情/财报/公告/资金面 | ① 已打包 | — |
| `roadshow-research-report` | Word 研究报告生成 | ① 已打包 | — |
| `westock-data` | 港美股数据 | ② 平台内置 | — |
| `docx` / `xlsx` / `pdf` / `pptx` | 文档/表格/PDF 生成与解析 | ② 平台内置 | — |
| `summarize` | 长文/材料摘要 | ② 平台内置 | — |
| `wind-find-finance-skill` / `wind-mcp-skill` | Wind 权威数据补充 | ③ 可选增强 | 缺失则回退到 `a-stock-data` / `westock-data`，并标注实际来源 |
| `openai-whisper` / `openai-whisper-api` | 录音/视频转录 | ③ 可选增强 | 缺失则跳过音视频材料解析，其余分析不受影响 |
| `tencent-meeting-skill` | 腾讯会议录制导入 | ③ 可选增强 | 缺失则跳过会议录制导入 |
| `nano-pdf` | PDF 精细解析 | ③ 可选增强 | 缺失则由 `pdf` 兜底 |

> **硬依赖** = `a-stock-data` + `roadshow-research-report`（已随包打包，开箱即用）；平台内置项 WorkBuddy 自带；可选增强项缺失均不阻断核心报告产出。
>
> 本专家包由 expert-publisher 统一上架，无需手动运行注册脚本。

## 打包分享

```bash
zip -r roadshow-research-team.zip roadshow-research-team/
```
