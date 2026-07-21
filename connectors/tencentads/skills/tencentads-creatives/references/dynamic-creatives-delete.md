# 删除创意 (dynamic_creatives/delete)


## 请求参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告主账号ID，不支持代理商ID |
| dynamic_creative_id | int64 | 要删除的创意ID |

---

## 请求示例

```json
{
  "account_id": 123456789,
  "dynamic_creative_id": 111222333
}
```

## 响应参数

| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | integer | 0 表示成功 |
| data.dynamic_creative_id | int64 | 被删除的创意ID |

## 常见错误

| 错误码 | 说明 | 解决方案 |
|--------|------|---------|
| 40006 | `dynamic_creative_id` 不存在 | 确认创意ID是否正确 |
| 45000 | 同广告组下有并发操作 | 等待上一操作完成后再重试（串行执行） |
