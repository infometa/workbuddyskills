# 外部数据源导入

> 腾讯会议录制导入、iWiki 文档迁移。

---

## 工具概览

### 🎥 腾讯会议录制
- `tx_meeting_search_tx_meeting_records` — 搜索录制记录
- `tx_meeting_describe_tx_meeting_record` — 查看录制详情
- `tx_meeting_import_tx_meeting_record` — 导入录制到知识库
- `tx_meeting_reload_tx_meeting_record` — 重新导入已有录制

### 📄 iWiki 迁移
- `iwiki_import_iwiki_doc` — 将 iWiki 页面导入到知识库

---

## 腾讯会议录制导入

```
Step 1: 搜索
  tx_meeting_search_tx_meeting_records(meeting_code="123456789")

Step 2: 确定目标位置
  space_describe_space(space_id) → root_entry_id

Step 3: 导入
  tx_meeting_import_tx_meeting_record(
    parent_entry_id = root_entry_id,
    record_file_id = "xxx",
    start_time = record.start_time - 300,
    end_time = record.end_time + 300
  )
```

### 注意事项

1. 时间范围建议各提前/延后 5 分钟
2. `tx_meeting_list_tx_meeting_records` 已废弃，用 search 替代
3. 从会议链接提取会议号后再搜索
4. 授权错误 → 提示用户在网页端先授权

---

## iWiki 文档迁移

```
Step 1: 确认 iWiki 链接
  https://iwiki.woa.com/pages/viewpage.action?pageId=xxx

Step 2: 确定目标位置
  space_describe_space(space_id) → root_entry_id

Step 3: 导入
  iwiki_import_iwiki_doc(url="https://iwiki.woa.com/...", parent_entry_id=root_entry_id)
```

### 注意事项

1. 授权错误 → 提示用户在乐享网页端先授权 iWiki
2. URL 格式必须完整
3. 仅内网环境可用
