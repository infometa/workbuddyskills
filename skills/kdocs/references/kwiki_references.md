# 个人知识库（kwiki）工具完整参考文档

本文件说明金山文档 Skill 中个人知识库相关的 `kwiki.*` 工具如何使用。它们面向"知识库空间"和"知识库内资料管理"场景，适合创建知识库、浏览库内目录、导入已有云文档，以及整理知识库中的文件和文件夹。

## 通用说明

### 何时使用 `kwiki.*`

- 需要新建一个个人知识库或资料库空间
- 需要查询已有知识库列表，或按名称/ID 获取某个知识库详情
- 需要浏览知识库根目录或某个知识库文件夹下的资料
- 需要把**已有云文档**导入知识库
- 需要在知识库里新建文件夹或在线文件，并对库内资料做移动、删除、下载
- 仔细阅读接口参数说明，不猜测，不胡编乱造

### 特别说明

> - 仔细阅读接口参数说明，不猜测，不胡编乱造

> - 本地上传不走 `kwiki.*`

### 链接输出规范

接口返回的数据中，`url` 字段为**相对路径**（如 `/l/xxx?source=kmwiki` 或 `/wiki/l/xxx`），`kuid`字段为**知识库/文件夹/文件id**。**Agent 在拼接完整链接时，必须遵循以下规则，不猜测：**

1. **拼接规则**：`https://www.kdocs.cn` + `data.url 原值`。
2. **手动构造**：若接口未返回 `url` 但返回了 `kuid`，格式为 `https://www.kdocs.cn/wiki/l/${kuid}`。

### 标识说明

在 `kwiki.*` 场景里，常见会用到以下标识：

- `drive_id`: 知识库对应的驱动盘 ID
- `group_id`: 知识库所属组 ID
- `kuid`: 知识库或知识库内文件/文件夹的标识

经验上：

- 知识库本身的 `kuid` 常见为 `0s...`
- 知识库内文件夹/文件的 `kuid` 常见为 `0l...`

如果用户只给了知识库名称，通常先用 `kwiki.list_knowledge_views` 搜，再把返回的 `drive_id` / `group_id` / `kuid` 传给后续工具。

> **注意**： `kuid` 仅用于 kwiki 专属操作（`delete_item`/`move_items`/`import_cloud_doc` 等）。

---

## 个人知识库（kwiki）专属接口

### 1. kwiki.create_knowledge_view

#### 功能说明

创建新的个人知识库空间，可设置名称、状态、描述、封面与来源等基础信息。

#### 调用示例

创建销售知识库：

```json
{
  "space_name": "销售知识库",
  "desc": "沉淀销售话术、案例和培训资料",
  "status": 1
}
```


#### 参数说明

- `space_name` (string, 必填): 知识库名称
- `status` (number, 必填): 知识库可见状态，传 `1` 表示正常公开
- `desc` (string, 可选): 知识库简介文本
- `img` (string, 可选): 封面图 URL 或资源标识，不传使用系统默认封面
- `source` (string, 可选): 创建来源标识，用于业务溯源
- `role_id` (string, 可选): 创建者角色 ID，不传使用默认角色

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "drive_id": "8001234567",
    "group_id": "6200987654",
    "kuid": "0s_8001234567"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.drive_id` | string | 新建知识库的驱动盘 ID |
| `data.group_id` | string | 新建知识库的群组 ID |
| `data.kuid` | string | 新建知识库的 kuid，格式 `0s_...` |


#### 操作约束

- **后置验证**：新建后调用 `kwiki.get_knowledge_view` 或 `kwiki.list_knowledge_views` 核对返回的 `drive_id`、`group_id`、`kuid`
---

### 2. kwiki.list_knowledge_views

#### 功能说明

分页查询当前用户的个人知识库列表，支持按关键字过滤。

#### 调用示例

按关键字分页查询：

```json
{
  "keyword": "销售",
  "page_size": 20
}
```


#### 参数说明

- `keyword` (string, 可选): 搜索关键字，匹配知识库名称；不传则返回全部
- `page_size` (number, 可选): 每页返回条数，不传使用服务端默认值
- `page_token` (string, 可选): 分页 token，首次请求不传；后续页传上一次返回的 `next_page_token`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "has_more": false,
    "list": [
      {
        "drive_id": "8001234567",
        "group_id": "6200987654",
        "kuid": "0s_8001234567",
        "space_name": "销售知识库",
        "desc": "沉淀销售话术、案例和培训资料",
        "cover_img": "https://cdn.example.com/2025/06/09/other/1.png",
        "file_total": 12,
        "member_total": 1,
        "utime": 1775221117,
        "owner": {
          "id": 900012345,
          "name": "张三",
          "avatar": "https://img.example.com/avatar/default"
        }
      }
    ],
    "next_page_token": ""
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.list` | array[object] | 知识库摘要列表 |
| `data.has_more` | boolean | 是否有更多页 |
| `data.next_page_token` | string | 下一页 token，为空表示无更多页 |

