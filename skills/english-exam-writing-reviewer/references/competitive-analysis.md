# 差异化说明与竞品对比

> 按需加载：当用户询问"这个 Skill 比 XX 软件好在哪"或需要说明 Skill 定位时读取。

## 相对主流商业竞品

> 以 `docs/requirements/AI作文批改/参考资料/competitive-analysis.md` 的 6 大类竞品调研为基础；
> 此处列出最常被学生使用的 3 个对标产品：**网易有道作文批改**（C 端免费最广）、**批改网 pigai**（学校 B 端覆盖最广）、**通用 LLM**（ChatGPT/Claude 裸提示）。

| 维度 | 网易有道作文批改 | 批改网 pigai | 通用 LLM（ChatGPT / Claude）| **本 Skill** |
|------|-----------------|--------------|-----------------------------|-------------|
| CET4 / CET6 支持 | ✅ | ✅ | ⚠️ 未校准 | ✅ 5 档完整 + 档内 ±1 |
| 考研英一 A+B / 英二 A+B | ✅（技术口径，细分档不公开）| ⚠️ 有但偏弱 | ⚠️ 未校准 | ✅ 4 节全覆盖 + 0.5 档内调节 |
| 评分法是否对齐官方 holistic | ⚠️ 自造数十维度加权 | ⚠️ 语料库距离算法 | ❌ 易给 Band 5.5 作文打 7.0 | ✅ 官方描述符**原文逐字**引用 |
| 档次判定可追溯 | ❌ 黑盒分数 | ❌ 黑盒分数 | ❌ 即兴解释 | ✅ `rationale_trace` 每步 claim + evidence + rubric_ref |
| 考研 A 节 Directions 原句照搬检测 | ❌ | ❌ | ❌ | ✅ ≥ 8 词 n-gram 连续检测 |
| 题型子类差异化（letter 10 类 / chart 7 类 / cartoon 三段论）| ⚠️ 按考试粒度 | ❌ | ❌ | ✅ 精细化枚举 + 专属 rubric |
| 词汇升档建议分级 | ⚠️ 好词好句推荐 | ⚠️ 按句点评 | ⚠️ 不分级 | ✅ Low/Mid/High/Academic 4 层 × `exam_level` 最低达标 tier |
| 防幻觉（低频/越界题型处理）| ❌ 强行打分 | ❌ | ❌ | ✅ `calibration_status` 免责 + 越界 `raw_score=null` |
| 校准集公开（可验证）| ❌ 闭源 | ❌ 闭源语料库 | ❌ | ✅ 55 篇锚点 + 15 金标 + `calibrate.py` 回归脚本全开源 |
| 反馈语言 | 中英混合 | 中文为主 | 英文为主 | ✅ 全中文 + 术语双语 |
| 输出形态 | Web 端 + APP | Web 端 | 聊天文本 | ✅ 结构化 JSON + 中文 HTML（含 SVG 雷达图/进度条）|
| 批改完成后交互 | 一次性出页面 | 一次性出页面 | 需用户追问 | ✅ 主动询问是否生成 HTML 报告 |
| 部署形态 / 定价 | APP 免费 / API 0.08–0.10 元/次 | SaaS 订阅 / 学校集采 | 订阅 $20/mo+ | ✅ Agent Skill（Anthropic 规范，Cursor / Claude Desktop / Knot 等兼容宿主均可直接加载；零摩擦 / 开源可验证 / 离线可跑）|

## 本 Skill 的核心护城河

1. **蓝海切入 CET + 考研**：D 类 AI 新秀几乎 100% 聚焦雅思托福；国内主流考试的**可追溯评分**是真空
2. **可追溯 + 可审计**：每一分都能回到"官方描述符原文 + 作文证据句 + rubric 文件路径"，对齐 2026 Nature Scientific Reports 提出的 AI 评分一致性痛点
3. **防幻觉**：通用 LLM 对 Band 5.5 作文常给 7.0 虚高分（English AIdol 实测数据）；本 Skill 用 55 篇校准集 + 低频防御分支 + `calibration_status` 机制杜绝
4. **零摩擦交付**：遵循 Anthropic Agent Skills 规范，Cursor / Claude Desktop / Knot 等兼容宿主都能直接加载；对已使用 AI 助手的高校学生无需离开备考上下文，且所有规则/校准集/脚本全部开源可改

## 相对 Treasoni/kaoyan-english-writing

- kaoyan-english-writing 是**词汇输出训练**（替换升级 / 汉译英 / 词义辨析）
- 本 Skill 是**作文批改**——引用 kaoyan 的分级词汇库作为 Step 6 升档建议的素材来源
- 两个 Skill **互补不冲突**：用户可同时装，考前用 kaoyan 训练，考后用本 Skill 批改
