# 微云 MCP API 完整参考

## 服务信息

- MCP 服务地址：`https://www.weiyun.com/api/v3/mcpserver`（Stateless HTTP 模式）

---

## Tool: weiyun.list — 目录列表查询

查询微云网盘的目录内容，支持按目录查看文件和子目录，支持分页和排序。

### 请求（McpListReq）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| get_type | uint32 | 否 | 获取类型：0-所有（默认），1-仅目录，2-仅文件，其他值返回所有 |
| offset | uint32 | 否 | 分页起始偏移量，从 0 开始 |
| limit | uint32 | **是** | 每页返回数量，最大 50 |
| order_by | uint32 | 否 | 排序字段：0-不排序（默认），1-按名字排序，2-按修改时间排序 |
| asc | bool | 否 | 排序方向：true-升序，false-降序（默认） |
| dir_key | string | 否 | 要查询的目录 key（hex 编码），为空则使用 token 绑定的 dirkey |
| pdir_key | string | 否 | 要查询的父目录 key（hex 编码），为空则使用 token 绑定的 pdirkey |

### 响应（McpListRsp）

| 字段 | 类型 | 说明 |
|------|------|------|
| pdir_key | string | 当前列表的父目录 key（hex 编码） |
| total_dir_count | uint32 | 子目录总数量 |
| total_file_count | uint32 | 文件总数量 |
| dir_list | McpDirItem[] | 目录列表 |
| file_list | McpFileItem[] | 文件列表 |
| finish_flag | bool | 是否已拉取完毕，true 表示已全部返回 |
| error | string | 错误信息，操作失败时返回具体的错误描述 |

### McpDirItem（目录项）

| 字段 | 类型 | 说明 |
|------|------|------|
| dir_key | string | 目录 key（hex 编码） |
| dir_name | string | 目录名称 |
| dir_ctime | int64 | 目录创建时间，单位毫秒 |
| dir_mtime | int64 | 目录修改时间，单位毫秒 |

### McpFileItem（文件项）

| 字段 | 类型 | 说明 |
|------|------|------|
| file_id | string | 文件唯一标识符 |
| filename | string | 文件名称 |
| file_size | int64 | 文件大小，单位字节 |
| file_ctime | int64 | 文件创建时间，单位毫秒 |
| file_mtime | int64 | 文件修改时间，单位毫秒 |
| pdir_key | string | 所在目录 key（hex 编码） |

### 注意事项

- 查询范围由 `mcp_token` 绑定的 `dirkey` 和 `pdirkey` 决定
- 腾讯文档类型的文件会被自动过滤，不出现在返回结果中

---

## Tool: weiyun.list_by_category — 按分类拉取文件列表

按微云文件分类分页拉取文件列表，支持文档、图片、视频等分类以及 `server_version` 续拉。

### 请求（McpListByCategoryReq）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| category_id | uint64 | 否 | 分类 ID（位运算值），有值时优先于 `lib_id` 和 `suffix_list`。例如：1-doc、2-excel、4-ppt、8-pdf、64-image、512-腾讯文档、4095-全部 |
| lib_id | int32 | 否 | 库 ID：1-文档，2-图片，3-音乐，4-视频，5-其他。`category_id` 有值时会忽略此字段 |
| local_version | string | 否 | 上次返回的 `server_version`，用于增量续拉；首次请求传空字符串 |
| group_id | int32 | 否 | 分组 ID。文档库：0-全部，1-doc，2-xls，3-ppt，4-pdf，50-腾讯文档 Doc，51-腾讯文档 Sheet，52-腾讯文档表单；图片/视频库可传相册分组 ID |
| suffix_list | string[] | 否 | 指定后缀列表，仅文档库和其他库有效，例如 `["docx", "xlsx"]` |
| count | int32 | **是** | 本次拉取数量，最大 100 |
| sort_type | int32 | 否 | 排序类型：0-创建时间，1-修改时间，2-名称，3-拍摄时间，4-大小 |
| is_desc_order | bool | 否 | 是否降序排列：true-降序（默认），false-升序 |

### 响应（McpListByCategoryRsp）

| 字段 | 类型 | 说明 |
|------|------|------|
| server_version | string | 服务端游标；下一次请求请回填到 `local_version` 以继续拉取 |
| finish_flag | bool | 是否已拉取完成，true 表示当前条件下已经没有更多结果 |
| file_list | McpFileItem[] | 分类文件列表（结构同 `weiyun.list` 的 `McpFileItem`） |
| error | string | 错误信息，操作失败时返回具体的错误描述 |

### 注意事项

