# file URL 识别

云之家文件在多个场景下以 URL 形态出现：IM 富文本图片、知识库附件、群头像、消息卡片缩略图、静态资源 CDN 等。本文档定义识别规则与 `fileId` 提取流程，供 `file download` 命令使用。

## 已知 URL 格式

| 场景 | URL 格式 | ID 提取 | 用于 |
|------|----------|---------|------|
| IM 文件 / 附件下载（query 形） | `https://{host}/docrest/doc/user/downloadfile?fileId=<FILE_ID>` | query 参数 `fileId` | `file download --id` |
| 图片 / 缩略图（query 形） | `https://{host}/docrest/doc/user/image?fileId=<FILE_ID>` | query 参数 `fileId` | `file download --id` |
| 群头像 / 静态资源（path 形） | `https://{host}/microblog/filesvr/<FILE_ID>` | path 中 `filesvr/` 的下一段 | `file download --id` |
| 旧版下载链（path 形） | `https://{host}/docrest/file/downloadfile/<FILE_ID>?w280=&big=1` | path 中 `downloadfile/` 的下一段 | `file download --id` |

`{host}` 必须命中下列有效域名后缀之一，否则视为不可识别链接：

- `*.yunzhijia.com`
- `*.yunzhijia.cn`
- `*.kdweibo.com`
- `*.kdweibo.cn`

即四个一级域名：`yunzhijia.com`、`yunzhijia.cn`、`kdweibo.com`、`kdweibo.cn`。

> 示例：
> - `https://static.yunzhijia.com/docrest/doc/user/downloadfile?fileId=6a601d5ed64b03000162ad07` → `FILE_ID = 6a601d5ed64b03000162ad07`
> - `https://www.yunzhijia.com/microblog/filesvr/69b51749e4b05d56218f3510` → `FILE_ID = 69b51749e4b05d56218f3510`

## 提取规则（硬性）

按以下顺序命中第一条即返回，未命中转「不可识别」：

0. **域名校验**：URL 的 host 必须以上述四个有效后缀结尾，否则直接判为不可识别，不再进入后续步骤。
1. **Query 形优先**：URL 含 `?` 且 query 中存在 `fileId=<VALUE>`，取 `VALUE`（需 URL-decode）。
2. **Path 形回退**：将 path 按 `/` 切分，找到 `filesvr` 或 `downloadfile` 段，取其**下一段**非空 path segment 作为 ID。
3. **裸 ID 直通**：输入既无 `?` 也无 `/`、且非空时，视为裸 `fileId` 直接使用。

约束：
- 提取出的 ID 直接用于 `file download --id`；CLI 当前不会代理解析 URL，**禁止**把整个 URL 传给 `--id`。
- 不要把整段 path（如 `docrest/doc/user/downloadfile`）作为 ID。
- query 形与 path 形都可能出现在同一 URL 中（如 `.../downloadfile/<ID>?w280=&big=1`），此时以 path 段为准（因为 `?` 后是缩略参数而非 `fileId`）。

伪代码：

```
input = "https://static.yunzhijia.com/docrest/doc/user/downloadfile?fileId=6a601d5ed64b03000162ad07"

# step 0: host 校验
host = parse_host(input)  # → "static.yunzhijia.com"
if not (host.endswith(".yunzhijia.com") or host.endswith(".yunzhijia.cn")
        or host.endswith(".kdweibo.com") or host.endswith(".kdweibo.cn")):
    return UNRECOGNIZED

# step 1: query
if "fileId=" in input:
    return url_decode(query_value("fileId"))  # → "6a601d5ed64b03000162ad07"

# step 2: path
segments = path.split("/")
for i, seg in enumerate(segments):
    if seg in ("filesvr", "downloadfile") and i+1 < len(segments):
        return segments[i+1]

# step 3: bare id
if "/" not in input and "?" not in input and input != "":
    return input
```

## URL 粘贴场景

| 用户输入 | 处理 |
|----------|------|
| 只粘贴 URL，无其他指令 | 提取 `FILE_ID` → `file download --id <FILE_ID>`；若服务端返回 2001/2002，向用户解释为文件已过期或无权限 |
| URL + 「下载到 xxx」/「另存为」 | `file download --id <FILE_ID> --output <PATH>` |
| URL + 「覆盖下载」 | `file download --id <FILE_ID> --output <PATH> --overwrite`（先确认目标路径） |
| URL + 「上传到群」/「发到群里」 | 先 `file download` 拿到本地文件 → `file upload --file <LOCAL>` 换取新 fileId → `im message send --msg-type file --file-id <NEW_FILE_ID>`；不能直接把原 URL 的 fileId 转发到其他群，可能无权限 |
| URL + 「这文件是啥 / 看下」 | 不能直接预览；先 `file download` 到本地再让用户打开 |

## 不可识别的 URL

- host 不在有效域名后缀白名单内（非 `*.yunzhijia.com`、`*.yunzhijia.cn`、`*.kdweibo.com`、`*.kdweibo.cn`）
- 不含 `fileId=` query，path 中也无 `filesvr/`、`downloadfile/` 标记
- 路径里 `filesvr` / `downloadfile` 后没有下一段（如 `…/filesvr?x=1`）
- 移动端短链 / 站外分享链（可能经过跳转，落地 URL 才是上述形态）
- 知识库 SPA 路由 `https://www.yunzhijia.com/knowledge#/share/doc/<DOC_ID>` —— 这是文档节点，不是文件，应走 `doc` 而非 `file`（参考 [./doc.md](./doc.md)）

→ 直接告知用户「该链接暂不支持解析」，请用户描述来源（IM 消息 / 知识库附件 / 群头像 / 邮件附件），或直接提供 `fileId`。

## 注意事项

- **`fileId` 的有效期与权限**：URL 中携带的 fileId 可能属于他人或其他企业，`file download` 会先调 `getDownloadInfoOpen` 校验权限（`errorCode=2002` 表示无权限，`2001` 表示文件不存在或已过期）。失败时直接把错误透传给用户，不要静默失败。
- **白名单内的常见 host**：凡是 `yunzhijia.com`、`yunzhijia.cn`、`kdweibo.com`、`kdweibo.cn` 及其任意子域都按 path / query 规则识别；白名单以外的 host 直接判为不可识别。
- **path 形 URL 的 query 参数可能是缩略图参数**（`w280`、`big` 等），不是 fileId，不要误用。
