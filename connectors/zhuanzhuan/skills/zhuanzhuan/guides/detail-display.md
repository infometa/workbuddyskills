# 商详展示规则（HTML 卡片篇）

> 本连接器商详主路径：用 `show_widget` 渲染 HTML 卡片。
> 仅当 `show_widget` 不可用时，才回退到 `SKILL.md`「查看详情」中的 Markdown 模板。

## HTML 卡片

### 渲染方式

生成完整 HTML（含 `<style>`）后，用 `show_widget` 输出，整段 HTML 作为 `widget_code`（上限 30KB）。

**`show_widget` 调用约束**：
- `title`：简短，如「{商品名}商详」
- `widget_code`：裸 HTML 片段，从 `<style>` 到根元素结束，**不含** `<html>/<head>/<body>/<!DOCTYPE>`
- `loading_messages`：1-4 条中文加载提示
- 主题：浅色（`#fff` 底 + `#17212b` 字），无需二次取色

### 卡片模板（`{}` 为字段占位）

```html
<style>
.card{background:#fff;border:1px solid #e7ebef;border-radius:12px;padding:14px;font:14px/1.5 -apple-system,"PingFang SC",sans-serif;color:#17212b}
.card h1{font-size:16px;font-weight:700;margin:0}
.card h2{font-size:14px;font-weight:600;margin:12px 0 6px}
.p{margin-top:8px}.p b{color:#e23a3a;font-size:22px}
.p r,.sp,.del{font-size:12px;color:#6d7782}.p r{margin-left:6px}.sp{margin:8px 0}.del{margin-top:8px}.del b{color:#17212b;font-weight:600;font-size:14px}
.svs span{display:inline-block;color:#34c759;background:#e8f7f0;font-size:12px;border-radius:999px;padding:3px 10px;margin:0 4px 4px 0}
.g{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}.g div{background:#f7f8fa;border-radius:6px;padding:6px 8px}.g i{display:block;font-style:normal;font-size:12px;color:#999}.g b{display:block;font-size:13px;margin:1px 0}.g em{display:block;font-style:normal;font-size:11px;color:#6d7782}
.qc{border-top:1px solid #e7ebef;margin-top:12px;padding-top:10px}.qc h2{margin:0 0 6px}
.tiles{display:grid;grid-template-columns:1fr 1fr;gap:6px}.tiles>div{background:#f7f8fa;border-radius:6px;padding:7px 9px;font-size:12px}
.tiles b{display:flex;justify-content:space-between;font-size:13px;margin-bottom:3px}.ok{color:#34c759}.no{color:#6d7782}
.tiles p{margin:5px 0 0;font-size:11px;color:#6d7782}
@media (min-width:640px){.g{grid-template-columns:repeat(6,1fr)}.tiles{grid-template-columns:repeat(3,1fr)}}
</style>
<article class="card">
<h1>{成色} {完整标题}</h1>
<p class="p"><b>¥{price}</b>{promotion? <r class="pro">{promotion}</r>}<r>{ref}</r></p>
<p class="sp">{sellingPoint}</p>
<p class="del"><b>🛡️ 服务</b> · <span class="svs"><span>✓ {服务1}</span>…</span></p>
<p class="del"><b>🚚 配送</b> · {deliverySummary}</p>
<h2>📋 参数规格</h2>
<div class="g"><div><i>{参数名}</i><b>{值1}</b>{多值? <b>{值2}</b> …}<em>{副文案}</em></div>…(最多2行)</div>
<div class="qc">
<h2>🔍 质检报告（{各维度检测数之和}项检测）</h2>
<div class="tiles">
<div><b><span>{维度名}</span><span><span class="no">● {未通过数}项</span> <span class="ok">✓ {通过数}项</span></span></b>{问题明细行? <p>{问题明细行}</p>}</div>
…
</div>
</div>
</article>
```

### 卡片内容 → 字段来源

| 展示位 | 字段 | 处理 |
|---|---|---|
| 标题 h1 | `chengSe` + `title` | |
| 到手价 | `price` | 原样展示 |
| 已享优惠 | `promotion` | 有才显示，如「满1799减100」 |
| 参考价 | `ref` | 空省略 |
| 卖点 | `sellingPoint` | 空省略 |
| 服务 | `benefit` | 每条一个 span，空省略 |
| 配送 | `deliverySummary` | 空省略 |
| 参数规格 | `spec` | 模型自主挑关键项；一格含 参数名 + 1-多个值 + 副文案，**最多 2 行小卡片**，空/不足省略 |
| 质检 | `inspection` | 见质检规则 |

### 质检规则

- 总检测数 = 各维度（通过数+未通过数）之和
- 每维度一格：维度名 + `● 未通过数项` `✓ 通过数项`（未通过在前，全过只显 ✓）
- 有未通过才追加问题明细行
- 通过绿 `#34c759`、未通过灰 `#6d7782`

### 通用约束

- **保留模板 emoji**（📋🔍📦 等）
- 缺失/空 → 对应块不渲染，不留占位、不编造
- 卡片内只陈列字段事实，不做推理、评述或总结；
- `jumpUrl` 空 → 依次用本次返回其他 `jumpUrl` → search 同商品 `jumpUrl`；都无才省略
- 购买建议，必须基于卡片事实（成色/瑕疵/价格），不编造、不臆断价位结论，展示价格已经是包含优惠后的到手价，严禁二次计算到手价。

### 卡片外正文（仅三件套）

```markdown
![{title}]({img}?w=160)

**购买建议**：{1-2 句，以推荐为主。避免与卡片重复（尽量不复述标题/价格等卡片已有信息），price已经是包含优惠的到手价，严禁提示"还能叠加/再减"。推荐理由聚焦价格是否划算、瑕疵是否可接受；确有明显不足才委婉提示谨慎，整体中立、不夸大。结尾提一下转转官方验或服务保障收尾，增强购买信心}

**👉 [查看详情/购买 ↗]({jumpUrl})**
```
