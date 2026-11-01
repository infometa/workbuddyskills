# 文件上传/解析/引用详细规则

## 上传

```text
training.file.upload_document
  fileContent: base64 编码的文件内容
  fileName:    文件名（建议带扩展名，如 .txt/.pdf/.docx）
  knowledge_type: 0（课程参考资料，自动触发解析）
```

- 返回 `{fileId, fileName, size, mimeType}`
- MCP 路径 base64 有膨胀，建议 ≤20MB；更大走 PC 端直传
- `fileName` 建议带扩展名以便服务端推断 mime

## 解析状态轮询

```text
training.file.status(fileId) → {parseStatus, fileName, updateAt}
  parseStatus=2 → 解析完成，可引用
  parseStatus=3 → 解析失败，丢弃该文件并告知用户
  parseStatus=0/1 → 解析中/未开始，数秒后重查
  0/1 超过 10 分钟 → 停止轮询，直接携带 fileIds 进 chat（服务端守卫会自动恢复解析）
```

## 引用规则

- 在 `training.flashcard.update` 的 `metadata.fileIds` 中携带文件 ID 数组
- `fileIds` 必须为正整数数组、去重、≤20 个，任一非法整体拒绝（43505）
- **重复携带同一 fileIds 合法且必要**（服务端指纹去重 + 陈旧解析恢复路径）
- 文件必须属于当前用户所属组织，否则 43505
