---
name: weiyun
description: 微云网盘 MCP 接口完整技能。包含 weiyun.list、weiyun.list_by_category、weiyun.download、weiyun.delete、weiyun.upload、weiyun.gen_share_link、weiyun.rename_file、weiyun.rename_dir、weiyun.create_dir、weiyun.move_dir、weiyun.move_file、check_skill_update
  共 12 个 MCP Tool 的使用指南，以及 FTN 上传协议所需的 SHA1 分块计算脚本。当用户提到微云上传、MCP 上传、block_sha_list 计算、FTN 上传、微云文件管理或上述任一 Tool 名时触发。
description_zh: 管理腾讯微云网盘文件（列表、上传、下载、删除、分享）
description_en: Manage Tencent Weiyun cloud drive files (list, upload, download, delete, share)
version: 1.0.5
---

# 微云网盘 MCP 技能

首次安装使用时，需要先完成本地安装和注册，详见 `references/auth.md`。

> **Windows 用户**：所有 `bash ./setup.sh` 命令请替换为 `powershell -ExecutionPolicy Bypass -File setup.ps1`，详见 `references/auth.md`。

## 版本更新检查（每天首次使用前必须执行）

每天使用本 SKILL 前进行一次更新检查，按照如下步骤执行：

### 1. 查看当前版本 version

读取本文件顶部 frontmatter 中的 `version` 字段；格式为 `MAJOR.MINOR.PATCH`。

### 2. 查看最新版本 latest

通过命令获取最新版本信息 `latest`，输入参数 `version` 为上一步获取的当前版本：

```bash
mcporter call "https://www.weiyun.com/api/v3/mcpserver" "check_skill_update" --args '{"version": "当前版本"}'
```