- 该接口要求同时携带真实微云 cookie（如 `uid`、`uid_key`）和 `mcp_token`
- `category_id` 为位运算值，可组合使用（例如 `1 | 2 | 4 = 7` 表示 doc + excel + ppt）
- 首次请求 `local_version` 传空字符串，后续续拉时回填上次响应的 `server_version`
- 当 `finish_flag` 为 `true` 时表示已无更多数据

---

## Tool: weiyun.download — 批量下载

批量获取微云网盘文件的 HTTPS 下载链接。

### 请求（McpDownloadReq）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| items | McpDownloadFileItem[] | **是** | 需要获取下载链接的文件列表 |

### McpDownloadFileItem（下载文件项）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_id | string | **是** | 文件唯一标识符 |
| pdir_key | string | **是** | 文件所在目录 key（hex 编码） |

### 响应（McpDownloadRsp）

| 字段 | 类型 | 说明 |
|------|------|------|
| items | McpDownloadResultItem[] | 下载结果列表 |
| error | string | 错误信息，操作失败时返回具体的错误描述 |

### McpDownloadResultItem（下载结果项）

| 字段 | 类型 | 说明 |
|------|------|------|
| file_id | string | 文件唯一标识符 |
| https_download_url | string | HTTPS 下载链接 |
| file_size | int64 | 文件大小，单位字节 |
| cookie | string | 下载时需要携带的 cookie（格式：`cookieName=cookieValue`） |

### 注意事项

- 如果 `pdir_key` 为空，使用 token 绑定的 `dirkey`
- 会校验目录所有权，非本人目录的文件会被跳过
- 下载链接无限速

---

## Tool: weiyun.delete — 批量删除

批量删除微云网盘中的文件或目录，支持移动到回收站或彻底删除。

### 请求（McpDeleteReq）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_list | McpDeleteFileItem[] | 否 | 待删除的文件列表 |
| dir_list | McpDeleteDirItem[] | 否 | 待删除的目录列表 |
| delete_completely | bool | 否 | 是否彻底删除：false-移动到回收站（默认），true-彻底删除 |

**注意**：`file_list` 和 `dir_list` 至少要有一个非空。

### McpDeleteFileItem（删除文件项）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_id | string | **是** | 文件唯一标识符 |
| pdir_key | string | **是** | 文件所在目录 key（hex 编码） |

### McpDeleteDirItem（删除目录项）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dir_key | string | **是** | 目录 key（hex 编码） |
| pdir_key | string | **是** | 父目录 key（hex 编码） |

### 响应（McpDeleteRsp）

| 字段 | 类型 | 说明 |
|------|------|------|
| freed_space | int64 | 释放的空间大小，单位字节 |
| freed_index_cnt | uint32 | 删除的文件数和目录数之和 |
| error | string | 错误信息，操作失败时返回具体的错误描述 |

### 注意事项

- 文件删除会校验目录所有权，非本人目录的文件会被跳过
- 删除之后会进回收站，一般7天内可以恢复，会员和超级会员则分别是 30 天和 90 天

---

## Tool: weiyun.upload — 文件上传

上传文件到微云网盘，采用两阶段协议：预上传 + 分片上传，支持秒传。
注意： 除非用户提了明确的要求，修改文件名称，否则，尽量使用原本的文件名称进行上传。

### 请求（McpUploadReq）

#### 预上传阶段（upload_key 为空）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| filename | string | **是** | 文件名称 |
| file_size | uint64 | **是** | 文件大小，单位字节 |
| file_sha | string | **是** | 整个文件的 SHA1 值（hex 编码，40 字符）。必须等于 block_sha_list 最后一个值 |
| block_sha_list | string[] | **是** | 每个分块的 SHA1 状态列表（hex 编码，每个 40 字符），按 512KB 分块顺序排列。计算方法详见 SKILL.md 中的分块 SHA1 算法 |
| check_sha | string | **是** | SHA1 校验中间状态（hex 编码，40 字符） |
| check_data | string | 否 | 文件末尾 checkBlockSize 字节的 Base64 编码 |
| file_md5 | string | 否 | 整个文件的 MD5 值（hex 编码，32 字符），用于秒传校验 |
| pdir_key | string | 否 | 上传到的目录 key（hex 编码），不填则使用 token 绑定的目录 |

#### 分片上传阶段（upload_key 非空）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| upload_key | string | **是** | 预上传返回的 upload_key（hex 编码） |
| channel_list | McpChannelInfo[] | **是** | 预上传返回的通道列表 |
| channel_id | uint32 | **是** | 分片上传使用的通道编号 |
| ex | string | **是** | 预上传返回的扩展字段（hex 编码） |
| file_data | bytes | **是** | 当前分片的文件数据（二进制，JSON 传输时为 base64） |
| filename | string | **是** | 文件名称（与预上传相同） |

