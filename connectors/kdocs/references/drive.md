# 金山文档 Skill 工具完整参考

本文件包含金山文档 Skill 所有工具的 API 说明、参数、返回值。

> **通用返回字段**：所有接口均返回 `code`（状态码，0 表示成功）和 `msg`（人可阅读的文本信息）。

---

## 一、文档创建与上传

> 新建云文档、上传本地文件、网页剪藏与附件上传

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`create_file`](drive/create_and_upload.md) | 在云盘下新建文件 | `file_type`, `name` |
| [`create_folder`](drive/create_and_upload.md) | 在云盘下新建文件夹 | `drive_id`, `parent_id`, `name` |
| [`scrape_url`](drive/create_and_upload.md) | 网页剪藏，抓取网页内容并自动保存为智能文档 | `url` |
| [`scrape_progress`](drive/create_and_upload.md) | 查询网页剪藏任务进度 | `job_id` |
| [`upload_file`](drive/create_and_upload.md) | 全量上传写入文件（更新已有 docx/pdf 或新建并上传本地文件） | `file_id`\|`name`, `content_base64` |
| [`upload_attachment`](drive/create_and_upload.md) | 向已有文档上传附件，支持 URL 或 Base64 | `file_id`, `filename`, `url`\|`content_base64` |

## 二、文档读取与下载

> 列出目录、读取正文、获取下载信息与文件详情

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`list_files`](drive/read_and_download.md) | 获取指定文件夹下的子文件列表 | `drive_id`, `parent_id`, `page_size` |
| [`download_file`](drive/read_and_download.md) | 获取文件下载信息 | `file_id` |
| [`get_file_info`](drive/read_and_download.md) | 获取文件（夹）详细信息 | `file_id` |
| [`read_file_content`](drive/read_and_download.md) | 文档内容抽取为 Markdown/纯文本 | `drive_id`, `file_id`\|`link_id` |

## 三、文件组织

> 移动、重命名、复制以及同名检查

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`move_file`](drive/organize.md) | 批量移动文件(夹) | `drive_id`, `file_ids`, `dst_drive_id`, `dst_parent_id` |
| [`rename_file`](drive/organize.md) | 重命名文件（夹） | `file_id`, `dst_name` |
| [`copy_file`](drive/organize.md) | 复制文件到指定目录（可跨盘） | `file_id`, `dst_drive_id`, `dst_parent_id` |
| [`check_file_name`](drive/organize.md) | 检查目录下文件名是否已存在 | `drive_id`, `parent_id`, `name` |

## 四、分享

> 分享链接的开启、权限设置、取消、查询与在线访问

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`share_file`](drive/share.md) | 开启文件分享 | `file_id`, `scope` |
| [`set_share_permission`](drive/share.md) | 修改分享链接属性 | `link_id` |
| [`cancel_share`](drive/share.md) | 取消文件分享 | `file_id` |
| [`get_share_info`](drive/share.md) | 获取分享链接信息 | `link_id` |
| [`get_file_link`](drive/share.md) | 获取文件的云文档在线访问链接 | `file_id` |

## 五、搜索

> 跨云盘的文件搜索

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`search_files`](drive/search.md) | 文件（夹）搜索 | `type`, `page_size` |

## 六、标签

> 自定义标签的维护与对象打标

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`list_labels`](drive/label.md) | 分页获取云盘自定义标签列表（可按归属者、标签类型筛选） | `page_size` |
| [`create_label`](drive/label.md) | 创建自定义标签 | `allotee_type`, `name` |
| [`get_label_meta`](drive/label.md) | 获取单个标签详情（含系统标签固定 ID） | `label_id` |
| [`get_label_objects`](drive/label.md) | 获取某标签下的对象列表（文件/云盘等） | `label_id`, `object_type`, `page_size` |
| [`batch_add_label_objects`](drive/label.md) | 批量为多个文档对象添加同一标签（打标签） | `label_id`, `objects` |
| [`batch_remove_label_objects`](drive/label.md) | 批量取消标签 | `label_id`, `objects` |
| [`batch_update_label_objects`](drive/label.md) | 批量更新标签下对象排序或属性 | `label_id`, `objects` |
| [`batch_update_labels`](drive/label.md) | 批量修改自定义标签名称或属性 | `labels` |

## 七、收藏

> 收藏列表与批量操作

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`list_star_items`](drive/star.md) | 获取收藏（星标）列表 | `page_size` |
| [`batch_create_star_items`](drive/star.md) | 批量添加收藏 | `objects` |
| [`batch_delete_star_items`](drive/star.md) | 批量移除收藏 | `objects` |

## 八、最近与回收站

> 最近访问、回收站列表与还原

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`list_latest_items`](drive/recent_and_recycle.md) | 获取最近访问文档列表 | `page_size` |
| [`list_deleted_files`](drive/recent_and_recycle.md) | 获取回收站文件列表 | `page_size` |
| [`restore_deleted_file`](drive/recent_and_recycle.md) | 将回收站文件还原到原位置 | `file_id` |

## 附录

### A. 通用文件信息结构（FileInfo）

`create_file`、`upload_file`（步骤三）、`rename_file`、`list_files` 等接口返回的文件信息共用以下结构。响应字段表中 `array[FileInfo]` 即引用此结构：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 文件 ID |
| `name` | string | 文件名 |
| `type` | string | 文件类型：`file` / `folder` / `shortcut` |
| `size` | integer | 文件大小 |
| `parent_id` | string | 父目录 ID |
| `drive_id` | string | 驱动盘 ID |
| `version` | integer | 文件版本 |
| `ctime` | integer | 文件创建时间（时间戳，秒） |
| `mtime` | integer | 文件修改时间（时间戳，秒） |
| `shared` | boolean | 是否开启分享（link.status = 'open' 时为 true） |
| `link_id` | string | 分享 ID |
| `link_url` | string | 分享链接 URL |
| `created_by` | object | 文件创建者信息 |
| `created_by.id` | string | 身份 ID |
| `created_by.name` | string | 用户或应用的名称 |
| `created_by.type` | string | 身份类型：`user` / `sp` / `unknown` |
| `created_by.avatar` | string | 头像 |
| `created_by.company_id` | string | 身份所归属的公司 |
| `modified_by` | object | 文件修改者信息（结构同 created_by） |
| `ext_attrs` | array[object] | 文件扩展属性（`with_ext_attrs=true` 时返回），每项含 name 和 value |
| `drive` | object | 文件驱动盘信息（`with_drive=true` 时返回）

**`permission` 对象**（`with_permission=true` 时返回）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `comment` | boolean | 评论 |
| `copy` | boolean | 复制 |
| `copy_content` | boolean | 内容复制 |
| `delete` | boolean | 文件删除 |
| `download` | boolean | 下载 |
| `history` | boolean | 历史版本（仅公网支持） |
| `list` | boolean | 列表 |
| `move` | boolean | 文件移动 |
| `new_empty` | boolean | 新建 |
| `perm_ctl` | boolean | 权限管理 |
| `preview` | boolean | 预览 |
| `print` | boolean | 打印 |
| `rename` | boolean | 文件重命名 |
| `saveas` | boolean | 另存为（仅公网支持） |
| `secret` | boolean | 安全文档（仅公网支持） |
| `share` | boolean | 分享 |
| `update` | boolean | 编辑/更新 |
| `upload` | boolean | 上传：手动上传新版本
