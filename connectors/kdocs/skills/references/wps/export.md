# wps.export

## 1. wps.export

#### 功能说明

统一导出在线文字文档，按 `format` 分发到不同导出分支：

- `docx`：返回 DOCX 下载结果
- `pdf`：创建 PDF 导出任务
- `ap`：发起 AP 导出流程

**幂等性**：否 — 导出为异步任务，用 task_id 轮询结果而非重复提交

#### 调用示例

`format=docx` 导出 DOCX：

```json
{
  "file_id": "023bf8fd81ab3d089b9d284a29d9b143",
  "format": "docx",
  "with_checksums": "md5,sha256"
}
```

`format=pdf` 导出 PDF：

```json
{
  "file_id": "023bf8fd81ab3d089b9d284a29d9b143",
  "format": "pdf",
  "from_page": 1,
  "to_page": 10
}
```

`format=ap` 导出 AP 文稿：

```json
{
  "file_id": "023bf8fd81ab3d089b9d284a29d9b143",
  "format": "ap",
  "name": "季度经营分析"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `format` (string, 必填): 导出格式。可选值：`docx` / `pdf` / `ap`
- `with_checksums` (string, 可选): `format=docx` 时可传，校验算法列表，如 `md5,sha256`
- `cid` (string, 可选): `format=docx` 时可传，分享链接 ID
- `from_page` (number, 可选): `format=pdf` 时可传，起始页码；默认值：`1`
- `to_page` (number, 可选): `format=pdf` 时可传，结束页码；默认值：`9999`
- `client_id` (string, 可选): 导出时可选的客户端标识
- `password` (string, 可选): `format=pdf` 时可传，源文档密码
- `store_type` (string, 可选): `format=pdf` 时可传，如 `ks3`、`cloud`
- `multipage` (number, 可选): `format=pdf` 时可传；默认值：`1`
- `opt_frame` (boolean, 可选): `format=pdf` 时可传；默认值：`true`
- `export_open_password` (string, 可选): `format=pdf` 时可传，导出 PDF 打开密码
- `export_modify_password` (string, 可选): `format=pdf` 时可传，导出 PDF 修改密码
- `name` (string, 可选): `format=ap` 时必填，智能文档名称，不含后缀