### McpChannelInfo（上传通道信息）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | uint32 | 通道编号 |
| offset | uint64 | 分片在文件中的偏移量 |
| len | uint32 | 分片的数据长度 |

### 响应（McpUploadRsp）

| 字段 | 类型 | 说明 |
|------|------|------|
| file_id | string | 文件唯一标识符，预上传成功后返回 |
| filename | string | 上传后的文件名 |
| file_exist | bool | 是否秒传成功，true 表示文件已存在无需上传分片 |
| upload_state | int32 | 上传状态：1-需要上传下一分片，2-上传完成，3-等待其他通道完成 |
| upload_key | string | upload_key（hex 编码），后续分片上传时需携带 |
| channel_list | McpChannelInfo[] | 通道列表，用于后续分片上传 |
| ex | string | 扩展字段（hex 编码），后续分片上传时需携带 |
| error | string | 错误信息，操作失败时返回具体的错误描述 |

### 注意事项

- 预上传会校验目录所有权，非本人目录禁止上传
- 如果 `pdir_key` 为空，使用 token 绑定的 `dirkey`
- 文件已存在时执行覆盖策略
- 默认使用多通道上传模式（最多 4 通道）
- 分片上传时 `file_data` 经过 Base64 双重处理：MCP 框架自动 base64 → bytes，服务端再次进行 Base64 解码

---

## Tool: weiyun.gen_share_link — 生成分享外链

为微云网盘中的文件或目录生成分享短链接。

### 请求（McpGenShareLinkReq）

| 字段 | 类型 | 必填 | 说明                                             |
|------|------|------|------------------------------------------------|
| file_list | McpShareFileItem[] | 否 | 待分享的文件列表                                       |
| dir_list | McpShareDirItem[] | 否 | 待分享的目录列表                                       |
| share_name | string | 否 | 分享名称，不填则使用第一个文件或目录名                            |
| passwd | string | 否 | 分享密码，不填则创建无密码分享，长度一定是 6 个字符。支持随机密码，也支持用户指定特定密码 |

**注意**：`file_list` 和 `dir_list` 至少要有一个非空。

随机分享密码生成规则：长度6，全小写字母+数字混合，不包含特殊字符

### McpShareFileItem（分享文件项）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_id | string | **是** | 文件唯一标识符 |
| pdir_key | string | **是** | 文件所在目录 key（hex 编码）。**必须使用 `weiyun.list` 响应顶层的 `pdir_key`**，不可为空 |

### McpShareDirItem（分享目录项）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dir_key | string | **是** | 目录 key（hex 编码） |
| pdir_key | string | **是** | 父目录 key（hex 编码）。**必须使用 `weiyun.list` 响应顶层的 `pdir_key`**，不可为空 |

### 响应（McpGenShareLinkRsp）

| 字段 | 类型 | 说明 |
|------|------|------|
| short_url | string | 分享短链接 |
| share_name | string | 分享名称 |
| error | string | 错误信息，操作失败时返回具体的错误描述 |

### 注意事项

- **⚠️ pdir_key 不可为空**：如果传入空的 `pdir_key`，可能导致分享链接异常，**强烈建议**调用方显式传入正确值
- `pdir_key` 应使用 `weiyun.list` 响应中**顶层的 `pdir_key`** 字段值，而非文件项中的 `pdir_key`（该字段可能为空字符串）

---

## Tool: weiyun.rename_file — 重命名文件

重命名微云网盘中的文件，需要提供文件所在目录 key 和文件 ID。

### 请求（McpRenameFileReq）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_id | string | **是** | 文件唯一标识符 |
| pdir_key | string | **是** | 文件所在目录 key（hex 编码） |
| new_filename | string | **是** | 修改后的文件名 |

### 响应（McpRenameFileRsp）

| 字段 | 类型 | 说明 |
|------|------|------|
| error | string | 错误信息，操作失败时返回具体的错误描述 |

### 注意事项

- `pdir_key` 应使用 `weiyun.list` 响应中**顶层的 `pdir_key`** 字段值
- 重命名不会改变文件的 `file_id`

---

## Tool: weiyun.rename_dir — 重命名目录

重命名微云网盘中的目录，需要提供目录 key 和父目录 key。

### 请求（McpRenameDirReq）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dir_key | string | **是** | 目录 key（hex 编码） |
| pdir_key | string | **是** | 父目录 key（hex 编码） |
| new_dir_name | string | **是** | 修改后的目录名 |
| src_dir_name | string | **是** | 修改前的目录名 |

### 响应（McpRenameDirRsp）