> **Windows (PowerShell)** 用户注意：需先切换 UTF-8 编码，单引号内的 JSON 需改为转义双引号：
> ```powershell
> chcp 65001 >nul && mcporter call "https://www.weiyun.com/api/v3/mcpserver" "check_skill_update" --args "{`"version`": `"当前版本`"}"
> ```

JSON 格式数据返回，返回参数示例：

| 字段 | 类型 | 说明 |
|------|------|------|
| `latest` | string | 最新版本号，格式为 MAJOR.MINOR.PATCH |
| `release_note` | string | 最新版本发布说明 |
| `instruction` | string | 更新指令 |

### 3. 更新版本

如果当前版本 `version` 低于最新版本 `latest`，则遵循 `instruction` 指令进行更新，或提示用户更新。

---

## 功能概述

提供微云（Weiyun）网盘通过 MCP 协议进行文件管理的完整能力，包含 **12 个 MCP Tool**：

| Tool 名称 | 功能 | 说明 |
|-----------|------|------|
| `weiyun.list` | 目录列表查询 | 按目录查看文件和子目录，支持分页和排序 |
| `weiyun.list_by_category` | 按分类拉取文件列表 | 按文档、图片、视频等分类分页拉取文件，支持续拉 |
| `weiyun.download` | 批量下载 | 批量获取文件的 HTTPS 下载链接 |
| `weiyun.delete` | 批量删除 | 批量删除文件或目录，支持回收站或彻底删除 |
| `weiyun.upload` | 文件上传 | 两阶段协议：预上传 + 分片上传，支持秒传 |
| `weiyun.gen_share_link` | 生成分享外链 | 为文件或目录生成分享短链接，支持设置分享密码 |
| `weiyun.rename_file` | 重命名文件 | 重命名微云网盘中的文件 |
| `weiyun.rename_dir` | 重命名目录 | 重命名微云网盘中的目录 |
| `weiyun.create_dir` | 创建文件夹 | 在微云网盘中创建文件夹 |
| `weiyun.move_dir` | 移动文件夹 | 移动微云网盘中的文件夹到目标目录 |
| `weiyun.move_file` | 移动文件 | 移动微云网盘中的文件到目标目录 |
| `check_skill_update` | 技能版本检查更新 | 检查当前 Skill 版本是否为最新，获取更新指令 |

**核心架构原则**：文件哈希计算和 `block_sha_list` 生成**必须在客户端/本地完成**。服务端只接收预计算好的哈希值，不会接收原始文件数据来计算哈希。这种设计是为了防止海量请求打爆服务器的存储和 CPU。

## 触发场景

- 使用微云 MCP 工具进行文件管理（查询、下载、删除、上传、分享、重命名、创建文件夹、移动文件/目录）
- **上传文件到微云**：优先使用 `scripts/upload_to_weiyun.py` 一键完成，无需手动计算参数或调用 MCP
- 按分类（文档、图片、视频等）查找微云文件（`weiyun.list_by_category` Tool）
- 重命名微云文件或目录（`weiyun.rename_file`、`weiyun.rename_dir` Tool）
- 在微云中创建文件夹（`weiyun.create_dir` Tool）
- 移动微云文件或目录到其他位置（`weiyun.move_file`、`weiyun.move_dir` Tool）
- 实现或调试微云 MCP 文件上传（`weiyun.upload` Tool）
- 计算 `block_sha_list`、`check_sha`、`check_data` 等上传参数
- 理解微云两阶段上传协议（预上传 → 分片上传）
- 检查技能版本更新（`check_skill_update`）
- 调试 FTN 上传错误或 SHA1 校验不匹配问题

## 接口一览

**注意** : 所有接口请求时都**务必**要在 `req_header` 字段中携带上报数据，详见下方「数据上报」章节

### 1. weiyun.list — 目录列表查询

查询微云网盘的目录内容，返回子目录和文件列表。

**请求参数**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| get_type | uint32 | 否 | 获取类型：0-所有，1-仅目录，2-仅文件 |
| offset | uint32 | 否 | 分页起始偏移量，从 0 开始 |
| limit | uint32 | **是** | 每页返回数量，最大 50 |
| order_by | uint32 | 否 | 排序字段：0-不排序，1-按名字，2-按修改时间 |
| asc | bool | 否 | true-升序，false-降序（默认） |
| dir_key | string | 否 | 要查询的目录 key（hex 编码），为空则使用 token 绑定的 dirkey |
| pdir_key | string | 否 | 要查询的父目录 key（hex 编码），为空则使用 token 绑定的 pdirkey |
| req_header | ReqHeader | 推荐 | 请求信息头，用于数据上报（含 `qua` 和 `version`） |

**响应**：返回 `pdir_key`（父目录 key）、`dir_list`（目录列表）、`file_list`（文件列表）、`finish_flag`（是否拉取完毕）。

**注意**：腾讯文档文件会被自动过滤，不出现在返回结果中。

### 2. weiyun.list_by_category — 按分类拉取文件列表

按文件分类（文档、图片、视频等）分页拉取文件列表，支持通过 `server_version` 续拉。

**请求参数**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| category_id | uint64 | 否 | 分类 ID（位运算值），有值时优先于 lib_id 和 suffix_list。例如：1-doc、2-excel、4-ppt、8-pdf、64-image、512-腾讯文档、4095-全部 |
| lib_id | int32 | 否 | 库 ID：1-文档，2-图片，3-音乐，4-视频，5-其他。`category_id` 有值时会忽略此字段 |
| local_version | string | 否 | 上次返回的 `server_version`，用于增量续拉；首次请求传空字符串 |
| group_id | int32 | 否 | 分组 ID。文档库：0-全部，1-doc，2-xls，3-ppt，4-pdf，50-腾讯文档 Doc，51-腾讯文档 Sheet，52-腾讯文档表单；图片/视频库可传相册分组 ID |
| suffix_list | string[] | 否 | 指定后缀列表，仅文档库和其他库有效，例如 `["docx", "xlsx"]` |
| count | int32 | **是** | 本次拉取数量，最大 100 |
| sort_type | int32 | 否 | 排序类型：0-创建时间，1-修改时间，2-名称，3-拍摄时间，4-大小 |
| is_desc_order | bool | 否 | 是否降序排列：true-降序（默认），false-升序 |

**响应**：返回 `server_version`（服务端游标，续拉时回填到 `local_version`）、`file_list`（文件列表）、`finish_flag`（是否拉取完成）。

**注意**：该接口要求同时携带真实微云 cookie（如 `uid`、`uid_key`）和 `mcp_token`。

### 3. weiyun.download — 批量下载

批量获取微云文件的 HTTPS 下载链接。

**注意事项**：

本功能无法下载微云分享的链接里面的文件，只能下载用户微云网盘中的文件。

**请求参数**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| items | McpDownloadFileItem[] | **是** | 需要下载的文件列表 |

每个 `McpDownloadFileItem` 包含 `file_id`（文件 ID）和 `pdir_key`（所在目录 key），均为必填。

**响应**：每个文件返回 `file_id`、`https_download_url`（下载链接）、`file_size`（文件大小）、`cookie`（下载时需携带的 cookie）。

**权限校验**：只能下载当前用户拥有的文件（通过 `pdir_key` 判断目录所有权）。

### 4. weiyun.delete — 批量删除

批量删除微云网盘中的文件或目录。

**请求参数**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_list | McpDeleteFileItem[] | 否 | 待删除的文件列表（`file_id` + `pdir_key`） |
| dir_list | McpDeleteDirItem[] | 否 | 待删除的目录列表（`dir_key` + `pdir_key` + `dir_name`） |
| delete_completely | bool | 否 | false-移到回收站（默认），true-彻底删除 |

**McpDeleteFileItem 字段**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_id | string | **是** | 文件唯一标识符 |
| pdir_key | string | **是** | 文件所在目录 key |

**McpDeleteDirItem 字段**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dir_key | string | **是** | 目录 key（hex 编码） |
| pdir_key | string | **是** | 父目录 key（hex 编码） |
| dir_name | string | **是** | 目录名称（**后端必填**，缺失会导致 `1192 参数错误，目录名无效`） |

**注意**：`file_list` 和 `dir_list` 至少要填一个。

**⚠️ 删除目录时,必须要用户再次确认是否删除，禁止 AI 自己做决定！！**：

**⚠️ 删除目录时 `dir_name` 必填**：
- `dir_name` 可通过 `weiyun.list` 获取目录信息时得到，删除目录时必须传入，否则后端返回 `1192 参数错误`。
- 删除**文件**不受影响，无需 `dir_name`。

**响应**：返回 `freed_space`（释放的空间字节数）和 `freed_index_cnt`（删除的文件/目录总数）。

### 5. weiyun.gen_share_link — 生成分享外链

为微云文件或目录生成分享短链接。

**请求参数**：

| 字段 | 类型 | 必填 | 说明                                           |
|------|------|------|----------------------------------------------|
| file_list | McpShareFileItem[] | 否 | 待分享的文件列表（`file_id` + `pdir_key`）             |
| dir_list | McpShareDirItem[] | 否 | 待分享的目录列表（`dir_key` + `pdir_key`）             |
| share_name | string | 否 | 分享名称，不填则使用第一个文件或目录名                          |
| passwd | string | 否 | 分享密码，不填则创建无密码分享，长度一定是 6 个字符。支持随机密码，也支持用户指定密码 |

**注意**：

`file_list` 和 `dir_list` 至少要填一个。

随机分享密码生成规则：长度6，全小写字母+数字混合，不包含特殊字符

分享外链无法使用本 skill 进行下载，需要提示用户打开网页进行下载

**⚠️ 关键：pdir_key 不能为空！**
- `pdir_key` 必须使用 `weiyun.list` 响应中**顶层的 `pdir_key`**，而不是文件自身的 `pdir_key` 字段（该字段可能为空字符串）
- 如果传空的 `pdir_key`，可能导致分享链接异常，**强烈建议**调用方显式传入正确的 `pdir_key`
- 错误示例：直接用 `file_list[i].pdir_key`（可能为空）
- 正确示例：使用 `weiyun.list` 响应顶层的 `pdir_key` 字段值

**响应**：返回 `short_url`（分享短链接）和 `share_name`（分享名称）。

### 6. weiyun.upload — 文件上传

微云文件上传采用**两阶段协议**：

#### 阶段一：预上传

发送文件元数据和分块 SHA1 列表，检查是否可以秒传，或获取上传通道。

**必填字段**：`filename`、`file_size`、`file_sha`、`block_sha_list`、`check_sha`
**可选字段**：`file_md5`、`check_data`、`pdir_key`

**关键行为**：`file_sha` **必须等于** `block_sha_list` 的最后一个值，否则校验会失败。

**响应判断**：
- `file_exist=true` → 秒传成功，上传完毕
- `file_exist=false` → 使用返回的 `upload_key`、`channel_list`、`ex` 进行分片上传

**⚠️ 重试策略**：
- 预上传或分片上传时，服务端可能返回 `retcode=50000, msg=服务繁忙`（瞬时不可用），这**不是 MCP 工具自身缺陷**。
- **推荐重试方式**：遇到 `50000` 错误时，等待 2~5 秒后重试，最多重试 3 次。
- 一键上传脚本 `upload_to_weiyun.py` 已内置重试逻辑，优先使用脚本上传。
- 手动调用 MCP 上传时，调用方应自行实现重试。

#### 阶段二：分片上传

根据预上传返回的通道列表，逐片上传文件数据。

**必填字段**：`upload_key`、`channel_list`、`channel_id`、`ex`、`file_data`、`filename`

**上传状态**：
- `1` = 继续上传下一分片
- `2` = 上传完成
- `3` = 等待其他通道完成

### 7. weiyun.rename_file — 重命名文件

重命名微云网盘中的文件，需要提供文件所在目录 key 和文件 ID。

**请求参数**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_id | string | **是** | 文件唯一标识符 |
| pdir_key | string | **是** | 文件所在目录 key（hex 编码） |
| new_filename | string | **是** | 修改后的文件名 |

**响应**：返回 `error`（错误信息，成功时为空）。

### 8. weiyun.rename_dir — 重命名目录

重命名微云网盘中的目录，需要提供目录 key、父目录 key 和修改前的目录名。

**请求参数**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dir_key | string | **是** | 目录 key（hex 编码） |
| pdir_key | string | **是** | 父目录 key（hex 编码） |
| new_dir_name | string | **是** | 修改后的目录名 |
| src_dir_name | string | **是** | 修改前的目录名 |

**响应**：返回 `error`（错误信息，成功时为空）。

### 9. weiyun.create_dir — 创建文件夹

在微云网盘中创建文件夹，需要提供父目录 key 和文件夹名称。

**请求参数**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pdir_key | string | 否 | 父目录 key（hex 编码），在此目录下创建新文件夹。为空则使用 token 绑定的目录 |
| dir_name | string | **是** | 新文件夹名称 |

**响应**：

| 字段 | 类型 | 说明 |
|------|------|------|
| dir_key | string | 新创建的目录 key（hex 编码） |
| dir_name | string | 创建后的目录名（可能被自动改名，如存在同名目录） |
| error | string | 错误信息，成功时为空 |

### 10. weiyun.move_dir — 移动文件夹

移动微云网盘中的文件夹到目标目录，需要提供源目录 key 和目标目录 key。

**请求参数**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dir_key | string | **是** | 待移动的目录 key（hex 编码） |
| src_pdir_key | string | **是** | 源父目录 key（hex 编码），即当前所在的目录 |
| dst_pdir_key | string | **是** | 目标父目录 key（hex 编码），即要移动到的目录 |
| dir_name | string | 否 | 目录名称，移动时可选填用于冲突处理 |

**响应**：返回 `error`（错误信息，成功时为空）。

**⚠️ 关键**：`src_pdir_key` 和 `dst_pdir_key` 都需要使用 `weiyun.list` 响应中**顶层的 `pdir_key`** 或对应目录的 `dir_key`，不能传空字符串。

### 11. weiyun.move_file — 移动文件

移动微云网盘中的文件到目标目录，需要提供文件 ID、源目录 key 和目标目录 key。

**请求参数**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_id | string | **是** | 待移动的文件唯一标识符 |
| src_pdir_key | string | **是** | 源父目录 key（hex 编码），即文件当前所在的目录 |
| dst_pdir_key | string | **是** | 目标父目录 key（hex 编码），即要移动到的目录 |
| filename | string | 否 | 文件名称，移动时可选填用于冲突处理 |

**响应**：返回 `error`（错误信息，成功时为空）。

**⚠️ 关键**：`src_pdir_key` 和 `dst_pdir_key` 都需要使用 `weiyun.list` 响应中**顶层的 `pdir_key`** 或对应目录的 `dir_key`，不能传空字符串。

### 12. check_skill_update — 技能版本检查更新

检查当前 Skill 版本是否为最新，如有新版本则返回更新指令。

**请求参数**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| version | string | **是** | 当前 Skill 版本号，格式 MAJOR.MINOR.PATCH |

**响应**：

| 字段 | 类型 | 说明 |
|------|------|------|
| latest | string | 最新版本号，格式 MAJOR.MINOR.PATCH |
| release_note | string | 最新版本发布说明 |
| instruction | string | 更新指令（需要更新时遵循此指令执行） |

**注意**：每天首次使用本 Skill 前必须执行一次版本检查（详见文档顶部「版本更新检查」章节）。

## 分块 SHA1 计算算法

这是上传功能最核心的部分。微云**不使用**标准的独立分块 SHA1，而是使用**流式 SHA1 内部状态**。

### 算法步骤（分块大小 = 512KB = 524288 字节）

1. 创建**一个**共享的 SHA1 哈希对象
2. 对于除最后一块之外的每个块：
   - 读取 524288 字节并 `update()` 到 SHA1 对象
   - 提取 SHA1 内部寄存器（h0, h1, h2, h3, h4）以**小端序**输出
   - 输出为 40 字符 hex 字符串 → 该块的 `sha` 值
3. 对于最后一块（可能不足 524288 字节）：
   - 继续用相同 SHA1 对象 update 剩余数据
   - `sha` 值为**整个文件的标准 SHA1 hexdigest**（大端序，含 finalization）

### check_sha 和 check_data 计算

用于服务端防篡改验证：

```
lastBlockSize = file_size % 524288（若为 0 则取 524288）
checkBlockSize = lastBlockSize % 128（若为 0 则取 128）