> 用户只提供了知识库名称时，先用它来定位知识库
> 需要列出某人当前有哪些知识库
---

### 3. kwiki.get_knowledge_view

#### 功能说明

根据 drive_id 或名称查询单个知识库的详细信息。drive_id 与 name 至少提供其一。

#### 调用示例

按 drive_id 查询：

```json
{
  "drive_id": "8001234567",
  "group_id": "6200987654"
}
```

按名称查询：

```json
{
  "name": "销售知识库"
}
```


#### 参数说明

- `drive_id` (string, 可选): 条件必填：已知知识库驱动盘 ID 时直接传（来自 `list_knowledge_views` / `create_knowledge_view` 返回值）。与 name 至少填其一
- `name` (string, 可选): 条件必填：仅知道名称时传入，模糊匹配。与 drive_id 至少填其一
- `group_id` (string, 可选): 群组 ID（来自 `list_knowledge_views` / `create_knowledge_view` 返回值），已知时传入可加速定位

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "drive_id": "8001234567",
    "group_id": "6200987654",
    "kuid": "0s_8001234567",
    "space_name": "销售知识库",
    "desc": "沉淀销售话术、案例和培训资料",
    "cover_img": "https://cdn.example.com/2025/06/09/other/7.png",
    "file_total": 12,
    "member_total": 1,
    "utime": 1775221117,
    "owner": {
      "id": 900012345,
      "name": "张三",
      "avatar": "https://img.example.com/avatar/default"
    }
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.drive_id` | string | 知识库驱动盘 ID |
| `data.group_id` | string | 群组 ID |
| `data.kuid` | string | 知识库唯一标识，格式 `0s_...`，用于构造访问链接：`https://www.kdocs.cn/wiki/l/{kuid}` |
| `data.space_name` | string | 知识库名称 |
| `data.desc` | string | 知识库描述 |
| `data.cover_img` | string | 封面图片 URL |
| `data.file_total` | number | 文档总数 |
| `data.member_total` | number | 成员总数 |
| `data.utime` | number | 最近更新时间（Unix 时间戳，秒） |
| `data.owner` | object | 知识库所有者信息，含 id / name / avatar |

> 如果用户同时给了名称和 ID，优先用 ID
> 若名称匹配到多个知识库，需结合返回结果进一步确认目标知识库
---

### 4. kwiki.update_knowledge_view

#### 功能说明

更新知识库名称、描述、封面、状态等配置，按需传入待修改字段。

#### 调用示例

更新名称与描述：

```json
{
  "drive_id": "8001234567",
  "group_id": "6200987654",
  "name": "销售知识库（2026版）",
  "desc": "沉淀销售方法论、案例和常见问答",
  "cover_img": "https://cdn.example.com/2025/06/09/other/7.png",
  "status": 1
}
```


#### 参数说明

- `drive_id` (string, 必填): 知识库驱动盘 ID，来自 `list_knowledge_views` 或 `get_knowledge_view` 返回值
- `group_id` (string, 可选): 群组 ID，来自 `list_knowledge_views` 或 `get_knowledge_view` 返回值
- `name` (string, 可选): 新的知识库名称，不传则保持原值
- `desc` (string, 可选): 新的知识库描述，不传则保持原值
- `cover_img` (string, 必填): 封面图 URL（后端必传，可从 get_knowledge_view 获取当前值回传）
- `status` (number, 必填): 知识库状态（后端必传，可从 get_knowledge_view 获取当前值回传）

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": ""
}

