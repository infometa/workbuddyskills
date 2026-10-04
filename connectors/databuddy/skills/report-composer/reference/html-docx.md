# reference/html-docx.md —— DOCX 导出（§L，可选）

> **触发条件**：`args.export_docx=true` 且已产出 html；否则跳过本文件，**不引** `html.md` §b 第二档的两个额外 CDN。
> **依赖**：`html.md` §b 第二档（`html2canvas` + `html-docx`）、§e（打印隐藏规则，本文 L.2 的导出按钮要按 §e 加进 print 隐藏清单）。

## L. DOCX 导出

### L.1 原理（为什么要两个库）

`wedata-chart` 图表内核是 ECharts `<canvas>`,`html-docx` 打包时会丢失 canvas 内容;所以要先把每个图表 canvas 用 `toDataURL()` 截成静态位图 `<img>`。KPI 卡片、表格、文字这些 **DOM 区域**不是 canvas,要先用 `html2canvas` 截成位图,再和图表位图一起,由 `html-docx` 打包进 `.docx`。两个库各司其职:

- `html2canvas`:DOM 区域(KPI / 表格 / 文字段)→ `<img>` 位图。
- `html-docx`(`window.htmlDocx.asBlob(html)`):把最终 HTML 字符串 → `.docx` 二进制 Blob。

### L.2 接入方式（在 §j 的 HTML 里加一个导出按钮 + 脚本）

在 `<head>` 按 §b 第二档加 `html2canvas` + `html-docx` 两个 CDN,并在 `<body>` 末尾加导出逻辑。组件化后**不再有 `CHART_INSTANCES` 句柄**,改为直接遍历页面上 `.wedata-chart` 卡片里 wedata-chart 渲染出的 `<canvas>`,逐个 `toDataURL()` 换成 `<img>`:

```html
<button class="docx-btn" onclick="exportDocx()">导出 Word</button>
<script>
  function exportDocx() {
    // wedata-chart 图表内核是 canvas，html-docx 会丢 canvas，先逐个换成静态位图 <img>
    var canvases = document.querySelectorAll('.wedata-chart canvas');
    for (var i = 0; i < canvases.length; i++) {
      var cv = canvases[i];
      try {
        var url = cv.toDataURL('image/png');
        var img = document.createElement('img');
        img.src = url;
        img.style.width = '100%';
        cv.parentNode.replaceChild(img, cv);
      } catch (e) { /* 单个图表截图失败不阻断整体导出 */ }
    }
    // 取整页 HTML（含已转成 <img> 的图表）→ docx Blob → 触发下载
    var html = '<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>'
             + document.body.innerHTML + '</body></html>';
    var blob = window.htmlDocx.asBlob(html);
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = (document.title || 'report') + '.docx';
    a.click();
  }
</script>
```

> 关键点:
> - wedata-chart 图表是 canvas,在 `html-docx` 里会丢,**必须先把 `.wedata-chart canvas` `toDataURL()` 换成 `<img>`** 再打包。
> - 导出前确保图表已渲染完成(页面加载后 wedata-chart 自动扫描渲染;导出按钮由用户点击触发,此时 canvas 已就绪)。
> - `.docx` 是浏览器端点击按钮下载——本 skill 的"产出 docx_path"指的是**该 HTML 自带导出能力**;若需服务端直接落一个 `.docx` 文件,属[阶段二]确定性渲染范围,本期以"HTML 内嵌导出按钮"交付。
> - 导出按钮在 `@media print` 与正常视图里都应 `display:none` 进 docx 自身(它是操作控件,不该印进文档),按 §e 加进 print 隐藏清单。

### L.3 自检（开 docx 时附加）

- [ ] `<head>` 含 `html2canvas.min.js` + `html-docx.min.js`,且均来自 `wedata.cdn.tencent.com`
- [ ] `exportDocx()` 里**先把 `.wedata-chart canvas` `toDataURL()` 换成 `<img>`** 再 `asBlob`
- [ ] 导出按钮 `.docx-btn` 在 `@media print` 中 `display:none`
- [ ] 未开 docx 的产物里**不出现** html2canvas / html-docx（§b 默认档只有 echarts + wedata-chart）
