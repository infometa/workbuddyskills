# 第三方资源登记

本目录存放技能脚本渲染报告时使用的**第三方前端资源**。资源随技能包一起分发，运行时**不做任何外部网络请求**。

## ECharts 5.5.1

| 项 | 值 |
|---|---|
| 文件 | echarts.min.js |
| 版本 | 5.5.1 |
| 许可 | Apache License 2.0（文件头部保留 Apache Software Foundation 许可声明，不得删除） |
| 字节数 | 1030855 |
| SHA-256 | e84270bd0cd5bdf60fefc26d00c2a391cb2e81f4d26a7a9ee16185a54773a3cf |
| 获取地址 | https://registry.npmmirror.com/echarts/5.5.1/files/dist/echarts.min.js |

**用途**：股权投资分析报告（generate_report.py）的图表引擎。渲染时把本文件**内联**进产出的 HTML，使报告成为单文件自包含产物——离线可打开、可单独转发与归档，且不依赖任何外部 CDN。

**为什么不用 CDN**：早期版本在 HTML 里引入外部 CDN。客户端离线或两个源都不可达时，报告里的图表会**静默空白**，用户看不出是加载失败还是本来就没数据。内联后不存在这个失败模式。

> 本技能包**自带**该资产，不跨技能引用——技能包必须自包含、禁止跨包 import。

## 维护约定

1. **内联前必须确认文件不含 `</script` 字面量**，否则会提前闭合 script 块、破坏 HTML。当前版本已确认不含。
2. **升级版本时**必须同步更新上表的版本号、字节数与 SHA-256，并重新执行第 1 条检查。
3. 本目录资源**只放第三方 vendored 资源**，不放本技能自己的代码。
4. 校验命令：

```bash
shasum -a 256 docs/skills/yj-fin-inv-pe/scripts/assets/echarts.min.js
```

输出的哈希必须与上表一致；不一致说明资源被改动或重新内置时取错了版本。
