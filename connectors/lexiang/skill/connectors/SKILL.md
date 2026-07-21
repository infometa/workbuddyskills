---
name: lexiang-connectors
description: "乐享知识库外部数据源导入：腾讯会议录制导入与 iWiki 文档迁移。当用户提到「乐享」「知识库」「lexiang」并包含会议录制/会议纪要/导入会议/iWiki/迁移文档意图时使用。典型触发：「把会议录制导入到乐享」「导入腾讯会议」「把昨天的会议记录保存到知识库」「搜一下我的会议录制」「把 iWiki 的文档迁移到乐享」「导入 iwiki.woa.com 的页面」。支持腾讯会议录制搜索、导入、详情查看、重新导入，以及 iWiki 文档一键迁移到乐享知识库。"
---

# 乐享外部数据源导入

> **基础知识**：数据模型、URL 规则见 `base/SKILL.md`。
> **前置条件**：本 skill 需要已配置乐享 MCP 连接。如未配置，请先读取 `setup/SKILL.md`。
> **遇到 401 错误**：不要重试，读取 `setup/SKILL.md` 引导用户续期（点击续期按钮即可恢复，无需重新配置）。

---

## 工具概览

### 🎥 腾讯会议录制
- `tx_meeting_search_tx_meeting_records` — 根据会议号搜索录制记录
- `tx_meeting_describe_tx_meeting_record` — 查看录制详情
- `tx_meeting_import_tx_meeting_record` — 导入录制到乐享知识库
- `tx_meeting_reload_tx_meeting_record` — 重新导入已有录制
- `tx_meeting_list_tx_meeting_records` — 列举录制记录（已废弃，请用 search）

### 📄 iWiki 文档迁移
- `iwiki_import_iwiki_doc` — 将 iWiki 页面导入到乐享知识库

---

## 腾讯会议录制导入

### 使用流程

```
场景：「把昨天的会议录制导入到 XX 知识库」

Step 1: 搜索会议录制
  tx_meeting_search_tx_meeting_records(meeting_code="123456789")
  → 返回录制列表，包含 record_file_id、start_time、end_time

Step 2: 确定目标位置
  search_kb_search(keyword="XX", type="space") 定位知识库
  space_describe_space(space_id) 获取 root_entry_id

Step 3: 导入录制
  tx_meeting_import_tx_meeting_record(
    parent_entry_id = root_entry_id,
    record_file_id = "xxx",
    start_time = record.start_time - 300,  // 提前5分钟
    end_time = record.end_time + 300       // 延后5分钟
  )
```

### ⚠️ 注意事项

1. **时间范围建议放宽**：`start_time` 和 `end_time` 比录制记录中的实际时间各提前/延后几分钟，确保录制内容完整
2. **`tx_meeting_list_tx_meeting_records` 已废弃**：请使用 `tx_meeting_search_tx_meeting_records` 替代
3. **重新导入**：如果之前导入的录制需要更新，使用 `tx_meeting_reload_tx_meeting_record`
4. **授权问题**：如果报授权错误，需要提示用户在网页端先进行腾讯会议授权

---

## iWiki 文档迁移

### 使用流程

```
场景：「把这个 iWiki 页面迁移到乐享」

Step 1: 确认 iWiki 链接
  用户提供 https://iwiki.woa.com/pages/viewpage.action?pageId=xxx

Step 2: 确定目标位置
  search_kb_search(keyword="XX", type="space") 定位目标知识库
  space_describe_space(space_id) 获取 root_entry_id

Step 3: 导入
  iwiki_import_iwiki_doc(url="https://iwiki.woa.com/...", parent_entry_id=root_entry_id)
```

### ⚠️ 注意事项

1. **授权错误**：如果导入报没有授权等错误，需要提示用户在乐享网页端先进行 iWiki 授权
2. **URL 格式**：必须是完整的 `iwiki.woa.com/pages/viewpage.action?pageId=xxx` 格式
3. **内网限制**：iWiki 导入仅在内网环境可用

---

## ⚠️ 核心注意事项

1. **`_mcp_fields` 优化**：所有工具支持 `_mcp_fields` 参数选择返回字段，减少 token 消耗
2. 参数不确定时以 `get_tool_schema(tool_name="xxx")` 返回为准
