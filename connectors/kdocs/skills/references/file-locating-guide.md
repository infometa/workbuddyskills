# 获取文件标识指南

多数工具可用 `url` / `link_id` / `file_id` 三选一定位。例外：`rename_file` 以及上传/移动等仍仅 `file_id`（或 `file_ids`）。

## 目录坐标：`drive_id` / `parent_id`

云盘目录场景 **不要传 `drive_id`**：schema 已全部可选，服务端能自查就补，补不出会报可行动错误并指出下一步。Agent 只提供意图对象：

| 你要做的事 | 传什么 | 不要做 |
|---------|--------|--------|
| 读 / 下 / 改名 / 分享 | `file_id` 或链接 | 不要传 `drive_id` |
| 新建到个人根 | 盘和目录都不传 | 不要抄 drive，不要自己填 `parent_id=0` |
| 新建到某文件夹 | `parent_id` = 文件夹 id | 不必再配 `drive_id` |
| 浏览个人根 | `list_my_files` | 不要 `list_files(parent_id=0)` |
| 浏览某文件夹 | `list_files(parent_id=该 id)` | 不必再找 drive |
| 移动 / 复制 / 另存 | 源 `file_id` + `dst_parent_id` | 不要把源盘抄到 dst；不要用 `parent_id` 当目标 |
| 搬到用户点名的「某盘的根」 | 当次 `list_my_files` / `list_doclibs` 的 `dst_drive_id` + `dst_parent_id="0"` | 不要用 search / 其它文件上的盘 ID 配 `"0"` |

**仍要传、但语义不是「文件所在盘」的**（单列，不与上表混）：`list_drive_roles` / `get_doclib_meta` / `kwiki.*` 的库 ID；`dbsheet.parent_*` 的记录 ID；`search_files` 的 `drive_ids` / `parent_ids` 数组；`wps.create_empty_document` / `wpp.create_empty_presentation` 的 `group_id` + 数值 `parent_id`（创建落点）。

> `parent_id="0"` 只表示**某个盘**的根，不是个人盘根。禁止用 search、其它文件、会话缓存的 `drive_id` 配 `"0"`。用户明确要落到某团队库根、且盘 ID 来自**当次** `list_doclibs`：合法，按传入走。

失败后的下一轮（硬约束）：

- `list_files` 失败后，**禁止**用同一个 `parent_id` 原样重试；改 `search_files` 按名找，或从 `list_my_files` 重走。
- 移入回收站不是 move/copy/save_as 的目标语义；已删除文件用 `list_deleted_files` 查看、`restore_deleted_file` 还原。

| 用户提供 | 定位方式 |
|---------|--------|
| 浏览我的云文档根目录 | `list_my_files` |
| 浏览指定文件夹（有文件夹 id） | `list_files(parent_id=该 id)`，不必再找 `drive_id` |
| 文件名/关键词（找**文件**） | `search_files` → 结果含 `file_id` |
| 查询我近期高频使用或编辑的文档（也可以按时间、打开行为、常用程度、权限背景或宽泛主题查找） | `search_high_value_documents(query=...)` → 优先返回近期常用、经常操作且与查询内容最匹配的文档 |
| 用户指定目标文件夹（路径或单级名） | 见下方「定位文件夹」 |
| 文档链接 | `read_file(url=链接)` 返回内容与 `file_id`；不需读内容时用 `get_share_info(link_id)`（见下方链接解析） |
| 已知 `file_id` | 场景工具直接传 `file_id`；不要为凑规则补 `drive_id` |
| 需确认文档类型/后缀 | `get_file_info`（有链接可传 `url`）→ 从 `name` 取后缀 |
| 创建文件（用户未指定文件夹） | 盘和目录都不传，直接 `create_file_with_content` / `create_empty_file` / `upload_new_file` |

浏览类工具参数与示例见 `drive/read_and_download.md`；`list_files` 的 `parent_id` 接续规则见该文件 list_files 工具卡。

### 精确查找与按使用情况找文档

- 如果知道文件名、关键词或文件类型，想精确查找或筛选文件，用 `search_files`。
- 如果想说“找我上周经常编辑的文件”“查一下今天看过的文档”或“找关于某个主题的资料”，用 `search_high_value_documents`；它会优先展示最近用过、经常使用且更符合描述的文档。
- 如果已经找到文档或已经有 `file_id`，直接进行读取、编辑等后续操作，不要重复搜索。

### 定位文件夹

所有「指定文件夹 / 查找文件夹 / 创建到某目录」共用本节。已知父目录或创建落点时按下述流程定位；按关键词跨目录查找文件夹可用 `search_files(keyword="文件夹名", type="file_name", file_type="folder", page_size=10)`。

**个人云文档根**：盘和目录都不传。浏览用 `list_my_files`；新建直接传 `name`。

**路径含 `/`（多级，从个人云根）**

1. 不必先查盘：`create_folder` 省略 `drive_id` / `parent_id` 时默认个人盘根，配 `parent_path`（除末段外的各段）+ `name`（末段）。例 `项目A/周报` → `name=周报`，`parent_path=["项目A"]`。
2. 用响应 `data.id` 作 `parent_id`。**已存在**：`parent_path` 会解析已有中间目录；若响应 `name` 与用户末段不一致（`on_name_conflict=rename`），在父目录 `list_files` 按名取已有 id，勿重复 create。
3. 用户明确指定非个人盘时：`drive_id` 只用**当次** `list_my_files` / `list_doclibs` 返回值，勿用 search 或会话缓存。

**单级文件夹名（无 `/`）**

1. 先 `list_my_files`（或父目录 `list_files`）按名精确匹配 → **命中用 `id` 作 `parent_id`**（只传 `parent_id`，跳过 create）。
2. 无匹配再 `create_folder(name=末段, on_name_conflict=rename)`——不传 `drive_id` / `parent_id`，默认个人盘根。

### 文档链接解析

当链接域名为 `365.kdocs.cn` 或 `www.kdocs.cn` 时，按路径格式提取末尾的 `link_id`：
| 路径格式 | 提取规则 |
|---------|---------|
| `/l/<link_id>` | 文件分享链接 |
| `/folder/<link_id>` | 文件夹分享链接 |
| `/view/l/<link_id>` | 文件预览链接 |
提取后调用 `get_share_info(link_id)` 获取 `file_id`。
