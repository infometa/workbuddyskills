# assets/

`echarts.min.js` 为报告渲染器内联使用的图表引擎（Apache ECharts，Apache-2.0）。
它由 `scripts/generate_report.py` 读入并**内联**进产物 HTML，使报告离线自包含、
双击即可打开、运行时零外部请求。

请勿手工修改本文件。校验：

    shasum -a 256 echarts.min.js
