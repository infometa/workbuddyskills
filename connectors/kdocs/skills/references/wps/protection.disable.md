# wps.protection.disable

## 1. wps.protection.disable

#### 功能说明

取消在线文字文档的编辑限制。

> disable 的 password 必须与 enable 时一致；未保护文档上 disable 通常仍返回成功。
> indexes/fields 等插入前若文档可能处于保护态，应先 disable。
> 排查提示：texts.font/highlight 等字符格式写操作报 500002，而 content/alignment/line_spacing 写正常时，大概率是文档处于保护态。先用本工具 disable 再重试写操作。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "password": "smoke"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `password` (string, 可选): 保护密码；若设置过密码则必填
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