check_sha：处理完所有非最后块后，继续 update 最后块中前 (lastBlockSize - checkBlockSize) 字节，
           然后取 SHA1 内部寄存器 h0-h4 小端序输出为 hex
check_data：文件末尾 checkBlockSize 字节的 Base64 编码
```

### 使用脚本

#### 一键上传脚本（推荐）

直接上传本地文件到微云，整合了参数计算 + 预上传 + 分片上传的完整流程：

```bash
# 基本用法
python3 scripts/upload_to_weiyun.py /path/to/file --token <mcp_token> --env_id <env_id>

# 指定上传目录
python3 scripts/upload_to_weiyun.py /path/to/file --token <mcp_token> --pdir_key <dir_key>

# 使用环境变量
export WEIYUN_MCP_TOKEN=<mcp_token>
export WEIYUN_ENV_ID=<env_id>
python3 scripts/upload_to_weiyun.py /path/to/file
```

> **Windows (PowerShell)** 用户：需先切换 UTF-8 编码，将 `python3` 替换为 `python`，`export` 替换为 `$env:VAR = "value"`：
> ```powershell
> # 基本用法
> chcp 65001 >nul && python scripts\upload_to_weiyun.py C:\path\to\file --token <mcp_token> --env_id <env_id>
>
> # 使用环境变量
> $env:WEIYUN_MCP_TOKEN = "<mcp_token>"
> $env:WEIYUN_ENV_ID = "<env_id>"
> chcp 65001 >nul && python scripts\upload_to_weiyun.py C:\path\to\file
> ```


脚本参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `file_path` | **是** | 本地文件路径（位置参数） |
| `--token` | **是** | MCP token（或设 `WEIYUN_MCP_TOKEN` 环境变量） |
| `--env_id` | 否 | 环境标识（如 `sit-0cd15bb3`，或设 `WEIYUN_ENV_ID`） |
| `--pdir_key` | 否 | 上传目标目录 key（不填使用 token 绑定目录） |
| `--mcp_url` | 否 | MCP 服务地址（默认 `https://www.weiyun.com/api/v3/mcpserver`） |
| `--max_rounds` | 否 | 最大上传轮数（默认 50） |

