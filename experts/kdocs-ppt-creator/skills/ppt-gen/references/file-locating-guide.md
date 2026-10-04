# 获取文件标识指南

多数工具可用 `url` / `link_id` / `file_id` 三选一定位。例外：`rename_file` 以及上传/移动等仍仅 `file_id`（或 `file_ids`）；部分工具另需 `drive_id`。按意图选择：

`create_file_with_content` / `create_empty_file` / `upload_new_file` 中 `drive_id`、`parent_id` 的传参规则：
- 可省略：用户未说明目标文件夹。
- 必须传入：用户已说明目标文件夹且已定位到对应 `drive_id`、`parent_id`；能传却省略视为错误。

`download_file` / `rename_file` / `share_file` / `cancel_share` / `copy_file` 的 **`drive_id` 非必填**：**已有明确的 drive_id 则传**，**没有则省略**。

| 用户提供 | 定位方式 |
|---------|--------|
| 浏览我的云文档根目录 | `drive.list_my_files` |
| 浏览指定文件夹（有 `drive_id` + `parent_id`） | `drive.list_files` |
| 文件名/关键词 | `search_files` → 结果含 `file_id`、`drive_id` |
| 文档链接 | `read_file(url=链接)` 返回内容与 `file_id`/`drive_id`；不需读内容时用 `get_share_info(link_id)`（见下方链接解析） |
| 已知 `file_id` | 场景工具直接传 `file_id`；补 `drive_id` 时用 `get_file_info(file_id)` |
| 需确认文档类型/后缀 | `get_file_info`（有链接可传 `url`）→ 从 `name` 取后缀 |
| 创建文件（指定文件夹） | `search_files` 等查到目标文件夹 → 传 `drive_id` + 该文件夹 `file_id` 作为 `parent_id` |
| 创建文件（用户未指定文件夹） | `drive_id`、`parent_id` 可不填，直接 `create_file_with_content` / `create_empty_file` / `upload_new_file` |

浏览类工具参数与示例见 [`drive/read_and_download.md`](drive/read_and_download.md)；`drive.list_files` 的 `drive_id`/`parent_id` 接续规则见该文件 list_files 工具卡。

> 根目录的 `parent_id` 固定为 `"0"`。

#### 文档链接解析

当链接域名为 `365.kdocs.cn` 或 `www.kdocs.cn` 时，按路径格式提取末尾的 `link_id`：
| 路径格式 | 提取规则 |
|---------|---------|
| `/l/<link_id>` | 文件分享链接 |
| `/folder/<link_id>` | 文件夹分享链接 |
| `/view/l/<link_id>` | 文件预览链接 |
提取后调用 `get_share_info(link_id)` 获取 `file_id` 和 `drive_id`。
