# 文档上传规则（单一权威）

**本文档是文档上传的单一权威来源**。SKILL.md 中的相关规则以本文为准。

## 核心规则

**只要用户提供了原始文档文件 → 强制上传**（无论文档长短）。

- ❌ 禁止提取为纯文字内联到 message
- ❌ 禁止直接调用 MCP 工具 `training.file.upload_document`（agent 无法生成 base64）
- ✅ 必须使用脚本 `upload_document.py` 上传

## 上传流程

### 步骤 1：使用脚本上传

```bash
python3 skills/ai_customer_design/scripts/upload_document.py /path/to/doc.pdf
```

脚本返回 JSON：
```json
{
  "fileId": 7667,
  "fileName": "doc.pdf",
  "status": "ready",
  "size": 12345,
  "mimeType": "application/pdf"
}
```

### 步骤 2：处理返回状态

**status="ready"**：解析完成，可以安全使用 fileId

**status="failed"**：解析失败，文件可能损坏或格式不支持，告知用户

**status="timeout_recovery"**：超过 10 分钟恢复阈值，但 **仍可带 fileIds 进入对话触发恢复**

```python
# 正确做法：无论 status 如何（除了 failed），都带 fileIds 进入对话
if result["status"] in ("ready", "timeout_recovery"):
    # 在建课对话中传递 metadata.fileIds: [fileId]
    # 服务端会在对话中触发文件解析恢复
    pass
elif result["status"] == "failed":
    # 告知用户文件解析失败
    pass
```

### 步骤 3：在建课对话中使用 fileIds

使用 `training.ai_customer.update` 工具时，在 metadata 中传递 fileIds：

```json
{
  "tool": "training.ai_customer.update",
  "arguments": {
    "courseId": 123,
    "message": "请根据上传的文档创建课程",
    "metadata": {
      "fileIds": [7667]
    }
  }
}
```

**注意**：完整的工具白名单请参考 `skills/ai_customer_design/SKILL.md` 的"工具白名单"章节。

## 错误处理

### 43505 错误码

**不要把所有 43505 都解释成"解析未完成"**。

43505 可能表示：
- 文件正在解析中（等待即可）
- 文件需要恢复（带 fileIds 进入对话触发恢复）
- 文件解析失败（告知用户）

根据 upload_document.py 返回的 status 判断：
- status="ready" 后遇到 43505 → 异常，报告运维
- status="timeout_recovery" 后遇到 43505 → 正常，带 fileIds 进入对话

### 脚本报错

**"MCP authentication failed"**：
- 先检查环境（test vs 生产）
- 使用 coach-mcp-connect 技能重新认证

**"Cannot connect to MCP server"**：
- 检查 mcp.json 配置
- 确认 MCP 服务器 URL 正确

## 轮询参数说明

**为什么是 10 分钟？**
- 10 分钟是"陈旧解析任务恢复阈值"，不是硬超时
- 超过 10 分钟后，文件仍可带 fileIds 进入对话触发恢复
- upload_document.py 在超时后返回 status="timeout_recovery"，不会退出

## 大文件处理

对于大文件（> 1MB）：
- 脚本会自动处理 base64 编码
- 上传时间可能较长，请耐心等待
- 如果上传失败，检查网络连接

## DOCX/PPTX/XLSX 文件

对于 Office 文档：
- 服务端会自动解析
- 如果解析失败（parseStatus=3），考虑转换为 PDF 后重试
- 或使用 pandoc 转换为 Markdown 后内联（仅当转换后 < 8000 字符时）