上传策略：循环「预上传获取通道 → 上传一片 → 重新预上传」直到完成。每次预上传会自动跳过已成功的分片（offset 随进度递增），支持秒传。

**AI Agent 使用时**：只需要 `execute_command` 运行此脚本即可，无需手动计算 block_sha_list 或调用 MCP。

#### 参数计算脚本

仅计算上传参数（不执行上传），用于调试或手动调用 MCP：

```bash
python3 scripts/gen_block_info_list.py /path/to/file
```

> **Windows (PowerShell)**：`chcp 65001 >nul && python scripts\gen_block_info_list.py C:\path\to\file`

输出包括：`block_sha_list`、`file_sha`、`file_md5`、`check_sha`、`check_data`、`block_size`、`block_count`。

两个脚本均包含纯 Python 的 SHA1 实现，支持提取未经 finalization 的内部状态 — 这是 Python 标准库 `hashlib.sha1` 无法做到的。


## 错误码说明

MCP 接口在出现异常时会返回以下错误码，调用方可根据错误码进行相应处理：

| 错误码 | 名称 | 说明 |
|--------|------|------|
| 1192 | 参数错误，目录名无效 | 删除目录时缺少 `dir_name` 字段，需通过 `weiyun.list` 获取后传入 |
| 50000 | 服务繁忙 | 服务端瞬时不可用，等待 2~5 秒后重试，最多重试 3 次 |
| 117401 | ERR_RATE_LIMIT | 每日调用配额已耗尽，请明天再试 |
| 117402 | ERR_MCP_TOKEN_INVALID | MCP token 无效或已过期，请重新生成 token |
| 117403 | ERR_MCP_PARAM_EMPTY | 请求必填参数为空（如删除接口 file_list 和 dir_list 都为空） |
| 117404 | ERR_MCP_PARAM_INVALID | 请求参数不合法（如 file_id 或 pdir_key 格式错误） |
| 117405 | ERR_MCP_PERMISSION_DENIED | 无权操作非本人目录的文件 |
| 117406 | ERR_MCP_BACKEND_FAIL | 后端服务调用失败，请稍后重试 |
| 117407 | ERR_MCP_TOKEN_DISABLED | MCP token 已被禁用（取消授权/手动拉黑/安全打击） |