```


#### 操作约束

- **前置检查**：`kwiki.get_knowledge_view` 确认目标知识库存在及当前配置
- **后置验证**：`kwiki.get_knowledge_view` 确认名称或简介已更新
---

### 5. kwiki.close_knowledge_view

#### 功能说明

关闭并删除指定个人知识库，操作前务必确认目标正确。

#### 调用示例

关闭指定知识库：

```json
{
  "drive_id": "8001234567"
}
```


#### 参数说明

- `drive_id` (string, 必填): 要关闭的知识库驱动盘 ID，来自 `list_knowledge_views` 或 `get_knowledge_view` 返回值

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": ""
}

```


#### 操作约束

- **用户确认**：关闭知识库不可恢复，必须向用户确认目标知识库名称和 ID
- **前置检查**：`kwiki.get_knowledge_view` 确认目标知识库
---

### 6. kwiki.list_items

#### 功能说明

列出知识库根目录或某个文件夹下的内容，返回文件和文件夹混合列表。

#### 调用示例

列出根目录内容：

```json
{
  "kuid": "0s_8002345678"
}
```


#### 参数说明

- `kuid` (string, 必填): 知识库 kuid（格式 `0s_...`，来自 `list_knowledge_views` / `get_knowledge_view`）或文件夹 kuid（来自 `list_items`）

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "has_more": false,
    "list": [
      {
        "kuid": "0lAbCdE1234fGH",
        "file_id": "100200300401",
        "title": "产品需求文档",
        "doc_type": "o",
        "doc_origin_type": "otl",
        "link_id": "AbCdE1234fGH",
        "ctime": 1775221153,
        "size": 28175,
        "parent_id": "0",
        "creator": {
          "id": 900012345,
          "name": "张三",
          "avatar": "https://img.example.com/avatar/default"
        }
      },
      {
        "kuid": "0lXyZw7KLmN1pQ",
        "file_id": "100200300402",
        "title": "培训材料",
        "doc_type": "folder",
        "doc_origin_type": "",
        "link_id": "XyZw7KLmN1pQ",
        "ctime": 1775221152,
        "size": 0,
        "parent_id": "0",
        "creator": {
          "id": 900012345,
          "name": "张三",
          "avatar": "https://img.example.com/avatar/default"
        }
      }
    ],
    "next_page_token": ""
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.list` | array | 目录项列表 |
| `data.has_more` | boolean | 是否有更多项 |
| `data.next_page_token` | string | 下一页 token，为空表示无更多页 |

**items 条目字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `kuid` | string | 知识库内唯一标识，**kwiki 操作（delete_item/move_items/import_cloud_doc）均使用此 ID** |
| `file_id` | string | 云文档系统 file_id |
| `title` | string | 文件/文件夹名称（不含扩展名） |
| `doc_type` | string | 类型：`o`=智能文档, `w`=Word, `p`=PPT, `s`=Excel, `i`=图片, `v`=视频, `folder`=文件夹 |
| `link_id` | string | 分享链接标识，可通过 `get_file_link(link_id=...)` 获取在线链接 |
| `ctime` | integer | 创建时间（Unix 时间戳，秒） |
| `size` | integer | 文件大小（字节） |

> ⚠️ **注意**：`kwiki.list_items` 不返回 `mtime`（修改时间）。如需按修改时间筛选，
> 使用 `list_files(drive_id=知识库drive_id, parent_id=file_id, order_by="mtime")` 获取 `mtime` 信息。

> 浏览知识库根目录或进入某个文件夹后继续查看下一级内容
> 为后续移动、删除、下载收集 `kuid`
---

### 7. kwiki.import_cloud_doc

#### 功能说明

把已有云文档导入到知识库中，可导入副本或快捷方式。这是「导入已有云文档」工具，不是「上传本地文件」工具。

#### 调用示例

复制导入云文档：

```json
{
  "action": "copy",
  "kuid": "0s_8002345678",
  "file_infos": [
    {
      "file_ids": [
        100200300403
      ],
      "group_id": 6200987654
    }
  ]
}
```


#### 参数说明

- `kuid` (string, 必填): 目标知识库 kuid（格式 `0s_...`）或知识库内文件夹 kuid，来自 `list_knowledge_views` / `list_items`
- `action` (string, 可选): 导入方式，copy 为副本，shortcut 为快捷方式。可选值：`copy` / `shortcut`；默认值：`copy`
- `file_infos` (array[object], 必填): 待导入云文档列表，每项含 `file_ids`（云文档 file_id 数组）和 `group_id`（文档所属群组 ID）

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "url": "/wiki/l/0s_8001234567"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.url` | string | 知识库相对路径，拼接 `https://www.kdocs.cn` + url 得到完整链接 |