| 字段 | 类型 | 说明 |
|------|------|------|
| error | string | 错误信息，操作失败时返回具体的错误描述 |

### 注意事项

- `pdir_key` 应使用 `weiyun.list` 响应中**顶层的 `pdir_key`** 字段值
- 重命名不会改变目录的 `dir_key`

---

## Tool: weiyun.create_dir — 创建文件夹

在微云网盘中创建文件夹，需要提供父目录 key 和文件夹名称。

### 请求（McpCreateDirReq）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pdir_key | string | 否 | 父目录 key（hex 编码），在此目录下创建新文件夹。为空则使用 token 绑定的目录 |
| dir_name | string | **是** | 新文件夹名称 |

### 响应（McpCreateDirRsp）

| 字段 | 类型 | 说明 |
|------|------|------|
| dir_key | string | 新创建的目录 key（hex 编码） |
| dir_name | string | 创建后的目录名（可能被自动改名，如存在同名目录） |
| error | string | 错误信息，操作失败时返回具体的错误描述 |

### 注意事项

- 如果 `pdir_key` 为空，使用 token 绑定的 `dirkey` 作为父目录
- 如果目标目录下已存在同名文件夹，返回的 `dir_name` 可能会被自动改名

---

## Tool: weiyun.move_dir — 移动文件夹

移动微云网盘中的文件夹到目标目录，需要提供源目录 key 和目标目录 key。

### 请求（McpMoveDirReq）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dir_key | string | **是** | 待移动的目录 key（hex 编码） |
| src_pdir_key | string | **是** | 源父目录 key（hex 编码），即当前所在的目录 |
| dst_pdir_key | string | **是** | 目标父目录 key（hex 编码），即要移动到的目录 |
| dir_name | string | 否 | 目录名称，移动时可选填用于冲突处理 |

### 响应（McpMoveDirRsp）

| 字段 | 类型 | 说明 |
|------|------|------|
| error | string | 错误信息，操作失败时返回具体的错误描述 |

### 注意事项

- **⚠️ `src_pdir_key` 和 `dst_pdir_key` 不可为空**，必须通过 `weiyun.list` 获取正确的目录 key
- `src_pdir_key` 应使用 `weiyun.list` 响应中**顶层的 `pdir_key`** 字段值
- `dst_pdir_key` 应使用目标目录的 `weiyun.list` 响应中**顶层的 `pdir_key`** 或目标目录的 `dir_key`

---

## Tool: weiyun.move_file — 移动文件

移动微云网盘中的文件到目标目录，需要提供文件 ID、源目录 key 和目标目录 key。

### 请求（McpMoveFileReq）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_id | string | **是** | 待移动的文件唯一标识符 |
| src_pdir_key | string | **是** | 源父目录 key（hex 编码），即文件当前所在的目录 |
| dst_pdir_key | string | **是** | 目标父目录 key（hex 编码），即要移动到的目录 |
| filename | string | 否 | 文件名称，移动时可选填用于冲突处理 |

### 响应（McpMoveFileRsp）

| 字段 | 类型 | 说明 |
|------|------|------|
| error | string | 错误信息，操作失败时返回具体的错误描述 |

### 注意事项

- **⚠️ `src_pdir_key` 和 `dst_pdir_key` 不可为空**，必须通过 `weiyun.list` 获取正确的目录 key
- `src_pdir_key` 应使用文件当前所在目录的 `weiyun.list` 响应中**顶层的 `pdir_key`** 字段值
- `dst_pdir_key` 应使用目标目录的 `weiyun.list` 响应中**顶层的 `pdir_key`** 或目标目录的 `dir_key`

---

## Tool: check_skill_update — 技能版本检查更新

检查当前 Skill 版本是否有新版本可用，返回最新版本号、发布说明和更新指令。

### 请求（CheckSkillUpdateReq）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| version | string | **是** | 当前技能版本号，格式为 MAJOR.MINOR.PATCH |

### 响应（CheckSkillUpdateRsp）

| 字段 | 类型 | 说明 |
|------|------|------|
| latest | string | 最新版本号，格式为 MAJOR.MINOR.PATCH |
| release_note | string | 最新版本发布说明 |
| instruction | string | 更新指令，需要更新时遵循此指令执行 |

### 注意事项

- 如果当前已是最新版本，返回请求中传入的版本号
- **不需要认证**：此接口不依赖 `mcp_token`，无需登录即可调用

---

## 认证机制

### MCP Token

所有 MCP 工具（除 `check_skill_update` 外）需要通过 `WyHeader` HTTP 头传递 `mcp_token`：

```
WyHeader: mcp_token=<token>
```

Token 可通过微云授权页面获取：https://www.weiyun.com/disk/authorization
