# 贴图头条

面向报纸编辑、记者和融媒体运营人员的 Agent 型专家：把整版报纸快速转成适合手机信息流传播、保留正式媒体气质的竖版头图。

## 版本策略（老杜指定）

日期版：`YY.M.D`，按交付日滚动。本次交付 **26.8.31**；原 1.x 序列终止于 1.2.0。`plugin.json`、本 README、marketplace 注册信息三处版本号保持一致。

## 26.8.31 Changelog

- **content-state.v2 契约**：新增 `source_manifest`（SHA-256 溯源链）、`layout_analysis`（bbox+置信度，双复跑稳定校验）、`items[]`（加权多条目+四维评分）、`editorial_log`（叙事/落选/模型/**自审 review 渲染硬门禁**）；v1 作为降级形式继续可用，双版本校验器同时执行；
- **综合版 synthesis 模板**：条目墙（编号+标题+一句话摘要+分隔线）+ 坐标表达式（`y = "=photo_bottom + 40"`，ast 安全求值，仅字面量/四则/已知变量）；条目自然收缩/丢层，长标题 0.85× 起步两行走；
- **四阶段 SOP agent**：分析（并行子代理）→ 决策（低置信 `confirmed:false` 停下等人）→ 自审（独立第二遍，review 未过禁止渲染）→ 执行（`build_covers.py` 一键四模板）；
- **决策日志归档**：每次成功构建自动追加 `editorial_log.jsonl`（本地优先，零连接器）；
- **SQLite 证据链**：`versions.db` 三表（versions/decisions/feedback），JSON 为主、DB 双写、SELECT-only 审计查询、幂等 JSON→DB 迁移；
- **自动化配方**：`references/automation-recipe.md` 无人值守日报（置信度门槛 ≥0.9 加严制，产物本机落盘，进门三句话汇报）；
- **编辑基准集骨架**：`tests/editorial_benchmark/`（`--min-cases` 防冒充门禁：case 不足直接报错，拒绝用少量样本冒充达标率）；
- **可选出口**：`push_wecom.py`（须显式 `--confirm-outbound`）、`make_review_page.py`（单文件静态审核页，零端口）、`make_dashboard.py`（本地看板）；
- **偏好学习**：`~/.workbuddy/MEMORY.md`「贴图头条-编辑偏好」小节，写入前过用户确认，同一偏好确认 ≥2 次固化。

## 当前状态

- 专家结构：已注册并通过官方专家包校验（26.8.31）；
- 确定性渲染：`content-state.v1/v2` 双契约校验、四种模板（authoritative/visual/digest/synthesis）、中文字体路径解析、标题换行、坐标表达式、等比裁切和版本状态回退；回归测试全绿（v1+v2）；
- 真实媒体验证：**已完成首轮**（见下节），发布签发仍需人工在会话内确认终稿；
- 头像：已提供确定性绘制的简洁占位图，不是 AI 生成头像，可按需替换。

## 真实媒体验证记录（2026-08-31，release-26.8.31）

- 素材：《中国民族报》2026-08-28 会演专刊 **8 版 PDF**（原文件只读，SHA-256 全量入 `source_manifest`）；
- 流程：epaper-ingest 批处理（pdfplumber@2100px）→ 版面视觉标注（bbox+置信度）→ content-state.v2 构造（7 条真实条目逐字取自版面，1 条头版时政条目落选并记录理由）→ 校验通过 → **四模板 1080×1920 全部渲染成功**；
- 综合主标题「民族文化根脉的当代回响」为编辑合成，已按契约标注并待签发确认；
- 证据链：`ingest/source_manifest.json`、`covers/editorial_log.jsonl`、`.tietu_versions/versions.db`（版本 release-26.8.31-synthesis）、`review.html`（审核页）、`dashboard.html`（看板）。

## 验收指标

| 指标 | 数值 | 来源 |
|------|------|------|
| 回归测试 | 全绿（v1+v2，四模板 lint / 契约门禁 / 表达式 / 长标题 / SQLite） | `test_pipeline.py` 2026-08-31 输出 |
| 真实素材 e2e | 8 PDF → 4 模板全部渲染 | `tietu-test/release-26.8.31/` |
| 综合版条目渲染 | 4 条/版（item_max），标题逐字忠实 | `cover_synthesis_*.png` |
| 编辑一致率（agree-rate） | **待基准集**（v1 目标 10 份真实标注，`--min-cases` 门禁生效中） | `tests/editorial_benchmark/` |
| 自动化接管率 | **待自动化运行数据**（配方就绪，门槛 ≥0.9） | `references/automation-recipe.md` |

## 核心能力

- 识别媒体名称、报头、日期、主要标题、核心新闻图片和版面重点（低置信自动停机等人）；
- 单版三方案 / 综合版条目墙，一次生成 authoritative/visual/digest/synthesis 四个方案；
- 以 `content-state.v1/v2` 保存原文、置信度、确认状态、锁定项、否定风格、修订关系与决策日志；
- 保留原标题和原始素材，支持结构化局部修改与完整状态回退；综合主标题强制标注并请求确认；
- 使用确定性文字排版和等比裁切，降低中文错字、乱码、变形和图片拉伸风险；
- 默认面向高清竖版 PNG（1080×1920）和手机信息流缩略图展示。

## 使用示例

- 上传这张报纸版面，生成 3 个贴图头条方案；
- 这 8 版做一张综合头图，主图用 08 版题图；
- 在当前版本上修改日期位置，整体更庄重、减少装饰；
- 返回上一版，并恢复标题、图片、锁定项和版式状态；
- 把四个方案做成审核页，我选一个再说修改。

## 设计边界

多模态模型负责看懂报纸、选择内容、提炼重点并输出结构化内容状态；固定排版程序负责准确绘制标题、报头、日期和图片。关键文字不交给图像模型直接绘制。自审未通过不渲染；低置信不猜。连接器零前提：核心闭环（素材进来→判断落盘→成品落盘→经验留下）不依赖任何连接器，企微/审核页/看板均为可选出口。

## 安装与测试

在专家包根目录中安装依赖：

```bash
python -m pip install -r requirements.txt
python skills/tietu-toutiao/scripts/test_pipeline.py
```

## 专家目录

将专家包放入 WorkBuddy 配置目录下的：

```text
<WORKBUDDY_CONFIG_DIR>/plugins/marketplaces/my-experts/plugins/tietu-toutiao/
```

注册和打包由 WorkBuddy 专家管理流程执行；不要把本机用户名或绝对路径写入共享包。

## 头像

`avatars/expert.png` 为确定性绘制的简洁占位图。如需替换，要求 PNG（推荐）或 JPG、512×512 px、单张不超过 500KB。
