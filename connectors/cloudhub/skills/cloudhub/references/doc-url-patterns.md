# doc / sheet 分享 URL 识别

云之家知识库的在线文档（`otl`）与多维表格（`dbt`）通过 SPA hash 路由分享。真实链接形态为 `https://{host}/knowledge/#/share/doc/<shareToken>?docId=<docId>`：fragment 中含分享凭证 `shareToken`，真正的节点 ID `docId` 藏在 fragment 内嵌的 query 中。本文档定义识别规则与 `docId` 提取流程，供 `doc` / `sheet` 命令使用。

> sheet 与 doc 共享同一 URL 形态，识别规则一致，本文档同时适用于 `sheet`。

## 已知 URL 格式

| 节点类型 | URL 格式 | ID 提取 | 用于 |
|----------|----------|---------|------|
| 在线文档（otl）/ 多维表格（dbt）/ 文件夹 | `https://{host}/knowledge/#/share/doc/<shareToken>?docId=<DOC_ID>` | fragment 内嵌 query 的 `docId` | `doc get --id`、`sheet get --id`、`doc list --parent-id`、`doc rename --id` 等 |

`{host}` 必须命中下列有效域名后缀之一，否则视为不可识别链接：

- `*.yunzhijia.com`
- `*.yunzhijia.cn`
- `*.kdweibo.com`
- `*.kdweibo.cn`

即四个一级域名：`yunzhijia.com`、`yunzhijia.cn`、`kdweibo.com`、`kdweibo.cn`。

> 示例：`https://www.yunzhijia.com/knowledge/#/share/doc/abc123token?docId=1dc4261b13f345f1a4af0e88f3ae4d2c` → `DOC_ID = 1dc4261b13f345f1a4af0e88f3ae4d2c`

## 提取规则（硬性）

按以下顺序命中第一条即返回，未命中转「不可识别」：

0. **域名校验**：URL 的 host 必须以上述四个有效后缀结尾，否则直接判为不可识别。
1. **path 校验**：URL 的 path 必须以 `/knowledge/` 开头（末尾斜杠可有可无），否则判为不可识别。
2. **Fragment 拆分**：取 `#` 之后的部分作为 fragment；fragment 内若含 `?`，则 `?` 前为 fragment path，`?` 后为 fragment query。
3. **取 docId**：从 fragment query 中解析 `docId=<VALUE>`（需 URL-decode）。若 fragment query 缺失或不含 `docId`，判为不可识别。
4. **shareToken 不作 ID 用**：fragment path 中的 `<shareToken>` 是分享凭证，不是节点 ID，禁止把它传给 `--id`。

约束：
- 提取出的 `docId` 直接用于 `doc --id` / `sheet --id`；CLI 当前不会代理解析 URL，**禁止**把整个 URL 传给 `--id`。
- 旧版 fragment 形态 `/share/<type>/<DOC_ID>`（fragment 末段即 docId）已废弃，因为 SHARE_ID 与真实 DOC_ID 不一致；一律以 fragment 内嵌 query 的 `docId` 为准。

伪代码：

```
input = "https://www.yunzhijia.com/knowledge/#/share/doc/abc123token?docId=1dc4261b13f345f1a4af0e88f3ae4d2c"

# step 0: host 校验
host = parse_host(input)  # → "www.yunzhijia.com"
if not (host.endswith(".yunzhijia.com") or host.endswith(".yunzhijia.cn")
        or host.endswith(".kdweibo.com") or host.endswith(".kdweibo.cn")):
    return UNRECOGNIZED

# step 1: path 校验
path = parse_path(input)  # → "/knowledge/"
if not path.startswith("/knowledge/"):
    return UNRECOGNIZED

# step 2-3: fragment 拆分 + 取 docId
fragment = input.split("#", 1)[1]  # → "/share/doc/abc123token?docId=1dc4261b13f345f1a4af0e88f3ae4d2c"
if "?" in fragment:
    fragment_path, fragment_query = fragment.split("?", 1)
else:
    fragment_query = ""
doc_id = url_decode(query_value(fragment_query, "docId"))
if not doc_id:
    return UNRECOGNIZED
return doc_id  # → "1dc4261b13f345f1a4af0e88f3ae4d2c"
```

## URL 粘贴场景

| 用户输入 | 处理 |
|----------|------|
| 只粘贴 URL，无其他指令 | 提取 `DOC_ID` → `doc get --id <DOC_ID>` 读节点信息判断 `fileSuffix`：`otl` 在线文档按 [./doc.md](./doc.md) 操作；`dbt` 多维表格按 [./sheet.md](./sheet.md) 操作；`type=1` 文件夹转 `doc list --workspace <KB_ID> --parent-id <DOC_ID>` |
| URL +「看下内容」 | otl：`doc get --id <DOC_ID>`；dbt：`sheet get --id <DOC_ID>` + `sheet record list --id <DOC_ID> --table-id <SHEET_ID>` |
| URL +「看下结构 / 字段」 | dbt：`sheet get --id <DOC_ID>` |
| URL +「改名 / 移动 / 删除」 | 复用 `doc rename` / `doc move` / `doc delete`，传 `<DOC_ID>` |

## 不可识别的 URL

- host 不在有效域名后缀白名单内（非 `*.yunzhijia.com` / `*.yunzhijia.cn` / `*.kdweibo.com` / `*.kdweibo.cn`）
- path 不以 `/knowledge/` 开头
- fragment 缺失、或 fragment 内嵌 query 中无 `docId`
- 移动端短链 / 站外分享链（可能经过跳转，落地 URL 才是上述形态）
- 旧版 `/share/<type>/<DOC_ID>` 形态：fragment 末段是 SHARE_ID 而非真实 DOC_ID，已废弃

→ 直接告知用户「该链接暂不支持解析」，请用户提供节点标题、所在知识库名称等线索，再通过 `doc workspace list` → `doc list` 路径找到目标节点。

## 注意事项

- **分享 URL 的权限**：分享 URL 能否访问取决于分享设置与当前账号权限；`doc get` / `sheet get` 失败时直接把错误透传给用户，不要静默失败。
- **白名单内的常见 host**：凡是 `yunzhijia.com`、`yunzhijia.cn`、`kdweibo.com`、`kdweibo.cn` 及其任意子域都按上述规则识别；白名单以外的 host 直接判为不可识别。
- **`shareToken` 与 `docId` 的区分**：fragment path 中的 `<shareToken>` 是分享凭证，调用 `doc` / `sheet` 命令用不到；`--id` 永远传 `docId`。
