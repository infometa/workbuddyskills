# 每日自动化配方（无人值守日报头图）

> 对应升级方案 §5.3。目标：每日自动从电子报产出头图方案，产物本机落盘，
> 进门三句话主动报账。**零连接器、零端口、置信度门槛制**——高置信全自动，
> 低置信停下来等人。

## 一、目录契约

全部路径相对当前 WorkBuddy 工作区（自动化运行时以绝对路径传入，见下方 prompt）：

| 用途 | 路径 | 说明 |
|------|------|------|
| 当日目录 | `.tietu_inbox/<YYYY-MM-DD>/` | 下载的 PDF/版面图（**原文件只读**） |
| 产物 | `.tietu_inbox/<YYYY-MM-DD>/covers/` | 头图 ×4 + layout + content-state |
| 停机留痕 | `.tietu_inbox/<YYYY-MM-DD>/NEEDS_HUMAN.md` | 存在即说明今日未达全自动门槛 |
| 决策日志归档 | `.tietu_inbox/editorial_log.jsonl` | 追加式，每次成功构建一条 |
| 版本库 | `.tietu_versions/versions.db`（可用时） | SQLite 证据链，不可用时仅 JSON |

`.tietu_inbox/` 同时是专家工作台的进门收件箱：自动化把产物放进去，
下次进会话「进门三句话」会主动汇报，不需要用户找文件。

## 二、置信度门槛（无人值守专用）

人工会话内低置信门槛是 0.85（`confirmed:false` 停下来等人）；自动化场景
没有人盯着，门槛**加严到 0.9**，且版面标注必须双复跑稳定（IoU ≥ 0.9）：

- 报头文本、日期、主图 bbox、标题文本四类关键字段**全部** ≥ 0.9 且双复跑稳定
  → `editorial_log.review = {passed:true, mode:"auto", evidence:[...]}`，
  直接渲染四模板头图。
- 任一字段不达标 → **不渲染**，落 `NEEDS_HUMAN.md`（逐字段列置信度、IoU、
  建议动作），content-state 与 layout_analysis 照常落盘供人复核。

`NEEDS_HUMAN` 不是失败，是设计内的停机。宁可空手，不可脑补。

## 三、自动化 Prompt（整段复制到 WorkBuddy 自动化设置）

> 使用前把「工作目录」换成你的实际工作区绝对路径；报纸源 URL 按需替换。

```text
执行贴图头条无人值守日报任务（专家包 tietu-toutiao 26.8.31）。

背景：这是每日定时运行的自动化任务，本次运行看不到任何对话历史，全部依据写在本
prompt 内。目标是把当日电子报变成头图方案，产物全部本机落盘，不依赖任何连接器。

常量：
- 工作目录 = <当前工作区绝对路径>（首次使用时替换，例如新建一个专属工作区后取其路径）
- 脚本目录 = <WORKBUDDY_CONFIG_DIR>\plugins\marketplaces\my-experts\plugins\tietu-toutiao\skills\tietu-toutiao\scripts
- 今日目录 D = 工作目录\.tietu_inbox\<今日日期 YYYY-MM-DD>

步骤：
1. 检查 D 内是否已有素材（PDF/JPG/PNG）。若无，用 agent-browser 技能访问
   https://www.mzb.com.cn 当日电子报页面，下载 1-2 个版面 PDF 到 D；
   下载后一律只读。两路都没有素材 → 写 D\NEEDS_HUMAN.md（原因：无输入）后正常结束。
2. PDF 用 epaper-ingest 技能处理：渲染版面图（DPI = 目标宽/(页宽pt/72)，钳制
   100-400）、生成 source_manifest（含 SHA-256）。
3. 版面分析用 layout-analysis 技能：多模态标注 bbox+置信度，双复跑 IoU>=0.9 才算
   稳定；报头/日期/主图/标题四类关键字段逐个记录置信度。
4. 生成 content-state v2（schema 见专家包 references/content-state.v2.schema.json）：
   items[] 带权重与四维评分；editorial_log 记录 narrative/excluded/model；
   标题一律用报纸原标题，禁止改写与合成。
5. 门槛判定（自动化专用 >=0.9，比人工 0.85 严）：
   - 四类关键字段全部 >=0.9 且双复跑稳定 → editorial_log.review =
     {passed:true, mode:"auto", evidence:[各字段置信度]}，然后运行
     python <脚本目录>\build_covers.py --state <state> --out-dir D\covers
     生成四模板头图。
   - 否则 → 不渲染。写 D\NEEDS_HUMAN.md：逐字段列出置信度、双复跑 IoU、建议
     动作。content-state 与 layout_analysis 照常落盘供人复核。
6. 归档：成功构建时把 editorial_log 追加到 工作目录\.tietu_inbox\editorial_log.jsonl；
   并用 python <脚本目录>\version_manager.py save 保存版本（versions.db 不可用时
   仅 JSON，不算失败）。
7. 汇报：最终输出「进门三句话」格式摘要——今日生成了什么 / 哪些待确认 /
   文件绝对路径清单。

铁律：
- 低置信不渲染：宁可空手，不可脑补；NEEDS_HUMAN 是设计内停机，不是失败。
- 原素材只读；所有写入仅限 工作目录\.tietu_inbox\ 内。
- 不向任何云端 API 上传素材内容；企微推送是可选出口，本次不做，留给人工会话决定。
- 单次运行不装依赖、不改脚本；脚本缺失或校验失败 → 写 NEEDS_HUMAN.md
  （原因 + stderr 摘要）后结束。
- 任何不确定（多报纸混入、日期不明、版面过小）一律停机留痕，不自行猜测。
```

## 四、创建步骤

1. WorkBuddy 左侧 → 自动化 → 新建；类型选 **recurring**，每日 07:30
   （RRULE：`FREQ=DAILY;BYHOUR=7;BYMINUTE=30`，间隔 1 天）。
2. prompt 粘贴上文第三节整段，核对「工作目录」常量。
3. 首次运行前手动触发一次，确认目录权限与脚本路径无误。
4. 次日进门，「进门三句话」应主动报昨日产物；没有报说明自动化没跑成，查
   `NEEDS_HUMAN.md` 或自动化运行日志。

## 五、签发流程（自动化只生产，签发留给人工）

进门三句话 → 看方案 → 说修改（或「就这个」）→ 专家转结构化 patch →
终版归档。自动化产物默认视为**草稿**：未经人工会话确认，不进
`.tietu_versions/` 的正式版本链（只记 source="auto" 草稿版本）。

## 六、可选出口（插拔自由，拔掉主路径不残缺）

- **企微推送**：`scripts/push_wecom.py`（详见脚本头部说明；需显式
  `--confirm-outbound`，符合外发确认边界）。
- **审核页**：`scripts/make_review_page.py` 生成单文件静态 review.html，
  零端口，选完复制回执贴回会话即可。
- **看板**：`scripts/make_dashboard.py` 汇总 versions.db + editorial_log.jsonl
  生成本地 dashboard.html。
