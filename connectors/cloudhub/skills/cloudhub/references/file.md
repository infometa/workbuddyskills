# file（文件上传与下载）

通用文件 scope，独立于 doc / im / sheet。

> 用户粘贴文件 URL（IM 附件、群头像、CDN 资源等）时，先按 [file/url-patterns.md](./file-url-patterns.md) 提取 `fileId`，再走下列命令。

## 意图映射

| 用户说 | 命令 |
|--------|------|
| 上传文件 / 传个附件 / 上传本地文件 | `file upload --file <LOCAL_PATH>` |
| 批量上传 / 上传多个文件 | `file upload --file a.txt b.txt c.txt`（最多 5 并发，超出排队） |
| 上传并改名 | `file upload --file <LOCAL_PATH> --name <NEW_NAME>`（仅单文件） |
| 下载文件 / 按 fileId 拉 | `file download --id <FILE_ID>` |
| 下载到指定路径 | `file download --id <FILE_ID> --output <PATH>` |
| 下载时同名强制覆盖 | `file download --id <FILE_ID> --overwrite`（不传 `--overwrite` 时自动重命名，如 `report.pdf` → `report (1).pdf`） |

## 核心工作流

```
本地文件 → file upload → file_id → 用于其他 scope（im 消息、doc 附件等）
file_id → file download → 本地文件
```

## 命令速查

```bash
# 上传（单文件）
yzj-cli file upload --file ./report.pdf

# 上传并改名
yzj-cli file upload --file ./report.pdf --name "Q1汇报.pdf"

# 批量上传（最多 5 并发，超出排队）
yzj-cli file upload --file a.txt b.txt c.txt
yzj-cli file upload --file a.txt --file b.txt

# 下载（按 file_id）
yzj-cli file download --id <FILE_ID>
yzj-cli file download --id <FILE_ID> --output ./downloads/
yzj-cli file download --id <FILE_ID> --output ./save.zip --overwrite
```

## file upload

上传本地文件到云之家文件服务，返回 `fileId`。

| 参数 | 必填 | 说明 |
|------|------|------|
| `--file` | 是 | 本地文件路径，可重复或空格分隔多个 |
| `--name` | 否 | 上传后的文件名；**仅单文件可用**，多文件时报错退出，不发起请求 |

**限制**：
- 单文件大小上限 **30MB**
- 多文件最多 **5 个并发**，超出排队
- `--name` 与多文件共用时命令直接退出，不发起请求

**校验**：
- 路径不存在 / 是目录 / 文件为空 → 即时退出，不发起请求
- 多文件 + `--name` → 即时退出，不发起请求
- 单文件超过 30MB → 即时退出，不发起请求

**输出**：
- 单文件：成功信封，`data` 为上传结果对象（含 `fileId`、`fileName`、`length`）
- 多文件：全部成功时 `data` 为各文件结果数组（按完成顺序）；任一文件失败则整条命令报错——stderr 输出单行错误信封（message 含失败文件路径），退出码按首个错误派生，stdout 为空

## file download

按 `fileId` 下载文件到本地。两步流程：

1. 先调 `getDownloadInfoOpen` 做权限与存在性前置校验（无权限 `errorCode=2002`、文件不存在或已过期 `2001`），同时取 `fileName` 用于输出路径推断
2. 再调 `downloadfileOpen` 流式拉取文件内容

**下载流程**：
1. `getDownloadInfoOpen` 校验 + 取元信息（失败直接退出）
2. 确定目标路径：`--output` > `getDownloadInfoOpen.fileName` > `Content-Disposition` 文件名 > `file_id`
3. 目标文件已存在且无 `--overwrite` → 自动重命名（`report.pdf` → `report (1).pdf`）
4. 流式写入临时文件 `<name>.yzjdownload`（64KB 缓冲）
5. 成功后重命名为最终路径（原子操作）

| 参数 | 必填 | 说明 |
|------|------|------|
| `--id` | 是 | 文件 ID |
| `--output` | 否 | 输出路径，可为目录或文件路径；省略时按 `getDownloadInfoOpen.fileName` → `Content-Disposition` → `file_id` 顺序推断；以路径分隔符结尾或指向已存在目录时按目录处理 |
| `--overwrite` | 否 | 目标文件已存在时强制覆盖；不传时自动重命名避免冲突 |

**输出**：成功时打印 `downloaded <N> bytes to <path>`。

## 危险操作

- `file download --overwrite` — 覆盖本地已存在文件，执行前需确认目标路径
- `file upload` 上传即落服务端，无法撤销；敏感文件需用户确认

## 与其他 scope 的关系

- `im message send --msg-type file --file-id <FILE_ID>`：`file upload` 返回的 `fileId` 直接可用于发文件消息
- `im message send --msg-type richText --image <FILE_ID>`：图片类富文本消息同样复用 `fileId`
- doc 详情返回的 `fileUrl` 是否走同一 file_id 池未验证，跨 scope 前先小批量试