**处理建议**：
- **1192**：删除目录时 `dir_name` 缺失导致，请先通过 `weiyun.list` 获取目录名再传入 `weiyun.delete`
- **50000**：服务端临时异常，等待 2~5 秒后重试，最多 3 次。上传场景建议优先使用 `upload_to_weiyun.py`（已内置重试）
- **117401**：等待次日零点配额自动重置，或开通微云会员提升配额
- **117402**：重新生成 token
- **117403/117404**：检查请求参数是否完整且格式正确
- **117405**：确认操作的文件/目录属于当前用户
- **117406**：属于服务端临时异常，可重试
- **117407**：错误是取消授权则需要重新授权，被安全误打击则需要联系微云客服人员做解封处理

## 常见操作工作流

### 工作流 1：查找并下载文件

当需要在微云中找到某个文件并下载到本地时，按以下步骤操作：

**第一步：查询根目录**

```
调用 weiyun.list，参数：limit=50, get_type=0
```

- 响应中的 `file_list` 包含文件，`dir_list` 包含子目录
- **记住响应顶层的 `pdir_key`**（后续下载需要用到）
- 如果文件在根目录 → 进入第三步
- 如果文件不在根目录 → 需要遍历子目录（第二步）

**第二步：遍历子目录查找文件**

```
调用 weiyun.list，参数：
  dir_key = <子目录的 dir_key>（从 dir_list 中获取）
  pdir_key = <子目录所在父目录的 pdir_key>（即上一次 list 响应顶层的 pdir_key，或子目录所在目录的 dir_key）
  limit = 50
```

