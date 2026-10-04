# wps.query_export

## 1. wps.query_export

#### 功能说明

统一查询异步导出结果：

- `format=pdf`：查询 PDF 导出任务
- `format=ap`：查询 AP 导出任务

#### 调用示例

`format=pdf` 查询 PDF 导出结果：

```json
{
  "format": "pdf",
  "task_id": "task_xxx",
  "task_type": "normal_export"
}
```

`format=ap` 查询 AP 导出结果：

```json
{
  "format": "ap",
  "file_id": "ap_file_xxx",
  "task_id": "task_xxx"
}
```

#### 参数说明

- `format` (string, 必填): 导出格式。可选值：`pdf` / `ap`
- `task_id` (string, 必填): 导出任务 ID
- `task_type` (string, 可选): `format=pdf` 时可传，通常为 `normal_export`
- `file_id` (string, 可选): `format=ap` 时必填，传 `wps.export` 返回的新智能文档文件 ID
- `extra_query` (object, 可选): `format=ap` 时可传，补充查询参数
