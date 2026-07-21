# v2.5.3 迁移指南：`/new` 和 `/navigate` 改 POST body

## TL;DR

```diff
- curl -s "http://localhost:3456/new?url=https://example.com"
+ curl -s -X POST --data-raw 'https://example.com' http://localhost:3456/new

- curl -s "http://localhost:3456/navigate?target=ID&url=https://example.com"
+ curl -s -X POST --data-raw 'https://example.com' "http://localhost:3456/navigate?target=ID"
```

旧写法收到 `400` + 包含本文档路径的错误信息后，按下方对照表改写调用。同时把发现的旧写法在源站点经验文件中就地修正。

## 为什么改

旧版 `/new?url=...` 把目标 URL 塞进 query 参数。当目标 URL 自带 query（如小红书笔记必须携带 `xsec_token`、B 站、微博的分享链接），proxy 用 `URL.searchParams` 解析时，目标 URL 里未编码的 `&` 会被当成 **proxy 自身的** query 分隔符，导致目标 URL 被错误切分、token 等关键参数丢失，页面返回"内容不存在"或被反爬拦截。

例：

```
GET /new?url=https://xhs.com/explore/x?a=1&b=2
```

proxy 解析结果：
- `q.url = "https://xhs.com/explore/x?a=1"` ← 被截断
- `q.b = "2"` ← 被当成 proxy 自己的参数吃掉

根因是用一种"带语法的格式（query string）"承载另一种"也带相同语法的数据（URL）"，存在结构性歧义。靠调用方守纪律做 URL-encode 治标不治本：Agent 偶尔忘记就翻车，且增加每次调用的 token 成本。

v2.5.3 把 URL 改为通过 **POST body** 传入。HTTP body 是不透明字节流（边界由 `Content-Length` header 显式声明，与数据本身解耦），不存在任何分隔符歧义，URL 原样传输，零编码负担。

## 转换对照表

### `/new`

| 场景 | 旧（v2.5.2） | 新（v2.5.3） |
|---|---|---|
| 简单 URL | `curl ".../new?url=https://example.com"` | `curl -X POST --data-raw 'https://example.com' .../new` |
| URL 含 query | `curl ".../new?url=https://xhs.com/explore/x?xsec_token=ABC"` ⚠️ token 丢失 | `curl -X POST --data-raw 'https://xhs.com/explore/x?xsec_token=ABC' .../new` ✓ |
| URL 含 `#` fragment | `curl ".../new?url=https://app/page#sec"` ⚠️ fragment 丢失 | `curl -X POST --data-raw 'https://app/page#sec' .../new` ✓ |

### `/navigate`

| 旧 | 新 |
|---|---|
| `curl ".../navigate?target=ID&url=URL"` | `curl -X POST --data-raw 'URL' ".../navigate?target=ID"` |

`target` 仍走 query（它是无特殊字符的不透明 ID，没有歧义问题）。

## Agent 自检 checklist

在迁移后的环境中工作时，遇到任何来源的 web-access 调用，按以下顺序处理：

1. **判断调用是否过时**：搜索字符串 `localhost:3456/new?url=` 或 `localhost:3456/navigate?` 后跟 `&url=`。这两类模式属于 v2.5.2 旧写法。
2. **就地改写**：按上表对照修改成 POST 形式。
3. **更新源文件**：如果旧写法来自 `references/site-patterns/*.md` 中某个站点经验文件，把源文件也一并修正掉（不要只在当前调用上改）—— 这样下次复用同一站点经验时不会再踩坑。
4. **保留 URL 原样**：POST body 是不透明字节流，目标 URL 中的 `?`、`&`、`=`、`#`、`%` 等字符**无需任何转义**，从 DOM/分享链接抓到什么样就传什么样。

## FAQ

**Q: 我用 GET `?url=` 调用会发生什么？**
A: 收到 HTTP 400 响应，body 中包含 `error`、`migration` 文档路径、`example` 示例。按提示改 POST 调用即可。

**Q: 为什么不在 proxy 里做兼容（同时支持 GET 和 POST）？**
A: 兼容路径会留下永久的"启发式截取 query"代码 + SKILL.md 里"也支持旧写法"的脚注。两条路径长期共存 → Agent 学得不彻底、维护者两套都要测、读代码的人要分辨主路径 vs 兼容路径。把架构债转成了认知债。一次性 breaking change 配合迁移指南，更彻底也更便宜。

**Q: 我自己的脚本/别名/笔记里有大量旧写法，有迁移脚本吗？**
A: 没有也不打算提供。站点经验和脚本是人写的文档/代码，掺着说明、注释、上下文判断，正则替换容易误伤。本指南的 Agent 自检 checklist 就是给"Agent 看着内容自己判断怎么改"的，比脚本可靠。

**Q: 还有哪些 endpoint 用 POST body？**
A: 一直都有：`/eval`、`/click`、`/clickAt`、`/setFiles` 全是 POST + body。这次 `/new` `/navigate` 加入后，**所有传输"任意字符串载荷"的写操作都统一走 POST body** —— 内部一致性提升。