**⚠️ 关键**：查询子目录时 `dir_key` 和 `pdir_key` 的含义：
- `dir_key`：要查询的目标子目录的 key（从 `dir_list` 中的 `dir_key` 字段获取）
- `pdir_key`：该子目录所在的父目录 key（从上一级 `weiyun.list` 响应顶层的 `pdir_key` 获取）

如果还有嵌套子目录，递归重复此步骤。

**第三步：获取下载链接**

```
调用 weiyun.download，参数：
  items = [{"file_id": "<文件的 file_id>", "pdir_key": "<文件所在目录的 pdir_key>"}]
```

- `file_id`：从 `file_list` 中获取
- `pdir_key`：使用 `weiyun.list` 响应中**顶层的 `pdir_key`**（不是文件自身的 `pdir_key` 字段）

**第四步：下载文件到本地**

```bash
curl -s -L -o <本地文件名> -b "<cookie>" "<https_download_url>"
```

> **Windows (PowerShell)**：
> ```powershell
> $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
> $session.Cookies.Add((New-Object System.Net.Cookie("FTN5K", "<cookie值>", "/", ".weiyun.com")))
> Invoke-WebRequest -Uri "<https_download_url>" -OutFile "<本地文件名>" -WebSession $session
> ```

- `-L`：跟随重定向（必须）
- `-b`：携带 cookie（从 download 响应中获取，格式如 `FTN5K=08bfd4be`）
- 下载完成后验证文件大小与 `file_size` 一致

### 工作流 2：上传文件到微云

**推荐方式**（一键脚本）：

```bash
# 1. 先查根目录获取 pdir_key
# 调用 weiyun.list limit=50 → 记住响应中的 pdir_key

# 2. 上传
python3 scripts/upload_to_weiyun.py /path/to/file --pdir_key <pdir_key>
```

> **Windows (PowerShell)**：`chcp 65001 >nul && python scripts\upload_to_weiyun.py C:\path\to\file --pdir_key <pdir_key>`

**手动方式**：参见上方「5. weiyun.upload — 文件上传」章节。

### 工作流 3：生成分享链接

```
# 1. 先查目录获取文件信息和 pdir_key
调用 weiyun.list → 找到目标文件的 file_id，记住响应**顶层** pdir_key

# 2. 生成分享链接（pdir_key 必须非空！）
调用 weiyun.gen_share_link，参数：
  file_list = [{"file_id": "<file_id>", "pdir_key": "<响应顶层的 pdir_key>"}]
  share_name = "<文件名>"
```

**⚠️ 关键**：`pdir_key` 必须使用 `weiyun.list` 响应中**顶层的 `pdir_key`**，绝对不能传空字符串！文件项中的 `pdir_key` 字段可能为空，不可使用。

### 工作流 4：删除文件或目录

```
# 1. 先查目录获取文件信息
调用 weiyun.list → 找到目标文件的 file_id 或目录的 dir_key 和 dir_name，记住响应顶层 pdir_key

# 2a. 删除文件
调用 weiyun.delete，参数：
  file_list = [{"file_id": "<file_id>", "pdir_key": "<pdir_key>"}]
  delete_completely = false  （移到回收站，更安全）

# 2b. 删除目录（dir_name 必填）
调用 weiyun.delete，参数：
  dir_list = [{"dir_key": "<dir_key>", "pdir_key": "<pdir_key>", "dir_name": "<目录名>"}]
  delete_completely = false
```

**注意**：删除目录时 `dir_name` 必填，可通过 `weiyun.list` 返回的 `dir_list[].dir_name` 获取。

### 工作流 5：重命名文件或目录

```
# 1. 先查目录获取文件/目录信息
调用 weiyun.list → 找到目标文件的 file_id 或目录的 dir_key，记住响应顶层 pdir_key

# 2a. 重命名文件
调用 weiyun.rename_file，参数：
  file_id = "<file_id>"
  pdir_key = "<响应顶层的 pdir_key>"
  new_filename = "<新文件名>"

# 2b. 重命名目录
调用 weiyun.rename_dir，参数：
  dir_key = "<dir_key>"
  pdir_key = "<响应顶层的 pdir_key>"
  new_dir_name = "<新目录名>"
  src_dir_name = "<原目录名>"
```

