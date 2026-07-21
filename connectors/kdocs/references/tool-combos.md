# 工具组合速查

| 用户需求 | 推荐工具组合 |
|----------|-------------|
| 找文档 | `search_files` |
| 找 + 读 | `search_files` → `read_file_content` |
| 找 + 读 + 写新 | `search_files` → `read_file_content` → `create_file` → `upload_file` |
| 找 + 读 + 更新 | `search_files` → `read_file_content` → `upload_file`（传 file_id） |
| 浏览目录 | `list_files` |
| 整理归类 | `list_files` → `read_file_content` → `create_folder` → `move_file` |
| 网页保存 | `scrape_url` → `scrape_progress` |
| 分享文档 | `share_file` → `set_share_permission` |
| 获取链接 | `get_file_link` |
| 新建标签并打标 | `create_label` → `batch_add_label_objects` |
| 回收站恢复 | `list_deleted_files` → `restore_deleted_file` |
