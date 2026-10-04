# wps.protection.enable

## 1. wps.protection.enable

#### 功能说明

限制在线文字文档的编辑。

> enable 后文档处于保护态，后续 fields/indexes/多数 insert 会失败。
> 若还要继续编辑，必须先 wps.protection.disable，password 与 enable 时一致。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "password": "smoke",
  "protect_type": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `password` (string, 可选): 保护密码，可选
- `protect_type` (number, 必填): 保护类型：1=仅修订，2=仅批注，3=仅窗体域，4=只读
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "protect_type": 1
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