### 工作流 6：按分类查找文件

```
# 查找所有 PDF 文件
调用 weiyun.list_by_category，参数：
  category_id = 8    （8 = PDF）
  count = 50

# 续拉更多结果
调用 weiyun.list_by_category，参数：
  category_id = 8
  count = 50
  local_version = "<上次响应的 server_version>"

# 按后缀查找
调用 weiyun.list_by_category，参数：
  lib_id = 1         （1 = 文档库）
  suffix_list = ["docx", "xlsx"]
  count = 50
```

### 工作流 7：创建文件夹

```
# 1. 先查目录获取 pdir_key（如果要在子目录下创建）
调用 weiyun.list → 记住响应顶层 pdir_key 或目标子目录的 dir_key

# 2. 创建文件夹
调用 weiyun.create_dir，参数：
  pdir_key = "<目标父目录的 pdir_key>"（为空则在 token 绑定的根目录下创建）
  dir_name = "<新文件夹名称>"
```

**响应**：返回新创建目录的 `dir_key` 和 `dir_name`（可能因同名被自动改名）。

### 工作流 8：移动文件或目录

```
# 1. 先查源目录获取文件/目录信息
调用 weiyun.list，查询源目录 → 找到目标文件的 file_id 或目录的 dir_key，记住响应顶层 pdir_key 作为 src_pdir_key

# 2. 查目标目录获取 dst_pdir_key
调用 weiyun.list，查询目标目录 → 记住响应顶层的 pdir_key 作为 dst_pdir_key

# 3a. 移动文件
调用 weiyun.move_file，参数：
  file_id = "<file_id>"
  src_pdir_key = "<源目录的 pdir_key>"
  dst_pdir_key = "<目标目录的 pdir_key>"

# 3b. 移动目录
调用 weiyun.move_dir，参数：
  dir_key = "<要移动的目录 dir_key>"
  src_pdir_key = "<源父目录的 pdir_key>"
  dst_pdir_key = "<目标父目录的 pdir_key>"
```

**⚠️ 关键**：`src_pdir_key` 和 `dst_pdir_key` 不能为空，必须通过 `weiyun.list` 获取正确的目录 key。

## 认证机制

所有 MCP 工具需要通过 `WyHeader` HTTP 头传递 `mcp_token`：

```
WyHeader: mcp_token=<token>
```



## 数据上报

为了方便微云官方进行问题故障定位，MCP 客户端在调用每个接口时，**应在请求体的 `req_header` 字段中携带上报数据**。

### ReqHeader 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `qua` | string | 推荐 | 用户设备信息，格式：`{平台}_{平台版本}_{渠道}_{渠道方版本}`，如 `MAC_15.4.1_CODEBUDDY_4.8.1` |
| `version` | string | 推荐 | skill 的版本号，如 `1.0.4`，取自本文件顶部 frontmatter 的 `version` 字段 |

### qua 规则（客户端实时采集）

QUA 是一个字符串，由设备信息拼接而成：

```
{平台}_{平台版本}_{渠道}_{渠道方版本}
```

- **平台**：检测当前操作系统类型（`MAC` / `WINDOWS` / `LINUX`）
- **平台版本**：获取操作系统版本号（如 macOS `15.4.1`，Windows `10.0.19045`）
- **渠道**：MCP 客户端的产品名称（如 `CODEBUDDY`、`WORKBUDDY`）
- **渠道方版本**：MCP 客户端（IDE 插件）的版本号

| 平台 | QUA 示例 |
|------|---------|
| macOS | `MAC_15.4.1_CODEBUDDY_4.8.1` |
| Windows | `WINDOWS_10.0.19045_WORKBUDDY_4.8.1` |
| Linux | `LINUX_6.1.0_CODEBUDDY_4.8.1` |

### 请求示例

```json
{
  "limit": 50,
  "req_header": {
    "qua": "MAC_15.4.1_CODEBUDDY_4.8.1",
    "version": "1.0.5"
  }
}
```

## 常见问题

