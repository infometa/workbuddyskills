# 国内机票交互分析页

> 加载时机：按 `workflows/air-domestic-search.md` 出国内单程分析页时。
> 对照下面「默认页能力摘要」即可判断够不够用，**不要打开** `assets/air-domestic-oneway-page.html`。
> 出页不要改 HTML/模板。查询按 [`../workflows/air-domestic-search.md`](../workflows/air-domestic-search.md)。

## 默认页能力摘要

渲染脚本 `scripts/air_domestic_oneway_render_page.py` + 模板 `assets/air-domestic-oneway-page.html`（与往返 `assets/air-domestic-roundtrip-page.html` 成对，文件名分开）。
标准查询只跑 `scripts/air_domestic_query.py`，读 `run_summary.json` 的 `html` 打开。
只吃 **国内单程** `domestic_shopping` 的返回。往返、经停专页、创单/支付、差标都不在本页。
标识：航班 `{serialNumber, flightId}`，选舱再加 `cabId`（不要 `flightList`）。

| 块 | 已有能力（有即直接出页，不要改模板） |
|---|---|
| KPI | 直飞班次；最低含税价（航班号 + 是否协议价）；协议价舱位数/舱位总数；执飞航司数 |
| 分布 | 多变机场条（出发侧或到达侧自动推断）；出发时段条（06-09 … 21-24） |
| 工具栏 | 机场 / 时段 / 航司筛选；共享下拉（非共享 / 共享 / 全部，**默认非共享**，`shareId` 非空=共享）；关键字搜索；「仅看含协议价」；按出发时间 / 价格 / 时长排序；**本地分页**（每页 20 班，筛/排仍对完整结果，翻页不重查） |
| 航班卡 | 航司+航班号、共享徽标、机型、餐食、准点率、机建/燃油、起降时刻+时长（`fmtDur`/`_fmt_dur` 紧凑格式如 `2h25m`，非裸分钟；**排序仍按分钟数值**）+机场路线、最低含税价；**前 5 班**（`--top-open`，按推荐）默认展开并预载舱位；其余航班点「更多」展开本次 `domestic_shopping` 已返回的舱位（不打 busi / 不重查 shopping） |
| 舱位表 | 独立 7 列：舱位字母（代购舱加紫色徽标）、等级（协议舱在后面加红色「协议价」标签，无协议舱不留占位）、余量（A→9 位）、免费托运、票价(含税)+门市/折扣、**退改/行李**（退+改文案齐全：`.cab-link` CSS 弹层；**退或改任一为空**且有 `cabId`：页内直调 busi `rule`，请求头 infoCode）、**去下单**（免登 `/oauth2/forward?authCode=forwardCode`）；每班默认渲染前 3 档舱位，可「展开全部」；价格下方小字为「含税总价起 · N个舱位」；代购舱去下单链接与普通舱一致 |
| 页脚流水号 | `.note` 下几乎不可见一行 `请求流水号 requestSeqNo：<值>`（信封层，缺则不渲染） |
| 口径 | `official=true` 才有协议价标签；shopping 舱位自带退改文本写入 `rule`；价格 KPI/卡片最低价按含税总价；下单跳转=`#/bookingPricing`，最外层 `serialNumber`/`flightId`/`cabId`（选舱后有 cabId，flightId=航段级航班号），不要 flightList |

行李文案来自 shopping 舱位字段 `luggage`（弹层正文）；列「免费托运」仍用 `weight`（kg）。结构化 `portableWeight` / `cabin.baggage` 供往返页等其它展示，单程弹层以 `luggage` 去重为准。

改脚本展示维度后同步本表，不要让模型去读 HTML 自行归纳。

## 出页

查询参数（城市码、`official=true` 等）以 [`../workflows/air-domestic-search.md`](../workflows/air-domestic-search.md) 为准，本文件只写出页。

用本轮 `domestic_shopping` 的返回跑脚本。大 JSON **不要整份读进大模型**；`src` 可以是 `-`（stdin）
或本轮落盘的文件路径（脚本两种都支持，自动截取首个 `[` 或 `{`）。不要去 skill 目录翻旧文件。

```bash
python3 scripts/air_domestic_oneway_render_page.py - \
  --from-city 长沙 --to-city 成都 \
  --from-code CSX --to-code CTU1 \
  --date 2026-09-03 --date-text "2026-09-03(周四)" \
  --adult 1 --top-open 5 \
  --full-note \
  --out "<输出.html>"
```

`--side` 缺省 `auto`；`--no-order-links` 可关闭去下单链接（仅纯展示时）。脚本失败会非 0 退出；
成功则打印航班/舱位/协议舱/航司/机场分布/最低价。不要打开生成 HTML 做结构检查，不要跑 `node --check`。

- 脚本打印 `航班 N · 舱位 N · 协议舱 N` 与预期大体一致（因公时协议舱>0）。
- 页面无 `{{XXX}}` 占位符残留。
- 含关键标记：`details.card`、`btn-book` 去下单链接、`window.__syncOpenLazy` 展开自动拉舱、`.tag-ent`（有协议价时，位于等级列内）。

## 预览与汇报

WorkBuddy 用 `present_files` **直接打开本地 HTML 路径**。禁止 `http.server`、任何本地端口、
拉起系统浏览器。其它宿主按其 HTML 预览能力即可。国内页没有 selection-map，不要去找映射文件。
页内退改直调失败就地显示原因，禁止复制指令降级。

对话不超过两句摘要。关键指标用脚本打印的统计填 markdown 表 + 编号要点（直飞班次、机场分布、
航司数、舱位/协议舱、最低价、值得关注航班），不要另写 python 抽源 JSON。

用户点「去下单」即经免登 forward 跳 portal 下单页继续操作；字段契约见
[`air-domestic-sso-forward.md`](air-domestic-sso-forward.md)，编码与 `/forward` 见
[`sso-forward.md`](sso-forward.md)。