#### 操作约束

- **后置验证**：`kwiki.list_items` 确认文档已导入
> 如果用户提供的是本地文件内容，应改用 `upload_file`
---

### 8. kwiki.create_item

#### 功能说明

在指定父级 kuid 下新建文件夹或指定类型的云文档。

#### 调用示例

创建文件夹：

```json
{
  "doc_type": "folder",
  "kuid": "0s_8002345678",
  "title": "培训材料"
}
```

创建文字文档：

```json
{
  "doc_type": "w",
  "kuid": "0l_parent_xxx",
  "title": "销售常见问题"
}
```


#### 参数说明

- `doc_type` (string, 必填): 文档类型。可选值：`folder` / `w` / `s` / `o` / `p` / `d`
  - `folder`=文件夹
  - `w`=在线文字
  - `s`=表格
  - `o`=智能文档
  - `p`=演示文稿
  - `d`=轻维表
- `kuid` (string, 必填): 父级 kuid——传知识库 kuid（`0s_...`）创建在根目录，传文件夹 kuid 创建在该文件夹下
- `title` (string, 必填): 新建文件或文件夹的标题名称

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "kuid": "0lXyZw7KLmN1pQ",
    "title": "培训材料",
    "url": "/l/XyZw7KLmN1pQ?source=kmwiki"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.kuid` | string | 新建项的 kuid |
| `data.title` | string | 新建项标题 |
| `data.url` | string | 相对路径，拼接 `https://www.kdocs.cn` + url 得到完整链接 |


#### 操作约束

- **后置验证**：`kwiki.list_items` 确认创建成功
> 传知识库 `kuid` 则创建在根目录，传文件夹 `kuid` 则创建在该文件夹下
---

### 9. kwiki.delete_item

#### 功能说明

删除后进入知识库回收站，7 天内可通过 restore_deleted_file 恢复。支持删除文件夹（包括非空文件夹，会连带删除内部所有内容）。

#### 调用示例

删除指定条目：

```json
{
  "kuid": "0lPqRs8WxYzAbC"
}
```


#### 参数说明