1. **上传文件应该怎么做**：直接用 `python3 scripts/upload_to_weiyun.py <文件路径> --pdir_key <目录key>`，无需手动计算参数或调用 MCP
2. **下载时 pdir_key 应该填什么**：使用 `weiyun.list` 响应中**顶层的 `pdir_key`**，而不是文件自身的 `pdir_key` 字段（该字段可能为空字符串）
3. **生成分享链接时 pdir_key 不能为空**：必须先调用 `weiyun.list`，使用响应**顶层的 `pdir_key`**（不是 `file_list[i].pdir_key`，该字段通常为空）。`pdir_key` 为空会导致分享链接打开异常
4. **查询子目录时 pdir_key 怎么填**：填入子目录所在父目录的 key。对于根目录下的子目录，就是根目录 `weiyun.list` 响应顶层的 `pdir_key`
5. **下载时需要携带 cookie**：`weiyun.download` 返回的下载链接需要用 `curl -b "<cookie>"` 携带 cookie 值，同时 `-L` 跟随重定向
6. **上传报 "Cannot upload to a directory that you do not own"**：必须指定 `--pdir_key` 参数。先调用 `weiyun.list` 获取响应中顶层的 `pdir_key`
7. **分片上传通道 len=0**：每轮上传完一片后，返回的通道列表可能全部 len=0，需要重新预上传获取下一批通道。`upload_to_weiyun.py` 已自动处理此问题
8. **SHA1 不匹配**：确保分块 SHA 值使用流式 SHA1 内部状态（小端序），而非独立分块 SHA1
9. **file_sha 被覆盖**：服务端用最后一个 block 的 SHA 覆盖 file_sha — 两者必须相等
10. **Base64 双重编码**：MCP 框架自动将 base64 字符串转为 bytes 传给 `file_data` 字段，服务端会再次进行 Base64 解码
11. **通道 ID 不匹配**：上传分片时 `channel_id` 必须与 `channel_list` 中某个条目匹配
12. **环境标识**：SIT 环境需在 Cookie 中携带 `env_id=sit-xxxxx`
13. **权限校验**：下载、删除、分享操作会校验目录所有权，非本人目录的文件会被跳过
14. **腾讯文档过滤**：列表查询会自动过滤腾讯文档类型的文件
15. **pip install requests**：上传脚本依赖 `requests` 库，如提示缺少请先安装：`pip install requests`
16. **所有需要 pdir_key 的操作**（下载、删除、分享、上传、重命名），都应使用 `weiyun.list` 响应**顶层**的 `pdir_key`，而不是文件/目录条目自身的 `pdir_key` 字段
17. **Windows 编码要求（防止中文乱码）**：Windows 下执行 Python 脚本或 mcporter 命令前**必须**先切换控制台代码页为 UTF-8，格式为 `chcp 65001 >nul && python ...`。Python 脚本已内置 `_encoding_fix.py` 模块自动修复 stdout/stderr 编码，但 `chcp 65001` 仍然是必要的（确保 cmd/PowerShell 控制台本身使用 UTF-8 解码输出）
18. **Windows 下使用 `python` 而非 `python3`**：Windows 系统通常使用 `python` 命令，macOS/Linux 使用 `python3`。请根据用户操作系统自动选择正确的命令
19. **重命名文件/目录**：先调用 `weiyun.list` 获取 `file_id`/`dir_key`、`dir_name` 和顶层 `pdir_key`，再调用 `weiyun.rename_file` 或 `weiyun.rename_dir`（重命名目录时需额外传 `src_dir_name` 即原目录名）
20. **按分类查找文件**：使用 `weiyun.list_by_category`，通过 `category_id` 或 `lib_id` 指定分类，支持 `server_version` 续拉。该接口需要同时携带真实微云 cookie 和 `mcp_token`
21. **生成带密码的分享链接**：在调用 `weiyun.gen_share_link` 时设置 `passwd` 参数即可创建加密分享
22. **创建文件夹**：调用 `weiyun.create_dir`，传入 `pdir_key`（父目录 key）和 `dir_name`（文件夹名称）。`pdir_key` 为空时在 token 绑定的根目录下创建。返回的 `dir_name` 可能因同名冲突被自动改名
23. **移动文件/目录**：使用 `weiyun.move_file` 或 `weiyun.move_dir`。需要先通过 `weiyun.list` 分别获取源目录和目标目录的 `pdir_key`，填入 `src_pdir_key` 和 `dst_pdir_key`。两个 key 都不能为空
24. **移动操作的目录 key 获取**：`src_pdir_key` 来自文件/目录当前所在位置的 `weiyun.list` 响应顶层 `pdir_key`；`dst_pdir_key` 来自目标位置的 `weiyun.list` 响应顶层 `pdir_key` 或目标目录的 `dir_key`
25. **删除目录返回 1192 错误**：`dir_name` 是删除目录时的必填字段，需通过 `weiyun.list` 获取目录的 `dir_name` 后传入 `weiyun.delete`。删除文件不需要此字段
26. **上传时报 50000 服务繁忙**：这是服务端瞬时不可用，非 MCP 工具缺陷。等待 2~5 秒后重试，最多 3 次。推荐使用 `upload_to_weiyun.py` 一键上传脚本（已内置重试逻辑）


