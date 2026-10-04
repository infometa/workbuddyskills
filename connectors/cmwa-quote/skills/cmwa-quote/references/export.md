# 导出（export）

> ⛔ **对外口径**：工具名、字段名（`structuredContent` / `contentBase64` 等）、下载链路实现
> 仅供内部执行，**禁止出现在给用户的文字里**。对用户只说「询价单已导出」。

## 工具

`exportExcel`：导出询价 Excel。

## 调用方式

无入参（空对象）：

```
exportExcel()
```

## 返回契约（★ 重要）

成功返回 `structuredContent`，字段固定为：

| 字段 | 类型 | 说明 |
|---|---|---|
| `fileName` | string | 文件名，如 `询价导出_20260917.xlsx` |
| `contentBase64` | string | **Excel 文件内容的 base64**（非空） |

即：

```json
{
  "isError": false,
  "content": [{ "type": "text", "text": "导出完成" }],
  "structuredContent": {
    "fileName": "询价导出_20260917.xlsx",
    "contentBase64": "UEsDBBQABgAIAAAAIQ..."
  }
}
```

> ⚠️ **字段名是 `contentBase64`，不是 `base64`。**
> 页面（`web-dyb/index.html`）曾因读 `sc.base64` 而拿不到内容，直接落到兜底分支
> 并谎报「导出成功」——表现为「点了导出没反应/没文件」。已在页面侧修正为
> `sc.contentBase64 || sc.base64 || sc.fileContent || sc.excelBase64`。

## 页面侧下载链路

页面用 `app.callServerTool({ name: 'exportExcel', arguments: {} })` 取回内容，再交给宿主落盘：

```js
await app.downloadFile({
  contents: [{
    type: 'resource',
    resource: { uri: 'file:///' + encodeURIComponent(fileName),
                mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                blob: contentBase64 }   // 宿主用 atob() 校验，须为纯 base64
  }]
});
```

- `type: 'resource'` = 内联内容（宿主直接用 `blob`）；`type: 'resource_link'` = 宿主自己去下载（仅 http/https）。
- 宿主从 `resource.uri` 的最后一段推导文件名，所以 **uri 里必须带上文件名**（中文需 `encodeURIComponent`）。
- `contentBase64` 里若有换行/空白，建议先 `.replace(/\s/g, '')` 再传。
- 宿主内部日志标记：`services.downloadFile.start` / `services.downloadFile.result`。

## 注意事项

- 导出为读操作，可直接执行；
- **`exportExcel` 不带页面**：调它**不会**打开/重复打开询价报价；
- 用户直接说「导出询价」时：调 `exportExcel` 并**把文件直接交给用户**，
  不要引导用户去页面上点「导出」按钮；
- 导出结果文件路径/下载方式由返回内容决定，AI 据实告知用户即可；
- 对用户只说「询价单已导出」（必要时附文件名），**不要**提字段名、编码格式、下载实现方式。

## 与询价报价的关系

- 页面上的「导出」按钮走的是**同一个** `exportExcel` 工具。若用户已在页面上操作，无需再调一次；
- **不要**为了导出而先打开询价报价 —— 导出不需要页面在场。