- `kuid` (string, 必填): 待删除条目的 kuid，来自 `list_items` 返回值

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "message": "文件已移至回收站，7天内可恢复",
    "trash_url": "https://www.kdocs.cn/enttrash/0"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.message` | string | 操作结果描述 |
| `data.trash_url` | string | 回收站页面链接 |


#### 操作约束

- **前置检查**：`kwiki.list_items` 确认对象名称和位置
- **用户确认**：删除操作不可逆（非空文件夹会连带删除），必须向用户确认
> 仅支持单个删除，批量清理时需循环调用
> 删除后进入知识库回收站，7 天内可通过 `restore_deleted_file(file_id=...)` 恢复
> **也支持删除文件夹**（包括空文件夹和非空文件夹），非空文件夹会连带删除内部所有内容
---


## 工具速查表

| # | 工具名 | 功能 | 必填参数 |
|---|--------|------|----------|
| 1 | `kwiki.create_knowledge_view` | 创建个人知识库 | `space_name`, `status` |
| 2 | `kwiki.list_knowledge_views` | 查询知识库列表 |  |
| 3 | `kwiki.get_knowledge_view` | 获取单个知识库详情 |  |
| 4 | `kwiki.update_knowledge_view` | 修改知识库基础配置 | `drive_id`, `cover_img`, `status` |
| 5 | `kwiki.close_knowledge_view` | 关闭（删除）知识库 | `drive_id` |
| 6 | `kwiki.list_items` | 列出知识库目录下的内容 | `kuid` |
| 7 | `kwiki.import_cloud_doc` | 将已有云文档导入知识库 | `kuid`, `file_infos` |
| 8 | `kwiki.create_item` | 在知识库中创建文件或文件夹 | `doc_type`, `kuid`, `title` |
| 9 | `kwiki.delete_item` | 删除知识库中的文件或文件夹 | `kuid` |

## 常用工作流

### 上传本地文件到知识库

**触发示例**：「把本地 XX 文件归档/上传/同步/放到 XX 库的 XX 文件夹」「把这些资料归档/上传/同步/放到 XX 库」「定时归档/上传/同步/放 XX 到 XX 库」

**流程**：
1. `kwiki.get_knowledge_view` 或 `kwiki.list_knowledge_views` 获取目标知识库的 `drive_id`
2. 如需放入子文件夹：
   - `kwiki.list_items` 定位目标文件夹，获取其 `kuid`（用于 kwiki 操作）和 `file_id`（用于通用接口的 `parent_id`）
   - 放入根目录则 `parent_id="0"`
3. 按文件类型选择上传方式：

**常规文件（docx/pdf/pptx/xlsx 等）**：
`upload_file(drive_id=知识库drive_id, parent_id=目标文件夹id, name="文件名.docx", content_base64=...)`

**Markdown 文件（.md）**：
> 默认转为在线智能文档，保留格式和结构化内容。仅当用户明确要求"上传并保持 md 格式"时，才使用 `upload_file` 直接上传原始 `.md` 文件。

- `kwiki.create_item(doc_type="o", kuid=目标文件夹kuid, title="文件名（不含后缀）")` 创建智能文档
- 读取本地 `.md` 文件内容
- `otl.insert_content(file_id=新文档的file_id, content=markdown原文, pos="begin")` 将 markdown 写入智能文档
  - 如果内容过长（>3000 字符），分段写入：首段用 `pos="begin"`，后续段用 `pos="end"` 追加
- 从 `kwiki.list_items` 返回中获取 `link_id`，拼接在线链接

### 重命名知识库内的文件或文件夹

使用通用接口 `rename_file` 重命名知识库内的文件或文件夹：

1. `kwiki.get_knowledge_view(name="知识库名")` 获取知识库的 `drive_id` 和 `kuid`
2. `kwiki.list_items(kuid=知识库kuid)` 定位目标文件，获取 `file_id` 和 `drive_id`
3. `rename_file(drive_id=drive_id, file_id=file_id, dst_name="新名称")`
   - 文件须带后缀（如 `"新报告.docx"`）
   - 文件夹不带后缀（如 `"项目资料"`）

### 下载知识库文件到本地

**流程**：

1. `kwiki.list_items(kuid=目标目录kuid)` 定位目标文件，获取 `file_id`、`link_id`、`drive_id`
2. 根据文件类型选择下载方式：

**普通文件（docx/pptx/pdf/图片等）**：
1. 使用 `wps_export` 等导出工具获取带签名的下载 URL（`link_id` 来自 `kwiki.list_items`）
2. `curl.exe -L -o "文件名" "签名URL"` 下载

**智能文档（doc_type="o"）**：`wps_export` 不支持直接导出，无特殊情况，默认转换成Markdown格式：
- **Markdown** → `read_file_content(drive_id, file_id, format="markdown")`（异步，需轮询 task_id），将返回的 markdown 内容保存为 `.md` 文件

**快捷方式文件（type="shortcut"）**：通过 `search_files` 搜索原始文件名找到源文件，再用源文件的 `link_id` 走上述通用流程。

> 注意：`download_file` 返回的 URL 需登录态，无法直接 curl。始终优先使用 `wps_export` 获取带签名的下载 URL。受保护文件（SecureDocumentError / forbidProtectedFile）所有导出接口均无法操作，需提示用户。

### 把文件放到知识库

**触发示例**：「帮我把 XX 放到 XX 知识库」「把这些文件归档到 XX 库的 XX 文件夹」「帮我把本地 XX 文件夹的文件放到 XX 库里面」「帮我把 XX 网页的文章放到知识库」

**流程**：

1. **定位知识库**：指定库名 → `kwiki.get_knowledge_view(name=...)`；未指定 → `kwiki.list_knowledge_views` 推荐或引导创建
2. **定位目标路径**：指定文件夹 → `kwiki.list_items` 逐层查找，不存在则 `kwiki.create_item(doc_type="folder")` 按层级创建；未指定 → 根目录
3. **归档**：
   - 本地文件/文件夹 → 按「上传本地文件到知识库」流程逐个上传，保持子目录结构时递归创建文件夹
   - 网页 → `scrape_url` + `scrape_progress` 轮询完成后，`move_file` 移入目标库
   - 云盘已有文件 → `kwiki.import_cloud_doc(action="copy"/"shortcut")`
4. **确认结果**：`kwiki.list_items` 返回存放路径与直达链接；批量时展示成功/失败明细

### 查找知识库内的文件

**触发示例**：「帮我找一下 XX 文件」「在 XX 库里找 XX 相关的资料」「我要找关于 XX 的文档」

**流程**：

1. **提取条件**：从用户指令中识别关键词、指定库名、文件类型等筛选条件
2. **定位搜索范围**：
   - 指定库 → `kwiki.get_knowledge_view(name=...)` 确认库存在，获取 `drive_id`
   - 未指定库 → `kwiki.list_knowledge_views` 获取全量知识库列表
3. **执行搜索**：`search_files(keyword="关键词", type="all", drive_ids=[目标drive_id列表])` 跨库或指定库检索
4. **返回结果**：按匹配度排序，展示文件名、所在库/路径、修改时间、直达链接；结果过多时提示用户按文件类型或时间范围二次筛选
5. **展示结果并询问用户** → 展示文件信息 + **主动询问是否下载到本地或打开查看（提供在线链接）用户选择下载时的后续操作**：

- `search_files` 返回的 `file_id` 可直接用于 `read_file_content` 等通用接口
- 根据文件类型选择下载方式，详见「下载知识库文件到本地」流程

### 整理分类知识库

**触发示例**：「帮我整理一下 XX 知识库」「把 XX 库里的文件按类型分类」

> ⚠️ **场景识别**：当用户明确提到「知识库」「库」「资料库」等关键词时，优先使用 `kwiki.*` 系列接口完成整理/分类，确保知识库内部元数据（索引、搜索等）一致。

**流程**：

1. `kwiki.list_knowledge_views(keyword="库名")` 搜索目标知识库，获取 `drive_id`、`group_id`、`kuid` 等关键标识
2. `kwiki.list_items(kuid=知识库kuid)` 遍历根目录内容；如需递归遍历子文件夹，继续用文件夹的 `kuid` 调用 `kwiki.list_items`。收集每个文件的 `kuid`、`title`、`doc_type` 信息
3. 列出需新建的分类文件夹、文件移动目标、建议删除的内容，明确标注操作影响范围，**提交用户确认后再执行**
4. 批量创建文件夹（`kwiki.create_item`）→ 批量移动文件（`move_file`）→ 删除确认的冗余内容（`kwiki.delete_item`），提示回收站恢复路径（7 天内可恢复）

### 清理知识库无用文件

**触发示例**：「清理 XX 库里 1 个月未修改的文件」「删掉 XX 库里的空文件夹」「把 XX 库里过期的资料清理一下」

**流程**：

1. `kwiki.list_items(kuid=空间kuid)` 递归遍历全库，获取每个文件/文件夹的 `kuid`、`file_id`、`title`、`doc_type`、`ctime`
2. **如需按修改时间筛选**：用 `list_files(drive_id=知识库drive_id, parent_id=父目录file_id, order_by="mtime")` 获取 `mtime`，通过 `file_id` 匹配到 `kuid`
3. **向用户展示待删除清单并确认**
4. `kwiki.delete_item(kuid=xxx)` 逐个删除（进入回收站，7 天内可 `restore_deleted_file` 恢复）
5. 空文件夹可同样通过 `kwiki.delete_item` 删除

### 网页内容存入知识库

> **触发示例**：「把公众号文章存入XX知识库」「把这个链接存到知识库里」

**流程**
1. 主流程：scrape_url → scrape_progress(status=1) → move_file → get_file_link
2. 降级流程（scrape_url 失败/status=-1，如公众号等 JS 渲染页面）：
   browser 抓取正文 → create_file(name=xxx.docx)
   → upload_file(drive_id=xxx parent_id=0 file_id=xxx content_format=markdown content_base64=xxx)
   → move_file → get_file_link

| 注意 | 说明 |
|------|------|
| upload_file 必填参数 | `drive_id` 和 `parent_id` 必须显式传递 |
| ID 体系 | kwiki 内部 kuid 需通过 `kwiki.list_items` 获取 |

## 错误速查表

> ⛔ **强制规则**：命中下方任一错误条目时，**必须立即按「处理方式」向用户提示，禁止尝试其他接口绕过或反复重试。**

| 错误特征 | 原因 | 处理方式 |
|----------|------|----------|
| `code: 403000006`，`msg: "当前版本仅支持个人用户"` | 当前登录的是企业/团队账号，该知识库接口仅对个人账号开放 | 提示用户切换至个人账号后重试 |
