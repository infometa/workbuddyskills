# 国内机票推荐往返组合页

> 加载时机：按 `workflows/air-domestic-search.md` 出国内**推荐往返**（`journeyType=1`）结果页时。
> 对照下面摘要即可，**不要打开** `assets/air-domestic-roundtrip-page.html`，不要改 HTML。
> 单程走 `air-domestic-oneway-page.md`，不要把往返结果丢给单程脚本。

每个 `flightList` 行是一个固定组合：去程段 + 返程段，每段各一个舱位，没有「展开看全部舱位」。
行数可能上千，本页是紧凑列表。脚本 `scripts/air_domestic_roundtrip_render_page.py`，
模板 `assets/air-domestic-roundtrip-page.html`。只吃 `journeyType=1` 且每行恰两段。

## 默认页能力摘要

| 块 | 已有能力（有即直接出页） |
|---|---|
| 标题/副标 | 城市往返；组数（去程×返程）、全部直飞与否、最低往返含税、静态截断说明 |
| KPI | 组合总数；最低往返合计含税（两段航班号）；含协议价组合数；执飞航司数 |
| 工具栏 | 去程/返程时段、航司、共享下拉（非共享 / 共享 / 全部，**默认非共享**；去或回任一 `shareId` 非空=共享）、关键字、「仅看含协议价组合」、排序（总价/去程最早/返程最早）、计数 |
| 组合行 | 去程 + 返程两段：日期时刻机场时长、航班号航司共享直飞机型餐食准点舱位余量行李；不显示单程价 |
| 舱位 | 字母+等级（协议价红字/代购紫标）、余量（A→9 位）、免费托运；不展示 enterpriseId |
| 总价与下单 | 往返含税合计 + 「去下单」（免登 `#/bookingPricing`，`flyType=2`，字段见 [`air-domestic-sso-forward.md`](air-domestic-sso-forward.md)） |
| 退改 | 文案齐全：弹层；退或改缺一侧且有 `cabId`：页内 `domestic_rule`（头 infoCode） |
| 行李 | 每段「行李政策」独立弹层 |
| 大列表 | JS 全量筛选排序；静态区 ≤400 行全量，>400 只预渲染前 200（无 JS 仍能看样例） |
| 页脚 | `requestSeqNo`（缺则不渲染） |
| 口径 | `official=true` 才有协议价；代购同样有去下单链接；跳转进下单页 ≠ 已下单 |

## 出页

用本轮 `domestic_shopping`（`journeyType=1`）的返回跑脚本。大 JSON 不要进大模型；
`<src>` 可以是 `-` 或本轮落盘路径。

```bash
python3 scripts/air_domestic_roundtrip_render_page.py <src> \
  --from-city 北京 --to-city 西宁 \
  --go-date 2026-09-20 --ret-date 2026-10-12 \
  --full-note \
  --out "<输出.html>"
```

`--go-date`/`--ret-date` 缺省时从数据首/次段自动取。成功则打印组合数/去回航班数/含协议价组合/最低往返含税价。
出页自检只做静态区 `div` 平衡与 `{{XXX}}` 残留检查；不要对 `<script>` 做括号计数，也不要每次跑 `node --check`（注入的航班 JSON 字符串常含半角括号，会误报）。

## 预览与汇报

WorkBuddy 用 `present_files` 打开本地 HTML。禁止 `http.server`、任何本地端口、系统浏览器。
国内页没有 selection-map，不要去找映射文件。页内退改直调失败就地显示原因，禁止复制指令降级。
对话不超过两句摘要：用脚本打印的统计填表 + 编号要点，不另写 python 抽源 JSON。

用户点「去下单」是免登跳转下单页，不等于已下单。缺 `infoCode`/`forwardCode` 时脚本拒绝带下单按钮的页。
纯展示传 `--no-order-links`。
